import json

import pytest
from fastapi import HTTPException

from app.api.v1.media import upload_media


@pytest.mark.asyncio
async def test_audio_upload_rejects_missing_speaker_consent_before_storage():
    metadata = {
        "title": "Gĩkũyũ story",
        "license": "CC-BY",
        "consent_to_archive": True,
        "confirm_rights": True,
        "speaker_consent_confirmed": False,
        "language_confirmed": True,
    }

    with pytest.raises(HTTPException) as raised:
        await upload_media(db=None, user=None, file=None, meta=json.dumps(metadata))

    assert raised.value.status_code == 422
    assert "speaker" in raised.value.detail.lower()


@pytest.mark.asyncio
async def test_audio_upload_rejects_unconfirmed_language_before_storage():
    metadata = {
        "title": "Gĩkũyũ story",
        "license": "CC-BY",
        "consent_to_archive": True,
        "confirm_rights": True,
        "speaker_consent_confirmed": True,
        "language_confirmed": False,
    }

    with pytest.raises(HTTPException) as raised:
        await upload_media(db=None, user=None, file=None, meta=json.dumps(metadata))

    assert raised.value.status_code == 422
    assert "gĩkũyũ" in raised.value.detail.lower()
