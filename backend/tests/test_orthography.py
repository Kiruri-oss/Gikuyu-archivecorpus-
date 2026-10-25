from app.services.orthography import suggest_orthography


def test_suggests_kikuyu_diacritics_without_changing_other_text():
    original = "mucii wa mundu; andu ni wega."
    suggested, changes = suggest_orthography(original)
    assert suggested == "mũciĩ wa mũndũ; andũ ni wega."
    assert [item.original for item in changes] == ["mucii", "mundu", "andu"]
    assert original == "mucii wa mundu; andu ni wega."


def test_preserves_basic_capitalisation():
    suggested, changes = suggest_orthography("Mucii na GIKUYU")
    assert suggested == "Mũciĩ na GĨKŨYŨ"
    assert len(changes) == 2


def test_does_not_replace_inside_larger_words_or_empty_input():
    assert suggest_orthography("muciix andamundu") == ("muciix andamundu", [])
    assert suggest_orthography("") == ("", [])


@__import__("pytest").mark.asyncio\nasync def test_orthography_api_returns_suggestions_not_saved_changes(client):
    response = client.post("/api/v1/orthography/suggest", json={"text": "mucii"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["original_text"] == "mucii"
    assert payload["suggested_text"] == "mũciĩ"
    assert payload["suggestions"][0]["original"] == "mucii"
    assert "not automatically saved" in payload["note"]
