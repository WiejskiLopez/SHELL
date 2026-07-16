@echo off
pwsh.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0pre-commit.ps1"
if %errorlevel% neq 0 exit /b %errorlevel%
