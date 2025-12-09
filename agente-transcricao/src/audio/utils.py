from datetime import datetime
from pathlib import Path

def default_input_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("data/input") / f"rec_{ts}.wav"

def default_output_path(suffix: str = "txt") -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("data/output") / f"transcript_{ts}.{suffix}"

def output_path_from_input(input_path: Path, suffix: str = "txt") -> Path:
    """
    Gera data/output/<nome_base>.<suffix> a partir do arquivo de entrada.
    Ex.: data/input/reuniao.m4a -> data/output/reuniao.txt
    """
    base = Path(input_path).stem 
    return Path("data/output") / f"{base}.{suffix}"
