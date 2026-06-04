"""Transcription orchestrator shared by both flows (recording and file upload).

Pipeline: ffmpeg extract/compress -> split if > limit -> Groq per chunk -> merge.
On Groq failure, callers catch GroqUnavailableError and call transcribe_local_fast().
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

from src.audio.utils import output_path_from_input
from src.audio.preprocessor import extract_and_compress, split_if_needed, cleanup_paths
from src.stt.groq_transcriber import GroqTranscriber, GroqUnavailableError  # noqa: F401 (re-export)
from src.stt.transcribe import Transcriber
from config.settings import GROQ_MAX_FILE_MB, LOCAL_WHISPER_MODEL, LOCAL_WHISPER_BEAM_SIZE


# Progress callback: on_progress(fraction in [0, 1] OR None for "indeterminate", message).
ProgressCallback = Optional[Callable[[Optional[float], str], None]]


def transcribe_with_groq(input_path: Path, on_progress: ProgressCallback = None) -> dict:
    """Transcribe an audio/video file via Groq. Raises GroqUnavailableError on failure.

    Progress (when ``on_progress`` is given): media conversion maps to 0–50% and the
    per-chunk Groq transcription to 50–100%. Groq returns each chunk in a single call,
    so a single-chunk file reports None (indeterminate) while that call is in flight.
    """
    input_path = Path(input_path)
    transcriber = GroqTranscriber()  # raises GroqUnavailableError if no key/SDK
    conv_cb = (lambda f, m: on_progress(0.5 * f, m)) if on_progress else None
    flac = extract_and_compress(input_path, on_progress=conv_cb)
    chunks = split_if_needed(flac, GROQ_MAX_FILE_MB)
    try:
        results = []
        n = len(chunks)
        for i, chunk in enumerate(chunks):
            if on_progress:
                if n == 1:
                    on_progress(None, "Transcrevendo áudio no Groq…")
                else:
                    on_progress(0.5 + 0.5 * (i / n), f"Transcrevendo parte {i + 1}/{n} no Groq…")
            results.append(transcriber.transcribe_file(chunk))
            if on_progress and n > 1:
                on_progress(0.5 + 0.5 * ((i + 1) / n), f"Parte {i + 1}/{n} transcrita.")
        if on_progress:
            on_progress(1.0, "Transcrição concluída.")
        return _merge_chunk_results(results)
    finally:
        cleanup_paths(set(chunks) | {flac})


def transcribe_local_fast(input_path: Path, on_progress: ProgressCallback = None) -> dict:
    """Fallback: local faster-whisper with a fast preset (small + beam_size=1)."""
    input_path = Path(input_path)
    conv_cb = (lambda f, m: on_progress(0.5 * f, m)) if on_progress else None
    try:
        audio = extract_and_compress(input_path, on_progress=conv_cb)  # makes video files work too
        cleanup_after = audio != input_path
    except Exception:
        audio = input_path  # ffmpeg missing: try the raw file directly
        cleanup_after = False

    transcriber = Transcriber(
        model_size=LOCAL_WHISPER_MODEL,
        device="cpu",
        compute_type="int8",
        language=None,
        beam_size=LOCAL_WHISPER_BEAM_SIZE,
        best_of=LOCAL_WHISPER_BEAM_SIZE,
    )
    trans_cb = (lambda f, m: on_progress(0.5 + 0.5 * f, m)) if on_progress else None
    try:
        return transcriber.transcribe_file(audio, on_progress=trans_cb)
    finally:
        if cleanup_after:
            cleanup_paths([audio])


def save_transcription(input_path: Path, result: dict) -> tuple[Path, Path]:
    """Write data/output/<stem>.txt and .json in the shape used across the project."""
    input_path = Path(input_path)
    txt_path = output_path_from_input(input_path, "txt")
    json_path = output_path_from_input(input_path, "json")
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(result["text"], encoding="utf-8")
    payload = {
        "audio_path": str(input_path),
        "language": result.get("language"),
        "language_probability": result.get("language_probability"),
        "duration": result.get("duration"),
        "segments": result.get("segments"),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return txt_path, json_path


def _merge_chunk_results(results: list[dict]) -> dict:
    """Concatenate text and shift each chunk's timestamps by the accumulated offset."""
    if not results:
        return {"language": "", "language_probability": 0.0, "duration": 0.0, "segments": [], "text": ""}
    if len(results) == 1:
        return results[0]

    merged_segments: list[dict] = []
    text_parts: list[str] = []
    offset = 0.0
    for r in results:
        for seg in r.get("segments") or []:
            merged_segments.append({
                "start": seg["start"] + offset,
                "end": seg["end"] + offset,
                "text": seg["text"],
            })
        text_parts.append(r.get("text", ""))
        offset += float(r.get("duration", 0.0))

    return {
        "language": results[0].get("language", ""),
        "language_probability": results[0].get("language_probability", 1.0),
        "duration": offset,
        "segments": merged_segments,
        "text": " ".join(t.strip() for t in text_parts if t).strip(),
    }
