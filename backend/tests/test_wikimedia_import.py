import io
import json
import zipfile

import pytest
from sqlalchemy import select
from app.models.source import Source, SourceStatus
from app.models.text_record import TextRecord
from app.services.wikimedia_import import import_gikuyu_bible, import_random_wikipedia_pages, BIBLICA_SOURCE


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "query": {
                "pages": [
                    {
                        "pageid": 123,
                        "title": "Sample Gĩkũyũ article",
                        "extract": "This is a sufficiently long sample article in Gĩkũyũ. " * 4,
                        "fullurl": "https://ki.wikipedia.org/wiki/Sample",
                        "revisions": [{"revid": 456, "timestamp": "2026-10-25T12:00:00Z"}],
                    }
                ]
            }
        }


class FakeClient:
    async def get(self, url, params, headers):
        assert url == "https://ki.wikipedia.org/w/api.php"
        assert params["generator"] == "random"
        assert headers["User-Agent"].startswith("GikuyuLanguageArchive/")
        return FakeResponse()


@pytest.mark.asyncio
async def test_wikimedia_import_preserves_provenance_and_disables_training_by_default(db_session):
    from unittest.mock import AsyncMock, patch

    with patch("app.services.wikimedia_import.search_index.index_document", new_callable=AsyncMock) as index:
        result = await import_random_wikipedia_pages(db_session, "ki", limit=1, client=FakeClient())
    await db_session.commit()

    assert result.imported == 1
    record = (await db_session.execute(select(TextRecord))).scalar_one()
    source = await db_session.get(Source, record.source_id)
    assert source is not None
    assert source.status == SourceStatus.APPROVED
    assert source.url == "https://ki.wikipedia.org/wiki/Sample"
    assert record.language_code == "ki"
    assert record.allow_public_display is True
    assert record.allow_research_use is True
    assert record.allow_ai_training is False
    assert record.allow_commercial_use is False
    index.assert_awaited_once()


@pytest.mark.asyncio
async def test_wikimedia_import_is_idempotent_for_existing_source(db_session):
    from unittest.mock import AsyncMock, patch

    with patch("app.services.wikimedia_import.search_index.index_document", new_callable=AsyncMock):
        first = await import_random_wikipedia_pages(db_session, "ki", limit=1, client=FakeClient())
        await db_session.commit()
        second = await import_random_wikipedia_pages(db_session, "ki", limit=1, client=FakeClient())
    assert first.imported == 1
    assert second.imported == 0
    assert second.skipped_existing_source == 1


@pytest.mark.asyncio
async def test_wikimedia_import_rejects_unsupported_language(db_session):
    with pytest.raises(ValueError):
        await import_random_wikipedia_pages(db_session, "xx", limit=1, client=FakeClient())


@pytest.mark.asyncio
async def test_wikimedia_import_rejects_other_languages(db_session):
    for code in ("rw", "sw", "ha", "yo", "en"):
        with pytest.raises(ValueError):
            await import_random_wikipedia_pages(db_session, code, limit=1, client=FakeClient())


def make_fake_bible_zip() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "GEN_1.txt",
            "Mũndũ nĩ arĩa mũgambo wa Ngai na andũ a Gĩkũyũ. " * 8,
        )
        archive.writestr(
            "GEN_2.txt",
            "Ũndũ wa gũcooka hamwe, nĩ wĩra wa andũ a Gĩkũyũ na nyũmba ciao. " * 8,
        )
        archive.writestr("README.md", "Publisher notes that must not enter the corpus.")
    return stream.getvalue()


class FakeBibleResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None


class FakeBibleClient:
    def __init__(self, content: bytes):
        self.content = content
        self.calls = 0

    async def get(self, url):
        assert url == "https://ebible.org/Scriptures/kik_readaloud.zip"
        self.calls += 1
        return FakeBibleResponse(self.content)


@pytest.mark.asyncio
async def test_bible_import_batches_content_and_preserves_permissions(db_session):
    from unittest.mock import AsyncMock, patch

    client = FakeBibleClient(make_fake_bible_zip())
    with patch("app.services.wikimedia_import.search_index.index_documents", new_callable=AsyncMock) as index:
        result = await import_gikuyu_bible(db_session, client=client)

    assert result["imported"] == 2
    assert client.calls == 1

    records = (await db_session.execute(select(TextRecord).order_by(TextRecord.title))).scalars().all()
    assert len(records) == 2
    assert all(record.language_code == "ki" for record in records)
    assert all(record.dialect == "Gĩkũyũ" for record in records)
    assert all(record.allow_public_display for record in records)
    assert all(record.allow_research_use for record in records)
    assert all(not record.allow_ai_training for record in records)
    assert all(not record.allow_commercial_use for record in records)
    assert all(record.license == "CC BY-SA 4.0" for record in records)

    sources = (await db_session.execute(select(Source).where(Source.domain == "ebible.org"))).scalars().all()
    assert len(sources) == 2
    assert all(source.status == SourceStatus.APPROVED for source in sources)
    assert all(BIBLICA_SOURCE in source.url for source in sources)
    assert index.await_count == 1
    indexed_batch = index.await_args.args[1]
    assert len(indexed_batch) == 2
    assert all(item["language_code"] == "ki" for item in indexed_batch)
    assert all(item["allow_ai_training"] is False for item in indexed_batch)


@pytest.mark.asyncio
async def test_bible_import_records_completion_and_skips_redownload(db_session):
    client = FakeBibleClient(make_fake_bible_zip())
    first = await import_gikuyu_bible(db_session, client=client)
    assert first["imported"] == 2

    second_client = FakeBibleClient(b"")
    second = await import_gikuyu_bible(db_session, client=second_client)
    assert second == {"imported": 0, "skipped": 1}
    assert second_client.calls == 0

    sources = (await db_session.execute(select(Source).where(Source.domain == "ebible.org"))).scalars().all()
    metadata = [json.loads(source.raw_metadata or "{}") for source in sources]
    assert any(item.get("import_complete") is True for item in metadata)
