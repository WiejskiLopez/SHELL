#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Shell backend orchestrator — uruchamia skrypty poszczegolnych mikroserwisow.

.DESCRIPTION
    Ten skrypt NIE uruchamia obrazow bezposrednio. Deleguje do skryptu manage.ps1
    kazdego mikroserwisu (shell/<service>/docker/scripts/manage.ps1) oraz rabbit
    (shell/rabbitmq/docker/scripts/manage.ps1). Dzieki temu z tego poziomu mozesz
    zrestartowac/zdeployowac kazdy mikroserwis z osobna, uzywajac jego wlasnego skryptu.

    Start calosci = uruchomienie manage.ps1 każdego mikroserwisu po kolei.

    Przyklady:
        .\backend.ps1 up                       # uruchom wszystkie mikroserwisy + rabbit (dev)
        .\backend.ps1 up -Environment prod
        .\backend.ps1 restart                  # restart wszystkich
        .\backend.ps1 restart execution        # restart TYLKO execution (przez jego skrypt)
        .\backend.ps1 redeploy definition      # rebuild + recreate TYLKO definition
        .\backend.ps1 restart rabbit           # restaRT Rabbit
        .\backend.ps1 logs session             # logi session
        .\backend.ps1 status                   # status calosci
        .\backend.ps1 test                     # uruchom run_tests.ps1
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false, Position = 0)]
    [ValidateSet("up", "down", "restart", "redeploy", "logs", "status", "test", "help")]
    [string]$Action = "help",

    [Parameter(Mandatory = $false, Position = 1)]
    [AllowEmptyString()]
    [string]$Unit = "",

    [Parameter(Mandatory = $false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"
$shellDir = $PSScriptRoot
$projectRoot = (Split-Path -Parent $shellDir)

$serviceDirs = [ordered]@{
    user         = "user_service"
    definition   = "definition_service"
    session      = "session_service"
    ingestion    = "ingestion_service"
    project      = "project_service"
    scheduling   = "scheduling_service"
    execution    = "execution_service"
    rabbit       = "rabbitmq"
}

function Show-Help {
    Write-Host @"
Shell backend orchestrator (deleguje do skryptow poszczegolnych mikroserwisow)

Usage:
  .\backend.ps1 <action> [unit] [-Environment dev|prod]

Actions:
  up [unit]                     uruchom wszystkie mikroserwisy (lub jeden przez jego skrypt)
  down [unit]                   zatrzymaj wszystkie (lub jeden)
  restart [unit]                restart wszystkich (lub tylko wskazany mikroserwis)
  redeploy <unit>               rebuild + recreate wskazanego mikroserwisu
  logs [unit]                   logi wszystkich (lub jednego)
  status                        status calosci (docker compose ps)
  test                          uruchom run_tests.ps1
  help                          ten ekran

Units:
  user | definition | session | ingestion | project | scheduling | execution | rabbit

Kazdy mikroserwis ma wlasny skrypt: shell/<service>/docker/scripts/manage.ps1
"@
}

function Invoke-ServiceScript {
    param(
        [string]$Name,
        [string]$ScriptAction
    )

    if (-not $serviceDirs.Contains($Name)) {
        Write-Host "Nieznany mikroserwis: '$Name'. Dozwolone: $($serviceDirs.Keys -join ', ')" -ForegroundColor Red
        exit 1
    }

    $serviceRoot = Join-Path $shellDir $serviceDirs[$Name]
    $script = Join-Path (Join-Path $serviceRoot "docker") "scripts\manage.ps1"
    if (-not (Test-Path -LiteralPath $script)) {
        Write-Host "Brak skryptu mikroserwisu: $script" -ForegroundColor Red
        exit 1
    }

    & $script $ScriptAction -Environment $Environment
    exit $LASTEXITCODE
}

function Invoke-ServiceScriptNoExit {
    param(
        [string]$Name,
        [string]$ScriptAction
    )

    $serviceRoot = Join-Path $shellDir $serviceDirs[$Name]
    $script = Join-Path (Join-Path $serviceRoot "docker") "scripts\manage.ps1"
    if (-not (Test-Path -LiteralPath $script)) {
        Write-Host "Brak skryptu mikroserwisu: $script" -ForegroundColor Red
        exit 1
    }

    & $script $ScriptAction -Environment $Environment
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Blad skryptu $Name ($ScriptAction): $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

function Invoke-RabbitScript {
    param([string]$ScriptAction)
    Invoke-ServiceScriptNoExit -Name "rabbit" -ScriptAction $ScriptAction
}

if ($Action -eq "help" -or $Action -eq "") {
    Show-Help
    exit 0
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker nie jest dostepny w PATH" -ForegroundColor Red
    exit 1
}

$microservices = @("user", "definition", "session", "ingestion", "project", "scheduling", "execution")

switch ($Action) {
    "test" {
        & (Join-Path $projectRoot "run_tests.ps1")
        exit $LASTEXITCODE
    }

    "status" {
        $baseFile = Join-Path $projectRoot "docker\docker-compose.yml"
        $overrideFile = Join-Path $projectRoot "docker\docker-compose.$Environment.yml"
        docker compose -f $baseFile -f $overrideFile ps
        exit $LASTEXITCODE
    }

    "up" {
        if (-not [string]::IsNullOrWhiteSpace($Unit)) {
            Invoke-ServiceScript -Name $Unit -ScriptAction "up"
        }
        else {
            Invoke-RabbitScript -ScriptAction "up"
            foreach ($bc in $microservices) {
                Invoke-ServiceScriptNoExit -Name $bc -ScriptAction "up"
            }
        }
    }

    "down" {
        if (-not [string]::IsNullOrWhiteSpace($Unit)) {
            Invoke-ServiceScript -Name $Unit -ScriptAction "down"
        }
        else {
            foreach ($bc in $microservices) {
                Invoke-ServiceScriptNoExit -Name $bc -ScriptAction "down"
            }
            Invoke-RabbitScript -ScriptAction "down"
        }
    }

    "restart" {
        if (-not [string]::IsNullOrWhiteSpace($Unit)) {
            Invoke-ServiceScript -Name $Unit -ScriptAction "restart"
        }
        else {
            foreach ($bc in $microservices) {
                Invoke-ServiceScriptNoExit -Name $bc -ScriptAction "restart"
            }
            Invoke-RabbitScript -ScriptAction "restart"
        }
    }

    "redeploy" {
        if ([string]::IsNullOrWhiteSpace($Unit)) {
            Write-Host "redeploy wymaga wskazania mikroserwisu: <bc> | rabbit" -ForegroundColor Red
            exit 1
        }
        Invoke-ServiceScript -Name $Unit -ScriptAction "redeploy"
    }

    "logs" {
        if ([string]::IsNullOrWhiteSpace($Unit)) {
            Write-Host "logs wymaga wskazania mikroserwisu: <bc> | rabbit" -ForegroundColor Red
            exit 1
        }
        Invoke-ServiceScript -Name $Unit -ScriptAction "logs"
    }
}