$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$LaunchScript = Join-Path $PSScriptRoot "launch_split_models_operational_conversion_dashboard.py"

Push-Location $RepoRoot
try {
    python $LaunchScript
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
