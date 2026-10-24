from __future__ import annotations

import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import engine, get_db, init_db
from .models import HR, CV, CVStatus
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
    TemplateResponse,
    FieldConfigResponse,
)
from .s3_client import s3_storage
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_connector")

_LOG_BUFFER: deque[dict] = deque(maxlen=200)

class InMemoryLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "service": "db_connector",
                "message": self.format(record),
            }
            _LOG_BUFFER.appendleft(entry)
        except Exception:
            self.handleError(record)

_log_handler = InMemoryLogHandler()
_log_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(_log_handler)


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


@app.get("/internal/logs")
def get_internal_logs(limit: int = 100):
    """Внутренний эндпоинт буферизированных системных логов (TASK-3.4)."""
    return {"service": "db_connector", "logs": list(_LOG_BUFFER)[:limit]}


# --- HR Endpoints ---

@app.post("/users", response_model=HRResponse, status_code=201)
def create_user(hr_in: HRCreate, db: Session = Depends(get_db)):
    from . import crud
    existing = crud.get_hr_by_login(db, hr_in.login)
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    db_hr = crud.create_hr(db, hr_in)
    return HRResponse.model_validate(db_hr)


@app.get("/users/login/{login}", response_model=HRInDB)
def get_user_by_login(login: str, db: Session = Depends(get_db)):
    from . import crud
    db_hr = crud.get_hr_by_login(db, login)
    if not db_hr:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return HRInDB.model_validate(db_hr)


@app.get("/users/id/{hr_id}", response_model=HRResponse)
def get_user_by_id(hr_id: int, db: Session = Depends(get_db)):
    from . import crud
    db_hr = crud.get_hr_by_id(db, hr_id)
    if not db_hr:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return HRResponse.model_validate(db_hr)


@app.get("/users", response_model=List[HRResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from . import crud
    hrs = crud.list_hrs(db, skip=skip, limit=limit)
    return [HRResponse.model_validate(h) for h in hrs]


# --- CV Endpoints ---

@app.post("/cv", response_model=CVResponse, status_code=201)
def create_cv_record(cv_in: CVCreate, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.create_cv(db, cv_in)
    return CVResponse.model_validate(db_cv)


@app.get("/cv/{cv_id}", response_model=CVResponse)
def get_cv_record(cv_id: int, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.get_cv_by_id(db, cv_id)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse.model_validate(db_cv)


@app.put("/cv/{cv_id}", response_model=CVResponse)
def update_cv_record(cv_id: int, cv_update: CVUpdate, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.update_cv(db, cv_id, cv_update)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse.model_validate(db_cv)


@app.put("/cv/{cv_id}/status", response_model=CVResponse)
def update_cv_status_record(cv_id: int, update: CVStatusUpdate, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.update_cv_status(db, cv_id, update.status)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse.model_validate(db_cv)


@app.put("/cv/{cv_id}/docx", response_model=CVResponse)
def update_cv_docx_record(cv_id: int, docx_key: str, status: Optional[str] = CVStatus.READY.value, db: Session = Depends(get_db)):
    from . import crud
    db_cv = crud.update_cv_docx(db, cv_id, docx_key, status)
    if not db_cv:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
    return CVResponse.model_validate(db_cv)


@app.get("/cv", response_model=List[CVResponse])
def list_cvs(hr_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    from . import crud
    if hr_id is not None:
        cvs = crud.list_cvs_by_hr(db, hr_id, skip, limit)
    else:
        cvs = crud.list_all_cvs(db, skip, limit)
    return [CVResponse.model_validate(c) for c in cvs]


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


# --- Template Endpoints (PostgreSQL) ---

@app.get("/templates", response_model=List[TemplateResponse])
def get_templates_list(db: Session = Depends(get_db)):
    """Возвращает список всех шаблонов Word из базы данных."""
    from . import crud
    templates = crud.list_templates(db)
    return [TemplateResponse(**t.to_dict()) for t in templates]


@app.get("/templates/active", response_model=TemplateResponse)
def get_active_template_endpoint(db: Session = Depends(get_db)):
    """Возвращает текущий активный шаблон из БД."""
    from . import crud
    active = crud.get_active_template(db)
    if not active:
        raise HTTPException(status_code=404, detail="Активный шаблон не найден")
    return TemplateResponse(**active.to_dict())


@app.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template_endpoint(template_id: str, db: Session = Depends(get_db)):
    """Возвращает метаданные шаблона по ID."""
    from . import crud
    tpl = crud.get_template_by_id(db, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Шаблон с ID '{template_id}' не найден")
    return TemplateResponse(**tpl.to_dict())


@app.get("/templates/{template_id}/download")
def download_template_endpoint(template_id: str, db: Session = Depends(get_db)):
    """Скачивание бинарного файла .docx шаблона прямо из базы данных (BYTEA)."""
    from . import crud
    tpl = crud.get_template_by_id(db, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Шаблон с ID '{template_id}' не найден")

    ascii_filename = "".join(c for c in tpl.filename if c.isascii() and (c.isalnum() or c in "._-")) or "template.docx"
    disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(tpl.filename)}'

    return Response(
        content=tpl.file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": disposition, "X-Filename": quote(tpl.filename)},
    )


@app.post("/templates", response_model=TemplateResponse)
async def upload_template_to_db(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    make_active: bool = Form(False),
    hr_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """Сохранение нового .docx шаблона в базу данных PostgreSQL."""
    import uuid
    from . import crud
    content = await file.read()
    if not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="Файл не является корректным документом .docx")

    template_id = str(uuid.uuid4())[:8]
    tpl = crud.create_template(
        db=db,
        template_id=template_id,
        name=name or file.filename or "Шаблон Word",
        filename=file.filename or "template.docx",
        file_bytes=content,
        description=description,
        is_system=False,
        is_active=make_active,
        hr_id=hr_id,
    )
    return TemplateResponse(**tpl.to_dict())


@app.post("/templates/{template_id}/set-default", response_model=TemplateResponse)
def set_active_template_endpoint(template_id: str, db: Session = Depends(get_db)):
    """Установка активного шаблона в базе данных."""
    from . import crud
    tpl = crud.set_active_template(db, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Шаблон с ID '{template_id}' не найден")
    return TemplateResponse(**tpl.to_dict())


@app.delete("/templates/{template_id}")
def delete_template_endpoint(template_id: str, db: Session = Depends(get_db)):
    """Удаление пользовательского шаблона из БД."""
    from . import crud
    try:
        success = crud.delete_template(db, template_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Шаблон с ID '{template_id}' не найден")
        return {"status": "ok", "message": f"Шаблон {template_id} удален из БД"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


# --- FieldConfig Endpoints (PostgreSQL) ---

@app.get("/configs/fields", response_model=FieldConfigResponse)
def get_fields_config_endpoint(config_key: str = "default", db: Session = Depends(get_db)):
    """Получение JSON-конфигурации полей из базы данных."""
    from . import crud
    cfg = crud.get_field_config(db, config_key)
    if not cfg:
        default_fields = {
            "fio": True, "vacancy": True, "total_year_work": True,
            "citizenship_location": True, "employment": True, "status": True,
            "pitch": True, "skills_and_tools": True, "project_backround": True,
            "languages": True, "projects": True, "project_role": True,
            "project_period": True, "project_tasks": True, "project_achievements": True,
            "project_skills": True, "education": True, "advanced_training": True
        }
        cfg = crud.save_field_config(db, fields=default_fields, config_key=config_key)
    return FieldConfigResponse(**cfg.to_dict())


@app.post("/configs/fields", response_model=FieldConfigResponse)
def save_fields_config_endpoint(
    payload: Dict[str, bool],
    config_key: str = "default",
    name: Optional[str] = "Конфигурация полей",
    hr_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Сохранение JSON-конфигурации полей в базу данных."""
    from . import crud
    cfg = crud.save_field_config(db, fields=payload, config_key=config_key, name=name or "Конфигурация полей", hr_id=hr_id)
    return FieldConfigResponse(**cfg.to_dict())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.service_host, port=settings.service_port)
