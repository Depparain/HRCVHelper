from __future__ import annotations

import io
from typing import Any, Dict, Optional
import httpx
from fastapi import HTTPException
from ..config import settings
from ..logger_collector import log_event


class AuthClient:
    def __init__(self, base_url: str = settings.auth_system_url):
        self.base_url = base_url

    async def login(self, login_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(f"{self.base_url}/auth/login", json=login_data)
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=resp.json().get("detail", "Ошибка входа"),
                    )
                return resp.json()
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"AuthSystem недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис авторизации временно недоступен")


class MDClient:
    def __init__(self, base_url: str = settings.md_convertor_url):
        self.base_url = base_url

    async def convert(self, filename: str, file_bytes: bytes) -> str:
        try:
            files = {"file": (filename, io.BytesIO(file_bytes), "application/octet-stream")}
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/convert", files=files)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ошибка конвертации в Markdown: {resp.text}")
                return resp.json().get("markdown", "")
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"MDConvertor недоступен: {e}")
            raise RuntimeError(f"Сервис MDConvertor недоступен: {e}")


class LLMClient:
    def __init__(self, base_url: str = settings.llm_convertor_url):
        self.base_url = base_url

    async def parse(
        self,
        markdown: Optional[str] = None,
        cv_data: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        rework_comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "markdown": markdown,
            "cv_data": cv_data,
            "original_filename": filename,
            "rework_comment": rework_comment,
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(f"{self.base_url}/parse", json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(f"Ошибка парсинга LLM: {resp.text}")
                return resp.json().get("data", {})
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"LLMConvertor недоступен: {e}")
            raise RuntimeError(f"Сервис LLMConvertor недоступен: {e}")


class WordClient:
    def __init__(self, base_url: str = settings.json_to_word_url):
        self.base_url = base_url

    async def generate(self, validated_json: Dict[str, Any]) -> bytes:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{self.base_url}/generate", json=validated_json)
                if resp.status_code != 200:
                    log_event("api_gateway", "ERROR", f"Ошибка JSONToWord: {resp.text}")
                    raise HTTPException(status_code=500, detail=f"Ошибка генерации DOCX: {resp.text}")
                return resp.content
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"JSONToWord сервис недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис JSONToWord недоступен")


auth_client = AuthClient()
md_client = MDClient()
llm_client = LLMClient()
word_client = WordClient()
