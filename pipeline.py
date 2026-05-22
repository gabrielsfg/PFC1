"""
Pipeline multi-agente de elicitação de requisitos.

Modos de entrada (mutuamente exclusivos):
  --full            Abre a GUI de gravação e encadeia todos os agentes ao parar
  --from-audio      Começa a partir de um arquivo de áudio existente (pula gravação)
  --from-transcript Começa a partir de um .txt de transcrição (pula Agents 1)
  --from-json       Começa a partir do JSON do Agent 2 (pula Agents 1 e 2)

Em todos os casos os agentes 3 e 4 são executados sequencialmente ao final.
"""

import argparse
import sys
import threading
from pathlib import Path

# ── resolve project root so each agent package is importable ─────────────────
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))


# ── Agent runners ─────────────────────────────────────────────────────────────

def _venv_python(agent_dir: str) -> str:
    """Returns the path to the venv Python for a given agent folder."""
    return str(_ROOT / agent_dir / ".venv" / "bin" / "python")


def _run_agent2(txt_path: Path) -> Path:
    import subprocess
    python = _venv_python("agente-identificacao")
    output_dir = str(_ROOT / "agente-identificacao" / "data" / "output")
    result = subprocess.run(
        [python, "main.py", "--file", str(txt_path.resolve()), "--output-dir", output_dir],
        cwd=str(_ROOT / "agente-identificacao"),
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Agent 2 falhou.")
    out_dir = Path(output_dir)
    candidates = sorted(out_dir.glob(f"{txt_path.stem}_personas_*.json"), reverse=True)
    if not candidates:
        raise RuntimeError(f"Nenhum JSON encontrado em {out_dir}")
    return candidates[0]


def _run_agent3(json_path: Path) -> Path:
    import subprocess
    python = _venv_python("agente-srs")
    output_dir = str(_ROOT / "agente-srs" / "data" / "output")
    result = subprocess.run(
        [python, "main.py", "--file", str(json_path.resolve())],
        cwd=str(_ROOT / "agente-srs"),
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Agent 3 falhou.")
    out_dir = Path(output_dir)
    candidates = sorted(out_dir.glob(f"{json_path.stem.replace('_personas_', '_srs_')}*.md"), reverse=True)
    if not candidates:
        candidates = sorted(out_dir.glob("*.md"), reverse=True)
    if not candidates:
        raise RuntimeError(f"Nenhum .md encontrado em {out_dir}")
    return candidates[0]


def _run_agent4(json_path: Path, srs_md_path: Path) -> dict:
    import subprocess
    python = _venv_python("agente-diagramas")
    output_dir = str(_ROOT / "agente-diagramas" / "data" / "output")
    result = subprocess.run(
        [python, "main.py", "--file", str(json_path.resolve()), "--srs-md", str(srs_md_path.resolve())],
        cwd=str(_ROOT / "agente-diagramas"),
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Agent 4 falhou.")
    out_dir = Path(output_dir)
    pdf = sorted(out_dir.glob("*.pdf"), reverse=True)
    md = sorted(out_dir.glob("*.md"), reverse=True)
    return {
        "pdf": str(pdf[0]) if pdf else None,
        "markdown": str(md[0]) if md else None,
        "entities": 0,
        "relationships": 0,
    }


def _run_agents3_and_4(json_path: Path) -> dict:
    print(f"\n{'='*60}")
    print("AGENT 3 — SRS + Casos de Uso")
    print(f"{'='*60}")
    srs_md = _run_agent3(json_path)

    print(f"\n{'='*60}")
    print("AGENT 4 — Diagrama de Domínio + Documento Final")
    print(f"{'='*60}")
    final = _run_agent4(json_path, srs_md_path=srs_md)
    return final


# ── Entry points per starting stage ──────────────────────────────────────────

def _from_transcript(txt_path: Path) -> None:
    print(f"\n{'='*60}")
    print("AGENT 2 — Identificação de Personas")
    print(f"{'='*60}")
    json_path = _run_agent2(txt_path)
    result = _run_agents3_and_4(json_path)
    _print_summary(result)


def _from_json(json_path: Path) -> None:
    result = _run_agents3_and_4(json_path)
    _print_summary(result)


def _from_audio(audio_path: Path) -> None:
    import os
    from dotenv import load_dotenv
    load_dotenv(_ROOT / "agente-transcricao" / ".env")

    sys.path.insert(0, str(_ROOT / "agente-transcricao"))
    from src.stt.transcribe import Transcriber  # type: ignore
    from src.audio.utils import output_path_from_input  # type: ignore

    print(f"\n{'='*60}")
    print("AGENT 1 — Transcrição")
    print(f"{'='*60}")
    print(f"Transcrevendo: {audio_path.name}...")

    tr = Transcriber(model_size="medium", device="cpu", compute_type="int8", language=None)
    result = tr.transcribe_file(audio_path)

    import json as _json
    txt_path = output_path_from_input(audio_path, "txt")
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(result["text"], encoding="utf-8")

    json_out = output_path_from_input(audio_path, "json")
    json_out.write_text(
        _json.dumps({
            "audio_path": str(audio_path),
            "language": result["language"],
            "language_probability": result["language_probability"],
            "duration": result["duration"],
            "segments": result["segments"],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Transcrição salva em: {txt_path}")
    _from_transcript(txt_path)


def _full_pipeline() -> None:
    """Opens the recording GUI; on stop, runs the full pipeline."""
    import tkinter as tk
    from tkinter import messagebox
    import json as _json
    import time

    sys.path.insert(0, str(_ROOT / "agente-transcricao"))
    from src.audio.record import record_wav_continuous  # type: ignore
    from src.audio.utils import default_input_path, output_path_from_input  # type: ignore
    from src.stt.transcribe import Transcriber  # type: ignore

    stop_event = None
    _recording_start = [0.0]
    _timer_active = [False]

    def beep(freq=800, dur_ms=150):
        try:
            import winsound
            winsound.Beep(freq, dur_ms)
        except Exception:
            sys.stdout.write("\a")
            sys.stdout.flush()

    def set_status(text, color="#aaaaaa"):
        status_label.config(text=text, fg=color)
        root.update()

    def set_phase(step, total, description):
        phase_label.config(text=f"Etapa {step}/{total}: {description}")
        root.update()

    def _tick_timer():
        if _timer_active[0]:
            elapsed = int(time.time() - _recording_start[0])
            m, s = divmod(elapsed, 60)
            timer_label.config(text=f"Gravando: {m:02d}:{s:02d}")
            root.after(1000, _tick_timer)
        else:
            timer_label.config(text="")

    def _pipeline_thread(audio_path):
        try:
            set_phase(1, 4, "Transcrevendo audio...")
            set_status("Isso pode levar alguns minutos.", "#ffaa00")
            tr = Transcriber(model_size="medium", device="cpu", compute_type="int8", language=None)
            result = tr.transcribe_file(audio_path)

            txt_path = output_path_from_input(audio_path, "txt")
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            txt_path.write_text(result["text"], encoding="utf-8")

            json_out = output_path_from_input(audio_path, "json")
            json_out.write_text(
                _json.dumps({
                    "audio_path": str(audio_path),
                    "language": result["language"],
                    "language_probability": result["language_probability"],
                    "duration": result["duration"],
                    "segments": result["segments"],
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            set_phase(2, 4, "Identificando personas e user stories...")
            set_status("Analisando transcricao com IA.", "#ffaa00")
            json_path = _run_agent2(txt_path)

            set_phase(3, 4, "Gerando documento SRS (IEEE 830)...")
            set_status("Estruturando requisitos.", "#ffaa00")
            srs_md = _run_agent3(json_path)

            set_phase(4, 4, "Gerando diagrama de dominio e documento final...")
            set_status("Finalizando...", "#ffaa00")
            final = _run_agent4(json_path, srs_md_path=srs_md)

            doc = final.get('pdf') or final.get('markdown') or ''
            doc_path = Path(doc) if doc else None
            doc_name = doc_path.name if doc_path else "ver agente-diagramas/data/output/"
            doc_dir = str(doc_path.parent) if doc_path else "agente-diagramas/data/output/"

            phase_label.config(text="Pipeline concluido com sucesso!")
            set_status("", "#4CAF50")
            result_label.config(
                text=f"Arquivo: {doc_name}\nPasta: {doc_dir}",
                fg="#4CAF50"
            )
            root.update()
        except Exception as e:
            phase_label.config(text="Erro no pipeline.")
            set_status(str(e), "#f44336")
            messagebox.showerror("Erro", str(e))
        finally:
            btn_start.config(state=tk.NORMAL)

    def on_start():
        nonlocal stop_event
        stop_event = threading.Event()
        audio_path = default_input_path()

        btn_start.config(state=tk.DISABLED)
        btn_stop.config(state=tk.NORMAL)
        phase_label.config(text="Gravando...")
        set_status("Clique em Parar quando terminar.", "#aaaaaa")
        _recording_start[0] = time.time()
        _timer_active[0] = True
        _tick_timer()
        beep()

        def record_then_pipeline():
            try:
                record_wav_continuous(audio_path, stop_event)
                beep(1000, 250)
                _timer_active[0] = False
                btn_stop.config(state=tk.DISABLED)
                _pipeline_thread(audio_path)
            except Exception as e:
                _timer_active[0] = False
                set_status(f"Erro na gravacao: {e}", "#f44336")
                btn_start.config(state=tk.NORMAL)
                btn_stop.config(state=tk.DISABLED)

        threading.Thread(target=record_then_pipeline, daemon=True).start()

    def on_stop():
        if stop_event:
            btn_stop.config(state=tk.DISABLED)
            phase_label.config(text="Encerrando gravacao...")
            stop_event.set()

    root = tk.Tk()
    root.title("Pipeline de Elicitacao de Requisitos")
    root.geometry("500x300")
    root.resizable(False, False)
    root.configure(bg="#2b2b2b")

    tk.Label(
        root,
        text="Pipeline de Elicitacao de Requisitos",
        font=("Helvetica", 14, "bold"),
        bg="#2b2b2b", fg="white"
    ).pack(pady=(20, 2))

    tk.Label(
        root,
        text="Grava a reuniao e gera: SRS · Casos de Uso · Diagrama · Documento Final",
        font=("Helvetica", 10),
        bg="#2b2b2b", fg="#aaaaaa"
    ).pack(pady=(0, 12))

    btn_frame = tk.Frame(root, bg="#2b2b2b")
    btn_frame.pack()

    btn_start = tk.Button(btn_frame, text="Iniciar Gravacao", command=on_start,
                          width=18, bg="#4CAF50", fg="white", font=("Helvetica", 11))
    btn_start.pack(side=tk.LEFT, padx=8)

    btn_stop = tk.Button(btn_frame, text="Parar Gravacao", command=on_stop,
                         width=18, bg="#f44336", fg="white", font=("Helvetica", 11),
                         state=tk.DISABLED)
    btn_stop.pack(side=tk.LEFT, padx=8)

    timer_label = tk.Label(root, text="", font=("Helvetica", 12, "bold"),
                           bg="#2b2b2b", fg="#4CAF50")
    timer_label.pack(pady=(12, 0))

    phase_label = tk.Label(root, text="Pronto.", font=("Helvetica", 11, "bold"),
                           bg="#2b2b2b", fg="white")
    phase_label.pack(pady=(4, 0))

    status_label = tk.Label(root, text="Clique em Iniciar Gravacao para comecar.",
                            font=("Helvetica", 9), bg="#2b2b2b", fg="#aaaaaa")
    status_label.pack(pady=(2, 0))

    result_label = tk.Label(root, text="", font=("Helvetica", 9),
                            bg="#2b2b2b", fg="#4CAF50", justify="center")
    result_label.pack(pady=(4, 0))

    root.update()
    root.mainloop()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_summary(result: dict) -> None:
    print(f"\n{'='*60}")
    print("PIPELINE CONCLUÍDO")
    print(f"{'='*60}")
    print(f"Documento final (MD):  {result.get('markdown')}")
    print(f"Documento final (PDF): {result.get('pdf') or 'não gerado'}")
    print(f"Entidades de domínio:  {result.get('entities', 0)}")
    print(f"Relacionamentos:       {result.get('relationships', 0)}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo de elicitação de requisitos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python pipeline.py --full                          # abre GUI de gravação, roda tudo
  python pipeline.py --from-audio reuniao.wav        # transcreve e continua
  python pipeline.py --from-transcript reuniao.txt   # identifica personas e continua
  python pipeline.py --from-json reuniao_personas.json  # gera SRS + documento final
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full", action="store_true",
                       help="Abre GUI de gravação e encadeia todos os agentes")
    group.add_argument("--from-audio", type=Path, metavar="AUDIO",
                       help="Começa a partir de um arquivo de áudio (.wav/.mp3/etc)")
    group.add_argument("--from-transcript", type=Path, metavar="TXT",
                       help="Começa a partir de uma transcrição .txt")
    group.add_argument("--from-json", type=Path, metavar="JSON",
                       help="Começa a partir do JSON de saída do Agent 2")
    args = parser.parse_args()

    if args.full:
        _full_pipeline()
    elif args.from_audio:
        _from_audio(args.from_audio)
    elif args.from_transcript:
        _from_transcript(args.from_transcript)
    elif args.from_json:
        _from_json(args.from_json)


if __name__ == "__main__":
    main()
