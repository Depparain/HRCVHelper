from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from docxtpl import DocxTemplate


def _load_data(json_path: Path) -> Dict[str, Any]:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _clean_str_list(raw_items: Any) -> List[str]:
    res: List[str] = []
    if not raw_items:
        return res
    if not isinstance(raw_items, list):
        raw_items = str(raw_items).split("\n")
    for item in raw_items:
        clean = re.sub(r"^[•\-\*—·\s]+", "", str(item)).strip()
        if clean:
            res.append(clean)
    return res


def _format_courses_strings(raw_courses: Any) -> List[str]:
    res: List[str] = []
    if not raw_courses:
        return res
    if not isinstance(raw_courses, list):
        raw_courses = [raw_courses]
    for c in raw_courses:
        if isinstance(c, dict):
            yr = str(c.get("year", "")).strip()
            nm = str(c.get("name", "")).strip()
            if yr and nm:
                res.append(f"{yr}, {nm}")
            elif nm:
                res.append(nm)
            elif yr:
                res.append(yr)
        elif isinstance(c, str) and c.strip():
            res.append(re.sub(r"^[•\-\*—·\s]+", "", c).strip())
    return res


def _format_education_string(edu_data: Any) -> str:
    if not edu_data:
        return ""
    if isinstance(edu_data, str):
        return edu_data.strip()
    if not isinstance(edu_data, list):
        edu_data = [edu_data]
    lines: List[str] = []
    for item in edu_data:
        if isinstance(item, dict):
            parts = []
            yr = str(item.get("year", "")).strip()
            inst = str(item.get("institution", "")).strip()
            spec = str(item.get("speciality", "")).strip()
            header = f"{yr}, {inst}" if yr and inst else (inst or yr)
            if header:
                parts.append(header)
            if spec:
                parts.append(spec)
            if parts:
                lines.append("\n".join(parts))
        elif isinstance(item, str) and item.strip():
            lines.append(item.strip())
    return "\n\n".join(lines)


def _format_skills_string(raw_skills: Any) -> str:
    if not raw_skills:
        return ""
    if isinstance(raw_skills, str):
        return raw_skills.strip()
    if isinstance(raw_skills, list):
        return "\n".join(str(s).strip() for s in raw_skills if str(s).strip())
    return str(raw_skills)


def _build_projects(projects: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not isinstance(projects, list):
        return items

    for project in projects:
        if not isinstance(project, dict):
            continue

        raw_place = project.get("place_time_raw") or project.get("name") or ""
        raw_period = project.get("period") or ""
        if raw_place and raw_period:
            place_time = f"{raw_place}\n{raw_period}"
        else:
            place_time = raw_place or raw_period

        role_clean = re.sub(r"^роль:\s*", "", str(project.get("role_in_project") or ""), flags=re.IGNORECASE).strip()
        skills_clean = str(project.get("skills_tools_in_project") or "").strip()

        items.append(
            {
                "project_place_and_work_time": place_time,
                "role_in_project": role_clean,
                "task_on_project": _clean_str_list(project.get("task_on_project")),
                "achievements_in_project": _clean_str_list(project.get("achievements_in_project")),
                "skills_tools_in_project": skills_clean,
            }
        )

    return items


def generate_cv(json_path: Path | str, template_path: Path | str, output_path: Path | str) -> Path:
    json_file = Path(json_path)
    template_file = Path(template_path)
    output_file = Path(output_path)

    if not json_file.exists():
        raise FileNotFoundError(f"JSON не найден: {json_file}")
    if not template_file.exists():
        raise FileNotFoundError(f"Шаблон DOCX не найден: {template_file}")

    data = _load_data(json_file)
    doc = DocxTemplate(str(template_file))

    context: Dict[str, Any] = {
        "fio": str(data.get("fio") or ""),
        "vacancy": str(data.get("vacancy") or ""),
        "total_year_work": str(data.get("total_year_work") or ""),
        "project_backround": str(data.get("project_backround") or ""),
        "pitch": str(data.get("pitch") or ""),
        "skills_tools": _format_skills_string(data.get("skills_and_tools")),
        "education": _format_education_string(data.get("education")),
        "courses": _format_courses_strings(data.get("advanced_training")),
        "languages": str(data.get("languages") or ""),
        "citizenship_location": str(data.get("citizenship_location") or ""),
        "employment": str(data.get("employment") or ""),
        "status": str(data.get("status") or ""),
        "projects": _build_projects(data.get("projects")),
    }

    doc.render(context)
    doc.save(str(output_file))
    return output_file


__all__ = ["generate_cv"]
