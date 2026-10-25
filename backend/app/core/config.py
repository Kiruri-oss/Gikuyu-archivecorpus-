from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, AnyHttpUrl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Gikuyu Archive Corpus"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn

    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_AUDIO: str = "gikuyu-audio"
    S3_BUCKET_TEXT: str = "gikuyu-text"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = True

    MEILISEARCH_URL: str = "http://localhost:7700"
    MEILISEARCH_KEY: str

    FRONTEND_URL: AnyHttpUrl = "http://localhost:3000"
    BACKEND_URL: AnyHttpUrl = "http://localhost:8000"

    CRAWLER_USER_AGENT: str = "GikuyuArchiveBot/1.0 (+https://gikuyu-archivecorpus.vercel.app/about)"
    # Start from Gĩkũyũ references and major public catalogue/search surfaces.
    # The hunter follows outbound references with a bounded domain/page budget.
    CRAWLER_SEED_URLS: str = (
        "https://ki.wikipedia.org/wiki/Main_Page,"
        "https://ki.wiktionary.org/wiki/Main_Page,"
        "https://commons.wikimedia.org/wiki/Category:Kikuyu_language,"
        "https://wikisource.org/wiki/Special:Search?search=Kikuyu,"
        "https://archive.org/search?query=%28title%3Akikuyu+OR+subject%3Akikuyu+OR+description%3Agikuyu%29,"
        "https://openlibrary.org/search?q=kikuyu,"
        "https://www.gutenberg.org/ebooks/search/?query=kikuyu,"
        "https://www.europeana.eu/en/search?query=kikuyu,"
        "https://openverse.org/search/?q=kikuyu,"
        "https://www.loc.gov/search/?q=kikuyu,"
        "https://www.wikidata.org/w/index.php?search=Kikuyu,"
        "https://opendata.go.ke/"
    )
    CRAWLER_RESPECT_ROBOTS: bool = True
    CRAWLER_MAX_CONCURRENCY: int = 5
    CRAWLER_MAX_PAGES: int = 250
    CRAWLER_MAX_DOMAINS: int = 75
    CRAWLER_MAX_PAGES_PER_DOMAIN: int = 12

    LANGUAGE_DETECTION_THRESHOLD: float = 0.55
    MAX_UPLOAD_SIZE_MB: int = 500


@lru_cache
def get_settings() -> Settings:
    return Settings()
