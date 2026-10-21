from __future__ import annotations

import io
import json
import uuid
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from services.db_connector.app.main import app as db_app
from services.db_connector.app.database import engine, Base, SessionLocal
from services.db_connector.app.models import HR, CV
from services.auth_system.app.main import app as auth_app
from services.md_convertor.app.main import app as md_app
from services.llm_convertor.app.main import app as llm_app
from services.json_to_word.app.main import app as jtw_app
from services.api_gateway.app.main import app as gateway_app
from services.api_gateway.app.config import settings as gw_settings

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLE_JSON_PATH = BASE_DIR / "services" / "json_to_word" / "template" / "example.json"


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(CV).delete()
        db.query(HR).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.mark.asyncio
async def test_complete_e2e_workflow(monkeypatch):
    """
    Полный сквозной тест:
    1. Инициализация и регистрация HR
    2. Логин через API Gateway
    3. Загрузка файла резюме и прогон через весь пайплайн (MD -> LLM -> DB)
    4. Валидация JSON и генерация .docx
    5. Скачивание готового .docx
    6. Проверка логов и отчета о состоянии
    """
    db_transport = ASGITransport(app=db_app)
    auth_transport = ASGITransport(app=auth_app)
    md_transport = ASGITransport(app=md_app)
    llm_transport = ASGITransport(app=llm_app)
    jtw_transport = ASGITransport(app=jtw_app)
    gw_transport = ASGITransport(app=gateway_app)

    original_async_client = AsyncClient

    def mock_async_client(*args, **kwargs):
        kwargs.pop("transport", None)
        return original_async_client(
            mounts={
                gw_settings.db_connector_url: db_transport,
                gw_settings.auth_system_url: auth_transport,
                gw_settings.md_convertor_url: md_transport,
                gw_settings.llm_convertor_url: llm_transport,
                gw_settings.json_to_word_url: jtw_transport,
            },
            *args,
            **kwargs,
        )

    monkeypatch.setattr("services.api_gateway.app.main.httpx.AsyncClient", mock_async_client)
    monkeypatch.setattr("services.auth_system.app.main.httpx.AsyncClient", mock_async_client)

    unique_login = f"hr_{uuid.uuid4().hex[:8]}"

    # Создаем пользователя через AuthSystem
    async with AsyncClient(transport=auth_transport, base_url="http://auth_system:8001") as auth_client:
        reg_resp = await auth_client.post(
            "/auth/register",
            json={"full_name": "Елена Рекрутер", "login": unique_login, "password": "securepassword123"},
        )
        assert reg_resp.status_code == 201

    # Шаг 1: Авторизация через API Gateway
    async with AsyncClient(transport=gw_transport, base_url="http://gateway:8000") as gw_client:
        login_resp = await gw_client.post(
            "/api/v1/auth/login",
            json={"login": unique_login, "password": "securepassword123"},
        )
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        token = token_data["access_token"]
        hr_id = token_data["user"]["hr_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Шаг 2: Загрузка резюме (Upload -> MD -> LLM -> DB "Ожидает проверки HR")
        sample_resume_content = b"""# Alexey Ivanov
Python Senior Developer
Skills: Python, FastAPI, Docker, PostgreSQL, Redis, Kubernetes
Experience:
Yandex, Senior Backend Developer, 2021-2024
Built high-load microservices.
"""
        files = {"file": ("alexey_cv.md", io.BytesIO(sample_resume_content), "text/markdown")}
        data = {"hr_id": str(hr_id)}

        upload_resp = await gw_client.post(
            "/api/v1/cv/upload",
            files=files,
            data=data,
            headers=headers,
        )
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        cv_id = upload_data["cv_id"]
        assert upload_data["status"] == "Ожидает проверки HR"
        assert upload_data["data"]["fio"] != ""

        # Шаг 3: Получение CV по ID
        get_resp = await gw_client.get(f"/api/v1/cv/{cv_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "Ожидает проверки HR"

        # Шаг 4: Валидация JSON от HR и генерация .docx
        example_json = json.loads(EXAMPLE_JSON_PATH.read_text(encoding="utf-8"))
        example_json["fio"] = "Иванов Алексей Петрович"
        example_json["vacancy"] = "Senior Python Lead"

        val_resp = await gw_client.put(
            f"/api/v1/cv/{cv_id}/validate",
            json=example_json,
            headers=headers,
        )
        assert val_resp.status_code == 200
        val_data = val_resp.json()
        assert val_data["status"] == "Готово"
        assert val_data["download_url"] == f"/api/v1/cv/{cv_id}/download"

        # Шаг 5: Скачивание сгенерированного .docx
        down_resp = await gw_client.get(f"/api/v1/cv/{cv_id}/download", headers=headers)
        assert down_resp.status_code == 200
        assert len(down_resp.content) > 50000
        assert "openxmlformats-officedocument" in down_resp.headers["content-type"]

        # Шаг 6: Проверка админ-эндпоинтов
        logs_resp = await gw_client.get("/api/v1/admin/logs")
        assert logs_resp.status_code == 200
        assert logs_resp.json()["total"] > 0

        health_resp = await gw_client.get("/api/v1/admin/health")
        assert health_resp.status_code == 200
        assert "services" in health_resp.json()
