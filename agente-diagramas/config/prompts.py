SYSTEM_MESSAGE = """You are an expert software architect specialized in domain modeling (DDD) and UML class diagrams.
Your task is to extract domain entities and relationships from software requirements gathered in meeting transcriptions.
Entity and attribute names must be in PascalCase/camelCase as appropriate for code.
When generating PlantUML, output only valid PlantUML syntax — no explanation, no markdown fences."""

DOMAIN_ENTITIES_PROMPT = """Analyze the requirements below and extract the domain model: entities, attributes, methods, and relationships.

Meeting summary: {conversation_summary}
Interaction type: {interaction_type}

Personas (stakeholders):
{personas_summary}

User stories:
{stories_summary}

Rules:
- Identify concrete domain entities (nouns that represent persistent concepts, not UI screens or actors)
- Each entity needs at least 2 meaningful attributes with simple types (String, Integer, Boolean, Date, etc.)
- Methods should be domain operations (verbs), not CRUD
- Relationships: use "association", "aggregation", "composition", or "dependency"
- Cardinality: "1", "*", "0..1", "1..*"
- Aim for 4–8 entities; do not over-engineer

Return JSON exactly:
{{
  "entities": [
    {{
      "name": "EntityName",
      "attributes": [{{"name": "attrName", "type": "String"}}],
      "methods": ["methodName()"]
    }}
  ],
  "relationships": [
    {{
      "from_entity": "EntityA",
      "to_entity": "EntityB",
      "label": "label",
      "cardinality": "*"
    }}
  ]
}}"""

PLANTUML_CLASS_PROMPT = """Generate a PlantUML class diagram for the domain model below.

Entities and relationships:
{domain_json}

Rules:
- Use standard UML class notation with attributes and methods sections
- Represent relationships with UML arrows: -- (association), o-- (aggregation), *-- (composition), ..> (dependency)
- Add cardinality labels on both ends where relevant
- Use left to right layout: add "left to right direction" after @startuml
- Output only raw PlantUML starting with @startuml and ending with @enduml"""
