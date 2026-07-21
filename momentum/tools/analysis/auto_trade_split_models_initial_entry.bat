@echo off
setlocal

set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."
python "%SCRIPT_DIR%auto_trade_split_models_initial_entry.py" %*
set EXIT_CODE=%ERRORLEVEL%
popd

exit /b %EXIT_CODE%
