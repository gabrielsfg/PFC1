# gui_app.py  — Passo 1: GUI simples para gravar e transcrever (rodar: python gui_app.py)
from pathlib import Path
import threading
import json
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Beep (Windows funciona melhor; fallback nos demais)
def beep(freq=800, dur_ms=150):
    try:
        import winsound
        winsound.Beep(freq, dur_ms)
    except Exception:
        sys.stdout.write("\a")
        sys.stdout.flush()

# ===== Imports do seu projeto =====
# Execute este arquivo na RAIZ do projeto (onde existe a pasta "src")
from src.audio.utils import default_input_path, output_path_from_input
from src.audio.record import record_wav
from src.stt.transcribe import Transcriber

# Configs padrão
MODEL_CHOICES = ["tiny", "base", "small", "medium", "large-v3"]
DEVICE_CHOICES = ["cpu", "cuda"]

def transcrever(model_size, device, seconds, export_txt, export_json, status_label, btn_run):
    try:
        # Validações simples
        try:
            seconds = float(seconds)
        except:
            raise ValueError("Informe um número de segundos válido.")
        if seconds < 1: seconds = 1.0
        if seconds > 600: seconds = 600.0  # limite alto por segurança

        # compute_type automático
        compute_type = "float16" if device == "cuda" else "int8"

        # 1) Gravação
        status_label.config(text=f"Gravando {seconds:.0f}s...")
        root.update_idletasks()
        beep()
        audio_path = default_input_path()
        record_wav(audio_path, seconds=seconds)
        beep(1000, 250)

        # 2) Transcrição
        status_label.config(text=f"Transcrevendo (model={model_size}, device={device})...")
        root.update_idletasks()
        tr = Transcriber(
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            language=None,   # auto-detecção
        )
        result = tr.transcribe_file(audio_path)

        # 3) Exportar
        saved_paths = []
        if export_txt:
            out_txt = output_path_from_input(audio_path, "txt")
            out_txt.parent.mkdir(parents=True, exist_ok=True)
            out_txt.write_text(result["text"], encoding="utf-8")
            saved_paths.append(str(out_txt))

        if export_json:
            out_json = output_path_from_input(audio_path, "json")
            out_json.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "audio_path": str(audio_path),
                "language": result["language"],
                "language_probability": result["language_probability"],
                "duration": result["duration"],
                "segments": result["segments"],
            }
            out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            saved_paths.append(str(out_json))

        # Feedback
        status_label.config(text="Concluído!")
        msg = (
            f"Idioma: {result['language']} ({result['language_probability']:.0%})\n"
            f"Duração: {result['duration']:.2f}s\n\n"
            f"Arquivos salvos:\n- " + "\n- ".join(saved_paths)
        )
        messagebox.showinfo("OK", msg)
    except Exception as e:
        status_label.config(text="Erro.")
        messagebox.showerror("Erro", str(e))
    finally:
        btn_run.config(state=tk.NORMAL)

def on_run(model_var, device_var, seconds_var, txt_var, json_var, status_label, btn_run):
    btn_run.config(state=tk.DISABLED)
    status_label.config(text="Preparando...")
    # roda em thread pra não travar a janela
    t = threading.Thread(
        target=transcrever,
        args=(
            model_var.get(),
            device_var.get(),
            seconds_var.get(),
            bool(txt_var.get()),
            bool(json_var.get()),
            status_label,
            btn_run,
        ),
        daemon=True,
    )
    t.start()

# === GUI ===
root = tk.Tk()
root.title("Agente de Transcrição (Whisper)")

frm = ttk.Frame(root, padding=16)
frm.grid(column=0, row=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Model
ttk.Label(frm, text="Modelo:").grid(column=0, row=0, sticky="w")
model_var = tk.StringVar(value="small")
cmb_model = ttk.Combobox(frm, textvariable=model_var, values=MODEL_CHOICES, state="readonly", width=12)
cmb_model.grid(column=1, row=0, sticky="we", padx=(8,0))

# Device
ttk.Label(frm, text="Device:").grid(column=0, row=1, sticky="w", pady=(8,0))
device_var = tk.StringVar(value="cpu")
cmb_device = ttk.Combobox(frm, textvariable=device_var, values=DEVICE_CHOICES, state="readonly", width=12)
cmb_device.grid(column=1, row=1, sticky="we", padx=(8,0), pady=(8,0))

# Seconds
ttk.Label(frm, text="Segundos:").grid(column=0, row=2, sticky="w", pady=(8,0))
seconds_var = tk.StringVar(value="5")
spn_seconds = ttk.Spinbox(frm, from_=1, to=600, textvariable=seconds_var, width=10)
spn_seconds.grid(column=1, row=2, sticky="w", padx=(8,0), pady=(8,0))

# Export options
txt_var = tk.IntVar(value=1)
json_var = tk.IntVar(value=1)
chk_txt = ttk.Checkbutton(frm, text="Exportar TXT", variable=txt_var)
chk_json = ttk.Checkbutton(frm, text="Exportar JSON", variable=json_var)
chk_txt.grid(column=0, row=3, sticky="w", pady=(8,0))
chk_json.grid(column=1, row=3, sticky="w", pady=(8,0))

# Run button
btn_run = ttk.Button(frm, text="Gravar e Transcrever", command=lambda: on_run(
    model_var, device_var, seconds_var, txt_var, json_var, status_label, btn_run
))
btn_run.grid(column=0, row=4, columnspan=2, sticky="we", pady=(12,0))

# Status
status_label = ttk.Label(frm, text="Pronto.", anchor="w")
status_label.grid(column=0, row=5, columnspan=2, sticky="we", pady=(8,0))

# Layout tweaks
for i in range(2):
    frm.columnconfigure(i, weight=1)

root.mainloop()
