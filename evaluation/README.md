# Evaluation harness (PFC2 metrics)

Scripts that compute the quantitative metrics for the monograph's evaluation
chapter. None of this existed before — it is built from scratch here.

Each script adds the relevant agent's folder to `sys.path` and loads that
agent's `.env`, so run each one **inside the matching agent's virtualenv** with
the extra deps installed:

```bash
pip install -r evaluation/requirements.txt
```

| Script | Research question | Run inside | Needs |
|---|---|---|---|
| `qp1_wer_cer.py` | QP1 — transcription WER/CER/RTF | `agente-transcricao/.venv` | audio corpus + `GROQ_API_KEY` |
| `qp2_personas.py` | QP2 — persona Precision/Recall/F1 | any (pure Python) | gold roles file |
| `qp2_invest.py` | QP2 — INVEST conformance (LLM-judge) | `agente-identificacao/.venv` | `ANTHROPIC_API_KEY` |
| `qp5_cost.py` | QP5 — API cost per agent | any (pure Python) | token usage + prices |

> **QP3 (survey)** — pending: no responses yet. When the Google Forms CSV
> exists, a `qp3_survey.py` (mean/SD, Cronbach's alpha, NPS, Mann-Whitney) will
> be added here.
> **QP4 (coverage)** — the qualitative discussion is written in the monograph
> (Chapter 5). The numeric Precision/Recall/F1 needs an item-by-item matching
> protocol on the comparable scope (item 2.1) — not yet scripted.

---

## QP1 — WER / CER / RTF

Use a Portuguese audio corpus with reference transcripts (e.g. Mozilla Common
Voice PT). The manifest uses Common Voice's own column names (`path`,
`sentence`):

```bash
cd agente-transcricao            # so its venv/imports resolve
python ../evaluation/qp1_wer_cer.py \
    --manifest /path/to/cv-corpus/pt/validated.tsv \
    --clips-dir /path/to/cv-corpus/pt/clips \
    --engine both --limit 200 --out ../evaluation/results_qp1.csv
```

Reports corpus-level WER/CER and mean RTF for Groq and the local fallback.

## QP2 — personas (Precision / Recall / F1)

1. Copy `gold_roles.template.json` → `gold_roles.json` and set the true roles
   per meeting (key = `metadata.arquivo_origem` without `.txt`).
2. Copy `aliases.template.json` → `aliases.json` and map each predicted role
   (e.g. `"designer"`) to a canonical gold role (`"industrial designer"`). This
   is the human matching protocol.

```bash
python qp2_personas.py \
    --pred-dir ../agente-identificacao/data/output \
    --gold gold_roles.json --aliases aliases.json \
    --out results_qp2_personas.csv
```

## QP2 — INVEST conformance (LLM-judge)

```bash
cd agente-identificacao
python ../evaluation/qp2_invest.py \
    --pred-dir data/output \
    --model claude-haiku-4-5-20251001 \
    --out ../evaluation/results_qp2_invest.csv
```

For **inter-rater agreement**: score a random sample of stories by hand
(0/1 conformant), then compute Cohen's kappa against the judge's `conformant`
column with `sklearn.metrics.cohen_kappa_score`.

## QP5 — cost (and timing)

- **Timing:** run the pipeline and record the wall-clock per stage
  (`pipeline.py` already prints the total). Report seconds per agent.
- **Cost:** fill `prices.template.json` → `prices.json` with current USD/MTok,
  build a `usage.csv` (`stage,model,input_tokens,output_tokens`; the INVEST
  judge prints its token totals), then:

```bash
python qp5_cost.py --usage usage.csv --prices prices.json
```

Agent 1 (Groq Whisper) is priced per audio time, not tokens — add it separately.
