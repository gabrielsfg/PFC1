SYSTEM_MESSAGE = """You are an expert requirements engineer specialized in IEEE 830 Software Requirements Specifications and UML use case modeling.
Your task is to analyze structured requirements data extracted from meeting transcriptions and produce formal SRS document sections.
Always respond in Portuguese (Brazil), as the output document is intended for Brazilian teams.
When generating PlantUML, output only valid PlantUML syntax — no explanation, no markdown fences."""

INTRODUCTION_PROMPT = """Based on the following meeting analysis, write the introduction and general description sections of an IEEE 830 SRS document in Portuguese (Brazil).

Meeting data:
- Summary: {conversation_summary}
- Interaction type: {interaction_type}
- Identified personas: {personas_summary}

Return a JSON with the following fields:
{{
  "purpose": "purpose of this document in 2-3 sentences",
  "system_scope": "what the system does and explicitly what it does NOT do",
  "problem_statement": "3-5 sentences describing the context, the problem, and why automation is needed",
  "product_perspective": "how this system fits into the broader context",
  "definitions": [{{"term": "term", "definition": "definition"}}]
}}"""

FUNCTIONAL_REQUIREMENTS_PROMPT = """Based on the following user stories, extract and normalize a list of functional requirements in IEEE 830 format. Write all requirement descriptions in Portuguese (Brazil).

User stories:
{user_stories}

Rules:
- Each requirement must be atomic (one behavior per requirement)
- Use the format: "O sistema deve [verbo] [objeto] [condição]"
- Number them RF001, RF002, etc.
- Group related stories into a single requirement when appropriate
- Do NOT duplicate requirements

Return a JSON:
{{
  "functional_requirements": [
    {{
      "id": "RF001",
      "description": "O sistema deve...",
      "source_stories": ["story_1", "story_2"]
    }}
  ]
}}"""

USE_CASES_PROMPT = """Based on the user stories below, generate structured use cases in Portuguese (Brazil) following UML best practices.

Persona: {persona_nome} ({persona_papel})
Context: {persona_contexto}

User stories:
{stories}

Rules:
- Create one use case per distinct system interaction (group closely related stories if they represent the same action)
- Each use case must have a clear, action-oriented name (verb + object, e.g. "Registrar Ponto")
- Main flow must be numbered steps describing the happy path
- Alternative flows: deviations that still succeed
- Exception flows: error conditions and system responses
- Keep each step atomic and in active voice ("O sistema exibe...", "O usuário seleciona...")
- IDs start at UC{start_index:03d}

Return JSON exactly:
{{
  "use_cases": [
    {{
      "id": "UC001",
      "name": "Nome do Caso de Uso",
      "actor": "{persona_nome}",
      "preconditions": ["..."],
      "postconditions": ["..."],
      "main_flow": [{{"step": 1, "description": "..."}}],
      "alternative_flows": ["FA1: ..."],
      "exception_flows": ["FE1: ..."],
      "source_stories": ["US001"]
    }}
  ]
}}"""

PLANTUML_USECASE_PROMPT = """Generate a PlantUML use case diagram for the persona and use cases below.

Persona (actor): {persona_nome} — {persona_papel}
Use cases:
{use_cases_list}

Rules:
- Use standard UML use case notation: actor on the left, system boundary rectangle labeled "Sistema"
- Each use case is an oval labeled with its name
- Connect actor to each use case with a line
- Use <<include>> only when one use case always includes another
- Use <<extend>> only when one use case optionally extends another
- Output only raw PlantUML starting with @startuml and ending with @enduml"""


# ── "Empresa" format prompts (SGG-GO "Documento de Requisitos") ───────────────
# These build the alternative company document. Output is always Portuguese (Brazil).
# They reuse SYSTEM_MESSAGE above.

FEATURE_DESCRIPTION_PROMPT = """Com base na análise de reunião abaixo, escreva, em português (Brasil),
o nome e a descrição da FUNCIONALIDADE principal discutida, no estilo de um "Documento de Requisitos"
corporativo.

Dados da reunião:
- Resumo: {conversation_summary}
- Tipo de interação: {interaction_type}
- Personas identificadas: {personas_summary}

Retorne um JSON:
{{
  "name": "nome curto e objetivo da funcionalidade (ex.: 'Manutenção de Saldo Orçamentário')",
  "description": "1 a 3 parágrafos descrevendo o objetivo da funcionalidade. Este texto também servirá de base para a modelagem de dados."
}}"""

EMPRESA_FUNCTIONAL_REQUIREMENTS_PROMPT = """Com base nas histórias de usuário abaixo, gere a lista de
REQUISITOS FUNCIONAIS no formato de um "Documento de Requisitos" corporativo, em português (Brasil).

Histórias de usuário:
{user_stories}

Regras:
- Descreva cada requisito de forma MACRO (a funcionalidade específica), não atômica.
- CONSOLIDE: agrupe histórias que descrevem a MESMA capacidade do sistema em um único requisito denso,
  evitando fragmentar uma funcionalidade em vários RF. Prefira menos requisitos, porém mais completos.
  Não há número fixo — gere quantos forem necessários para cobrir o núcleo funcional, sem repetir.
- Inclua APENAS requisitos de COMPORTAMENTO DO SOFTWARE (o que o sistema deve fazer). EXCLUA discussões de
  gestão de projeto e atividades da equipe: priorização de escopo, EAP, cronograma, negociação de prazos,
  alocação de pessoas, reuniões de validação, mapeamento de código, transferência de conhecimento. Se um item
  descreve uma atividade humana de processo (não um comportamento do sistema), NÃO o liste como requisito.
- Cada requisito tem um nome em CAIXA ALTA curto e um detalhamento claro e resumido.
- Numere RF1, RF2, RF3, ... (sem zeros à esquerda).
- "comments" é opcional (observações, restrições, validações de acesso); use "" quando não houver.
- NÃO invente telas/imagens; o campo de tela é preenchido depois por uma pessoa.

Retorne um JSON:
{{
  "functional_requirements": [
    {{
      "id": "RF1",
      "name": "NOME DO REQUISITO",
      "detail": "Detalhamento do requisito funcional.",
      "comments": "Observações, restrições ou comentários relevantes (ou \\"\\")"
    }}
  ]
}}"""

BUSINESS_RULES_PROMPT = """Com base no contexto da funcionalidade e nas histórias de usuário abaixo,
derive as REGRAS DE NEGÓCIO em português (Brasil), agrupadas por contexto.

Funcionalidade: {feature_name}
Histórias de usuário:
{user_stories}

Regras:
- Considere APENAS regras de negócio do SOFTWARE (validações, restrições, comportamentos condicionais).
  EXCLUA discussões de gestão de projeto/processo (cronograma, EAP, prazos, alocação, reuniões, mapeamento
  de código, transferência de conhecimento) — isso não é regra de negócio do sistema.
- Agrupe as regras por contexto (ex.: "Regras de uso – <assunto>").
- Numere as regras como RN01, RN02, ... dentro de cada grupo (a numeração final contínua é ajustada depois).
- Cada regra tem um nome curto e um detalhamento claro.
- Se a reunião não deixar regras explícitas, infira regras plausíveis e conservadoras a partir do contexto.

Retorne um JSON:
{{
  "business_rule_groups": [
    {{
      "context": "Regras de uso – <assunto>",
      "rules": [
        {{ "id": "RN01", "name": "Nome da regra", "detail": "Descrição da regra de negócio." }}
      ]
    }}
  ]
}}"""

EMPRESA_USE_CASES_PROMPT = """Com base nas histórias de usuário abaixo, gere CASOS DE USO em português
(Brasil) seguindo boas práticas de UML, para um "Documento de Requisitos" corporativo.

Persona: {persona_nome} ({persona_papel})
Contexto: {persona_contexto}

Histórias de usuário:
{stories}

Regras:
- O ATOR de cada caso de uso é a PERSONA DO SISTEMA (usuário do software), não um participante da reunião.
- Crie casos de uso APENAS para interações com o SOFTWARE. EXCLUA atividades de gestão de projeto/processo
  (priorização de escopo, EAP, prazos, reuniões, mapeamento de código, transferência de conhecimento).
- Crie um caso de uso por interação distinta com o sistema (agrupe histórias muito próximas).
- Cada caso de uso tem: objetivo, ator, pré-condições, pós-condições, fluxo principal numerado e,
  quando fizer sentido, fluxos alternativos (FA001, FA002, ...) e de exceção (FE001, FE002, ...).
- Fluxos alternativos/exceção descrevem a condição de desvio ("Se no passo X ...") e os passos.
- Passos atômicos, em voz ativa ("O sistema exibe...", "O usuário seleciona...").
- IDs dos casos de uso começam em UC{start_index:03d}.

Retorne EXATAMENTE este JSON:
{{
  "use_cases": [
    {{
      "id": "UC001",
      "name": "Nome do Caso de Uso",
      "objective": "Objetivo do caso de uso",
      "actor": "{persona_nome}",
      "preconditions": ["..."],
      "postconditions": ["..."],
      "main_flow": {{ "title": "Título do fluxo", "steps": ["Passo 1", "Passo 2"] }},
      "alternative_flows": [
        {{ "id": "FA001", "title": "Título", "condition": "Se no passo X ...", "steps": ["..."] }}
      ],
      "exception_flows": [
        {{ "id": "FE001", "title": "Título", "condition": "Se no passo X ...", "steps": ["..."] }}
      ]
    }}
  ]
}}"""

NON_FUNCTIONAL_REQUIREMENTS_PROMPT = """Com base no contexto da funcionalidade e nas histórias de
usuário abaixo, derive os REQUISITOS NÃO-FUNCIONAIS em português (Brasil).

Funcionalidade: {feature_name}
Histórias de usuário:
{user_stories}

Regras:
- Numere RNF1, RNF2, ... (sem zeros à esquerda).
- Cada requisito tem nome, categoria (Desempenho / Segurança / Usabilidade / Disponibilidade / etc.),
  descrição e critério de aceitação (como será validado).
- Se a reunião não deixar requisitos explícitos, infira requisitos plausíveis e conservadores.

Retorne um JSON:
{{
  "non_functional_requirements": [
    {{
      "id": "RNF1",
      "name": "Nome do requisito",
      "category": "Desempenho",
      "description": "Descrição do requisito não-funcional.",
      "acceptance_criteria": "Como será validado."
    }}
  ]
}}"""
