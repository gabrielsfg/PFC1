from pathlib import Path
import json
import time
import sys
import typer
from rich import print
from rich.panel import Panel

from src.audio.utils import default_input_path, default_output_path, output_path_from_input
from src.audio.record import record_wav
from src.stt.transcribe import Transcriber

app = typer.Typer(help="Agente 1 – Escuta & Transcrição (Whisper/faster-whisper)")

# =======================
# CONFIG DO MODO RÁPIDO
# =======================
SECONDS = 5            # tempo fixo de gravação
MODEL_SIZE = "small"   # tiny/base/small/medium/large-v3
DEVICE = "cpu"         # "cpu" ou "cuda"
COMPUTE_TYPE = "int8"  # int8/int8_float16/float16/float32
LANGUAGE = None        # None = detecção automática

def beep(freq=800, dur_ms=150):
    """Beep cross-platform: melhor no Windows; fallback nos demais."""
    try:
        import winsound  # type: ignore
        winsound.Beep(freq, dur_ms)
    except Exception:
        sys.stdout.write("\a")
        sys.stdout.flush()

def countdown(n=3):
    for i in range(n, 0, -1):
        print(f"Iniciando em {i}...")
        beep()
        time.sleep(1)

def _save_outputs(audio_path: Path, result: dict, out_txt: Path | None = None):
    out_txt = out_txt or output_path_from_input(audio_path, "txt")
    out_json = output_path_from_input(audio_path, "json")
    out_txt.parent.mkdir(parents=True, exist_ok=True)

    # Salva .txt
    out_txt.write_text(result["text"], encoding="utf-8")

    # Salva .json com metadados e segmentos
    payload = {
        "audio_path": str(audio_path),
        "language": result["language"],
        "language_probability": result["language_probability"],
        "duration": result["duration"],
        "segments": result["segments"],  # [{start, end, text}]
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_txt, out_json

# --------------------------------
# 1) MODO RÁPIDO (igual simple_run)
# --------------------------------
@app.command("quick")
def quick():
    """Grava SECONDS fixos, transcreve e salva TXT + JSON (sem flags)."""
    print("[0/3] Prepare-se. Faça silêncio por um instante.")
    countdown(3)

    audio_path = default_input_path()
    print(f"[1/3] Gravando {SECONDS}s do microfone...")
    record_wav(audio_path, seconds=SECONDS)
    beep(1000, 250)

    print("[2/3] Transcrevendo com faster-whisper...")
    tr = Transcriber(
        model_size=MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        language=LANGUAGE,
    )
    result = tr.transcribe_file(audio_path)

    out_txt, out_json = _save_outputs(audio_path, result)

    print(Panel.fit(
        f"[bold green]Concluído![/]\n\n"
        f"[b]Idioma:[/] {result['language']} ({result['language_probability']:.0%})\n"
        f"[b]Duração:[/] {result['duration']:.2f}s\n\n"
        f"[b]Áudio:[/] {audio_path}\n"
        f"[b]TXT:[/]   {out_txt}\n"
        f"[b]JSON:[/]  {out_json}"
    ))

@app.command("quick-seconds")
def quick_seconds(
    seconds: float = typer.Argument(5.0, help="Duração da gravação em segundos (1 a 120)"),
):
    """Igual ao 'quick', mas você escolhe os segundos como ARGUMENTO POSICIONAL."""
    # validação simples
    if seconds < 1:
        seconds = 1
    if seconds > 120:
        seconds = 120

    print("[0/3] Prepare-se. Faça silêncio por um instante.")
    countdown(3)

    audio_path = default_input_path()
    print(f"[1/3] Gravando {seconds:.2f}s do microfone...")
    record_wav(audio_path, seconds=seconds)
    beep(1000, 250)

    print("[2/3] Transcrevendo com faster-whisper...")
    tr = Transcriber(
        model_size=MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        language=LANGUAGE,
    )
    result = tr.transcribe_file(audio_path)

    out_txt, out_json = _save_outputs(audio_path, result)

    print(Panel.fit(
        f"[bold green]Concluído![/]\n\n"
        f"[b]Idioma:[/] {result['language']} ({result['language_probability']:.0%})\n"
        f"[b]Duração:[/] {result['duration']:.2f}s\n\n"
        f"[b]Áudio:[/] {audio_path}\n"
        f"[b]TXT:[/]   {out_txt}\n"
        f"[b]JSON:[/]  {out_json}"
    ))

@app.command("quick-config")
def quick_config(
    model_size: str = typer.Argument("small", help="tiny | base | small | medium | large-v3"),
    device: str = typer.Argument("cpu", help="cpu | cuda"),
    seconds: float = typer.Argument(5.0, help="Duração da gravação em segundos (1 a 120)"),
):
    """
    Grava 'seconds' segundos e transcreve escolhendo modelo e device como argumentos posicionais.
    Ex.: python -m src.main quick-config small cpu 8
         python -m src.main quick-config medium cuda 10
    """
    # normaliza entradas
    model_size = model_size.lower()
    device = device.lower()
    if seconds < 1: seconds = 1
    if seconds > 120: seconds = 120

    # compute_type automático (regra prática)
    compute_type = "float16" if device == "cuda" else "int8"

    print("[0/3] Prepare-se. Faça silêncio por um instante.")
    countdown(3)

    audio_path = default_input_path()
    print(f"[1/3] Gravando {seconds:.2f}s do microfone...")
    record_wav(audio_path, seconds=seconds)
    beep(1000, 250)

    print(f"[2/3] Transcrevendo com faster-whisper (model={model_size}, device={device}, compute={compute_type})...")
    tr = Transcriber(
        model_size=model_size,
        device=device,
        compute_type=compute_type,
        language=LANGUAGE,  # None = detecção automática
    )
    result = tr.transcribe_file(audio_path)
    out_txt, out_json = _save_outputs(audio_path, result)

    print(Panel.fit(
        f"[bold green]Concluído![/]\n\n"
        f"[b]Idioma:[/] {result['language']} ({result['language_probability']:.0%})\n"
        f"[b]Duração:[/] {result['duration']:.2f}s\n\n"
        f"[b]Áudio:[/] {audio_path}\n"
        f"[b]TXT:[/]   {out_txt}\n"
        f"[b]JSON:[/]  {out_json}\n"
        f"[b]Config usada:[/] model={model_size}, device={device}, compute={compute_type}"
    ))

# --------------------------------
# 2) TRANSCRITAR ARQUIVO EXISTENTE
# --------------------------------
@app.command("transcribe-file")
def transcribe_file(
    file: Path = typer.Argument(..., help="Caminho do arquivo de áudio (wav/mp3/flac)"),
):
    """Transcreve um arquivo existente e salva TXT + JSON."""
    tr = Transcriber(
        model_size=MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        language=LANGUAGE,
    )
    result = tr.transcribe_file(file)
    out_txt, out_json = _save_outputs(file, result, out_txt=default_output_path("txt"))

    print(Panel.fit(
        f"[bold green]Transcrição concluída![/]\n\n"
        f"[b]Idioma:[/] {result['language']} ({result['language_probability']:.0%})\n"
        f"[b]Duração:[/] {result['duration']:.2f}s\n\n"
        f"[b]Arquivo de áudio:[/] {file}\n"
        f"[b]TXT:[/]   {out_txt}\n"
        f"[b]JSON:[/]  {out_json}"
    ))

if __name__ == "__main__":
    app()
