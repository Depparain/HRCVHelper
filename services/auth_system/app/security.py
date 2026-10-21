from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from .config import settings


def hash_password(password: str) -> str:
    """Генерирует безопасный bcrypt-хэш пароля."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет пароль против сохраненного хэша.
    Поддерживает:
    1. Bcrypt (современная нативная реализация без устаревших оберток)
    2. SHA256 (для гибкости и совместимости с ФТ-HR.1 'хэш пароля')
    """
    if not hashed_password or not plain_password:
        return False

    # Если хэш в bcrypt формате ($2b$, $2a$)
    if hashed_password.startswith("$2"):
        try:
            plain_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(plain_bytes, hash_bytes)
        except Exception:
            return False

    # SHA256 сравнение
    sha_input = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(sha_input.lower(), hashed_password.lower()):
        return True

    # Прямое совпадение (если plain_password сам уже был передан как sha256)
    if hmac.compare_digest(plain_password.lower(), hashed_password.lower()):
        return True

    return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.PyJWTError:
        return None
