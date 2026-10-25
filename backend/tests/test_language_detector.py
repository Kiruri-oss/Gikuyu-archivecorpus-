from app.services.language_detector import LanguageDetector


def test_distinctive_gikuyu_text_is_detected_as_kikuyu(monkeypatch):
    detector = LanguageDetector()
    monkeypatch.setattr(detector, "_load_model", lambda: None)

    language, confidence = detector.detect(
        "Nĩguo mũndũ aĩkaga wĩra wake mũciĩ. Andũ nĩmagĩrĩire ũndũ ũcio."
    )

    assert language == "ki"
    assert confidence >= 0.55


def test_common_syllables_do_not_make_swahili_look_like_kikuyu(monkeypatch):
    detector = LanguageDetector()
    monkeypatch.setattr(detector, "_load_model", lambda: None)

    language, _ = detector.detect(
        "Habari za asubuhi. Watu wanakwenda kwa nyumba zao, lakini leo hakuna nafasi."
    )

    assert language == "unknown"


def test_english_text_is_not_classified_as_kikuyu(monkeypatch):
    detector = LanguageDetector()
    monkeypatch.setattr(detector, "_load_model", lambda: None)

    language, _ = detector.detect(
        "The people and their language are important. This text is about their history."
    )

    assert language == "unknown"


def test_ambiguous_single_word_is_not_auto_classified(monkeypatch):
    detector = LanguageDetector()
    monkeypatch.setattr(detector, "_load_model", lambda: None)

    language, _ = detector.detect("mũciĩ")

    assert language == "unknown"
