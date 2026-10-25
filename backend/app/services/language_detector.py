from functools import lru_cache
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LanguageDetector:
    """
    Lightweight heuristic + optional transformer-based Kikuyu detector.
    Falls back to trigram frequency when the transformer is unavailable.
    """

    KIKUYU_MARKERS = (
        "na", "kĩ", "ũ", "mũ", "gĩ", "ny", "th", "ng'", "nj", "mb", "nd",
        "kũ", "rĩ", "ũrĩ", "nĩ", "ũndũ", "andũ", "mũndũ", "gũkũ",
    )
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

        sample = text.lower()[:2000]

        # Fast path: Kikuyu-specific digraph/trigraph signals
        kik_hits = sum(sample.count(m) for m in self.KIKUYU_MARKERS)
        sw_hits = sum(sample.count(m) for m in self.SWAHILI_MARKERS)
        en_hits = sum(sample.count(m) for m in self.ENGLISH_MARKERS)
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