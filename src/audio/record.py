from pathlib import Path
import sounddevice as sd
import soundfile as sf
import numpy as np

DEFAULT_SR = 16000
DEFAULT_CHANNELS = 1

def record_wav(
    out_path: Path,
    seconds: float = 10.0,
    samplerate: int = DEFAULT_SR,
    channels: int = DEFAULT_CHANNELS,
):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Gravando {seconds}s @ {samplerate} Hz, {channels} canal(is)...")
    audio = sd.rec(
        int(seconds * samplerate),
        samplerate=samplerate,
        channels=channels,
        dtype="float32",
        blocking=True,
    )
    sd.wait()
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(str(out_path), audio, samplerate)
    print(f"[Arquivo salvo em: {out_path.resolve()}")
    return out_path
