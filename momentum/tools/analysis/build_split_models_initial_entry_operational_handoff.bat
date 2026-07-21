@echo off
setlocal

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%build_split_models_initial_entry_operational_handoff.py" %*
exit /b %ERRORLEVEL%
