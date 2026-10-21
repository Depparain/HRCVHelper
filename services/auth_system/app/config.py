import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    db_connector_url: str = os.getenv("DB_CONNECTOR_URL", "http://localhost:8005")
    secret_key: str = os.getenv("SECRET_KEY", "hrcvhelper-super-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    service_host: str = os.getenv("AUTH_SERVICE_HOST", "0.0.0.0")
    service_port: int = int(os.getenv("AUTH_SERVICE_PORT", "8001"))

settings = Settings()
