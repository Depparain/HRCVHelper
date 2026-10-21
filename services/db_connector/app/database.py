import logging
import os
from sqlalchemy import create_engine
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
