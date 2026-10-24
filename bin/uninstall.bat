@echo off
setlocal
set "CALLER_DIR=%CD%"
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\PeriodCompare.ps1" Uninstall %*
endlocal
