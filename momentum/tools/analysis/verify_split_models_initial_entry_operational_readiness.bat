@echo off
setlocal

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%verify_split_models_initial_entry_operational_readiness.py" %*
exit /b %ERRORLEVEL%
