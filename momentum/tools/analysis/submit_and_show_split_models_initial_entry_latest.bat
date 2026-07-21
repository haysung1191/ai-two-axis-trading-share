@echo off
setlocal

set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."
python "%SCRIPT_DIR%submit_and_show_split_models_initial_entry_latest.py" %*
set EXIT_CODE=%ERRORLEVEL%
popd

exit /b %EXIT_CODE%
