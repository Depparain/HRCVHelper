from __future__ import annotations

import logging
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings, get_cached_prompt_files, get_tech_dictionary
from .schemas import ParseRequest, ParseResponse, HealthResponse
from .parser import parse_cv_with_llm, check_ollama_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_convertor")

_LOG_BUFFER: deque[dict] = deque(maxlen=200)

class InMemoryLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "service": "llm_convertor",
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
    prompts, _ = get_cached_prompt_files()
    tech_dict = get_tech_dictionary()
    logger.info(
        "LLMConvertor инициализирован. Загружено технологий в словарь: %d, размер системного промпта: %d байт",
        len(tech_dict),
        len(prompts),
    )
    yield


app = FastAPI(
    title="HRCVHelper - LLMConvertor Service",
    version="1.0.0",
    description="Микросервис семантического парсинга Markdown в структурированный JSON (Ollama / Gemma-3, 152-ФЗ)",
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
async def health_check():
    ollama_ok = await check_ollama_health()
    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama_connected=ollama_ok,
        model=settings.ollama_model,
    )


@app.get("/internal/logs")
def get_internal_logs(limit: int = 100):
    """Внутренний эндпоинт буферизированных системных логов (TASK-3.4)."""
    return {"service": "llm_convertor", "logs": list(_LOG_BUFFER)[:limit]}


@app.post("/parse", response_model=ParseResponse)
async def parse_cv(req: ParseRequest):
    markdown = (req.markdown or "").strip()
    if not markdown and req.cv_data:
        from .parser import reconstruct_markdown_from_cv
        markdown = reconstruct_markdown_from_cv(req.cv_data)

    if not markdown:
        raise HTTPException(status_code=400, detail="Текст Markdown или данные резюме не переданы")

    cv_data, source = await parse_cv_with_llm(
        markdown=markdown,
        filename=req.original_filename,
        force_dynamic=req.force_dynamic,
        rework_comment=req.rework_comment,
    )
    return ParseResponse(
        data=cv_data,
        source=source,
        status="ok",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.service_host, port=settings.service_port)
