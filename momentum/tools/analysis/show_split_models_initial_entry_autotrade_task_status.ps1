$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ScriptPath = Join-Path $PSScriptRoot "show_split_models_initial_entry_autotrade_task_status.py"

Push-Location $RepoRoot
try {
    python $ScriptPath @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
