import hashlib
import json
from datetime import timedelta
from typing import BinaryIO

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class StorageService:
    """Object storage abstraction: Firebase Cloud Storage or S3-compatible storage.

    Firebase uses one bucket; the existing logical bucket names become object-key
    prefixes so callers and database records do not need a schema migration.
    """

    def __init__(self) -> None:
        self._firebase_bucket = None
        self._client = None

        firebase_configured = bool(
            settings.FIREBASE_STORAGE_BUCKET
            and settings.FIREBASE_SERVICE_ACCOUNT_JSON
        )
        if firebase_configured:
            try:
                import firebase_admin
                from firebase_admin import credentials, storage

                try:
                    app = firebase_admin.get_app("gikuyu-archive")
                except ValueError:
                    service_account = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON or "{}")
                    credential = credentials.Certificate(service_account)
                    app = firebase_admin.initialize_app(
                        credential,
                        {
                            "projectId": settings.FIREBASE_PROJECT_ID or service_account.get("project_id"),
                            "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
                        },
                        name="gikuyu-archive",
                    )
                self._firebase_bucket = storage.bucket(
                    settings.FIREBASE_STORAGE_BUCKET, app=app
                )
                self.provider = "firebase"
            except Exception as exc:
                logger.error("storage.firebase_initialization_failed", error=str(exc))
                raise RuntimeError("Firebase Storage is configured but could not initialise") from exc
        else:
            if not (
                settings.S3_ENDPOINT
                and settings.S3_ACCESS_KEY
                and settings.S3_SECRET_KEY
            ):
                raise RuntimeError(
                    "Configure Firebase Storage credentials or S3_ENDPOINT/S3_ACCESS_KEY/S3_SECRET_KEY"
                )
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
            )
            self.provider = "s3"

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

    @staticmethod
    def _key(bucket: str, key: str) -> str:
        return f"{bucket.strip('/')}/{key.lstrip('/')}"

    def upload_fileobj(self, bucket: str, key: str, fileobj: BinaryIO, content_type: str) -> str:
        """Upload a spooled file without buffering the full recording."""
        fileobj.seek(0)
        try:
            if self._firebase_bucket is not None:
                blob = self._firebase_bucket.blob(self._key(bucket, key))
                blob.upload_from_file(fileobj, content_type=content_type, rewind=True)
            else:
                config = TransferConfig(
                    multipart_threshold=8 * 1024 * 1024,
                    multipart_chunksize=8 * 1024 * 1024,
                    max_concurrency=2,
                    use_threads=True,
                )
                self._client.upload_fileobj(
                    fileobj,
                    bucket,
                    key,
                    ExtraArgs={"ContentType": content_type},
                    Config=config,
                )
            logger.info("storage.upload_fileobj", provider=self.provider, bucket=bucket, key=key)
            return key
        except Exception as exc:
            logger.error("storage.upload_failed", provider=self.provider, bucket=bucket, key=key, error=str(exc))
            raise

    def upload(self, bucket: str, key: str, data: bytes, content_type: str) -> str:
        try:
            if self._firebase_bucket is not None:
                blob = self._firebase_bucket.blob(self._key(bucket, key))
                blob.upload_from_string(data, content_type=content_type)
            else:
                self._client.put_object(
                    Bucket=bucket, Key=key, Body=data, ContentType=content_type
                )
            logger.info("storage.upload", provider=self.provider, bucket=bucket, key=key, size=len(data))
            return key
        except Exception as exc:
            logger.error("storage.upload_failed", provider=self.provider, bucket=bucket, key=key, error=str(exc))
            raise

    def download_fileobj(self, bucket: str, key: str, fileobj: BinaryIO) -> None:
        """Stream an object-store recording into a caller-owned file."""
        try:
            fileobj.seek(0)
            if self._firebase_bucket is not None:
                self._firebase_bucket.blob(self._key(bucket, key)).download_to_file(fileobj)
            else:
                self._client.download_fileobj(bucket, key, fileobj)
            fileobj.seek(0)
        except Exception as exc:
            logger.error("storage.download_failed", provider=self.provider, bucket=bucket, key=key, error=str(exc))
            raise

    def delete(self, bucket: str, key: str) -> None:
        try:
            if self._firebase_bucket is not None:
                self._firebase_bucket.blob(self._key(bucket, key)).delete()
            else:
                self._client.delete_object(Bucket=bucket, Key=key)
            logger.info("storage.delete", provider=self.provider, bucket=bucket, key=key)
        except Exception as exc:
            logger.error("storage.delete_failed", provider=self.provider, bucket=bucket, key=key, error=str(exc))
            raise

    def presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        if self._firebase_bucket is not None:
            blob = self._firebase_bucket.blob(self._key(bucket, key))
            return blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires),
                method="GET",
            )
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires,
        )


storage_service = StorageService()
