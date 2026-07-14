#!/usr/bin/env python3
"""QP2 (part 2) -- INVEST conformance of generated user stories (LLM-judge).

Scores every user story produced by Agent 2 against the six INVEST criteria
using Claude as a judge, and reports the conformance rate (a story is conformant
when all six criteria hold). Token usage is accumulated so the run can also feed
the cost estimate (QP5).

Run inside the agente-identificacao virtualenv (it has the ``anthropic`` SDK),
with ANTHROPIC_API_KEY set in agente-identificacao/.env:

    python qp2_invest.py --pred-dir ../agente-identificacao/data/output \
        --model claude-haiku-4-5-20251001 --out results_qp2_invest.csv

Validate a manual sample against this output and report Cohen's kappa
(see qp2_kappa note in the README).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT2 = REPO_ROOT / "agente-identificacao"

from dotenv import load_dotenv  # noqa: E402

load_dotenv(AGENT2 / ".env", override=True)

from anthropic import Anthropic  # noqa: E402

JUDGE_SYSTEM = (
    "Você é um avaliador rigoroso de qualidade de histórias de usuário. "
    "Avalie objetivamente segundo os critérios INVEST e responda apenas com JSON."
)

JUDGE_PROMPT = """Avalie a história de usuário a seguir segundo os seis critérios INVEST.
Para cada critério, responda true (atende) ou false (não atende):

- independente: não depende de outra história para ter valor;
- negociavel: descreve a intenção, não um contrato fechado de implementação;
- valiosa: entrega valor a um usuário/ator do sistema;
- estimavel: é possível estimar o esforço;
- pequena: cabe em uma única iteração (não é ampla demais);
- testavel: admite critérios de aceitação verificáveis.

HISTÓRIA:
"{story}"

Retorne APENAS um JSON no formato:
{{"independente": bool, "negociavel": bool, "valiosa": bool,
  "estimavel": bool, "pequena": bool, "testavel": bool,
  "justificativa": "uma frase curta"}}"""

CRITERIA = ["independente", "negociavel", "valiosa", "estimavel", "pequena", "testavel"]


def strip_fences(text: str) -> str:
    """Remove ```json ... ``` fences that the model often wraps JSON in."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def iter_stories(pred_dir: Path):
    """Yield (meeting, persona, story_text) from Agent 2 outputs."""
    for pred_file in sorted(pred_dir.glob("*_personas_*.json")):
        data = json.loads(pred_file.read_text(encoding="utf-8"))
        meeting = Path((data.get("metadata", {}) or {}).get("arquivo_origem", pred_file.stem)).stem
        groups = (data.get("historias_usuario", {}) or {}).get("user_stories", []) or []
        for g in groups:
            persona = g.get("persona_nome", g.get("persona_id", "?"))
            for h in g.get("historias", []) or []:
                story = h.get("historia")
                if story:
                    yield meeting, persona, story


def main() -> int:
    ap = argparse.ArgumentParser(description="QP2: INVEST conformance via LLM-judge.")
    ap.add_argument("--pred-dir", required=True, type=Path)
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--sample", type=int, default=None, help="Score only the first N stories.")
    ap.add_argument("--out", type=Path, default=Path("results_qp2_invest.csv"))
    args = ap.parse_args()

    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment/.env
    stories = list(iter_stories(args.pred_dir))
    if args.sample:
        stories = stories[: args.sample]
    if not stories:
        print("No user stories found in --pred-dir.", file=sys.stderr)
        return 1
    print(f"Scoring {len(stories)} stories with {args.model}…")

    conformant = 0
    scored = 0
    in_tokens = out_tokens = 0
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["meeting", "persona", "story", *CRITERIA, "conformant", "justification"])
        for meeting, persona, story in stories:
            try:
                resp = client.messages.create(
                    model=args.model, max_tokens=400, temperature=0.0,
                    system=JUDGE_SYSTEM,
                    messages=[{"role": "user", "content": JUDGE_PROMPT.format(story=story)}],
                )
                in_tokens += resp.usage.input_tokens
                out_tokens += resp.usage.output_tokens
                verdict = json.loads(strip_fences(resp.content[0].text))
            except Exception as exc:  # noqa: BLE001
                print(f"  [skip] {exc}", file=sys.stderr)
                continue
            flags = [bool(verdict.get(c, False)) for c in CRITERIA]
            ok = all(flags)
            conformant += int(ok)
            scored += 1
            w.writerow([meeting, persona, story, *flags, ok, verdict.get("justificativa", "")])
            print(f"  [{'OK ' if ok else 'X  '}] {story[:70]}")

    rate = conformant / scored if scored else 0.0
    print("\n=== INVEST conformance ===")
    print(f"Conformant: {conformant}/{scored} = {rate:.1%}")
    print(f"Judge tokens: input={in_tokens}, output={out_tokens} "
          f"(feed qp5_cost.py for the cost of this judging run)")
    print(f"Per-story results written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
