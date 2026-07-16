#!/usr/bin/env pwsh
param(
    [string]$Message = "auto: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "=== Krok 1: Testy ===" -ForegroundColor Cyan
& "$PSScriptRoot\run_tests.ps1" -UnitOnly -SkipSecurity
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

Write-Host "`n=== Krok 3: Build obrazu ===" -ForegroundColor Cyan
docker compose -f docker/dev/docker-compose.yml build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build obrazu nie powiodl sie" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Krok 4: Restart kontenera ===" -ForegroundColor Cyan
docker compose -f docker/dev/docker-compose.yml down --remove-orphans
docker compose -f docker/dev/docker-compose.yml up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Restart kontenera nie powiodl sie" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Deploy zakonczony ===" -ForegroundColor Green
