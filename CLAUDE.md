# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TCC/PFC (Projeto Final de Curso) em duas fases — PFC1 (concluído) e PFC2 (em andamento) — sobre IA Generativa e Engenharia de Software na UFG. O objetivo é automatizar o pipeline completo de elicitação de requisitos: de áudios de reuniões até documentos de requisitos estruturados, usando uma arquitetura multi-agente.

**PFC1 results** (validated on AMI Meeting Corpus, 7 meetings): 100% persona identification accuracy (28/28), 83% INVEST compliance, 9/10 qualitative framework score.

**PFC2 goals**: quantitative metrics (WER/CER for Agent 1; Precision/Recall/F1 for Agent 2), expand validation to more AMI meetings, real-world validation with the SGG-GO government partner (meeting already processed, gold-standard document available).

## Conventions

Full details in [Documentation/conventions.md](Documentation/conventions.md). Key rules:

- **All code in English** — variable names, function names, class names, file names, comments, docstrings. Exception: agent folder names (`agente-srs/` etc.) and string content sent to the LLM stay in Portuguese.
- **Layered service pattern** — every agent follows the same structure: `main.py` (CLI only) → `<agent>_processor.py` (orchestrator) → `<agent>_generator.py` (LLM + logic) → `document_renderer.py` (formatting agents only). `config/prompts.py` holds all prompt strings. `src/models.py` holds all Pydantic models.
- **Naming**: PascalCase for classes, snake_case for functions/files, UPPER_SNAKE_CASE for constants, leading `_` for private methods.

## Architecture

Four specialized agents in a sequential file-based pipeline:

```
agente-transcricao/   → Agent 1: Groq whisper-large-v3-turbo STT, outputs .txt
agente-identificacao/ → Agent 2: claude-haiku-4-5 persona identification + user story extraction, outputs .json
agente-srs/           → Agent 3: claude-sonnet-4-6 SRS document generator (IEEE 830 or empresa format), outputs .md + .pdf
agente-diagramas/     → Agent 4: claude-sonnet-4-6 domain diagram + final unified document (IEEE 830 only)
data/                 → Shared input/output directory (gitignored)
```

**Full data flow**:
```
audio/video file
  → Agent 1 → transcription .txt
  → Agent 2 → personas + user stories .json
  → Agent 3 → requirements document (.md + .pdf)  [empresa format: pipeline ends here]
  → Agent 4 → domain diagram + final unified document (.md + .pdf)  [ieee format only]
```

Agents communicate through a shared file system — the unified executor (`pipeline.py`) runs them sequentially. Watchdog-based monitoring is available for `--monitor` mode.

## Output formats and the unified executor

The pipeline supports **two selectable output document formats** (one per run — never both):

- **`ieee`** (default) — IEEE 830 SRS rendered from `agente-srs/templates/srs.md.j2`. Runs Agent 3 **and** Agent 4 (domain diagram + final consolidated document).
- **`empresa`** — the SGG-GO partner "Documento de Requisitos" rendered from `agente-srs/templates/feature_requirements.md.j2` (Funcionalidade, RF with Detalhamento/Comentários, Regras de Negócio em tabela, Casos de Uso `CSU`, Requisitos Não-Funcionais optional). This format has **no diagrams**, so **Agent 4 is skipped** — Agent 3's output is the final document.

Format selection:
- `--format {ieee,empresa}` on `pipeline.py`, `agente-srs/main.py`, and `agente-diagramas/main.py`.
- Env var `DOCUMENT_FORMAT` is the default for `--monitor` mode (watchdog).
- In the GUI (`pipeline.py --full`) there is a radio selector.
- Empresa document metadata (project code, client, system version, authors, dates) is **not** derivable from audio — `default_empresa_meta()` in `agente-srs/src/srs_processor.py` fills placeholders (TODO: collect via the GUI).

**Unified executor** — `pipeline.py` entry points:
- `--full` — opens the Tkinter GUI: record or insert audio/video file, pick format, runs full pipeline
- `--from-audio <file>` — starts from an audio/video file (skips recording)
- `--from-transcript <file>` — starts from an existing `.txt` transcription (skips Agent 1)
- `--from-json <file>` — starts from an existing Agent 2 JSON (skips Agents 1 and 2)

**Transcription engine** — Agent 1 transcribes via **Groq** (`whisper-large-v3-turbo`) by default, with an automatic **local faster-whisper fallback** (fast preset: `small` + `beam_size=1`). Any audio **or video** input is normalized by **ffmpeg** to 16 kHz mono FLAC and split on silence if it exceeds `GROQ_MAX_FILE_MB` (~20 MB). Requires `ffmpeg` on the PATH and `GROQ_API_KEY` in `agente-transcricao/.env`. Shared modules: `agente-transcricao/src/stt/transcription_service.py`, `groq_transcriber.py`, `src/audio/preprocessor.py`.

### agente-identificacao

- `main.py` — CLI entry point (`--file`, `--dir`, `--monitor`, `--output-dir` modes)
- `src/persona_identifier.py` — Core orchestration: calls Anthropic Claude twice (identify personas → generate user stories), parses JSON, saves output
- `src/anthropic_client.py` — Anthropic Claude wrapper with tenacity retry/backoff; default model: `claude-haiku-4-5-20251001` (overridable via `ANTHROPIC_MODEL` env var)
- `src/openai_client.py` — **legacy dead code** (kept for reference; not used by persona_identifier.py)
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

### agente-srs

- `main.py` — CLI entry point (`--file`, `--format {ieee,empresa}`, `--project-name`)
- `src/srs_processor.py` — Orchestrator: routes to ieee or empresa generator based on `--format`
- `src/srs_generator.py` — IEEE 830 generator: calls Claude sonnet to produce introduction, functional requirements, use cases + PlantUML diagrams via kroki.io
- `src/feature_generator.py` — Empresa format generator: calls Claude sonnet to produce Funcionalidade, RF, RN, CSU, RNF sections
- `src/anthropic_client.py` — Anthropic Claude wrapper; default model: `claude-sonnet-4-6`
- `src/document_renderer.py` — Jinja2 template rendering → Markdown → PDF via WeasyPrint
- `templates/srs.md.j2` — IEEE 830 Jinja2 template
- `templates/feature_requirements.md.j2` — Empresa format Jinja2 template (includes Sumário with CSS page numbers)

### agente-diagramas (Agent 4)

- `main.py` — CLI entry point (`--file`, `--format`)
- `src/domain_diagram_generator.py` — Calls Claude sonnet to extract domain entities and relationships, generates PlantUML class diagram, renders via kroki.io
- `src/document_assembler.py` — Assembles final unified requirements document
- `src/anthropic_client.py` — Anthropic Claude wrapper; default model: `claude-sonnet-4-6`
- `src/kroki_client.py` — kroki.io API client (PlantUML → PNG/SVG)

### agente-transcricao

- `src/main.py` — Typer CLI (`record`, `transcribe-file` commands)
- `gui_app.py` — Tkinter GUI (record **or** insert audio/video file; Groq + local fallback)
- `run_transcribe.py` — Simpler CLI bypassing Typer, useful for direct calls
- `src/stt/transcription_service.py` — orchestrator: ffmpeg preprocess → split → Groq per chunk → merge; `transcribe_with_groq`, `transcribe_local_fast`, `save_transcription`
- `src/stt/groq_transcriber.py` — Groq Whisper client (`GroqUnavailableError` triggers fallback)
- `src/stt/transcribe.py` — `Transcriber` class wrapping faster-whisper (configurable `beam_size`/`best_of`)
- `src/audio/preprocessor.py` — ffmpeg extract/compress (16 kHz mono FLAC) + silence-based split
- `src/audio/record.py` — Microphone capture via sounddevice
- `config/settings.py` — Groq/local config from `.env`; default `GROQ_MAX_FILE_MB=20`

## Setup

Each agent has its own `requirements.txt` and `.env`. Install and configure them separately:

```bash
# Identification agent
cd agente-identificacao
pip install -r requirements.txt
cp .env.example .env  # then fill in ANTHROPIC_API_KEY

# Transcription agent
cd agente-transcricao
pip install -r requirements.txt
# fill in GROQ_API_KEY in .env

# SRS agent
cd agente-srs
pip install -r requirements.txt
# fill in ANTHROPIC_API_KEY in .env

# Diagrams agent
cd agente-diagramas
pip install -r requirements.txt
# fill in ANTHROPIC_API_KEY in .env
```

### Environment variables (agente-identificacao/.env)

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Required |
| `ANTHROPIC_MODEL` | Default: `claude-haiku-4-5-20251001` |
| `INPUT_DIR` | Path to transcription .txt files |
| `OUTPUT_DIR` | Path for output JSON files |
| `PROCESSED_DIR` | Tracks already-processed files |
| `CHECK_INTERVAL` | Monitor polling interval (seconds) |
| `MAX_RETRIES` | Anthropic API retry attempts |
| `HUGGINGFACE_TOKEN` | For AMI dataset scripts only |

### Environment variables (agente-srs/.env and agente-diagramas/.env)

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Required |
| `ANTHROPIC_MODEL` | Default: `claude-sonnet-4-6` |
| `DOCUMENT_FORMAT` | Default format for `--monitor` mode (`ieee` or `empresa`) |
| `EMPRESA_INCLUDE_NFR` | Set to `false` to omit the RNF section in empresa format |

## Running the agents

### Full pipeline (recommended)

```bash
# GUI mode — record or insert file, pick format
python pipeline.py --full

# From an audio/video file
python pipeline.py --from-audio path/to/meeting.mp4 --format empresa

# From existing transcript
python pipeline.py --from-transcript path/to/transcript.txt --format ieee

# From existing Agent 2 JSON
python pipeline.py --from-json path/to/analysis.json --format empresa --project-name "MyProject"
```

### Individual agents

```bash
# Agent 2 — Identification
cd agente-identificacao
python main.py --file path/to/transcription.txt

# Agent 3 — SRS
cd agente-srs
python main.py --file path/to/analysis.json --format empresa --project-name "MyProject"

# Agent 1 — Transcription
cd agente-transcricao
python src/main.py transcribe-file <audio_file>
python run_transcribe.py <file> --model-size small --device cpu
```

## Key implementation details

- `_parse_json_response()` in `persona_identifier.py` strips markdown code fences before JSON parsing — LLM responses often wrap JSON in ```json blocks.
- `processed_files.txt` in `PROCESSED_DIR` prevents reprocessing the same file; delete it to reprocess.
- Whisper fallback model is `small` with `beam_size=1` for speed; configurable via `LOCAL_WHISPER_MODEL` and `LOCAL_WHISPER_BEAM_SIZE` env vars.
- User stories follow the **INVEST** criteria and Portuguese format: *"Como [persona], eu quero [objetivo] para [benefício]"*. Main failure mode: violating the "Small" criterion (stories too broad).
- AMI dataset scripts (`import_ami_dataset.py`, `investigate_ami.py`) are exploratory utilities, not part of the main pipeline. AMI data is accessed via HuggingFace `datasets` library using `HUGGINGFACE_TOKEN`.
- **Persona vs. actor distinction** (empresa format): prompts distinguish `participantes_reuniao` (meeting attendees) from `atores_sistema` (actual software users/actors). This was a known failure mode in v1 (meeting participants were used as actors) — fixed in v2 via prompt engineering.
- **Empresa format use cases**: numbered as `CSU1`, `CSU2`, ... (not `UC`); business rules numbered continuously as `RN1`, `RN2`, ... (not restarting per group).
- WeasyPrint PDF engine is fixed for the empresa format to enable CSS Paged Media (table of contents with `target-counter(page)`). Pandoc is the alternative engine for IEEE 830.
- kroki.io is the public PlantUML rendering API (no key required). Used by both `agente-srs` (use case diagrams, ieee format) and `agente-diagramas` (domain class diagram).

## Real-world case study (SGG-GO)

A partnership with a Brazilian public sector technology agency provided a real stakeholder meeting for end-to-end validation:
- **Meeting**: 10 participants, 1h 37m 47s, Brazilian Portuguese, budget balance management domain
- **Input**: 609 MB video file → Agent 1 → Agent 2 → Agent 3 (empresa format)
- **Gold standard**: official requirements document (`PR0102`) produced manually by the agency's analyst
- **Comparison files**: `analise-tcc/comparacao_PR0102.md` (v1 analysis) and `comparacao_PR0102_v2_pos_melhorias.md` (v2 after prompt improvements)
- **Known error propagation example**: Whisper transcribed "IPOF" as "HIPOF" — this error propagated through all downstream agents into the final document (quantitative RQ5 evidence)
