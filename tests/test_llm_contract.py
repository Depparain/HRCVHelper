from __future__ import annotations

import json
from pathlib import Path
from services.llm_convertor.app.schemas import CVJsonContract
from services.llm_convertor.app.parser import clean_json_string, heuristic_extract_cv

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLE_JSON_PATH = BASE_DIR / "services" / "json_to_word" / "template" / "example.json"


def test_clean_json_string():
    raw_markdown = """```json
    {
        "fio": "Иван Иванов",
        "vacancy": "Python Developer"
    }
    ```"""
    cleaned = clean_json_string(raw_markdown)
    data = json.loads(cleaned)
    assert data["fio"] == "Иван Иванов"


def test_example_json_matches_contract():
    raw_text = EXAMPLE_JSON_PATH.read_text(encoding="utf-8")
    data = json.loads(raw_text)

    contract = CVJsonContract.model_validate(data)
    assert contract.fio != ""
    assert contract.vacancy != ""
    assert isinstance(contract.skills_and_tools, list)
    assert isinstance(contract.projects, list)
    assert len(contract.projects) > 0


def test_heuristic_fallback():
    sample_md = """# Алексей Смирнов
    Ведущий Python Разработчик
    
    ## Навыки
    * Python, FastAPI, Docker, PostgreSQL
    
    ## Опыт работы
    Яндекс, 2021-2024
    """
    cv = heuristic_extract_cv(sample_md, "alexey.pdf")
    assert cv.fio == "Алексей Смирнов"
    assert "Python" in cv.vacancy or "Разработчик" in cv.vacancy
    assert len(cv.projects) > 0
