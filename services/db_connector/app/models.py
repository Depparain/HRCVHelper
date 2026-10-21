from __future__ import annotations

import enum
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
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


class HR(Base):
    """Таблица HR-специалистов."""
    __tablename__ = "HR"

    HR_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)
    Full_Name = Column(String(255), nullable=False)
    Login = Column(String(128), unique=True, nullable=False, index=True)
    Hash_Pass = Column(String(255), nullable=False)

    cvs = relationship("CV", back_populates="hr", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hr_id": self.HR_ID,
            "full_name": self.Full_Name,
            "login": self.Login,
        }


class CV(Base):
    """Таблица обрабатываемых резюме."""
    __tablename__ = "CV"

    CV_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)
    HR_ID = Column(Integer, ForeignKey("HR.HR_ID"), nullable=False, index=True)
    JSONB = Column(JSON, nullable=False, default=dict)
    Status = Column(String(64), nullable=False, default=CVStatus.UPLOADED.value)
    Docx = Column(Text, nullable=True)

    hr = relationship("HR", back_populates="cvs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cv_id": self.CV_ID,
            "hr_id": self.HR_ID,
            "jsonb": self.JSONB,
            "status": self.Status,
            "docx": self.Docx,
        }
