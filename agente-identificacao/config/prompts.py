SYSTEM_MESSAGE = """Você é um especialista em engenharia de requisitos e análise de reuniões de elicitação.
Sua tarefa é analisar a transcrição de uma reunião e separar claramente DOIS conceitos:

1. PERSONAS / ATORES DO SISTEMA: os perfis de usuário que vão USAR o software discutido
   (ex.: Administrador, Operador, Cliente, Gestor, Usuário do órgão). Você os infere a partir das
   funcionalidades descritas, MESMO que essas pessoas não estejam presentes na reunião.
2. PARTICIPANTES DA REUNIÃO: as pessoas que efetivamente falaram (equipe do projeto: analistas,
   desenvolvedores, gerente de projeto, prototipador). Servem apenas como metadado de rastreabilidade
   e NÃO são as personas do sistema — a menos que sejam, claramente, também usuárias do software.

Os requisitos e casos de uso derivados depois serão escritos do ponto de vista das PERSONAS (atores do sistema).
Seja preciso e baseie-se apenas na transcrição."""


PERSONA_IDENTIFICATION_PROMPT = """Analise a transcrição de reunião abaixo e produza a análise de personas
do SISTEMA que está sendo discutido.

TRANSCRIÇÃO:
{transcription}

IMPORTANTE — distinga DOIS conceitos:
- "personas": os ATORES / USUÁRIOS DO SISTEMA (perfis que vão usar o software), inferidos das
  funcionalidades discutidas (ex.: "Operador de Orçamento", "Gestor", "Administrador", "Usuário do órgão").
  Mesmo que essas pessoas não estejam presentes na reunião. NÃO use os nomes dos participantes da reunião
  como personas (a não ser que sejam, claramente, também usuários do sistema). Identifique de 2 a 6 atores
  distintos, consolidando perfis semelhantes.
- "participantes_reuniao": as pessoas que efetivamente FALARAM na reunião (equipe do projeto). Apenas metadado.

Separe também, de forma RESUMIDA, as DISCUSSÕES DE GESTÃO DE PROJETO (cronograma, EAP, prazos, alocação de
equipe, reuniões de validação, priorização de escopo, mapeamento de código, transferência de conhecimento)
no campo "gestao_projeto" — essas discussões NÃO são requisitos do software, mas devem ser registradas à parte.

Retorne em formato JSON:

{{
  "personas": [
    {{
      "id": "persona_1",
      "nome": "Nome do ATOR DO SISTEMA (ex.: Operador de Orçamento)",
      "papel": "Perfil/função de uso no sistema",
      "caracteristicas": ["característica relevante 1", "característica 2"],
      "contexto": "Como esse ator usa o sistema e quais necessidades tem",
      "trechos_relevantes": ["Trecho da transcrição que evidencia esse ator/necessidade"]
    }}
  ],
  "participantes_reuniao": [
    {{ "nome": "Nome de quem falou", "papel_na_reuniao": "ex.: analista de negócio, desenvolvedor, gerente de projeto" }}
  ],
  "resumo_conversa": "Resumo do contexto geral e do sistema/funcionalidade discutidos",
  "tipo_interacao": "Tipo de interação (ex.: reunião de levantamento de requisitos)",
  "gestao_projeto": {{
    "resumo": "1 a 3 frases resumindo as decisões/ações de gestão do projeto (não são requisitos)",
    "pontos": ["ponto principal 1", "ponto principal 2"]
  }}
}}

Seja preciso e baseie-se apenas na transcrição.
Retorne APENAS o JSON, sem texto adicional antes ou depois."""


USER_STORIES_PROMPT = """Com base nas PERSONAS DO SISTEMA (atores) abaixo, crie histórias de usuário
(user stories) seguindo os critérios INVEST (Independente, Negociável, Valiosa, Estimável, Pequena e Testável).

PERSONAS (ATORES DO SISTEMA):
{personas_json}

Para cada persona (ator do sistema), crie histórias no formato:
"Como [ator do sistema], eu quero [objetivo no sistema] para [benefício/razão]"

REGRAS IMPORTANTES:
- Escreva do ponto de vista do ATOR DO SISTEMA (use o campo "personas", NÃO os "participantes_reuniao").
- Inclua APENAS necessidades de COMPORTAMENTO DO SOFTWARE. NÃO crie histórias sobre gestão de projeto
  (cronograma, EAP, prazos, alocação de equipe, reuniões, mapeamento de código, transferência de conhecimento).
- Consolide histórias redundantes; foque no que o sistema deve fazer para cada ator.

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