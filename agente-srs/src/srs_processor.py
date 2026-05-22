from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from src.models import Agent2Output
from src.srs_generator import SRSGenerator
from src.document_renderer import DocumentRenderer


class SRSProcessor:
    def __init__(self, output_dir: str = "./data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.generator = SRSGenerator(self.images_dir)
        self.renderer = DocumentRenderer()

    def process(self, json_path: Path) -> dict | None:
        print(f"\n{'='*60}")
        print(f"Processando: {json_path.name}")
        print(f"{'='*60}")

        agent2_output = self._load_input(json_path)
        if agent2_output is None:
            return None

        document = self.generator.generate(agent2_output)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = f"{json_path.stem}_srs_{timestamp}"
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

        print("\nSRS gerado com sucesso!")
        return {
            "source": str(json_path),
            "markdown": str(md_path),
            "pdf": str(pdf_path) if pdf_path else None,
            "functional_requirements": len(document.functional_requirements),
            "use_cases": len(document.use_cases),
            "diagrams": len(document.use_case_diagrams),
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
