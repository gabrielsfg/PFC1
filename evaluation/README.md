# Evaluation harness (quantitative metrics)

Reproducible scripts that compute the quantitative metrics reported in Chapter 5
of the monograph and in the [conference paper](../paper/SE4AS-2026-paper-en.pdf).

Each script adds the relevant agent's folder to `sys.path` and loads that agent's
`.env`, so run each one **inside the matching agent's virtualenv** with the extra
dependencies installed:

```bash
pip install -r evaluation/requirements.txt
```

## Research-question numbering

Script filenames keep the internal `qpN` numbering from an earlier five-question
draft. The final work reports **four research questions** (the perceived-quality
survey was dropped for lack of responses, and the remaining questions were
renumbered). The mapping below reconciles the two:

| Final RQ | Topic | Script(s) |
|---|---|---|
| **RQ1** | Transcription WER / CER / RTF | `qp1_wer_cer.py` |
| **RQ2** | Personas P/R/F1 · INVEST conformance · judge×human agreement | `qp2_personas.py`, `qp2_invest.py`, `qp2_kappa.py` |
| **RQ3** | Requirement coverage vs. human gold standard | `qp4_coverage.py` |
| **RQ4** | Cost & latency (and error propagation) | `qp5_run_case_study.py`, `qp5_cost.py` |

## Results summary

All four research questions are complete. Full discussion is in Chapter 5 of the
monograph; the numbers are reproduced from the CSVs in this folder.

| RQ | Metric | Result | Output CSV |
|---|---|---|---|
| RQ1 | WER / CER (Common Voice PT, 200 clips) | Groq **6.3% / 2.3%** · local 13.5% / 4.9% | `results_qp1_groq.csv`, `results_qp1_local.csv` |
| RQ2 | Personas P / R / F1 (AMI, 7 meetings) | **1.00 / 0.92 / 0.96** | `results_qp2_personas.csv` |
| RQ2 | INVEST conformance (strict LLM-judge) | AMI **52.5%** · real domain **66.7%** | `results_qp2_invest*.csv` |
| RQ2 | Judge × human agreement (Cohen's κ) | AMI **0.13** · real domain **0.31** | `kappa_*_FINAL.csv` |
| RQ3 | Coverage (recall vs. gold, item 2.1) | **72.7%** (business rules & use cases 100%) | `qp4_casamento_FINAL.csv` |
| RQ4 | Full real meeting (1h38m) end to end | **~US$0.72 · ~11 min** | `results_qp5*` / `timings` |

---

## RQ1 — WER / CER / RTF

Use a Portuguese audio corpus with reference transcripts (e.g. Mozilla Common
Voice PT). The manifest uses Common Voice's own column names (`path`, `sentence`):

```bash
cd agente-transcricao            # so its venv/imports resolve
python ../evaluation/qp1_wer_cer.py \
    --manifest /path/to/cv-corpus/pt/test.tsv \
    --clips-dir /path/to/cv-corpus/pt/clips \
    --engine both --limit 200 --out ../evaluation/results_qp1.csv
```

Reports corpus-level WER/CER and mean RTF for Groq and the local fallback. Each
engine writes its own CSV (`results_qp1_groq.csv`, `results_qp1_local.csv`) so a
failure in one does not corrupt the other.

> One-command helper (edit the corpus path at the top first):
> `.\evaluation\run_qp1.ps1`

## RQ2 — personas (Precision / Recall / F1)

1. Copy `gold_roles.template.json` → `gold_roles.json` and set the true roles per
   meeting (key = `metadata.arquivo_origem` without `.txt`).
2. Copy `aliases.template.json` → `aliases.json` and map each predicted role
   (e.g. `"designer"`) to a canonical gold role. This is the human matching
   protocol.

```bash
python qp2_personas.py \
    --pred-dir ../agente-identificacao/data/output \
    --gold gold_roles.json --aliases aliases.json \
    --out results_qp2_personas.csv
```

## RQ2 — INVEST conformance (LLM-judge)

```bash
cd agente-identificacao
python ../evaluation/qp2_invest.py \
    --pred-dir data/output \
    --model claude-sonnet-4-6 \
    --out ../evaluation/results_qp2_invest.csv
```

The judge model matters: the paper reports a Haiku × Sonnet comparison because a
weaker judge under-scores Estimable/Small/Testable. **Sonnet is the reference
judge.**

## RQ2 — judge × human agreement (Cohen's κ)

Score a random sample of stories by hand (blind, 0/1 per criterion), then compare
against the judge's verdict:

```bash
python qp2_kappa.py \
    --human kappa_amostra_para_anotar.csv \
    --judge kappa_amostra_gabarito_juiz.csv
```

Frozen annotations live in `kappa_amostra_anotada_FINAL.csv` (AMI) and
`kappa_estado_anotada_FINAL.csv` (real domain). The CSV separator (`,` or `;`) is
auto-detected. Low κ on aesthetic/subjective criteria (e.g. "nice design" is not
objectively testable) is a validity finding, not an evaluator error.

## RQ3 — coverage (recall vs. official document)

Item-by-item matching of the generated document against the human gold-standard
(`PR0102`) on the comparable scope. Fill `qp4_casamento_FINAL.csv` (each official
requirement marked covered/not), then:

```bash
python qp4_coverage.py --casamento qp4_casamento_FINAL.csv
```

Reports recall per category (RF / RN / CSU) and overall. The uncovered items are
pure-UI actions ("hide screen X") that require visual input the audio-only
pipeline cannot perceive — a modality limitation, not an extraction failure.

## RQ4 — cost & latency (real case study)

Run the full pipeline end to end on the real meeting and record per-stage timings:

```bash
python qp5_run_case_study.py \
    --audio /path/to/real-meeting.mp4 \
    --project-name "Controle de Saldo Orçamentário"
```

Then compute cost from token usage and current prices:

- Fill `prices.template.json` → `prices.json` with current USD/MTok.
- Build `usage.csv` (`stage,model,input_tokens,output_tokens`; the agents'
  `anthropic_client` prints `[tokens]` totals).

```bash
python qp5_cost.py --usage usage.csv --prices prices.json
```

Agent 1 (Groq Whisper) is priced per audio time, not tokens — add it separately.

> One-command helper for all RQ2 scripts: `.\evaluation\run_qp2.ps1`

---

## Notes

- `NOTES_resultados.md` is the running lab notebook — every run dated, with its
  methodological caveats (blind re-annotation, judge model choice, circularity
  risks). Read it to understand how each number was produced.
- Where a gold standard was partly derived from model output (an early
  personas run), the notes flag the circularity risk and the corrected protocol.
- Timings can vary with network and load; the reported figures are from the
  real 1h38m meeting run.
