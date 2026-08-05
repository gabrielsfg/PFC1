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

DESCARTE trechos que NÃO tratam do projeto/problema. Uma reunião real contém muito conteúdo irrelevante
que não deve influenciar a análise nem aparecer no documento final:
- conversa fiada, saudações, despedidas, assuntos pessoais, piadas, comentários sobre clima/almoço/futebol;
- problemas técnicos da chamada ("está me ouvindo?", "travou", "caiu", "compartilha a tela", "liga a câmera");
- interrupções: alguém entra ou sai da sala/reunião, telefone tocando, alguém chamando outra pessoa,
  conversas paralelas com terceiros que não participam da reunião;
- pausas, esperas ("vamos aguardar o João entrar"), testes de áudio, avisos administrativos.
Ignore completamente esses trechos: eles não geram personas, nem necessidades, nem requisitos.

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
- NÃO crie histórias a partir de conversa fiada, saudações, interrupções (alguém entrando na sala,
  telefone), problemas técnicos da chamada ou assuntos pessoais — nada disso é necessidade do sistema.

- CONSOLIDAÇÃO (regra crítica): em reuniões reais o mesmo assunto é retomado várias vezes — discute-se
  um tema, passa-se a outro e depois VOLTA-SE ao primeiro. Isso NÃO significa que há duas necessidades.
  Cada necessidade distinta deve gerar UMA ÚNICA história, reunindo tudo o que foi dito sobre ela nos
  diferentes momentos da reunião.
- Antes de responder, releia todas as histórias que você criou: se duas descrevem o mesmo objetivo com
  palavras diferentes, ou se uma é caso particular da outra, FUNDA-AS em uma só. Isso vale também
  ENTRE personas diferentes — se a mesma necessidade serve a duas personas, atribua-a à persona mais
  adequada, sem repeti-la nas duas.
- Prefira menos histórias, mais completas, a muitas histórias parecidas.

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