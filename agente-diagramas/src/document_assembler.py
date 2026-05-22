from __future__ import annotations
from pathlib import Path

from src.models import Agent2Output, DomainModel, FinalDocument


class DocumentAssembler:
    def assemble(
        self,
        agent2_output: Agent2Output,
        domain_model: DomainModel,
        srs_md_path: Path | None = None,
    ) -> FinalDocument:
        srs_content = None
        if srs_md_path and srs_md_path.exists():
            srs_content = srs_md_path.read_text(encoding="utf-8")

        return FinalDocument(
            metadata=agent2_output.metadata,
            conversation_summary=agent2_output.analise_personas.resumo_conversa,
            interaction_type=agent2_output.analise_personas.tipo_interacao,
            personas=agent2_output.analise_personas.personas,
            domain_model=domain_model,
            srs_markdown_path=str(srs_md_path) if srs_md_path else None,
            srs_content=srs_content,
        )
