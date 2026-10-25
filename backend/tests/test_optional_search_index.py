import pytest
from app.services.indexing import SearchIndexService, settings


@pytest.mark.asyncio
async def test_search_index_can_be_disabled_without_blocking_archive(monkeypatch):
    monkeypatch.setattr(settings, "MEILISEARCH_URL", None)
    monkeypatch.setattr(settings, "MEILISEARCH_KEY", None)
    service = SearchIndexService()
    assert service.enabled is False
    await service.ensure_indexes()
    await service.index_document("texts", {"id": "test"})
    await service.delete_document("texts", "test")
    assert await service.search("texts", "Gĩkũyũ") == {"hits": []}
