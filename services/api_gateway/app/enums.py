from __future__ import annotations

import enum


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
