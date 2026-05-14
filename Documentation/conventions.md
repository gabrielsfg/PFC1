# Project Conventions

## Language

All code must be written in English. This applies to:
- Variable, function, method, and class names
- File names (except agent folder names: `agente-srs/`, `agente-casos-de-uso/`, `agente-diagramas/`)
- Pydantic model fields and Enum values
- Jinja2 template variable names
- Dictionary keys created in code (not keys from external JSON — those stay as-is)
- Comments and docstrings
- Test function and fixture names

Portuguese is allowed only in:
- String content sent to the LLM (prompts, user-facing messages)
- Generated document content (SRS, user stories, use cases)
- Commit messages and PR descriptions (either language is fine)

## Architecture — Layered Service Pattern

Each agent follows the same three-layer structure:

```
main.py                   # Entry point: CLI arg parsing only, delegates immediately
src/
  models.py               # Pydantic models for input and output data
  <agent>_processor.py    # Orchestrator: coordinates the pipeline steps
  <agent>_generator.py    # Business logic: LLM calls, data transformation
  file_monitor.py         # Watchdog-based directory watcher
  document_renderer.py    # (formatting agents only) Jinja2 + PDF rendering
config/
  prompts.py              # All prompt strings and template functions, nothing else
templates/
  *.md.j2                 # Jinja2 templates for document sections
```

### Layer responsibilities

**`main.py`** — parses CLI args and calls the processor. No business logic.

**`models.py`** — Pydantic models only. Two groups per agent:
- Input models: represent the JSON received from the previous agent
- Output models: represent the data this agent produces

**`<agent>_processor.py`** — the orchestrator. Knows the sequence of steps, calls the generator and renderer, handles file I/O, tracks processed files. Does not contain LLM or rendering logic directly.

**`<agent>_generator.py`** — calls the LLM, parses responses, transforms data. No file I/O.

**`file_monitor.py`** — watchdog handler. Calls the processor when a new file is detected. Copy the pattern from `agente-identificacao/src/file_monitor.py`.

**`config/prompts.py`** — prompt strings and functions that build prompts. No imports from `src/`.

### Naming conventions

| What | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase | `SRSGenerator`, `FileMonitor` |
| Functions / methods | snake_case | `process_file`, `render_pdf` |
| Private methods | leading underscore | `_parse_json_response` |
| Constants | UPPER_SNAKE_CASE | `SYSTEM_MESSAGE`, `MAX_RETRIES` |
| Files | snake_case | `srs_generator.py`, `document_renderer.py` |
| Pydantic models (input) | suffix with context | `Agent2Output`, `Persona`, `Historia` |
| Pydantic models (output) | descriptive noun | `SRSDocument`, `RequisitoFuncional` |

### Error handling

- Use `try/except` only in the generator layer (LLM calls can fail).
- Let Pydantic validation errors propagate — they indicate a schema mismatch that must be fixed.
- Log errors with `print()` for now (same pattern as existing agents). Do not swallow exceptions silently.

### JSON parsing from LLM responses

Always strip markdown code fences before parsing — LLM responses frequently wrap JSON in ```json blocks. Use this pattern (already in `agente-identificacao`):

```python
def _parse_json_response(self, response: str) -> dict:
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())
```

### Processed files tracking

Each agent keeps a `processed_files.txt` in `PROCESSED_DIR` to avoid reprocessing. Delete this file to reprocess all inputs.

### Environment variables

Each agent has its own `.env` (from `.env.example`). Variables follow UPPER_SNAKE_CASE. `INPUT_DIR` always points to the output directory of the previous agent.
