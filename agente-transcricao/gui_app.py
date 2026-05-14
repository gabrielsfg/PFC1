# gui_app.py  — GUI com gravação contínua (clica pra gravar, clica pra parar)
from pathlib import Path
import threading
import json
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from src.audio.utils import default_input_path, output_path_from_input
from src.audio.record import record_wav_continuous
from src.stt.transcribe import Transcriber

# Modelo fixo: medium oferece boa qualidade sem exigir GPU
MODEL_SIZE = "medium"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# Estado global da gravação
_stop_event: threading.Event | None = None
_audio_path: Path | None = None


def beep(freq=800, dur_ms=150):
    try:
        import winsound
        winsound.Beep(freq, dur_ms)
    except Exception:
        sys.stdout.write("\a")
        sys.stdout.flush()


def _run_transcription(audio_path: Path, status_label: ttk.Label, btn_start: ttk.Button):
    """Executa a transcrição em thread separada após a gravação."""
    try:
        status_label.config(text="Transcrevendo... aguarde.")
        root.update_idletasks()

        tr = Transcriber(
            model_size=MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            language=None,
        )
        result = tr.transcribe_file(audio_path)

        # Salva TXT
        out_txt = output_path_from_input(audio_path, "txt")
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_text(result["text"], encoding="utf-8")

        # Salva JSON
        out_json = output_path_from_input(audio_path, "json")
        payload = {
            "audio_path": str(audio_path),
            "language": result["language"],
            "language_probability": result["language_probability"],
            "duration": result["duration"],
            "segments": result["segments"],
        }
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        status_label.config(text="Pronto.")
        messagebox.showinfo(
            "Transcrição concluída",
            f"Idioma detectado: {result['language']} ({result['language_probability']:.0%})\n"
            f"Duração: {result['duration']:.2f}s\n\n"
            f"TXT:  {out_txt}\n"
            f"JSON: {out_json}",
        )
    except Exception as e:
        status_label.config(text="Erro na transcrição.")
        messagebox.showerror("Erro", str(e))
    finally:
        btn_start.config(state=tk.NORMAL)


def _run_recording(stop_event: threading.Event, audio_path: Path,
                   status_label: ttk.Label, btn_start: ttk.Button, btn_stop: ttk.Button):
    """Grava até stop_event ser sinalizado, depois dispara transcrição."""
    try:
        record_wav_continuous(audio_path, stop_event)
        beep(1000, 250)
        btn_stop.config(state=tk.DISABLED)
        _run_transcription(audio_path, status_label, btn_start)
    except Exception as e:
        status_label.config(text="Erro na gravação.")
        messagebox.showerror("Erro", str(e))
        btn_start.config(state=tk.NORMAL)
        btn_stop.config(state=tk.DISABLED)


def on_start(status_label: ttk.Label, btn_start: ttk.Button, btn_stop: ttk.Button):
    global _stop_event, _audio_path

    _stop_event = threading.Event()
    _audio_path = default_input_path()

    btn_start.config(state=tk.DISABLED)
    btn_stop.config(state=tk.NORMAL)
    status_label.config(text="Gravando... clique em Parar quando terminar.")
    beep()

    t = threading.Thread(
        target=_run_recording,
        args=(_stop_event, _audio_path, status_label, btn_start, btn_stop),
        daemon=True,
    )
    t.start()


def on_stop(status_label: ttk.Label, btn_stop: ttk.Button):
    global _stop_event
    if _stop_event:
        btn_stop.config(state=tk.DISABLED)
        status_label.config(text="Encerrando gravação...")
        _stop_event.set()


# === GUI ===
root = tk.Tk()
root.title("Agente de Transcrição")
root.resizable(False, False)

frm = ttk.Frame(root, padding=20)
frm.grid(column=0, row=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

ttk.Label(frm, text="Agente de Transcrição de Reuniões", font=("", 12, "bold")).grid(
    column=0, row=0, columnspan=2, pady=(0, 16)
)

btn_start = ttk.Button(
    frm, text="▶  Iniciar Gravação",
    command=lambda: on_start(status_label, btn_start, btn_stop),
    width=22,
)
btn_start.grid(column=0, row=1, padx=(0, 8), sticky="we")

btn_stop = ttk.Button(
    frm, text="■  Parar Gravação",
    command=lambda: on_stop(status_label, btn_stop),
    width=22,
    state=tk.DISABLED,
)
btn_stop.grid(column=1, row=1, sticky="we")

status_label = ttk.Label(frm, text="Pronto.", anchor="center", foreground="#555")
status_label.grid(column=0, row=2, columnspan=2, pady=(14, 0), sticky="we")

for i in range(2):
    frm.columnconfigure(i, weight=1)

root.mainloop()
