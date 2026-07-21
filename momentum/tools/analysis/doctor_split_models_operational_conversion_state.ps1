$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DoctorScript = Join-Path $PSScriptRoot "doctor_split_models_operational_conversion_state.py"

Push-Location $RepoRoot
try {
    python $DoctorScript
}
finally {
    Pop-Location
}
