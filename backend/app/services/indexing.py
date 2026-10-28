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
        self.base_url = (settings.MEILISEARCH_URL or "").rstrip("/")
        self.enabled = bool(self.base_url and settings.MEILISEARCH_KEY)
        self.headers = {
            "Authorization": f"Bearer {settings.MEILISEARCH_KEY or ''}",
            "Content-Type": "application/json",
        }

    async def ensure_indexes(self) -> None:
        if not self.enabled:
            logger.info("search.postgres_fallback_enabled")
            return
        async with httpx.AsyncClient(timeout=10) as client:
            for index in (self.INDEX_MEDIA, self.INDEX_SEGMENTS, self.INDEX_TEXTS):
                resp = await client.get(
                    f"{self.base_url}/indexes/{index}", headers=self.headers
                )
                if resp.status_code == 404:
                    resp = await client.post(
                        f"{self.base_url}/indexes",
                        headers=self.headers,
                        json={"uid": index, "primaryKey": "id"},
                    )
                resp.raise_for_status()
                logger.info("search.index_ready", index=index)

    async def index_documents(self, index: str, documents: list[dict]) -> None:
        """Index a batch together to avoid one network request per corpus record."""
        if not self.enabled or not documents:
            return
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/indexes/{index}/documents",
                headers=self.headers,
                json=documents,
            )
            resp.raise_for_status()

    async def index_document(self, index: str, document: dict) -> None:
        await self.index_documents(index, [document])

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
