@echo off
setlocal

set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."
python "%SCRIPT_DIR%open_split_models_operational_conversion_dashboard.py"
set EXIT_CODE=%ERRORLEVEL%
popd

exit /b %EXIT_CODE%
