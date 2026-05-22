SYSTEM_MESSAGE = """Você é um especialista em análise de transcrições de áudio e identificação de personas.
Sua tarefa é analisar transcrições de conversas e identificar claramente quem são os participantes (personas) envolvidos.

Para cada persona identificada, você deve extrair:
- Nome ou identificador
- Papel/função na conversa
- Características relevantes mencionadas
- Contexto de suas falas

Seja preciso e objetivo na identificação."""


PERSONA_IDENTIFICATION_PROMPT = """Analise a seguinte transcrição de áudio e identifique todas as personas (participantes) envolvidos na conversa.

TRANSCRIÇÃO:
{transcription}

Para cada persona identificada, forneça as seguintes informações em formato JSON:

{{
  "personas": [
    {{
      "id": "persona_1",
      "nome": "Nome ou identificador da pessoa",
      "papel": "Função ou papel na conversa (ex: entrevistador, cliente, vendedor)",
      "caracteristicas": ["característica 1", "característica 2"],
      "contexto": "Breve contexto sobre a participação dessa pessoa",
      "trechos_relevantes": ["Trecho 1 onde a pessoa fala", "Trecho 2 onde a pessoa fala"]
    }}
  ],
  "resumo_conversa": "Breve resumo do contexto geral da conversa",
  "tipo_interacao": "Tipo de interação (ex: entrevista, reunião, atendimento ao cliente, etc.)"
}}

Seja preciso e baseie-se apenas nas informações presentes na transcrição.
Retorne APENAS o JSON, sem texto adicional antes ou depois."""


USER_STORIES_PROMPT = """Com base nas personas identificadas, crie histórias de usuário (user stories)
para cada persona seguindo os critérios INVEST (Independente, Negociável, Valiosa, Estimável, Pequena e Testável).

PERSONAS IDENTIFICADAS:
{personas_json}

Para cada persona, crie histórias de usuário no formato:
"Como [persona], eu quero [objetivo] para [benefício/razão]"

Retorne em formato JSON:

{{
  "user_stories": [
    {{
      "persona_id": "persona_1",
      "persona_nome": "Nome da persona",
      "historias": [
        {{
          "id": "story_1",
          "historia": "Como [persona], eu quero [objetivo] para [benefício]",
          "prioridade": "alta|média|baixa",
          "contexto": "Contexto adicional da história",
          "trecho_base": "Trecho da transcrição que originou esta história"
        }}
      ]
    }}
  ]
}}

Retorne APENAS o JSON, sem texto adicional."""


def get_identification_prompt(transcription: str) -> str:
    """Retorna o prompt formatado para identificação de personas"""
    return PERSONA_IDENTIFICATION_PROMPT.format(transcription=transcription)


def get_user_stories_prompt(personas_json: str, transcription: str = "") -> str:
    """Retorna o prompt formatado para criação de user stories"""
    return USER_STORIES_PROMPT.format(personas_json=personas_json)