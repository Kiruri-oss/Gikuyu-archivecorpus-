from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, AnyHttpUrl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Gikuyu Language Archive"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn | None = None

    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_AUDIO: str = "gikuyu-audio"
    S3_BUCKET_TEXT: str = "gikuyu-text"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = True

    MEILISEARCH_URL: AnyHttpUrl | None = None
    MEILISEARCH_KEY: str | None = None

    FRONTEND_URL: AnyHttpUrl = "http://localhost:3000"
    BACKEND_URL: AnyHttpUrl = "http://localhost:8000"

    CRAWLER_USER_AGENT: str = "GikuyuArchiveBot/1.0 (+https://gikuyu-archivecorpus.vercel.app/about)"
    CRAWLER_SEED_URLS: str = "https://ki.wikipedia.org/wiki/Main_Page,https://ki.wiktionary.org/wiki/Main_Page,https://www.wikidata.org/wiki/Wikidata:Main_Page,https://opendata.go.ke/,https://archive.org/"
    CRAWLER_RESPECT_ROBOTS: bool = True
    CRAWLER_MAX_CONCURRENCY: int = 5

    LANGUAGE_DETECTION_THRESHOLD: float = 0.55
    MAX_UPLOAD_SIZE_MB: int = 500


@lru_cache
def get_settings() -> Settings:
    return Settings()