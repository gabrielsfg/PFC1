import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Agent 4 — Domain Diagram + Final Consolidated Document"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Agent 2 JSON file to process")
    group.add_argument("--dir", type=Path, help="Batch process a directory of JSON files")
    group.add_argument("--monitor", action="store_true", help="Monitor input directory continuously")
    parser.add_argument("--srs-md", type=Path, default=None,
                        help="Path to Agent 3 Markdown output to embed in the final document")
    parser.add_argument("--check-interval", type=int, default=int(os.getenv("CHECK_INTERVAL", "5")))
    args = parser.parse_args()

    output_dir = os.getenv("OUTPUT_DIR", "./data/output")
    processed_dir = os.getenv("PROCESSED_DIR", "./data/processed")
    input_dir = os.getenv("INPUT_DIR", "../agente-identificacao/data/output")

    if args.file:
        from src.diagrams_processor import DiagramsProcessor
        processor = DiagramsProcessor(output_dir)
        result = processor.process(args.file, srs_md_path=args.srs_md)
        if not result:
            raise SystemExit(1)

    elif args.dir:
        from src.diagrams_processor import DiagramsProcessor
        processor = DiagramsProcessor(output_dir)
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
        )
        monitor.start()


if __name__ == "__main__":
    main()
