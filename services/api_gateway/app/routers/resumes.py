from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile, status

from ..clients.db_client import db_client
from ..clients.service_clients import md_client, llm_client, word_client
from ..dependencies import get_current_user
from ..enums import CVStatus
from ..logger_collector import log_event
from ..schemas import (
    CVDetailResponse,
    CVUploadResponse,
    CVValidateResponse,
    ReworkRequest,
)

logger = logging.getLogger("api_gateway.routers.resumes")
router = APIRouter(prefix="/api/v1/cv", tags=["CV"])


async def run_upload_pipeline(cv_id: int, effective_hr_id: int, filename: str, file_bytes: bytes):
    """
    Фоновый конвейер обработки загруженного резюме (TASK-3.1 + TASK-3.2):
    1. Перевод в статус 'Конвертация в MD' и вызов MDConvertor.
    2. Перевод в статус 'Обработка резюме' и вызов LLMConvertor.
    3. Сохранение распарсенного JSONB и перевод в статус 'Ожидает проверки HR'.
    При любом сбое статус надежно переводится в 'Ошибка парсинга'.
    """
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Запуск фонового конвейера обработки для файла '{filename}'")
    try:
        # 1. Переход: "Конвертация в MD"
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Переход в статус: {CVStatus.MD_CONVERSION.value}")
        await db_client.update_cv_status(cv_id, CVStatus.MD_CONVERSION.value)

        markdown_content = await md_client.convert(filename, file_bytes)

        # 2. Переход: "Обработка резюме" (LLM Gemma-3)
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Переход в статус: {CVStatus.LLM_PROCESSING.value} (Gemma-3)")
        await db_client.update_cv_status(cv_id, CVStatus.LLM_PROCESSING.value)

        parsed_data = await llm_client.parse(
            markdown=markdown_content,
            filename=filename,
        )
        parsed_data["_raw_markdown"] = markdown_content
        parsed_data["_original_filename"] = filename

        # 3. Переход: "Ожидает проверки HR" и сохранение структурированного JSONB
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Парсинг успешно завершен. Переход в статус: {CVStatus.AWAITING_HR.value}")
        update_payload = {
            "jsonb": parsed_data,
            "status": CVStatus.AWAITING_HR.value,
        }
        await db_client.update_cv(cv_id, update_payload)

    except Exception as e:
        logger.exception("[CV %s] Ошибка в фоновом конвейере обработки: %s", cv_id, e)
        log_event("api_gateway", "ERROR", f"[CV {cv_id}] Сбой обработки резюме: {e}")
        try:
            await db_client.update_cv_status(cv_id, CVStatus.ERROR.value)
        except Exception as update_err:
            logger.error("[CV %s] Не удалось перевести резюме в статус ошибки: %s", cv_id, update_err, exc_info=True)


async def run_rework_pipeline(cv_id: int, rework_comment: Optional[str] = None):
    """
    Фоновый конвейер пересоздания резюме при возврате на доработку:
    1. Извлекает текущее состояние резюме из БД.
    2. Передает структурированные данные в LLMConvertor для внутренней реконструкции и доработки.
    3. Сохраняет обновленный JSONB и переводит статус обратно в 'Ожидает проверки HR'.
    """
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Запущен фоновый конвейер пересоздания (доработки) резюме")
    try:
        cv_record = await db_client.get_cv(cv_id)
        if not cv_record:
            log_event("api_gateway", "ERROR", f"[CV {cv_id}] Резюме не найдено при пересоздании")
            await db_client.update_cv_status(cv_id, CVStatus.ERROR.value)
            return

        jsonb_data = cv_record.get("jsonb", {})
        markdown_content = jsonb_data.get("_raw_markdown")
        filename = jsonb_data.get("_original_filename") or f"cv_{cv_id}.pdf"

        # Делегируем парсинг и реконструкцию текста сервису LLM (TASK-3.2)
        new_parsed_data = await llm_client.parse(
            markdown=markdown_content,
            cv_data=jsonb_data,
            filename=filename,
            rework_comment=rework_comment,
        )
        new_parsed_data["_raw_markdown"] = markdown_content or ""
        new_parsed_data["_original_filename"] = filename
        if rework_comment:
            new_parsed_data["_rework_comment"] = rework_comment

        update_payload = {
            "jsonb": new_parsed_data,
            "status": CVStatus.AWAITING_HR.value,
        }
        await db_client.update_cv(cv_id, update_payload)
        log_event("api_gateway", "INFO", f"[CV {cv_id}] Повторная обработка завершена. Статус: {CVStatus.AWAITING_HR.value}")

    except Exception as e:
        logger.exception("[CV %s] Ошибка в фоновом конвейере доработки: %s", cv_id, e)
        log_event("api_gateway", "ERROR", f"[CV {cv_id}] Ошибка в фоновом конвейере доработки: {e}")
        try:
            await db_client.update_cv_status(cv_id, CVStatus.ERROR.value)
        except Exception as update_err:
            logger.error("[CV %s] Не удалось перевести резюме в статус ошибки: %s", cv_id, update_err, exc_info=True)


@router.post("/upload", response_model=CVUploadResponse, status_code=status.HTTP_200_OK)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    hr_id: Optional[int] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ФТ-HR.2: Неблокирующая загрузка CV. Валидирует файл, создает черновик в БД
    в начальном статусе 'Загружено', запускает асинхронный пайплайн в фоновом режиме
    и мгновенно возвращает ответ клиенту (HTTP 200/202).
    """
    filename = file.filename or "cv_document"
    effective_hr_id = hr_id or current_user.get("hr_id")

    log_event("api_gateway", "INFO", f"Принят запрос на загрузку резюме '{filename}' от HR_ID={effective_hr_id}")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Файл резюме пуст")

    clean_name = filename.rsplit(".", 1)[0].replace("_", " ")
    init_jsonb = {
        "fio": clean_name,
        "vacancy": "ИИ-структурирование резюме...",
        "skills_and_tools": [],
        "education": [],
        "projects": [],
    }
    init_cv_payload = {
        "hr_id": effective_hr_id,
        "jsonb": init_jsonb,
        "status": CVStatus.UPLOADED.value,
    }

    cv_record = await db_client.create_cv(init_cv_payload)
    cv_id = cv_record["cv_id"]

    # Запуск фонового пайплайна
    background_tasks.add_task(
        run_upload_pipeline,
        cv_id=cv_id,
        effective_hr_id=effective_hr_id,
        filename=filename,
        file_bytes=file_bytes,
    )

    log_event("api_gateway", "INFO", f"[CV {cv_id}] Запись создана в статусе '{CVStatus.UPLOADED.value}'. Фоновая обработка запланирована.")
    return CVUploadResponse(
        cv_id=cv_id,
        hr_id=effective_hr_id,
        status=CVStatus.UPLOADED.value,
        data=init_jsonb,
        filename=filename,
    )


@router.put("/{cv_id}/validate", response_model=CVValidateResponse)
async def validate_and_generate_docx(
    cv_id: int,
    validated_json: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ФТ-HR.3 + ФТ-HR.4: Подтверждение проверенного HR-специалистом JSON,
    сохранение в БД, вызов JSONToWord для генерации .docx, загрузка в S3
    и перевод резюме в финальный статус 'Готово'.
    """
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Получен подтвержденный JSON от HR. Начинаем валидацию и генерацию docx")

    cv_record = await db_client.get_cv(cv_id)
    if not cv_record:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")

    # 1. Переводим статус в "Формирование docx" и обновляем JSONB
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Переход в статус: {CVStatus.DOCX_GENERATION.value}")
    await db_client.update_cv(cv_id, {"jsonb": validated_json, "status": CVStatus.DOCX_GENERATION.value})

    # 2. Вызов сервиса JSONToWord (docxtpl)
    docx_bytes = await word_client.generate(validated_json)

    # 3. Сохранение файла в хранилище S3 через DBConnector
    fio_slug = validated_json.get("fio", "candidate").replace(" ", "_")
    object_key = f"resumes/cv_{cv_id}_{fio_slug}.docx"
    storage_data = await db_client.upload_storage_file(object_name=object_key, file_bytes=docx_bytes)
    docx_url_or_key = storage_data.get("url_or_path", object_key)

    # 4. Фиксация статуса "Готово" и ключа Docx в БД
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Документ сохранен в S3. Переход в статус: {CVStatus.READY.value}")
    await db_client.update_cv_docx(cv_id, docx_key=object_key, status=CVStatus.READY.value)

    download_url = f"/api/v1/cv/{cv_id}/download"

    return CVValidateResponse(
        cv_id=cv_id,
        hr_id=cv_record["hr_id"],
        status=CVStatus.READY.value,
        docx_url=docx_url_or_key,
        download_url=download_url,
        data=validated_json,
    )


@router.put("/{cv_id}/rework")
async def return_cv_for_rework(
    cv_id: int,
    req: Optional[ReworkRequest] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ФТ-HR.3: Возврат резюме на доработку при обнаружении ошибок/неточностей.
    Переводит резюме в статус 'Обработка резюме' и запускает фоновый процесс пересоздания с учетом замечаний HR.
    """
    comment = req.comment if req else None
    comment_str = f" Замечания HR: '{comment}'" if comment else ""
    log_event("api_gateway", "WARNING", f"[CV {cv_id}] HR вернул резюме на доработку (Найдены ошибки).{comment_str} Переход в статус: {CVStatus.LLM_PROCESSING.value}")

    await db_client.update_cv_status(cv_id, CVStatus.LLM_PROCESSING.value)

    # Запускаем фоновый процесс пересоздания
    asyncio.create_task(run_rework_pipeline(cv_id, comment))

    return {
        "cv_id": cv_id,
        "status": CVStatus.LLM_PROCESSING.value,
        "message": "Резюме возвращено на доработку, запущен повторный парсинг ИИ",
        "comment": comment,
    }


@router.put("/{cv_id}/draft")
async def save_cv_draft(
    cv_id: int,
    draft_json: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ФТ-HR.3: Сохранение промежуточного черновика JSON HR-специалистом без генерации DOCX.
    """
    log_event("api_gateway", "INFO", f"[CV {cv_id}] Сохранение черновика HR")
    await db_client.update_cv(cv_id, {"jsonb": draft_json, "status": CVStatus.AWAITING_HR.value})
    return {"cv_id": cv_id, "status": CVStatus.AWAITING_HR.value, "message": "Черновик успешно сохранен"}


@router.get("/{cv_id}", response_model=CVDetailResponse)
async def get_cv(
    cv_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Получение данных резюме, статуса и ссылки на готовый .docx.
    """
    cv_record = await db_client.get_cv(cv_id)
    if not cv_record:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")

    download_url = f"/api/v1/cv/{cv_id}/download" if cv_record.get("docx") else None
    return CVDetailResponse(
        cv_id=cv_record["cv_id"],
        hr_id=cv_record["hr_id"],
        status=cv_record["status"],
        jsonb=cv_record["jsonb"],
        docx=cv_record["docx"],
        download_url=download_url,
    )


@router.get("/{cv_id}/download")
async def download_cv_docx(
    cv_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Скачивание сгенерированного корпоративного документа .docx из S3.
    """
    cv_record = await db_client.get_cv(cv_id)
    if not cv_record:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {cv_id} не найдено")

    docx_key = cv_record.get("docx")
    if not docx_key:
        raise HTTPException(status_code=400, detail="Файл .docx для данного резюме еще не сгенерирован")

    content = await db_client.download_storage_file(docx_key)

    filename = docx_key.split("/")[-1]
    ascii_filename = "".join(c for c in filename if c.isascii() and (c.isalnum() or c in "._-")) or "resume.docx"
    disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}'
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": disposition},
    )


@router.get("", response_model=List[CVDetailResponse])
async def list_cvs(
    hr_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Получение списка резюме (с фильтром по HR-специалисту).
    """
    items = await db_client.list_cvs(hr_id=hr_id, skip=skip, limit=limit)
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
