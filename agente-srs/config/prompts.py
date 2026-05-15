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
