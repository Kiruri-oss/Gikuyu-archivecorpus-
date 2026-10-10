from app.core.logging import get_logger

logger = get_logger(__name__)


class TranscriptionService:
    """
    Wraps OpenAI Whisper for Kikuyu transcription.
    Uses the fine-tuned `microsoft/paza-whisper-large-v3-turbo` checkpoint
    (trained on Kenya Next Voices + DigiGreen Kikuyu) when available.
    """

    def __init__(self, model_name: str = "microsoft/paza-whisper-large-v3-turbo") -> None:
        self.model_name = model_name
        self._pipeline = None

    def _ensure_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline
        try:
            from transformers import pipeline  # type: ignore
            self._pipeline = pipeline(
                "automatic-speech-recognition",
                model=self.model_name,
                chunk_length_s=30,
                device=-1,
            )
            logger.info("transcription.model_loaded", model=self.model_name)
        except Exception as exc:
            logger.error("transcription.model_load_failed", error=str(exc))
            self._pipeline = None
        return self._pipeline

    def transcribe(self, audio_path: str) -> dict:
        pipe = self._ensure_pipeline()
        if pipe is None:
            return {"text": "", "language": "ki", "status": "unavailable"}
        try:
            result = pipe(audio_path, generate_kwargs={"language": "sw"})
            return {
                "text": result.get("text", "").strip(),
                "language": "ki",
                "status": "ok",
            }
        except Exception as exc:
            logger.error("transcription.failed", error=str(exc))
            return {"text": "", "language": "ki", "status": "error"}


transcription_service = TranscriptionService()