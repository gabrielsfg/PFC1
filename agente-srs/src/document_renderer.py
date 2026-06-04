import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.models import SRSDocument, FeatureRequirementsDocument

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class DocumentRenderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=False,
            keep_trailing_newline=True,
        )

    def render_markdown(self, document: SRSDocument, output_path: Path) -> Path:
        template = self.env.get_template("srs.md.j2")
        content = template.render(
            metadata=document.metadata,
            introduction=document.introduction,
            personas=document.personas,
            functional_requirements=document.functional_requirements,
            user_stories=document.user_stories,
            use_cases=document.use_cases,
            use_case_diagrams=document.use_case_diagrams,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def render_feature_markdown(
        self, document: FeatureRequirementsDocument, output_path: Path
    ) -> Path:
        """Renders the company "Documento de Requisitos" (SGG-GO) format."""
        template = self.env.get_template("feature_requirements.md.j2")
        content = template.render(
            document=document.document,
            feature=document.feature,
            functional_requirements=document.functional_requirements,
            business_rule_groups=document.business_rule_groups,
            use_cases=document.use_cases,
            non_functional_requirements=document.non_functional_requirements,
            project_notes=document.project_notes,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def render_pdf(self, markdown_path: Path, pdf_path: Path) -> Path:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        if _pandoc_available():
            _pandoc_convert(markdown_path, pdf_path)
        else:
            _weasyprint_convert(markdown_path, pdf_path)
        return pdf_path


def _pandoc_available() -> bool:
    try:
        subprocess.run(
            ["pandoc", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _pandoc_convert(markdown_path: Path, pdf_path: Path) -> None:
    subprocess.run(
        [
            "pandoc", str(markdown_path),
            "-o", str(pdf_path),
            "--pdf-engine=xelatex",
            "-V", "geometry:margin=2.5cm",
            "-V", "lang=pt-BR",
        ],
        check=True,
    )


def _weasyprint_convert(markdown_path: Path, pdf_path: Path) -> None:
    import markdown as md_lib
    from weasyprint import HTML

    html_content = md_lib.markdown(
        markdown_path.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code"],
    )
    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 2.5cm; line-height: 1.5; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; }}
  th {{ background: #f0f0f0; }}
  h1, h2, h3, h4 {{ color: #222; }}
  img {{ max-width: 100%; }}
  blockquote {{ color: #555; border-left: 3px solid #ccc; padding-left: 1em; }}
</style>
</head>
<body>{html_content}</body>
</html>"""
    HTML(string=full_html).write_pdf(str(pdf_path))
