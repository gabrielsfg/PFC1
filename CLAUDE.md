# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TCC/PFC (Projeto Final de Curso) em duas fases — PFC1 (concluído) e PFC2 (em andamento) — sobre IA Generativa e Engenharia de Software na UFG. O objetivo é automatizar o pipeline completo de elicitação de requisitos: de áudios de reuniões até histórias de usuário estruturadas, usando uma arquitetura multi-agente.

**PFC1 results** (validated on AMI Meeting Corpus, 7 meetings): 100% persona identification accuracy (28/28), 83% INVEST compliance, 9/10 qualitative framework score.

**PFC2 goals**: implement Agent 3 (Formatting Agent), quantitative metrics (WER/CER for Agent 1; Precision/Recall/F1 for Agent 2), expand validation to 50–100 AMI meetings, real-world validation with dev teams.

## Conventions

Full details in [Documentation/conventions.md](Documentation/conventions.md). Key rules:

- **All code in English** — variable names, function names, class names, file names, comments, docstrings. Exception: agent folder names (`agente-srs/` etc.) and string content sent to the LLM stay in Portuguese.
- **Layered service pattern** — every agent follows the same structure: `main.py` (CLI only) → `<agent>_processor.py` (orchestrator) → `<agent>_generator.py` (LLM + logic) → `document_renderer.py` (formatting agents only). `config/prompts.py` holds all prompt strings. `src/models.py` holds all Pydantic models.
- **Naming**: PascalCase for classes, snake_case for functions/files, UPPER_SNAKE_CASE for constants, leading `_` for private methods.

## Architecture

Five specialized agents in a sequential file-based pipeline:

```
agente-transcricao/   → Agent 1: Whisper speech-to-text, outputs .txt
agente-identificacao/ → Agent 2: GPT-4o-mini persona identification + user story extraction, outputs .json
agente-srs/           → Agent 3: generates IEEE 830 SRS document (Markdown + PDF)          [PLANNED]
agente-casos-de-uso/  → Agent 4: generates structured use cases + UML diagrams via kroki.io  [PLANNED]
agente-diagramas/     → Agent 5: generates domain model diagram, assembles final document     [PLANNED]
data/                 → Shared input/output directory (gitignored)
```

**Full data flow**:
```
audio recording
  → Agent 1 → transcription .txt
  → Agent 2 → personas + user stories .json
  → Agent 3 → SRS document IEEE 830 (.md + .pdf)
  → Agent 4 → use cases document (.md + .pdf, UML diagrams via kroki.io)
  → Agent 5 → domain diagram + final unified requirements document (.md + .pdf)
```

Agents communicate through a shared file system monitored by watchdog — each agent triggers the next when a new file appears in the output directory.

## Output formats and the unified executor

The pipeline supports **two selectable output document formats** (one per run — never both):

- **`ieee`** (default) — IEEE 830 SRS rendered from `agente-srs/templates/srs.md.j2`. Runs Agent 3 **and** Agent 4 (domain diagram + final consolidated document).
- **`empresa`** — the client (SGG-GO) "Documento de Requisitos" rendered from `agente-srs/templates/feature_requirements.md.j2` (Funcionalidade, RF with Detalhamento/Comentários, Regras de Negócio em tabela, Casos de Uso `UC`, Requisitos Não-Funcionais). This format has **no diagrams**, so **Agent 4 is skipped** — Agent 3's output is the final document.

Format selection:
- `--format {ieee,empresa}` on `pipeline.py`, `agente-srs/main.py`, and `agente-diagramas/main.py`.
- Env var `DOCUMENT_FORMAT` is the default for `--monitor` mode (watchdog).
- In the GUI (`pipeline.py --full`) there is a radio selector.
- Empresa document metadata (project code, client, system version, authors, dates) is **not** derivable from audio — `default_empresa_meta()` in `agente-srs/src/srs_processor.py` fills placeholders for now (TODO: collect via the GUI).

**Unified executor** — `python pipeline.py --full` opens a single window where you either **record** a meeting or **insert an audio/video file** (skips recording), pick the document format, and the whole pipeline runs to the final document.

**Transcription engine** — Agent 1 transcribes via **Groq** (`whisper-large-v3-turbo`) by default, with an automatic **local faster-whisper fallback** (fast preset: `small` + `beam_size=1`). Any audio **or video** input is normalized by **ffmpeg** to 16 kHz mono FLAC and split on silence if it exceeds `GROQ_MAX_FILE_MB` (~25 MB Groq limit). Requires `ffmpeg` on the PATH and `GROQ_API_KEY` in `agente-transcricao/.env`. Shared modules: `agente-transcricao/src/stt/transcription_service.py`, `groq_transcriber.py`, `src/audio/preprocessor.py`.

### agente-identificacao

- `main.py` — CLI entry point (`--file`, `--dir`, `--monitor` modes)
- `src/persona_identifier.py` — Core orchestration: calls OpenAI twice (identify personas → generate user stories), parses JSON, saves output
- `src/openai_client.py` — OpenAI wrapper with tenacity retry/backoff
- `src/file_monitor.py` — Watchdog-based watcher; calls `PersonaIdentifier` on new `.txt` files
- `config/prompts.py` — All LLM prompts (system message, persona identification, user stories with INVEST criteria)

Output JSON shape:
```json
{
  "metadata": { "arquivo_origem", "data_processamento", "modelo_usado" },
  "analise_personas": { "personas": [...], "resumo_conversa", "tipo_interacao" },
  "historias_usuario": { "user_stories": [...] }
}
```

### agente-transcricao

- `src/main.py` — Typer CLI (`record`, `transcribe-file` commands)
- `gui_app.py` — Tkinter GUI (record **or** insert audio/video file; Groq + local fallback)
- `run_transcribe.py` — Simpler CLI bypassing Typer, useful for direct calls
- `src/stt/transcription_service.py` — orchestrator: ffmpeg preprocess → split → Groq per chunk → merge; `transcribe_with_groq`, `transcribe_local_fast`, `save_transcription`
- `src/stt/groq_transcriber.py` — Groq Whisper client (`GroqUnavailableError` triggers fallback)
- `src/stt/transcribe.py` — `Transcriber` class wrapping faster-whisper (configurable `beam_size`/`best_of`)
- `src/audio/preprocessor.py` — ffmpeg extract/compress (16 kHz mono FLAC) + silence-based split
- `src/audio/record.py` — Microphone capture via sounddevice
- `config/settings.py` — Groq/local config from `.env`

## Setup

Each agent has its own `requirements.txt` and `.env`. Install and configure them separately:

```bash
# Identification agent
cd agente-identificacao
pip install -r requirements.txt
cp .env.example .env  # then fill in OPENAI_API_KEY

# Transcription agent
cd agente-transcricao
pip install -r requirements.txt
```

### Environment variables (agente-identificacao/.env)

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Required |
| `OPENAI_MODEL` | Default: `gpt-4o-mini` |
| `INPUT_DIR` | Path to transcription .txt files |
| `OUTPUT_DIR` | Path for output JSON files |
| `PROCESSED_DIR` | Tracks already-processed files |
| `CHECK_INTERVAL` | Monitor polling interval (seconds) |
| `MAX_RETRIES` | OpenAI API retry attempts |
| `HUGGINGFACE_TOKEN` | For AMI dataset scripts |

## Running the agents

### Identification agent

```bash
cd agente-identificacao

# Monitor a directory continuously (main use case)
python main.py --monitor

# Process a single transcription file
python main.py --file path/to/transcription.txt

# Batch process a directory
python main.py --dir path/to/dir

# Custom monitor interval
python main.py --monitor --check-interval 10
```

### Transcription agent

```bash
cd agente-transcricao

# Record audio and transcribe
python src/main.py record

# Transcribe an existing audio file
python src/main.py transcribe-file <audio_file>

# Direct transcription (simpler)
python run_transcribe.py <file> --model-size small --device cpu

# Launch GUI
python gui_app.py
```

## Key implementation details

- `_parse_json_response()` in `persona_identifier.py` strips markdown code fences before JSON parsing — LLM responses often wrap JSON in ```json blocks.
- `processed_files.txt` in `PROCESSED_DIR` prevents reprocessing the same file; delete it to reprocess.
- Whisper model sizes: `tiny`, `base`, `small`, `medium`, `large-v3` — balance speed vs. accuracy. Default is `small`.
- User stories follow the **INVEST** criteria and Portuguese format: *"Como [persona], eu quero [objetivo] para [benefício]"*. The main failure mode identified in PFC1 is violating the "Small" criterion (stories too broad, need decomposition).
- AMI dataset scripts (`import_ami_dataset.py`, `investigate_ami.py`) are exploratory utilities, not part of the main pipeline. AMI data is accessed via HuggingFace `datasets` library using `HUGGINGFACE_TOKEN`.
- Known issue from PFC1: UTF-8 encoding errors with special characters in output JSON — needs fixing in PFC2.
- Agent 3 (Formatting Agent) is planned but not yet implemented. It will read Agent 2's JSON output and produce structured requirements documentation (PDF/Markdown or integration with requirements management tools).

## Agent 3, 4 and 5 — Requirements Formatting (planned, PFC2)

The formatting stage is split into three specialized agents, all triggered sequentially by file monitoring (same watchdog pattern as Agents 1→2):

```
agente-identificacao/output/*.json
        ↓ Agent 3
User stories document (Markdown + PDF)
        ↓ Agent 4
Use cases document (Markdown + PDF)
        ↓ Agent 5
Domain diagrams (PlantUML via kroki.io → PNG/SVG embedded in Markdown + PDF)
        ↓
Final unified requirements document (Markdown + PDF)
```

### Agent 3 — SRS Document Generator (`agente-srs/`)

**Input**: JSON from Agent 2 (`analise_personas` + `historias_usuario`)

**Output**: Software Requirements Specification (SRS) following **IEEE 830**, assembled by LLM from the Agent 2 JSON:

```
1. Introdução
   1.1 Propósito do documento
   1.2 Escopo do sistema
   1.3 Definições, acrônimos e abreviações
   1.4 Referências (reunião de origem, data, participantes — from metadata)

2. Descrição Geral
   2.1 Identificação do problema (derived from resumo_conversa + tipo_interacao)
   2.2 Perspectiva do produto
   2.3 Stakeholders / Personas (name, role, characteristics, context — from analise_personas)

3. Requisitos Funcionais
   RF001, RF002, ... (numbered, extracted and normalized from user stories)

4. Histórias de Usuário
   Table per persona: ID | Como... | Quero... | Para... | INVEST score
```

Cases de uso (Agent 4) and domain diagrams (Agent 5) are referenced in the document but generated by downstream agents.

**Format**: Markdown source (`.md`) + PDF via Pandoc or WeasyPrint

**Stack** (suggested): `jinja2` for SRS template rendering, `weasyprint` or `pandoc` (subprocess) for PDF, LLM call (GPT-4o-mini) to fill free-text sections (problem statement, scope, definitions)

---

### Agent 4 — Use Case Generator (`agente-casos-de-uso/`)

**Input**: Agent 3 output + original Agent 2 JSON

**Output**: For each user story / persona interaction:
- Structured use case template: Actor, Pre-condition, Post-condition, Main flow, Alternative flows, Exception flows
- Use case diagram in PlantUML (rendered to PNG/SVG via kroki.io API)

**Format**: Markdown + embedded diagram images + PDF

**Stack** (suggested): `requests` (kroki.io API calls), `jinja2` for use case templates

---

### Agent 5 — Domain Diagram Generator (`agente-diagramas/`)

**Input**: Agents 3 + 4 output + Agent 2 JSON

**Output**:
- Domain model diagram: entities, attributes, relationships extracted from personas and requirements context
- PlantUML class diagram source sent to kroki.io → PNG/SVG
- Final unified requirements document assembling all previous sections

**Format**: Markdown with embedded images + single final PDF

**Stack** (suggested): `requests` (kroki.io), LLM call (GPT-4o-mini) to extract domain entities from requirements context

---

### Inter-agent communication (Agents 3–5)

Same file-based watchdog pattern as Agents 1–2. Each agent monitors the output directory of the previous one. Suggested directory layout:

```
agente-srs/               # Agent 3 — IEEE 830 SRS document
agente-casos-de-uso/      # Agent 4 — use cases + UML diagrams
agente-diagramas/         # Agent 5 — domain diagram + final unified document
```

Each with its own `requirements.txt`, `.env`, `main.py`, `src/`, `config/prompts.py`, and `templates/` (Jinja2 templates for document sections).

### kroki.io integration note

kroki.io is a free public API that renders PlantUML/Mermaid/etc. diagrams to PNG/SVG. Encoding: POST diagram source (or base64-encode it in the URL). No API key required for public instance. Consider self-hosting for production to avoid external dependency.
