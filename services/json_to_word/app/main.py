from __future__ import annotations

import json
import logging
import tempfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Response, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Импортируем готовый модуль генерации (поддержка как локального пакета, так и Docker контейнера)
try:
    from ..json_to_docx import generate_cv
except (ImportError, ValueError):
    from json_to_docx import generate_cv

try:
    from .template_manager import TemplateManager
except (ImportError, ValueError):
    from template_manager import TemplateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("json_to_word")

_LOG_BUFFER: deque[dict] = deque(maxlen=200)

class InMemoryLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "service": "json_to_word",
                "message": self.format(record),
            }
            _LOG_BUFFER.appendleft(entry)
        except Exception:
            self.handleError(record)

_log_handler = InMemoryLogHandler()
_log_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(_log_handler)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "template" / "placeholders_cv_docx.docx"
STYLE_PATH = BASE_DIR / "template" / "style.json"

app = FastAPI(
    title="HRCVHelper - JSONToWord Service",
    version="1.0.0",
    description="Микросервис сборки корпоративного .docx-документа по шаблону (docxtpl)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    template_exists: bool
    style_exists: bool


@app.get("/health", response_model=HealthResponse)
def health_check():
    tpl_ok = TEMPLATE_PATH.exists()
    style_ok = STYLE_PATH.exists()
    return HealthResponse(
        status="ok" if (tpl_ok and style_ok) else "degraded",
        template_exists=tpl_ok,
        style_exists=style_ok,
    )


@app.get("/internal/logs")
def get_internal_logs(limit: int = 100):
    """Внутренний эндпоинт буферизированных системных логов (TASK-3.4)."""
    return {"service": "json_to_word", "logs": list(_LOG_BUFFER)[:limit]}


# --- Endpoints управления шаблонами DOCX ---

@app.get("/templates")
def get_templates():
    """Возвращает список всех доступных шаблонов (системный и пользовательские)."""
    return {"templates": TemplateManager.list_templates()}


@app.post("/templates/upload")
async def upload_template(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    make_active: bool = Form(False),
):
    """Загружает новый пользовательский .docx шаблон."""
    content = await file.read()
    try:
        tpl_info = TemplateManager.save_custom_template(
            filename=file.filename or "template.docx",
            content=content,
            name=name,
            description=description,
            make_active=make_active,
        )
        return tpl_info
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Ошибка сохранения шаблона: %s", e)
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения шаблона: {e}")


@app.get("/templates/{template_id}/download")
def download_template(template_id: str):
    """Скачивание файла шаблона .docx (системного или пользовательского)."""
    try:
        content, filename = TemplateManager.get_template_bytes(template_id)
        ascii_filename = "".join(c for c in filename if c.isascii() and (c.isalnum() or c in "._-")) or "template.docx"
        disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}'
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": disposition, "X-Filename": quote(filename)},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/templates/{template_id}/set-default")
def set_default_template(template_id: str):
    """Делает указанный шаблон активным по умолчанию."""
    try:
        TemplateManager.set_active_template(template_id)
        return {"status": "ok", "active_template_id": template_id}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.delete("/templates/{template_id}")
def delete_template(template_id: str):
    """Удаляет пользовательский шаблон (системный удалить нельзя)."""
    try:
        success = TemplateManager.delete_custom_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        return {"status": "ok", "message": f"Шаблон {template_id} успешно удален"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.post("/generate")
async def generate_document(payload: Dict[str, Any], template_id: Optional[str] = Query(None)):
    """
    Принимает JSON-структуру резюме кандидата,
    вызывает генератор docxtpl по выбранному или активному шаблону
    и возвращает готовый бинарный .docx-файл.
    """
    selected_template_id = template_id or payload.get("template_id")
    cv_data = payload.get("data") if (isinstance(payload.get("data"), dict) and "fio" in payload.get("data", {})) else payload

    try:
        template_path = TemplateManager.get_template_path(selected_template_id)
    except Exception as e:
        logger.warning("Не удалось разрешить шаблон %s: %s, используется стандартный", selected_template_id, e)
        template_path = TEMPLATE_PATH

    if not template_path.exists():
        raise HTTPException(status_code=500, detail=f"Шаблон DOCX не найден по пути: {template_path}")

    try:
        # Создаем временный файл JSON и выходной файл DOCX
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tmp_json:
            json.dump(cv_data, tmp_json, ensure_ascii=False, indent=2)
            tmp_json_path = Path(tmp_json.name)

        output_docx_path = tmp_json_path.with_suffix(".docx")

        try:
            logger.info("Генерация DOCX для кандидата: %s (шаблон: %s)", cv_data.get("fio", "Кандидат"), template_path.name)
            generate_cv(
                json_path=tmp_json_path,
                template_path=template_path,
                output_path=output_docx_path,
            )

            docx_bytes = output_docx_path.read_bytes()
            fio_slug = cv_data.get("fio", "candidate").replace(" ", "_")
            ascii_fio = "".join(c for c in fio_slug if c.isascii() and (c.isalnum() or c in "_-")) or "candidate"
            filename = f"CV_{ascii_fio}.docx"
            utf8_filename = f"CV_{fio_slug}.docx"

            # Стандарт RFC 5987 для безопасной передачи кириллических имен файлов в HTTP-заголовках
            disposition = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{quote(utf8_filename)}'

            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": disposition,
                    "X-Filename": quote(utf8_filename),
                },
            )
        finally:
            tmp_json_path.unlink(missing_ok=True)
            output_docx_path.unlink(missing_ok=True)

    except Exception as e:
        logger.error("Ошибка при генерации DOCX: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка генерации документа: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
