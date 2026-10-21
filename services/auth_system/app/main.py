from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .security import hash_password, verify_password, create_access_token, decode_access_token
from .schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    VerifyTokenRequest,
    VerifyTokenResponse,
    HRUserPayload,
    HealthResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_system")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создает демо-пользователя HR при первом запуске, если база пуста."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.db_connector_url}/users/login/hr_admin")
            if resp.status_code == 404:
                payload = {
                    "full_name": "Администратор HR",
                    "login": "hr_admin",
                    "hash_pass": hash_password("hrpassword123"),
                }
                create_resp = await client.post(f"{settings.db_connector_url}/users", json=payload)
                if create_resp.status_code == 201:
                    logger.info("Создан дефолтный пользователь HR: hr_admin")
    except Exception as e:
        logger.info("Фоновая проверка дефолтного пользователя: %s", e)
    yield


app = FastAPI(
    title="HRCVHelper - AuthSystem Service",
    version="1.0.0",
    description="Микросервис авторизации и управления сессиями пользователей",
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
    db_ok = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.db_connector_url}/health")
            if resp.status_code == 200:
                db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_connector=db_ok,
    )


@app.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.db_connector_url}/users/login/{req.login}")
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный логин или пароль",
                )
            user_data = resp.json()
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ошибка соединения с сервисом БД: {e}",
        )

    # Проверяем пароль
    password_to_check = req.password or req.hash_pass
    if not password_to_check or not verify_password(password_to_check, user_data["hash_pass"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    user_payload = HRUserPayload(
        hr_id=user_data["hr_id"],
        full_name=user_data["full_name"],
        login=user_data["login"],
    )

    token = create_access_token(user_payload.model_dump())
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_payload,
    )


@app.post("/auth/register", response_model=HRUserPayload, status_code=201)
async def register(req: RegisterRequest):
    hashed = hash_password(req.password)
    payload = {
        "full_name": req.full_name,
        "login": req.login,
        "hash_pass": hashed,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{settings.db_connector_url}/users", json=payload)
            if resp.status_code == 400:
                raise HTTPException(status_code=400, detail="Логин уже занят")
            if resp.status_code != 201:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            created = resp.json()
            return HRUserPayload(
                hr_id=created["hr_id"],
                full_name=created["full_name"],
                login=created["login"],
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Ошибка сервиса БД: {e}")


@app.post("/auth/verify", response_model=VerifyTokenResponse)
def verify_token(req: VerifyTokenRequest):
    payload = decode_access_token(req.token)
    if not payload or "hr_id" not in payload:
        return VerifyTokenResponse(valid=False, detail="Недействительный или истекший токен")

    user = HRUserPayload(
        hr_id=payload["hr_id"],
        full_name=payload.get("full_name", ""),
        login=payload.get("login", ""),
    )
    return VerifyTokenResponse(valid=True, user=user)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.service_host, port=settings.service_port)
