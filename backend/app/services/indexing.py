import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SearchIndexService:
    INDEX_MEDIA = "media"
    INDEX_SEGMENTS = "segments"
    INDEX_TEXTS = "texts"

    def __init__(self) -> None:
        self.enabled = bool(settings.MEILISEARCH_URL and settings.MEILISEARCH_KEY)
        self.base_url = str(settings.MEILISEARCH_URL).rstrip("/") if settings.MEILISEARCH_URL else ""
        self.headers = {
            "Authorization": f"Bearer {settings.MEILISEARCH_KEY or ''}",
            "Content-Type": "application/json",
        }

    async def ensure_indexes(self) -> None:
        if not self.enabled:
            logger.info("search.index_disabled", mode="postgres_fallback")
            return
        async with httpx.AsyncClient(timeout=10) as client:
            for index in (self.INDEX_MEDIA, self.INDEX_SEGMENTS, self.INDEX_TEXTS):
                resp = await client.get(f"{self.base_url}/indexes/{index}", headers=self.headers)
                if resp.status_code == 404:
                    created = await client.post(
                        f"{self.base_url}/indexes",
                        headers=self.headers,
                        json={"uid": index, "primaryKey": "id"},
                    )
                    created.raise_for_status()
                    logger.info("search.index_created", index=index)
                else:
                    resp.raise_for_status()

    async def index_document(self, index: str, document: dict) -> None:
        if not self.enabled:
            return
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/indexes/{index}/documents",
                headers=self.headers,
                json=[document],
            )
            resp.raise_for_status()

    async def delete_document(self, index: str, doc_id: str) -> None:
        if not self.enabled:
            return
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(
                f"{self.base_url}/indexes/{index}/documents/{doc_id}",
                headers=self.headers,
            )
            resp.raise_for_status()

    async def search(self, index: str, query: str, limit: int = 20) -> dict:
        if not self.enabled:
            return {"hits": []}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/indexes/{index}/search",
                headers=self.headers,
                json={"q": query, "limit": limit},
            )
            resp.raise_for_status()
            return resp.json()


search_index = SearchIndexService()
