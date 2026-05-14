import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Agent 5 — Domain Diagram Generator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path)
    group.add_argument("--dir", type=Path)
    group.add_argument("--monitor", action="store_true")
    parser.add_argument("--check-interval", type=int, default=5)
    args = parser.parse_args()

    # TODO: implement domain diagram generator + final unified document
    raise NotImplementedError("Agent 5 not yet implemented")


if __name__ == "__main__":
    main()
