#!/usr/bin/env python3
"""QP2 (kappa) -- concordância entre o LLM-juiz e o anotador humano (Cohen's kappa).

Compara a planilha anotada à mão (``kappa_amostra_para_anotar.csv``, preenchida
pelo autor) com o veredito do juiz guardado em ``kappa_amostra_gabarito_juiz.csv``.
Calcula o kappa de Cohen para o rótulo "conforme (6/6)" e, opcionalmente, por
critério INVEST.

Preenchimento da planilha cega: para cada história, marque 1 (atende) ou 0 (não
atende) em cada critério, e 1/0 em ``conforme_6de6`` (1 só se atender os seis).
Aceita também true/false, sim/não, x.

    python qp2_kappa.py \
        --human kappa_amostra_para_anotar.csv \
        --judge kappa_amostra_gabarito_juiz.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

CRITERIA = ["independente", "negociavel", "valiosa", "estimavel", "pequena", "testavel"]

TRUE = {"1", "true", "t", "sim", "s", "x", "yes", "y", "v"}
FALSE = {"0", "false", "f", "nao", "não", "n", "no", ""}


def to_bool(cell: str):
    """Map a free-form annotation cell to 1/0, or None if blank/unrecognized."""
    v = (cell or "").strip().lower()
    if v in TRUE:
        return 1
    if v in FALSE:
        return None if v == "" else 0
    return None


def cohen_kappa(a: list[int], b: list[int]) -> float:
    """Cohen's kappa for two binary label lists (no external deps)."""
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    # marginal probabilities
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def load(path: Path) -> dict[str, dict]:
    """Load a CSV/';'-CSV keyed by id; auto-detects the delimiter."""
    text = path.read_text(encoding="utf-8-sig")
    first_line = text.splitlines()[0] if text else ""
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    import io
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = {}
    for row in reader:
        key = (row.get("id") or "").strip()
        if key != "":
            rows[key] = {(k or "").strip(): v for k, v in row.items()}
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="QP2: Cohen's kappa juiz x humano.")
    ap.add_argument("--human", required=True, type=Path,
                    help="Planilha anotada à mão (kappa_amostra_para_anotar.csv).")
    ap.add_argument("--judge", required=True, type=Path,
                    help="Veredito do juiz (kappa_amostra_gabarito_juiz.csv).")
    args = ap.parse_args()

    human = load(args.human)
    judge = load(args.judge)
    ids = [i for i in human if i in judge]
    if not ids:
        print("Nenhum id em comum entre as duas planilhas.", file=sys.stderr)
        return 1

    # --- kappa do rótulo principal: conforme (6/6) ---
    h_conf, j_conf, used = [], [], 0
    for i in ids:
        hv = to_bool(human[i].get("conforme_6de6", ""))
        jv = to_bool(judge[i].get("conformant", ""))
        if hv is None or jv is None:
            continue
        h_conf.append(hv)
        j_conf.append(jv)
        used += 1

    if used == 0:
        print("A coluna 'conforme_6de6' não foi preenchida na planilha humana.",
              file=sys.stderr)
        return 1

    agree = sum(1 for x, y in zip(h_conf, j_conf) if x == y)
    kappa = cohen_kappa(h_conf, j_conf)
    print(f"=== Conforme (6/6): juiz x humano sobre {used} histórias ===")
    print(f"Concordância observada: {agree}/{used} = {agree/used:.1%}")
    print(f"Cohen's kappa: {kappa:.3f}  ({interpret(kappa)})")

    # --- kappa por critério (se as colunas estiverem preenchidas) ---
    print("\n=== Kappa por critério (quando anotado) ===")
    for c in CRITERIA:
        ha, ja = [], []
        for i in ids:
            hv = to_bool(human[i].get(c, ""))
            jv = to_bool(judge[i].get(c, ""))
            if hv is None or jv is None:
                continue
            ha.append(hv); ja.append(jv)
        if ha:
            print(f"  {c:12s}: kappa={cohen_kappa(ha, ja):.3f}  (n={len(ha)})")
        else:
            print(f"  {c:12s}: (não anotado)")
    return 0


def interpret(k: float) -> str:
    if k != k:
        return "indefinido"
    if k < 0.0:
        return "pior que o acaso"
    if k < 0.20:
        return "leve"
    if k < 0.40:
        return "razoável"
    if k < 0.60:
        return "moderada"
    if k < 0.80:
        return "substancial"
    return "quase perfeita"


if __name__ == "__main__":
    raise SystemExit(main())
