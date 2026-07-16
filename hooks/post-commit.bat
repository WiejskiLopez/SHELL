@echo off
pwsh.exe -ExecutionPolicy Bypass -NoProfile -Command "docker compose -f docker/dev/docker-compose.yml build"
if %errorlevel% neq 0 exit /b %errorlevel%
