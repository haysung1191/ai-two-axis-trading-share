@echo off
setlocal

set SCRIPT_DIR=%~dp0
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_btc_1d_shadow_update_and_open.ps1"
set EXIT_CODE=%ERRORLEVEL%

endlocal & exit /b %EXIT_CODE%
