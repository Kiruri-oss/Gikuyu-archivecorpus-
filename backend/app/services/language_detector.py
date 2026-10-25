import re
from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LanguageDetector:
    """Lightweight Gĩkũyũ-first heuristic with an optional multilingual model."""

    KIKUYU_MARKERS = (
        "na", "kĩ", "ũ", "mũ", "gĩ", "ny", "th", "ng'", "nj", "mb", "nd",
        "kũ", "rĩ", "ũrĩ", "nĩ", "ũndũ", "andũ", "mũndũ", "gũkũ",
    )
    # Whole-word markers are more discriminative than short character fragments.
    KIKUYU_STRONG_WORDS = frozenset({
        "gĩkũyũ", "mũciĩ", "mũndũ", "andũ", "ũhoro", "ũndũ", "gũkũ",
        "ũrĩ", "nĩ", "rĩu", "mũtĩ", "gĩthaka", "mũthenya", "kũrĩ",
        "ũgĩ", "thĩ", "ndũrĩ", "wĩ", "nĩwe", "nĩĩ",
    })
    SWAHILI_MARKERS = ("na", "ya", "wa", "kwa", "hii", "hiyo", "sana", "kabisa")
    ENGLISH_MARKERS = ("the", "and", "with", "this", "that", "from", "have")

    @lru_cache(maxsize=1)
    def _load_model(self):
        try:
            from transformers import pipeline  # type: ignore
            return pipeline("text-classification", model="papluca/xlm-roberta-base-language-detection")
        except Exception as exc:  # pragma: no cover
            logger.warning("lang_detector.model_unavailable", error=str(exc))
            return None

    def detect(self, text: str) -> tuple[str, float]:
        if not text or not text.strip():
            return ("unknown", 0.0)

        sample = text.lower()[:5000]
        tokens = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", sample, flags=re.UNICODE)
        diacritic_tokens = sum(any(char in token for char in "ĩũ") for token in tokens)
        strong_hits = sum(token in self.KIKUYU_STRONG_WORDS for token in tokens)

        # Gĩkũyũ orthography has highly informative ĩ/ũ patterns. This path keeps
        # the hunter useful without requiring the optional heavyweight model.
        if len(tokens) >= 8 and strong_hits >= 2 and diacritic_tokens >= 2:
            score = min(0.99, 0.70 + 0.04 * min(strong_hits, 5) + 0.02 * min(diacritic_tokens, 5))
            return ("ki", round(score, 4))
        if len(tokens) >= 12 and diacritic_tokens >= 5:
            return ("ki", 0.72)

        kik_hits = sum(sample.count(marker) for marker in self.KIKUYU_MARKERS)
        sw_hits = sum(sample.count(marker) for marker in self.SWAHILI_MARKERS)
        en_hits = sum(sample.count(marker) for marker in self.ENGLISH_MARKERS)
        total = kik_hits + sw_hits + en_hits + 1
        kik_ratio = kik_hits / total
        if kik_ratio >= settings.LANGUAGE_DETECTION_THRESHOLD:
            return ("ki", round(kik_ratio, 4))

        model = self._load_model()
        if model is None:
            return ("unknown", round(kik_ratio, 4))

        try:
            result = model(sample)[0]
            label = result["label"].lower()
            score = float(result["score"])
            mapping = {"sw": "sw", "en": "en", "so": "so", "fr": "fr"}
            return (mapping.get(label, label), score)
        except Exception as exc:  # pragma: no cover
            logger.error("lang_detector.inference_failed", error=str(exc))
            return ("unknown", 0.0)


language_detector = LanguageDetector()
