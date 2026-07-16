#!/usr/bin/env pwsh
& "$PSScriptRoot\..\run_tests.ps1" -UnitOnly -SkipSecurity
if ($LASTEXITCODE -ne 0) { exit 1 }
