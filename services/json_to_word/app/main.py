from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Импортируем готовый модуль генерации (поддержка как локального пакета, так и Docker контейнера)
try:
    from ..json_to_docx import generate_cv
except (ImportError, ValueError):
    from json_to_docx import generate_cv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("json_to_word")

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


@app.post("/generate")
async def generate_document(payload: Dict[str, Any]):
    """
    Принимает JSON-структуру резюме кандидата,
    вызывает генератор docxtpl по шаблону
    и возвращает готовый бинарный .docx-файл.
    """
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Шаблон DOCX не найден по пути: {TEMPLATE_PATH}")

    try:
        # Создаем временный файл JSON и выходной файл DOCX
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tmp_json:
            json.dump(payload, tmp_json, ensure_ascii=False, indent=2)
            tmp_json_path = Path(tmp_json.name)

        output_docx_path = tmp_json_path.with_suffix(".docx")

        try:
            logger.info("Генерация DOCX для кандидата: %s", payload.get("fio", "Кандидат"))
            generate_cv(
                json_path=tmp_json_path,
                template_path=TEMPLATE_PATH,
                output_path=output_docx_path,
            )

            docx_bytes = output_docx_path.read_bytes()
            fio_slug = payload.get("fio", "candidate").replace(" ", "_")
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
