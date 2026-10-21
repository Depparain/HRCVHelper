# 📄 Комплект документации и инструкций для реализации проекта HRCVHelper

> **Назначение документа:** Этот файл содержит полную техническую спецификацию системы **HRCVHelper**, готовые проверенные модули генерации `.docx` документов и строгий пошаговый промпт для ИИ-агента по реализации проекта (сначала Backend, затем Frontend).

---

## 📋 Оглавление документации
1. [Введение в проект](#1-введение-в-проект)
2. [Бизнес-процесс и Ролевая модель](#2-бизнес-процесс-и-ролевая-модель)
3. [Функциональные требования](#3-функциональные-требования)
4. [Архитектура системы (C4 Model)](#4-архитектура-системы-c4-model)
5. [Спецификация API и JSON-контракт](#5-спецификация-api-и-json-контракт)
6. [Модель данных (PostgreSQL)](#6-модель-данных-postgresql)
7. [Нефункциональные требования (NFR)](#7-нефункциональные-требования-nfr)
8. [Готовый код для модуля JSONToWord (`json_to_docx.py` & `formatters.py`)](#8-готовый-код-для-модуля-jsontoword)
9. [Промпт-инструкция для ИИ-агента](#9-промпт-инструкция-для-ии-агента)

---

## 1. Введение в проект

### 1.1. Назначение и цели проекта
Целью разработки системы **HRCVHelper** является автоматизация рутинных операций HR-специалиста на этапе переработки, унификации и оформления входящих резюме (CV) кандидатов.

> **Ключевая ценность продукта:** Система берет на себя извлечение неструктурированного текста из исходных файлов резюме, преобразует его в строгую структуру с помощью локальной языковой модели (`Gemma-3`) и после быстрой валидации рекрутером автоматически генерирует корпоративный документ `.docx` с сохранением в объектное хранилище `S3`.

**Основные задачи системы:**
* 🎯 **Снижение затрат человеческого ресурса:** освобождение HR-специалистов от ручного копирования, переписывания и форматирования резюме под единый стандарт.
* ⚖️ **Минимизация человеческого фактора:** исключение случайных опечаток и потери ключевых блоков опыта благодаря строгому JSON-контракту и шаблонизации.
* 🚀 **Сокращение времени отправки готовых резюме (Time-to-Send):** кратное ускорение цикла подготовки профиля кандидата.

### 1.2. Глоссарий
* **HR-специалист (HR):** Внутренний пользователь, загружающий резюме, проверяющий JSON-данные и генерирующий `.docx`.
* **Администратор:** Технический специалист, отслеживающий логи, доступность контейнеров и `health report`.
* **MD (Markdown):** Промежуточный формат текста после конвертации из исходного файла перед подачей в `LLM`.
* **LLM:** Локальная модель (`Gemma-3` через `Ollama`), извлекающая сущности из текста в JSON.
* **S3:** Объектное хранилище для готовых `.docx`-резюме.

---

## 2. Бизнес-процесс и Ролевая модель

### 2.1. Роли пользователей
* **HR-специалист (`HR`):** Авторизуется, загружает файлы CV, проверяет/редактирует извлеченные данные в форме валидации, запускает генерацию `.docx`.
* **Администратор (`Admin`):** Контролирует состояние контейнеров, читает логи и отчеты о работоспособности.

### 2.2. Бизнес-процесс (TO-BE)
1. Авторизация HR в системе через `APIGateway`.
2. Загрузка исходного файла резюме $\rightarrow$ конвертация в Markdown (`MarkItDown`).
3. Передача MD в локальную LLM (`Gemma-3`) $\rightarrow$ получение структурированного JSON (статус `Ожидает проверки HR`).
4. Проверка и валидация данных HR-специалистом в веб-интерфейсе (с возможностью правок).
5. Генерация `.docx` по шаблону (`docxtpl`), сохранение файла в `S3` и выдача готового документа HR.

*Все графические схемы бизнес-процессов, состояний и архитектуры хранятся в папке `docs/images/`.*

### 2.3. Жизненный цикл резюме (State Machine)
* `Загружено` $\rightarrow$ `Конвертация в MD` $\rightarrow$ `Обработка резюме` $\rightarrow$ `Ожидает проверки HR` $\rightarrow$ `Формирование docx` $\rightarrow$ `Готово` (файл в S3).

---

## 3. Функциональные требования

* **ФТ-HR.1. Авторизация:** Вход по логину и хэшу пароля.
* **ФТ-HR.2. Парсинг CV:** Загрузка файла, конвертация в MD и структурирование через `Gemma-3`.
* **ФТ-HR.3. Валидация JSON:** Веб-интерфейс для просмотра и ручной корректировки извлеченных полей.
* **ФТ-HR.4. Генерация `.docx`:** Автоматическая сборка документа по шаблону, сохранение в S3 и скачивание.
* **ФТ-АДМ.1-2.** Просмотр логов и мониторинг состояния системы (`health report`).

---

## 4. Архитектура системы (C4 Model)

Система построена по модульной микросервисной архитектуре с единой точкой входа (`APIGateway`). Фронтенд взаимодействует исключительно с API.

### Перечень контейнеров и стек:
* **Frontend (`FE`)**: Dart, Flutter (Web) — порт `8501`
* **APIGateway (`Gate`)**: Python, FastAPI — порт `8000`
* **AuthSystem (`Auth`)**: Python (авторизация)
* **MDConvertor (`MDCo`)**: Python, `MarkItDown` (конвертация в MD)
* **LLMConvertor (`LLM`)**: Python, Ollama, `Gemma-3` (парсинг в JSON)
* **JSONToWord (`JTW`)**: Python, `docxtpl` (генерация `.docx`)
* **DBConnector**: Python, SQLAlchemy (работа с БД и S3)
* **DB**: PostgreSQL (хранение пользователей, статусов и JSONB)
* **S3**: Объектное хранилище файлов

---

## 5. Спецификация API и JSON-контракт

### 5.1. Основные эндпоинты APIGateway
* `POST /api/v1/auth/login` — Авторизация HR.
* `POST /api/v1/cv/upload` — Загрузка файла CV, парсинг в JSON и возврат черновика.
* `PUT /api/v1/cv/{cv_id}/validate` — Сохр. проверенного JSON, генерация `.docx`, отправка в S3.
* `GET /api/v1/cv/{cv_id}` — Получение данных резюме и статуса.
* `GET /api/v1/admin/logs` — Просмотр системных логов.
* `GET /api/v1/admin/health` — Отчет о состоянии системы (`health report`).

### 5.2. Формат JSON-контракта резюме
```json
{
  "fio": "ФИО",
  "vacancy": "Вакансия",
  "total_year_work": "Общее время работы по этой профессии X ЛЕТ Y МЕСЯЦЕВ",
  "project_backround": "Краткое описание отраслей работы",
  "pitch": "рассказ о себе от первого лица, без 'Я' кратко 3 - 5 предложений",
  "skills_and_tools": [],
  "education": [
    {
      "type": "Высшее:",
      "institution": "Название института",
      "speciality": "Специальность",
      "year": "Год поступления - год выпуска"
    }
  ],
  "advanced_training": [
    {
      "name": "Название курса",
      "year": "Год прохождения"
    }
  ],
  "languages": "Английский на уровне A2",
  "citizenship_location": "Страна проживания, город",
  "employment": "Полная занятость, удаленная работа",
  "status": "Готов к переезду",
  "projects": [
    {
      "place_time_raw": "Название компании",
      "period": "XXXX год YY месяц - ZZZZ год VV месяц",
      "role_in_project": "Роль",
      "task_on_project": ["Задача 1", "Задача 2"],
      "achievements_in_project": ["Достижение 1"],
      "skills_tools_in_project": "Использованные инструменты"
    }
  ]
}
```

---

## 6. Модель данных (PostgreSQL)

* **Таблица `HR`**: `HR_ID` (PK), `Full_Name`, `Login`, `Hash_Pass`.
* **Таблица `CV`**: `CV_ID` (PK), `HR_ID` (FK), `JSONB` (данные резюме), `Status`, `Docx` (путь/ключ в S3).

---

## 7. Нефункциональные требования (NFR)

* **152-ФЗ:** Локальная обработка ПДн через `Gemma-3` без передачи данных во внешние облачные API.
* **API-First:** Клиент общается только через `APIGateway`.
* **Human-in-the-Loop:** Генерация `.docx` блокируется до подтверждения JSON рекрутером.

---

---

## 8. Готовый код для модуля JSONToWord

Ниже представлены два проверенных файла, которые можно внедрить в сервис `json_to_word`:

### Файл 1: `services/json_to_word/json_to_docx.py`

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from docxtpl import DocxTemplate

from .tools import formatters as fmt


def _load_data(json_path: Path) -> Dict[str, Any]:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_projects(projects: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not isinstance(projects, list):
        return items

    for project in projects:
        if not isinstance(project, dict):
            continue

        raw_place = project.get("place_time_raw") or project.get("name") or ""
        raw_period = project.get("period") or ""

        items.append(
            {
                "project_place_and_work_time": fmt.format_project_name(raw_place, raw_period),
                "role_in_project": fmt.format_role_in_project(project.get("role_in_project")),
                "task_on_project": fmt.format_list_for_word(project.get("task_on_project")),
                "achievements_in_project": fmt.format_list_for_word(project.get("achievements_in_project")),
                "skills_tools_in_project": fmt.format_skills_tools_in_project(project.get("skills_tools_in_project")),
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
        "fio": fmt.format_fio(data.get("fio")),
        "vacancy": fmt.format_vacancy(data.get("vacancy")),
        "total_year_work": fmt.format_total_year_work(data.get("total_year_work")),
        "project_backround": fmt.format_project_backround(data.get("project_backround")),
        "pitch": fmt.format_pitch(data.get("pitch")),
        "skills_tools": fmt.format_skills_tools(data.get("skills_and_tools")),
        "education": fmt.format_education(data.get("education")),
        "courses": fmt.format_courses_list(data.get("advanced_training")),
        "languages": fmt.format_language(data.get("languages")),
        "citizenship_location": fmt.format_simple_field(data.get("citizenship_location"), bold=False),
        "employment": fmt.format_employment(data.get("employment")),
        "status": fmt.format_status(data.get("status")),
        "projects": _build_projects(data.get("projects")),
    }

    doc.render(context)
    doc.save(str(output_file))
    return output_file


__all__ = ["generate_cv"]
```

### Файл 2: `services/json_to_word/tools/formatters.py`

```python
from pathlib import Path
from .new_tools.new_formatters import DocxRichTextBuilder, load_style_from_json

_STYLE_PATH = Path(__file__).resolve().parent.parent / "template" / "style.json"
_builder = DocxRichTextBuilder(load_style_from_json(str(_STYLE_PATH)))

def clean_upper(raw_str):
    return _builder.clean_text(raw_str, uppercase=True)

def add_segment(rt, text, *, bold=False):
    if text:
        _builder.add_segment(rt, str(text), bold=bold)

def build_rt(*segments):
    return _builder.build_rt(*segments)

def format_simple_field(raw_value, uppercase=False, bold=True):
    return _builder.format_simple_field(raw_value, uppercase=uppercase, bold=bold)

def format_fio(val): return _builder.format_fio(val)
def format_vacancy(val): return _builder.format_vacancy(val)
def format_total_year_work(val): return _builder.format_total_year_work(val)
def format_project_backround(val): return _builder.format_project_background(val)
def format_pitch(val): return _builder.format_pitch(val)
def format_language(val): return _builder.format_language(val)
def format_employment(val): return _builder.format_employment(val)
def format_status(val): return _builder.format_status(val)
def format_role_in_project(val): return _builder.format_role_in_project(val)
def format_skills_tools_in_project(val): return _builder.format_skills_tools_in_project(val)
def format_project_name(raw_name, raw_period): return _builder.format_project_name(raw_name, raw_period)
def format_skills_tools(raw_data): return _builder.format_skills_tools(raw_data)
def format_education(education_data): return _builder.format_education(education_data)
def format_courses_list(raw_courses): return _builder.format_courses_list(raw_courses)
def format_list_for_word(raw_text): return _builder.format_list_for_word(raw_text)
```

---

---

## 9. Промпт-инструкция для ИИ-агента

*Скопируйте этот блок и передайте его ИИ-агенту (в Cursor, Claude Engineer, Aider и др.), чтобы запустить разработку:*

```markdown
Ты — ведущий Backend и Frontend разработчик. Твоя задача — реализовать с нуля программный комплекс **HRCVHelper** строго по технической документации, приведенной выше в этом файле.

### 📜 Строгие правила и ограничения (Guardrails):
1. **Строго по документации:** Архитектура, структура таблиц БД, JSON-контракты и эндпоинты API должны на 100% соответствовать разделам 4, 5 и 6 этого документа. Никакой самодеятельности.
2. **Используй готовый код генерации `.docx`:** В разделе 8 этого документа даны готовые рабочие файлы `json_to_docx.py` и `formatters.py`. Ты обязан внедрить их в модуль `json_to_word` без изменений рендеринга `docxtpl`.
3. **Изоляция:** Система собирается через единый `docker-compose.yml`.
4. **152-ФЗ:** Локальная обработка через Ollama / Gemma-3.

---

### 🚀 Порядок выполнения задач (Phases):

#### ЭТАП 1: Разработка Backend-контура (Строго сначала!)
1. **База данных и модели (`db_connector`):** Разверни PostgreSQL, настрой модели SQLAlchemy для таблиц `HR` и `CV` (с типом `JSONB` и статусами по State Machine), подключи S3.
2. **Система авторизации (`auth_system`):** Реализуй хэширование паролей и проверку учетных данных HR.
3. **Модули парсинга (`md_convertor`, `llm_convertor`):** Интегрируй `MarkItDown` и локальную Ollama (`Gemma-3`) для парсинга MD в JSON строго по контракту из пункта 5.2.
4. **Генератор документов (`json_to_word`):** Размести предоставленные в разделе 8 файлы `json_to_docx.py` и `formatters.py`, подключив шаблон `style.json` и корпоративный шаблон `.docx`.
5. **Оркестратор (`api_gateway`):** Собери FastAPI-приложение и реализуй REST API эндпоинты из пункта 5.1.

*После полного тестирования бэкенда переходи к Этапу 2.*

---

#### ЭТАП 2: Разработка Frontend-контура
1. **Веб-интерфейс на Flutter (`frontend`):**
   - Экран авторизации HR.
   - Загрузка файлов CV с индикацией прогресса.
   - Форма интерактивной валидации и редактирования полей JSON.
   - Скачивание готового `.docx`-файла.
   - Админ-панель для просмотра логов и `health report`.

---

### 🛠️ Инструкция по старту:
1. Изучи требования в этом файле.
2. Напиши план реализации **Этапа 1 (Backend)** с учетом готового кода генератора `.docx` и приступай к работе пошагово.
```
