$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$OpenScript = Join-Path $PSScriptRoot "open_split_models_operational_conversion_dashboard.py"

Push-Location $RepoRoot
try {
    python $OpenScript
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
