param(
  [ValidateSet("plan", "buy", "rebalance")]
  [string]$Mode = "buy",
  [int]$RunHour = 9,
  [int]$RunMinute = 5,
  [int]$WindowMinutes = 20,
  [int]$SleepSeconds = 60
)

$ErrorActionPreference = "Stop"
$Root = "C:\AI"

if ($Mode -eq "plan") {
  $StatePath = Join-Path $Root "ops\stock_etf_axis_operation\kis_daily_plan_window_state.json"
  $StdoutPath = Join-Path $Root "ops\stock_etf_axis_operation\stock_etf_axis_operation_stdout.log"
  $Command = "python C:\AI\run_stock_etf_axis_operation_loop.py --skip-model-refresh --format json"
} elseif ($Mode -eq "buy") {
  $StatePath = Join-Path $Root "ops\stock_etf_axis_operation\kis_daily_buy_window_state.json"
  $StdoutPath = Join-Path $Root "ops\stock_etf_axis_operation\stock_etf_axis_operation_stdout.log"
  $Command = "python C:\AI\run_stock_etf_axis_operation_loop.py --submit --skip-model-refresh --skip-operation-refresh --format json"
} else {
  $StatePath = Join-Path $Root "ops\kis_position_rebalance\kis_daily_rebalance_window_state.json"
  $StdoutPath = Join-Path $Root "ops\kis_position_rebalance\kis_position_rebalance_stdout.log"
  $Command = "python C:\AI\run_kis_position_rebalance_loop.py --execute --format json"
}

function Get-State {
  if (!(Test-Path $StatePath)) {
    return @{}
  }
  try {
    return Get-Content -Raw $StatePath | ConvertFrom-Json -AsHashtable
  } catch {
    return @{}
  }
}

function Write-State {
  param([hashtable]$State)
  $dir = Split-Path -Parent $StatePath
  if (!(Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir | Out-Null
  }
  $State | ConvertTo-Json -Depth 5 | Set-Content -Path $StatePath -Encoding UTF8
}

Set-Location $Root

while ($true) {
  $now = Get-Date
  $today = $now.ToString("yyyy-MM-dd")
  $windowStart = Get-Date -Year $now.Year -Month $now.Month -Day $now.Day -Hour $RunHour -Minute $RunMinute -Second 0
  $windowEnd = $windowStart.AddMinutes($WindowMinutes)
  $state = Get-State
  $lastRunDate = [string]($state["last_run_date"])

  if ($now -ge $windowStart -and $now -lt $windowEnd -and $lastRunDate -ne $today) {
    $started = (Get-Date).ToUniversalTime().ToString("o")
    $output = Invoke-Expression $Command 2>&1
    $output | Out-File -FilePath $StdoutPath -Append -Encoding utf8
    Write-State @{
      mode = $Mode
      last_run_date = $today
      last_started_at_utc = $started
      last_finished_at_utc = (Get-Date).ToUniversalTime().ToString("o")
      command = $Command
    }
    Start-Sleep -Seconds ([Math]::Max($SleepSeconds, 300))
    continue
  }

  Start-Sleep -Seconds $SleepSeconds
}
