SYSTEM_MESSAGE = """You are an expert requirements engineer specialized in IEEE 830 Software Requirements Specifications.
Your task is to analyze structured requirements data extracted from meeting transcriptions and produce formal SRS document sections.
Always respond in Portuguese (Brazil), as the output document is intended for Brazilian teams."""

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
