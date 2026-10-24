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

    async def generate(self, validated_json: Dict[str, Any], template_id: Optional[str] = None) -> bytes:
        params = {"template_id": template_id} if template_id else {}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{self.base_url}/generate", json=validated_json, params=params)
                if resp.status_code != 200:
                    log_event("api_gateway", "ERROR", f"Ошибка JSONToWord: {resp.text}")
                    raise HTTPException(status_code=500, detail=f"Ошибка генерации DOCX: {resp.text}")
                return resp.content
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"JSONToWord сервис недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис JSONToWord недоступен")

    async def list_templates(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/templates")
                if resp.status_code == 200:
                    return resp.json().get("templates", [])
                return []
        except Exception as e:
            logger.warning("Не удалось получить шаблоны из JSONToWord: %s", e)
            return []

    async def upload_template(
        self,
        file_bytes: bytes,
        filename: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        make_active: bool = False,
    ) -> Dict[str, Any]:
        try:
            files = {"file": (filename, file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            data = {"make_active": str(make_active).lower()}
            if name:
                data["name"] = name
            if description:
                data["description"] = description

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/templates/upload", files=files, data=data)
                if resp.status_code == 200:
                    return resp.json()
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Ошибка передачи шаблона в JSONToWord: %s", e)
            raise HTTPException(status_code=500, detail=f"Не удалось загрузить шаблон: {e}")

    async def download_template(self, template_id: str) -> tuple[bytes, str]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{self.base_url}/templates/{template_id}/download")
                if resp.status_code == 200:
                    content_disp = resp.headers.get("Content-Disposition", "")
                    filename = "template.docx"
                    if "filename=" in content_disp:
                        filename = content_disp.split("filename=")[-1].strip('"; ')
                    return resp.content, filename
                raise HTTPException(status_code=resp.status_code, detail="Шаблон не найден")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Ошибка скачивания шаблона из JSONToWord: %s", e)
            raise HTTPException(status_code=500, detail=f"Ошибка скачивания шаблона: {e}")

    async def set_active_template(self, template_id: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.base_url}/templates/{template_id}/set-default")
                if resp.status_code == 200:
                    return resp.json()
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_template(self, template_id: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.delete(f"{self.base_url}/templates/{template_id}")
                if resp.status_code == 200:
                    return resp.json()
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


auth_client = AuthClient()
md_client = MDClient()
llm_client = LLMClient()
word_client = WordClient()
