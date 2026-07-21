param(
    [switch]$Strict
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath "C:\AI"
$env:PYTHONDONTWRITEBYTECODE = "1"

$steps = @(
    "build_stage13_completion_audit.py",
    "build_pipeline_direct_blocker_packet.py",
    "build_pipeline_direct_next_command.py",
    "build_start_here_after_reboot_validator.py",
    "build_pipeline_blocked_stop_state.py",
    "build_pipeline_blocked_runtime_safety_snapshot.py"
)

$results = @()
foreach ($step in $steps) {
    $started = Get-Date
    & python ".\$step"
    $exitCode = $LASTEXITCODE
    $results += [pscustomobject]@{
        script = $step
        exit_code = $exitCode
        started_at = $started.ToString("o")
        finished_at = (Get-Date).ToString("o")
    }
    if ($Strict -and $exitCode -ne 0) {
        throw "Step failed: $step"
    }
}

$next = Get-Content -Raw -LiteralPath "C:\AI\reports\operations\pipeline_direct_next_command_latest.json" | ConvertFrom-Json
$stage13 = Get-Content -Raw -LiteralPath "C:\AI\reports\operations\stage13_completion_audit_latest.json" | ConvertFrom-Json
$validator = Get-Content -Raw -LiteralPath "C:\AI\reports\operations\start_here_after_reboot_validator_latest.json" | ConvertFrom-Json

$summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString("o")
    report = "pipeline_direct_recheck"
    status = if ($validator.status -eq "PASS") { "PASS" } else { "FAIL" }
    completion_decision = $stage13.completion_decision
    stage13_complete = $stage13.stage13_complete
    next_command_status = $next.status
    next_command_kind = $next.command_kind
    next_command_blockers = $next.blockers
    safety = $next.safety
    steps = $results
    non_goals = @(
        "does_not_enable_paper",
        "does_not_enable_live",
        "does_not_allow_broker_submit",
        "does_not_create_order_intent",
        "does_not_submit_orders"
    )
}

$out = "C:\AI\reports\operations\pipeline_direct_recheck_latest.json"
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding UTF8
$summary | ConvertTo-Json -Depth 8
