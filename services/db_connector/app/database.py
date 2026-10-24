import logging
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .config import settings
from .models import Base

logger = logging.getLogger("db_connector.database")

db_url = settings.database_url

# Проверка диалекта: если postgresql, проверяем наличие драйвера, иначе используем sqlite
if db_url.startswith("postgresql"):
    try:
        import psycopg2  # noqa: F401
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    except ImportError:
        try:
            import psycopg  # noqa: F401
        except ImportError:
            fallback_sqlite = "sqlite:///./hrcvhelper.db"
            logger.warning(
                "PostgreSQL драйвер (psycopg/psycopg2) не найден. Переключение на локальный SQLite: %s",
                fallback_sqlite,
            )
            db_url = fallback_sqlite

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url, 
    pool_pre_ping=True, 
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE "HR" ADD COLUMN IF NOT EXISTS "Role" VARCHAR(32) NOT NULL DEFAULT \'hr\';'))
            conn.execute(text('UPDATE "HR" SET "Role" = \'admin\' WHERE "Login" IN (\'hr_admin\', \'recruiter@hrhelper.ai\');'))
    except Exception as e:
        logger.info("Миграция колонки Role: %s", e)

    # Инициализация дефолтного шаблона и схемы полей в БД, если они отсутствуют
    try:
        db = SessionLocal()
        from .models import Template, FieldConfig
        default_tpl = db.query(Template).filter(Template.template_id == "default").first()
        if not default_tpl:
            docx_candidates = [
                Path(__file__).resolve().parent.parent.parent / "json_to_word" / "template" / "placeholders_cv_docx.docx",
                Path("services/json_to_word/template/placeholders_cv_docx.docx"),
                Path("/app/templates/placeholders_cv_docx.docx"),
            ]
            content = b""
            for p in docx_candidates:
                if p.exists():
                    content = p.read_bytes()
                    break

            if content:
                from .crud import create_template
                create_template(
                    db=db,
                    template_id="default",
                    name="Классический корпоративный шаблон",
                    filename="placeholders_cv_docx.docx",
                    file_bytes=content,
                    description="Стандартный двухколоночный корпоративный шаблон HRCVHelper",
                    is_system=True,
                    is_active=True,
                )
                logger.info("В БД инициализирован базовый шаблон Word (Template)")

        default_cfg = db.query(FieldConfig).filter(FieldConfig.config_key == "default").first()
        if not default_cfg:
            from .crud import save_field_config
            initial_fields = {
                "fio": True, "vacancy": True, "total_year_work": True,
                "citizenship_location": True, "employment": True, "status": True,
                "pitch": True, "skills_and_tools": True, "project_backround": True,
                "languages": True, "projects": True, "project_role": True,
                "project_period": True, "project_tasks": True, "project_achievements": True,
                "project_skills": True, "education": True, "advanced_training": True
            }
            save_field_config(db, fields=initial_fields, config_key="default", name="Стандартная конфигурация полей")
            logger.info("В БД инициализирована базовая конфигурация полей (FieldConfig)")
        db.close()
    except Exception as e:
        logger.warning("Инициализация шаблонов/конфигураций в БД: %s", e)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
