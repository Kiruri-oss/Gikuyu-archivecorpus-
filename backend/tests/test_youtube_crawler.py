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


@pytest.mark.asyncio
async def test_discovered_video_sources_are_persisted_as_reviewable_archive_records(monkeypatch):
    import json

    from app.crawlers.scheduler import CrawlScheduler
    from app.models.source import SourceStatus, SourceType

    class FakeResult:
        def scalar_one_or_none(self):
            return None

    class FakeSession:
        def __init__(self):
            self.added = []
            self.committed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, _statement):
            return FakeResult()

        def add(self, record):
            self.added.append(record)

        async def commit(self):
            self.committed = True

    session = FakeSession()
    monkeypatch.setattr("app.crawlers.scheduler.AsyncSessionLocal", lambda: session)
    scheduler = CrawlScheduler()
    candidates = [
        {
            "url": "https://www.youtube.com/watch?v=video-1",
            "title": "Gĩkũyũ oral story",
            "channel": "Archive Channel",
            "duration": 120,
            "query": "Gĩkũyũ stories",
        },
        {
            "url": "https://www.youtube.com/watch?v=video-1",
            "title": "Duplicate result",
            "channel": "Other channel",
            "duration": 120,
            "query": "Kikuyu folklore",
        },
    ]

    saved = await scheduler._archive_youtube_candidates(candidates)

    assert saved == 1
    assert session.committed is True
    assert len(session.added) == 1
    source = session.added[0]
    assert source.source_type == SourceType.YOUTUBE
    assert source.status == SourceStatus.PENDING
    metadata = json.loads(source.raw_metadata)
    assert metadata["language"] == "ki"
    assert metadata["content_state"] == "metadata_only"
    assert metadata["title"] == "Gĩkũyũ oral story"
