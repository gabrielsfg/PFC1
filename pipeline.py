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

def _run_agent2(txt_path: Path) -> Path:
    """Runs Agent 2 on a transcription .txt and returns the output .json path."""
    import os
    from dotenv import load_dotenv
    load_dotenv(_ROOT / "agente-identificacao" / ".env")

    sys.path.insert(0, str(_ROOT / "agente-identificacao"))
    from src.persona_identifier import PersonaIdentifier  # type: ignore

    output_dir = os.getenv("OUTPUT_DIR", str(_ROOT / "agente-identificacao" / "data" / "output"))
    identifier = PersonaIdentifier(output_dir=output_dir)
    result = identifier.process_transcription(txt_path)
    if not result:
        raise RuntimeError("Agent 2 falhou ao processar a transcrição.")

    # Find the most recent output JSON for this stem
    out_dir = Path(output_dir)
    candidates = sorted(out_dir.glob(f"{txt_path.stem}_personas_*.json"), reverse=True)
    if not candidates:
        raise RuntimeError(f"Nenhum JSON de saída encontrado em {out_dir}")
    return candidates[0]


def _run_agent3(json_path: Path) -> Path:
    """Runs Agent 3 (SRS + use cases) and returns the output .md path."""
    import os
    from dotenv import load_dotenv
    load_dotenv(_ROOT / "agente-srs" / ".env")

    sys.path.insert(0, str(_ROOT / "agente-srs"))
    from src.srs_processor import SRSProcessor  # type: ignore

    output_dir = os.getenv("OUTPUT_DIR", str(_ROOT / "agente-srs" / "data" / "output"))
    processor = SRSProcessor(output_dir=output_dir)
    result = processor.process(json_path)
    if not result:
        raise RuntimeError("Agent 3 falhou.")
    return Path(result["markdown"])


def _run_agent4(json_path: Path, srs_md_path: Path) -> dict:
    """Runs Agent 4 (domain diagram + final document) and returns result dict."""
    import os
    from dotenv import load_dotenv
    load_dotenv(_ROOT / "agente-diagramas" / ".env")

    sys.path.insert(0, str(_ROOT / "agente-diagramas"))
    from src.diagrams_processor import DiagramsProcessor  # type: ignore

    output_dir = os.getenv("OUTPUT_DIR", str(_ROOT / "agente-diagramas" / "data" / "output"))
    processor = DiagramsProcessor(output_dir=output_dir)
    result = processor.process(json_path, srs_md_path=srs_md_path)
    if not result:
        raise RuntimeError("Agent 4 falhou.")
    return result


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
    from tkinter import ttk, messagebox
    import json as _json

    sys.path.insert(0, str(_ROOT / "agente-transcricao"))
    from src.audio.record import record_wav_continuous  # type: ignore
    from src.audio.utils import default_input_path, output_path_from_input  # type: ignore
    from src.stt.transcribe import Transcriber  # type: ignore

    stop_event: threading.Event | None = None
    audio_path_holder: list[Path] = []

    def beep(freq=800, dur_ms=150):
        try:
            import winsound
            winsound.Beep(freq, dur_ms)
        except Exception:
            sys.stdout.write("\a")
            sys.stdout.flush()

    def _pipeline_thread(audio_path: Path, status: ttk.Label):
        try:
            status.config(text="Transcrevendo...")
            root.update_idletasks()

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
            status.config(text="Identificando personas...")
            root.update_idletasks()

            json_path = _run_agent2(txt_path)

            status.config(text="Gerando SRS e casos de uso...")
            root.update_idletasks()
            srs_md = _run_agent3(json_path)

            status.config(text="Gerando diagrama de domínio e documento final...")
            root.update_idletasks()
            final = _run_agent4(json_path, srs_md_path=srs_md)

            status.config(text="Concluído!")
            messagebox.showinfo(
                "Pipeline concluído",
                f"Documento final:\n{final.get('pdf') or final.get('markdown')}\n\n"
                f"Entidades de domínio: {final.get('entities', 0)}\n"
                f"Relacionamentos: {final.get('relationships', 0)}",
            )
        except Exception as e:
            status.config(text="Erro no pipeline.")
            messagebox.showerror("Erro", str(e))
        finally:
            btn_start.config(state=tk.NORMAL)

    def on_start():
        nonlocal stop_event
        stop_event = threading.Event()
        audio_path = default_input_path()
        audio_path_holder.clear()
        audio_path_holder.append(audio_path)

        btn_start.config(state=tk.DISABLED)
        btn_stop.config(state=tk.NORMAL)
        status_label.config(text="Gravando... clique em Parar quando terminar.")
        beep()

        def record_then_pipeline():
            try:
                record_wav_continuous(audio_path, stop_event)
                beep(1000, 250)
                btn_stop.config(state=tk.DISABLED)
                _pipeline_thread(audio_path, status_label)
            except Exception as e:
                status_label.config(text="Erro na gravação.")
                messagebox.showerror("Erro", str(e))
                btn_start.config(state=tk.NORMAL)
                btn_stop.config(state=tk.DISABLED)

        threading.Thread(target=record_then_pipeline, daemon=True).start()

    def on_stop():
        if stop_event:
            btn_stop.config(state=tk.DISABLED)
            status_label.config(text="Encerrando gravação...")
            stop_event.set()

    root = tk.Tk()
    root.title("Pipeline de Elicitação de Requisitos")
    root.resizable(False, False)

    frm = ttk.Frame(root, padding=24)
    frm.grid(column=0, row=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Label(frm, text="Pipeline de Elicitação de Requisitos", font=("", 13, "bold")).grid(
        column=0, row=0, columnspan=2, pady=(0, 6)
    )
    ttk.Label(
        frm,
        text="Grava a reunião e gera automaticamente:\nSRS · Casos de Uso · Diagrama de Domínio · Documento Final",
        justify="center",
        foreground="#555",
    ).grid(column=0, row=1, columnspan=2, pady=(0, 18))

    btn_start = ttk.Button(frm, text="▶  Iniciar Gravação", command=on_start, width=22)
    btn_start.grid(column=0, row=2, padx=(0, 8), sticky="we")

    btn_stop = ttk.Button(frm, text="■  Parar Gravação", command=on_stop, width=22, state=tk.DISABLED)
    btn_stop.grid(column=1, row=2, sticky="we")

    status_label = ttk.Label(frm, text="Pronto.", anchor="center", foreground="#555")
    status_label.grid(column=0, row=3, columnspan=2, pady=(14, 0), sticky="we")

    for i in range(2):
        frm.columnconfigure(i, weight=1)

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
