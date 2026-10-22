from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
import httpx
from fastapi import HTTPException
from ..config import settings
from ..logger_collector import log_event


class DBClient:
    def __init__(self, base_url: str = settings.db_connector_url):
        self.base_url = base_url

    async def create_cv(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.base_url}/cv", json=payload)
                if resp.status_code != 201:
                    raise HTTPException(status_code=500, detail="Не удалось создать запись CV в БД")
                return resp.json()
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис базы данных недоступен")

    async def get_cv(self, cv_id: int) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cv/{cv_id}")
                if resp.status_code == 404:
                    return None
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                return resp.json()
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис базы данных недоступен")

    async def list_cvs(self, hr_id: Optional[int] = None, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            params = {"skip": skip, "limit": limit}
            if hr_id is not None:
                params["hr_id"] = hr_id
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cv", params=params)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                return resp.json()
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис базы данных недоступен")

    async def update_cv(self, cv_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.put(f"{self.base_url}/cv/{cv_id}", json=payload)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail="Не удалось обновить запись CV")
                return resp.json()
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис базы данных недоступен")

    async def update_cv_status(self, cv_id: int, status: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.put(f"{self.base_url}/cv/{cv_id}/status", json={"status": status})
                if resp.status_code != 200:
                    log_event("api_gateway", "WARNING", f"[CV {cv_id}] Ошибка обновления статуса на '{status}': {resp.text}")
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector недоступен при смене статуса: {e}")

    async def update_cv_docx(self, cv_id: int, docx_key: str, status: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.put(
                    f"{self.base_url}/cv/{cv_id}/docx",
                    params={"docx_key": docx_key, "status": status},
                )
                if resp.status_code != 200:
                    raise HTTPException(status_code=500, detail="Не удалось обновить статус 'Готово' в БД")
                return resp.json()
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector недоступен: {e}")
            raise HTTPException(status_code=503, detail="Сервис базы данных недоступен")

    async def upload_storage_file(self, object_name: str, file_bytes: bytes) -> Dict[str, Any]:
        try:
            files = {"file": (object_name, io.BytesIO(file_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/storage/upload",
                    files=files,
                    data={"object_name": object_name},
                )
                if resp.status_code != 200:
                    log_event("api_gateway", "ERROR", f"Ошибка S3 storage: {resp.text}")
                    raise HTTPException(status_code=500, detail="Ошибка сохранения файла в S3")
                return resp.json()
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector Storage недоступен: {e}")
            raise HTTPException(status_code=503, detail="Хранилище S3 недоступно")

    async def download_storage_file(self, docx_key: str) -> bytes:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{self.base_url}/storage/download/{docx_key}")
                if resp.status_code != 200:
                    raise HTTPException(status_code=404, detail="Файл не найден в хранилище S3")
                return resp.content
        except httpx.RequestError as e:
            log_event("api_gateway", "ERROR", f"DBConnector Storage недоступен: {e}")
            raise HTTPException(status_code=503, detail="Хранилище S3 недоступно")


db_client = DBClient()
