# Projeto Final de Curso — IA Generativa e Engenharia de Software

**Autor:** Gabriel Ferreira Silva  
**Instituição:** UFG — Universidade Federal de Goiás  
**Fase atual:** PFC2 (em andamento)

Pipeline multi-agente que automatiza a elicitação de requisitos de software: parte de gravações de reuniões e produz documentos estruturados de requisitos (SRS IEEE 830, diagramas de domínio e histórias de usuário).

---

## Resultados PFC1 (validado no AMI Meeting Corpus — 7 reuniões)

- 100% de precisão na identificação de personas (28/28)
- 83% de conformidade INVEST nas histórias de usuário
- Nota 9/10 no framework qualitativo de avaliação

---

## Arquitetura

Quatro agentes especializados em pipeline sequencial, comunicando-se via sistema de arquivos:

```
Gravação de áudio
    ↓
[Agente 1] agente-transcricao/   — Whisper STT → .txt
    ↓
[Agente 2] agente-identificacao/ — Personas + User Stories → .json
    ↓
[Agente 3] agente-srs/           — SRS IEEE 830 + Casos de Uso → .md + .pdf
    ↓
[Agente 4] agente-diagramas/     — Diagrama de Domínio + Documento Final → .md + .pdf
```

Cada agente monitora o diretório de saída do anterior via watchdog e dispara automaticamente quando um novo arquivo aparece.

---

## Pré-requisitos

- **Python 3.11** (recomendado — 3.14 não tem wheels pré-compiladas para pydantic-core)
- **Chave de API Anthropic** (agentes 3 e 4)
- **Chave de API OpenAI** (agente 2)
- **Pandoc + xelatex** (opcional — para geração de PDF)
  - Pandoc: https://pandoc.org/installing.html
  - xelatex via MiKTeX: https://miktex.org/download

---

## Instalação

### 1. Instalar dependências de cada agente

Execute da raiz do projeto (`PFC1/`):

```powershell
foreach ($agent in @("agente-transcricao", "agente-identificacao", "agente-srs", "agente-diagramas")) {
    Write-Host "`n=== $agent ===" -ForegroundColor Cyan
    py -3.11 -m pip install -r "$agent\requirements.txt"
}
```

### 2. Configurar variáveis de ambiente

Execute da raiz do projeto para gerar todos os `.env` de uma vez (pede a chave uma única vez):

```powershell
$anthropic = Read-Host "ANTHROPIC_API_KEY"
$openai    = Read-Host "OPENAI_API_KEY"

@"
HUGGINGFACE_TOKEN=your_token_here
"@ | Set-Content agente-transcricao\.env -Encoding utf8

@"
OPENAI_API_KEY=$openai
OPENAI_MODEL=gpt-4o-mini
INPUT_DIR=../agente-transcricao/data/output
OUTPUT_DIR=./data/output
PROCESSED_DIR=./data/processed
CHECK_INTERVAL=5
MAX_RETRIES=3
"@ | Set-Content agente-identificacao\.env -Encoding utf8

@"
ANTHROPIC_API_KEY=$anthropic
ANTHROPIC_MODEL=claude-sonnet-4-6
INPUT_DIR=../agente-identificacao/data/output
OUTPUT_DIR=./data/output
PROCESSED_DIR=./data/processed
CHECK_INTERVAL=5
MAX_RETRIES=3
"@ | Set-Content agente-srs\.env -Encoding utf8

@"
ANTHROPIC_API_KEY=$anthropic
ANTHROPIC_MODEL=claude-sonnet-4-6
INPUT_DIR=../agente-srs/data/output
OUTPUT_DIR=./data/output
PROCESSED_DIR=./data/processed
CHECK_INTERVAL=5
MAX_RETRIES=3
"@ | Set-Content agente-diagramas\.env -Encoding utf8

Write-Host "Arquivos .env criados com sucesso."
```

---

## Como executar

### Agente 1 — Transcrição

```powershell
cd agente-transcricao

# Gravar pelo microfone e transcrever
py -3.11 src\main.py record

# Transcrever um arquivo de áudio existente
py -3.11 src\main.py transcribe-file caminho\do\audio.wav
```

**Saída:** `.txt` e `.json` em `agente-transcricao/data/output/`

---

### Agente 2 — Identificação de Personas

```powershell
cd agente-identificacao

# Processar um arquivo de transcrição
py -3.11 main.py --file "../agente-transcricao/data/output/transcricao.txt"

# Processar um diretório completo
py -3.11 main.py --dir "../agente-transcricao/data/output"

# Monitorar diretório automaticamente (modo contínuo)
py -3.11 main.py --monitor
```

**Saída:** `.json` em `agente-identificacao/data/output/` com personas e histórias de usuário.

---

### Agente 3 — SRS IEEE 830 + Casos de Uso

```powershell
cd agente-srs

# Processar um arquivo JSON do Agente 2
py -3.11 main.py --file "../agente-identificacao/data/output/meeting_X.json"

# Processar um diretório completo
py -3.11 main.py --dir "../agente-identificacao/data/output"

# Monitorar diretório automaticamente
py -3.11 main.py --monitor
```

**Saída:** `.md` e `.pdf` em `agente-srs/data/output/` com o documento SRS completo.

---

### Agente 4 — Diagrama de Domínio + Documento Final

```powershell
cd agente-diagramas

# Processar um arquivo JSON do Agente 2 (auto-descobre o SRS do Agente 3)
py -3.11 main.py --file "../agente-identificacao/data/output/meeting_X.json"

# Processar com SRS específico
py -3.11 main.py --file "../agente-identificacao/data/output/meeting_X.json" --srs-md "../agente-srs/data/output/meeting_X_srs.md"

# Monitorar diretório automaticamente
py -3.11 main.py --monitor
```

**Saída:** `.md` e `.pdf` em `agente-diagramas/data/output/` com o documento final unificado e diagrama de domínio PlantUML (renderizado via kroki.io).

---

### Executar Agentes 3 e 4 em sequência

```powershell
$file = "../agente-identificacao/data/output/meeting_X.json"
cd agente-srs; py -3.11 main.py --file $file; cd ../agente-diagramas; py -3.11 main.py --file $file
```

---

### Converter Markdown para PDF sem chamar o LLM

Útil para regenerar o PDF a partir de um `.md` já existente sem gastar tokens:

```powershell
pandoc "agente-srs\data\output\meeting_X_srs.md" `
  -o "agente-srs\data\output\meeting_X_srs.pdf" `
  --pdf-engine=xelatex `
  -V geometry:margin=2.5cm `
  -V lang=pt-BR
```

---

## Estrutura de diretórios

```
PFC1/
├── agente-transcricao/
│   ├── src/
│   │   ├── main.py           # CLI (record, transcribe-file)
│   │   ├── audio/record.py   # Captura de microfone
│   │   └── stt/transcribe.py # Wrapper faster-whisper
│   ├── data/output/          # Saída: .txt e .json
│   ├── requirements.txt
│   └── .env
│
├── agente-identificacao/
│   ├── main.py               # CLI (--file, --dir, --monitor)
│   ├── src/
│   │   ├── persona_identifier.py  # Orquestrador principal
│   │   ├── openai_client.py       # Wrapper OpenAI com retry
│   │   └── file_monitor.py        # Watchdog
│   ├── config/prompts.py          # Todos os prompts LLM
│   ├── data/output/               # Saída: .json
│   ├── requirements.txt
│   └── .env
│
├── agente-srs/
│   ├── main.py               # CLI (--file, --dir, --monitor)
│   ├── src/
│   │   ├── srs_processor.py       # Orquestrador
│   │   ├── srs_generator.py       # Geração via LLM
│   │   ├── anthropic_client.py    # Wrapper Anthropic com retry
│   │   ├── kroki_client.py        # Renderização PlantUML via kroki.io
│   │   ├── document_renderer.py   # Markdown → PDF
│   │   ├── file_monitor.py        # Watchdog
│   │   └── models.py              # Modelos Pydantic
│   ├── config/prompts.py          # Todos os prompts LLM
│   ├── templates/                 # Templates Jinja2
│   ├── data/output/               # Saída: .md e .pdf
│   ├── requirements.txt
│   └── .env
│
├── agente-diagramas/
│   ├── main.py               # CLI (--file, --dir, --monitor, --srs-md)
│   ├── src/
│   │   ├── diagrams_processor.py       # Orquestrador
│   │   ├── domain_diagram_generator.py # Extração de entidades + PlantUML via LLM
│   │   ├── document_assembler.py       # Montagem do documento final
│   │   ├── anthropic_client.py         # Wrapper Anthropic com retry
│   │   ├── kroki_client.py             # Renderização PlantUML via kroki.io
│   │   ├── document_renderer.py        # Markdown → PDF
│   │   ├── file_monitor.py             # Watchdog
│   │   └── models.py                   # Modelos Pydantic
│   ├── config/prompts.py               # Todos os prompts LLM
│   ├── templates/                      # Templates Jinja2
│   ├── data/output/                    # Saída: .md, .pdf e imagens PNG
│   ├── requirements.txt
│   └── .env
│
├── Documentation/            # Convenções e documentação do projeto
├── CLAUDE.md                 # Instruções para Claude Code
└── README.md
```

---

## Variáveis de ambiente

### agente-identificacao/.env

| Variável | Descrição | Padrão |
|---|---|---|
| `OPENAI_API_KEY` | Chave da API OpenAI | — |
| `OPENAI_MODEL` | Modelo OpenAI | `gpt-4o-mini` |
| `INPUT_DIR` | Diretório de entrada | `../agente-transcricao/data/output` |
| `OUTPUT_DIR` | Diretório de saída | `./data/output` |
| `PROCESSED_DIR` | Controle de arquivos processados | `./data/processed` |
| `CHECK_INTERVAL` | Intervalo do monitor (segundos) | `5` |
| `MAX_RETRIES` | Tentativas de retry na API | `3` |

### agente-srs/.env e agente-diagramas/.env

| Variável | Descrição | Padrão |
|---|---|---|
| `ANTHROPIC_API_KEY` | Chave da API Anthropic | — |
| `ANTHROPIC_MODEL` | Modelo Claude | `claude-sonnet-4-6` |
| `INPUT_DIR` | Diretório de entrada | varia por agente |
| `OUTPUT_DIR` | Diretório de saída | `./data/output` |
| `PROCESSED_DIR` | Controle de arquivos processados | `./data/processed` |
| `CHECK_INTERVAL` | Intervalo do monitor (segundos) | `5` |
| `MAX_RETRIES` | Tentativas de retry na API | `3` |

---

## Geração de PDF

Os agentes 3 e 4 tentam gerar PDF nesta ordem de prioridade:

1. **Pandoc + xelatex** (recomendado) — instale Pandoc e MiKTeX
2. **WeasyPrint + GTK3** (fallback) — instale o GTK3 Runtime para Windows

Se nenhum estiver disponível, o `.md` é gerado normalmente e o PDF pode ser convertido manualmente com o comando Pandoc acima.

---

## Dataset AMI

Os scripts `import_ami_dataset.py` e `investigate_ami.py` são utilitários exploratórios para acesso ao AMI Meeting Corpus via HuggingFace. Não fazem parte do pipeline principal. Para usá-los configure `HUGGINGFACE_TOKEN` no `.env` do `agente-transcricao` e `agente-identificacao`.
