# Agent 2 — Persona & User-Story Identification

Second agent of the [requirements-elicitation pipeline](../README.md). It reads a meeting **transcription** (`.txt`), identifies the **personas** (system actors) discussed, and generates **user stories** following the INVEST criteria — all via Anthropic Claude.

- **Input:** `.txt` transcription (from Agent 1)
- **Output:** `.json` with personas + user stories (consumed by Agent 3)
- **Model:** `claude-haiku-4-5` (a cheap, fast model is enough for this narrow extraction task)

## Features

- Automatic persona identification from a transcript
- Extraction of each persona's characteristics and context
- User-story generation in the Portuguese format *"Como [persona], eu quero [objetivo] para [benefício]"*, checked against **INVEST**
- Automatic monitoring of new files (watchdog)
- Batch processing of a whole directory
- Tracking of already-processed files (no reprocessing)

## Project structure

```
agente-identificacao/
├── main.py                     # CLI entry point (--file, --dir, --monitor, --output-dir)
├── src/
│   ├── persona_identifier.py   # Orchestrator: 2 Claude calls (personas → user stories) + JSON parsing
│   ├── anthropic_client.py     # Anthropic Claude wrapper with tenacity retry/backoff
│   ├── file_monitor.py         # Watchdog-based watcher
│   └── openai_client.py        # legacy (v1 used OpenAI) — kept for reference, NOT used
├── config/
│   └── prompts.py              # All LLM prompts (system message, personas, INVEST user stories)
├── data/
│   ├── output/                 # Generated JSON results
│   └── processed/              # processed_files.txt — tracks handled inputs
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

```bash
cd agente-identificacao
pip install -r requirements.txt

# Configure the environment
cp .env.example .env            # then edit .env and set ANTHROPIC_API_KEY
```

Minimal `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
INPUT_DIR=../agente-transcricao/data/output
OUTPUT_DIR=./data/output
```

## Usage

```bash
# Single file
python main.py --file ../agente-transcricao/data/output/transcription.txt

# Whole directory
python main.py --dir ../agente-transcricao/data/output

# Continuous monitor mode (auto-processes new .txt files)
python main.py --monitor

# Monitor with a custom polling interval / directories
python main.py --monitor --check-interval 10
python main.py --monitor --input-dir ./custom/input --output-dir ./custom/output
```

## Output format

```json
{
  "metadata": {
    "arquivo_origem": "transcription_20260610.txt",
    "data_processamento": "2026-06-10T20:30:00",
    "modelo_usado": "claude-haiku-4-5-20251001"
  },
  "analise_personas": {
    "personas": [
      {
        "id": "persona_1",
        "nome": "Usuário Final",
        "papel": "Ator do sistema",
        "caracteristicas": ["Opera o sistema no dia a dia"],
        "contexto": "Responsável por acompanhar o saldo orçamentário",
        "trechos_relevantes": ["Eu preciso de...", "Meu problema é..."]
      }
    ],
    "resumo_conversa": "...",
    "tipo_interacao": "levantamento de requisitos"
  },
  "historias_usuario": {
    "user_stories": [
      {
        "persona_id": "persona_1",
        "persona_nome": "Usuário Final",
        "historias": [
          {
            "id": "story_1",
            "historia": "Como usuário final, eu quero X para Y",
            "prioridade": "alta",
            "contexto": "...",
            "trecho_base": "..."
          }
        ]
      }
    ]
  }
}
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key | *required* |
| `ANTHROPIC_MODEL` | Claude model | `claude-haiku-4-5-20251001` |
| `INPUT_DIR` | Input directory | `../agente-transcricao/data/output` |
| `OUTPUT_DIR` | Output directory | `./data/output` |
| `PROCESSED_DIR` | Processed-files tracking | `./data/processed` |
| `CHECK_INTERVAL` | Monitor polling interval (s) | `5` |
| `MAX_RETRIES` | API retry attempts | `3` |

## Implementation notes

- **Personas are system actors, not meeting attendees.** The prompts explicitly separate `participantes_reuniao` (who spoke) from `atores_sistema` (who will use the software). Using attendees as actors was a v1 failure mode, fixed via prompt engineering.
- **INVEST — main failure mode:** the "Small" criterion (stories too broad); "Estimable" and "Testable" are also frequent gaps, especially for aspirational/aesthetic requirements. See the evaluation ([`../evaluation/`](../evaluation/)) for the quantitative INVEST results.
- `_parse_json_response()` in `persona_identifier.py` strips markdown code fences (```json … ```) before parsing, because the LLM often wraps its JSON output.
- `processed_files.txt` in `PROCESSED_DIR` prevents reprocessing; delete it to reprocess a file.

## Troubleshooting

- **"ANTHROPIC_API_KEY not found":** make sure `.env` exists and the key is set.
- **No files processed:** check that the input directory actually contains `.txt` files.
- **Invalid JSON from the model:** handled automatically — the client retries (default 3 attempts).

## Author

Gabriel Ferreira Silva — TCC/PFC, Institute of Informatics, UFG (2026). See the [root README](../README.md) for the full project, results, and written work.
