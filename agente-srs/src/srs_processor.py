from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path

from src.models import Agent2Output, EmpresaDocumentMeta, VersionEntry
from src.srs_generator import SRSGenerator
from src.feature_generator import FeatureRequirementsGenerator
from src.document_renderer import DocumentRenderer


class SRSProcessor:
    def __init__(self, output_dir: str = "./data/output", fmt: str = "ieee",
                 project_name: str = ""):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.fmt = fmt
        # Optional human title for the empresa document (used as H1 + output filename).
        self.project_name = (project_name or os.getenv("EMPRESA_PROJECT_NAME", "")).strip()
        if fmt == "empresa":
            self.generator = FeatureRequirementsGenerator()
        else:
            self.generator = SRSGenerator(self.images_dir)
        self.renderer = DocumentRenderer()

    def process(self, json_path: Path) -> dict | None:
        print(f"\n{'='*60}")
        print(f"Processando: {json_path.name}  (formato: {self.fmt})")
        print(f"{'='*60}")

        agent2_output = self._load_input(json_path)
        if agent2_output is None:
            return None

        if self.fmt == "empresa":
            return self._process_empresa(json_path, agent2_output)
        return self._process_ieee(json_path, agent2_output)

    def _process_ieee(self, json_path: Path, agent2_output: Agent2Output) -> dict:
        document = self.generator.generate(agent2_output)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = f"{json_path.stem}_srs_{timestamp}"
        md_path = self.output_dir / f"{stem}.md"
        pdf_path = self.output_dir / f"{stem}.pdf"

        print("Renderizando Markdown...")
        self.renderer.render_markdown(document, md_path)
        print(f"  -> {md_path}")

        pdf_path = self._render_pdf(md_path, pdf_path)

        print("\nSRS gerado com sucesso!")
        return {
            "source": str(json_path),
            "markdown": str(md_path),
            "pdf": str(pdf_path) if pdf_path else None,
            "functional_requirements": len(document.functional_requirements),
            "use_cases": len(document.use_cases),
            "diagrams": len(document.use_case_diagrams),
        }

    def _process_empresa(self, json_path: Path, agent2_output: Agent2Output) -> dict:
        doc_meta = default_empresa_meta()
        if self.project_name:
            doc_meta.title = self.project_name  # used as the H1 document title
        # RNF section is optional (the SGG model document has none). On by default.
        include_nfr = os.getenv("EMPRESA_INCLUDE_NFR", "true").strip().lower() not in ("0", "false", "no", "nao", "não")
        document = self.generator.generate(agent2_output, doc_meta, include_nfr=include_nfr)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Name the output after the project name when provided, else the JSON stem.
        base = _safe_filename(self.project_name) if self.project_name else json_path.stem
        stem = f"{base}_requisitos_{timestamp}"
        md_path = self.output_dir / f"{stem}.md"
        pdf_path = self.output_dir / f"{stem}.pdf"

        print("Renderizando Markdown...")
        self.renderer.render_feature_markdown(document, md_path)
        print(f"  -> {md_path}")

        # WeasyPrint so the Sumário gets page numbers (CSS target-counter).
        pdf_path = self._render_pdf(md_path, pdf_path, engine="weasyprint")

        print("\nDocumento de Requisitos (formato empresa) gerado com sucesso!")
        return {
            "source": str(json_path),
            "markdown": str(md_path),
            "pdf": str(pdf_path) if pdf_path else None,
            "functional_requirements": len(document.functional_requirements),
            "use_cases": len(document.use_cases),
            "business_rules": sum(len(g.rules) for g in document.business_rule_groups),
            "non_functional_requirements": len(document.non_functional_requirements),
        }

    def _render_pdf(self, md_path: Path, pdf_path: Path, engine: str = "auto") -> Path | None:
        print("Renderizando PDF...")
        try:
            self.renderer.render_pdf(md_path, pdf_path, engine=engine)
            print(f"  -> {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"  Aviso: falha ao gerar PDF ({e})")
            return None

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


def _safe_filename(name: str, max_len: int = 80) -> str:
    """Turn a free-text project name into a safe file base (no path/invalid chars)."""
    import re
    cleaned = re.sub(r'[\\/:*?"<>|]+', " ", name)        # drop filesystem-invalid chars
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        cut = cleaned[:max_len]
        if " " in cut:
            cut = cut[:cut.rstrip().rfind(" ")]          # avoid cutting mid-word
        cleaned = cut.strip()
    return cleaned or "documento"


def default_empresa_meta() -> EmpresaDocumentMeta:
    """Placeholder document metadata for the "empresa" format.

    These values cannot be derived from the audio. For now they are placeholders;
    TODO: collect them from the user via the GUI (project code, client, product,
    phase, version and the version-control table).
    """
    return EmpresaDocumentMeta(
        project_code="PR0XX",
        client="<CLIENTE>",
        product="<PRODUTO>",
        phase="<FASE>",
        version="1.0.0",
        version_history=[
            VersionEntry(
                date="<dd/mm/aaaa>",
                version="1.0.0",
                description="Criação do documento",
                authors="<autor>",
            )
        ],
    )
