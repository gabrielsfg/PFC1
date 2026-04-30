from pathlib import Path
import json
import sys
import threading
import typer
from rich import print
from rich.panel import Panel

from src.audio.utils import default_input_path, default_output_path, output_path_from_input
from src.audio.record import record_wav_continuous
from src.stt.transcribe import Transcriber

app = typer.Typer(help="Agente 1 – Gravação & Transcrição (Whisper)")

# Modelo fixo: medium — boa qualidade, roda em CPU sem configuração extra
MODEL_SIZE = "medium"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


def beep(freq=800, dur_ms=150):
    try:
        import winsound  # type: ignore
        winsound.Beep(freq, dur_ms)
    except Exception:
        sys.stdout.write("\a")
        sys.stdout.flush()


def _save_outputs(audio_path: Path, result: dict):
    out_txt = output_path_from_input(audio_path, "txt")
    out_json = output_path_from_input(audio_path, "json")
    out_txt.parent.mkdir(parents=True, exist_ok=True)

    out_txt.write_text(result["text"], encoding="utf-8")

    payload = {
        "audio_path": str(audio_path),
        "language": result["language"],
        "language_probability": result["language_probability"],
        "duration": result["duration"],
        "segments": result["segments"],
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_txt, out_json


def _transcribe(audio_path: Path):
    tr = Transcriber(model_size=MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, language=None)
    return tr.transcribe_file(audio_path)


# --------------------------------
# 1) GRAVAR ATÉ O USUÁRIO PARAR
# --------------------------------
@app.command("record")
def record():
    """Grava o microfone até você pressionar ENTER, depois transcreve."""
    audio_path = default_input_path()

    stop_event = threading.Event()

    print("[bold]Gravando...[/] Pressione [bold]ENTER[/] para parar.")
    beep()

    t = threading.Thread(
        target=record_wav_continuous,
        args=(audio_path, stop_event),
        daemon=True,
    )
    t.start()

    input()          # aguarda ENTER
    stop_event.set()
    t.join()
    beep(1000, 250)

    print("Transcrevendo... aguarde.")
    result = _transcribe(audio_path)
    out_txt, out_json = _save_outputs(audio_path, result)

    print(Panel.fit(
        f"[bold green]Concluído![/]\n\n"
        f"[b]Idioma:[/] {result['language']} ({result['language_probability']:.0%})\n"
        f"[b]Duração:[/] {result['duration']:.2f}s\n\n"
        f"[b]Áudio:[/] {audio_path}\n"
        f"[b]TXT:[/]   {out_txt}\n"
        f"[b]JSON:[/]  {out_json}"
    ))


# --------------------------------
# 2) TRANSCREVER ARQUIVO EXISTENTE
# --------------------------------
@app.command("transcribe-file")
def transcribe_file(
    file: Path = typer.Argument(..., help="Caminho do arquivo de áudio (wav/mp3/flac)"),
):
    """Transcreve um arquivo de áudio existente e salva TXT + JSON."""
    if not file.exists():
        print(f"[red]Arquivo não encontrado: {file}[/]")
        raise typer.Exit(1)

    print(f"Transcrevendo [b]{file.name}[/]... aguarde.")
    result = _transcribe(file)
    out_txt, out_json = _save_outputs(file, result)

    print(Panel.fit(
        f"[bold green]Transcrição concluída![/]\n\n"
        f"[b]Idioma:[/] {result['language']} ({result['language_probability']:.0%})\n"
        f"[b]Duração:[/] {result['duration']:.2f}s\n\n"
        f"[b]Arquivo:[/] {file}\n"
        f"[b]TXT:[/]   {out_txt}\n"
        f"[b]JSON:[/]  {out_json}"
    ))


if __name__ == "__main__":
    app()
