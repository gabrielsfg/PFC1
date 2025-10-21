import argparse
from pathlib import Path
from src.stt.transcribe import Transcriber
from src.audio.utils import output_path_from_input

def main():
    p = argparse.ArgumentParser(description="Transcrever arquivo de áudio (bypass Typer)")
    p.add_argument("file", type=Path, help="Caminho do arquivo (wav/mp3/m4a/flac/ogg/aac/opus)")
    p.add_argument("--model-size", default="small", choices=["tiny","base","small","medium","large-v3"])
    p.add_argument("--device", default="cpu", choices=["cpu","cuda"])
    p.add_argument("--compute-type", default="int8", choices=["int8","int8_float16","float16","float32"])
    p.add_argument("--language", default=None, help="pt, en, es... (None = auto)")
    args = p.parse_args()

    tr = Transcriber(
        model_size=args.model_size,
        device=args.device,
        compute_type=args.compute_type,
        language=args.language
    )
    result = tr.transcribe_file(args.file)
    out_txt = output_path_from_input(args.file, "txt")
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_text(result["text"], encoding="utf-8")

    print(f"OK! idioma={result['language']} "
          f"({result['language_probability']:.2%}), duracao={result['duration']:.2f}s\n"
          f"saida: {out_txt}")

if __name__ == "__main__":
    main()
