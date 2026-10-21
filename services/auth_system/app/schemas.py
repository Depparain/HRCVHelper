from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class HRUserPayload(BaseModel):
    hr_id: int
    full_name: str
    login: str


class LoginRequest(BaseModel):
    login: str
    password: Optional[str] = None
    hash_pass: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: HRUserPayload


class RegisterRequest(BaseModel):
    full_name: str
    login: str
    password: str


class VerifyTokenRequest(BaseModel):
    token: str


class VerifyTokenResponse(BaseModel):
    valid: bool
    user: Optional[HRUserPayload] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    db_connector: bool
