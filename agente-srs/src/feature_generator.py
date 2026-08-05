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
        # Set per-run by generate(); "" when the user declared no acronyms.
        self.acronyms_block = ""

    def generate(
        self,
        agent2_output: Agent2Output,
        doc_meta: EmpresaDocumentMeta,
        include_nfr: bool = True,
        acronyms: str = "",
    ) -> FeatureRequirementsDocument:
        # User-declared acronyms become a context block in every prompt, so the LLM
        # spells them correctly instead of echoing a garbled transcription.
        self.acronyms_block = _acronyms_block(acronyms)

        print("[1/4] Gerando descrição da funcionalidade...")
        feature = self._generate_feature(agent2_output)

        print("[2/4] Gerando requisitos funcionais e regras de negócio...")
        functional_requirements = self._generate_functional_requirements(agent2_output)
        functional_requirements = _dedupe_requirements(functional_requirements)
        _renumber_requirements(functional_requirements)   # continuous RF1, RF2, ...
        business_rule_groups = self._generate_business_rules(agent2_output, feature.name)
        business_rule_groups = _dedupe_business_rules(business_rule_groups)
        _renumber_business_rules(business_rule_groups)  # continuous RN1, RN2, ...

        print("[3/4] Gerando casos de uso por persona...")
        use_cases = self._generate_use_cases(agent2_output)
        use_cases = _dedupe_use_cases(use_cases)
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
            acronyms_block=self.acronyms_block,
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.4)
        parsed = _parse_json(raw)
        return Feature(name=parsed["name"], description=parsed["description"])

    def _generate_functional_requirements(
        self, data: Agent2Output
    ) -> list[EmpresaFunctionalRequirement]:
        prompt = EMPRESA_FUNCTIONAL_REQUIREMENTS_PROMPT.format(
            user_stories=_all_stories_text(data),
            acronyms_block=self.acronyms_block,
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
            acronyms_block=self.acronyms_block,
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
            # Personas are processed one at a time, so the LLM cannot see what the
            # previous calls produced — pass the names so it does not repeat them.
            use_cases = self._generate_use_cases_for_persona(
                group, persona, uc_counter, existing=all_use_cases
            )
            all_use_cases.extend(use_cases)
            uc_counter += len(use_cases)

        return all_use_cases

    def _generate_use_cases_for_persona(
        self, group, persona, start_index: int, existing: list[EmpresaUseCase] | None = None
    ) -> list[EmpresaUseCase]:
        stories_text = "\n".join(
            f"[{s.id}] {s.historia} (prioridade: {s.prioridade})" for s in group.historias
        )
        prompt = EMPRESA_USE_CASES_PROMPT.format(
            persona_nome=group.persona_nome,
            persona_papel=persona.papel if persona else "",
            persona_contexto=persona.contexto if persona else "",
            stories=stories_text,
            start_index=start_index,
            acronyms_block=self.acronyms_block,
            existing_use_cases=_existing_use_cases_block(existing),
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
            acronyms_block=self.acronyms_block,
        )
        raw = self.client.generate_completion(prompt, SYSTEM_MESSAGE, temperature=0.3)
        parsed = _parse_json(raw)
        return [
            NonFunctionalRequirement(**rnf)
            for rnf in parsed.get("non_functional_requirements", [])
        ]


# ── Deduplication ─────────────────────────────────────────────────────────────
# The same topic often comes up at several points in a meeting ("we discussed X,
# moved on to Y, then went back to X"), which made the LLM emit near-identical
# blocks. The prompts ask for consolidation; these helpers are the safety net for
# whatever still slips through.

# Similarity above which two titles are considered the same item.
_DUPLICATE_THRESHOLD = 0.86


def _normalize_title(text: str) -> str:
    """Lowercase, strip accents/punctuation and drop filler words, so
    'Consultar saldo do orçamento' and 'Consulta de saldo orçamentário' compare close."""
    import re
    import unicodedata

    stripped = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    stripped = re.sub(r"[^\w\s]", " ", stripped).lower()
    stopwords = {"de", "da", "do", "das", "dos", "e", "o", "a", "os", "as",
                 "em", "no", "na", "para", "por", "com", "um", "uma"}
    words = [w for w in stripped.split() if w and w not in stopwords]
    return " ".join(sorted(words))


def _is_duplicate(a: str, b: str) -> bool:
    from difflib import SequenceMatcher

    na, nb = _normalize_title(a), _normalize_title(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= _DUPLICATE_THRESHOLD


def _dedupe_requirements(
    requirements: list[EmpresaFunctionalRequirement],
) -> list[EmpresaFunctionalRequirement]:
    """Drops functional requirements whose name repeats an earlier one, merging the
    detail text so no information is lost."""
    kept: list[EmpresaFunctionalRequirement] = []
    for rf in requirements:
        match = next((k for k in kept if _is_duplicate(k.name, rf.name)), None)
        if match is None:
            kept.append(rf)
            continue
        print(f"  [dedup] RF duplicado removido: '{rf.name}' (mesclado em '{match.name}')")
        # Keep the longer detail; append genuinely new text from the duplicate.
        if len(rf.detail) > len(match.detail):
            match.detail, rf.detail = rf.detail, match.detail
        if rf.detail and not _is_duplicate(rf.detail, match.detail):
            match.detail = f"{match.detail}\n\n{rf.detail}"
        if rf.comments and not match.comments:
            match.comments = rf.comments
    return kept


def _dedupe_business_rules(groups: list[BusinessRuleGroup]) -> list[BusinessRuleGroup]:
    """Merges groups with near-identical contexts and drops repeated rules
    (globally, since the same rule often lands in two different groups)."""
    merged: list[BusinessRuleGroup] = []
    for group in groups:
        match = next((m for m in merged if _is_duplicate(m.context, group.context)), None)
        if match is None:
            merged.append(group)
        else:
            print(f"  [dedup] Grupo de RN mesclado: '{group.context}' -> '{match.context}'")
            match.rules.extend(group.rules)

    seen: list[str] = []
    for group in merged:
        unique = []
        for rule in group.rules:
            if any(_is_duplicate(rule.name, s) for s in seen):
                print(f"  [dedup] RN duplicada removida: '{rule.name}'")
                continue
            seen.append(rule.name)
            unique.append(rule)
        group.rules = unique
    # A group can end up empty after deduplication — drop it.
    return [g for g in merged if g.rules]


def _dedupe_use_cases(use_cases: list[EmpresaUseCase]) -> list[EmpresaUseCase]:
    """Drops use cases that repeat an earlier one (same name AND same actor).

    The actor check matters: "Consultar Saldo" by an Operator and by a Manager are
    legitimately different use cases, so only same-actor repeats are removed.
    """
    kept: list[EmpresaUseCase] = []
    for uc in use_cases:
        duplicate = next(
            (
                k for k in kept
                if _is_duplicate(k.name, uc.name)
                and _normalize_title(k.actor) == _normalize_title(uc.actor)
            ),
            None,
        )
        if duplicate is None:
            kept.append(uc)
            continue
        print(f"  [dedup] Caso de uso duplicado removido: '{uc.name}' ({uc.actor})")
        # Preserve the richer description of the two.
        if len(uc.main_flow.steps) > len(duplicate.main_flow.steps):
            duplicate.main_flow = uc.main_flow
        if not duplicate.objective:
            duplicate.objective = uc.objective
    return kept


def _renumber_requirements(requirements: list[EmpresaFunctionalRequirement]) -> None:
    """Renumber functional requirements continuously (RF1, RF2, ...) after dedup."""
    for i, rf in enumerate(requirements, start=1):
        rf.id = f"RF{i}"


def _existing_use_cases_block(existing: list[EmpresaUseCase] | None) -> str:
    """Names of the use cases already generated for previous personas, so the next
    persona's prompt can avoid re-creating them. "" on the first call."""
    if not existing:
        return ""
    names = "\n".join(f"- {uc.name} (ator: {uc.actor})" for uc in existing)
    return (
        "\nCASOS DE USO JÁ CRIADOS para outras personas deste mesmo documento "
        "(NÃO os repita; se a história descrever a mesma interação já listada, "
        "simplesmente não gere um novo caso de uso):\n" + names + "\n"
    )


def _acronyms_block(acronyms: str) -> str:
    """Formats the user-declared acronyms as a prompt context block.

    Returns "" when the user declared none, so the prompt renders unchanged.
    """
    text = (acronyms or "").strip()
    if not text:
        return ""
    return (
        "\nSIGLAS E TERMOS DO DOMÍNIO declarados pelo usuário (grafia CORRETA). "
        "Use exatamente esta grafia no documento; se a transcrição trouxer uma "
        "variação parecida (erro de transcrição), trate como sendo esta sigla:\n"
        + text.strip()
        + "\n"
    )


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
