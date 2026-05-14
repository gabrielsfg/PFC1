from pathlib import Path
import threading
import sounddevice as sd
import soundfile as sf
import numpy as np

DEFAULT_SR = 16000
DEFAULT_CHANNELS = 1


def record_wav_continuous(
    out_path: Path,
    stop_event: threading.Event,
    samplerate: int = DEFAULT_SR,
    channels: int = DEFAULT_CHANNELS,
) -> Path:
    """Grava áudio do microfone continuamente até stop_event ser sinalizado."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    chunks: list[np.ndarray] = []

    def callback(indata, frames, time, status):
        chunks.append(indata.copy())

    with sd.InputStream(
        samplerate=samplerate,
        channels=channels,
        dtype="float32",
        callback=callback,
    ):
        stop_event.wait()

    audio = np.concatenate(chunks, axis=0) if chunks else np.zeros((1, channels), dtype="float32")
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(str(out_path), audio, samplerate)
    return out_path
