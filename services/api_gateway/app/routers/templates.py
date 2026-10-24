from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from ..clients.db_client import db_client
from ..clients.service_clients import word_client
from ..dependencies import get_current_user
from ..logger_collector import log_event

logger = logging.getLogger("api_gateway.routers.templates")
router = APIRouter(prefix="/api/v1/templates", tags=["Templates & Schema Customization"])

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
FIELDS_CONFIG_PATH = CONFIG_DIR / "fields_config.json"

DEFAULT_FIELDS: List[Dict[str, Any]] = [
    {
        "key": "fio",
        "name": "ФИО кандидата",
        "category": "personal",
        "category_name": "Личные данные и статус",
        "tag": "{{ fio }}",
        "type": "string",
        "description": "Полное имя кандидата в именительном падеже",
        "enabled": True,
        "sample": "Иванов Иван Иванович",
    },
    {
        "key": "vacancy",
        "name": "Желаемая должность / позиция",
        "category": "personal",
        "category_name": "Личные данные и статус",
        "tag": "{{ vacancy }}",
        "type": "string",
        "description": "Целевая инженерная или управленческая роль",
        "enabled": True,
        "sample": "Senior Python Developer / Team Lead",
    },
    {
        "key": "total_year_work",
        "name": "Общий стаж работы",
        "category": "personal",
        "category_name": "Личные данные и статус",
        "tag": "{{ total_year_work }}",
        "type": "string",
        "description": "Суммарный опыт работы с точным склонением (X ЛЕТ Y МЕСЯЦЕВ)",
        "enabled": True,
        "sample": "7 ЛЕТ 4 МЕСЯЦА",
    },
    {
        "key": "citizenship_location",
        "name": "Город / Гражданство",
        "category": "personal",
        "category_name": "Личные данные и статус",
        "tag": "{{ citizenship_location }}",
        "type": "string",
        "description": "Город фактического нахождения и гражданство соискателя",
        "enabled": True,
        "sample": "Москва, Россия (гражданство РФ)",
    },
    {
        "key": "employment",
        "name": "Формат занятости",
        "category": "personal",
        "category_name": "Личные данные и статус",
        "tag": "{{ employment }}",
        "type": "string",
        "description": "Предпочитаемый график (полная занятость, удаленка, гибрид)",
        "enabled": True,
        "sample": "Полная занятость, удаленная работа",
    },
    {
        "key": "status",
        "name": "Готовность к переезду",
        "category": "personal",
        "category_name": "Личные данные и статус",
        "tag": "{{ status }}",
        "type": "string",
        "description": "Готовность к релокации или командировкам",
        "enabled": True,
        "sample": "Готов к переезду",
    },
    {
        "key": "pitch",
        "name": "Elevator Pitch / Саммари",
        "category": "competencies",
        "category_name": "Квалификация и ключевые навыки",
        "tag": "{{ pitch }}",
        "type": "string",
        "description": "Краткая выжимка опыта кандидата от 3-го лица без местоимения «Я»",
        "enabled": True,
        "sample": "Инженер с 7+ годами опыта проектирования распределенных микросервисных архитектур...",
    },
    {
        "key": "skills_and_tools",
        "name": "Ключевые навыки и стек",
        "category": "competencies",
        "category_name": "Квалификация и ключевые навыки",
        "tag": "{{ skills_tools }}",
        "type": "list",
        "description": "Глобальный стек технологий (Python, Docker, FastAPI, PostgreSQL...)",
        "enabled": True,
        "sample": "Python, FastAPI, Docker, PostgreSQL, Redis, Kafka, Kubernetes",
    },
    {
        "key": "project_backround",
        "name": "Проектный бэкграунд / Отрасли",
        "category": "competencies",
        "category_name": "Квалификация и ключевые навыки",
        "tag": "{{ project_backround }}",
        "type": "string",
        "description": "Сферы деятельности проектов (Финтех, Банки, E-commerce, Телеком)",
        "enabled": True,
        "sample": "Финтех, Банковская сфера, E-commerce",
    },
    {
        "key": "languages",
        "name": "Иностранные языки",
        "category": "competencies",
        "category_name": "Квалификация и ключевые навыки",
        "tag": "{{ languages }}",
        "type": "string",
        "description": "Уровень владения языками (Русский родной, Английский A2-C1)",
        "enabled": True,
        "sample": "Русский — Родной, Английский — B2",
    },
    {
        "key": "projects",
        "name": "Опыт работы и проекты (весь блок)",
        "category": "experience",
        "category_name": "Опыт работы и проекты",
        "tag": "{% for p in projects %} ... {% endfor %}",
        "type": "array_of_objects",
        "description": "Хронологическая история проектов и мест работы кандидата",
        "enabled": True,
        "sample": "Массив проектов с ролями, задачами, достижениями и стеком",
    },
    {
        "key": "project_role",
        "name": "Роль на проекте",
        "category": "experience",
        "category_name": "Опыт работы и проекты",
        "tag": "{{ p.role_in_project }}",
        "type": "string",
        "parent_key": "projects",
        "description": "Должность или позиция на конкретном месте работы",
        "enabled": True,
        "sample": "Lead Backend Developer",
    },
    {
        "key": "project_period",
        "name": "Период и компания",
        "category": "experience",
        "category_name": "Опыт работы и проекты",
        "tag": "{{ p.project_place_and_work_time }}",
        "type": "string",
        "parent_key": "projects",
        "description": "Название организации и временной интервал работы",
        "enabled": True,
        "sample": "ООО «Технологии будущего» (01.2021 — 05.2024)",
    },
    {
        "key": "project_tasks",
        "name": "Задачи на проекте",
        "category": "experience",
        "category_name": "Опыт работы и проекты",
        "tag": "{% for t in p.task_on_project %}• {{ t }}{% endfor %}",
        "type": "list",
        "parent_key": "projects",
        "description": "Список инженерных и организационных задач",
        "enabled": True,
        "sample": "Проектирование высоконагруженных API, рефакторинг legacy-монолита",
    },
    {
        "key": "project_achievements",
        "name": "Достижения на проекте",
        "category": "experience",
        "category_name": "Опыт работы и проекты",
        "tag": "{% for a in p.achievements_in_project %}• {{ a }}{% endfor %}",
        "type": "list",
        "parent_key": "projects",
        "description": "Измеримые результаты (сократил издержки, ускорил запросы)",
        "enabled": True,
        "sample": "Снизил p99 latency на 40%, сократил время сборки релизов в 2 раза",
    },
    {
        "key": "project_skills",
        "name": "Стек технологий проекта",
        "category": "experience",
        "category_name": "Опыт работы и проекты",
        "tag": "{{ p.skills_tools_in_project }}",
        "type": "string",
        "parent_key": "projects",
        "description": "Инструменты и библиотеки, примененные в проекте",
        "enabled": True,
        "sample": "Python 3.11, FastAPI, Kafka, Redis, PostgreSQL, Helm",
    },
    {
        "key": "education",
        "name": "Высшее образование",
        "category": "education",
        "category_name": "Образование и курсы",
        "tag": "{{ education }}",
        "type": "list_or_string",
        "description": "Базовые учебные заведения, квалификация и годы окончания",
        "enabled": True,
        "sample": "2020, МГТУ им. Н.Э. Баумана, Информационные системы и технологии",
    },
    {
        "key": "advanced_training",
        "name": "Курсы и сертификаты",
        "category": "education",
        "category_name": "Образование и курсы",
        "tag": "{% for c in courses %}• {{ c }}{% endfor %}",
        "type": "list",
        "description": "Дополнительное профессиональное обучение, повышение квалификации",
        "enabled": True,
        "sample": "2023, Deep Learning Specialization (Coursera)",
    },
]


def _load_saved_fields_config() -> Dict[str, bool]:
    if not FIELDS_CONFIG_PATH.exists():
        return {item["key"]: bool(item.get("enabled", True)) for item in DEFAULT_FIELDS}
    try:
        with FIELDS_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Ошибка чтения fields_config.json: %s", e)
        return {item["key"]: bool(item.get("enabled", True)) for item in DEFAULT_FIELDS}


def _save_fields_config(config: Dict[str, bool]) -> None:
    try:
        with FIELDS_CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка записи fields_config.json: %s", e)


@router.get("", response_model=Dict[str, Any])
async def list_templates(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Получение списка доступных шаблонов .docx из базы данных PostgreSQL (с fallback на word_client).
    """
    templates = await db_client.list_templates()
    if not templates:
        templates = await word_client.list_templates()
    return {"templates": templates}


@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    make_active: bool = Form(False),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Загрузка нового корпоративного шаблона Word (.docx) в базу данных PostgreSQL.
    """
    content = await file.read()
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Поддерживаются только файлы с расширением .docx")

    log_event("api_gateway", "INFO", f"HR {current_user.get('login')} сохраняет шаблон DOCX в БД: '{name or file.filename}'")
    hr_id = current_user.get("hr_id")
    try:
        tpl = await db_client.upload_template(
            file_bytes=content,
            filename=file.filename,
            name=name,
            description=description,
            make_active=make_active,
            hr_id=hr_id,
        )
    except Exception as e:
        logger.warning("Ошибка сохранения в DBConnector: %s, fallback на локальный менеджер", e)
        tpl = await word_client.upload_template(
            file_bytes=content,
            filename=file.filename,
            name=name,
            description=description,
            make_active=make_active,
        )

    # Синхронизируем локальный кэш json_to_word
    try:
        await word_client.upload_template(
            file_bytes=content,
            filename=file.filename,
            name=name,
            description=description,
            make_active=make_active,
        )
    except Exception:
        pass

    return tpl


@router.get("/{template_id}/download")
async def download_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Скачивание файла шаблона .docx из базы данных PostgreSQL.
    """
    try:
        content, filename = await db_client.download_template(template_id)
    except Exception:
        content, filename = await word_client.download_template(template_id)

    ascii_filename = "".join(c for c in filename if c.isascii() and (c.isalnum() or c in "._-")) or "template.docx"
    disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}'

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": disposition, "X-Filename": quote(filename)},
    )


@router.post("/{template_id}/set-default")
async def set_active_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Назначение шаблона активным по умолчанию в базе данных PostgreSQL.
    """
    log_event("api_gateway", "INFO", f"HR {current_user.get('login')} установил активный шаблон в БД: {template_id}")
    try:
        res = await db_client.set_active_template(template_id)
    except Exception:
        res = await word_client.set_active_template(template_id)

    try:
        await word_client.set_active_template(template_id)
    except Exception:
        pass

    return res


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Удаление пользовательского шаблона из базы данных PostgreSQL.
    """
    log_event("api_gateway", "WARNING", f"HR {current_user.get('login')} удаляет шаблон из БД: {template_id}")
    try:
        res = await db_client.delete_template(template_id)
    except Exception:
        res = await word_client.delete_template(template_id)

    try:
        await word_client.delete_template(template_id)
    except Exception:
        pass

    return res


@router.get("/fields", response_model=Dict[str, Any])
async def get_fields_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Возвращает спецификацию всех доступных полей извлечения резюме (JSON Contract) из базы данных PostgreSQL.
    """
    saved_config = await db_client.get_fields_config()
    if not saved_config:
        saved_config = _load_saved_fields_config()

    fields = []
    for item in DEFAULT_FIELDS:
        f_copy = dict(item)
        f_copy["enabled"] = saved_config.get(item["key"], item.get("enabled", True))
        fields.append(f_copy)

    enabled_count = sum(1 for f in fields if f["enabled"])
    return {
        "total_fields": len(fields),
        "enabled_count": enabled_count,
        "fields": fields,
    }


@router.post("/fields")
async def save_fields_config(
    payload: Dict[str, bool],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Сохраняет конфигурацию активных полей извлечения резюме в базу данных PostgreSQL.
    """
    log_event("api_gateway", "INFO", f"HR {current_user.get('login')} обновил конфигурацию полей резюме в БД")
    hr_id = current_user.get("hr_id")
    try:
        await db_client.save_fields_config(payload, hr_id=hr_id)
    except Exception as e:
        logger.warning("Не удалось сохранить в БД: %s, пишем локально", e)

    _save_fields_config(payload)
    return {"status": "ok", "message": "Конфигурация полей успешно сохранена в базе данных", "saved_fields": payload}
