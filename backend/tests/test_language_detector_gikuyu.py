from app.services.language_detector import LanguageDetector


def test_detects_gikuyu_from_distinctive_orthography_without_transformers():
    detector = LanguageDetector()
    text = (
        "Gĩkũyũ nĩ lugha ya andũ. Mũndũ nĩ atũire mũciĩ wake. "
        "Ũhoro ũyũ ũrĩ na ũndũ wa gũtũũra wega. "
    ) * 2
    assert detector.detect(text)[0] == "ki"


def test_swahili_only_text_is_not_misclassified_as_gikuyu(monkeypatch):
    detector = LanguageDetector()
    monkeypatch.setattr(detector, "_load_model", lambda: None)
    text = (
        "Habari za asubuhi. Watu wanaenda sokoni na wanazungumza kuhusu kazi. "
        "Hii ni habari nzuri kwa familia na jamii. "
    ) * 3
    assert detector.detect(text)[0] != "ki"
