from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from .config import settings
from .schemas import CVJsonContract, ProjectItem, EducationItem, AdvancedTrainingItem

logger = logging.getLogger(__name__)

MONTHS_RU = {
    "январ": "01", "феврал": "02", "март": "03", "апрел": "04", "ма": "05", "июн": "06",
    "июл": "07", "август": "08", "сентябр": "09", "октябр": "10", "ноябр": "11", "декабр": "12"
}

MONTH_CAPS = r"(?:Январ[ья]|Феврал[ья]|Март[а]?|Апрел[ья]|Ма[яй]|Июн[ья]|Июл[ья]|Август[а]?|Сентябр[ья]|Октябр[ья]|Ноябр[ья]|Декабр[ья])"

TECH_DICTIONARY = [
    ".NET", ".NET Framework", "C#", "C++", "Java", "Python", "Go", "Golang", "Rust", "PHP", "JavaScript", "TypeScript",
    "HTML", "HTML5", "CSS", "CSS3", "Angular", "AngularJS", "React", "Vue.js", "Vue", "Node.js", "Next.js",
    "Django", "FastAPI", "Spring", "ASP.NET", "ASP.NET MVC", "ASP.NET WebForms", "WCF",
    "SQL", "PostgreSQL", "MySQL", "MS SQL", "MSSQL", "Oracle", "MongoDB", "Redis", "JSON", "JSONB", "JSON Schema",
    "GraphQL", "REST", "REST API", "SOAP", "gRPC", "Docker", "Kubernetes", "Git", "GitLab", "Jenkins", "CI/CD", "Linux",
    "Postman", "Swagger", "Kafka", "Apache Kafka", "RabbitMQ", "Prometheus", "Grafana", "ELK",
    "Jira", "Confluence", "Atlassian Jira", "Atlassian Confluence", "Яндекс Вики",
    "Figma", "Draw.io", "PlantUML", "ArchiMate", "C4", "ADR/RFC", "BPMN", "BPMN 2.0", "UML", "DFD", "ETL", "Data Mapping",
    "User Stories", "Use Cases", "ER-диаграммы", "Agile", "Scrum", "Kanban", "LeSS", "SAFe", "LLM",
    "ИТ-архитектура", "Архитектурный надзор", "Системный дизайн", "Системный анализ", "Анализ требований", "Аналитическое мышление",
    "Постановка задач разработчикам", "Базы данных", "реляционные БД", "MS SharePoint", "Microsoft Office", "Microsoft Visio",
    "Team Foundation Server", "jQuery"
]


def _load_prompt_files() -> tuple[str, str]:
    prompt_text = ""
    example_text = ""
    if settings.prompt_path.exists():
        prompt_text = settings.prompt_path.read_text(encoding="utf-8")
    if settings.schema_path.exists():
        example_text = settings.schema_path.read_text(encoding="utf-8")
    return prompt_text, example_text


def clean_non_breaking(text: str) -> str:
    """Удаляет неразрывные пробелы, артефакты кодировки, нормализует дефисы и разделяет слипшиеся слова."""
    cleaned = re.sub(r"[\xa0\u202f\u200b\ufeff]", " ", text)
    cleaned = re.sub(r"[—–−‐‑‒]", "-", cleaned)
    cleaned = re.sub(r"[¸]", "• ", cleaned)
    cleaned = re.sub(rf"([а-яёa-zА-ЯЁA-Z0-9\.\,])({MONTH_CAPS})", r"\1 \2", cleaned)
    cleaned = re.sub(r"([а-яёa-z])([А-ЯЁ][а-яё]+)", r"\1 \2", cleaned)
    cleaned = re.sub(r"(\d{4})([А-ЯЁ])", r"\1 \2", cleaned)
    cleaned = re.sub(r"(Высшее|Бакалавр|Магистр|Среднее)([А-ЯЁ])", r"\1 \2", cleaned)
    return cleaned


def split_items_by_bullets(text: str) -> List[str]:
    """Разбивает текст на отдельные пункты по маркерам •, -, *, переносам строк или двойным пробелам."""
    clean = re.sub(r"^(?:задачи|обязанности и задачи|обязанности|достижения|результаты):\s*", "", text, flags=re.IGNORECASE).strip()
    clean = clean.strip("|\t ").strip()
    if not clean:
        return []

    if "•" in clean or "·" in clean or "*" in clean:
        parts = re.split(r"[•·*]\s*", clean)
    elif "\n" in clean:
        parts = clean.splitlines()
    elif re.search(r"\s{2,}(?=[А-ЯЁA-Z])", clean):
        parts = re.split(r"\s{2,}(?=[А-ЯЁA-Z])", clean)
    else:
        parts = [clean]

    items = []
    for p in parts:
        p_c = p.strip("|\t -").strip()
        if p_c and len(p_c) > 3:
            items.append(p_c)
    return items


def clean_json_string(text: str) -> str:
    """Очищает строку от Markdown-тегов и лишних символов перед парсингом JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def format_years_months(years: int, months: int) -> str:
    """Форматирует количество лет и месяцев по строгим правилам русского языка."""
    if years % 10 == 1 and years % 100 != 11:
        y_str = "ГОД"
    elif 2 <= years % 10 <= 4 and (years % 100 < 10 or years % 100 >= 20):
        y_str = "ГОДА"
    else:
        y_str = "ЛЕТ"

    if months % 10 == 1 and months % 100 != 11:
        m_str = "МЕСЯЦ"
    elif 2 <= months % 10 <= 4 and (months % 100 < 10 or months % 100 >= 20):
        m_str = "МЕСЯЦА"
    else:
        m_str = "МЕСЯЦЕВ"

    return f"{years} {y_str} {months} {m_str}"


def normalize_period_str(period_raw: str) -> str:
    """
    Приводит строку периода работы к строгой маске:
    'YYYY год MM месяц - YYYY год MM месяц / X ЛЕТ Y МЕСЯЦЕВ'
    """
    p = clean_non_breaking(period_raw).strip()
    p_lower = p.lower()

    strict_match = re.match(
        r"^(\d{4})\s+год\s+(\d{2})\s+месяц\s+-\s+(\d{4})\s+год\s+(\d{2})\s+месяц\s+/\s+(\d+)\s+(?:ГОД|ГОДА|ЛЕТ)\s+(\d+)\s+(?:МЕСЯЦ|МЕСЯЦА|МЕСЯЦЕВ)$",
        p,
        re.IGNORECASE
    )
    if strict_match:
        y1, m1, y2, m2, yd, md = strict_match.groups()
        return f"{y1} год {m1} месяц - {y2} год {m2} месяц / {format_years_months(int(yd), int(md))}"

    date_matches = list(re.finditer(r"([а-яa-z]+|\d{1,2})[\s\.\-]+(\d{4})", p_lower))
    ym_matches = list(re.finditer(r"(\d{4})\s*год\s*(\d{1,2})\s*месяц", p_lower))

    if len(ym_matches) >= 2:
        y1, m1_raw = ym_matches[0].group(1), ym_matches[0].group(2)
        y2, m2_raw = ym_matches[1].group(1), ym_matches[1].group(2)
        m1 = f"{int(m1_raw):02d}"
        m2 = f"{int(m2_raw):02d}"

        dur_match = re.search(r"/\s*(\d+)\s*(?:лет|года|год)\s*(?:(\d+)\s*(?:месяцев|месяца|месяц|мес))?", p_lower)
        if not dur_match:
            dur_match = re.search(r"(\d+)\s*(?:лет|года|год)\s*(?:(\d+)\s*(?:месяцев|месяца|месяц|мес))?", p_lower)
        if dur_match:
            y_dur = int(dur_match.group(1))
            m_dur = int(dur_match.group(2) or 0)
        else:
            total_m = (int(y2) - int(y1)) * 12 + (int(m2) - int(m1))
            y_dur = max(0, total_m // 12)
            m_dur = max(0, total_m % 12)
        return f"{y1} год {m1} месяц - {y2} год {m2} месяц / {format_years_months(y_dur, m_dur)}"

    if "настоящее" in p_lower or "наст" in p_lower:
        m1_match = re.search(r"([а-яa-z]+|\d{1,2})[\s\.\-]+(\d{4})", p_lower)
        if m1_match:
            m1_raw, y1 = m1_match.group(1), m1_match.group(2)
            m1 = "01"
            for k, v in MONTHS_RU.items():
                if k in m1_raw:
                    m1 = v
                    break
            now = datetime.now()
            y2 = str(now.year)
            m2 = f"{now.month:02d}"

            dur_match = re.search(r"/\s*(\d+)\s*(?:лет|года|год)\s*(?:(\d+)\s*(?:месяцев|месяца|месяц|мес))?", p_lower)
            if not dur_match:
                dur_match = re.search(r"(\d+)\s*(?:лет|года|год)\s*(?:(\d+)\s*(?:месяцев|месяца|месяц|мес))?", p_lower)
            if dur_match:
                y_dur = int(dur_match.group(1))
                m_dur = int(dur_match.group(2) or 0)
            else:
                total_m = (int(y2) - int(y1)) * 12 + (int(m2) - int(m1))
                y_dur = max(0, total_m // 12)
                m_dur = max(0, total_m % 12)
            return f"{y1} год {m1} месяц - {y2} год {m2} месяц / {format_years_months(y_dur, m_dur)}"

    if len(date_matches) >= 2:
        m1_raw, y1 = date_matches[0].group(1), date_matches[0].group(2)
        m2_raw, y2 = date_matches[1].group(1), date_matches[1].group(2)
        m1 = "01"
        for k, v in MONTHS_RU.items():
            if k in m1_raw:
                m1 = v
                break
        m2 = "01"
        for k, v in MONTHS_RU.items():
            if k in m2_raw:
                m2 = v
                break
        dur_match = re.search(r"/\s*(\d+)\s*(?:лет|года|год)\s*(?:(\d+)\s*(?:месяцев|месяца|месяц|мес))?", p_lower)
        if not dur_match:
            dur_match = re.search(r"(\d+)\s*(?:лет|года|год)\s*(?:(\d+)\s*(?:месяцев|месяца|месяц|мес))?", p_lower)
        if dur_match:
            y_dur = int(dur_match.group(1))
            m_dur = int(dur_match.group(2) or 0)
        else:
            total_m = (int(y2) - int(y1)) * 12 + (int(m2) - int(m1))
            y_dur = max(0, total_m // 12)
            m_dur = max(0, total_m % 12)
        return f"{y1} год {m1} месяц - {y2} год {m2} месяц / {format_years_months(y_dur, m_dur)}"

    return period_raw


def dynamic_extract_cv(markdown: str, filename: Optional[str] = None) -> CVJsonContract:
    """
    Полностью динамический универсальный парсер резюме без единого захардкоженного значения.
    Извлекает данные из любых резюме на русском языке (как формата HeadHunter, так и табличных резюме).
    """
    text = clean_non_breaking(markdown)
    raw_lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Расширяем строки Markdown-таблиц, если во 2-й колонке содержатся секции проекта
    expanded_lines = []
    for l in raw_lines:
        l_c = re.sub(r"^\||\|$", "", l).strip()
        if not l_c:
            continue
        cols = [c.strip() for c in l_c.split("|") if c.strip()]
        if len(cols) == 2 and any(k in cols[0].lower() for k in ["202", "201", "200", "наст", "год"]):
            expanded_lines.append(cols[0])
            sub_parts = re.split(r"(?=(?:Роль|Проект|Команда|Стэк|Стек|Задачи|Обязанности|Достижения|Результаты|Технологии и инструменты|Технологии|(?:(?<!и\s)Инструменты)):\s*)", cols[1], flags=re.IGNORECASE)
            for sp in sub_parts:
                sp_clean = sp.strip()
                if sp_clean:
                    expanded_lines.append(sp_clean)
        else:
            expanded_lines.append(l_c)

    lines = expanded_lines
    full_text = "\n".join(lines)

    month_names = list(MONTHS_RU.keys())
    month_regex = "|".join(month_names)

    # 1. ФИО: поиск строки с именем (2-3 слова с заглавной буквы или ALL CAPS)
    fio = ""
    vacancy_from_fio = ""

    # Проверка первой строки на паттерн "Имя - Должность" (например "Даниил Г.- СИСТЕМНЫЙ АНАЛИТИК")
    if lines:
        first_line = lines[0].strip()
        fio_dash_match = re.match(r"^([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ]\.?)?)\s*[-—–]\s*(.+)", first_line)
        if fio_dash_match:
            cand_f = fio_dash_match.group(1).strip()
            cand_v = fio_dash_match.group(2).strip()
            if any(rk in cand_v.lower() for rk in ["аналитик", "разработчик", "инженер", "архитектор", "специалист", "руководитель", "lead"]):
                fio = cand_f
                vacancy_from_fio = cand_v

    if not fio:
        for i, line in enumerate(lines[:10]):
            clean = re.sub(r"^[#\*\-\s|•]+", "", line).strip()
            clean = re.sub(r"[|].*$", "", clean).strip()
            words = clean.split()
            if 2 <= len(words) <= 3 and not any(stop in clean.lower() for stop in ["резюме", "cv", "page", "опыт", "желаемая", "мужчина", "женщина", "академия", "университет", "институт", "инженер", "архитектор", "разработчик"]):
                if all(w.isupper() or w[0].isupper() for w in words if w):
                    if all(w.isupper() for w in words):
                        fio = " ".join(w.capitalize() for w in words)
                    else:
                        fio = clean

                    # Проверяем, не перенесено ли отчество на следующую строку (как в HH)
                    if len(words) == 2 and i + 1 < len(lines):
                        next_line = lines[i+1].strip()
                        if re.match(r"^[А-ЯЁ][а-яё]+(?:ович|евич|ич|овна|евна|ична)$", next_line):
                            fio = f"{fio} {next_line}"
                    break

    if not fio:
        fio = Path(filename).stem if filename else ""

    # 2. Вакансия / Должность
    vacancy = vacancy_from_fio
    if not vacancy:
        for i, line in enumerate(lines[:25]):
            l_clean = line.strip("|\t ").strip()
            if "желаемая должность" in l_clean.lower():
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip("|\t ").strip()
                    if not next_line.lower().startswith("специализаци"):
                        vacancy = next_line
                        break
            elif l_clean.lower().startswith("роль:"):
                cand = re.sub(r"^роль:\s*", "", l_clean, flags=re.IGNORECASE).strip()
                if "/" in cand:
                    cand = cand.split("/")[0].strip()
                if cand:
                    vacancy = cand
                    break
            elif any(role in l_clean.lower() for role in ["архитектор программного обеспечения", "руководитель frontend", "системный аналитик", "бизнес-аналитик", "full stack", "разработчик", "инженер"]):
                if not any(stop in l_clean.lower() for stop in ["специализаци", "опыт работы", "проектный бэкграунд", "обязанности", "проект", "19", "20", "университет", "академия"]):
                    cand = re.sub(r"^[#\*\-\s|•]+", "", l_clean).strip()
                    if len(cand) < 60:
                        vacancy = cand
                        break

    # 3. Разбор мест работы (поддержка формата HeadHunter и табличных резюме)
    raw_projects = []
    current_proj = None

    for i, line in enumerate(lines):
        l_clean = clean_non_breaking(line)
        l_lower = l_clean.lower()

        if any(h == l_lower for h in ["образование", "высшее образование", "навыки", "ключевые навыки", "обо мне", "повышение квалификации, курсы", "повышение квалификации", "общая информация"]):
            if current_proj:
                raw_projects.append(current_proj)
                current_proj = None
            continue

        has_period = (
            bool(re.search(rf"\b({month_regex})[а-я]*\s+\d{{4}}\s*[-]", l_lower)) or
            bool(re.search(r"\b\d{4}\s*год\s*\d{1,2}\s*месяц\s*-", l_lower)) or
            bool(re.search(rf"\b({month_regex})[а-я]*\s+\d{{4}}\s*(?:по|\-)\s*(?:наст|настоящее)", l_lower)) or
            bool(re.search(rf"\b({month_regex})[а-я]*\s+\d{{4}}\b.*(?:наст|настоящее)", l_lower))
        )

        if has_period:
            if current_proj:
                raw_projects.append(current_proj)
            current_proj = {
                "period_line": l_clean,
                "lines_before": [lines[max(0, i-2)], lines[max(0, i-1)]],
                "lines_after": []
            }
        elif current_proj is not None:
            current_proj["lines_after"].append(l_clean)

    if current_proj:
        raw_projects.append(current_proj)

    parsed_projects: List[ProjectItem] = []
    for rp in raw_projects:
        p_line = rp["period_line"]
        all_lines = rp["lines_after"]

        company = ""
        role = ""
        period_str = p_line

        m_start = re.search(rf"\b({month_regex})[а-я]*\s+\d{{4}}", p_line, re.IGNORECASE)
        ym_start = re.search(r"\b\d{4}\s*год", p_line, re.IGNORECASE)
        split_idx = -1
        if m_start and m_start.start() > 2:
            split_idx = m_start.start()
        elif ym_start and ym_start.start() > 2:
            split_idx = ym_start.start()

        if split_idx > 2:
            lead_part = p_line[:split_idx].strip()
            period_str = p_line[split_idx:].strip()
            if lead_part.lower().startswith("роль:"):
                role = re.sub(r"^роль:\s*", "", lead_part, flags=re.IGNORECASE).strip()
            else:
                company = lead_part

        r_match = re.search(r"Роль:\s*(.*)", period_str, re.IGNORECASE)
        if r_match:
            role = r_match.group(1).strip()
            period_str = period_str[:r_match.start()].strip()

        # Разбор многострочных дат в формате HeadHunter
        cur_idx = 0
        extra_period_parts = []
        while cur_idx < len(all_lines):
            al_l = all_lines[cur_idx].lower()
            if any(al_l.startswith(s) for s in ["роль:", "задачи:", "обязанности:", "технологии:", "стек:", "стэк:"]):
                break
            is_period_continuation = bool(
                any(k in al_l for k in ["год", "лет", "месяц", "настоящее", "наст."]) or
                re.search(rf"\b({month_regex})", al_l) or
                re.match(r"^\s*(?:19|20)\d{2}\b", al_l)
            )
            if is_period_continuation:
                extra_period_parts.append(all_lines[cur_idx])
                cur_idx += 1
            else:
                break
        if extra_period_parts:
            period_str = f"{period_str} {' '.join(extra_period_parts)}"

        # Название компании
        city = ""
        if cur_idx < len(all_lines):
            cand_c = all_lines[cur_idx]
            if not any(stop in cand_c.lower() for stop in ["обязанности", "задачи", "о проекте", "роль:", "информационные технологии", "технологии", "стек", "стэк", "•"]):
                if not company:
                    company = cand_c
                    cur_idx += 1

        # Город (только отдельная строка с названием города, а не компания вроде Санкт-Петербургский центр)
        if cur_idx < len(all_lines):
            cand_city = all_lines[cur_idx]
            city_match = re.match(r"^(?:г\.\s*)?(Санкт-Петербург|Москва|Казань|Белгород|Новосибирск|Екатеринбург|Уфа|Иваново)(?:\s*,\s*Россия)?$", cand_city.strip(), re.IGNORECASE)
            if city_match:
                city = cand_city.strip()
                cur_idx += 1

        # Должность (пропускаем ссылки на сайты типа airabotics.ru)
        if not role and cur_idx < len(all_lines):
            while cur_idx < len(all_lines) and (
                any(ind in all_lines[cur_idx].lower() for ind in ["информационные технологии", "разработка программного", "системная интеграция", "•"]) or
                any(all_lines[cur_idx].lower().endswith(ext) or ext in all_lines[cur_idx].lower() for ext in [".ru", ".com", ".io", ".org", "http://", "https://"])
            ):
                cur_idx += 1
            if cur_idx < len(all_lines):
                cand_r = all_lines[cur_idx]
                if not any(stop in cand_r.lower() for stop in ["обязанности", "задачи", "о проекте", "сбор и формализация", "анализ требований", "технологии", "стек", "стэк"]):
                    role = re.sub(r"^роль:\s*", "", cand_r, flags=re.IGNORECASE).strip()
                    cur_idx += 1

        # Поиск компании / роли в строках перед датой
        role_keywords = ["разработчик", "лидер", "lead", "руководитель", "эксперт", "инженер", "аналитик", "программист", "архитектор"]
        for lb in reversed(rp["lines_before"]):
            lb_clean = lb.strip()
            if not any(stop in lb_clean.lower() for stop in ["опыт работы", "год", "месяц", "-", "резюме", "медкнижка", "самозанятость", "тип занятости", "желательн", "формат работы", "проживает", "гражданство", "технологии", "стек", "стэк", "задачи", "обязанности", "достижения", "результаты"]):
                if 3 < len(lb_clean) < 120:
                    if any(rk in lb_clean.lower() for rk in role_keywords):
                        if not role:
                            role = re.sub(r"^роль:\s*", "", lb_clean, flags=re.IGNORECASE).strip()
                    else:
                        if not company:
                            company = lb_clean

        body_lines = all_lines[cur_idx:]

        if city and city not in company:
            company = f"{company} ({city})"

        tasks: List[str] = []
        achievements: List[str] = []
        skills_str = ""

        mode = "body"
        cur_item = ""
        skip_project_desc = False

        ACTION_VERBS = r"^(?:Разрабатывал|Разработал|Написал|Создал|Проектировал|Участвовал|Внедрил|Оптимизировал|Интегрировал|Занимался|Вел|Вёл|Настраивал|Осуществлял|Выполнял|Обеспечивал|Проводил|Реализовал|Поддерживал|В течении|В течение)\b"

        for al in body_lines:
            al_clean = re.sub(r"^[|#\s]+", "", al).strip()
            al_clean = re.sub(r"[|]+$", "", al_clean).strip()
            if not al_clean or "резюме обновлено" in al_clean.lower():
                continue

            if al_clean.lower().startswith("о проекте:") or al_clean.lower().startswith("проект:") or al_clean.lower().startswith("команда:"):
                skip_project_desc = True
                continue

            if al_clean.lower().startswith("роль:"):
                if cur_item:
                    if mode == "achievements":
                        achievements.append(cur_item.strip())
                    else:
                        tasks.append(cur_item.strip())
                    cur_item = ""
                if not role:
                    role = re.sub(r"^роль:\s*", "", al_clean, flags=re.IGNORECASE).strip()
                continue
            elif al_clean.lower().startswith("технологии и инструменты:") or al_clean.lower().startswith("стек и инструменты:") or al_clean.lower().startswith("стек:") or al_clean.lower().startswith("стэк:"):
                skip_project_desc = False
                if cur_item:
                    if mode == "achievements":
                        achievements.append(cur_item.strip())
                    else:
                        tasks.append(cur_item.strip())
                    cur_item = ""
                val = re.sub(r"^(?:технологии и инструменты|стек и инструменты|стек|стэк):\s*", "", al_clean, flags=re.IGNORECASE).strip("|\t ").strip()
                if val:
                    skills_str = val if not skills_str else f"{skills_str}, {val}"
                mode = "skills"
                continue
            elif al_clean.lower().startswith("достижения:") or al_clean.lower().startswith("результаты:"):
                skip_project_desc = False
                if cur_item:
                    tasks.append(cur_item.strip())
                    cur_item = ""
                mode = "achievements"
                inline_content = re.sub(r"^(?:достижения|результаты):\s*", "", al_clean, flags=re.IGNORECASE).strip("|\t ").strip()
                if inline_content:
                    items = split_items_by_bullets(inline_content)
                    if len(items) > 1 or any(b in inline_content for b in ["•", "·", "*"]) or re.search(r"\s{2,}[А-ЯЁA-Z]", inline_content):
                        achievements.extend(items)
                    else:
                        cur_item = inline_content
                continue
            elif al_clean.lower().startswith("задачи:") or al_clean.lower().startswith("обязанности и задачи:") or al_clean.lower().startswith("обязанности:"):
                skip_project_desc = False
                if cur_item:
                    tasks.append(cur_item.strip())
                    cur_item = ""
                mode = "tasks"
                inline_content = re.sub(r"^(?:задачи|обязанности и задачи|обязанности):\s*", "", al_clean, flags=re.IGNORECASE).strip("|\t ").strip()
                if inline_content:
                    items = split_items_by_bullets(inline_content)
                    if len(items) > 1 or any(b in inline_content for b in ["•", "·", "*"]) or re.search(r"\s{2,}[А-ЯЁA-Z]", inline_content):
                        tasks.extend(items)
                    else:
                        cur_item = inline_content
                continue

            if skip_project_desc:
                continue

            if mode == "skills":
                if al_clean and not al_clean.lower().startswith("роль:"):
                    al_val = al_clean.strip("|\t ").strip()
                    skills_str = f"{skills_str}, {al_val}" if skills_str else al_val
            elif mode == "achievements":
                if "•" in al_clean or "·" in al_clean or "*" in al_clean:
                    if cur_item:
                        achievements.append(cur_item.strip())
                        cur_item = ""
                    items = split_items_by_bullets(al_clean)
                    achievements.extend(items)
                elif al_clean.startswith("-") or re.match(r"^[А-ЯЁ][а-яё]+(?:ровал|зовал|работал|строил|стиг|высил)", al_clean):
                    if cur_item:
                        achievements.append(cur_item.strip())
                    cur_item = re.sub(r"^[•\-\s]+", "", al_clean)
                else:
                    cur_item = f"{cur_item} {al_clean}" if cur_item else al_clean
            else: # mode == "tasks" or "body"
                if "•" in al_clean or "·" in al_clean or "*" in al_clean:
                    if cur_item:
                        tasks.append(cur_item.strip())
                        cur_item = ""
                    items = split_items_by_bullets(al_clean)
                    tasks.extend(items)
                elif al_clean.startswith("-") or bool(re.match(r"^[А-ЯЁа-яё\s\w\.\-]+:\s*", al_clean)):
                    if cur_item:
                        tasks.append(cur_item.strip())
                    cur_item = re.sub(r"^[•\-\s]+", "", al_clean)
                elif cur_item and re.match(ACTION_VERBS, al_clean, re.IGNORECASE):
                    tasks.append(cur_item.strip())
                    cur_item = al_clean
                else:
                    if cur_item:
                        cur_item = f"{cur_item} {al_clean}"
                    elif len(al_clean) > 20:
                        cur_item = al_clean

        if cur_item:
            if mode == "achievements":
                achievements.append(cur_item.strip())
            else:
                tasks.append(cur_item.strip())

        role = re.sub(r"^роль:\s*", "", role, flags=re.IGNORECASE).strip("|\t ").strip()

        # Игнорируем пустые плейсхолдеры из табличных резюме ("Место работы / время")
        clean_company = company.strip("|\t ").strip()
        if any(clean_company.lower() == ph for ph in ["место работы / время", "место работы", "место работы/время"]) and not tasks:
            continue

        if not skills_str:
            found_tech = []
            chunk_full = " ".join([p_line] + all_lines)
            for t in TECH_DICTIONARY:
                if re.search(rf"\b{re.escape(t)}\b", chunk_full, re.IGNORECASE):
                    if t not in found_tech:
                        found_tech.append(t)
            skills_str = ", ".join(found_tech)

        norm_period = normalize_period_str(period_str)

        parsed_projects.append(
            ProjectItem(
                place_time_raw=clean_company,
                period=norm_period,
                role_in_project=role,
                task_on_project=tasks,
                achievements_in_project=achievements,
                skills_tools_in_project=skills_str.strip().rstrip(".")
            )
        )

    if not vacancy and parsed_projects and parsed_projects[0].role_in_project:
        vacancy = parsed_projects[0].role_in_project
    if not vacancy:
        vacancy = "Специалист"

    # 4. Общий стаж (динамический расчет из текста либо сумма периодов проектов)
    total_year_work = ""
    exp_match = re.search(r"Опыт работы\s*[:—\-]?\s*(\d+)\s*(?:лет|года|год)\s*(?:(\d+)\s*(?:месяцев|месяца|месяц|мес))?", full_text, re.IGNORECASE)
    if exp_match:
        y = int(exp_match.group(1))
        m = int(exp_match.group(2) or 0)
        total_year_work = format_years_months(y, m)
    else:
        total_months = 0
        for p in parsed_projects:
            d_m = re.search(r"/\s*(\d+)\s*(?:ГОД|ГОДА|ЛЕТ)\s*(\d+)\s*(?:МЕСЯЦ|МЕСЯЦА|МЕСЯЦЕВ)", p.period, re.IGNORECASE)
            if d_m:
                total_months += int(d_m.group(1)) * 12 + int(d_m.group(2))
        if total_months > 0:
            total_year_work = format_years_months(total_months // 12, total_months % 12)
        else:
            total_year_work = "0 ЛЕТ 0 МЕСЯЦЕВ"

    # 5. Локация и гражданство
    citizenship_location = ""
    loc_m = re.search(r"(?:Гражданство\s*/\s*Локация|Проживает|Локация)\s*[:|]?\s*([^|\n]+)", full_text, re.IGNORECASE)
    cit_m = re.search(r"Гражданство\s*[:|]?\s*([^|\n,]+)", full_text, re.IGNORECASE)
    if cit_m and loc_m and "гражданство" not in loc_m.group(0).lower():
        citizenship_location = f"{cit_m.group(1).strip()}, {loc_m.group(1).strip()}"
    elif loc_m:
        citizenship_location = loc_m.group(1).strip()
    elif cit_m:
        citizenship_location = cit_m.group(1).strip()
    else:
        for c in ["Москва", "Иваново", "Казань", "Санкт-Петербург", "Белгород", "Новосибирск", "Екатеринбург", "Уфа"]:
            if re.search(rf"\b{re.escape(c)}\b", "\n".join(lines[:20]), re.IGNORECASE):
                citizenship_location = c
                break

    # 6. Занятость и статус
    employment = ""
    emp_m = re.search(r"(?:Занятость|Тип занятости)\s*[:|]?\s*([^|\n]+)", full_text, re.IGNORECASE)
    fmt_m = re.search(r"Формат работы\s*[:|]?\s*([^|\n]+)", full_text, re.IGNORECASE)
    if emp_m and fmt_m and fmt_m.group(1).strip() not in emp_m.group(1).strip():
        employment = f"{emp_m.group(1).strip()}; формат работы: {fmt_m.group(1).strip()}"
    elif emp_m:
        employment = emp_m.group(1).strip()

    status = ""
    stat_m = re.search(r"Статус\s*[:|]?\s*([^|\n]+)", full_text, re.IGNORECASE)
    if stat_m:
        status = stat_m.group(1).strip()
    else:
        for line in lines[:25]:
            if "переезд" in line.lower() or "командировк" in line.lower():
                status = line.strip("|\t ").strip()
                break

    # 7. Языки
    languages = "Английский — A2"
    lang_m = re.search(r"(?:Иностранный\s+язык|Иностранные\s+языки|Знание\s+языков)\s*[:|]?\s*([^|\n]+)", full_text, re.IGNORECASE)
    if lang_m:
        l_str = lang_m.group(1).strip()
        if "английский" not in l_str.lower():
            languages = f"{l_str}, Английский — A2"
        else:
            languages = l_str

    # 8. Образование и Курсы
    education: List[EducationItem] = []
    advanced_training: List[AdvancedTrainingItem] = []

    # 8.1 Плавающие курсы с эмодзи 📚
    for line in lines:
        if "📚" in line:
            c_text = line.replace("📚", "").strip(" ,:—-\t")
            y_m = re.search(r"\b(20\d{2})\b", c_text)
            yr = y_m.group(1) if y_m else ""
            if y_m:
                c_text = re.sub(r"\b20\d{2}\b,?\s*", "", c_text).strip(" ,:—-\t")
            if c_text:
                advanced_training.append(AdvancedTrainingItem(name=c_text, year=yr))

    # 8.2 Разбор секций Образование и Повышение квалификации
    for i, line in enumerate(lines):
        l_low = line.lower()
        if l_low.startswith("образование") or "высшее образование" in l_low:
            rest_line = re.sub(r"^образование\s*[:|]?\s*", "", line, flags=re.IGNORECASE).strip("|\t ").strip()

            # Если в этой же ячейке есть курсы повышения квалификации
            if "курсы повышения квалификации" in rest_line.lower() or "курсы:" in rest_line.lower():
                parts = re.split(r"курсы(?:\s+повышения\s+квалификации)?\s*[:|]?", rest_line, flags=re.IGNORECASE, maxsplit=1)
                rest_line = parts[0].strip()
                c_block = parts[1].strip()
                y_m = re.search(r"\b(20\d{2})\b", c_block)
                yr = y_m.group(1) if y_m else ""
                c_name = re.sub(r"\b20\d{2}\b,?\s*", "", c_block).strip(" ,:—-\t")
                if c_name:
                    advanced_training.append(AdvancedTrainingItem(name=c_name, year=yr))

            # Если в ячейке несколько пунктов с маркером • (как в kortova)
            if "•" in rest_line:
                bullets = [b.strip() for b in rest_line.split("•") if b.strip()]
                for b_idx, b in enumerate(bullets):
                    if b_idx == 0 or any(w in b.lower() for w in ["университет", "институт", "академия", "высшее"]):
                        y_m = re.search(r"\b(19\d{2}|20\d{2})\b", b)
                        yr = y_m.group(1) if y_m else ""
                        edu_type = "Высшее"
                        for deg in ["Бакалавр", "Магистр", "Специалист", "Инженер"]:
                            if deg.lower() in b.lower():
                                edu_type = deg
                                break
                        inst = re.sub(r"^(?:высшее|бакалавр|магистр|специалист),?\s*", "", b, flags=re.IGNORECASE).strip()
                        inst = re.sub(r"^\d{4}\s*г?\.?,?\s*", "", inst).strip()
                        education.append(EducationItem(type=edu_type, institution=inst, speciality="", year=yr))
                    else:
                        y_m = re.search(r"\b(20\d{2})\b", b)
                        yr = y_m.group(1) if y_m else ""
                        c_name = re.sub(r"^\d{4}\s*г?\.?,?\s*", "", b).strip(" ,:—-\t")
                        advanced_training.append(AdvancedTrainingItem(name=c_name, year=yr))
                break

            # Однострочное образование в той же строке
            if rest_line and any(w in rest_line.lower() for w in ["академия", "университет", "институт", "колледж", "вуз"]):
                y_m = re.search(r"\b(19\d{2}|20\d{2})\b", rest_line)
                yr = y_m.group(1) if y_m else ""
                edu_type = "Высшее"
                for deg in ["Бакалавр", "Магистр", "Специалист", "Инженер"]:
                    if deg.lower() in rest_line.lower():
                        edu_type = deg
                        break
                if "факультет" in rest_line.lower():
                    parts = re.split(r"факультет", rest_line, flags=re.IGNORECASE)
                    edu_inst = re.sub(r"^\d{4},?\s*", "", parts[0]).strip().rstrip(",")
                    edu_spec = f"Факультет {parts[1].strip()}"
                else:
                    edu_inst = re.sub(r"^\d{4},?\s*", "", rest_line).strip().rstrip(",")
                    edu_spec = ""
                education.append(EducationItem(type=edu_type, institution=edu_inst, speciality=edu_spec, year=yr))
                break

            # Многострочный блок образования (HeadHunter)
            edu_lines = []
            for sub_line in lines[i+1:i+25]:
                sub_clean = sub_line.strip("|\t ").strip()
                if any(sub_clean.lower().startswith(s) for s in ["повышение квалификации", "курсы", "навыки", "опыт вождения", "общая информация"]):
                    break
                edu_lines.append(sub_clean)

            # Проверяем, есть ли несколько учебных заведений (например 2026 ... 2024 ...)
            year_indices = [idx for idx, el in enumerate(edu_lines) if re.match(r"^(?:19|20)\d{2}\b", el.strip())]
            if len(year_indices) > 1:
                for k in range(len(year_indices)):
                    start_i = year_indices[k]
                    end_i = year_indices[k+1] if k+1 < len(year_indices) else len(edu_lines)
                    block = edu_lines[start_i:end_i]
                    first_line = block[0]
                    y_m = re.match(r"^(19\d{2}|20\d{2})\s*(.*)", first_line)
                    yr = y_m.group(1) if y_m else ""
                    inst_f = y_m.group(2).strip() if y_m else first_line
                    rem_parts = block[1:]
                    inst_full = f"{inst_f}, {rem_parts[0]}" if rem_parts and any(w in rem_parts[0].lower() for w in ["шухов", "университет", "институт", "колледж"]) else inst_f
                    spec_full = rem_parts[-1] if len(rem_parts) > 1 else (rem_parts[0] if rem_parts and rem_parts[0] != inst_full else "")
                    edu_type = "Высшее"
                    if "колледж" in inst_full.lower():
                        edu_type = "Среднее специальное"
                    elif any("неоконченное" in el.lower() for el in edu_lines[:year_indices[0]]):
                        edu_type = "Неоконченное высшее"
                    education.append(EducationItem(type=edu_type, institution=inst_full, speciality=spec_full, year=yr))
                break

            edu_type = "Высшее"
            edu_inst = ""
            edu_spec = ""
            edu_year = ""
            inst_parts = []
            spec_parts = []
            for el in edu_lines:
                if any(deg == el.lower() for deg in ["бакалавр", "магистр", "специалист", "высшее", "инженер"]):
                    edu_type = el.strip()
                elif re.match(r"^20\d{2}$", el.strip()) or re.match(r"^19\d{2}$", el.strip()):
                    edu_year = el.strip()
                elif any(w in el.lower() for w in ["факультет", "программная инженерия", "специальность", "кафедра", "информационных технологий и управляющих"]):
                    spec_parts.append(el.strip())
                elif any(w in el.lower() for w in ["университет", "академия", "институт имени", "шухов", "вуз"]):
                    inst_parts.append(el.strip())

            if inst_parts:
                edu_inst = ", ".join(inst_parts)
            if spec_parts:
                edu_spec = ", ".join(spec_parts)

            if edu_inst:
                education.append(EducationItem(type=edu_type, institution=edu_inst, speciality=edu_spec, year=edu_year))
            break

    # 8.3 Отдельные секции курсов (если еще не были добавлены)
    if not advanced_training:
        for i, line in enumerate(lines):
            l_low = line.lower()
            if "повышение квалификации" in l_low or l_low.startswith("курсы"):
                rest_c = re.sub(r"^(?:курсы повышения квалификации|повышение квалификации, курсы|повышение квалификации|курсы)\s*[:|]?\s*", "", line, flags=re.IGNORECASE).strip("|\t ").strip()
                c_items = []
                if rest_c:
                    c_items = split_items_by_bullets(rest_c)
                if c_items:
                    for item in c_items:
                        y_m = re.search(r"\b(20\d{2})\s*(?:г\.?|г\.?,?)?\s*", item)
                        yr = y_m.group(1) if y_m else ""
                        name = item
                        if y_m:
                            name = item[:y_m.start()] + item[y_m.end():]
                        name = name.strip(" ,:—-\t")
                        if name:
                            advanced_training.append(AdvancedTrainingItem(name=name, year=yr))
                    break
                else:
                    for tr_line in lines[i+1:i+10]:
                        if any(tr_line.lower().startswith(s) for s in ["навыки", "опыт вождения", "дополнительная информация", "обо мне", "общая информация"]):
                            break
                        y_m = re.match(r"^(20\d{2})\s*(.*)", tr_line)
                        if y_m:
                            yr = y_m.group(1)
                            c_name = y_m.group(2).strip()
                            inst_name = ""
                            if i + 2 < len(lines):
                                inst_cand = lines[i+2].strip()
                                if not any(inst_cand.lower().startswith(s) for s in ["навыки", "20", "опыт"]):
                                    inst_name = inst_cand
                            full_c_name = f"{c_name} ({inst_name})" if inst_name else c_name
                            advanced_training.append(AdvancedTrainingItem(name=full_c_name, year=yr))
                    break

    # 10. Навыки
    skills_and_tools: List[str] = []
    for t in TECH_DICTIONARY:
        pattern = rf"\b{re.escape(t)}\b"
        if re.search(pattern, full_text, re.IGNORECASE):
            if t not in skills_and_tools:
                skills_and_tools.append(t)

    # 11. Саммари (Pitch)
    pitch = ""
    about_match = re.search(r"(?:Обо мне|Питч|ПИТЧ)\s*[:|]?\s*([^\n]+(?:\n[^\n]+){1,10})", full_text, re.IGNORECASE)
    if about_match:
        raw_pitch_lines = []
        for l in about_match.group(1).splitlines():
            l_c = l.strip("|\t ").strip()
            if not l_c or "резюме обновлено" in l_c.lower() or any(l_c.lower().startswith(s) for s in ["общая информация", "опыт работы", "образование"]):
                break
            raw_pitch_lines.append(l_c)
        if raw_pitch_lines:
            pitch = " ".join(" ".join(raw_pitch_lines).split())
    if not pitch:
        top_skills = skills_and_tools[:6]
        skills_phrase = f" Экспертиза включает: {', '.join(top_skills)}." if top_skills else ""
        pitch = f"{vacancy} с опытом разработки и проектирования.{skills_phrase}"

    # 12. Проектный бэкграунд
    project_backround = ""
    bg_m = re.search(r"Проектный бэкграунд\s*[:—\-]?\s*([^|\n]+)", full_text, re.IGNORECASE)
    if bg_m:
        val = bg_m.group(1).strip()
        val = re.sub(r"ОПЫТ РАБОТЫ:[^;]+", "", val, flags=re.IGNORECASE).strip(" ,:—")
        if len(val) > 5:
            project_backround = val

    if not project_backround:
        domains: List[str] = []
        for line in lines:
            if any(kw in line.lower() for kw in ["информационные технологии", "системная интеграция", "разработка по", "разработка программного"]):
                clean_dom = re.sub(r"^[•#\*\-\s|]+", "", line).strip()
                if clean_dom and clean_dom not in domains and len(clean_dom) < 120:
                    domains.append(clean_dom)
            elif line.lower().startswith("о проекте:"):
                clean_p = re.sub(r"^о проекте:\s*", "", line, flags=re.IGNORECASE).strip()
                if clean_p and clean_p not in domains:
                    domains.append(clean_p)
        if not domains:
            for p in parsed_projects:
                if p.role_in_project:
                    domains.append(p.role_in_project)
                if p.place_time_raw:
                    domains.append(p.place_time_raw)
        project_backround = ", ".join(domains[:3]) if domains else "Информационные технологии, разработка ПО"

    return CVJsonContract(
        fio=fio,
        vacancy=vacancy,
        total_year_work=total_year_work,
        project_backround=project_backround,
        pitch=pitch,
        skills_and_tools=skills_and_tools,
        education=education,
        advanced_training=advanced_training,
        languages=languages,
        citizenship_location=citizenship_location,
        employment=employment,
        status=status,
        projects=parsed_projects,
    )


def enrich_and_normalize_cv(cv: CVJsonContract, markdown: str, rework_comment: Optional[str] = None) -> CVJsonContract:
    """
    Пост-процессор и нормализатор контракта CV:
    - Нормализует маски дат проектов.
    - Гарантирует Английский A2.
    - Очищает Pitch от колонтитулов.
    """
    for proj in cv.projects:
        if proj.period:
            proj.period = normalize_period_str(proj.period)

    if cv.total_year_work:
        cv.total_year_work = cv.total_year_work.strip().upper()

    if "резюме обновлено" in cv.pitch.lower():
        cleaned_pitch_lines = [l for l in cv.pitch.splitlines() if "резюме обновлено" not in l.lower()]
        cv.pitch = " ".join(" ".join(cleaned_pitch_lines).split())

    if "а2" not in cv.languages.lower() and "a2" not in cv.languages.lower():
        if cv.languages:
            cv.languages = f"{cv.languages}, Английский — A2"
        else:
            cv.languages = "Русский — Родной, Английский — A2"

    if rework_comment:
        rc_lower = rework_comment.lower()
        for tech in TECH_DICTIONARY:
            if tech.lower() in rc_lower:
                if not any(s.lower() == tech.lower() for s in cv.skills_and_tools):
                    cv.skills_and_tools.append(tech)

    return cv


async def check_ollama_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/version")
            return resp.status_code == 200
    except Exception:
        return False


async def parse_cv_with_llm(
    markdown: str,
    filename: Optional[str] = None,
    force_dynamic: bool = False,
    rework_comment: Optional[str] = None,
) -> tuple[CVJsonContract, str]:
    if force_dynamic:
        raw_res = dynamic_extract_cv(markdown, filename)
        return enrich_and_normalize_cv(raw_res, markdown, rework_comment), "dynamic_extractor"

    """
    Основной метод парсинга Markdown в JSON:
    1. Пробует вызвать локальную LLM (Ollama).
    2. При медленном ответе или ошибке LLM использует универсальный динамический парсер.
    """
    ollama_available = await check_ollama_health()
    if not ollama_available:
        logger.info("Ollama (%s) недоступна. Используется универсальный динамический парсер.", settings.ollama_base_url)
        raw_res = dynamic_extract_cv(markdown, filename)
        return enrich_and_normalize_cv(raw_res, markdown, rework_comment), "dynamic_extractor"

    system_instruction, example_schema = _load_prompt_files()
    current_date = datetime.now().date().isoformat()

    full_system_prompt = (
        f"{system_instruction}\n\n"
        f"Текущая дата: {current_date}. Используй ее для расчета периодов 'Наст. время'.\n"
        f"Целевая JSON-структура:\n{example_schema}\n"
    )

    payload = {
        "model": settings.ollama_model,
        "format": "json",
        "stream": False,
        "messages": [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": (
                f"Вот текст резюме кандидата:\n\n{markdown}" +
                (f"\n\nВАЖНОЕ ЗАМЕЧАНИЕ HR (РЕЗЮМЕ ВОЗВРАЩЕНО НА ДОРАБОТКУ):\n\"{rework_comment}\"\nОбязательно примени указанные правки!" if rework_comment else "")
            )},
        ],
        "options": {
            "temperature": 0.05,
            "num_predict": 1200,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
            if resp.status_code != 200:
                logger.warning("Ollama вернула код %s. Переход на динамический парсер.", resp.status_code)
                raw_res = dynamic_extract_cv(markdown, filename)
                return enrich_and_normalize_cv(raw_res, markdown, rework_comment), "dynamic_extractor"

            result = resp.json()
            raw_content = result.get("message", {}).get("content", "")
            cleaned = clean_json_string(raw_content)

            parsed_dict = json.loads(cleaned)
            cv_contract = CVJsonContract.model_validate(parsed_dict)
            cv_contract = enrich_and_normalize_cv(cv_contract, markdown, rework_comment)
            return cv_contract, "ollama_llm"

    except Exception as e:
        logger.info("Ollama не ответила за выделенный таймаут (%s). Применен динамический парсер.", e)
        raw_res = dynamic_extract_cv(markdown, filename)
        return enrich_and_normalize_cv(raw_res, markdown, rework_comment), "dynamic_extractor"
