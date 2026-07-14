#!/usr/bin/env python3
"""QP4 -- Cobertura do documento gerado frente ao documento oficial (PR0102).

Calcula Revocação (recall), Precisão e F1 da cobertura no ESCOPO COMPARÁVEL
(item 2.1, a tela de Manutenção de Saldo), a partir de um casamento item a item
anotado à mão entre os requisitos do documento oficial (gold standard) e os do
documento gerado pelo sistema.

A planilha de casamento (qp4_casamento_para_anotar.csv, separador ';') tem uma
linha por item do documento OFICIAL, com a coluna casa(1/0): 1 se o item oficial
está coberto por algum item do gerado, 0 caso contrário.

Métricas (por tipo: RF, RN, CSU, e global):
  - Revocação = itens_oficiais_cobertos / total_itens_oficiais
    (dos requisitos do gold, quantos o sistema capturou)
  - Precisão  = no escopo comparável, requer um segundo arquivo opcional com os
    itens do GERADO que pertencem ao item 2.1, marcando quais casam com o oficial.
    Sem esse arquivo, reporta-se apenas a Revocação (cobertura), que é a métrica
    central da QP4 ("quão completamente o gerado cobre o oficial").

Uso:
    python qp4_coverage.py --casamento qp4_casamento_para_anotar.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path


def load_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    delim = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def is_true(v: str) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "sim", "x", "yes"}


def main() -> int:
    ap = argparse.ArgumentParser(description="QP4: cobertura (recall) do gerado vs oficial.")
    ap.add_argument("--casamento", required=True, type=Path)
    args = ap.parse_args()

    rows = load_rows(args.casamento)
    if not rows:
        print("Planilha de casamento vazia.", file=sys.stderr)
        return 1

    # Agrupa por tipo (RF/RN/CSU) e global.
    by_type: dict[str, list[bool]] = {}
    for r in rows:
        t = (r.get("tipo") or "?").strip().upper()
        casa = is_true(r.get("casa(1/0)", r.get("casa", "")))
        by_type.setdefault(t, []).append(casa)

    print(f"{'Tipo':6s} {'Cobertos':>9s} {'Total':>6s} {'Revocacao':>10s}")
    print("-" * 36)
    tot_cov = tot_all = 0
    for t in sorted(by_type):
        covered = sum(by_type[t])
        total = len(by_type[t])
        tot_cov += covered
        tot_all += total
        rec = covered / total if total else 0.0
        print(f"{t:6s} {covered:>9d} {total:>6d} {rec:>10.2%}")
    print("-" * 36)
    rec_g = tot_cov / tot_all if tot_all else 0.0
    print(f"{'GLOBAL':6s} {tot_cov:>9d} {tot_all:>6d} {rec_g:>10.2%}")

    print("\nNota: a Revocação (cobertura) é a métrica central da QP4 — dos requisitos")
    print("do documento oficial (gold), a fração capturada pelo documento gerado.")
    print("A Precisão exige listar os itens do gerado pertencentes ao item 2.1 e")
    print("marcar quais correspondem ao oficial (escopo comparável). Itens do gerado")
    print("de OUTROS itens de escopo (2.2-2.7) NÃO contam como falso positivo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
