from pathlib import Path
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/hrcvhelper"
    )
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "cv-resumes")
    s3_region_name: str = os.getenv("S3_REGION_NAME", "us-east-1")
    storage_dir: str = os.getenv("STORAGE_DIR", str(Path(__file__).resolve().parent.parent / "storage"))
    
    service_host: str = os.getenv("DB_CONNECTOR_HOST", "0.0.0.0")
    service_port: int = int(os.getenv("DB_CONNECTOR_PORT", "8005"))

settings = Settings()
