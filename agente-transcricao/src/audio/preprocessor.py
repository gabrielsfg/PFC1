"""Audio preprocessing: extract/compress with ffmpeg and split large files.

Both flows (live recording and file upload) go through here before transcription,
so a 581 MB meeting video becomes a small 16 kHz mono FLAC ready for Groq.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable, Optional

_PROCESSED_DIR = Path("data/input/_processed")

# Progress callback: on_progress(fraction in [0, 1], human message).
ProgressCallback = Optional[Callable[[float, str], None]]


def ensure_ffmpeg() -> None:
    """Raise a friendly error if ffmpeg is not on the PATH."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg não encontrado no PATH. Instale-o e tente novamente "
            "(Windows: 'winget install Gyan.FFmpeg')."
        )


def _media_duration_seconds(path: Path) -> Optional[float]:
    """Total media duration via ffprobe, or None if it can't be determined."""
    if shutil.which("ffprobe") is None:
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return float(out) if out else None
    except Exception:
        return None


def extract_and_compress(input_path: Path, on_progress: ProgressCallback = None) -> Path:
    """Extract audio from any audio/video file as 16 kHz mono FLAC.

    Whisper resamples to 16 kHz mono internally, so this is lossless for STT and
    drops the video stream. FLAC of dense speech runs ~60-100 MB per hour, so long
    meetings are split into chunks by split_if_needed before upload.

    When ``on_progress`` is given, ffmpeg's ``-progress`` stream is parsed to report
    real conversion progress (fraction in [0, 1] of the media duration).
    """
    ensure_ffmpeg()
    input_path = Path(input_path)
    _PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _PROCESSED_DIR / f"{input_path.stem}_16k.flac"
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "flac",
    ]

    if on_progress is None:
        subprocess.run(
            cmd + [str(out_path)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return out_path

    total = _media_duration_seconds(input_path)
    proc = subprocess.Popen(
        cmd + ["-progress", "pipe:1", "-nostats", str(out_path)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )
    try:
        for line in proc.stdout or []:
            key, _, val = line.strip().partition("=")
            # Both out_time_us (newer ffmpeg) and out_time_ms (older) carry microseconds.
            if key in ("out_time_us", "out_time_ms") and total:
                try:
                    frac = max(0.0, min(1.0, (int(val) / 1_000_000) / total))
                except (ValueError, ZeroDivisionError):
                    continue
                on_progress(frac, f"Convertendo mídia em áudio… {int(frac * 100)}%")
            elif key == "progress" and val == "end":
                on_progress(1.0, "Áudio extraído.")
    finally:
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg falhou (código {proc.returncode}) ao processar {input_path.name}."
        )
    return out_path


def split_if_needed(audio_path: Path, max_mb: float = 24.0) -> list[Path]:
    """Split the audio into chunks (cutting on silence) only if it exceeds max_mb.

    Every returned chunk is guaranteed to be <= max_mb. We aim each cut at a byte
    size safely below the limit (speech compresses worse than silence, so equal-time
    cuts vary a lot in bytes), and any chunk that still ends up oversized is halved
    again until it fits.

    Returns a list of chunk paths (a single-element list when no split is needed).
    """
    audio_path = Path(audio_path)
    size_mb = audio_path.stat().st_size / (1024 * 1024)
    if size_mb <= max_mb:
        return [audio_path]

    from pydub import AudioSegment

    audio = AudioSegment.from_file(str(audio_path))
    # Target chunk byte-size = 80% of the limit to absorb compression variance.
    bytes_per_ms = audio_path.stat().st_size / max(1, len(audio))
    target_ms = max(1000, int(max_mb * 0.8 * 1024 * 1024 / bytes_per_ms))

    boundaries = _find_cut_points(audio, target_ms) + [len(audio)]

    counter = [0]
    paths: list[Path] = []
    prev = 0
    for point in boundaries:
        if point <= prev:
            continue
        _export_under_limit(audio[prev:point], audio_path, max_mb, counter, paths)
        prev = point
    return paths or [audio_path]


def _export_under_limit(segment, base_path: Path, max_mb: float,
                        counter: list, out_paths: list) -> None:
    """Export one segment to FLAC; if it exceeds max_mb, halve it by time and recurse.

    Guarantees each produced file is <= max_mb (down to a ~2 s floor).
    """
    out = base_path.parent / f"{base_path.stem}_chunk_{counter[0]:03d}.flac"
    counter[0] += 1
    segment.export(str(out), format="flac")
    if out.stat().st_size / (1024 * 1024) <= max_mb or len(segment) <= 2000:
        out_paths.append(out)
        return
    out.unlink(missing_ok=True)  # too big: discard and split this segment in half
    mid = len(segment) // 2
    _export_under_limit(segment[:mid], base_path, max_mb, counter, out_paths)
    _export_under_limit(segment[mid:], base_path, max_mb, counter, out_paths)


def cleanup_paths(paths: Iterable[Path]) -> None:
    """Best-effort removal of intermediate files."""
    for p in paths:
        try:
            Path(p).unlink(missing_ok=True)
        except Exception:
            pass


def _find_cut_points(audio, target_ms: int, search_window_ms: int = 15000,
                     min_silence_ms: int = 400) -> list[int]:
    """Pick cut positions near each target boundary, snapped to the nearest silence."""
    from pydub.silence import detect_silence

    total = len(audio)
    points: list[int] = []
    boundary = target_ms
    while boundary < total:
        win_start = max(0, boundary - search_window_ms)
        win_end = min(total, boundary + search_window_ms)
        window = audio[win_start:win_end]
        thresh = (window.dBFS if window.dBFS != float("-inf") else -40) - 16
        silences = detect_silence(window, min_silence_len=min_silence_ms, silence_thresh=thresh)
        if silences:
            best = min(
                silences,
                key=lambda s: abs((win_start + (s[0] + s[1]) // 2) - boundary),
            )
            cut = win_start + (best[0] + best[1]) // 2
        else:
            cut = boundary
        if points and cut <= points[-1]:
            cut = boundary
        points.append(cut)
        boundary += target_ms
    return points
