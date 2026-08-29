param(
    [string]$CaDirectory = (Join-Path $PSScriptRoot "..\shell\certs"),
    [int]$LifetimeDays = 1825,
    [switch]$Force
)

$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$arguments = @(
    "-m", "shell.certificates", "ensure-ca",
    "--ca-dir", $CaDirectory,
    "--lifetime-days", $LifetimeDays
)
if ($Force) {
    $arguments += "--force"
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Unable to prepare the SHELL mTLS CA"
}
