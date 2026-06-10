from __future__ import annotations
from pydantic import BaseModel


# ── Input models (Agent 2 JSON) ───────────────────────────────────────────────

class Metadata(BaseModel):
    arquivo_origem: str
    data_processamento: str
    modelo_usado: str


class Persona(BaseModel):
    id: str
    nome: str
    papel: str
    caracteristicas: list[str]
    contexto: str
    trechos_relevantes: list[str]


class MeetingParticipant(BaseModel):
    """Who actually spoke in the meeting — metadata only, NOT a system actor."""
    nome: str = ""
    papel_na_reuniao: str = ""


class ProjectNotes(BaseModel):
    """Short summary of project-management discussion (schedule, scope, EAP, ...).
    These are NOT software requirements; kept separate for traceability."""
    resumo: str = ""
    pontos: list[str] = []


class PersonaAnalysis(BaseModel):
    personas: list[Persona]
    resumo_conversa: str
    tipo_interacao: str
    # New (optional, backward-compatible with older Agent 2 JSON):
    participantes_reuniao: list[MeetingParticipant] = []
    gestao_projeto: ProjectNotes | None = None


class Story(BaseModel):
    id: str
    historia: str
    prioridade: str
    contexto: str
    trecho_base: str


class PersonaStories(BaseModel):
    persona_id: str
    persona_nome: str
    historias: list[Story]


class UserStoriesSection(BaseModel):
    user_stories: list[PersonaStories]


class Agent2Output(BaseModel):
    metadata: Metadata
    analise_personas: PersonaAnalysis
    historias_usuario: UserStoriesSection


# ── SRS sections ──────────────────────────────────────────────────────────────

class Definition(BaseModel):
    term: str
    definition: str


class SRSIntroduction(BaseModel):
    purpose: str
    system_scope: str
    problem_statement: str
    product_perspective: str
    definitions: list[Definition]


class FunctionalRequirement(BaseModel):
    id: str
    description: str
    source_stories: list[str]


# ── Use case sections ─────────────────────────────────────────────────────────

class UseCaseFlow(BaseModel):
    step: int
    description: str


class UseCase(BaseModel):
    id: str
    name: str
    actor: str
    preconditions: list[str]
    postconditions: list[str]
    main_flow: list[UseCaseFlow]
    alternative_flows: list[str]
    exception_flows: list[str]
    source_stories: list[str]


class UseCaseDiagram(BaseModel):
    persona_nome: str
    plantuml_source: str
    image_path: str | None = None


# ── Unified output document ───────────────────────────────────────────────────

class SRSDocument(BaseModel):
    metadata: Metadata
    introduction: SRSIntroduction
    personas: list[Persona]
    conversation_summary: str
    interaction_type: str
    functional_requirements: list[FunctionalRequirement]
    user_stories: list[PersonaStories]
    use_cases: list[UseCase]
    use_case_diagrams: list[UseCaseDiagram]


# ── "Empresa" document format (SGG-GO "Documento de Requisitos") ──────────────
# Output models for the alternative, company-specific template. Field names match
# templates/feature_requirements.md.j2 exactly.

class VersionEntry(BaseModel):
    date: str
    version: str
    description: str
    authors: str


class EmpresaDocumentMeta(BaseModel):
    """Document-level metadata that is NOT derivable from the audio.
    Filled with placeholders for now; meant to be collected via the GUI later."""
    project_code: str
    client: str
    product: str
    phase: str
    version: str
    version_history: list[VersionEntry]
    # Optional human-friendly document title. When set, it is used as the H1 title
    # (instead of the "code – client – product – phase" line). Collected via the GUI.
    title: str = ""


class Feature(BaseModel):
    name: str
    description: str


class EmpresaFunctionalRequirement(BaseModel):
    id: str                       # e.g. "RF1"
    name: str
    screen: str | None = None     # "Tela" — left as placeholder (not derived from audio)
    detail: str                   # "Detalhamento"
    comments: str | None = None   # "Comentários"


class BusinessRule(BaseModel):
    id: str                       # e.g. "RN01"
    name: str
    detail: str


class BusinessRuleGroup(BaseModel):
    context: str
    rules: list[BusinessRule]


class EmpresaFlow(BaseModel):
    title: str = ""
    steps: list[str]


class EmpresaAltFlow(BaseModel):
    id: str                       # e.g. "FA001" / "FE001"
    title: str = ""
    condition: str = ""
    steps: list[str]


class EmpresaUseCase(BaseModel):
    id: str                       # e.g. "UC001"
    name: str
    objective: str
    actor: str
    preconditions: list[str]
    postconditions: list[str]
    main_flow: EmpresaFlow
    alternative_flows: list[EmpresaAltFlow] = []
    exception_flows: list[EmpresaAltFlow] = []


class NonFunctionalRequirement(BaseModel):
    id: str                       # e.g. "RNF1"
    name: str
    category: str
    description: str
    acceptance_criteria: str


class FeatureRequirementsDocument(BaseModel):
    document: EmpresaDocumentMeta
    feature: Feature
    functional_requirements: list[EmpresaFunctionalRequirement]
    business_rule_groups: list[BusinessRuleGroup]
    use_cases: list[EmpresaUseCase]
    non_functional_requirements: list[NonFunctionalRequirement]
    metadata: Metadata            # carried through from Agent 2 for traceability
    project_notes: ProjectNotes | None = None  # short project-management summary (separate section)
