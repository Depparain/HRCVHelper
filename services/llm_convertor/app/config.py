from pathlib import Path
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    service_host: str = os.getenv("LLM_SERVICE_HOST", "0.0.0.0")
    service_port: int = int(os.getenv("LLM_SERVICE_PORT", "8003"))
    
    prompt_path: Path = Path(__file__).resolve().parent.parent / "prompts" / "prompt.md"
    schema_path: Path = Path(__file__).resolve().parent.parent / "prompts" / "example.json"

settings = Settings()
