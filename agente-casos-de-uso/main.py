import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Agent 4 — Use Case Generator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path)
    group.add_argument("--dir", type=Path)
    group.add_argument("--monitor", action="store_true")
    parser.add_argument("--check-interval", type=int, default=5)
    args = parser.parse_args()

    # TODO: implement use case generator + UML via kroki.io
    raise NotImplementedError("Agent 4 not yet implemented")


if __name__ == "__main__":
    main()
