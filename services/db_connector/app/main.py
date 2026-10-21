from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from urllib.parse import quote
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import engine, get_db, init_db
from .models import HR, CV
from .schemas import (
    HRCreate,
    HRResponse,
    HRInDB,
    CVCreate,
    CVUpdate,
    CVStatusUpdate,
    CVResponse,
    StorageUploadResponse,
    HealthResponse,
)
from .s3_client import s3_storage
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_connector")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("База данных инициализирована")
    yield


app = FastAPI(
    title="HRCVHelper - DBConnector Service",
    version="1.0.0",
    description="Микросервис управления базой данных PostgreSQL и объектным хранилищем S3",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("Ошибка проверки БД: %s", e)

    storage_ok = s3_storage.is_healthy()

    status = "ok" if (db_ok and storage_ok) else "degraded"
    return HealthResponse(status=status, database=db_ok, storage=storage_ok)


# --- HR Endpoints ---

@app.post("/users", response_model=HRResponse, status_code=201)
def create_user(hr_in: HRCreate, db: Session = Depends(get_db)):
    from . import crud
    existing = crud.get_hr_by_login(db, hr_in.login)
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    db_hr = crud.create_hr(db, hr_in)
    return HRResponse(hr_id=db_hr.HR_ID, full_name=db_hr.Full_Name, login=db_hr.Login)


@app.get("/users/login/{login}", response_model=HRInDB)
def get_user_by_login(login: str, db: Session = Depends(get_db)):
    from . import crud
    db_hr = crud.get_hr_by_login(db, login)
    if not db_hr:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return HRInDB(
        hr_id=db_hr.HR_ID,
        full_name=db_hr.Full_Name,
        login=db_hr.Login,
        hash_pass=db_hr.Hash_Pass,
    )


@app.get("/users/id/{hr_id}", response_model=HRResponse)
def get_user_by_id(hr_id: int, db: Session = Depends(get_db)):
    from . import crud
    db_hr = crud.get_hr_by_id(db, hr_id)
    if not db_hr:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return HRResponse(hr_id=db_hr.HR_ID, full_name=db_hr.Full_Name, login=db_hr.Login)


@app.get("/users", response_model=List[HRResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from . import crud
    hrs = crud.list_hrs(db, skip=skip, limit=limit)
    return [HRResponse(hr_id=h.HR_ID, full_name=h.Full_Name, login=h.Login) for h in hrs]


# --- CV Endpoints ---

@app.post("/cv", response_model=CVResponse, status_code=201)
def create_cv_record(cv_in: CVCreate, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.create_cv(db, cv_in)
    return CVResponse(
        cv_id=db_cv.CV_ID,
        hr_id=db_cv.HR_ID,
        jsonb=db_cv.JSONB,
        status=db_cv.Status,
        docx=db_cv.Docx,
    )


@app.get("/cv/{cv_id}", response_model=CVResponse)
def get_cv_record(cv_id: int, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.get_cv_by_id(db, cv_id)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse(
        cv_id=db_cv.CV_ID,
        hr_id=db_cv.HR_ID,
        jsonb=db_cv.JSONB,
        status=db_cv.Status,
        docx=db_cv.Docx,
    )


@app.put("/cv/{cv_id}", response_model=CVResponse)
def update_cv_record(cv_id: int, cv_update: CVUpdate, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.update_cv(db, cv_id, cv_update)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse(
        cv_id=db_cv.CV_ID,
        hr_id=db_cv.HR_ID,
        jsonb=db_cv.JSONB,
        status=db_cv.Status,
        docx=db_cv.Docx,
    )


@app.put("/cv/{cv_id}/status", response_model=CVResponse)
def update_cv_status_record(cv_id: int, update: CVStatusUpdate, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.update_cv_status(db, cv_id, update.status)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse(
        cv_id=db_cv.CV_ID,
        hr_id=db_cv.HR_ID,
        jsonb=db_cv.JSONB,
        status=db_cv.Status,
        docx=db_cv.Docx,
    )


@app.put("/cv/{cv_id}/docx", response_model=CVResponse)
def update_cv_docx_record(cv_id: int, docx_key: str, status: Optional[str] = "Готово", db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.update_cv_docx(db, cv_id, docx_key, status)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse(
        cv_id=db_cv.CV_ID,
        hr_id=db_cv.HR_ID,
        jsonb=db_cv.JSONB,
        status=db_cv.Status,
        docx=db_cv.Docx,
    )


@app.get("/cv", response_model=List[CVResponse])
def list_cvs(hr_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from . import crud
    if hr_id is not None:
        cvs = crud.list_cvs_by_hr(db, hr_id, skip, limit)
    else:
        cvs = crud.list_all_cvs(db, skip, limit)
    return [
        CVResponse(
            cv_id=c.CV_ID,
            hr_id=c.HR_ID,
            jsonb=c.JSONB,
            status=c.Status,
            docx=c.Docx,
        )
        for c in cvs
    ]


# --- Storage Endpoints ---

@app.post("/storage/upload", response_model=StorageUploadResponse)
async def upload_file_to_storage(
    file: UploadFile = File(...),
    object_name: Optional[str] = Form(None),
):
    contents = await file.read()
    key = object_name or file.filename or "unnamed_file"
    url_or_path = s3_storage.upload_bytes(contents, key)
    return StorageUploadResponse(key=key, url_or_path=url_or_path)


@app.get("/storage/download/{key:path}")
def download_file_from_storage(key: str):
    try:
        data = s3_storage.download_bytes(key)
        raw_filename = key.split("/")[-1]
        ascii_filename = "".join(c for c in raw_filename if c.isascii() and (c.isalnum() or c in "._-")) or "document.docx"
        disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(raw_filename)}'

        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": disposition},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Файл {key} не найден")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.service_host, port=settings.service_port)
