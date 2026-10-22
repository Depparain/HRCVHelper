from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# --- Auth ---

class LoginRequest(BaseModel):
    login: str
    password: Optional[str] = None
    hash_pass: Optional[str] = None


class UserProfile(BaseModel):
    hr_id: int
    full_name: str
    login: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


# --- CV ---

class CVUploadResponse(BaseModel):
    cv_id: int
    hr_id: int
    status: str
    data: Dict[str, Any]
    filename: Optional[str] = None


class CVValidateResponse(BaseModel):
    cv_id: int
    hr_id: int
    status: str
    docx_url: Optional[str] = None
    download_url: str
    data: Dict[str, Any]


class CVDetailResponse(BaseModel):
    cv_id: int
    hr_id: int
    status: str
    jsonb: Dict[str, Any]
    docx: Optional[str] = None
    download_url: Optional[str] = None


class ReworkRequest(BaseModel):
    comment: Optional[str] = None


# --- Admin ---

class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str


class AdminLogsResponse(BaseModel):
    total: int
    logs: List[LogEntry]


class ServiceHealthStatus(BaseModel):
    service: str
    status: str
    details: Optional[Dict[str, Any]] = None


class HealthReportResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, ServiceHealthStatus]
