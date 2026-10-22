from __future__ import annotations

import io
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import settings
from .schemas import (
    LoginRequest,
    LoginResponse,
    UserProfile,
    CVUploadResponse,
    CVValidateResponse,
    CVDetailResponse,
    AdminLogsResponse,
    HealthReportResponse,
    ServiceHealthStatus,
)
from .logger_collector import setup_in_memory_logging, get_system_logs, log_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_gateway")
setup_in_memory_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_event("api_gateway", "INFO", "API Gateway успешно запущен и готов к обработке запросов")
    yield


app = FastAPI(
    title="HRCVHelper - API Gateway",
    version="1.0.0",
    description="Центральный API-шлюз и оркестратор системы HRCVHelper",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Разрешаем CORS для Flutter Web (порт 8501) и локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Хелперы для извлечения пользователя ---

async def get_optional_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{settings.auth_system_url}/auth/verify", json={"token": token})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    return data.get("user")
    except Exception as e:
        logger.warning("Ошибка проверки токена: %s", e)
    return None


# =========================================================================
# 🧑‍💼 Контур HR-специалиста
# =========================================================================

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    ФТ-HR.1: Авторизация HR-специалиста.
    Перенаправляет запрос в AuthSystem, возвращает токен сессии и профиль.
    """
    log_event("api_gateway", "INFO", f"Попытка авторизации пользователя: {req.login}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.auth_system_url}/auth/login",
                json=req.model_dump(),
            )
            if resp.status_code != 200:
                log_event("api_gateway", "WARNING", f"Ошибка авторизации пользователя {req.login}: {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", "Ошибка входа"))

            data = resp.json()
            log_event("api_gateway", "INFO", f"Успешная авторизация: {req.login}")
            return LoginResponse(**data)
    except httpx.RequestError as e:
        log_event("api_gateway", "ERROR", f"AuthSystem недоступен: {e}")
        raise HTTPException(status_code=503, detail="Сервис авторизации временно недоступен")


@app.post("/api/v1/cv/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    hr_id: Optional[int] = Form(None),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    ФТ-HR.2: Загрузка исходного файла CV, конвертация в MD, семантический парсинг
    через Gemma-3 и возврат JSON-черновика со статусом 'Ожидает проверки HR'.
    """
    filename = file.filename or "cv_document"
    effective_hr_id = hr_id or (current_user.get("hr_id") if current_user else 1) or 1

    log_event("api_gateway", "INFO", f"Начало обработки резюме '{filename}' от HR_ID={effective_hr_id}")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Файл резюме пуст")

    async with httpx.AsyncClient(timeout=360.0) as client:
        # 1. Фиксация начального состояния в БД: "Загружено"
        try:
            clean_name = filename.rsplit(".", 1)[0].replace("_", " ")
            init_cv_payload = {
                "hr_id": effective_hr_id,
                "jsonb": {
                    "fio": clean_name,
                    "vacancy": "ИИ-структурирование резюме...",
                    "skills_and_tools": [],
                    "education": [],
                    "projects": []
                },
                "status": "Загружено",
            }
            create_resp = await client.post(f"{settings.db_connector_url}/cv", json=init_cv_payload)
            if create_resp.status_code != 201:
                raise HTTPException(status_code=500, detail="Не удалось создать запись CV в БД")
            cv_record = create_resp.json()
            cv_id = cv_record["cv_id"]
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис базы данных недоступен")

        # 2. Переход: "Конвертация в MD"
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Переход в статус: Конвертация в MD")
        await client.put(f"{settings.db_connector_url}/cv/{cv_id}/status", json={"status": "Конвертация в MD"})

        try:
            files = {"file": (filename, io.BytesIO(file_bytes), file.content_type or "application/octet-stream")}
            md_resp = await client.post(f"{settings.md_convertor_url}/convert", files=files)
            if md_resp.status_code != 200:
                raise HTTPException(status_code=md_resp.status_code, detail=f"Ошибка конвертации в Markdown: {md_resp.text}")
            markdown_content = md_resp.json().get("markdown", "")
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"MDConvertor недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис MDConvertor недоступен")

        # 3. Переход: "Обработка резюме" (LLM Gemma-3)
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Переход в статус: Обработка резюме (Gemma-3)")
        await client.put(f"{settings.db_connector_url}/cv/{cv_id}/status", json={"status": "Обработка резюме"})

        try:
            llm_payload = {"markdown": markdown_content, "original_filename": filename}
            llm_resp = await client.post(f"{settings.llm_convertor_url}/parse", json=llm_payload)
            if llm_resp.status_code != 200:
                raise HTTPException(status_code=llm_resp.status_code, detail=f"Ошибка парсинга LLM: {llm_resp.text}")
            parsed_data = llm_resp.json().get("data", {})
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"LLMConvertor недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис LLMConvertor недоступен")

        # 4. Переход: "Ожидает проверки HR" и сохранение черновика JSONB
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Парсинг завершен. Переход в статус: Ожидает проверки HR")
        update_payload = {
            "jsonb": parsed_data,
            "status": "Ожидает проверки HR",
        }
        update_resp = await client.put(f"{settings.db_connector_url}/cv/{cv_id}", json=update_payload)
        if update_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Не удалось сохранить распарсенный JSON в БД")

        return CVUploadResponse(
            cv_id=cv_id,
            hr_id=effective_hr_id,
            status="Ожидает проверки HR",
            data=parsed_data,
            filename=filename,
        )


@app.put("/api/v1/cv/{cv_id}/validate", response_model=CVValidateResponse)
async def validate_and_generate_docx(
    cv_id: int,
    validated_json: Dict[str, Any],
):
    """
    ФТ-HR.3 + ФТ-HR.4: Подтверждение проверенного HR-специалистом JSON,
    сохранение в БД, вызов JSONToWord для генерации .docx, загрузка в S3
    и перевод резюме в финальный статус 'Готово'.
    """
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Получен подтвержденный JSON от HR. Начинаем валидацию и генерацию docx")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Проверяем наличие резюме
        cv_check = await client.get(f"{settings.db_connector_url}/cv/{cv_id}")
        if cv_check.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
        cv_record = cv_check.json()

        # 1. Переводим статус в "Формирование docx" и обновляем JSONB
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Переход в статус: Формирование docx")
        await client.put(
            f"{settings.db_connector_url}/cv/{cv_id}",
            json={"jsonb": validated_json, "status": "Формирование docx"},
        )

        # 2. Вызов сервиса JSONToWord (docxtpl)
        try:
            jtw_resp = await client.post(
                f"{settings.json_to_word_url}/generate",
                json=validated_json,
            )
            if jtw_resp.status_code != 200:
                log_event("api_gateway", "ERROR", f"[CV {cv_id}] Ошибка JSONToWord: {jtw_resp.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка генерации DOCX: {jtw_resp.text}")
            docx_bytes = jtw_resp.content
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"JSONToWord сервис недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис JSONToWord недоступен")

        # 3. Сохранение файла в хранилище S3 через DBConnector
        fio_slug = validated_json.get("fio", "candidate").replace(" ", "_")
        object_key = f"resumes/cv_{cv_id}_{fio_slug}.docx"

        try:
            files = {"file": (object_key, io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            storage_resp = await client.post(
                f"{settings.db_connector_url}/storage/upload",
                files=files,
                data={"object_name": object_key},
            )
            if storage_resp.status_code != 200:
                log_event("api_gateway", "ERROR", f"[CV {cv_id}] Ошибка S3 storage: {storage_resp.text}")
                raise HTTPException(status_code=500, detail="Ошибка сохранения файла в S3")
            storage_data = storage_resp.json()
            docx_url_or_key = storage_data.get("url_or_path", object_key)
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector Storage недоступен: {e}")
            raise HTTPException(status_code=503, detail="Хранилище S3 недоступно")

        # 4. Фиксация статуса "Готово" и ключа Docx в БД
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Документ сохранен в S3. Переход в статус: Готово")
        final_resp = await client.put(
            f"{settings.db_connector_url}/cv/{cv_id}/docx",
            params={"docx_key": object_key, "status": "Готово"},
        )
        if final_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Не удалось обновить статус 'Готово' в БД")

        download_url = f"/api/v1/cv/{cv_id}/download"

        return CVValidateResponse(
            cv_id=cv_id,
            hr_id=cv_record["hr_id"],
            status="Готово",
            docx_url=docx_url_or_key,
            download_url=download_url,
            data=validated_json,
        )


@app.put("/api/v1/cv/{cv_id}/rework")
async def return_cv_for_rework(cv_id: int):
    """
    ФТ-HR.3: Возврат резюме на доработку при обнаружении ошибок/неточностей.
    Переводит резюме в статус 'Обработка резюме' (согласно UML State Machine).
    """
    log_event("api_gateway", "WARNING", f"[CV {cv_id}] HR вернул резюме на доработку (Найдены ошибки). Переход в статус: Обработка резюме")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.put(
            f"{settings.db_connector_url}/cv/{cv_id}/status",
            json={"status": "Обработка резюме"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Не удалось обновить статус резюме в БД")
        return {"cv_id": cv_id, "status": "Обработка резюме", "message": "Резюме возвращено на доработку"}


@app.put("/api/v1/cv/{cv_id}/draft")
async def save_cv_draft(cv_id: int, draft_json: Dict[str, Any]):
    """
    ФТ-HR.3: Сохранение промежуточного черновика JSON HR-специалистом без генерации DOCX.
    """
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Сохранение черновика HR")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.put(
            f"{settings.db_connector_url}/cv/{cv_id}",
            json={"jsonb": draft_json, "status": "Ожидает проверки HR"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Не удалось сохранить черновик в БД")
        return {"cv_id": cv_id, "status": "Ожидает проверки HR", "message": "Черновик успешно сохранен"}


@app.get("/api/v1/cv/{cv_id}", response_model=CVDetailResponse)
async def get_cv(cv_id: int):
    """
    Получение данных резюме, статуса и ссылки на готовый .docx.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{settings.db_connector_url}/cv/{cv_id}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()

        download_url = f"/api/v1/cv/{cv_id}/download" if data.get("docx") else None
        return CVDetailResponse(
            cv_id=data["cv_id"],
            hr_id=data["hr_id"],
            status=data["status"],
            jsonb=data["jsonb"],
            docx=data["docx"],
            download_url=download_url,
        )


@app.get("/api/v1/cv/{cv_id}/download")
async def download_cv_docx(cv_id: int):
    """
    Скачивание сгенерированного корпоративного документа .docx из S3.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Проверяем запись CV
        resp = await client.get(f"{settings.db_connector_url}/cv/{cv_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")

        cv_record = resp.json()
        docx_key = cv_record.get("docx")
        if not docx_key:
            raise HTTPException(status_code=400, detail="Файл .docx для данного резюме еще не сгенерирован")

        # Скачиваем из хранилища
        download_resp = await client.get(f"{settings.db_connector_url}/storage/download/{docx_key}")
        if download_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Файл не найден в хранилище S3")

        filename = docx_key.split("/")[-1]
        ascii_filename = "".join(c for c in filename if c.isascii() and (c.isalnum() or c in "._-")) or "resume.docx"
        disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}'
        return Response(
            content=download_resp.content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": disposition},
        )


@app.get("/api/v1/cv", response_model=List[CVDetailResponse])
async def list_cvs(hr_id: Optional[int] = None, skip: int = 0, limit: int = 50):
    """
    Получение списка резюме (с фильтром по HR-специалисту).
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        params = {"skip": skip, "limit": limit}
        if hr_id is not None:
            params["hr_id"] = hr_id
        resp = await client.get(f"{settings.db_connector_url}/cv", params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        items = resp.json()
        return [
            CVDetailResponse(
                cv_id=c["cv_id"],
                hr_id=c["hr_id"],
                status=c["status"],
                jsonb=c["jsonb"],
                docx=c["docx"],
                download_url=f"/api/v1/cv/{c['cv_id']}/download" if c.get("docx") else None,
            )
            for c in items
        ]


# =========================================================================
# 🛠️ Контур Администратора
# =========================================================================

@app.get("/api/v1/admin/logs", response_model=AdminLogsResponse)
def get_logs(limit: int = 100):
    """
    ФТ-АДМ.1: Просмотр системных логов работы контейнеров.
    """
    logs = get_system_logs(limit=limit)
    return AdminLogsResponse(total=len(logs), logs=logs)


@app.get("/api/v1/admin/health", response_model=HealthReportResponse)
async def get_health_report():
    """
    ФТ-АДМ.2: Сводный отчет о состоянии всех микросервисов и хранилищ системы (health report).
    """
    services_status: Dict[str, ServiceHealthStatus] = {}
    overall_ok = True

    targets = [
        ("auth_system", f"{settings.auth_system_url}/health"),
        ("md_convertor", f"{settings.md_convertor_url}/health"),
        ("llm_convertor", f"{settings.llm_convertor_url}/health"),
        ("json_to_word", f"{settings.json_to_word_url}/health"),
        ("db_connector", f"{settings.db_connector_url}/health"),
    ]

    async with httpx.AsyncClient(timeout=3.0) as client:
        for s_name, url in targets:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    services_status[s_name] = ServiceHealthStatus(
                        service=s_name,
                        status="healthy",
                        details=r.json(),
                    )
                else:
                    overall_ok = False
                    services_status[s_name] = ServiceHealthStatus(
                        service=s_name,
                        status="degraded",
                        details={"status_code": r.status_code, "text": r.text},
                    )
            except Exception as e:
                overall_ok = False
                services_status[s_name] = ServiceHealthStatus(
                    service=s_name,
                    status="unreachable",
                    details={"error": str(e)},
                )

    services_status["api_gateway"] = ServiceHealthStatus(
        service="api_gateway",
        status="healthy",
        details={"version": "1.0.0"},
    )

    return HealthReportResponse(
        status="healthy" if overall_ok else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services_status,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.gateway_host, port=settings.gateway_port)
