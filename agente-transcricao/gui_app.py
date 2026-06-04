# gui_app.py — GUI de transcrição avulsa: gravar OU inserir arquivo (áudio/vídeo).
# Motor: Groq (com fallback para Whisper local). Gera apenas .txt/.json em data/output.
from pathlib import Path
import threading
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from src.audio.utils import default_input_path
from src.audio.record import record_wav_continuous
from src.stt import transcription_service
from src.stt.groq_transcriber import GroqUnavailableError

# Estado global
_stop_event: threading.Event | None = None
_selected_file: Path | None = None


def beep(freq=800, dur_ms=150):
    try:
        import winsound
        winsound.Beep(freq, dur_ms)
    except Exception:
        sys.stdout.write("\a")
        sys.stdout.flush()


def _ask_fallback(msg: str) -> bool:
    """Pergunta (na main thread) se deve usar o Whisper local."""
    holder = {}
    done = threading.Event()

    def ask():
        holder["yes"] = messagebox.askyesno(
            "Groq indisponível",
            f"{msg}\n\nDeseja transcrever com o Whisper local (mais rápido)?",
        )
        done.set()

    root.after(0, ask)
    done.wait()
    return holder.get("yes", False)


def _process(input_path: Path):
    """Transcreve (Groq → fallback local) e salva .txt/.json."""
    try:
        status_label.config(text="Transcrevendo (Groq)... aguarde.")
        root.update_idletasks()
        try:
            result = transcription_service.transcribe_with_groq(input_path)
        except GroqUnavailableError as e:
            if not _ask_fallback(str(e)):
                status_label.config(text="Transcrição cancelada.")
                return
            status_label.config(text="Usando Whisper local (mais rápido)...")
            root.update_idletasks()
            result = transcription_service.transcribe_local_fast(input_path)

        out_txt, out_json = transcription_service.save_transcription(input_path, result)

        status_label.config(text="Pronto.")
        messagebox.showinfo(
            "Transcrição concluída",
            f"Idioma: {result.get('language')}\n"
            f"Duração: {float(result.get('duration') or 0):.2f}s\n\n"
            f"TXT:  {out_txt}\n"
            f"JSON: {out_json}",
        )
    except Exception as e:
        status_label.config(text="Erro na transcrição.")
        messagebox.showerror("Erro", str(e))
    finally:
        _reset_controls()


def _disable_controls():
    btn_start.config(state=tk.DISABLED)
    btn_file.config(state=tk.DISABLED)
    btn_process.config(state=tk.DISABLED)


def _reset_controls():
    btn_start.config(state=tk.NORMAL)
    btn_file.config(state=tk.NORMAL)
    btn_process.config(state=(tk.NORMAL if _selected_file else tk.DISABLED))
    btn_stop.config(state=tk.DISABLED)


def _run_recording(stop_event: threading.Event, audio_path: Path):
    try:
        record_wav_continuous(audio_path, stop_event)
        beep(1000, 250)
        btn_stop.config(state=tk.DISABLED)
        _process(audio_path)
    except Exception as e:
        status_label.config(text="Erro na gravação.")
        messagebox.showerror("Erro", str(e))
        _reset_controls()


def on_start():
    global _stop_event
    _stop_event = threading.Event()
    audio_path = default_input_path()

    _disable_controls()
    btn_stop.config(state=tk.NORMAL)
    status_label.config(text="Gravando... clique em Parar quando terminar.")
    beep()

    threading.Thread(
        target=_run_recording, args=(_stop_event, audio_path), daemon=True
    ).start()


def on_stop():
    global _stop_event
    if _stop_event:
        btn_stop.config(state=tk.DISABLED)
        status_label.config(text="Encerrando gravação...")
        _stop_event.set()


def on_select_file():
    global _selected_file
    path = filedialog.askopenfilename(
        title="Selecionar arquivo de áudio ou vídeo",
        filetypes=[
            ("Áudio/Vídeo", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.mp4 *.mkv *.mov *.avi *.webm"),
            ("Todos os arquivos", "*.*"),
        ],
    )
    if path:
        _selected_file = Path(path)
        file_label.config(text=f"arquivo: {_selected_file.name}")
        btn_process.config(state=tk.NORMAL)


def on_start_processing():
    if not _selected_file:
        return
    _disable_controls()
    status_label.config(text="Processando arquivo...")
    threading.Thread(target=lambda: _process(_selected_file), daemon=True).start()


# === GUI ===
root = tk.Tk()
root.title("Agente de Transcrição")
root.resizable(False, False)

frm = ttk.Frame(root, padding=20)
frm.grid(column=0, row=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

ttk.Label(frm, text="Agente de Transcrição de Reuniões", font=("", 12, "bold")).grid(
    column=0, row=0, columnspan=2, pady=(0, 12)
)

ttk.Label(frm, text="── Gravar reunião ──", foreground="#777").grid(
    column=0, row=1, columnspan=2, pady=(0, 4)
)
btn_start = ttk.Button(frm, text="▶  Iniciar Gravação", command=on_start, width=22)
btn_start.grid(column=0, row=2, padx=(0, 8), sticky="we")
btn_stop = ttk.Button(frm, text="■  Parar Gravação", command=on_stop, width=22, state=tk.DISABLED)
btn_stop.grid(column=1, row=2, sticky="we")

ttk.Label(frm, text="── Ou inserir arquivo (áudio/vídeo) ──", foreground="#777").grid(
    column=0, row=3, columnspan=2, pady=(14, 4)
)
btn_file = ttk.Button(frm, text="📁  Selecionar arquivo", command=on_select_file, width=22)
btn_file.grid(column=0, row=4, padx=(0, 8), sticky="we")
btn_process = ttk.Button(frm, text="▶  Iniciar Processamento", command=on_start_processing,
                         width=22, state=tk.DISABLED)
btn_process.grid(column=1, row=4, sticky="we")
file_label = ttk.Label(frm, text="arquivo: (nenhum)", foreground="#555")
file_label.grid(column=0, row=5, columnspan=2, pady=(6, 0), sticky="we")

ttk.Label(frm, text="Motor: Groq (fallback: Whisper local)", foreground="#999").grid(
    column=0, row=6, columnspan=2, pady=(12, 0)
)
status_label = ttk.Label(frm, text="Pronto.", anchor="center", foreground="#555")
status_label.grid(column=0, row=7, columnspan=2, pady=(8, 0), sticky="we")

for i in range(2):
    frm.columnconfigure(i, weight=1)

root.mainloop()
