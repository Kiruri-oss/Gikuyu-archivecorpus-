import json

import pytest
from sqlalchemy import select

from app.crawlers import scheduler as scheduler_module
from app.crawlers.scheduler import CrawlScheduler
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord


class ExistingSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, traceback):
        return False


@pytest.mark.asyncio
async def test_hunter_persists_source_leads_and_only_ingests_licensed_gikuyu_text(db_session, monkeypatch):
    monkeypatch.setattr(
        scheduler_module,
        "AsyncSessionLocal",
        lambda: ExistingSessionContext(db_session),
    )
    scheduler = CrawlScheduler()
    candidates = [
        {
            "url": "https://catalogue.example/kikuyu",
            "title": "Gĩkũyũ catalogue entry",
            "text": "",
            "language": "unknown",
            "confidence": 0,
            "license": "UNVERIFIED",
            "license_url": None,
            "archive_content": False,
            "permits_research": False,
            "permits_ai_training": False,
            "permits_commercial_use": False,
        },
        {
            "url": "https://open.example/gikuyu-proverb",
            "title": "Gĩkũyũ proverb",
            "text": "Nĩguo mũciĩ wa mũndũ.",
            "language": "ki",
            "confidence": 0.99,
            "license": "CC-BY",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "archive_content": True,
            "permits_research": True,
            "permits_ai_training": True,
            "permits_commercial_use": True,
        },
    ]

    counts = await scheduler._archive_candidates(candidates)

    assert counts["sources_saved"] == 2
    assert counts["texts_saved"] == 1
    sources = (await db_session.execute(select(Source).order_by(Source.url))).scalars().all()
    assert len(sources) == 2
    assert all(source.status == SourceStatus.PENDING for source in sources)
    catalogue_metadata = json.loads(sources[0].raw_metadata)
    assert catalogue_metadata["rights_state"] == "rights_not_detected"
    assert catalogue_metadata["content_archived"] is False

    texts = (await db_session.execute(select(TextRecord))).scalars().all()
    assert len(texts) == 1
    assert texts[0].language_code == "ki"
    assert texts[0].allow_public_display is True
    assert texts[0].allow_ai_training is True
    # Public endpoints must still filter this record because its source is pending.
    assert texts[0].source.status == SourceStatus.PENDING


@pytest.mark.asyncio
async def test_hunter_does_not_reimport_taken_down_source(db_session, monkeypatch):
    monkeypatch.setattr(
        scheduler_module,
        "AsyncSessionLocal",
        lambda: ExistingSessionContext(db_session),
    )
    source = Source(
        url="https://removed.example/gikuyu",
        domain="removed.example",
        source_type=SourceType.WEB,
        status=SourceStatus.TAKEN_DOWN,
        license="CC-BY",
        raw_metadata="{}",
    )
    db_session.add(source)
    await db_session.commit()

    scheduler = CrawlScheduler()
    counts = await scheduler._archive_candidates([{
        "url": source.url,
        "title": "Previously removed",
        "text": "Nĩguo mũciĩ wa mũndũ.",
        "language": "ki",
        "confidence": 0.99,
        "license": "CC-BY",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "archive_content": True,
        "permits_research": True,
        "permits_ai_training": True,
        "permits_commercial_use": True,
    }])

    assert counts["sources_saved"] == 0
    assert counts["texts_saved"] == 0
    texts = (await db_session.execute(select(TextRecord))).scalars().all()
    assert texts == []
