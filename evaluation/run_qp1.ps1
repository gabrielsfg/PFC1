# Roda a QP1 (WER/CER/RTF da transcricao) com um comando.
# ANTES DE RODAR: edite as duas variaveis abaixo com o caminho do corpus baixado.
# Uso (a partir da raiz do projeto C:\Users\gabri\Tcc):  .\evaluation\run_qp1.ps1

# >>>>>>>>>>>>>>>>>>>>>>  JA CONFIGURADO PARA O SEU CORPUS  <<<<<<<<<<<<<<<<<<<<<<
$CORPUS    = "C:\Users\gabri\Tcc\Documentation\Corpus\1781716768543-cv-corpus-26.0-2026-06-12-pt\cv-corpus-26.0-2026-06-12\pt"
$MANIFEST  = Join-Path $CORPUS "test.tsv"    # conjunto de teste padrao (colunas path + sentence)
$CLIPS_DIR = Join-Path $CORPUS "clips"       # pasta com os audios .mp3
$LIMIT     = 200                              # quantos clipes avaliar (aumente se quiser)
$MIN_WORDS = 3                                # ignora referencias muito curtas (inflam o WER)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$agent = Join-Path $root "agente-transcricao"
$py   = Join-Path $agent "venv\Scripts\python.exe"
$script = Join-Path $root "evaluation\qp1_wer_cer.py"
# Cada engine grava em seu proprio CSV: se um falhar, o outro fica salvo
# (e evita os dois processos disputarem o mesmo arquivo, que o corrompia).
$outGroq  = Join-Path $root "evaluation\results_qp1_groq.csv"
$outLocal = Join-Path $root "evaluation\results_qp1_local.csv"

if (-not (Test-Path $py))       { Write-Host "ERRO: venv do agente-transcricao nao encontrado em $py" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $MANIFEST)) { Write-Host "ERRO: manifest nao encontrado: $MANIFEST" -ForegroundColor Red; Write-Host "Baixe o Common Voice PT em https://commonvoice.mozilla.org/pt/datasets e ajuste os caminhos no topo deste script." -ForegroundColor Yellow; exit 1 }

Push-Location $agent          # roda dentro do agente p/ imports/.env resolverem

# 1) Groq (nuvem, rapido, sem problema de RAM)
Write-Host "[1/2] Rodando QP1 no Groq sobre $LIMIT clipes (min-words $MIN_WORDS)..." -ForegroundColor Cyan
& $py $script --manifest $MANIFEST --clips-dir $CLIPS_DIR --engine groq --limit $LIMIT --min-words $MIN_WORDS --out $outGroq

# 2) Local (faster-whisper) — modelo carregado uma vez so; rode sem outros programas pesados abertos.
#    Se reclamar de memoria, rode antes:  $env:QP1_LOCAL_THREADS = "1"
Write-Host "[2/2] Rodando QP1 no engine local sobre $LIMIT clipes (min-words $MIN_WORDS)..." -ForegroundColor Cyan
& $py $script --manifest $MANIFEST --clips-dir $CLIPS_DIR --engine local --limit $LIMIT --min-words $MIN_WORDS --out $outLocal

Pop-Location

Write-Host ""
Write-Host "Pronto." -ForegroundColor Green
Write-Host "  Groq : $outGroq"  -ForegroundColor Green
Write-Host "  Local: $outLocal" -ForegroundColor Green
Write-Host "Me envie a linha de agregado (WER/CER/meanRTF) que cada execucao imprime no quadro '=== Aggregate ==='." -ForegroundColor Green
