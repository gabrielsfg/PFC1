import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Agent 3 — SRS Document Generator (IEEE 830)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Process a single Agent 2 JSON file")
    group.add_argument("--dir", type=Path, help="Batch process a directory of JSON files")
    group.add_argument("--monitor", action="store_true", help="Monitor input directory continuously")
    parser.add_argument("--check-interval", type=int, default=int(os.getenv("CHECK_INTERVAL", "5")))
    args = parser.parse_args()

    output_dir = os.getenv("OUTPUT_DIR", "./data/output")
    processed_dir = os.getenv("PROCESSED_DIR", "./data/processed")
    input_dir = os.getenv("INPUT_DIR", "../agente-identificacao/data/output")

    if args.file:
        from src.srs_processor import SRSProcessor
        processor = SRSProcessor(output_dir)
        result = processor.process(args.file)
        if not result:
            raise SystemExit(1)

    elif args.dir:
        from src.srs_processor import SRSProcessor
        processor = SRSProcessor(output_dir)
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
