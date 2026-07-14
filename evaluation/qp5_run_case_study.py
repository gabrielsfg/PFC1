#!/usr/bin/env python3
"""QP5 (case study) -- roda o pipeline na reunião real cronometrando cada agente.

Executa Agente 1 (transcrição Groq), Agente 2 (identificação) e Agente 3 (documento
empresa) sobre o vídeo da reunião do parceiro, medindo o tempo de relógio por
estágio e acumulando o uso de tokens (Agentes 2 e 3). Produz:
  - timings.csv : stage, seconds, audio_seconds (para o Agente 1), notas
  - usage.csv   : stage, model, input_tokens, output_tokens  (alimenta qp5_cost.py)

Cada agente roda no seu próprio venv via subprocess? Não: para capturar tokens com
precisão, chamamos as bibliotecas diretamente. Por isso ESTE script deve rodar com
um interpretador que tenha acesso aos três agentes. Como os venvs são separados,
rodamos cada etapa via o subprocess do venv correspondente e lemos a saída.

Uso (a partir da raiz do repo):
    python evaluation/qp5_run_case_study.py --audio "caminho/reuniao.mp4"
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "agente-transcricao"
A2 = REPO / "agente-identificacao"
A3 = REPO / "agente-srs"
PY = lambda agent: agent / "venv" / "Scripts" / "python.exe"


def run(cmd: list[str], cwd: Path) -> tuple[float, str]:
    """Run a command, returning (elapsed_seconds, combined_stdout+stderr)."""
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        print(out)
        raise SystemExit(f"FALHOU ({cwd.name}): exit {proc.returncode}")
    return elapsed, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True, type=Path)
    ap.add_argument("--project-name", default="Controle de Saldo Orçamentário")
    ap.add_argument("--out-dir", type=Path, default=REPO / "evaluation")
    args = ap.parse_args()

    audio = args.audio.resolve()
    if not audio.exists():
        raise SystemExit(f"Áudio não encontrado: {audio}")

    timings = []  # (stage, seconds, extra)

    # ---------------- Agente 1: transcrição (Groq) ----------------
    print("=== Agente 1: transcrição (Groq) ===")
    helper = (
        "import sys, time, json\n"
        "from pathlib import Path\n"
        "from dotenv import load_dotenv\n"
        "load_dotenv('.env', override=True)\n"
        "from src.stt.transcription_service import transcribe_with_groq, save_transcription\n"
        f"audio = Path(r'{audio}')\n"
        "t0 = time.perf_counter()\n"
        "res = transcribe_with_groq(audio)\n"
        "el = time.perf_counter() - t0\n"
        "txt, js = save_transcription(audio, res)\n"
        "print('TXT_PATH=' + str(Path(txt).resolve()))\n"
        "print('AUDIO_SECONDS=' + str(res.get('duration') or 0))\n"
        "print('PROC_SECONDS=%.2f' % el)\n"
    )
    el1, out1 = run([str(PY(A1)), "-c", helper], cwd=A1)
    txt_path = next((l.split("=", 1)[1] for l in out1.splitlines() if l.startswith("TXT_PATH=")), "")
    audio_s = next((l.split("=", 1)[1] for l in out1.splitlines() if l.startswith("AUDIO_SECONDS=")), "0")
    proc_s = next((l.split("=", 1)[1] for l in out1.splitlines() if l.startswith("PROC_SECONDS=")), f"{el1:.2f}")
    print(f"  transcrição salva: {txt_path}")
    print(f"  áudio={audio_s}s  proc={proc_s}s")
    timings.append(("agente1_transcricao", proc_s, f"audio_s={audio_s}"))

    # ---------------- Agente 2: identificação ----------------
    print("=== Agente 2: identificação ===")
    el2, out2 = run([str(PY(A2)), "main.py", "--file", txt_path, "--output-dir", "./data/output"], cwd=A2)
    # localizar o JSON mais recente
    json_path = max((A2 / "data" / "output").glob("*_personas_*.json"), key=lambda p: p.stat().st_mtime)
    print(f"  JSON: {json_path}  ({el2:.2f}s)")
    timings.append(("agente2_identificacao", f"{el2:.2f}", json_path.name))

    # ---------------- Agente 3: documento (empresa) ----------------
    print("=== Agente 3: documento (formato empresa) ===")
    el3, out3 = run([str(PY(A3)), "main.py", "--file", str(json_path),
                     "--format", "empresa", "--project-name", args.project_name], cwd=A3)
    timings.append(("agente3_documento", f"{el3:.2f}", "formato=empresa"))
    print(f"  documento gerado ({el3:.2f}s)")

    # ---------------- gravar timings ----------------
    tpath = args.out_dir / "timings.csv"
    with tpath.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stage", "seconds", "notes"])
        for row in timings:
            w.writerow(row)
    print(f"\nTimings -> {tpath}")
    print("Tokens: capture os totais impressos pelos Agentes 2 e 3 (ou via console "
          "da Anthropic) e monte usage.csv para qp5_cost.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
