import pytest

from app.crawlers.youtube import YouTubeCrawler


@pytest.mark.asyncio
async def test_youtube_discovery_deduplicates_videos_across_searches(monkeypatch):
    crawler = YouTubeCrawler(search_queries=["Gĩkũyũ stories", "Kikuyu folklore"])

    def fake_search(query: str, limit: int = 25):
        assert limit == 10
        if query == "Gĩkũyũ stories":
            return [
                {"id": "video-1", "title": "Gĩkũyũ oral story", "channel": "Archive Channel", "duration": 120},
                {"id": "video-2", "title": "Proverb collection", "channel": "Speaker", "duration": 60},
            ]
        return [
            {"id": "video-1", "title": "Duplicate title", "channel": "Other channel", "duration": 120},
            {"id": "video-3", "title": "Kikuyu folklore", "uploader": "Elder", "duration": 90},
        ]

    monkeypatch.setattr(crawler, "_search_sync", fake_search)
    results = await crawler.discover(limit_per_query=10)

    assert [item["url"] for item in results] == [
        "https://www.youtube.com/watch?v=video-1",
        "https://www.youtube.com/watch?v=video-2",
        "https://www.youtube.com/watch?v=video-3",
    ]
    assert results[0]["title"] == "Gĩkũyũ oral story"
    assert results[2]["channel"] == "Elder"
    assert results[0]["query"] == "Gĩkũyũ stories"
