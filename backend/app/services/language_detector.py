import re
from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LanguageDetector:
    """
    Conservative Gĩkũyũ detector for corpus ingestion.

    It prefers distinctive Gĩkũyũ orthography and vocabulary over generic
    letter sequences shared with Kiswahili or English. Unknown text is not
    promoted to Gĩkũyũ merely because a common syllable appears frequently.
    """

    KIKUYU_MARKERS = frozenset({
        "nĩ", "rĩ", "kĩ", "mũ", "gĩ", "ũndũ", "andũ", "mũndũ", "gũkũ",
        "kũ", "ũrĩ", "nĩguo", "gĩkũyũ", "mũciĩ", "nyũmba", "wĩra",
        "ũhoro", "gũtirĩ", "mũthenya", "rĩrĩa", "ũcio", "ĩno", "ĩyo",
        "ndĩ", "nĩwe", "thutha", "gũcooka", "ũgĩ", "mũthenya",
    })
    SWAHILI_MARKERS = frozenset({
        "kwa", "hii", "hiyo", "sana", "kabisa", "yake", "watu", "habari",
        "ndiyo", "lakini", "mimi", "wewe", "sisi", "nyumba", "mtu",
        "kwamba", "bila", "kama", "leo", "asubuhi", "nzuri", "karibu",
    })
    ENGLISH_MARKERS = frozenset({
        "the", "and", "with", "this", "that", "from", "have", "people",
        "language", "their", "there", "which", "would", "about", "because",
    })

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
        tokens = re.findall(r"[a-zĩũ]+(?:['’][a-zĩũ]+)?", sample)
        if not tokens:
            return ("unknown", 0.0)

        unique_tokens = set(tokens)
        kik_signals = {
            token for token in unique_tokens
            if token in self.KIKUYU_MARKERS or "ĩ" in token or "ũ" in token
        }
        sw_signals = unique_tokens & self.SWAHILI_MARKERS
        en_signals = unique_tokens & self.ENGLISH_MARKERS
        kik_hits = len(kik_signals)
        total = kik_hits + len(sw_signals) + len(en_signals) + 1
        kik_ratio = kik_hits / total

        # Require more than one independent signal to avoid labelling short,
        # ambiguous words as Gĩkũyũ. A caller can send uncertain text for review.
        if kik_hits >= 2 and kik_ratio >= settings.LANGUAGE_DETECTION_THRESHOLD:
            return ("ki", round(kik_ratio, 4))

        model = self._load_model()
        if model is None:
            return ("unknown", round(kik_ratio, 4))

        try:
            result = model(sample)[0]
            label = str(result["label"]).lower()
            score = float(result["score"])
            mapping = {"sw": "sw", "en": "en", "so": "so", "fr": "fr"}
            return (mapping.get(label, label), score)
        except Exception as exc:  # pragma: no cover
            logger.error("lang_detector.inference_failed", error=str(exc))
            return ("unknown", 0.0)


language_detector = LanguageDetector()
