import hashlib
from typing import BinaryIO
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class StorageService:
    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            use_ssl=settings.S3_USE_SSL,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
        )

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def upload(self, bucket: str, key: str, data: bytes, content_type: str) -> str:
        try:
            self._client.put_object(
                Bucket=bucket, Key=key, Body=data, ContentType=content_type
            )
            logger.info("storage.upload", bucket=bucket, key=key, size=len(data))
            return key
        except ClientError as exc:
            logger.error("storage.upload_failed", bucket=bucket, key=key, error=str(exc))
            raise

    def delete(self, bucket: str, key: str) -> None:
        try:
            self._client.delete_object(Bucket=bucket, Key=key)
            logger.info("storage.delete", bucket=bucket, key=key)
        except ClientError as exc:
            logger.error("storage.delete_failed", bucket=bucket, key=key, error=str(exc))
            raise

    def presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires,
        )


storage_service = StorageService()