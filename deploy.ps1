#!/usr/bin/env pwsh
param(
    [string]$Message = "auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "=== Krok 1: Testy ===" -ForegroundColor Cyan
& "$PSScriptRoot\run_tests.ps1" -UnitOnly -SkipSecurity
if ($LASTEXITCODE -ne 0) {
    Write-Host "Testy nie przeszły — deploy anulowany" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Krok 2: Commit ===" -ForegroundColor Cyan
git add -A
git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "Commit anulowany (brak zmian lub błąd)" -ForegroundColor Yellow
}

Write-Host "`n=== Krok 3: Build obrazu ===" -ForegroundColor Cyan
docker compose -f docker/dev/docker-compose.yml build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build obrazu nie powiódł się" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Deploy zakończony ===" -ForegroundColor Green
