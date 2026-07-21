$ErrorActionPreference = "Stop"

$CurrentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object Security.Principal.WindowsPrincipal($CurrentIdentity)
$IsAdmin = $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$HardenScript = Join-Path $PSScriptRoot "harden_split_models_initial_entry_autotrade_task.ps1"
$StatusScript = Join-Path $PSScriptRoot "show_split_models_initial_entry_autotrade_task_status.ps1"
$ReadinessScript = Join-Path $PSScriptRoot "verify_split_models_initial_entry_operational_readiness.ps1"
$HandoffScript = Join-Path $PSScriptRoot "build_split_models_initial_entry_operational_handoff.ps1"
$Timestamp = Get-Date -Format "yyyyMMddTHHmmss"
$TaskStatusJson = Join-Path $RepoRoot "output\split_models_shadow\autotrade_task_status_latest.json"
$TaskStatusText = Join-Path $RepoRoot "output\split_models_shadow\autotrade_task_status_latest.txt"
$TaskStatusHistoryJson = Join-Path $RepoRoot ("output\split_models_shadow\autotrade_task_status_{0}.json" -f $Timestamp)
$TaskStatusHistoryText = Join-Path $RepoRoot ("output\split_models_shadow\autotrade_task_status_{0}.txt" -f $Timestamp)
$OperationalReadinessJson = Join-Path $RepoRoot "output\split_models_shadow\operational_readiness_latest.json"
$OperationalReadinessText = Join-Path $RepoRoot "output\split_models_shadow\operational_readiness_latest.txt"
$OperationalReadinessHistoryJson = Join-Path $RepoRoot ("output\split_models_shadow\operational_readiness_{0}.json" -f $Timestamp)
$OperationalReadinessHistoryText = Join-Path $RepoRoot ("output\split_models_shadow\operational_readiness_{0}.txt" -f $Timestamp)
$OperationalHandoffJson = Join-Path $RepoRoot "output\split_models_shadow\operational_handoff_latest.json"
$OperationalHandoffText = Join-Path $RepoRoot "output\split_models_shadow\operational_handoff_latest.txt"
$OperationalHandoffHistoryJson = Join-Path $RepoRoot ("output\split_models_shadow\operational_handoff_{0}.json" -f $Timestamp)
$OperationalHandoffHistoryText = Join-Path $RepoRoot ("output\split_models_shadow\operational_handoff_{0}.txt" -f $Timestamp)

if (-not $IsAdmin) {
    $argList = @(
        "-NoProfile"
        "-ExecutionPolicy", "Bypass"
        "-File", ('"{0}"' -f $PSCommandPath)
    ) -join " "
    Start-Process powershell -Verb RunAs -ArgumentList $argList
    exit 0
}

Push-Location $RepoRoot
try {
    & $HardenScript
    & $StatusScript `
        -output-json-path $TaskStatusJson `
        -output-text-path $TaskStatusText
    & $StatusScript `
        -output-json-path $TaskStatusHistoryJson `
        -output-text-path $TaskStatusHistoryText
    & $ReadinessScript `
        -output-json-path $OperationalReadinessJson `
        -output-text-path $OperationalReadinessText
    & $ReadinessScript `
        -output-json-path $OperationalReadinessHistoryJson `
        -output-text-path $OperationalReadinessHistoryText
    & $HandoffScript `
        -output-json-path $OperationalHandoffJson `
        -output-text-path $OperationalHandoffText
    & $HandoffScript `
        -output-json-path $OperationalHandoffHistoryJson `
        -output-text-path $OperationalHandoffHistoryText
}
finally {
    Pop-Location
}
