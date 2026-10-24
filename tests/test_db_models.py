from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.db_connector.app.models import Base, HR, CV, CVStatus
from services.db_connector.app import crud
from services.db_connector.app.schemas import HRCreate, CVCreate, CVUpdate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_create_and_get_hr(db_session):
    hr_in = HRCreate(full_name="Иван Петров", login="ivan", hash_pass="some_hash")
    hr = crud.create_hr(db_session, hr_in)
    assert hr.HR_ID is not None
    assert hr.Full_Name == "Иван Петров"

    found = crud.get_hr_by_login(db_session, "ivan")
    assert found is not None
    assert found.HR_ID == hr.HR_ID


def test_cv_lifecycle(db_session):
    hr_in = HRCreate(full_name="Анна HR", login="anna", hash_pass="hash123")
    hr = crud.create_hr(db_session, hr_in)

    # 1. Загружено
    cv_in = CVCreate(hr_id=hr.HR_ID, jsonb={}, status=CVStatus.UPLOADED.value)
    cv = crud.create_cv(db_session, cv_in)
    assert cv.CV_ID is not None
    assert cv.Status == "Загружено"

    # 2. Конвертация в MD
    cv = crud.update_cv_status(db_session, cv.CV_ID, CVStatus.MD_CONVERSION.value)
    assert cv.Status == "Конвертация в MD"

    # 3. Обработка резюме
    cv = crud.update_cv_status(db_session, cv.CV_ID, CVStatus.LLM_PROCESSING.value)
    assert cv.Status == "Обработка резюме"

    # 4. Ожидает проверки HR
    sample_json = {"fio": "Тестовый Кандидат", "vacancy": "Python Dev"}
    cv = crud.update_cv(db_session, cv.CV_ID, CVUpdate(jsonb=sample_json, status=CVStatus.AWAITING_HR.value))
    assert cv.Status == "Ожидает проверки HR"
    assert cv.JSONB["fio"] == "Тестовый Кандидат"

    # 5. Формирование docx
    cv = crud.update_cv_status(db_session, cv.CV_ID, CVStatus.DOCX_GENERATION.value)
    assert cv.Status == "Формирование docx"

    # 6. Готово
    cv = crud.update_cv_docx(db_session, cv.CV_ID, "resumes/cv_1.docx", status=CVStatus.READY.value)
    assert cv.Status == "Готово"
    assert cv.Docx == "resumes/cv_1.docx"


def test_template_lifecycle(db_session):
    # Создание системного и кастомного шаблона
    dummy_docx = b"PK\x03\x04mock_docx_binary_data"
    tpl = crud.create_template(
        db_session,
        name="IT Корпоративный",
        filename="it_corp.docx",
        file_bytes=dummy_docx,
        description="Шаблон для технических специалистов",
        is_system=False,
        make_active=True,
    )
    assert tpl.template_id is not None
    assert tpl.name == "IT Корпоративный"
    assert tpl.is_active is True
    assert tpl.file_bytes == dummy_docx

    # Получение активного шаблона
    active = crud.get_active_template(db_session)
    assert active is not None
    assert active.template_id == tpl.template_id

    # Список шаблонов
    templates = crud.list_templates(db_session)
    assert len(templates) >= 1
    assert any(t.template_id == tpl.template_id for t in templates)

    # Удаление
    deleted = crud.delete_template(db_session, tpl.template_id)
    assert deleted is True
    assert crud.get_template_by_id(db_session, tpl.template_id) is None


def test_field_config_lifecycle(db_session):
    fields_map = {
        "fio": True,
        "vacancy": True,
        "pitch": True,
        "skills_tools": True,
        "projects": True,
        "education": False,
    }
    cfg = crud.save_field_config(
        db_session,
        fields=fields_map,
        config_key="custom_tech",
        name="Технический профиль",
    )
    assert cfg.config_key == "custom_tech"
    assert cfg.name == "Технический профиль"
    assert cfg.fields["fio"] is True
    assert cfg.fields["education"] is False

    # Получение конфигурации
    loaded = crud.get_field_config(db_session, "custom_tech")
    assert loaded is not None
    assert loaded.fields["pitch"] is True

    # Обновление существующей конфигурации
    updated_fields = dict(fields_map)
    updated_fields["education"] = True
    cfg_updated = crud.save_field_config(db_session, fields=updated_fields, config_key="custom_tech")
    assert cfg_updated.fields["education"] is True

