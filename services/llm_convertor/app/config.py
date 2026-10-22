from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    service_host: str = os.getenv("LLM_SERVICE_HOST", "0.0.0.0")
    service_port: int = int(os.getenv("LLM_SERVICE_PORT", "8003"))

    prompt_path: Path = Path(__file__).resolve().parent.parent / "prompts" / "prompt.md"
    schema_path: Path = Path(__file__).resolve().parent.parent / "prompts" / "example.json"
    tech_dictionary_path: Path = Path(__file__).resolve().parent.parent / "config" / "tech_dictionary.json"


settings = Settings()

# Кеш в оперативной памяти для промптов и конфигурационных словарей
_cached_prompts: Tuple[str, str] | None = None
_cached_tech_dict: List[str] | None = None


def get_cached_prompt_files() -> Tuple[str, str]:
    """Возвращает предзагруженный кортеж (prompt_text, example_schema)."""
    global _cached_prompts
    if _cached_prompts is None:
        prompt_text = ""
        example_text = ""
        if settings.prompt_path.exists():
            prompt_text = settings.prompt_path.read_text(encoding="utf-8")
        if settings.schema_path.exists():
            example_text = settings.schema_path.read_text(encoding="utf-8")
        _cached_prompts = (prompt_text, example_text)
    return _cached_prompts


def get_tech_dictionary() -> List[str]:
    """Возвращает предзагруженный список ключевых технологий из конфигурации."""
    global _cached_tech_dict
    if _cached_tech_dict is None:
        if settings.tech_dictionary_path.exists():
            try:
                _cached_tech_dict = json.loads(settings.tech_dictionary_path.read_text(encoding="utf-8"))
            except Exception:
                _cached_tech_dict = []
        else:
            _cached_tech_dict = []
    return _cached_tech_dict
