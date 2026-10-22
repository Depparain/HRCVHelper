from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .converter import convert_file_to_markdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("md_convertor")

_LOG_BUFFER: deque[dict] = deque(maxlen=200)

class InMemoryLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "service": "md_convertor",
                "message": self.format(record),
            }
            _LOG_BUFFER.appendleft(entry)
        except Exception:
            self.handleError(record)

_log_handler = InMemoryLogHandler()
_log_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(_log_handler)

app = FastAPI(
    title="HRCVHelper - MDConvertor Service",
    version="1.0.0",
    description="Микросервис преобразования документов резюме в Markdown (MarkItDown)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConvertResponse(BaseModel):
    markdown: str
    filename: str
    status: str = "ok"


class HealthResponse(BaseModel):
    status: str
    service: str = "md_convertor"


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok")


@app.get("/internal/logs")
def get_internal_logs(limit: int = 100):
    """Внутренний эндпоинт буферизированных системных логов (TASK-3.4)."""
    return {"service": "md_convertor", "logs": list(_LOG_BUFFER)[:limit]}


@app.post("/convert", response_model=ConvertResponse)
async def convert_file(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_resume"
    logger.info("Получен файл для конвертации в MD: %s", filename)

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Загруженный файл пуст")

        markdown_text = convert_file_to_markdown(contents, filename)
        if not markdown_text.strip():
            raise HTTPException(status_code=422, detail="Не удалось извлечь текст из документа")

        return ConvertResponse(
            markdown=markdown_text,
            filename=filename,
            status="ok",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка конвертации файла: %s", e)
        raise HTTPException(status_code=500, detail=f"Ошибка конвертации в Markdown: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
