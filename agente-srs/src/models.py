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


class PersonaAnalysis(BaseModel):
    personas: list[Persona]
    resumo_conversa: str
    tipo_interacao: str


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
