from __future__ import annotations

import logging
from fastapi import APIRouter
from ..clients.service_clients import auth_client
from ..logger_collector import log_event
from ..schemas import LoginRequest, LoginResponse

logger = logging.getLogger("api_gateway.routers.auth")
router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    ФТ-HR.1: Авторизация HR-специалиста.
    Перенаправляет запрос в AuthSystem, возвращает токен сессии и профиль.
    """
    log_event("api_gateway", "INFO", f"Попытка авторизации пользователя: {req.login}")
    data = await auth_client.login(req.model_dump())
    log_event("api_gateway", "INFO", f"Успешная авторизация: {req.login}")
    return LoginResponse(**data)
