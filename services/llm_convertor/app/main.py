from __future__ import annotations

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import ParseRequest, ParseResponse, HealthResponse
from .parser import parse_cv_with_llm, check_ollama_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_convertor")

app = FastAPI(
    title="HRCVHelper - LLMConvertor Service",
    version="1.0.0",
    description="Микросервис семантического парсинга Markdown в структурированный JSON (Ollama / Gemma-3, 152-ФЗ)",
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


@app.post("/parse", response_model=ParseResponse)
async def parse_cv(req: ParseRequest):
    if not req.markdown.strip():
        raise HTTPException(status_code=400, detail="Текст Markdown пуст")

    cv_data, source = await parse_cv_with_llm(req.markdown, req.original_filename, req.force_dynamic)
    return ParseResponse(
        data=cv_data,
        source=source,
        status="ok",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.service_host, port=settings.service_port)
