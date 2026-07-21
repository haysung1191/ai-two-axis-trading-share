$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ScriptPath = Join-Path $PSScriptRoot "auto_trade_split_models_initial_entry.py"

Push-Location $RepoRoot
try {
    python $ScriptPath @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
