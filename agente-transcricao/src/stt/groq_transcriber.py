"""Groq Whisper transcription client (default engine)."""
from __future__ import annotations

from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import GROQ_API_KEY, GROQ_MODEL


class GroqUnavailableError(Exception):
    """Raised when Groq cannot be used: missing key/SDK, auth error, or network failure.

    Callers should catch this and offer the local Whisper fallback.
    """


class GroqTranscriber:
    def __init__(self):
        if not GROQ_API_KEY:
            raise GroqUnavailableError("GROQ_API_KEY não configurada no .env.")
        try:
            from groq import Groq
        except ImportError as e:
            raise GroqUnavailableError(f"SDK 'groq' não instalado: {e}")
        self.model = GROQ_MODEL
        self._client = Groq(api_key=GROQ_API_KEY)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def _call(self, path: Path):
        with open(path, "rb") as f:
            return self._client.audio.transcriptions.create(
                file=(path.name, f.read()),
                model=self.model,
                response_format="verbose_json",
                temperature=0,
            )

    def transcribe_file(self, audio_path: Path) -> dict:
        """Transcribe one (already preprocessed, <25 MB) audio file via Groq.

        Returns the same dict shape as the local Transcriber.
        Raises GroqUnavailableError on any API/network failure.
        """
        path = Path(audio_path)
        try:
            resp = self._call(path)
        except Exception as e:  # auth, rate, network, timeout — treat as unavailable
            raise GroqUnavailableError(f"Falha ao transcrever via Groq: {e}") from e
        return _normalize_response(resp)


def _normalize_response(resp) -> dict:
    data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
    segments = []
    for seg in data.get("segments") or []:
        segments.append({
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "text": (seg.get("text") or "").strip(),
        })
    return {
        "language": data.get("language", ""),
        "language_probability": 1.0,
        "duration": float(data.get("duration", 0.0)),
        "segments": segments,
        "text": (data.get("text") or "").strip(),
    }
