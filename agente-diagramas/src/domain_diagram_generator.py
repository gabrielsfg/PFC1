import json
from pathlib import Path

from src.models import (
    Agent2Output,
    DomainModel,
    DomainEntity,
    DomainAttribute,
    DomainRelationship,
)
from src.anthropic_client import AnthropicClient as OpenAIClient
from src.kroki_client import KrokiClient
from config.prompts import SYSTEM_MESSAGE, DOMAIN_ENTITIES_PROMPT, PLANTUML_CLASS_PROMPT


class DomainDiagramGenerator:
    def __init__(self, images_dir: Path):
        self.llm = OpenAIClient()
        self.kroki = KrokiClient()
        self.images_dir = images_dir

    def generate(self, agent2_output: Agent2Output) -> DomainModel:
        print("  [1/3] Extraindo entidades de domínio via LLM...")
        entities, relationships = self._extract_domain_model(agent2_output)

        print("  [2/3] Gerando diagrama PlantUML...")
        plantuml = self._generate_plantuml(entities, relationships)

        print("  [3/3] Renderizando diagrama via kroki.io...")
        image_path = self._render_diagram(plantuml)

        return DomainModel(
            entities=entities,
            relationships=relationships,
            plantuml_source=plantuml,
            image_path=str(image_path) if image_path else None,
        )

    def _extract_domain_model(
        self, data: Agent2Output
    ) -> tuple[list[DomainEntity], list[DomainRelationship]]:
        personas_summary = "\n".join(
            f"- {p.nome} ({p.papel}): {p.contexto}"
            for p in data.analise_personas.personas
        )
        stories_summary = "\n".join(
            f"  [{s.id}] {s.historia}"
            for group in data.historias_usuario.user_stories
            for s in group.historias
        )
        prompt = DOMAIN_ENTITIES_PROMPT.format(
            conversation_summary=data.analise_personas.resumo_conversa,
            interaction_type=data.analise_personas.tipo_interacao,
            personas_summary=personas_summary,
            stories_summary=stories_summary,
        )
        raw = self.llm.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.3)
        parsed = _parse_json(raw)

        entities = [
            DomainEntity(
                name=e["name"],
                attributes=[DomainAttribute(**a) for a in e.get("attributes", [])],
                methods=e.get("methods", []),
            )
            for e in parsed.get("entities", [])
        ]
        relationships = [DomainRelationship(**r) for r in parsed.get("relationships", [])]
        return entities, relationships

    def _generate_plantuml(
        self,
        entities: list[DomainEntity],
        relationships: list[DomainRelationship],
    ) -> str:
        domain_json = json.dumps(
            {
                "entities": [
                    {
                        "name": e.name,
                        "attributes": [{"name": a.name, "type": a.type} for a in e.attributes],
                        "methods": e.methods,
                    }
                    for e in entities
                ],
                "relationships": [
                    {
                        "from_entity": r.from_entity,
                        "to_entity": r.to_entity,
                        "label": r.label,
                        "cardinality": r.cardinality,
                    }
                    for r in relationships
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        prompt = PLANTUML_CLASS_PROMPT.format(domain_json=domain_json)
        return self.llm.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.2)

    def _render_diagram(self, plantuml: str) -> Path | None:
        output_path = self.images_dir / "domain_model.png"
        try:
            self.kroki.render(plantuml, output_path)
            return output_path
        except Exception as e:
            print(f"    Aviso: falha ao renderizar via kroki.io ({e})")
            return None


def _parse_json(response: str) -> dict:
    cleaned = response.strip()
    for prefix in ("```json", "```"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())
