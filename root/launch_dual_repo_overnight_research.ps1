param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$Root = "C:\AI"
$DisableFlag = Join-Path $Root "overnight_runs\DISABLE_DUAL_REPO_RESEARCH_LOOP"

if (Test-Path -LiteralPath $DisableFlag) {
    Write-Output "DISABLE_DUAL_REPO_RESEARCH_LOOP is present. Exiting without generating reports."
    exit 0
}

Write-Error "Dual repo research loop launcher is frozen after cleanup. Restore the runner explicitly before restarting."
exit 2
