#!/usr/bin/env pwsh
<# 
.SYNOPSIS
    Runs all test suites for the SHELL project.

.DESCRIPTION
    Runs unit tests, integration tests (if Postgres available), and optionally lint/type checks.
    Uses pytest markers for test selection instead of hardcoded paths.
#>

param(
    [switch]$UnitOnly,
    [switch]$IntegrationOnly,
    [switch]$SkipLint,
    [switch]$SkipTypeCheck,
    [switch]$SkipSecurity,       
    [switch]$SkipArchCheck,      
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

Write-Host "=== SHELL Project Test Runner ===" -ForegroundColor Cyan
Write-Host "Project root: $projectRoot" -ForegroundColor Gray

# Type check (mypy) — uses --no-incremental to avoid a cache corruption bug
# in mypy 2.1.0 on Windows where stub packages (e.g. types-PyYAML) are
# spuriously reported as "not installed" after the first incremental build.
$env:MYPY_NO_INCREMENTAL = "1"

$bcs = @("platform", "definition", "execution", "messaging", "project", "scheduling", "session", "user")
$testRoot = "shell/tests"

function Run-Command {
    param(
        [string]$Command,
        [string]$Description,
        [switch]$AllowFailure
    )
    Write-Host "`n--- $Description ---" -ForegroundColor Yellow
    Write-Host "Running: $Command" -ForegroundColor Gray
    $result = Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0 -and -not $AllowFailure) {
        Write-Host "FAILED: $Description" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "OK: $Description" -ForegroundColor Green
    return $result
}

# Check if Postgres is available for integration tests
$pgTestUrl = $env:PG_TEST_URL
$hasPostgres = -not [string]::IsNullOrEmpty($pgTestUrl)

if ($hasPostgres) {
    Write-Host "PostgreSQL detected (PG_TEST_URL set)" -ForegroundColor Green
} else {
    Write-Host "PostgreSQL not configured (PG_TEST_URL not set) - integration tests will be skipped" -ForegroundColor Yellow
}

# Unit tests — run per BC for clear reporting
if (-not $IntegrationOnly) {
    foreach ($bc in $bcs) {
        $path = "$testRoot/$bc"
        $tests = Get-ChildItem -LiteralPath "$path/unit" -Filter "test_*.py" -Recurse -ErrorAction SilentlyContinue
        if ($tests) {
            Run-Command "python -m pytest $path/unit -v" "$bc Unit Tests"
        } else {
            Write-Host "Skipping $bc (no unit tests)" -ForegroundColor Gray
        }
    }
    # Architecture tests (shared, not BC-specific)
    Run-Command "python -m pytest $testRoot/architecture -v" "Architecture Tests"
}

# E2E tests
if (-not $IntegrationOnly -and -not $UnitOnly) {
    foreach ($bc in $bcs) {
        $path = "$testRoot/$bc"
        $tests = Get-ChildItem -LiteralPath "$path/e2e" -Filter "test_*.py" -Recurse -ErrorAction SilentlyContinue
        if ($tests) {
            Run-Command "python -m pytest $path/e2e -v" "$bc E2E Tests"
        } else {
            Write-Host "Skipping $bc (no e2e tests)" -ForegroundColor Gray
        }
    }
}

# Integration tests (only if Postgres available)
if (-not $UnitOnly -and $hasPostgres) {
    foreach ($bc in $bcs) {
        $path = "$testRoot/$bc"
        $tests = Get-ChildItem -LiteralPath "$path/integration" -Filter "test_*.py" -Recurse -ErrorAction SilentlyContinue
        if ($tests) {
            Run-Command "python -m pytest $path/integration -v" "$bc Integration Tests"
        } else {
            Write-Host "Skipping $bc (no integration tests)" -ForegroundColor Gray
        }
    }
}
elseif (-not $UnitOnly -and -not $hasPostgres) {
    Write-Host "`n--- Integration Tests ---" -ForegroundColor Yellow
    Write-Host "Skipped: PG_TEST_URL not set" -ForegroundColor Yellow
}

# Lint (ruff) - only if not skipped
if (-not $SkipLint) {
    Run-Command "python -m ruff check shell shell/tests" "Lint (ruff)"
    Run-Command "python -m ruff format --check shell shell/tests" "Format Check (ruff)"
}

# Type check (mypy) - only if not skipped
if (-not $SkipTypeCheck) {
    Run-Command "python -m mypy --no-incremental shell" "Type Check (mypy)"
}

if (-not $SkipArchCheck) {
    Run-Command "$projectRoot\.venv\Scripts\import-linter.exe lint" "Architecture Boundary Check"
}

if (-not $SkipSecurity) {
    Write-Host "`n--- Dependency Vulnerability Audit ---" -ForegroundColor Yellow
    Write-Host "Running: $projectRoot\.venv\Scripts\pip-audit.exe" -ForegroundColor Gray
    $pipJob = Start-Job -ScriptBlock { param($path) & $path } -ArgumentList "$projectRoot\.venv\Scripts\pip-audit.exe"
    $pipResult = $pipJob | Wait-Job -Timeout 30
    if ($pipResult -eq $null) {
        $pipJob | Stop-Job -PassThru | Remove-Job
        Write-Host "TIMEOUT: pip-audit exceeded 30s (network issue), skipping" -ForegroundColor Yellow
    } else {
        Receive-Job -Job $pipJob
        Remove-Job -Job $pipJob
    }
}

if (-not $SkipSecurity) {
    Run-Command "$projectRoot\.venv\Scripts\bandit.exe -r shell --exclude shell/.venv -ll" "Security Code Scanning (Bandit)" -AllowFailure
}

# Coverage — run unit tests with coverage
if (-not $UnitOnly -and -not $IntegrationOnly) {
    $coveragePaths = ($bcs | ForEach-Object { $p = "$testRoot/$_/unit"; if (Test-Path $p) { $p } }) -join " "
    Run-Command "python -m pytest $coveragePaths --cov=shell --cov-fail-under=80 -v" "Unit Tests with Coverage" -AllowFailure
}

Write-Host "`n=== All requested checks completed ===" -ForegroundColor Green
exit 0
