import json
from pathlib import Path

from src.models import (
    Agent2Output,
    SRSDocument,
    SRSIntroduction,
    FunctionalRequirement,
    Definition,
    UseCase,
    UseCaseFlow,
    UseCaseDiagram,
)
from src.openai_client import OpenAIClient
from src.kroki_client import KrokiClient
from config.prompts import (
    SYSTEM_MESSAGE,
    INTRODUCTION_PROMPT,
    FUNCTIONAL_REQUIREMENTS_PROMPT,
    USE_CASES_PROMPT,
    PLANTUML_USECASE_PROMPT,
)


class SRSGenerator:
    def __init__(self, images_dir: Path):
        self.client = OpenAIClient()
        self.kroki = KrokiClient()
        self.images_dir = images_dir

    def generate(self, agent2_output: Agent2Output) -> SRSDocument:
        print("[1/3] Gerando introdução e requisitos funcionais...")
        introduction = self._generate_introduction(agent2_output)
        functional_requirements = self._generate_functional_requirements(agent2_output)

        print("[2/3] Gerando casos de uso por persona...")
        all_use_cases, diagrams = self._generate_use_cases(agent2_output)

        print("[3/3] Documento montado.")
        return SRSDocument(
            metadata=agent2_output.metadata,
            introduction=introduction,
            personas=agent2_output.analise_personas.personas,
            conversation_summary=agent2_output.analise_personas.resumo_conversa,
            interaction_type=agent2_output.analise_personas.tipo_interacao,
            functional_requirements=functional_requirements,
            user_stories=agent2_output.historias_usuario.user_stories,
            use_cases=all_use_cases,
            use_case_diagrams=diagrams,
        )

    def _generate_introduction(self, data: Agent2Output) -> SRSIntroduction:
        personas_summary = ", ".join(
            f"{p.nome} ({p.papel})" for p in data.analise_personas.personas
        )
        prompt = INTRODUCTION_PROMPT.format(
            conversation_summary=data.analise_personas.resumo_conversa,
            interaction_type=data.analise_personas.tipo_interacao,
            personas_summary=personas_summary,
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.4)
        parsed = _parse_json(raw)
        return SRSIntroduction(
            purpose=parsed["purpose"],
            system_scope=parsed["system_scope"],
            problem_statement=parsed["problem_statement"],
            product_perspective=parsed["product_perspective"],
            definitions=[Definition(**d) for d in parsed.get("definitions", [])],
        )

    def _generate_functional_requirements(self, data: Agent2Output) -> list[FunctionalRequirement]:
        stories_text = "\n".join(
            f"  [{s.id}] {s.historia} (prioridade: {s.prioridade})"
            for group in data.historias_usuario.user_stories
            for s in group.historias
        )
        prompt = FUNCTIONAL_REQUIREMENTS_PROMPT.format(user_stories=stories_text)
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.3)
        parsed = _parse_json(raw)
        return [FunctionalRequirement(**rf) for rf in parsed.get("functional_requirements", [])]

    def _generate_use_cases(
        self, data: Agent2Output
    ) -> tuple[list[UseCase], list[UseCaseDiagram]]:
        all_use_cases: list[UseCase] = []
        diagrams: list[UseCaseDiagram] = []
        uc_counter = 1
        total = len(data.historias_usuario.user_stories)

        for idx, group in enumerate(data.historias_usuario.user_stories, 1):
            persona = next(
                (p for p in data.analise_personas.personas if p.id == group.persona_id),
                None,
            )
            print(f"  [{idx}/{total}] Casos de uso: {group.persona_nome}")

            use_cases = self._generate_use_cases_for_persona(group, persona, uc_counter)
            all_use_cases.extend(use_cases)
            uc_counter += len(use_cases)

            plantuml = self._generate_plantuml(group.persona_nome, persona, use_cases)
            image_path = self._render_diagram(plantuml, group.persona_id)
            diagrams.append(UseCaseDiagram(
                persona_nome=group.persona_nome,
                plantuml_source=plantuml,
                image_path=str(image_path) if image_path else None,
            ))

        return all_use_cases, diagrams

    def _generate_use_cases_for_persona(self, group, persona, start_index: int) -> list[UseCase]:
        stories_text = "\n".join(
            f"[{s.id}] {s.historia} (prioridade: {s.prioridade})"
            for s in group.historias
        )
        prompt = USE_CASES_PROMPT.format(
            persona_nome=group.persona_nome,
            persona_papel=persona.papel if persona else "",
            persona_contexto=persona.contexto if persona else "",
            stories=stories_text,
            start_index=start_index,
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.4)
        parsed = _parse_json(raw)
        return [
            UseCase(
                id=uc["id"],
                name=uc["name"],
                actor=uc["actor"],
                preconditions=uc["preconditions"],
                postconditions=uc["postconditions"],
                main_flow=[UseCaseFlow(**s) for s in uc["main_flow"]],
                alternative_flows=uc.get("alternative_flows", []),
                exception_flows=uc.get("exception_flows", []),
                source_stories=uc.get("source_stories", []),
            )
            for uc in parsed.get("use_cases", [])
        ]

    def _generate_plantuml(self, persona_nome: str, persona, use_cases: list[UseCase]) -> str:
        uc_list = "\n".join(f"- {uc.id}: {uc.name}" for uc in use_cases)
        prompt = PLANTUML_USECASE_PROMPT.format(
            persona_nome=persona_nome,
            persona_papel=persona.papel if persona else "",
            use_cases_list=uc_list,
        )
        return self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.2)

    def _render_diagram(self, plantuml: str, persona_id: str) -> Path | None:
        output_path = self.images_dir / f"usecase_{persona_id}.png"
        try:
            self.kroki.render(plantuml, output_path)
            return output_path
        except Exception as e:
            print(f"    Aviso: falha ao renderizar diagrama ({e})")
            return None


def _parse_json(response: str) -> dict:
    cleaned = response.strip()
    for prefix in ("```json", "```"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())
