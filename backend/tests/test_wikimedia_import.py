import pytest
from sqlalchemy import select
from app.models.source import Source, SourceStatus
from app.models.text_record import TextRecord
from app.services.wikimedia_import import import_random_wikipedia_pages


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
