#!/usr/bin/env python3
"""QP1 -- Transcription accuracy (WER/CER) and Real-Time Factor (RTF).

Runs Agent 1's transcription over a corpus of (audio, reference) pairs and
reports Word Error Rate, Character Error Rate and RTF for the Groq engine
and/or the local faster-whisper fallback.

The manifest is a TSV/CSV with at least two columns:
  - ``path``     : audio file name (relative to --clips-dir) or an absolute path
  - ``sentence`` : reference transcription
These names match Mozilla Common Voice's ``*.tsv`` files, so a Common Voice PT
split works directly: point --manifest at ``validated.tsv`` (or ``test.tsv``)
and --clips-dir at the ``clips`` folder.

Run inside the agente-transcricao virtualenv (it already has groq /
faster-whisper / ffmpeg) with jiwer + python-dotenv installed:

    python qp1_wer_cer.py \
        --manifest /path/to/cv-corpus/pt/validated.tsv \
        --clips-dir /path/to/cv-corpus/pt/clips \
        --engine both --limit 200 --out results_qp1.csv

The Groq engine needs GROQ_API_KEY in agente-transcricao/.env.
"""
from __future__ import annotations

import argparse
import csv
import re
import string
import sys
import time
from pathlib import Path

# --- make Agent 1's modules importable, and load its .env ------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT1 = REPO_ROOT / "agente-transcricao"
sys.path.insert(0, str(AGENT1))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(AGENT1 / ".env", override=True)

import jiwer  # noqa: E402

from src.stt.transcription_service import (  # noqa: E402
    transcribe_with_groq,
    transcribe_local_fast,
    GroqUnavailableError,
)

_PUNCT = str.maketrans("", "", string.punctuation + "«»“”‘’–—")


def normalize(text: str) -> str:
    """Lowercase, drop punctuation and collapse whitespace (accents are kept)."""
    text = (text or "").lower().translate(_PUNCT)
    return re.sub(r"\s+", " ", text).strip()


def load_manifest(manifest: Path, clips_dir: Path | None, limit: int | None):
    """Yield (audio_path, reference) from a Common-Voice-style TSV/CSV."""
    delimiter = "\t" if manifest.suffix.lower() == ".tsv" else ","
    with manifest.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        count = 0
        for row in reader:
            if limit is not None and count >= limit:
                break
            audio = row.get("path") or row.get("audio") or row.get("file")
            ref = row.get("sentence") or row.get("reference") or row.get("text")
            if not audio or not ref:
                continue
            p = Path(audio)
            if not p.is_absolute() and clips_dir is not None:
                p = clips_dir / p
            count += 1
            yield p, ref


def transcribe(engine: str, path: Path) -> tuple[str, float, float]:
    """Return (hypothesis_text, audio_duration_s, processing_time_s)."""
    start = time.perf_counter()
    result = transcribe_with_groq(path) if engine == "groq" else transcribe_local_fast(path)
    elapsed = time.perf_counter() - start
    return result.get("text", ""), float(result.get("duration") or 0.0), elapsed


def run_engine(engine: str, pairs: list[tuple[Path, str]], writer: csv.writer) -> dict:
    """Transcribe every pair with ``engine``; return aggregate metrics."""
    refs: list[str] = []
    hyps: list[str] = []
    rtfs: list[float] = []
    failures = 0

    for path, reference in pairs:
        if not path.exists():
            print(f"  [skip] missing audio: {path}", file=sys.stderr)
            failures += 1
            continue
        try:
            hyp, duration, elapsed = transcribe(engine, path)
        except GroqUnavailableError as exc:
            print(f"  [skip] Groq unavailable ({exc}); aborting groq run.", file=sys.stderr)
            failures += 1
            break
        except Exception as exc:  # noqa: BLE001 -- one bad clip must not kill the run
            print(f"  [skip] {path.name}: {exc}", file=sys.stderr)
            failures += 1
            continue

        ref_n, hyp_n = normalize(reference), normalize(hyp)
        wer = jiwer.wer(ref_n, hyp_n) if ref_n else float("nan")
        cer = jiwer.cer(ref_n, hyp_n) if ref_n else float("nan")
        rtf = (elapsed / duration) if duration > 0 else float("nan")

        refs.append(ref_n)
        hyps.append(hyp_n)
        if rtf == rtf:  # not NaN
            rtfs.append(rtf)
        writer.writerow([engine, path.name, f"{duration:.2f}", f"{elapsed:.2f}",
                         f"{rtf:.3f}", f"{wer:.4f}", f"{cer:.4f}"])
        print(f"  {engine:5s} {path.name:30s} WER={wer:.3f} CER={cer:.3f} RTF={rtf:.2f}")

    # Corpus-level WER/CER (aggregate over all words/chars, not a mean of ratios).
    corpus_wer = jiwer.wer(refs, hyps) if refs else float("nan")
    corpus_cer = jiwer.cer(refs, hyps) if refs else float("nan")
    mean_rtf = (sum(rtfs) / len(rtfs)) if rtfs else float("nan")
    return {"engine": engine, "n": len(refs), "failures": failures,
            "wer": corpus_wer, "cer": corpus_cer, "rtf": mean_rtf}


def main() -> int:
    ap = argparse.ArgumentParser(description="QP1: WER/CER/RTF of Agent 1 transcription.")
    ap.add_argument("--manifest", required=True, type=Path,
                    help="TSV/CSV with 'path' and 'sentence' columns (Common Voice style).")
    ap.add_argument("--clips-dir", type=Path, default=None,
                    help="Base directory for relative audio paths (e.g. the 'clips' folder).")
    ap.add_argument("--engine", choices=["groq", "local", "both"], default="both")
    ap.add_argument("--limit", type=int, default=None, help="Max number of clips to score.")
    ap.add_argument("--out", type=Path, default=Path("results_qp1.csv"))
    args = ap.parse_args()

    pairs = list(load_manifest(args.manifest, args.clips_dir, args.limit))
    if not pairs:
        print("No (audio, reference) pairs found in the manifest.", file=sys.stderr)
        return 1
    engines = ["groq", "local"] if args.engine == "both" else [args.engine]
    print(f"Loaded {len(pairs)} clips; engines: {', '.join(engines)}")

    summaries = []
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["engine", "clip", "audio_s", "proc_s", "rtf", "wer", "cer"])
        for engine in engines:
            print(f"\n=== Engine: {engine} ===")
            summaries.append(run_engine(engine, pairs, writer))

    print("\n=== Aggregate (corpus-level) ===")
    print(f"{'engine':8s} {'n':>4s} {'WER':>8s} {'CER':>8s} {'meanRTF':>8s} {'fails':>6s}")
    for s in summaries:
        print(f"{s['engine']:8s} {s['n']:>4d} {s['wer']:>8.4f} {s['cer']:>8.4f} "
              f"{s['rtf']:>8.3f} {s['failures']:>6d}")
    print(f"\nPer-clip results written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
