import asyncio
from app.core.logging import get_logger

logger = get_logger(__name__)


class YouTubeCrawler:
    """
    Uses yt-dlp to pull metadata + auto-captions for candidate Kikuyu videos.
    Downloads are handled by Celery workers, not in the request path.
    """

    def __init__(self, search_queries: list[str] | None = None) -> None:
        self.search_queries = search_queries or [
            "Kikuyu sermon",
            "Kikuyu news",
            "Kikuyu music",
            "Kikuyu lessons",
            "Kikuyu documentary",
        ]

    def _search_sync(self, query: str, limit: int = 20) -> list[dict]:
        try:
            import yt_dlp  # type: ignore
            ydl_opts = {
                "quiet": True,
                "skip_download": True,
                "extract_flat": True,
                "default_search": "ytsearch",
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                return info.get("entries", []) or []
        except Exception as exc:
            logger.error("youtube.search_failed", query=query, error=str(exc))
            return []

    async def discover(self, limit_per_query: int = 20) -> list[dict]:
        all_results: list[dict] = []
        for query in self.search_queries:
            results = await asyncio.to_thread(self._search_sync, query, limit_per_query)
            for item in results:
                if not item or not item.get("id"):
                    continue
                all_results.append({
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "title": item.get("title", ""),
                    "channel": item.get("channel") or item.get("uploader", ""),
                    "duration": item.get("duration"),
                    "query": query,
                })
        logger.info("youtube.discovered", total=len(all_results))
        return all_results