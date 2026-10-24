from __future__ import annotations

import json
import logging
import os
import re
import uuid
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("json_to_word.template_manager")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "template"
CUSTOM_DIR = TEMPLATE_DIR / "custom"
META_FILE = TEMPLATE_DIR / "templates_meta.json"
DEFAULT_TEMPLATE_PATH = TEMPLATE_DIR / "placeholders_cv_docx.docx"

# Обеспечиваем существование каталога для пользовательских шаблонов
CUSTOM_DIR.mkdir(parents=True, exist_ok=True)


def _load_meta() -> Dict[str, Any]:
    if not META_FILE.exists():
        initial_meta = {
            "active_template_id": "default",
            "templates": {
                "default": {
                    "id": "default",
                    "name": "Классический корпоративный шаблон (Системный)",
                    "description": "Стандартный двухколоночный корпоративный шаблон HRCVHelper с полной поддержкой всех полей",
                    "filename": "placeholders_cv_docx.docx",
                    "is_system": True,
                    "created_at": "2026-10-21T00:00:00Z",
                }
            },
        }
        _save_meta(initial_meta)
        return initial_meta

    try:
        with META_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Ошибка чтения templates_meta.json: %s", e)
        return {"active_template_id": "default", "templates": {}}


def _save_meta(meta: Dict[str, Any]) -> None:
    try:
        with META_FILE.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка записи templates_meta.json: %s", e)


def is_valid_docx(content: bytes) -> bool:
    """Проверяет, является ли байтовый поток валидным файлом Microsoft Word (.docx)."""
    try:
        with zipfile.ZipFile(BytesIO(content)) as zf:
            namelist = zf.namelist()
            return "word/document.xml" in namelist or "[Content_Types].xml" in namelist
    except Exception:
        return False


class TemplateManager:
    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        meta = _load_meta()
        active_id = meta.get("active_template_id", "default")
        result: List[Dict[str, Any]] = []

        # 1. Системный дефолтный шаблон
        default_size = DEFAULT_TEMPLATE_PATH.stat().st_size if DEFAULT_TEMPLATE_PATH.exists() else 0
        default_item = {
            "id": "default",
            "name": "Классический корпоративный шаблон",
            "description": "Базовый фирменный шаблон резюме с блочной структурой и табличной сеткой",
            "filename": "placeholders_cv_docx.docx",
            "is_system": True,
            "is_active": (active_id == "default"),
            "size_bytes": default_size,
            "created_at": "2026-10-21T12:00:00Z",
        }
        result.append(default_item)

        # 2. Пользовательские шаблоны
        templates_dict = meta.get("templates", {})
        for t_id, item in templates_dict.items():
            if t_id == "default":
                continue
            file_path = CUSTOM_DIR / item.get("saved_filename", "")
            if not file_path.exists():
                continue

            size_bytes = file_path.stat().st_size if file_path.exists() else 0
            result.append(
                {
                    "id": t_id,
                    "name": item.get("name", file_path.stem),
                    "description": item.get("description", "Пользовательский шаблон Word (.docx)"),
                    "filename": item.get("filename", file_path.name),
                    "is_system": False,
                    "is_active": (active_id == t_id),
                    "size_bytes": size_bytes,
                    "created_at": item.get("created_at", datetime.now(timezone.utc).isoformat()),
                }
            )

        return result

    @classmethod
    def get_template_path(cls, template_id: Optional[str] = None) -> Path:
        meta = _load_meta()
        target_id = template_id or meta.get("active_template_id", "default")

        if target_id == "default":
            if DEFAULT_TEMPLATE_PATH.exists():
                return DEFAULT_TEMPLATE_PATH
            raise FileNotFoundError(f"Системный шаблон не найден: {DEFAULT_TEMPLATE_PATH}")

        templates = meta.get("templates", {})
        item = templates.get(target_id)
        if item:
            saved_name = item.get("saved_filename")
            if saved_name:
                custom_path = CUSTOM_DIR / saved_name
                if custom_path.exists():
                    return custom_path

        # Если запрошенный не найден, возвращаем системный по умолчанию
        logger.warning("Шаблон с ID '%s' не найден, используется дефолтный шаблон", target_id)
        if DEFAULT_TEMPLATE_PATH.exists():
            return DEFAULT_TEMPLATE_PATH
        raise FileNotFoundError(f"Файл шаблона не найден для ID: {target_id}")

    @classmethod
    def save_custom_template(
        cls,
        filename: str,
        content: bytes,
        name: Optional[str] = None,
        description: Optional[str] = None,
        make_active: bool = False,
    ) -> Dict[str, Any]:
        if not is_valid_docx(content):
            raise ValueError("Переданный файл не является корректным документом Microsoft Word (.docx)")

        template_id = str(uuid.uuid4())[:8]
        safe_name = re.sub(r"[^\w\.-]", "_", filename)
        if not safe_name.lower().endswith(".docx"):
            safe_name += ".docx"

        saved_filename = f"{template_id}_{safe_name}"
        save_path = CUSTOM_DIR / saved_filename
        save_path.write_bytes(content)

        meta = _load_meta()
        display_name = name.strip() if name and name.strip() else Path(filename).stem
        display_desc = description.strip() if description and description.strip() else "Пользовательский шаблон HR"

        now_iso = datetime.now(timezone.utc).isoformat()
        meta["templates"][template_id] = {
            "id": template_id,
            "name": display_name,
            "description": display_desc,
            "filename": filename,
            "saved_filename": saved_filename,
            "is_system": False,
            "created_at": now_iso,
        }

        if make_active:
            meta["active_template_id"] = template_id

        _save_meta(meta)
        logger.info("Успешно сохранен новый шаблон: id=%s, name='%s'", template_id, display_name)

        return {
            "id": template_id,
            "name": display_name,
            "description": display_desc,
            "filename": filename,
            "is_system": False,
            "is_active": (meta.get("active_template_id") == template_id),
            "size_bytes": len(content),
            "created_at": now_iso,
        }

    @classmethod
    def set_active_template(cls, template_id: str) -> bool:
        meta = _load_meta()
        if template_id != "default" and template_id not in meta.get("templates", {}):
            raise ValueError(f"Шаблон с ID '{template_id}' не зарегистрирован")

        meta["active_template_id"] = template_id
        _save_meta(meta)
        logger.info("Активным шаблоном назначен ID: %s", template_id)
        return True

    @classmethod
    def delete_custom_template(cls, template_id: str) -> bool:
        if template_id == "default":
            raise ValueError("Нельзя удалить базовый системный шаблон")

        meta = _load_meta()
        templates = meta.get("templates", {})
        if template_id not in templates:
            return False

        item = templates.pop(template_id)
        saved_name = item.get("saved_filename")
        if saved_name:
            file_path = CUSTOM_DIR / saved_name
            file_path.unlink(missing_ok=True)

        if meta.get("active_template_id") == template_id:
            meta["active_template_id"] = "default"

        _save_meta(meta)
        logger.info("Удален пользовательский шаблон ID: %s", template_id)
        return True

    @classmethod
    def get_template_bytes(cls, template_id: str) -> Tuple[bytes, str]:
        path = cls.get_template_path(template_id)
        meta = _load_meta()
        if template_id == "default":
            filename = "placeholders_cv_docx.docx"
        else:
            item = meta.get("templates", {}).get(template_id, {})
            filename = item.get("filename", path.name)
        return path.read_bytes(), filename
