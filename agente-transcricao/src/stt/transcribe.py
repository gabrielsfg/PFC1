from pathlib import Path
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
        vad_filter: bool = True,
    ):
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        self.language = language
        self.vad_filter = vad_filter

    def transcribe_file(self, audio_path: Path) -> dict:
        segments, info = self.model.transcribe(
            str(audio_path),
            language=self.language,
            vad_filter=self.vad_filter,
            vad_parameters={"min_silence_duration_ms": 500},
            beam_size=5,
            best_of=5
        )

        text_parts = []
        segs = []
        for seg in segments:
            segs.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            })
            text_parts.append(seg.text.strip())

        full_text = " ".join(text_parts).strip()

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": segs,
            "text": full_text
        }