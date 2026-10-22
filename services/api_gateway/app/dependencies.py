from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import httpx
from fastapi import Depends, Header, HTTPException, Query, status

from .config import settings
from .enums import UserRole

logger = logging.getLogger("api_gateway.auth")


async def get_current_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> Dict[str, Any]:
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ", 1)[1].strip()
    elif token:
        raw_token = token.strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация (отсутствует токен доступа)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"{settings.auth_system_url}/auth/verify", json={"token": raw_token})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid") and data.get("user"):
                    return data["user"]
    except Exception as e:
        logger.warning("Ошибка связи с AuthSystem при проверке токена: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис аутентификации временно недоступен",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный или истекший токен авторизации",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    role = current_user.get("role", UserRole.HR.value)
    if role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуются права администратора",
        )
    return current_user
