from __future__ import annotations
import json

from src.models import (
    Agent2Output,
    EmpresaDocumentMeta,
    FeatureRequirementsDocument,
    Feature,
    EmpresaFunctionalRequirement,
    BusinessRule,
    BusinessRuleGroup,
    EmpresaFlow,
    EmpresaAltFlow,
    EmpresaUseCase,
    NonFunctionalRequirement,
)
from src.anthropic_client import AnthropicClient
from config.prompts import (
    SYSTEM_MESSAGE,
    FEATURE_DESCRIPTION_PROMPT,
    EMPRESA_FUNCTIONAL_REQUIREMENTS_PROMPT,
    BUSINESS_RULES_PROMPT,
    EMPRESA_USE_CASES_PROMPT,
    NON_FUNCTIONAL_REQUIREMENTS_PROMPT,
)


class FeatureRequirementsGenerator:
    """Builds the company "Documento de Requisitos" (SGG-GO) from Agent 2 output."""

    def __init__(self):
        self.client = AnthropicClient()

    def generate(
        self,
        agent2_output: Agent2Output,
        doc_meta: EmpresaDocumentMeta,
        include_nfr: bool = True,
    ) -> FeatureRequirementsDocument:
        print("[1/4] Gerando descrição da funcionalidade...")
        feature = self._generate_feature(agent2_output)

        print("[2/4] Gerando requisitos funcionais e regras de negócio...")
        functional_requirements = self._generate_functional_requirements(agent2_output)
        business_rule_groups = self._generate_business_rules(agent2_output, feature.name)
        _renumber_business_rules(business_rule_groups)  # continuous RN1, RN2, ...

        print("[3/4] Gerando casos de uso por persona...")
        use_cases = self._generate_use_cases(agent2_output)
        _renumber_use_cases(use_cases)  # continuous CSU1, CSU2, ...

        if include_nfr:
            print("[4/4] Gerando requisitos não-funcionais...")
            non_functional_requirements = self._generate_nfrs(agent2_output, feature.name)
        else:
            print("[4/4] Requisitos não-funcionais desativados (EMPRESA_INCLUDE_NFR=false).")
            non_functional_requirements = []

        print("Documento (formato empresa) montado.")
        return FeatureRequirementsDocument(
            document=doc_meta,
            feature=feature,
            functional_requirements=functional_requirements,
            business_rule_groups=business_rule_groups,
            use_cases=use_cases,
            non_functional_requirements=non_functional_requirements,
            metadata=agent2_output.metadata,
            project_notes=agent2_output.analise_personas.gestao_projeto,
        )

    def _generate_feature(self, data: Agent2Output) -> Feature:
        personas_summary = ", ".join(
            f"{p.nome} ({p.papel})" for p in data.analise_personas.personas
        )
        prompt = FEATURE_DESCRIPTION_PROMPT.format(
            conversation_summary=data.analise_personas.resumo_conversa,
            interaction_type=data.analise_personas.tipo_interacao,
            personas_summary=personas_summary,
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.4)
        parsed = _parse_json(raw)
        return Feature(name=parsed["name"], description=parsed["description"])

    def _generate_functional_requirements(
        self, data: Agent2Output
    ) -> list[EmpresaFunctionalRequirement]:
        prompt = EMPRESA_FUNCTIONAL_REQUIREMENTS_PROMPT.format(
            user_stories=_all_stories_text(data)
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.3)
        parsed = _parse_json(raw)
        return [
            EmpresaFunctionalRequirement(**rf)
            for rf in parsed.get("functional_requirements", [])
        ]

    def _generate_business_rules(
        self, data: Agent2Output, feature_name: str
    ) -> list[BusinessRuleGroup]:
        prompt = BUSINESS_RULES_PROMPT.format(
            feature_name=feature_name,
            user_stories=_all_stories_text(data),
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.3)
        parsed = _parse_json(raw)
        return [
            BusinessRuleGroup(
                context=g["context"],
                rules=[BusinessRule(**r) for r in g.get("rules", [])],
            )
            for g in parsed.get("business_rule_groups", [])
        ]

    def _generate_use_cases(self, data: Agent2Output) -> list[EmpresaUseCase]:
        all_use_cases: list[EmpresaUseCase] = []
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

        return all_use_cases

    def _generate_use_cases_for_persona(self, group, persona, start_index: int) -> list[EmpresaUseCase]:
        stories_text = "\n".join(
            f"[{s.id}] {s.historia} (prioridade: {s.prioridade})" for s in group.historias
        )
        prompt = EMPRESA_USE_CASES_PROMPT.format(
            persona_nome=group.persona_nome,
            persona_papel=persona.papel if persona else "",
            persona_contexto=persona.contexto if persona else "",
            stories=stories_text,
            start_index=start_index,
        )
        # Use cases per persona produce large JSON (main/alternative/exception flows),
        # so allow plenty of output tokens to avoid truncated/unterminated JSON.
        raw = self.client.generate_completion(
            prompt, SYSTEM_MESSAGE, temperature=0.4, max_tokens=16000
        )
        parsed = _parse_json(raw)

        use_cases: list[EmpresaUseCase] = []
        for uc in parsed.get("use_cases", []):
            main = uc.get("main_flow", {})
            if isinstance(main, list):  # tolerate the LLM returning a bare list of steps
                main = {"title": "", "steps": main}
            use_cases.append(
                EmpresaUseCase(
                    id=uc["id"],
                    name=uc["name"],
                    objective=uc.get("objective", ""),
                    actor=uc.get("actor", group.persona_nome),
                    preconditions=uc.get("preconditions", []),
                    postconditions=uc.get("postconditions", []),
                    main_flow=EmpresaFlow(
                        title=main.get("title", ""), steps=main.get("steps", [])
                    ),
                    alternative_flows=[
                        EmpresaAltFlow(**af) for af in uc.get("alternative_flows", [])
                    ],
                    exception_flows=[
                        EmpresaAltFlow(**ef) for ef in uc.get("exception_flows", [])
                    ],
                )
            )
        return use_cases

    def _generate_nfrs(
        self, data: Agent2Output, feature_name: str
    ) -> list[NonFunctionalRequirement]:
        prompt = NON_FUNCTIONAL_REQUIREMENTS_PROMPT.format(
            feature_name=feature_name,
            user_stories=_all_stories_text(data),
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.3)
        parsed = _parse_json(raw)
        return [
            NonFunctionalRequirement(**rnf)
            for rnf in parsed.get("non_functional_requirements", [])
        ]


def _renumber_business_rules(groups: list[BusinessRuleGroup]) -> None:
    """Renumber business rules continuously across all groups (RN1, RN2, ...),
    matching the model document (which does not restart per group)."""
    n = 1
    for group in groups:
        for rule in group.rules:
            rule.id = f"RN{n}"
            n += 1


def _renumber_use_cases(use_cases: list[EmpresaUseCase]) -> None:
    """Renumber use cases continuously as CSU1, CSU2, ... (the company doc uses 'CSU')."""
    for i, uc in enumerate(use_cases, start=1):
        uc.id = f"CSU{i}"


def _all_stories_text(data: Agent2Output) -> str:
    return "\n".join(
        f"  [{s.id}] {s.historia} (prioridade: {s.prioridade})"
        for group in data.historias_usuario.user_stories
        for s in group.historias
    )


def _parse_json(response: str) -> dict:
    cleaned = response.strip()
    for prefix in ("```json", "```"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())
