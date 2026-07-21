@echo off
setlocal

set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1"
exit /b %ERRORLEVEL%
