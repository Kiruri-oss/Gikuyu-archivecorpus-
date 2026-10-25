import csv
import json
import uuid
import pytest


@pytest.mark.asyncio
async def test_exports_require_role_and_only_include_explicitly_permitted_records(client, db_session, auth_headers):
    from app.models.media import Media, MediaKind
    from app.models.segment import Segment
    from app.models.source import Source, SourceStatus, SourceType
    from app.models.text_record import TextRecord
    from app.services.export import export_service

    source = Source(
        url="test://export-source",
        domain="test",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.APPROVED,
    )
    db_session.add(source)
    await db_session.flush()

    media = Media(
        source_id=source.id,
        kind=MediaKind.AUDIO,
        title="Approved oral history",
        file_key="private/object-key",
        sha256=uuid.uuid4().hex,
        dialect="Ki-Murang'a",
        license="CC BY 4.0",
        allow_public_display=True,
        allow_research_use=True,
        allow_ai_training=False,
        allow_commercial_use=False,
    )
    db_session.add(media)
    await db_session.flush()
    db_session.add(Segment(
        media_id=media.id,
        start_seconds=0,
        end_seconds=2,
        transcript="Nĩ wega.",
        translation="It is good.",
    ))

    text = TextRecord(
        source_id=source.id,
        title="Permitted story",
        body="Ũhoro wa tene.",
        language_code="ki",
        sha256=uuid.uuid4().hex,
        license="CC BY 4.0",
        allow_public_display=True,
        allow_research_use=True,
        allow_ai_training=False,
        allow_commercial_use=False,
    )
    db_session.add(text)
    await db_session.commit()

    research_lines = [line async for line in export_service.export_jsonl(db_session, purpose="research")]
    assert len(research_lines) == 2
    assert {json.loads(line)["record_type"] for line in research_lines} == {"text", "transcript_segment"}

    training_lines = [line async for line in export_service.export_jsonl(db_session, purpose="ai_training")]
    assert training_lines == []

    csv_data = await export_service.export_csv(db_session, purpose="research")
    rows = list(csv.DictReader(csv_data.splitlines()))
    assert len(rows) == 2
    assert {row["source_url"] for row in rows} == {"test://export-source"}
    assert "source_found_at" in rows[0]
    assert "license_url" in rows[0]

    forbidden = await client.get("/api/v1/exports/jsonl", headers=auth_headers)
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_export_license_filter_returns_only_matching_permitted_records(db_session):
    from app.models.source import Source, SourceStatus, SourceType
    from app.models.text_record import TextRecord
    from app.services.export import export_service

    source = Source(
        url="test://license-filter",
        domain="test",
        source_type=SourceType.USER_UPLOAD,
        status=SourceStatus.APPROVED,
    )
    db_session.add(source)
    await db_session.flush()
    db_session.add_all([
        TextRecord(
            source_id=source.id,
            title="CC0 proverb",
            body="Mũciĩ nĩ wa andũ.",
            language_code="ki",
            sha256=uuid.uuid4().hex,
            license="CC0",
            allow_public_display=True,
            allow_research_use=True,
            allow_ai_training=True,
        ),
        TextRecord(
            source_id=source.id,
            title="CC BY proverb",
            body="Ũhoro wa tene.",
            language_code="ki",
            sha256=uuid.uuid4().hex,
            license="CC BY 4.0",
            allow_public_display=True,
            allow_research_use=True,
            allow_ai_training=True,
        ),
    ])
    await db_session.commit()

    lines = [line async for line in export_service.export_jsonl(
        db_session, purpose="ai_training", license_filter="CC0"
    )]
    assert len(lines) == 1
    assert '"title": "CC0 proverb"' in lines[0]
    assert '"license": "CC0"' in lines[0]

    csv_data = await export_service.export_csv(
        db_session, purpose="ai_training", license_filter="CC0"
    )
    assert "CC0 proverb" in csv_data
    assert "CC BY proverb" not in csv_data
