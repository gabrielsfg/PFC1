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
import gc
import os
import re
import string
import sys
import time
from pathlib import Path

# Cap the math-library thread pools BEFORE numpy / ctranslate2 / MKL load.
# faster-whisper (via CTranslate2) otherwise spins one OpenMP/MKL worker per
# core, and each worker reserves its own scratch buffers; on a RAM-tight box
# that surfaces as "mkl_malloc: failed to allocate memory". A small, fixed
# pool keeps the local engine's footprint flat across hundreds of clips.
_THREADS = os.environ.get("QP1_LOCAL_THREADS", "2")
for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, _THREADS)

# --- make Agent 1's modules importable, and load its .env ------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT1 = REPO_ROOT / "agente-transcricao"
sys.path.insert(0, str(AGENT1))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(AGENT1 / ".env", override=True)

import jiwer  # noqa: E402

from src.stt.transcription_service import (  # noqa: E402
    transcribe_with_groq,
    GroqUnavailableError,
)
from src.stt.transcribe import Transcriber  # noqa: E402
from src.audio.preprocessor import extract_and_compress, cleanup_paths  # noqa: E402
from config.settings import LOCAL_WHISPER_MODEL, LOCAL_WHISPER_BEAM_SIZE  # noqa: E402

_PUNCT = str.maketrans("", "", string.punctuation + "«»“”‘’–—")

# --- normalização de números por extenso (PT) para dígitos ------------------
# Evita que "2026" (hipótese) vs "dois mil e vinte e seis" (referência) conte
# como erro de transcrição, quando na verdade é só diferença de formato.
_UNITS = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9,
    "dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14, "quatorze": 14,
    "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19,
    "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60,
    "setenta": 70, "oitenta": 80, "noventa": 90,
    "cem": 100, "cento": 100, "duzentos": 200, "trezentos": 300, "quatrocentos": 400,
    "quinhentos": 500, "seiscentos": 600, "setecentos": 700, "oitocentos": 800,
    "novecentos": 900,
}
_SCALES = {"mil": 1000, "milhao": 1_000_000, "milhão": 1_000_000,
           "milhoes": 1_000_000, "milhões": 1_000_000}


def _words_to_number(tokens: list[str]) -> str:
    """Convert a run of PT number-words into a single integer string."""
    total, current = 0, 0
    for t in tokens:
        if t in _UNITS:
            current += _UNITS[t]
        elif t in _SCALES:
            scale = _SCALES[t]
            current = (current or 1) * scale
            total += current
            current = 0
        # "e" e outros conectivos são ignorados
    return str(total + current)


def _collapse_number_words(text: str) -> str:
    """Replace each maximal run of number-words/'e' by its numeric value."""
    tokens = text.split()
    out, run = [], []
    numberish = set(_UNITS) | set(_SCALES) | {"e"}
    for tok in tokens:
        if tok in numberish:
            run.append(tok)
        else:
            if run:
                # só converte se o trecho tem ao menos um número (não só "e")
                if any(t in _UNITS or t in _SCALES for t in run):
                    out.append(_words_to_number([t for t in run if t != "e"]))
                else:
                    out.extend(run)
                run = []
            out.append(tok)
    if run and any(t in _UNITS or t in _SCALES for t in run):
        out.append(_words_to_number([t for t in run if t != "e"]))
    elif run:
        out.extend(run)
    return " ".join(out)


def normalize(text: str) -> str:
    """Lowercase, drop punctuation, normalize spelled-out numbers, collapse spaces."""
    text = (text or "").lower().translate(_PUNCT)
    text = re.sub(r"\s+", " ", text).strip()
    text = _collapse_number_words(text)
    return text


def load_manifest(manifest: Path, clips_dir: Path | None, limit: int | None,
                  min_words: int = 0):
    """Yield (audio_path, reference) from a Common-Voice-style TSV/CSV.

    Skips references with fewer than ``min_words`` words: very short clips make
    a single substitution explode the per-clip WER and add little statistical
    value.
    """
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
            if min_words and len(ref.split()) < min_words:
                continue
            p = Path(audio)
            if not p.is_absolute() and clips_dir is not None:
                p = clips_dir / p
            count += 1
            yield p, ref


def _transcribe_local_reuse(model: Transcriber, path: Path) -> dict:
    """Run the local engine on one clip, reusing a single ``Transcriber``.

    Mirrors ``transcribe_local_fast`` (ffmpeg-normalize → faster-whisper) but
    does NOT reload the Whisper model per clip — the caller builds it once.
    Reloading per clip is what let MKL scratch buffers pile up and exhaust RAM.
    """
    try:
        audio = extract_and_compress(path)  # makes video files work too
        cleanup_after = audio != path
    except Exception:  # noqa: BLE001 -- ffmpeg missing: feed the raw file
        audio = path
        cleanup_after = False
    try:
        return model.transcribe_file(audio)
    finally:
        if cleanup_after:
            cleanup_paths([audio])


def transcribe(engine: str, path: Path, local_model: Transcriber | None) -> tuple[str, float, float]:
    """Return (hypothesis_text, audio_duration_s, processing_time_s)."""
    start = time.perf_counter()
    if engine == "groq":
        result = transcribe_with_groq(path)
    else:
        result = _transcribe_local_reuse(local_model, path)
    elapsed = time.perf_counter() - start
    return result.get("text", ""), float(result.get("duration") or 0.0), elapsed


def run_engine(engine: str, pairs: list[tuple[Path, str]], writer: csv.writer) -> dict:
    """Transcribe every pair with ``engine``; return aggregate metrics."""
    refs: list[str] = []
    hyps: list[str] = []
    rtfs: list[float] = []
    failures = 0

    # Build the local model ONCE and reuse it across every clip (see above).
    local_model: Transcriber | None = None
    if engine == "local":
        local_model = Transcriber(
            model_size=LOCAL_WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
            language=None,
            beam_size=LOCAL_WHISPER_BEAM_SIZE,
            best_of=LOCAL_WHISPER_BEAM_SIZE,
        )

    for i, (path, reference) in enumerate(pairs):
        if not path.exists():
            print(f"  [skip] missing audio: {path}", file=sys.stderr)
            failures += 1
            continue
        try:
            hyp, duration, elapsed = transcribe(engine, path, local_model)
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
                         f"{rtf:.3f}", f"{wer:.4f}", f"{cer:.4f}", ref_n, hyp_n])
        print(f"  {engine:5s} {path.name:30s} WER={wer:.3f} CER={cer:.3f} RTF={rtf:.2f}")

        # Reclaim CTranslate2/MKL scratch periodically so the local engine's
        # memory stays flat over a long run.
        if engine == "local" and i % 25 == 0:
            gc.collect()

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
    ap.add_argument("--min-words", type=int, default=0,
                    help="Skip references with fewer than N words (e.g. 3).")
    ap.add_argument("--out", type=Path, default=Path("results_qp1.csv"))
    args = ap.parse_args()

    pairs = list(load_manifest(args.manifest, args.clips_dir, args.limit, args.min_words))
    if not pairs:
        print("No (audio, reference) pairs found in the manifest.", file=sys.stderr)
        return 1
    engines = ["groq", "local"] if args.engine == "both" else [args.engine]
    print(f"Loaded {len(pairs)} clips; engines: {', '.join(engines)}")

    summaries = []
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["engine", "clip", "audio_s", "proc_s", "rtf", "wer", "cer",
                          "reference", "hypothesis"])
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
