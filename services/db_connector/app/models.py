from __future__ import annotations

import enum
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class CVStatus(str, enum.Enum):
    UPLOADED = "Загружено"
    MD_CONVERSION = "Конвертация в MD"
    LLM_PROCESSING = "Обработка резюме"
    AWAITING_HR = "Ожидает проверки HR"
    DOCX_GENERATION = "Формирование docx"
    READY = "Готово"
    ERROR = "Ошибка парсинга"


class UserRole(str, enum.Enum):
    HR = "hr"
    ADMIN = "admin"


class HR(Base):
    """Таблица HR-специалистов."""
    __tablename__ = "HR"

    hr_id = Column("HR_ID", Integer, primary_key=True, autoincrement=True, index=True)
    full_name = Column("Full_Name", String(255), nullable=False)
    login = Column("Login", String(128), unique=True, nullable=False, index=True)
    hash_pass = Column("Hash_Pass", String(255), nullable=False)
    role = Column("Role", String(32), nullable=False, default=UserRole.HR.value)

    cvs = relationship("CV", back_populates="hr", cascade="all, delete-orphan")

    # Свойства обратной совместимости для старого кода
    @property
    def HR_ID(self) -> int:
        return self.hr_id

    @property
    def Full_Name(self) -> str:
        return self.full_name

    @property
    def Login(self) -> str:
        return self.login

    @property
    def Hash_Pass(self) -> str:
        return self.hash_pass

    @property
    def Role(self) -> str:
        return self.role

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hr_id": self.hr_id,
            "full_name": self.full_name,
            "login": self.login,
            "role": self.role,
        }


class CV(Base):
    """Таблица обрабатываемых резюме."""
    __tablename__ = "CV"

    cv_id = Column("CV_ID", Integer, primary_key=True, autoincrement=True, index=True)
    hr_id = Column("HR_ID", Integer, ForeignKey("HR.HR_ID"), nullable=False, index=True)
    jsonb = Column("JSONB", JSONB, nullable=False, default=dict)
    status = Column("Status", String(64), nullable=False, default=CVStatus.UPLOADED.value)
    docx = Column("Docx", Text, nullable=True)

    hr = relationship("HR", back_populates="cvs")

    # Свойства обратной совместимости для старого кода
    @property
    def CV_ID(self) -> int:
        return self.cv_id

    @property
    def HR_ID(self) -> int:
        return self.hr_id

    @property
    def JSONB(self) -> Dict[str, Any]:
        return self.jsonb

    @property
    def Status(self) -> str:
        return self.status

    @property
    def Docx(self) -> Optional[str]:
        return self.docx

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cv_id": self.cv_id,
            "hr_id": self.hr_id,
            "jsonb": self.jsonb,
            "status": self.status,
            "docx": self.docx,
        }
