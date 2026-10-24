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

    get = get_cv

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

    # --- PostgreSQL Template Methods ---

    async def list_templates(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/templates")
                if resp.status_code == 200:
                    return resp.json()
                return []
        except Exception as e:
            log_event("api_gateway", "WARNING", f"Не удалось получить шаблоны из DBConnector: {e}")
            return []

    async def upload_template(
        self,
        file_bytes: bytes,
        filename: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        make_active: bool = False,
        hr_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        try:
            files = {"file": (filename, io.BytesIO(file_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            data = {"make_active": str(make_active).lower()}
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if hr_id:
                data["hr_id"] = str(hr_id)

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/templates", files=files, data=data)
                if resp.status_code == 200:
                    return resp.json()
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except HTTPException:
            raise
        except Exception as e:
            log_event("api_gateway", "ERROR", f"Ошибка сохранения шаблона в БД: {e}")
            raise HTTPException(status_code=500, detail=f"Не удалось сохранить шаблон в БД: {e}")

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
                raise HTTPException(status_code=resp.status_code, detail="Шаблон не найден в БД")
        except HTTPException:
            raise
        except Exception as e:
            log_event("api_gateway", "ERROR", f"Ошибка загрузки шаблона из БД: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка загрузки шаблона из БД: {e}")

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

    # --- PostgreSQL FieldConfig Methods ---

    async def get_fields_config(self, config_key: str = "default") -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/configs/fields", params={"config_key": config_key})
                if resp.status_code == 200:
                    return resp.json().get("fields", {})
                return {}
        except Exception as e:
            log_event("api_gateway", "WARNING", f"Не удалось прочитать FieldConfig из БД: {e}")
            return {}

    async def save_fields_config(self, fields: Dict[str, bool], config_key: str = "default", hr_id: Optional[int] = None) -> Dict[str, Any]:
        try:
            params = {"config_key": config_key}
            if hr_id:
                params["hr_id"] = hr_id
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.base_url}/configs/fields", json=fields, params=params)
                if resp.status_code == 200:
                    return resp.json()
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
        except HTTPException:
            raise
        except Exception as e:
            log_event("api_gateway", "ERROR", f"Ошибка сохранения FieldConfig в БД: {e}")
            raise HTTPException(status_code=500, detail=f"Не удалось сохранить схему полей в БД: {e}")


db_client = DBClient()
