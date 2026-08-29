#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Zarzadza kontenerami mikroserwisu user (api + worker) w projekcie shell-dev.

.DESCRIPTION
    Wrapper na docker compose scoped do tego BC. Uzywa wlasnego
    docker-compose.yml serwisu - bez zadnej wspolnej orkiestracji.
    Uruchamiaj go bezposrednio lub przez ..\..\..\..\backend.ps1.

    Odpornosc:
      - up: jesli kontener juz istnieje (z innego projektu) jest usuwany i
        tworzony na nowo - skrypt nigdy nie pada z powodu istniejacego kontenera.
      - restart: jesli kontener nie dziala -> up; jesli dziala -> stop + start.

    Przyklady:
        .\docker\scripts\manage.ps1 up       # start kontenerow user
        .\docker\scripts\manage.ps1 restart  # restart kontenerow user
        .\docker\scripts\manage.ps1 redeploy # rebuild + recreate
        .\docker\scripts\manage.ps1 down     # zatrzymaj i usun kontenery
        .\docker\scripts\manage.ps1 logs     # podazaj za logami
        .\docker\scripts\manage.ps1 status   # status kontenerow BC
        .\docker\scripts\manage.ps1 up -Environment prod
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, Position = 0)]
    [ValidateSet("up", "down", "restart", "redeploy", "logs", "status")]
    [string]$Action = "up",

    [Parameter(Mandatory = $false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Continue"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker nie jest dostepny w PATH" -ForegroundColor Red
    exit 1
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$composeFile = Join-Path $PSScriptRoot "..\docker-compose.yml"

$composeArgs = @("-f", $composeFile)
if ($Environment -eq "prod") {
    $envFile = Join-Path $projectRoot ".env.prod"
    if (Test-Path -LiteralPath $envFile) {
        $composeArgs += @("--env-file", $envFile)
    }
}

$targetServices = @("shell-user-api", "shell-user-worker")
$containerNames = @("shell-user-shell-user-api-1", "shell-user-shell-user-worker-1")

Write-Host "user [$Action] ($Environment)" -ForegroundColor Cyan

function Remove-StaleContainers {
    foreach ($name in $containerNames) {
        $candidate = docker ps -a --filter "name=^/$name$" --format "{{.ID}}" 2>$null
        if ($candidate) {
            Write-Host "  Istniejacy kontener $name - usuwam i utworzy na nowo" -ForegroundColor Yellow
            docker rm -f $name 2>$null | Out-Null
        }
    }
}

function Invoke-Up {
    Remove-StaleContainers
    & docker compose @composeArgs up -d @targetServices 2>&1 | Out-Host
    exit $LASTEXITCODE
}

switch ($Action) {
    "up"       { Invoke-Up }
    "down"     { & docker compose @composeArgs down @targetServices 2>&1 | Out-Host; exit $LASTEXITCODE }
    "restart"  {
        $running = docker compose @composeArgs ps -q @targetServices 2>$null
        if ([string]::IsNullOrWhiteSpace($running)) {
            Write-Host "  Serwis nie dziala - uruchamiam (up)" -ForegroundColor Yellow
            Invoke-Up
        }
        else {
            & docker compose @composeArgs restart @targetServices 2>&1 | Out-Host
            exit $LASTEXITCODE
        }
    }
    "redeploy" { Remove-StaleContainers; & (Join-Path $projectRoot "scripts\prepare_mtls_ca.ps1"); if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; $env:CERTIFICATE_BUILD_ID = "user-$([DateTime]::UtcNow.ToString('yyyyMMddHHmmssfff'))-$PID"; & docker compose @composeArgs up -d --build @targetServices 2>&1 | Out-Host; exit $LASTEXITCODE }
    "logs"     { & docker compose @composeArgs logs -f --tail 200 @targetServices 2>&1 | Out-Host; exit $LASTEXITCODE }
    "status"   { & docker compose @composeArgs ps @targetServices 2>&1 | Out-Host; exit $LASTEXITCODE }
}