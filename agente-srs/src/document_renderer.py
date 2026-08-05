import re
import subprocess
import unicodedata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.models import SRSDocument, FeatureRequirementsDocument

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Valori visual identity, sampled from the reference document (Documento_Valori.pdf):
# dark green base, gold titles, teal tagline. Used by the 'valori' theme.
_VALORI_DARK = "#062D2C"
_VALORI_GOLD = "#CF9B51"
_VALORI_TEAL = "#06D6A0"
_VALORI_AMBER = "#FAA916"
_VALORI_LIGHT = "#F7F7F7"
_VALORI_GRAY = "#D9D9D9"

_VALORI_CSS = f"""
  @page {{
    size: A4;
    margin: 2.2cm 2.2cm 2cm 2.2cm;
    /* Header matches the reference document: document title on the left,
       confidentiality notice on the right, page number centred at the bottom. */
    @top-left {{
      content: string(valori-doc-title);
      font-size: 8.5pt;
      font-weight: bold;
      color: {_VALORI_DARK};
    }}
    @top-right {{
      content: "Confidencial — Uso Interno";
      font-size: 8pt;
      color: #555;
    }}
    @bottom-center {{
      content: counter(page);
      font-size: 9pt;
      color: #555;
    }}
  }}
  /* The cover carries the full-bleed dark background and no header/footer. */
  @page :first {{
    margin: 0;
    background: {_VALORI_DARK};
    @top-left {{ content: none; }}
    @bottom-right {{ content: none; }}
    @bottom-left {{ content: none; }}
  }}

  body {{
    font-family: "Helvetica Neue", Arial, sans-serif;
    margin: 0;
    line-height: 1.55;
    color: #1a1a1a;
    font-size: 10.5pt;
  }}

  /* ── Cover page ─────────────────────────────────────────────────────── */
  .valori-cover {{
    page-break-after: always;
    /* Fills the first page exactly (A4 is 29.7cm; box-sizing keeps the padding
       inside the height) so "Confidencial" can sit at the bottom without
       spilling onto page 2, as in the reference document. */
    box-sizing: border-box;
    height: 29.7cm;
    padding: 3.4cm 2.5cm 1.5cm 2.5cm;
    color: #ffffff;
    text-align: center;
    position: relative;
  }}
  /* Logo (gold shield + white wordmark) at the top of the cover. */
  .valori-cover-shield {{
    width: 4.2cm;
    height: auto;
    margin-bottom: 3.2cm;
  }}
  .valori-cover-title {{
    font-size: 30pt;
    font-weight: bold;
    color: #ffffff;
    line-height: 1.15;
  }}
  /* The two gold rules bracket the title block (title + subtitle). */
  .valori-cover-rule {{
    height: 2px;
    background: {_VALORI_GOLD};
    margin: 0.7cm auto;
    width: 46%;
  }}
  .valori-cover-subtitle {{
    font-size: 17pt;
    font-weight: bold;
    color: {_VALORI_GOLD};
    line-height: 1.25;
    margin-top: 0.35cm;
  }}
  .valori-cover-version {{
    font-size: 12pt;
    color: #ffffff;
    margin-top: 2.2cm;
  }}
  .valori-cover-note {{
    font-size: 10pt;
    color: {_VALORI_GRAY};
    margin-top: 1.8cm;
    line-height: 1.5;
  }}
  .valori-cover-confidential {{
    position: absolute;
    bottom: 1.5cm;
    left: 0;
    right: 0;
    font-size: 9pt;
    color: {_VALORI_GRAY};
    letter-spacing: 0.05em;
  }}

  /* ── Body ───────────────────────────────────────────────────────────── */
  h1, h2, h3, h4 {{ color: {_VALORI_DARK}; line-height: 1.25; }}
  h2 {{
    font-size: 15pt;
    border-bottom: 2px solid {_VALORI_GOLD};
    padding-bottom: 0.12cm;
    margin-top: 1.0cm;
    page-break-after: avoid;
  }}
  /* Feeds the running header: the document title, set once on the cover so it
     stays constant on every page (like the reference document). */
  .valori-cover-title {{
    string-set: valori-doc-title content();
  }}
  h3 {{
    font-size: 12pt;
    color: {_VALORI_DARK};
    margin-top: 0.7cm;
    page-break-after: avoid;
  }}
  h4 {{ font-size: 11pt; page-break-after: avoid; }}
  p {{ text-align: justify; }}

  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 0.35cm 0;
    font-size: 9.5pt;
  }}
  th, td {{
    border: 1px solid {_VALORI_GRAY};
    padding: 6px 9px;
    vertical-align: top;
  }}
  th {{
    background: {_VALORI_DARK};
    color: #ffffff;
    font-weight: bold;
    text-align: left;
  }}
  tr:nth-child(even) td {{ background: {_VALORI_LIGHT}; }}

  /* Forces a new page between the major sections of the document. */
  .valori-page-break {{
    page-break-after: always;
  }}

  /* Box that frames the "Detalhamento" of each requirement, and the annex note. */
  .valori-box {{
    background: {_VALORI_LIGHT};
    border-left: 3px solid {_VALORI_GOLD};
    padding: 0.2cm 0.45cm;
    margin: 0.3cm 0;
    page-break-inside: avoid;
  }}
  .valori-box p {{ margin: 0.18cm 0; }}
  .valori-box-detalhe {{
    border-left-color: {_VALORI_AMBER};
  }}
  blockquote {{
    color: #555;
    border-left: 3px solid {_VALORI_GOLD};
    padding-left: 1em;
    margin-left: 0;
  }}
  img {{ max-width: 100%; }}
  code {{ font-family: Consolas, monospace; font-size: 9pt; }}

  /* ── Sumário (ToC): dotted leader + resolved page number ─────────────── */
  a[href^="#"] {{
    text-decoration: none;
    color: {_VALORI_DARK};
    font-size: 10pt;
  }}
  a[href^="#"]::after {{
    content: " " leader(". ") " " target-counter(attr(href), page);
    color: #555;
    font-weight: normal;
    font-size: 9.5pt;
  }}
"""


def _valori_logo_data_uri() -> str:
    """The Valori logo as a data: URI, so the Markdown/PDF is self-contained.

    Returns "" when the file is missing, which renders the cover without a logo
    instead of failing the whole document.
    """
    import base64

    logo = _TEMPLATES_DIR / "valori_logo.png"
    if not logo.exists():
        return ""
    encoded = base64.b64encode(logo.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _slugify(value: str) -> str:
    """Replicate python-markdown's default (ascii) 'toc' slugify, so the manual
    Sumário links match the heading ids generated by the toc extension at PDF time."""
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


class DocumentRenderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=False,
            keep_trailing_newline=True,
        )
        self.env.filters["slug"] = _slugify

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

    def render_valori_markdown(
        self, document: FeatureRequirementsDocument, output_path: Path
    ) -> Path:
        """Renders the Valori format (cover page + Valori colour palette)."""
        template = self.env.get_template("valori.md.j2")
        content = template.render(
            logo_data_uri=_valori_logo_data_uri(),
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

    def render_pdf(
        self, markdown_path: Path, pdf_path: Path, engine: str = "auto", theme: str = "default"
    ) -> Path:
        """engine: 'weasyprint' (CSS, page-numbered ToC), 'pandoc', or 'auto'.
        theme: 'default' or 'valori' (Valori palette + cover). The Valori theme
        needs CSS Paged Media, so it always renders through WeasyPrint."""
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        if theme == "valori":
            _weasyprint_convert(markdown_path, pdf_path, theme="valori")
        elif engine == "weasyprint":
            _weasyprint_convert(markdown_path, pdf_path)
        elif engine == "pandoc":
            _pandoc_convert(markdown_path, pdf_path)
        elif _pandoc_available():
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


def _weasyprint_convert(markdown_path: Path, pdf_path: Path, theme: str = "default") -> None:
    import markdown as md_lib
    from weasyprint import HTML

    # 'toc' gives every heading an id so the Sumário links can resolve to a page.
    # 'md_in_html' lets the Valori template wrap sections in styled <div>s while
    # still having the Markdown inside them processed.
    html_content = md_lib.markdown(
        markdown_path.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "toc", "md_in_html"],
    )
    if theme == "valori":
        full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>{_VALORI_CSS}</style>
</head>
<body>{html_content}</body>
</html>"""
        HTML(string=full_html).write_pdf(str(pdf_path))
        return

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 2.5cm;
    @bottom-right {{ content: "Página " counter(page); font-size: 9pt; color: #777; }}
  }}
  body {{ font-family: Arial, sans-serif; margin: 0; line-height: 1.5; color: #1a1a1a; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; vertical-align: top; }}
  th {{ background: #f0f0f0; }}
  h1, h2, h3, h4 {{ color: #1a1a1a; }}
  img {{ max-width: 100%; }}
  blockquote {{ color: #555; border-left: 3px solid #ccc; padding-left: 1em; }}

  /* ── Sumário (índice) ──────────────────────────────────────────────
     Only the document's own internal links (href="#...") are ToC entries.
     Standard formatting: font size, color, dotted leader and page number. */
  a[href^="#"] {{
    text-decoration: none;
    color: #1a3a5a;
    font-size: 10.5pt;
  }}
  a[href^="#"]::after {{
    content: " " leader(". ") " " target-counter(attr(href), page);
    color: #555;
    font-weight: normal;
    font-size: 10pt;
  }}
</style>
</head>
<body>{html_content}</body>
</html>"""
    HTML(string=full_html).write_pdf(str(pdf_path))
