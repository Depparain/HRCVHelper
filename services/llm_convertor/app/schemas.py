from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class EducationItem(BaseModel):
    type: str = "Высшее:"
    institution: str = ""
    speciality: str = ""
    year: str = ""


class AdvancedTrainingItem(BaseModel):
    name: str = ""
    year: str = ""


class ProjectItem(BaseModel):
    place_time_raw: str = ""
    period: str = ""
    role_in_project: str = ""
    task_on_project: List[str] = Field(default_factory=list)
    achievements_in_project: List[str] = Field(default_factory=list)
    skills_tools_in_project: str = ""

    @field_validator("skills_tools_in_project", mode="before")
    @classmethod
    def normalize_skills(cls, v: Any) -> str:
        if isinstance(v, list):
            return ", ".join(str(x) for x in v if x)
        return str(v) if v is not None else ""

    @field_validator("task_on_project", "achievements_in_project", mode="before")
    @classmethod
    def normalize_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split("\n") if x.strip()]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []


class CVJsonContract(BaseModel):
    fio: str = ""
    vacancy: str = ""
    total_year_work: str = ""
    project_backround: str = ""
    pitch: str = ""
    skills_and_tools: List[str] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    advanced_training: List[AdvancedTrainingItem] = Field(default_factory=list)
    languages: str = "Английский на уровне A2"
    citizenship_location: str = ""
    employment: str = "Полная занятость, удаленная работа"
    status: str = "Готов к переезду"
    projects: List[ProjectItem] = Field(default_factory=list)

    @field_validator("skills_and_tools", mode="before")
    @classmethod
    def normalize_skills_tools(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split("\n") if x.strip()]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []


class ParseRequest(BaseModel):
    markdown: str
    original_filename: Optional[str] = None
    force_dynamic: bool = False
    rework_comment: Optional[str] = None


class ParseResponse(BaseModel):
    data: CVJsonContract
    source: str = "ollama"
    status: str = "ok"


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    model: str
