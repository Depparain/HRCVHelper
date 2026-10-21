import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    auth_system_url: str = os.getenv("AUTH_SYSTEM_URL", "http://localhost:8001")
    md_convertor_url: str = os.getenv("MD_CONVERTOR_URL", "http://localhost:8002")
    llm_convertor_url: str = os.getenv("LLM_CONVERTOR_URL", "http://localhost:8003")
    json_to_word_url: str = os.getenv("JSON_TO_WORD_URL", "http://localhost:8004")
    db_connector_url: str = os.getenv("DB_CONNECTOR_URL", "http://localhost:8005")

    gateway_host: str = os.getenv("GATEWAY_HOST", "0.0.0.0")
    gateway_port: int = int(os.getenv("GATEWAY_PORT", "8000"))

settings = Settings()
