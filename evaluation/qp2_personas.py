#!/usr/bin/env python3
"""QP2 (part 1) -- Precision/Recall/F1 of persona identification.

Compares the system actors (``analise_personas.personas[].papel``) produced by
Agent 2 against a human gold set of roles per meeting, using set-based matching.

Inputs
------
--pred-dir : folder with Agent 2 outputs (``*_personas_*.json``). The meeting key
             is taken from ``metadata.arquivo_origem`` (e.g. ``meeting_0.txt`` ->
             ``meeting_0``).
--gold     : JSON mapping meeting key -> list of gold roles, e.g.
             {
               "meeting_0": ["Project Manager", "Marketing", "User Interface",
                             "Industrial Designer"]
             }
--aliases  : (optional) JSON mapping a normalized predicted role to a canonical
             gold role, e.g. {"designer": "industrial designer",
             "especialista em marketing": "marketing"}. This is where the human
             matching protocol is encoded.

Matching is set-based per meeting: a predicted role counts as a true positive
when, after normalization + alias resolution, it equals a gold role. Metrics are
reported per meeting and micro-averaged over all meetings.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path


def normalize_role(role: str) -> str:
    """Lowercase, strip accents and collapse spaces for robust role matching."""
    role = (role or "").strip().lower()
    role = "".join(c for c in unicodedata.normalize("NFD", role)
                   if unicodedata.category(c) != "Mn")
    return " ".join(role.split())


def load_gold(path: Path) -> dict[str, set[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: {normalize_role(r) for r in roles} for k, roles in data.items()}


def load_aliases(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {normalize_role(k): normalize_role(v) for k, v in data.items()}


def meeting_key(pred: dict, fallback: str) -> str:
    origem = (pred.get("metadata", {}) or {}).get("arquivo_origem", "")
    return Path(origem).stem if origem else fallback


def predicted_roles(pred: dict, aliases: dict[str, str]) -> set[str]:
    personas = (pred.get("analise_personas", {}) or {}).get("personas", []) or []
    roles = set()
    for p in personas:
        norm = normalize_role(p.get("papel", ""))
        roles.add(aliases.get(norm, norm))
    roles.discard("")
    return roles


def main() -> int:
    ap = argparse.ArgumentParser(description="QP2: Precision/Recall/F1 of personas vs gold roles.")
    ap.add_argument("--pred-dir", required=True, type=Path)
    ap.add_argument("--gold", required=True, type=Path)
    ap.add_argument("--aliases", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path("results_qp2_personas.csv"))
    args = ap.parse_args()

    gold = load_gold(args.gold)
    aliases = load_aliases(args.aliases)

    rows = []
    tp_tot = fp_tot = fn_tot = 0
    for pred_file in sorted(args.pred_dir.glob("*_personas_*.json")):
        pred = json.loads(pred_file.read_text(encoding="utf-8"))
        key = meeting_key(pred, pred_file.stem)
        if key not in gold:
            print(f"  [skip] no gold for '{key}' ({pred_file.name})", file=sys.stderr)
            continue
        pred_set = predicted_roles(pred, aliases)
        gold_set = gold[key]
        tp = len(pred_set & gold_set)
        fp = len(pred_set - gold_set)
        fn = len(gold_set - pred_set)
        tp_tot += tp; fp_tot += fp; fn_tot += fn
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        rows.append((key, tp, fp, fn, prec, rec, f1,
                     ";".join(sorted(pred_set)), ";".join(sorted(gold_set))))
        print(f"  {key:18s} P={prec:.2f} R={rec:.2f} F1={f1:.2f}  "
              f"(TP={tp} FP={fp} FN={fn})")

    if not rows:
        print("No meetings matched between predictions and gold.", file=sys.stderr)
        return 1

    micro_p = tp_tot / (tp_tot + fp_tot) if (tp_tot + fp_tot) else 0.0
    micro_r = tp_tot / (tp_tot + fn_tot) if (tp_tot + fn_tot) else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) else 0.0

    import csv
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["meeting", "tp", "fp", "fn", "precision", "recall", "f1",
                    "predicted_roles", "gold_roles"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], f"{r[4]:.4f}", f"{r[5]:.4f}",
                        f"{r[6]:.4f}", r[7], r[8]])
        w.writerow([])
        w.writerow(["MICRO", tp_tot, fp_tot, fn_tot, f"{micro_p:.4f}",
                    f"{micro_r:.4f}", f"{micro_f1:.4f}", "", ""])

    print(f"\n=== Micro-average over {len(rows)} meetings ===")
    print(f"Precision={micro_p:.4f}  Recall={micro_r:.4f}  F1={micro_f1:.4f}")
    print(f"Per-meeting results written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
