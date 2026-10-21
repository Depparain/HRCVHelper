from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class HRBase(BaseModel):
    full_name: str
    login: str


class HRCreate(HRBase):
    hash_pass: str


class HRResponse(HRBase):
    hr_id: int
    model_config = ConfigDict(from_attributes=True)


class HRInDB(HRResponse):
    hash_pass: str


class CVBase(BaseModel):
    hr_id: int
    jsonb: Dict[str, Any]
    status: Optional[str] = "Загружено"
    docx: Optional[str] = None


class CVCreate(CVBase):
    pass


class CVUpdate(BaseModel):
    jsonb: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    docx: Optional[str] = None


class CVStatusUpdate(BaseModel):
    status: str


class CVResponse(BaseModel):
    cv_id: int
    hr_id: int
    jsonb: Dict[str, Any]
    status: str
    docx: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class StorageUploadResponse(BaseModel):
    key: str
    url_or_path: str


class HealthResponse(BaseModel):
    status: str
    database: bool
    storage: bool
