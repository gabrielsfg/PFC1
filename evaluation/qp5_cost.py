#!/usr/bin/env python3
"""QP5 (cost) -- estimate API cost per agent from token usage.

Per-stage *timing* is obtained by running the pipeline (``pipeline.py`` already
prints the total time; time each agent's CLI individually for per-stage numbers)
and reporting the wall-clock per stage. This script handles the *cost* side.

It reads a usage CSV and a prices JSON and prints the cost per stage and the
total. Token-based prices are USD per million tokens (MTok).

usage CSV columns (header required):  stage,model,input_tokens,output_tokens
prices JSON shape:  { "<model>": {"input": <USD/MTok>, "output": <USD/MTok>} }

Fill prices.template.json with the providers' current prices before running:
    python qp5_cost.py --usage usage.csv --prices prices.json

The INVEST judge (qp2_invest.py) prints the token totals of its run, which can
be added as a row in the usage CSV.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="QP5: API cost per agent from token usage.")
    ap.add_argument("--usage", required=True, type=Path,
                    help="CSV: stage,model,input_tokens,output_tokens")
    ap.add_argument("--prices", required=True, type=Path,
                    help="JSON: {model: {input: USD/MTok, output: USD/MTok}}")
    args = ap.parse_args()

    prices = json.loads(args.prices.read_text(encoding="utf-8"))

    total = 0.0
    print(f"{'stage':22s} {'model':28s} {'in_tok':>10s} {'out_tok':>10s} {'USD':>10s}")
    print("-" * 84)
    with args.usage.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            model = row["model"]
            if model not in prices:
                print(f"  [warn] no price for model '{model}'", file=sys.stderr)
                continue
            in_tok = int(row.get("input_tokens", 0) or 0)
            out_tok = int(row.get("output_tokens", 0) or 0)
            cost = in_tok / 1e6 * prices[model]["input"] + out_tok / 1e6 * prices[model]["output"]
            total += cost
            print(f"{row['stage']:22s} {model:28s} {in_tok:>10d} {out_tok:>10d} {cost:>10.4f}")
    print("-" * 84)
    print(f"{'TOTAL':22s} {'':28s} {'':>10s} {'':>10s} {total:>10.4f}")
    print("\nNote: Agent 1 (Groq Whisper) is priced per audio time, not tokens — "
          "add it separately from the provider's pricing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
