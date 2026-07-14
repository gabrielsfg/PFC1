# Roda TODOS os testes da QP2 (personas, INVEST, kappa) com um comando.
# Nao precisa ativar venv. Use:  .\evaluation\run_qp2.ps1
# (a partir da raiz do projeto C:\Users\gabri\Tcc)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot          # raiz do projeto
$py   = Join-Path $root "agente-identificacao\venv\Scripts\python.exe"
$eval = Join-Path $root "evaluation"
$pred = Join-Path $root "agente-identificacao\data\output"

if (-not (Test-Path $py)) {
    Write-Host "ERRO: venv do agente-identificacao nao encontrado em $py" -ForegroundColor Red
    Write-Host "Crie com:  py -3.11 -m venv agente-identificacao\venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " QP2.1 - Personas (Precisao / Revocacao / F1)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
& $py (Join-Path $eval "qp2_personas.py") `
    --pred-dir $pred `
    --gold (Join-Path $eval "gold_roles.json") `
    --aliases (Join-Path $eval "aliases.json") `
    --out (Join-Path $eval "results_qp2_personas.csv")

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " QP2.3 - Kappa de Cohen (juiz x humano)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
& $py (Join-Path $eval "qp2_kappa.py") `
    --human (Join-Path $eval "kappa_amostra_anotada_FINAL.csv") `
    --judge (Join-Path $eval "kappa_amostra_gabarito_juiz.csv")

Write-Host ""
Write-Host "Para re-rodar o INVEST (gasta API), use:" -ForegroundColor Yellow
Write-Host "  cd agente-identificacao" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\python.exe ..\evaluation\qp2_invest.py --pred-dir data\output --model claude-sonnet-4-6 --out ..\evaluation\results_qp2_invest_sonnet.csv" -ForegroundColor Yellow
