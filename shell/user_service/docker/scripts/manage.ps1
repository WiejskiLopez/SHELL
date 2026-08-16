#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Zarzadza kontenerami mikroserwisu user (api + worker) w projekcie shell-dev.

.DESCRIPTION
    Wrapper nakladka na docker compose (base + env overlay) scoped do tego BC.
    Wymaga gotowych obrazow i konfiguracji w docker/docker-compose.*.

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

$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker nie jest dostepny w PATH" -ForegroundColor Red
    exit 1
}

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$baseFile = Join-Path $projectRoot "docker\docker-compose.yml"
$overrideFile = Join-Path $projectRoot "docker\docker-compose.$Environment.yml"

$composeArgs = @("-f", $baseFile, "-f", $overrideFile)
if ($Environment -eq "prod") {
    $envFile = Join-Path $projectRoot ".env.prod"
    if (Test-Path -LiteralPath $envFile) {
        $composeArgs += @("--env-file", $envFile)
    }
}

$targetServices = @("shell-user-api", "shell-user-worker")

Write-Host "user [$Action] ($Environment)" -ForegroundColor Cyan

switch ($Action) {
    "up"       { & docker compose @composeArgs up -d @targetServices; exit $LASTEXITCODE }
    "down"     { & docker compose @composeArgs down @targetServices; exit $LASTEXITCODE }
    "restart"  { & docker compose @composeArgs restart @targetServices; exit $LASTEXITCODE }
    "redeploy" { & docker compose @composeArgs up -d --build @targetServices; exit $LASTEXITCODE }
    "logs"     { & docker compose @composeArgs logs -f --tail 200 @targetServices; exit $LASTEXITCODE }
    "status"   { & docker compose @composeArgs ps @targetServices; exit $LASTEXITCODE }
}