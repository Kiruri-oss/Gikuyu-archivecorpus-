import asyncio
import re
from app.core.logging import get_logger

logger = get_logger(__name__)


class YouTubeCrawler:
    """Discover public Gĩkũyũ video-source metadata for the archive review queue."""

    def __init__(self, search_queries: list[str] | None = None) -> None:
        self.search_queries = search_queries or [
            "Gĩkũyũ proverbs",
            "Gikuyu proverbs",
            "Gikuyu folktales",
            "Gikuyu stories",
            "Gikuyu oral history",
            "Kikuyu traditional songs",
            "Kikuyu language lesson",
            "Gikuyu conversation",
            "Gikuyu elders stories",
            "Gikuyu poetry",
            "Kikuyu folklore",
            "Kikuyu speech",
        ]

    def _search_sync(self, query: str, limit: int = 25) -> list[dict]:
        try:
            import yt_dlp  # type: ignore

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extract_flat": True,
                "default_search": "ytsearch",
                "noplaylist": True,
                "socket_timeout": 15,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                return info.get("entries", []) or []
        except Exception as exc:
            logger.warning("youtube.search_failed", query=query, error=str(exc))
            return []

    async def discover(self, limit_per_query: int = 25) -> list[dict]:
        """Find source records only; never claim a video or transcript was archived."""
        bounded_limit = max(1, min(limit_per_query, 50))
        unique: dict[str, dict] = {}
        for query in self.search_queries:
            results = await asyncio.to_thread(self._search_sync, query, bounded_limit)
            for item in results:
                if not item or not item.get("id"):
                    continue
                video_id = str(item["id"]).strip()
                if not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id):
                    continue
                if video_id in unique:
                    continue
                unique[video_id] = {
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": str(item.get("title") or "Untitled Gĩkũyũ video")[:500],
                    "channel": str(item.get("channel") or item.get("uploader") or "")[:250],
                    "duration": item.get("duration"),
                    "query": query,
                }
        logger.info("youtube.discovered", total=len(unique), queries=len(self.search_queries))
        return list(unique.values())
