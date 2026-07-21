$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ProbeScript = Join-Path $PSScriptRoot "probe_split_models_operational_conversion_gate.py"

Push-Location $RepoRoot
try {
    python $ProbeScript
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
