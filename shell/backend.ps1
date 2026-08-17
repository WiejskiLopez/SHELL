#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Shell backend orchestrator — zbiorczy agregat skryptow per-service.

.DESCRIPTION
    Ten skrypt NIE uruchamia obrazow bezposrednio i NIE ma wlasnej konfiguracji
    dockerowej. Deleguje do skryptu manage.ps1 kazdego mikroserwisu
    (shell/<service>/docker/scripts/manage.ps1) oraz rabbit
    (shell/rabbitmq/docker/scripts/manage.ps1). Kazdy mikroserwis ma wlasny
    docker-compose.yml, wlasne bazy danych (dev_db) i wlasne skrypty.

    Kazdy skrypt per-service zwraca do tego agregatu status (exit code).
    Agregat NIE przerywa pracy po bledzie jednego serwisu - kontynuuje z
    nastepnymi, a na koncu raportuje ktore zakonczyly sie bledem.

    Start calosci = uruchomienie manage.ps1 każdego mikroserwisu po kolei.

    Przyklady:
        .\backend.ps1 up                       # uruchom wszystkie mikroserwisy + rabbit (dev)
        .\backend.ps1 up -Environment prod
        .\backend.ps1 restart                  # restart wszystkich
        .\backend.ps1 restart execution        # restart TYLKO execution (przez jego skrypt)
        .\backend.ps1 redeploy definition      # rebuild + recreate TYLKO definition
        .\backend.ps1 restart rabbit           # restart Rabbit
        .\backend.ps1 logs session             # logi session
        .\backend.ps1 status                   # status calosci (status kazdego mikroserwisu)
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

$results = @()

function Show-Help {
    Write-Host @"
Shell backend orchestrator (zbiorczy agregat skryptow per-service manage.ps1)

Usage:
  .\backend.ps1 <action> [unit] [-Environment dev|prod]

Actions:
  up [unit]                     uruchom wszystkie mikroserwisy (lub jeden przez jego skrypt)
  down [unit]                   zatrzymaj wszystkie (lub jeden)
  restart [unit]                restart wszystkich (lub tylko wskazany mikroserwis)
  redeploy <unit>               rebuild + recreate wskazanego mikroserwisu
  logs [unit]                   logi wszystkich (lub jednego)
  status                        status calosci (status kazdego mikroserwisu)
  test                          uruchom run_tests.ps1
  help                          ten ekran

Units:
  user | definition | session | ingestion | project | scheduling | execution | rabbit

Kazdy mikroserwis ma wlasny skrypt: shell/<service>/docker/scripts/manage.ps1
"@
}

function Get-ServiceScript {
    param([string]$Name)
    $serviceRoot = Join-Path $shellDir $serviceDirs[$Name]
    return Join-Path (Join-Path $serviceRoot "docker") "scripts\manage.ps1"
}

function Invoke-ServiceScriptNoExit {
    param(
        [string]$Name,
        [string]$ScriptAction
    )

    $script = Get-ServiceScript -Name $Name
    if (-not (Test-Path -LiteralPath $script)) {
        Write-Host "Brak skryptu mikroserwisu: $script" -ForegroundColor Red
        $script:results += [PSCustomObject]@{ Unit = $Name; Action = $ScriptAction; Status = "Brak skryptu" }
        return
    }

    & $script $ScriptAction -Environment $Environment
    $code = $LASTEXITCODE
    if ($code -eq 0) {
        $script:results += [PSCustomObject]@{ Unit = $Name; Action = $ScriptAction; Status = "OK" }
    }
    else {
        $script:results += [PSCustomObject]@{ Unit = $Name; Action = $ScriptAction; Status = "Blad ($code)" }
    }
}

function Show-Results {
    Write-Host "`n=== Podsumowanie ===" -ForegroundColor Cyan
    $failed = @($results | Where-Object { $_.Status -ne "OK" })
    $passed = @($results | Where-Object { $_.Status -eq "OK" })
    foreach ($r in $results) {
        $color = if ($r.Status -eq "OK") { "Green" } else { "Red" }
        Write-Host ("  {0,-12} {1,-10} {2}" -f $r.Unit, $r.Action, $r.Status) -ForegroundColor $color
    }
    Write-Host ("Przeszlo: {0}, bledow: {1}" -f $passed.Count, $failed.Count) -ForegroundColor $(if ($failed.Count -eq 0) { "Green" } else { "Yellow" })
}

function Invoke-SingleUnit {
    param(
        [string]$Name,
        [string]$ScriptAction
    )

    if (-not $serviceDirs.Contains($Name)) {
        Write-Host "Nieznany mikroserwisy: '$Name'. Dozwolone: $($serviceDirs.Keys -join ', ')" -ForegroundColor Red
        exit 1
    }
    $result = Invoke-ServiceScriptNoExit -Name $Name -ScriptAction $ScriptAction
    Show-Results
    exit $(if ($script:results[0].Status -eq "OK") { 0 } else { 1 })
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
        if (-not [string]::IsNullOrWhiteSpace($Unit)) {
            Invoke-SingleUnit -Name $Unit -ScriptAction "status"
        }
        else {
            foreach ($bc in $serviceDirs.Keys) {
                Invoke-ServiceScriptNoExit -Name $bc -ScriptAction "status"
            }
            Show-Results
            exit $(if (@($results | Where-Object { $_.Status -ne "OK" }).Count -eq 0) { 0 } else { 1 })
        }
    }

    "up" {
        if (-not [string]::IsNullOrWhiteSpace($Unit)) {
            Invoke-SingleUnit -Name $Unit -ScriptAction "up"
        }
        else {
            Invoke-ServiceScriptNoExit -Name "rabbit" -ScriptAction "up"
            foreach ($bc in $microservices) {
                Invoke-ServiceScriptNoExit -Name $bc -ScriptAction "up"
            }
            Show-Results
            exit $(if (@($results | Where-Object { $_.Status -ne "OK" }).Count -eq 0) { 0 } else { 1 })
        }
    }

    "down" {
        if (-not [string]::IsNullOrWhiteSpace($Unit)) {
            Invoke-SingleUnit -Name $Unit -ScriptAction "down"
        }
        else {
            foreach ($bc in $microservices) {
                Invoke-ServiceScriptNoExit -Name $bc -ScriptAction "down"
            }
            Invoke-ServiceScriptNoExit -Name "rabbit" -ScriptAction "down"
            Show-Results
            exit $(if (@($results | Where-Object { $_.Status -ne "OK" }).Count -eq 0) { 0 } else { 1 })
        }
    }

    "restart" {
        if (-not [string]::IsNullOrWhiteSpace($Unit)) {
            Invoke-SingleUnit -Name $Unit -ScriptAction "restart"
        }
        else {
            foreach ($bc in $microservices) {
                Invoke-ServiceScriptNoExit -Name $bc -ScriptAction "restart"
            }
            Invoke-ServiceScriptNoExit -Name "rabbit" -ScriptAction "restart"
            Show-Results
            exit $(if (@($results | Where-Object { $_.Status -ne "OK" }).Count -eq 0) { 0 } else { 1 })
        }
    }

    "redeploy" {
        if ([string]::IsNullOrWhiteSpace($Unit)) {
            Write-Host "redeploy wymaga wskazania mikroserwisu: <bc> | rabbit" -ForegroundColor Red
            exit 1
        }
        Invoke-SingleUnit -Name $Unit -ScriptAction "redeploy"
    }

    "logs" {
        if ([string]::IsNullOrWhiteSpace($Unit)) {
            Write-Host "logs wymaga wskazania mikroserwisu: <bc> | rabbit" -ForegroundColor Red
            exit 1
        }
        Invoke-SingleUnit -Name $Unit -ScriptAction "logs"
    }
}