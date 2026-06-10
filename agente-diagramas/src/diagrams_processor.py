from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from src.models import Agent2Output
from src.domain_diagram_generator import DomainDiagramGenerator
from src.document_assembler import DocumentAssembler
from src.document_renderer import DocumentRenderer


class DiagramsProcessor:
    def __init__(self, output_dir: str = "./data/output", fmt: str = "ieee"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.fmt = fmt
        self.generator = DomainDiagramGenerator(self.images_dir)
        self.assembler = DocumentAssembler()
        self.renderer = DocumentRenderer()

    def process(self, json_path: Path, srs_md_path: Path | None = None) -> dict | None:
        """
        json_path: Agent 2 JSON output
        srs_md_path: Agent 3 Markdown output (optional — embedded in final document when provided)
        """
        print(f"\n{'='*60}")
        print(f"Processando: {json_path.name}")
        print(f"{'='*60}")

        # The "empresa" format has no domain/use-case diagrams: the Agent 3 document
        # is already the final deliverable, so Agent 4 is a no-op.
        if self.fmt == "empresa":
            print("Formato 'empresa' não requer o Agente 4 (documento já está completo). Pulando.")
            return {
                "skipped": True,
                "source": str(json_path),
                "markdown": str(srs_md_path) if srs_md_path else None,
                "pdf": None,
                "entities": 0,
                "relationships": 0,
            }

        agent2_output = self._load_input(json_path)
        if agent2_output is None:
            return None

        # Auto-discover SRS markdown if not provided: look in agente-srs/data/output
        if srs_md_path is None:
            srs_md_path = self._find_srs_markdown(json_path)
            if srs_md_path:
                print(f"SRS encontrado: {srs_md_path.name}")

        domain_model = self.generator.generate(agent2_output)
        document = self.assembler.assemble(agent2_output, domain_model, srs_md_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = f"{json_path.stem}_documento_final_{timestamp}"
        md_path = self.output_dir / f"{stem}.md"
        pdf_path = self.output_dir / f"{stem}.pdf"

        print("Renderizando Markdown...")
        self.renderer.render_markdown(document, md_path)
        print(f"  -> {md_path}")

        print("Renderizando PDF...")
        try:
            self.renderer.render_pdf(md_path, pdf_path)
            print(f"  -> {pdf_path}")
        except Exception as e:
            print(f"  Aviso: falha ao gerar PDF ({e})")
            pdf_path = None

        print("\nDocumento final gerado com sucesso!")
        return {
            "source": str(json_path),
            "markdown": str(md_path),
            "pdf": str(pdf_path) if pdf_path else None,
            "entities": len(domain_model.entities),
            "relationships": len(domain_model.relationships),
            "diagram_image": domain_model.image_path,
        }

    def process_directory(self, input_dir: Path) -> list[dict]:
        json_files = list(input_dir.glob("*.json"))
        if not json_files:
            print(f"Nenhum arquivo .json encontrado em {input_dir}")
            return []

        print(f"\nEncontrados {len(json_files)} arquivo(s) para processar\n")
        results = []
        for f in json_files:
            result = self.process(f)
            if result:
                results.append(result)

        print(f"\n{'='*60}")
        print(f"Concluído: {len(results)}/{len(json_files)} sucesso")
        print(f"{'='*60}\n")
        return results

    def _load_input(self, json_path: Path) -> Agent2Output | None:
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            return Agent2Output.model_validate(data)
        except Exception as e:
            print(f"Erro ao carregar {json_path.name}: {e}")
            return None

    def _find_srs_markdown(self, json_path: Path) -> Path | None:
        """Looks for the most recent SRS .md in agente-srs/data/output matching the same stem."""
        base_stem = json_path.stem
        srs_output = json_path.parent.parent.parent / "agente-srs" / "data" / "output"
        if not srs_output.exists():
            return None
        candidates = sorted(srs_output.glob(f"{base_stem}_srs_*.md"), reverse=True)
        return candidates[0] if candidates else None
