"""
Pipeline multi-agente de elicitação de requisitos.

Modos de entrada (mutuamente exclusivos):
  --full            Abre a GUI de gravação e encadeia todos os agentes ao parar
  --from-audio      Começa a partir de um arquivo de áudio existente (pula gravação)
  --from-transcript Começa a partir de um .txt de transcrição (pula Agents 1)
  --from-json       Começa a partir do JSON do Agent 2 (pula Agents 1 e 2)

Em todos os casos os agentes 3 e 4 são executados sequencialmente ao final.
"""

import argparse
import glob as _glob
import os
import sys
import threading
import time
from pathlib import Path


def _format_duration(seconds: float) -> str:
    """Human-readable elapsed time, e.g. '3m 12s' or '8.4s'."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m {secs:02d}s"

# ── resolve project root so each agent package is importable ─────────────────
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))


# ── Agent runners ─────────────────────────────────────────────────────────────

def _venv_python(agent_dir: str) -> str:
    """Returns the Python to run a given agent.

    Prefers the agent's own venv (cross-platform), falling back to the current
    interpreter when that venv doesn't exist.
    """
    base = _ROOT / agent_dir / ".venv"
    candidate = base / "Scripts" / "python.exe" if os.name == "nt" else base / "bin" / "python"
    return str(candidate) if candidate.exists() else sys.executable


def _fmt_label(fmt: str) -> str:
    return {"ieee": "IEEE 830", "empresa": "Empresa (SGG)", "valori": "Valori"}.get(fmt, fmt)


def _write_acronyms_file(acronyms: str) -> Path | None:
    """Persists the acronym table next to the outputs so Agent 3 can read it.

    Multi-line text is awkward to pass as a CLI argument, so it travels as a file.
    Returns None when the user declared no acronyms.
    """
    text = (acronyms or "").strip()
    if not text:
        return None
    out_dir = _ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "siglas.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _apply_acronyms(txt_path: Path, acronyms: str, log=print) -> Path:
    """Rewrites mis-transcribed acronyms in the transcription file, in place.

    Whisper garbles domain acronyms it has never heard (the "HIPOF" for "IPOF"
    case). Fixing the .txt before Agent 2 stops the error from propagating
    through the whole pipeline. Returns the path of the corrected file.
    """
    text = (acronyms or "").strip()
    if not text:
        return txt_path

    sys.path.insert(0, str(_ROOT / "agente-transcricao"))
    from src.stt.acronym_corrector import parse_acronyms, correct_transcription  # type: ignore

    parsed = parse_acronyms(text)
    if not parsed:
        return txt_path

    original = txt_path.read_text(encoding="utf-8")
    corrected, report = correct_transcription(original, parsed)
    if not report:
        log(f"Siglas: nenhuma correção necessária ({len(parsed)} sigla(s) declarada(s)).")
        return txt_path

    # Keep the raw Whisper output for traceability (the TCC compares WER/CER).
    backup = txt_path.with_name(f"{txt_path.stem}_original{txt_path.suffix}")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")
    txt_path.write_text(corrected, encoding="utf-8")

    total = sum(report.values())
    log(f"Siglas: {total} correção(ões) aplicada(s) na transcrição.")
    for change, count in sorted(report.items(), key=lambda kv: -kv[1]):
        log(f"   • {change} ({count}x)")
    return txt_path


def _run_agent2(txt_path: Path) -> Path:
    import subprocess
    python = _venv_python("agente-identificacao")
    output_dir = str(_ROOT / "agente-identificacao" / "data" / "output")
    result = subprocess.run(
        [python, "main.py", "--file", str(txt_path.resolve()), "--output-dir", output_dir],
        cwd=str(_ROOT / "agente-identificacao"),
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Agent 2 falhou.")
    out_dir = Path(output_dir)
    # glob.escape the stem: meeting filenames contain "[ ]" which are glob wildcards.
    stem = _glob.escape(txt_path.stem)
    candidates = sorted(out_dir.glob(f"{stem}_personas_*.json"), reverse=True)
    if not candidates:
        raise RuntimeError(f"Nenhum JSON encontrado em {out_dir}")
    return candidates[0]


def _run_agent3(json_path: Path, fmt: str = "ieee", project_name: str = "",
                acronyms: str = "") -> Path:
    import subprocess
    import time as _time
    python = _venv_python("agente-srs")
    output_dir = str(_ROOT / "agente-srs" / "data" / "output")
    started = _time.time()
    cmd = [python, "main.py", "--file", str(json_path.resolve()), "--format", fmt]
    if project_name:
        cmd += ["--project-name", project_name]
    acronyms_file = _write_acronyms_file(acronyms)
    if acronyms_file:
        cmd += ["--acronyms-file", str(acronyms_file.resolve())]
    result = subprocess.run(cmd, cwd=str(_ROOT / "agente-srs"), capture_output=False)
    if result.returncode != 0:
        raise RuntimeError("Agent 3 falhou.")
    out_dir = Path(output_dir)
    # The output filename depends on the project name, so discover by newest mtime
    # (a .md written by this run, i.e. modified at/after we started the subprocess).
    mds = [p for p in out_dir.glob("*.md") if p.stat().st_mtime >= started - 1]
    if not mds:
        mds = list(out_dir.glob("*.md"))
    if not mds:
        raise RuntimeError(f"Nenhum .md encontrado em {out_dir}")
    return max(mds, key=lambda p: p.stat().st_mtime)


def _run_agent4(json_path: Path, srs_md_path: Path) -> dict:
    import subprocess
    python = _venv_python("agente-diagramas")
    output_dir = str(_ROOT / "agente-diagramas" / "data" / "output")
    result = subprocess.run(
        [python, "main.py", "--file", str(json_path.resolve()), "--srs-md", str(srs_md_path.resolve())],
        cwd=str(_ROOT / "agente-diagramas"),
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Agent 4 falhou.")
    out_dir = Path(output_dir)
    pdf = sorted(out_dir.glob("*.pdf"), reverse=True)
    md = sorted(out_dir.glob("*.md"), reverse=True)
    return {
        "pdf": str(pdf[0]) if pdf else None,
        "markdown": str(md[0]) if md else None,
        "entities": 0,
        "relationships": 0,
    }


def _run_agents3_and_4(json_path: Path, fmt: str = "ieee", project_name: str = "",
                       acronyms: str = "") -> dict:
    print(f"\n{'='*60}")
    print(f"AGENT 3 — Documento ({_fmt_label(fmt)})")
    print(f"{'='*60}")
    srs_md = _run_agent3(json_path, fmt, project_name=project_name, acronyms=acronyms)

    if fmt != "ieee":
        # empresa/valori have no diagrams: Agent 3's output is the final document.
        pdf = srs_md.with_suffix(".pdf")
        return {
            "markdown": str(srs_md),
            "pdf": str(pdf) if pdf.exists() else None,
            "entities": 0,
            "relationships": 0,
        }

    print(f"\n{'='*60}")
    print("AGENT 4 — Diagrama de Domínio + Documento Final")
    print(f"{'='*60}")
    final = _run_agent4(json_path, srs_md_path=srs_md)
    return final


# ── Entry points per starting stage ──────────────────────────────────────────

def _from_transcript(txt_path: Path, fmt: str = "ieee", project_name: str = "",
                     acronyms: str = "") -> None:
    # Fix garbled acronyms before Agent 2, so the error does not propagate.
    txt_path = _apply_acronyms(txt_path, acronyms)
    print(f"\n{'='*60}")
    print("AGENT 2 — Identificação de Personas")
    print(f"{'='*60}")
    json_path = _run_agent2(txt_path)
    result = _run_agents3_and_4(json_path, fmt, project_name=project_name, acronyms=acronyms)
    _print_summary(result)


def _from_json(json_path: Path, fmt: str = "ieee", project_name: str = "",
               acronyms: str = "") -> None:
    result = _run_agents3_and_4(json_path, fmt, project_name=project_name, acronyms=acronyms)
    _print_summary(result)


def _from_audio(audio_path: Path, fmt: str = "ieee", project_name: str = "",
                acronyms: str = "") -> None:
    sys.path.insert(0, str(_ROOT / "agente-transcricao"))
    from src.stt import transcription_service  # type: ignore
    from src.stt.groq_transcriber import GroqUnavailableError  # type: ignore

    print(f"\n{'='*60}")
    print("AGENT 1 — Transcrição (Groq)")
    print(f"{'='*60}")
    print(f"Transcrevendo: {audio_path.name}...")

    try:
        result = transcription_service.transcribe_with_groq(audio_path)
    except GroqUnavailableError as e:
        print(f"Groq indisponível ({e}). Usando Whisper local rápido...")
        result = transcription_service.transcribe_local_fast(audio_path)

    txt_path, _ = transcription_service.save_transcription(audio_path, result)
    print(f"Transcrição salva em: {txt_path}")
    _from_transcript(txt_path, fmt, project_name=project_name, acronyms=acronyms)


def _full_pipeline(initial_fmt: str = "ieee") -> None:
    """Single executor GUI: record OR insert a file, then run the whole pipeline.

    Transcription uses Groq (with a fast local fallback). A format selector chooses
    the output document (IEEE 830 vs empresa/SGG); the empresa format skips Agent 4.
    """
    import tkinter as tk
    from tkinter import messagebox, filedialog, ttk
    import time

    sys.path.insert(0, str(_ROOT / "agente-transcricao"))
    from src.audio.record import record_wav_continuous  # type: ignore
    from src.audio.utils import default_input_path  # type: ignore
    from src.stt import transcription_service  # type: ignore
    from src.stt.groq_transcriber import GroqUnavailableError  # type: ignore

    stop_event = None
    selected_file = [None]
    _recording_start = [0.0]
    _timer_active = [False]

    def beep(freq=800, dur_ms=150):
        try:
            import winsound
            winsound.Beep(freq, dur_ms)
        except Exception:
            sys.stdout.write("\a")
            sys.stdout.flush()

    def set_status(text, color="#aaaaaa"):
        status_label.config(text=text, fg=color)
        root.update()

    def set_phase(step, total, description):
        phase_label.config(text=f"Etapa {step}/{total}: {description}")
        root.update()

    # ── Thread-safe UI helpers (worker thread schedules onto the Tk main loop) ──
    def _ui(fn):
        root.after(0, fn)

    def set_bar(pct):
        """Set the progress bar to a determinate percentage [0, 100]."""
        def f():
            progress.stop()
            progress.config(mode="determinate")
            prog_var.set(max(0, min(100, pct)))
        _ui(f)

    def pulse(on=True):
        """Switch the bar to an animated (indeterminate) state for unmeasurable steps."""
        def f():
            if on:
                progress.config(mode="indeterminate")
                progress.start(14)
            else:
                progress.stop()
                progress.config(mode="determinate")
        _ui(f)

    def ui_status(text, color="#ffaa00"):
        _ui(lambda: status_label.config(text=text, fg=color))

    def ui_phase(text):
        _ui(lambda: phase_label.config(text=text))

    def log(msg):
        def f():
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, msg + "\n")
            log_text.see(tk.END)
            log_text.config(state=tk.DISABLED)
        _ui(f)

    def _tick_timer():
        if _timer_active[0]:
            elapsed = int(time.time() - _recording_start[0])
            m, s = divmod(elapsed, 60)
            timer_label.config(text=f"Gravando: {m:02d}:{s:02d}")
            root.after(1000, _tick_timer)
        else:
            timer_label.config(text="")

    def _ask_fallback(msg):
        """Ask (on the main thread) whether to fall back to local Whisper."""
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

    def _disable_controls():
        btn_start.config(state=tk.DISABLED)
        btn_file.config(state=tk.DISABLED)
        btn_process.config(state=tk.DISABLED)

    def _reset_controls():
        btn_start.config(state=tk.NORMAL)
        btn_file.config(state=tk.NORMAL)
        btn_process.config(state=tk.NORMAL if selected_file[0] else tk.DISABLED)
        btn_stop.config(state=tk.DISABLED)

    def _process(input_path):
        fmt = format_var.get()
        # Read the widgets once, here on entry: _process runs on a worker thread.
        acronyms = get_acronyms()
        project_name = project_name_var.get().strip()
        # Overall progress slices (start%, end%) per pipeline stage.
        if fmt == "ieee":
            total = 4
            slices = {"trans": (0, 45), "agent2": (45, 60), "agent3": (60, 82), "agent4": (82, 100)}
        else:
            total = 3
            slices = {"trans": (0, 55), "agent2": (55, 78), "agent3": (78, 100)}
        t0 = time.time()
        try:
            # ── Stage 1: transcription (real % for conversion + chunks) ──
            ui_phase(f"Etapa 1/{total}: Transcrição (Groq)")
            log("▶ Iniciando transcrição (Groq)…")
            set_bar(0)
            lo, hi = slices["trans"]

            def on_trans(frac, msg):
                ui_status(msg)
                if frac is None:
                    pulse(True)
                else:
                    set_bar(lo + (hi - lo) * frac)

            try:
                result = transcription_service.transcribe_with_groq(input_path, on_progress=on_trans)
            except GroqUnavailableError as e:
                pulse(False)
                log(f"⚠ Erro do Groq: {e}")  # full message stays visible in the log
                if not _ask_fallback(str(e)):
                    raise RuntimeError("Transcrição cancelada (Groq indisponível).")
                log("⚠ Groq indisponível — usando Whisper local…")
                ui_status("Usando Whisper local (mais rápido)…")
                result = transcription_service.transcribe_local_fast(input_path, on_progress=on_trans)
            pulse(False)
            set_bar(hi)
            txt_path, _ = transcription_service.save_transcription(input_path, result)
            log("✔ Transcrição concluída.")

            # Fix garbled acronyms now, before Agent 2 — otherwise the error
            # propagates into every downstream document.
            if acronyms:
                ui_status("Corrigindo siglas na transcrição…")
                txt_path = _apply_acronyms(txt_path, acronyms, log=log)

            # ── Stage 2: persona identification (LLM subprocess → animated bar) ──
            ui_phase(f"Etapa 2/{total}: Identificando personas e histórias")
            log("▶ Identificando personas e user stories…")
            ui_status("Analisando a transcrição com IA…")
            set_bar(slices["agent2"][0])
            pulse(True)
            json_path = _run_agent2(txt_path)
            pulse(False)
            set_bar(slices["agent2"][1])
            log("✔ Personas e histórias identificadas.")

            # ── Stage 3: document generation ──
            ui_phase(f"Etapa 3/{total}: Gerando documento ({_fmt_label(fmt)})")
            log(f"▶ Gerando documento ({_fmt_label(fmt)})…")
            ui_status("Estruturando os requisitos…")
            set_bar(slices["agent3"][0])
            pulse(True)
            srs_md = _run_agent3(json_path, fmt, project_name=project_name, acronyms=acronyms)
            pulse(False)
            set_bar(slices["agent3"][1])
            log("✔ Documento gerado.")

            if fmt == "ieee":
                # ── Stage 4: domain diagram + final document ──
                ui_phase(f"Etapa 4/{total}: Diagrama de domínio + documento final")
                log("▶ Gerando diagrama de domínio e documento final…")
                ui_status("Finalizando…")
                set_bar(slices["agent4"][0])
                pulse(True)
                final = _run_agent4(json_path, srs_md_path=srs_md)
                pulse(False)
                log("✔ Documento final gerado.")
            else:
                pdf = srs_md.with_suffix(".pdf")
                final = {"markdown": str(srs_md), "pdf": str(pdf) if pdf.exists() else None}
            set_bar(100)

            doc = final.get('pdf') or final.get('markdown') or ''
            doc_path = Path(doc) if doc else None
            doc_name = doc_path.name if doc_path else "ver pasta de saída"
            doc_dir = str(doc_path.parent) if doc_path else ""

            elapsed = _format_duration(time.time() - t0)
            print(f"\nTempo total de execução: {elapsed}\n")  # to the terminal
            log(f"✅ Pipeline concluído com sucesso! (tempo: {elapsed})")
            ui_phase(f"Pipeline concluído em {elapsed}!")
            ui_status("", "#4CAF50")
            _ui(lambda: result_label.config(
                text=f"Arquivo: {doc_name}\nPasta: {doc_dir}", fg="#4CAF50"))
        except Exception as e:
            err = str(e)  # capture before the except scope clears `e`
            elapsed = _format_duration(time.time() - t0)
            print(f"\nFalhou após {elapsed}.\n")  # to the terminal
            pulse(False)
            log(f"✖ Erro após {elapsed}: {err}")
            ui_phase("Erro no pipeline.")
            ui_status(err, "#f44336")
            _ui(lambda: messagebox.showerror("Erro", err))
        finally:
            _timer_active[0] = False
            _reset_controls()

    def on_start():
        nonlocal stop_event
        stop_event = threading.Event()
        audio_path = default_input_path()

        _disable_controls()
        btn_stop.config(state=tk.NORMAL)
        phase_label.config(text="Gravando...")
        set_status("Clique em Parar quando terminar.", "#aaaaaa")
        _recording_start[0] = time.time()
        _timer_active[0] = True
        _tick_timer()
        beep()

        def record_then_process():
            try:
                record_wav_continuous(audio_path, stop_event)
                beep(1000, 250)
                _timer_active[0] = False
                btn_stop.config(state=tk.DISABLED)
                _process(audio_path)
            except Exception as e:
                _timer_active[0] = False
                set_status(f"Erro na gravação: {e}", "#f44336")
                _reset_controls()

        threading.Thread(target=record_then_process, daemon=True).start()

    def on_stop():
        if stop_event:
            btn_stop.config(state=tk.DISABLED)
            phase_label.config(text="Encerrando gravação...")
            stop_event.set()

    def on_select_file():
        path = filedialog.askopenfilename(
            title="Selecionar arquivo de áudio ou vídeo",
            filetypes=[
                ("Áudio/Vídeo", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.mp4 *.mkv *.mov *.avi *.webm"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if path:
            selected_file[0] = path
            file_label.config(text=f"arquivo: {Path(path).name}")
            btn_process.config(state=tk.NORMAL)

    def on_start_processing():
        if not selected_file[0]:
            return
        _disable_controls()
        phase_label.config(text="Processando arquivo...")
        threading.Thread(target=lambda: _process(Path(selected_file[0])), daemon=True).start()

    # === GUI layout ===
    root = tk.Tk()
    root.title("Pipeline de Elicitação de Requisitos")
    root.geometry("560x870")
    root.resizable(False, False)
    root.configure(bg="#2b2b2b")

    # Dark-themed determinate/indeterminate progress bar.
    style = ttk.Style(root)
    try:
        style.theme_use("default")
    except tk.TclError:
        pass
    style.configure("Pipe.Horizontal.TProgressbar", troughcolor="#1f1f1f",
                    background="#4CAF50", bordercolor="#1f1f1f",
                    lightcolor="#4CAF50", darkcolor="#4CAF50")

    tk.Label(root, text="Pipeline de Elicitação de Requisitos", font=("Helvetica", 14, "bold"),
             bg="#2b2b2b", fg="white").pack(pady=(16, 2))
    tk.Label(root, text="Gera: SRS · Casos de Uso · Diagrama · Documento Final",
             font=("Helvetica", 9), bg="#2b2b2b", fg="#aaaaaa").pack(pady=(0, 10))

    # Format selector
    format_var = tk.StringVar(value=initial_fmt if initial_fmt in ("ieee", "empresa") else "ieee")
    fmt_frame = tk.Frame(root, bg="#2b2b2b")
    fmt_frame.pack(pady=(0, 6))
    tk.Label(fmt_frame, text="Formato do documento:", font=("Helvetica", 10, "bold"),
             bg="#2b2b2b", fg="white").pack(anchor="w")
    tk.Radiobutton(fmt_frame, text="SRS — IEEE 830", variable=format_var, value="ieee",
                   bg="#2b2b2b", fg="white", selectcolor="#444444",
                   activebackground="#2b2b2b", activeforeground="white").pack(anchor="w")
    tk.Radiobutton(fmt_frame, text="Documento de Requisitos — Empresa (SGG)", variable=format_var,
                   value="empresa", bg="#2b2b2b", fg="white", selectcolor="#444444",
                   activebackground="#2b2b2b", activeforeground="white").pack(anchor="w")
    tk.Radiobutton(fmt_frame, text="Documento de Requisitos — Valori (com capa)", variable=format_var,
                   value="valori", bg="#2b2b2b", fg="white", selectcolor="#444444",
                   activebackground="#2b2b2b", activeforeground="white").pack(anchor="w")

    # Project/system name (optional) — used as the document title and output filename.
    name_frame = tk.Frame(root, bg="#2b2b2b")
    name_frame.pack(pady=(2, 6))
    tk.Label(name_frame, text="Nome do sistema/documento (opcional):", font=("Helvetica", 9),
             bg="#2b2b2b", fg="#cccccc").pack(anchor="w")
    project_name_var = tk.StringVar(value="")
    tk.Entry(name_frame, textvariable=project_name_var, width=52, font=("Helvetica", 10),
             bg="#3c3c3c", fg="white", insertbackground="white",
             relief="flat").pack(anchor="w", ipady=3)

    # ── Acronym table ────────────────────────────────────────────────────────
    # Whisper garbles domain acronyms it has never heard ("IPOF" -> "HIPOF").
    # Declaring them here corrects the transcription before Agent 2 runs.
    acr_frame = tk.Frame(root, bg="#2b2b2b")
    acr_frame.pack(pady=(2, 6))
    tk.Label(acr_frame, text="Siglas faladas na reunião (opcional):", font=("Helvetica", 9),
             bg="#2b2b2b", fg="#cccccc").pack(anchor="w")
    tk.Label(acr_frame, text="uma por linha — SIGLA = significado", font=("Helvetica", 8),
             bg="#2b2b2b", fg="#888888").pack(anchor="w")
    acr_inner = tk.Frame(acr_frame, bg="#2b2b2b")
    acr_inner.pack(anchor="w")
    acr_scroll = tk.Scrollbar(acr_inner)
    acr_scroll.pack(side=tk.RIGHT, fill="y")
    acronyms_text = tk.Text(acr_inner, height=4, width=52, font=("Consolas", 9),
                            bg="#3c3c3c", fg="white", insertbackground="white",
                            bd=0, relief="flat", wrap="none",
                            yscrollcommand=acr_scroll.set)
    acronyms_text.pack(side=tk.LEFT, ipady=2)
    acr_scroll.config(command=acronyms_text.yview)
    _ACR_HINT = "IPOF = Índice de Programação Orçamentária e Financeira"

    def _acr_focus_in(_event=None):
        if acronyms_text.get("1.0", "end-1c") == _ACR_HINT:
            acronyms_text.delete("1.0", "end")
            acronyms_text.config(fg="white")

    def _acr_focus_out(_event=None):
        if not acronyms_text.get("1.0", "end-1c").strip():
            acronyms_text.insert("1.0", _ACR_HINT)
            acronyms_text.config(fg="#777777")

    # Placeholder text showing the expected format; cleared on focus.
    acronyms_text.insert("1.0", _ACR_HINT)
    acronyms_text.config(fg="#777777")
    acronyms_text.bind("<FocusIn>", _acr_focus_in)
    acronyms_text.bind("<FocusOut>", _acr_focus_out)

    def get_acronyms() -> str:
        """The acronym table's content, or "" when only the placeholder is present."""
        value = acronyms_text.get("1.0", "end-1c").strip()
        return "" if value == _ACR_HINT else value

    # Record section
    tk.Label(root, text="── Gravar reunião ──", font=("Helvetica", 9, "bold"),
             bg="#2b2b2b", fg="#888888").pack(pady=(6, 2))
    btn_frame = tk.Frame(root, bg="#2b2b2b")
    btn_frame.pack()
    btn_start = tk.Button(btn_frame, text="▶ Iniciar Gravação", command=on_start, width=18,
                          bg="#4CAF50", fg="white", font=("Helvetica", 11))
    btn_start.pack(side=tk.LEFT, padx=8)
    btn_stop = tk.Button(btn_frame, text="■ Parar Gravação", command=on_stop, width=18,
                         bg="#f44336", fg="white", font=("Helvetica", 11), state=tk.DISABLED)
    btn_stop.pack(side=tk.LEFT, padx=8)
    timer_label = tk.Label(root, text="", font=("Helvetica", 11, "bold"), bg="#2b2b2b", fg="#4CAF50")
    timer_label.pack(pady=(6, 0))

    # File section
    tk.Label(root, text="── Ou inserir arquivo (áudio/vídeo) ──", font=("Helvetica", 9, "bold"),
             bg="#2b2b2b", fg="#888888").pack(pady=(8, 2))
    file_frame = tk.Frame(root, bg="#2b2b2b")
    file_frame.pack()
    btn_file = tk.Button(file_frame, text="📁 Selecionar arquivo", command=on_select_file, width=18,
                         bg="#555555", fg="white", font=("Helvetica", 11))
    btn_file.pack(side=tk.LEFT, padx=8)
    btn_process = tk.Button(file_frame, text="▶ Iniciar Processamento", command=on_start_processing,
                            width=18, bg="#4CAF50", fg="white", font=("Helvetica", 11),
                            state=tk.DISABLED)
    btn_process.pack(side=tk.LEFT, padx=8)
    file_label = tk.Label(root, text="arquivo: (nenhum)", font=("Helvetica", 9),
                          bg="#2b2b2b", fg="#aaaaaa")
    file_label.pack(pady=(4, 0))

    tk.Label(root, text="Motor: Groq (fallback: Whisper local)", font=("Helvetica", 8),
             bg="#2b2b2b", fg="#888888").pack(pady=(8, 0))
    phase_label = tk.Label(root, text="Pronto.", font=("Helvetica", 10, "bold"),
                           bg="#2b2b2b", fg="white")
    phase_label.pack(pady=(6, 0))

    # Progress bar (determinate during transcription, animated during LLM agents).
    prog_var = tk.DoubleVar(value=0)
    progress = ttk.Progressbar(root, style="Pipe.Horizontal.TProgressbar",
                               orient="horizontal", mode="determinate",
                               variable=prog_var, maximum=100, length=480)
    progress.pack(pady=(6, 2))

    status_label = tk.Label(root, text="Escolha o formato e grave ou insira um arquivo.",
                            font=("Helvetica", 9), bg="#2b2b2b", fg="#aaaaaa")
    status_label.pack(pady=(2, 0))

    # Scrollable, read-only log of pipeline milestones.
    log_frame = tk.Frame(root, bg="#2b2b2b")
    log_frame.pack(pady=(6, 0), padx=20, fill="x")
    log_scroll = tk.Scrollbar(log_frame)
    log_scroll.pack(side=tk.RIGHT, fill="y")
    log_text = tk.Text(log_frame, height=7, width=58, font=("Consolas", 9),
                       bg="#1f1f1f", fg="#dddddd", bd=0, relief="flat",
                       yscrollcommand=log_scroll.set, state=tk.DISABLED, wrap="word")
    log_text.pack(side=tk.LEFT, fill="x", expand=True)
    log_scroll.config(command=log_text.yview)

    result_label = tk.Label(root, text="", font=("Helvetica", 9),
                            bg="#2b2b2b", fg="#4CAF50", justify="center")
    result_label.pack(pady=(4, 0))

    root.update()
    root.mainloop()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_summary(result: dict) -> None:
    print(f"\n{'='*60}")
    print("PIPELINE CONCLUÍDO")
    print(f"{'='*60}")
    print(f"Documento final (MD):  {result.get('markdown')}")
    print(f"Documento final (PDF): {result.get('pdf') or 'não gerado'}")
    print(f"Entidades de domínio:  {result.get('entities', 0)}")
    print(f"Relacionamentos:       {result.get('relationships', 0)}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo de elicitação de requisitos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python pipeline.py --full                          # abre GUI (gravar/inserir + formato), roda tudo
  python pipeline.py --from-audio reuniao.mp4        # transcreve (Groq) e continua
  python pipeline.py --from-transcript reuniao.txt   # identifica personas e continua
  python pipeline.py --from-json reuniao_personas.json --format empresa  # gera no formato escolhido
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full", action="store_true",
                       help="Abre a GUI (gravar ou inserir arquivo + seletor de formato) e roda tudo")
    group.add_argument("--from-audio", type=Path, metavar="AUDIO",
                       help="Começa a partir de um arquivo de áudio/vídeo (.wav/.mp3/.mp4/etc)")
    group.add_argument("--from-transcript", type=Path, metavar="TXT",
                       help="Começa a partir de uma transcrição .txt")
    group.add_argument("--from-json", type=Path, metavar="JSON",
                       help="Começa a partir do JSON de saída do Agent 2")
    parser.add_argument("--format", choices=["ieee", "empresa", "valori"], default="ieee",
                        help="Formato do documento (ieee | empresa | valori). No modo --full há "
                             "seletor na janela.")
    parser.add_argument("--project-name", default="",
                        help="Formatos empresa/valori: título do documento e nome do arquivo de saída.")
    parser.add_argument("--acronyms-file", type=Path, default=None, metavar="TXT",
                        help="Arquivo com as siglas faladas na reunião ('SIGLA = significado', uma "
                             "por linha). Corrige a transcrição e orienta o LLM. No modo --full há "
                             "um quadro na janela.")
    args = parser.parse_args()

    acronyms = ""
    if args.acronyms_file and args.acronyms_file.exists():
        acronyms = args.acronyms_file.read_text(encoding="utf-8")

    if args.full:
        _full_pipeline(initial_fmt=args.format)
        return

    # CLI modes: time the whole run and report it at the end.
    start = time.time()
    if args.from_audio:
        _from_audio(args.from_audio, args.format, project_name=args.project_name,
                    acronyms=acronyms)
    elif args.from_transcript:
        _from_transcript(args.from_transcript, args.format, project_name=args.project_name,
                         acronyms=acronyms)
    elif args.from_json:
        _from_json(args.from_json, args.format, project_name=args.project_name,
                   acronyms=acronyms)
    print(f"Tempo total de execução: {_format_duration(time.time() - start)}\n")


if __name__ == "__main__":
    main()
