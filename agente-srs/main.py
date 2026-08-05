import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)


def main():
    parser = argparse.ArgumentParser(description="Agent 3 — Requirements Document Generator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Process a single Agent 2 JSON file")
    group.add_argument("--dir", type=Path, help="Batch process a directory of JSON files")
    group.add_argument("--monitor", action="store_true", help="Monitor input directory continuously")
    parser.add_argument("--check-interval", type=int, default=int(os.getenv("CHECK_INTERVAL", "5")))
    parser.add_argument(
        "--format", choices=["ieee", "empresa", "valori"],
        default=os.getenv("DOCUMENT_FORMAT", "ieee"),
        help="Output document format: 'ieee' (IEEE 830 SRS), 'empresa' (SGG-GO Documento de "
             "Requisitos) or 'valori' (Valori format, with cover page)",
    )
    parser.add_argument(
        "--project-name", default=os.getenv("EMPRESA_PROJECT_NAME", ""),
        help="Empresa/Valori format: human title used as the document title and output filename.",
    )
    parser.add_argument(
        "--acronyms-file", type=Path, default=None,
        help="Text file with the meeting acronyms ('SIGLA = significado', one per line). "
             "Used as extra context for the LLM so it spells them correctly.",
    )
    args = parser.parse_args()

    acronyms = ""
    if args.acronyms_file and args.acronyms_file.exists():
        acronyms = args.acronyms_file.read_text(encoding="utf-8")

    output_dir = os.getenv("OUTPUT_DIR", "./data/output")
    processed_dir = os.getenv("PROCESSED_DIR", "./data/processed")
    input_dir = os.getenv("INPUT_DIR", "../agente-identificacao/data/output")

    if args.file:
        from src.srs_processor import SRSProcessor
        processor = SRSProcessor(output_dir, fmt=args.format, project_name=args.project_name,
                                 acronyms=acronyms)
        result = processor.process(args.file)
        if not result:
            raise SystemExit(1)

    elif args.dir:
        from src.srs_processor import SRSProcessor
        processor = SRSProcessor(output_dir, fmt=args.format, project_name=args.project_name,
                                 acronyms=acronyms)
        results = processor.process_directory(args.dir)
        if not results:
            raise SystemExit(1)

    elif args.monitor:
        from src.file_monitor import FileMonitor
        monitor = FileMonitor(
            input_dir=input_dir,
            output_dir=output_dir,
            processed_dir=processed_dir,
            check_interval=args.check_interval,
            fmt=args.format,
        )
        monitor.start()


if __name__ == "__main__":
    main()
