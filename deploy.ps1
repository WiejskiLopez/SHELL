#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy SHELL: format + testy + commit + openapi + start wszystkich obrazow.

.DESCRIPTION
    Obrazy NIE sa uruchamiane bezposrednio przez ten skrypt - budowane i wznawiane
    sa przez skrypty per-service (shell/<service>/docker/scripts/manage.ps1 oraz
    shell/rabbitmq/docker/scripts/manage.ps1). Ten skrypt jedynie je wywoluje
    po kolei, jako zbiorczy orchestrator deployu.
#>
param(
    [string]$Message = "auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "=== Krok 0: Autoformat ===" -ForegroundColor Cyan
python -m ruff format shell/ shell/tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "Autoformat nie powiodl sie" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Krok 1: Testy ===" -ForegroundColor Cyan
& "$PSScriptRoot\run_tests.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Testy nie przeszly - deploy anulowany" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Krok 2: Commit ===" -ForegroundColor Cyan
git add -A
git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "Commit anulowany (brak zmian lub blad)" -ForegroundColor Yellow
}

Write-Host "`n=== Krok 3: OpenAPI spec ===" -ForegroundColor Cyan
python scripts/generate-openapi.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Generowanie openapi nie powiodlo sie" -ForegroundColor Red
    exit 1
}

$shellDir = Join-Path $PSScriptRoot "shell"
$services = [ordered]@{
    user         = "shell\user_service\docker\scripts\manage.ps1"
    definition   = "shell\definition_service\docker\scripts\manage.ps1"
    session      = "shell\session_service\docker\scripts\manage.ps1"
    ingestion    = "shell\ingestion_service\docker\scripts\manage.ps1"
    project      = "shell\project_service\docker\scripts\manage.ps1"
    scheduling   = "shell\scheduling_service\docker\scripts\manage.ps1"
    execution    = "shell\execution_service\docker\scripts\manage.ps1"
    rabbit       = "shell\rabbitmq\docker\scripts\manage.ps1"
}

Write-Host "`n=== Krok 4: Build + start obrazow (per-service) ===" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot $services["rabbit"]) up
if ($LASTEXITCODE -ne 0) {
    Write-Host "Start rabbit nie powiodl sie" -ForegroundColor Red
    exit 1
}

foreach ($name in $services.Keys) {
    if ($name -eq "rabbit") {
        continue
    }
    Write-Host "--- $name ---" -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot $services[$name]) redeploy
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Redeploy $name nie powiodl sie" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n=== Deploy zakonczony ===" -ForegroundColor Green