from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Union
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError
from .config import settings

logger = logging.getLogger(__name__)


class S3StorageService:
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.endpoint_url = settings.s3_endpoint_url
        self.storage_dir = Path(settings.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._s3_client = None
        self._is_s3_available: Optional[bool] = None

    def _get_client(self):
        if self._is_s3_available is False:
            return None
        if self._s3_client is not None:
            return self._s3_client

        try:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region_name,
                config=Config(
                    signature_version="s3v4",
                    connect_timeout=1,
                    read_timeout=1,
                    retries={"max_attempts": 1},
                ),
            )
            self._s3_client.head_bucket(Bucket=self.bucket_name)
            self._is_s3_available = True
            logger.info("S3/MinIO клиент успешно инициализирован, бакет: %s", self.bucket_name)
            return self._s3_client
        except Exception as e:
            logger.info("S3 (%s) не доступен: %s. Используется локальное хранилище: %s", self.endpoint_url, e, self.storage_dir)
            self._is_s3_available = False
            return None

    def is_healthy(self) -> bool:
        client = self._get_client()
        if client is None:
            return self.storage_dir.exists()
        try:
            client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document") -> str:
        client = self._get_client()
        if client:
            try:
                client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=data,
                    ContentType=content_type,
                )
                return f"s3://{self.bucket_name}/{object_name}"
            except Exception as e:
                logger.warning("Ошибка S3 при upload: %s. Сохраняем локально.", e)

        # Локальное сохранение
        local_path = self.storage_dir / object_name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
        return f"file://{local_path.resolve()}"

    def upload_file(self, file_path: Union[str, Path], object_name: Optional[str] = None) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        if object_name is None:
            object_name = path.name
        return self.upload_bytes(path.read_bytes(), object_name)

    def download_bytes(self, object_or_key: str) -> bytes:
        client = self._get_client()
        # Если ссылка s3://
        if object_or_key.startswith("s3://"):
            parts = object_or_key[5:].split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            if client:
                resp = client.get_object(Bucket=bucket, Key=key)
                return resp["Body"].read()
            local_path = self.storage_dir / key
            if local_path.exists():
                return local_path.read_bytes()

        # Если ссылка file://
        if object_or_key.startswith("file://"):
            local_path = Path(object_or_key[7:])
            if local_path.exists():
                return local_path.read_bytes()

        # Обычный ключ
        if client:
            try:
                resp = client.get_object(Bucket=self.bucket_name, Key=object_or_key)
                return resp["Body"].read()
            except Exception as e:
                logger.warning("Не удалось скачать из S3: %s", e)

        local_path = self.storage_dir / object_or_key
        if local_path.exists():
            return local_path.read_bytes()

        raise FileNotFoundError(f"Файл '{object_or_key}' не найден ни в S3, ни локально")


s3_storage = S3StorageService()
