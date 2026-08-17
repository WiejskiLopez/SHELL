#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Zarzadza kontenerem RabbitMQ w projekcie shell-dev.

.DESCRIPTION
    Wrapper na docker compose scoped do uslugi rabbitmq. Uzywa wlasnego
    docker-compose.yml - bez zadnej wspolnej orkiestracji.
    Uruchamiaj go bezposrednio lub przez ..\..\..\..\backend.ps1.

    Odpornosc:
      - up: jesli kontener juz istnieje (z innego projektu) jest usuwany i
        tworzony na nowo - skrypt nigdy nie pada z powodu istniejacego kontenera.
      - restart: jesli kontener nie dziala -> up; jesli dziala -> stop + start.

    Przyklady:
        .\docker\scripts\manage.ps1 up       # start Rabbit
        .\docker\scripts\manage.ps1 restart  # restart Rabbit
        .\docker\scripts\manage.ps1 redeploy # force-recreate (gdy obraz sie zmienil)
        .\docker\scripts\manage.ps1 down     # zatrzymaj i usun kontener
        .\docker\scripts\manage.ps1 logs     # podazaj za logami
        .\docker\scripts\manage.ps1 status   # status kontenera
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

$targetServices = @("rabbitmq")
$containerNames = @("shell-rabbitmq")

Write-Host "rabbit [$Action] ($Environment)" -ForegroundColor Cyan

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
            Write-Host "  Rabbit nie dziala - uruchamiam (up)" -ForegroundColor Yellow
            Invoke-Up
        }
        else {
            & docker compose @composeArgs restart @targetServices 2>&1 | Out-Host
            exit $LASTEXITCODE
        }
    }
    "redeploy" { Remove-StaleContainers; & docker compose @composeArgs up -d --force-recreate @targetServices 2>&1 | Out-Host; exit $LASTEXITCODE }
    "logs"     { & docker compose @composeArgs logs -f --tail 200 @targetServices 2>&1 | Out-Host; exit $LASTEXITCODE }
    "status"   { & docker compose @composeArgs ps @targetServices 2>&1 | Out-Host; exit $LASTEXITCODE }
}