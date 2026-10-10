import httpx
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SearchIndexService:
    INDEX_MEDIA = "media"
    INDEX_SEGMENTS = "segments"

    def __init__(self) -> None:
        self.base_url = settings.MEILISEARCH_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.MEILISEARCH_KEY}",
            "Content-Type": "application/json",
        }

    async def ensure_indexes(self) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            for index in (self.INDEX_MEDIA, self.INDEX_SEGMENTS):
                resp = await client.get(
                    f"{self.base_url}/indexes/{index}", headers=self.headers
                )
                if resp.status_code == 404:
                    await client.post(
                        f"{self.base_url}/indexes",
                        headers=self.headers,
                        json={"uid": index, "primaryKey": "id"},
                    )
                    logger.info("search.index_created", index=index)

    async def index_document(self, index: str, document: dict) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/indexes/{index}/documents",
                headers=self.headers,
                json=[document],
            )
            resp.raise_for_status()

    async def delete_document(self, index: str, doc_id: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(
                f"{self.base_url}/indexes/{index}/documents/{doc_id}",
                headers=self.headers,
            )
            resp.raise_for_status()

    async def search(self, index: str, query: str, limit: int = 20) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/indexes/{index}/search",
                headers=self.headers,
                json={"q": query, "limit": limit},
            )
            resp.raise_for_status()
            return resp.json()


search_index = SearchIndexService()