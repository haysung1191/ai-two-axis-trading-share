@echo off
setlocal

set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."
python "%SCRIPT_DIR%show_split_models_initial_entry_autotrade_task_status.py" %*
set EXIT_CODE=%ERRORLEVEL%
popd

exit /b %EXIT_CODE%
