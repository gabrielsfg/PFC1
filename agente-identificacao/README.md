# 🤖 Agente de Identificação de Personas

Agente inteligente que processa transcrições de áudio, identifica personas (participantes) e gera histórias de usuário usando LLM (OpenAI GPT).

## 📋 Funcionalidades

- ✅ Identificação automática de personas em transcrições
- ✅ Extração de características e contexto de cada persona
- ✅ Geração de histórias de usuário (user stories)
- ✅ Monitoramento automático de novos arquivos
- ✅ Processamento em lote
- ✅ Controle de arquivos já processados

## 🏗️ Estrutura do Projeto

```
agente-identificacao/
├── src/
│   ├── __init__.py
│   ├── persona_identifier.py    # Lógica principal de identificação
│   ├── openai_client.py         # Cliente OpenAI com retry
│   └── file_monitor.py          # Monitor de arquivos
├── config/
│   └── prompts.py               # Prompts otimizados para LLM
├── data/
│   ├── output/                  # Resultados JSON gerados
│   └── processed/               # Controle de arquivos processados
├── main.py                      # CLI principal
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Instalação

### 1. Instalar Dependências

```bash
cd C:\Users\gabri\Tcc\agente-identificacao
pip install -r requirements.txt
```

### 2. Configurar Ambiente

```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite o .env e adicione sua chave da OpenAI
notepad .env
```

Configuração mínima do `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
INPUT_DIR=../agente-transcricao/data/output
OUTPUT_DIR=./data/output
```

## 💻 Uso

### Modo Monitor (Recomendado)

Monitora automaticamente o diretório do agente-transcricao e processa novos arquivos:

```bash
python main.py --monitor
```

Saída esperada:
```
🚀 AGENTE DE IDENTIFICAÇÃO DE PERSONAS
📁 Monitorando: ..\agente-transcricao\data\output
📊 Modelo: gpt-4o-mini
⏱️  Intervalo de verificação: 5s
👀 Monitoramento ativo. Pressione Ctrl+C para parar.
```

### Processar Arquivo Único

```bash
python main.py --file ../agente-transcricao/data/output/transcricao.txt
```

### Processar Diretório Completo

```bash
python main.py --dir ../agente-transcricao/data/output
```

### Opções Avançadas

```bash
# Monitor com intervalo customizado
python main.py --monitor --check-interval 10

# Diretórios customizados
python main.py --monitor --input-dir ./custom/input --output-dir ./custom/output
```

## 📊 Formato de Saída

O agente gera arquivos JSON com a seguinte estrutura:

```json
{
  "metadata": {
    "arquivo_origem": "transcricao_20241208.txt",
    "data_processamento": "2024-12-08T20:30:00",
    "modelo_usado": "gpt-4o-mini"
  },
  "analise_personas": {
    "personas": [
      {
        "id": "persona_1",
        "nome": "João Silva",
        "papel": "Cliente",
        "caracteristicas": ["Interessado em produto X", "Trabalha na área Y"],
        "contexto": "Cliente buscando solução para problema Z",
        "trechos_relevantes": ["Eu preciso de...", "Meu problema é..."]
      }
    ],
    "resumo_conversa": "Conversa de vendas...",
    "tipo_interacao": "atendimento ao cliente"
  },
  "historias_usuario": {
    "user_stories": [
      {
        "persona_id": "persona_1",
        "persona_nome": "João Silva",
        "historias": [
          {
            "id": "story_1",
            "historia": "Como cliente, eu quero X para Y",
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

## 🔄 Fluxo de Integração

```
Agente Transcrição → data/output/transcricao.txt
                          ↓
        Agente Identificação (monitora)
                          ↓
        Identifica Personas + LLM
                          ↓
        Gera User Stories + LLM
                          ↓
    data/output/transcricao_personas_TIMESTAMP.json
```

## ⚙️ Configurações

### Variáveis de Ambiente (.env)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave da API OpenAI | *Obrigatório* |
| `OPENAI_MODEL` | Modelo a usar | `gpt-4o-mini` |
| `INPUT_DIR` | Diretório de entrada | `../agente-transcricao/data/output` |
| `OUTPUT_DIR` | Diretório de saída | `./data/output` |
| `PROCESSED_DIR` | Controle de processados | `./data/processed` |
| `CHECK_INTERVAL` | Intervalo de verificação (s) | `5` |
| `MAX_RETRIES` | Tentativas em caso de erro | `3` |

### Modelos Recomendados

- **gpt-4o-mini**: Rápido e econômico (recomendado)
- **gpt-4o**: Mais preciso, mais caro
- **gpt-4-turbo**: Alternativa balanceada

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY não encontrada"

```bash
# Verifique se o .env existe e está configurado
notepad .env
```

### Nenhum arquivo processado

```bash
# Verifique se há arquivos .txt no diretório de entrada
dir ..\agente-transcricao\data\output\*.txt
```

### Erro de JSON

O modelo pode ocasionalmente retornar JSON inválido. O sistema tem retry automático (3 tentativas).

## 📝 Desenvolvimento

### Modificar Prompts

Edite `config/prompts.py` para ajustar como o LLM identifica personas e cria user stories.

### Adicionar Novos Campos

Modifique os prompts em `config/prompts.py` e ajuste a estrutura esperada em `persona_identifier.py`.

## 🔐 Segurança

- ✅ Nunca faça commit do arquivo `.env`
- ✅ A chave da API nunca é logada
- ✅ Use variáveis de ambiente para credenciais

## 📄 Licença

[Adicione sua licença aqui]

## 👤 Autor

Gabriel - TCC Faculdade

---

**Status**: ✅ Em desenvolvimento
**Versão**: 1.0.0