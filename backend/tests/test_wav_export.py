import json
import os
import zipfile

from app.api.v1.exports import _build_wav_zip


def test_wav_export_bundle_contains_audio_and_source_provenance(monkeypatch):
    wav = b"RIFF\x24\x00\x00\x00WAVEfmt "

    def fake_download(bucket, key, fileobj):
        assert bucket
        assert key == "test/audio.wav"
        fileobj.write(wav)

    monkeypatch.setattr("app.api.v1.exports.storage_service.download_fileobj", fake_download)
    record = {
        "id": "media-123",
        "title": "Gĩkũyũ proverb recording",
        "file_key": "test/audio.wav",
        "size_bytes": len(wav),
        "source_url": "https://example.org/gikuyu-proverb",
        "license": "CC0",
        "sha256": "a" * 64,
        "dialect": "Ki-Murang'a",
        "speaker": "Speaker 1",
        "allow_research_use": True,
        "allow_ai_training": True,
        "allow_commercial_use": False,
    }

    zip_path = _build_wav_zip([record])
    try:
        with zipfile.ZipFile(zip_path) as archive:
            assert "audio/media-123.wav" in archive.namelist()
            manifest = json.loads(archive.read("manifest.json"))
            audio_content = archive.read("audio/media-123.wav")
        assert manifest["language_code"] == "ki"
        assert manifest["records"][0]["source_url"] == record["source_url"]
        assert manifest["records"][0]["license"] == "CC0"
        assert manifest["records"][0]["allow_ai_training"] is True
        assert audio_content == wav
    finally:
        os.unlink(zip_path)
