$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ScriptPath = Join-Path $PSScriptRoot "refresh_and_show_split_models_initial_entry_latest.py"

Push-Location $RepoRoot
try {
    python $ScriptPath @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
