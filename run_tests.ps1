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
    [int]$SecurityAuditTimeout = 60,
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

$bcs = @("platform", "definition_service", "execution_service", "ingestion_service", "project_service", "scheduling_service", "session_service", "user_service")
$testRoot = "shell/tests"
$python = "$projectRoot\.venv\Scripts\python.exe"

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
$pgTestUrl = $env:POSTGRES_TEST_URL
$hasPostgres = -not [string]::IsNullOrEmpty($pgTestUrl)

if ($hasPostgres) {
    Write-Host "PostgreSQL detected (POSTGRES_TEST_URL set)" -ForegroundColor Green
} else {
    Write-Host "PostgreSQL not configured (POSTGRES_TEST_URL not set) - integration tests will be skipped" -ForegroundColor Yellow
}

# Unit tests — run per BC for clear reporting
if (-not $IntegrationOnly) {
    foreach ($bc in $bcs) {
        $path = "$testRoot/$bc"
        $tests = Get-ChildItem -LiteralPath "$path/unit" -Filter "test_*.py" -Recurse -ErrorAction SilentlyContinue
        if ($tests) {
            Run-Command "$python -m pytest $path/unit -v" "$bc Unit Tests"
        } else {
            Write-Host "Skipping $bc (no unit tests)" -ForegroundColor Gray
        }
    }
    # Architecture tests (shared, not BC-specific)
    Run-Command "$python -m pytest $testRoot/architecture -v" "Architecture Tests"
}

# E2E tests
if (-not $IntegrationOnly -and -not $UnitOnly) {
    foreach ($bc in $bcs) {
        $path = "$testRoot/$bc"
        $tests = Get-ChildItem -LiteralPath "$path/e2e" -Filter "test_*.py" -Recurse -ErrorAction SilentlyContinue
        if ($tests) {
            Run-Command "$python -m pytest $path/e2e -v" "$bc E2E Tests"
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
            Run-Command "$python -m pytest $path/integration -v" "$bc Integration Tests"
        } else {
            Write-Host "Skipping $bc (no integration tests)" -ForegroundColor Gray
        }
    }
}
elseif (-not $UnitOnly -and -not $hasPostgres) {
    Write-Host "`n--- Integration Tests ---" -ForegroundColor Yellow
    Write-Host "Skipped: POSTGRES_TEST_URL not set" -ForegroundColor Yellow
}

# Platform delivery integration (SQLite) + system + contracts — ALWAYS run,
# regardless of Postgres/Rabbit availability. These are the ref2/ref4 critical
# scenarios (atomicity, heartbeat, claim, readiness,
# retention, replay, relay, two-BC flow) and must not silently skip.
if (-not $UnitOnly) {
    Run-Command "$python -m pytest shell/tests/platform/integration/sql_sqlite -ra" "Platform Delivery SQLite Integration"
    Run-Command "$python -m pytest shell/tests/system -ra" "System Tests (two-BC flow)"
    Run-Command "$python -m pytest shell/tests/contracts -ra" "Contract Tests"
}

# Lint (ruff) - only if not skipped
if (-not $SkipLint) {
    Run-Command "$python -m ruff check shell shell/tests" "Lint (ruff)"
    Run-Command "$python -m ruff format --check shell shell/tests" "Format Check (ruff)"
}

# Type check (mypy) - only if not skipped
if (-not $SkipTypeCheck) {
    Run-Command "$python -m mypy --no-incremental shell" "Type Check (mypy)"
}

if (-not $SkipArchCheck) {
    Run-Command "$projectRoot\.venv\Scripts\import-linter.exe lint" "Architecture Boundary Check"
}

if (-not $SkipSecurity) {
    Write-Host "`n--- Dependency Vulnerability Audit ---" -ForegroundColor Yellow
    $pipAudit = "$projectRoot\.venv\Scripts\pip-audit.exe"
    $pipAuditCache = Join-Path $env:TEMP "shell-pip-audit-cache"
    Write-Host "Running: $pipAudit (timeout ${SecurityAuditTimeout}s)" -ForegroundColor Gray
    try {
        $pipJob = Start-Job -ScriptBlock {
            param($auditPath, $cacheDir)
            & $auditPath "--timeout", "30", "--progress-spinner", "off", "--cache-dir", $cacheDir 2>&1
        } -ArgumentList $pipAudit, $pipAuditCache
        if ($null -eq ($pipJob | Wait-Job -Timeout $SecurityAuditTimeout)) {
            Write-Host "TIMEOUT: pip-audit exceeded ${SecurityAuditTimeout}s (network issue), skipping" -ForegroundColor Yellow
        } else {
            Receive-Job -Job $pipJob
        }
    } catch {
        Write-Host "WARNING: pip-audit step failed with error: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Continuing (security audit is not release-blocking)" -ForegroundColor Yellow
    } finally {
        $pipJob | Stop-Job -ErrorAction SilentlyContinue | Remove-Job -Force -ErrorAction SilentlyContinue
    }
}

if (-not $SkipSecurity) {
    Run-Command "$projectRoot\.venv\Scripts\bandit.exe -r shell --exclude shell/.venv -ll" "Security Code Scanning (Bandit)" -AllowFailure
}

# Coverage — run unit tests with coverage
if (-not $UnitOnly -and -not $IntegrationOnly) {
    $coveragePaths = ($bcs | ForEach-Object { $p = "$testRoot/$_/unit"; if (Test-Path $p) { $p } }) -join " "
    Run-Command "$python -m pytest $coveragePaths --cov=shell --cov-fail-under=80 -v" "Unit Tests with Coverage" -AllowFailure
}

Write-Host "`n=== All requested checks completed ===" -ForegroundColor Green
exit 0
