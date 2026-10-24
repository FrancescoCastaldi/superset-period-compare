@echo off
setlocal
set "CALLER_DIR=%CD%"
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\installer\PeriodCompare.ps1" DryRun %*
endlocal
