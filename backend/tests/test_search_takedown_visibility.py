import pytest

from app.models.media import Media, MediaKind
from app.models.segment import Segment
from app.models.source import Source, SourceStatus, SourceType
from app.models.text_record import TextRecord
from app.services import indexing


@pytest.mark.asyncio
async def test_search_filters_stale_hits_for_pending_sources(client, db_session, monkeypatch):
    public_source = Source(
        url="https://open.example/gikuyu",
        domain="open.example",
        source_type=SourceType.WEB,
        status=SourceStatus.APPROVED,
        license="CC-BY",
        raw_metadata="{}",
    )
    pending_source = Source(
        url="https://pending.example/gikuyu",
        domain="pending.example",
        source_type=SourceType.WEB,
        status=SourceStatus.PENDING,
        license="CC-BY",
        raw_metadata="{}",
    )
    db_session.add_all([public_source, pending_source])
    await db_session.flush()

    public_media = Media(
        source_id=public_source.id,
        kind=MediaKind.AUDIO,
        title="Public Gĩkũyũ recording",
        file_key="test/public.wav",
        sha256="a" * 64,
        license="CC-BY",
        allow_public_display=True,
    )
    pending_media = Media(
        source_id=pending_source.id,
        kind=MediaKind.AUDIO,
        title="Pending Gĩkũyũ recording",
        file_key="test/pending.wav",
        sha256="b" * 64,
        license="CC-BY",
        allow_public_display=True,
    )
    db_session.add_all([public_media, pending_media])
    await db_session.flush()

    public_segment = Segment(
        media_id=public_media.id,
        start_seconds=0,
        end_seconds=1,
        transcript="Nĩguo mũciĩ.",
    )
    pending_segment = Segment(
        media_id=pending_media.id,
        start_seconds=0,
        end_seconds=1,
        transcript="Pending transcript.",
    )
    public_text = TextRecord(
        source_id=public_source.id,
        title="Public proverb",
        body="Nĩguo mũciĩ.",
        language_code="ki",
        sha256="c" * 64,
        license="CC-BY",
        allow_public_display=True,
    )
    pending_text = TextRecord(
        source_id=pending_source.id,
        title="Pending proverb",
        body="Pending Gĩkũyũ text.",
        language_code="ki",
        sha256="d" * 64,
        license="CC-BY",
        allow_public_display=True,
    )
    db_session.add_all([public_segment, pending_segment, public_text, pending_text])
    await db_session.commit()

    hits = {
        "media": [{"id": str(public_media.id)}, {"id": str(pending_media.id)}],
        "segments": [{"id": str(public_segment.id)}, {"id": str(pending_segment.id)}],
        "texts": [{"id": str(public_text.id)}, {"id": str(pending_text.id)}],
    }

    async def fake_search(index_name, query, limit):
        return {"hits": hits[index_name]}

    monkeypatch.setattr(indexing.search_index, "enabled", True)
    monkeypatch.setattr(indexing.search_index, "search", fake_search)

    response = await client.get("/api/v1/search?q=gikuyu")
    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["media"]] == [str(public_media.id)]
    assert [item["id"] for item in payload["segments"]] == [str(public_segment.id)]
    assert [item["id"] for item in payload["texts"]] == [str(public_text.id)]
