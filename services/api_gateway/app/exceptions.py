from __future__ import annotations

import logging
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .logger_collector import log_event

logger = logging.getLogger("api_gateway.exceptions")


def _cors_headers(request: Request, extra_headers: Optional[dict] = None) -> dict:
    headers = dict(extra_headers or {})
    origin = request.headers.get("origin")
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
    return headers


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        incident_id = uuid.uuid4().hex[:12]
        logger.warning("HTTPException [%s] %s %s: %s", incident_id, request.method, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "code": exc.status_code,
                "detail": exc.detail,
                "incident_id": incident_id,
                "path": request.url.path,
            },
            headers=_cors_headers(request, exc.headers),
        )

    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
        incident_id = uuid.uuid4().hex[:12]
        logger.warning("ValidationError [%s] %s %s: %s", incident_id, request.method, request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "code": 422,
                "detail": "Ошибка валидации входных данных",
                "errors": exc.errors(),
                "incident_id": incident_id,
                "path": request.url.path,
            },
            headers=_cors_headers(request),
        )

    @app.exception_handler(Exception)
    async def custom_unhandled_exception_handler(request: Request, exc: Exception):
        incident_id = uuid.uuid4().hex[:12]
        logger.exception("Unhandled Exception [%s] %s %s: %s", incident_id, request.method, request.url.path, exc)
        log_event("api_gateway", "CRITICAL", f"Критический сбой [{incident_id}] на {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "code": 500,
                "detail": f"Внутренняя системная ошибка (ID инцидента: {incident_id})",
                "incident_id": incident_id,
                "path": request.url.path,
            },
            headers=_cors_headers(request),
        )
