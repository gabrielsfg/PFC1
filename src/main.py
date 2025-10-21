from pathlib import Path
import typer
from rich import print
from rich.panel import Panel
from src.audio.utils import default_input_path, default_output_path, output_path_from_input
from src.audio.record import record_wav
from src.stt.transcribe import Transcriber

app = typer.Typer(help="Agente 1 – Escuta & Transcrição (Whisper/faster-whisper)")

@app.command()
def record_and_transcribe(
    seconds: float = typer.Option(10.0, help="Duração da gravação (s)"),
    model_size: str = typer.Option("small", help="tiny/base/small/medium/large-v3"),
    device: str = typer.Option("cpu", help="cpu ou cuda"),
    compute_type: str = typer.Option("int8", help="int8/int8_float16/float16/float32"),
    language: str = typer.Option(None, help="pt/en/... ou None p/ auto"),
    out_txt: Path = typer.Option(None, help="Caminho para salvar a transcrição .txt"),
):
    audio_path = default_input_path()
    record_wav(audio_path, seconds=seconds)

    transcriber = Transcriber(
        model_size=model_size,
        device=device,
        compute_type=compute_type,
        language=language
    )
    result = transcriber.transcribe_file(file)
    text = result["text"]

    out_txt = out_txt or output_path_from_input(file, "txt")
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_text(text, encoding="utf-8")
@app.command()
def transcribe_file(
    file: Path = typer.Argument(..., help="Caminho do arquivo de áudio (wav/mp3/flac)"),
    model_size: str = typer.Option("small", help="tiny/base/small/medium/large-v3"),
    device: str = typer.Option("cpu", help="cpu ou cuda"),
    compute_type: str = typer.Option("int8", help="int8/int8_float16/float16/float32"),
    language: str = typer.Option(None, help="pt/en/... ou None p/ auto"),
    out_txt: Path = typer.Option(None, help="Caminho para salvar a transcrição .txt"),
):
    transcriber = Transcriber(
        model_size=model_size,
        device=device,
        compute_type=compute_type,
        language=language
    )
    result = transcriber.transcribe_file(file)
    text = result["text"]

    out_txt = out_txt or default_output_path("txt")
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_text(text, encoding="utf-8")

    print(Panel.fit(f"[bold green]Transcrição concluída![/]\n\n[b]Idioma:[/] {result['language']} ({result['language_probability']:.2%})\n[b]Duração:[/] {result['duration']:.2f}s\n\n[b]Arquivo de áudio:[/] {file}\n[b]Transcrição salva em:[/] {out_txt}"))

if __name__ == "__main__":
    app()