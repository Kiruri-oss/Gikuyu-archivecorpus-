import pytest
from pydantic import ValidationError

from app.schemas.text_record import TextRecordCreate


def test_text_record_accepts_gikuyu_language_code():
    payload = TextRecordCreate(
        title="Mũciĩ",
        body="Mũciĩ nĩ ũhoro.",
        language_code="ki",
        license="CC-BY",
        consent_to_archive=True,
        confirm_rights=True,
    )
    assert payload.language_code == "ki"


@pytest.mark.parametrize("language_code", ["sw", "en", "rw", "ha", "not-a-language"])
def test_text_record_rejects_every_non_gikuyu_language(language_code):
    with pytest.raises(ValidationError, match="accepts Gĩkũyũ"):
        TextRecordCreate(
            title="Test",
            body="Test body",
            language_code=language_code,
            license="CC-BY",
            consent_to_archive=True,
            confirm_rights=True,
            language_confirmed=True,
        )
