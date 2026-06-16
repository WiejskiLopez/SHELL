#!/usr/bin/env pwsh
<# 
.SYNOPSIS
    Runs all test suites for the SHELL project.

.DESCRIPTION
    Runs unit tests, integration tests (if Postgres available), and optionally lint/type checks.
#>

param(
    [switch]$UnitOnly,
    [switch]$IntegrationOnly,
    [switch]$SkipLint,
    [switch]$SkipTypeCheck,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

Write-Host "=== SHELL Project Test Runner ===" -ForegroundColor Cyan
Write-Host "Project root: $projectRoot" -ForegroundColor Gray

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

# Unit tests
if (-not $IntegrationOnly) {
    Run-Command "python -m pytest shell/tests/unit -v" "Unit Tests"
}

# E2E tests
if (-not $IntegrationOnly -and -not $UnitOnly) {
    Run-Command "python -m pytest shell/tests/e2e -v" "E2E Tests"
}

# Integration tests (only if Postgres available)
if (-not $UnitOnly -and $hasPostgres) {
    Run-Command "python -m pytest shell/tests/integration -v" "Integration Tests (PostgreSQL)"
}
elseif (-not $UnitOnly -and -not $hasPostgres) {
    Write-Host "`n--- Integration Tests (PostgreSQL) ---" -ForegroundColor Yellow
    Write-Host "Skipped: PG_TEST_URL not set" -ForegroundColor Yellow
}

# Lint (ruff) - only if not skipped
if (-not $SkipLint) {
    Run-Command "python -m ruff check shell tests" "Lint (ruff)" -AllowFailure
    Run-Command "python -m ruff format --check shell tests" "Format Check (ruff)" -AllowFailure
}

# Type check (mypy) - only if not skipped
if (-not $SkipTypeCheck) {
    Run-Command "python -m mypy shell" "Type Check (mypy)" -AllowFailure
}

Write-Host "`n=== All requested checks completed ===" -ForegroundColor Green