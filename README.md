# From Meeting Audio to Requirements: A Generative-AI Multi-Agent Pipeline

> Undergraduate final project (TCC / *Projeto Final de Curso*) — Institute of Informatics, **Federal University of Goiás (UFG)**, 2026.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Claude](https://img.shields.io/badge/LLM-Claude-D97757.svg)](https://www.anthropic.com/)
[![Status](https://img.shields.io/badge/status-complete-brightgreen.svg)]()

A pipeline of four specialized LLM agents that automates the full software **requirements-elicitation** workflow: it takes a raw recording of a stakeholder meeting and produces a structured requirements document — transcription, personas and user stories, an IEEE 830 SRS (or a company-format requirements document), and a domain diagram — with almost no manual effort.

```
 audio / video                                            requirements
   of a meeting  ─────────►  [ 4 specialized agents ]  ─────────►  document
                                                                  (.md + .pdf)
```

---

## 📄 Read the written work

- 🇬🇧 **Conference paper (English):** *From Meeting Audio to Requirements: A Generative-AI Multi-Agent Pipeline* — to appear at the **1st Workshop on Software Engineering for Agentic Systems (SE4AS)**, co-located with **CBSoft 2026** (IME-USP, São Paulo). **[⬇ Download PDF](paper/SE4AS-2026-paper-en.pdf)**
- 🇧🇷 **Monograph (Portuguese):** *Inteligência Artificial Generativa e Engenharia de Software: Um estudo de caso* — full undergraduate thesis. **[⬇ Download PDF](paper/monografia-pt-br.pdf)**

---

## About the project

Requirements elicitation is one of the most human-intensive and error-prone stages of software development: analysts sit through hours of meetings and manually translate loosely-structured conversation into personas, user stories, and formal requirements. This project investigates whether **Generative AI, organized as a multi-agent system**, can automate that translation end to end.

Instead of a single monolithic prompt, the work uses **four specialized agents** connected by a file-based contract, each with a model chosen to match its task (cheap models for narrow tasks, stronger models for open-ended synthesis). This design makes the system's behaviour observable — including how an error made by an early agent **propagates** through the rest of the pipeline, which the study treats as a first-class result rather than an anecdote.

The pipeline was validated on the **AMI Meeting Corpus**, on the **Mozilla Common Voice (PT)** corpus, and — most importantly — on a **real 1h38m stakeholder meeting** from a Brazilian public-sector technology agency, against an official requirements document written by a human analyst as gold standard.

---

## Architecture

Four agents run sequentially, communicating through a shared file system. The unified executor (`pipeline.py`) chains them; each agent can also run standalone.

```
 audio / video file
   │
   ▼
 [Agent 1] agente-transcricao/    Speech-to-text (Groq whisper-large-v3-turbo,
   │                              local faster-whisper fallback)        → .txt
   ▼
 [Agent 2] agente-identificacao/  Personas + user stories (INVEST)
   │                              claude-haiku-4-5                       → .json
   ▼
 [Agent 3] agente-srs/            Requirements document
   │                              claude-sonnet-4-6                      → .md + .pdf
   ▼
 [Agent 4] agente-diagramas/      Domain diagram + final unified doc
                                  claude-sonnet-4-6                      → .md + .pdf
```

### Two output formats (one per run)

| Format | Description | Agents run |
|---|---|---|
| **`ieee`** (default) | IEEE 830 SRS + PlantUML use-case & domain diagrams | Agents 1–4 |
| **`empresa`** | SGG-GO partner "Documento de Requisitos" (Funcionalidade, RF, RN, CSU, RNF); no diagrams | Agents 1–3 |

---

## Results

Final quantitative evaluation (see [`evaluation/`](evaluation/) for the reproducible harness and the monograph, Chapter 5, for full discussion).

| Research question | Metric | Result |
|---|---|---|
| **RQ1** — Transcription quality | WER / CER (Common Voice PT, 200 clips) | **Groq: 6.3% / 2.3%** · local fallback: 13.5% / 4.9% |
| **RQ2** — Persona identification | Precision / Recall / F1 (AMI, 7 meetings) | **P 1.00 · R 0.92 · F1 0.96** |
| **RQ2** — User-story quality (INVEST) | Strict LLM-judge conformance (6/6 criteria) | AMI **52.5%** · real domain **66.7%** (judge×human agreement κ = 0.13 / 0.31) |
| **RQ3** — Requirement coverage | Recall vs. human gold-standard document | **72.7%** overall (business rules & use cases **100%**) |
| **RQ4** — Cost & latency | Full 1h38m real meeting, end to end | **~US$0.72 · ~11 min** |

**Key findings**

- A full real meeting is processed for **under one dollar in about eleven minutes**, versus the hours a human analyst spends.
- Per-agent model selection pays off: Agent 3 (open-ended synthesis, Sonnet) accounts for ~82% of cost while the narrow tasks stay on the cheap Haiku model.
- The uncovered requirements are **pure-UI actions** ("hide screen X") that require *visual* input the audio-only pipeline cannot perceive — a modality limitation, not an extraction failure.
- **Error propagation is real and measurable:** Agent 1 mis-transcribed the domain term *IPOF* as *HIPOF*, and the error flowed unchanged through every downstream agent into the final document — a concrete argument for validation between agents.

> Numbers are reported honestly: the strict automatic INVEST judge is deliberately demanding, and the earlier PFC1 figures (based on a looser manual rubric) are superseded by this evaluation.

---

## Tech stack

- **Python 3.11**
- **LLMs:** Anthropic Claude (`claude-haiku-4-5`, `claude-sonnet-4-6`)
- **Speech-to-text:** Groq `whisper-large-v3-turbo`, with local [faster-whisper](https://github.com/SYSTRAN/faster-whisper) fallback
- **Audio/video:** ffmpeg (16 kHz mono FLAC normalization, silence-based splitting)
- **Data models & templating:** Pydantic, Jinja2
- **Diagrams:** PlantUML via [kroki.io](https://kroki.io/)
- **PDF:** WeasyPrint / Pandoc + xelatex
- **Orchestration:** Watchdog (file-based monitoring), Tkinter (GUI)

---

## Prerequisites

- **Python 3.11** (recommended — some dependencies lack pre-built wheels on 3.14)
- **ffmpeg** on your `PATH` — <https://ffmpeg.org/download.html>
- An **Anthropic API key** (Agents 2, 3, 4)
- A **Groq API key** (Agent 1; the pipeline falls back to a local model if absent)
- *Optional, for PDF export:* Pandoc + xelatex (MiKTeX) or the GTK3 runtime for WeasyPrint

---

## Installation

```bash
git clone https://github.com/gabrielsfg/PFC1.git
cd PFC1
```

Install each agent's dependencies (from the repo root, on Windows PowerShell):

```powershell
foreach ($agent in @("agente-transcricao","agente-identificacao","agente-srs","agente-diagramas")) {
    py -3.11 -m pip install -r "$agent\requirements.txt"
}
```

Configure each agent by copying its `.env.example` to `.env` and filling in the keys:

```powershell
foreach ($agent in @("agente-transcricao","agente-identificacao","agente-srs","agente-diagramas")) {
    Copy-Item "$agent\.env.example" "$agent\.env"
}
# then edit each .env:  GROQ_API_KEY (agent 1) and ANTHROPIC_API_KEY (agents 2–4)
```

---

## Usage

### Full pipeline (recommended)

```bash
# GUI: record or pick an audio/video file, choose the output format, run everything
python pipeline.py --full

# From an audio/video file
python pipeline.py --from-audio path/to/meeting.mp4 --format empresa

# From an existing transcript (skips Agent 1)
python pipeline.py --from-transcript path/to/transcript.txt --format ieee

# From an existing Agent 2 JSON (skips Agents 1 and 2)
python pipeline.py --from-json path/to/analysis.json --format empresa --project-name "MyProject"
```

### Individual agents

```bash
# Agent 1 — Transcription
cd agente-transcricao
python src/main.py transcribe-file path/to/audio.mp4

# Agent 2 — Persona & user-story identification
cd agente-identificacao
python main.py --file path/to/transcription.txt

# Agent 3 — Requirements document
cd agente-srs
python main.py --file path/to/analysis.json --format empresa --project-name "MyProject"

# Agent 4 — Domain diagram + final document (ieee format only)
cd agente-diagramas
python main.py --file path/to/analysis.json
```

### Reproducing the evaluation

The [`evaluation/`](evaluation/) directory holds the metrics harness (WER/CER, Precision/Recall/F1, INVEST LLM-judge, Cohen's κ, coverage, cost). Fill in the `*.template.json` files, provide the corpora and API keys, and run the `qp*.py` scripts — see [`evaluation/README.md`](evaluation/README.md).

---

## Project structure

```
PFC1/
├── agente-transcricao/    # Agent 1 — speech-to-text (Groq + local fallback)
├── agente-identificacao/  # Agent 2 — personas + user stories (Claude Haiku)
├── agente-srs/            # Agent 3 — SRS / company requirements doc (Claude Sonnet)
├── agente-diagramas/      # Agent 4 — domain diagram + final document (Claude Sonnet)
├── evaluation/            # Reproducible metrics harness (RQ1–RQ4)
├── analise-tcc/           # Real-case comparison against the human gold standard
├── data/                  # Shared input/output (gitignored)
├── pipeline.py            # Unified executor (GUI + CLI entry points)
├── CLAUDE.md              # Repository guide
└── LICENSE
```

Every agent follows the same layered structure: `main.py` (CLI) → `<agent>_processor.py` (orchestrator) → `<agent>_generator.py` (LLM + logic) → `document_renderer.py`, with prompts in `config/prompts.py` and Pydantic models in `src/models.py`.

---

## Author & advisor

- **Author:** Gabriel Ferreira Silva — [LinkedIn](https://www.linkedin.com/in/gabriel-ferreira-silva-3932b2210) · [GitHub](https://github.com/gabrielsfg)
- **Advisor:** Prof. Jacson Rodrigues Barbosa — Institute of Informatics, UFG

---

## License

Released under the [MIT License](LICENSE).

---

## Citation

If you reference this work, please cite the conference paper:

```bibtex
@inproceedings{silva2026meeting,
  author    = {Silva, Gabriel Ferreira and Barbosa, Jacson Rodrigues},
  title     = {From Meeting Audio to Requirements: A Generative-AI
               Multi-Agent Pipeline},
  booktitle = {Proceedings of the 1st Workshop on Software Engineering for
               Agentic Systems (SE4AS), co-located with CBSoft 2026},
  year      = {2026},
  address   = {S\~{a}o Paulo, Brazil}
}
```
