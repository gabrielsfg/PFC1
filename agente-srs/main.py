import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Agent 3 — SRS Document Generator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Process a single Agent 2 JSON file")
    group.add_argument("--dir", type=Path, help="Batch process a directory of JSON files")
    group.add_argument("--monitor", action="store_true", help="Monitor input directory continuously")
    parser.add_argument("--check-interval", type=int, default=5)
    args = parser.parse_args()

    # TODO: implement SRS generator, file monitor, batch processor
    raise NotImplementedError("Agent 3 not yet implemented")


if __name__ == "__main__":
    main()
