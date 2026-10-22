from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .exceptions import setup_exception_handlers
from .logger_collector import setup_in_memory_logging, log_event
from .routers.admin import router as admin_router
from .routers.auth import router as auth_router
from .routers.resumes import router as resumes_router

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

# Подключение глобальных обработчиков ошибок
setup_exception_handlers(app)

# Подключение модульных роутеров
app.include_router(auth_router)
app.include_router(resumes_router)
app.include_router(admin_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.gateway_host, port=settings.gateway_port)
