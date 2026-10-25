import hashlib
from typing import BinaryIO
from boto3.s3.transfer import TransferConfig
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

    def compute_sha256_file(self, fileobj: BinaryIO, max_bytes: int) -> tuple[str, int]:
        """Hash an uploaded file in bounded chunks without loading it into RAM."""
        digest = hashlib.sha256()
        size = 0
        fileobj.seek(0)
        while True:
            chunk = fileobj.read(8 * 1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                fileobj.seek(0)
                raise ValueError("File exceeds maximum upload size")
            digest.update(chunk)
        fileobj.seek(0)
        return digest.hexdigest(), size

    def upload_fileobj(self, bucket: str, key: str, fileobj: BinaryIO, content_type: str) -> str:
        """Multipart-upload a spooled file without buffering the full recording."""
        fileobj.seek(0)
        config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
            max_concurrency=2,
            use_threads=True,
        )
        try:
            self._client.upload_fileobj(
                fileobj,
                bucket,
                key,
                ExtraArgs={"ContentType": content_type},
                Config=config,
            )
            logger.info("storage.upload_fileobj", bucket=bucket, key=key)
            return key
        except ClientError as exc:
            logger.error("storage.upload_failed", bucket=bucket, key=key, error=str(exc))
            raise

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

    def download_fileobj(self, bucket: str, key: str, fileobj: BinaryIO) -> None:
        """Stream an object-store recording into a caller-owned file."""
        try:
            fileobj.seek(0)
            self._client.download_fileobj(bucket, key, fileobj)
            fileobj.seek(0)
        except ClientError as exc:
            logger.error("storage.download_failed", bucket=bucket, key=key, error=str(exc))
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