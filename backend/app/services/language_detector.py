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
    # Many online Gĩkũyũ sources omit the diacritics. These lexical markers
    # allow the Hunter to find that material without treating generic syllables
    # or English pages merely mentioning Kikuyu as Gĩkũyũ text.
    KIKUYU_ASCII_MARKERS = frozenset({
        "muthuri", "mutumia", "mucii", "ciana", "ngatho", "thayu",
        "agikuyu", "mugikuyu", "mbari", "nduriri", "guthoma",
        "gucooka", "ithui", "inyui", "athuri", "atumia", "mugumo",
        "murata", "mugambo", "njamba", "gikuyu",
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
        ascii_signals = unique_tokens & self.KIKUYU_ASCII_MARKERS
        sw_signals = unique_tokens & self.SWAHILI_MARKERS
        en_signals = unique_tokens & self.ENGLISH_MARKERS
        kik_hits = len(kik_signals)
        total = kik_hits + len(ascii_signals) + len(sw_signals) + len(en_signals) + 1
        kik_ratio = (kik_hits + len(ascii_signals)) / total

        # Diacritic-rich writing needs two independent signals; unmarked writing
        # needs three lexical signals so an English page merely mentioning Kikuyu
        # does not become a false-positive corpus record.
        if kik_hits >= 2 and kik_ratio >= settings.LANGUAGE_DETECTION_THRESHOLD:
            return ("ki", round(kik_ratio, 4))
        if len(ascii_signals) >= 3 and kik_ratio >= max(0.45, settings.LANGUAGE_DETECTION_THRESHOLD - 0.10):
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
