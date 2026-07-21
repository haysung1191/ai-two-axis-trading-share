param(
  [switch]$Watchdog,
  [switch]$RunOnceSafeEachCycle,
  [switch]$ReopenResearchLoops,
  [int]$Cycles = 0,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = "C:\AI"

function Test-LoopRunning {
  param([string]$Pattern)
  $existing = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and
    $_.CommandLine.Contains($Pattern) -and
    -not $_.CommandLine.Contains("Get-CimInstance") -and
    -not $_.CommandLine.Contains("Select-Object")
  } | Select-Object -First 1
  return $null -ne $existing
}

function Start-LoopIfMissing {
  param(
    [string]$Name,
    [string]$Pattern,
    [string]$Command,
    [string]$PidPath
  )

  if (Test-LoopRunning -Pattern $Pattern) {
    Write-Output "$Name already_running"
    return
  }

  if ($DryRun) {
    Write-Output "$Name would_start"
    return
  }

  $proc = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $Command
  )
  $pidDir = Split-Path -Parent $PidPath
  if (!(Test-Path $pidDir)) {
    New-Item -ItemType Directory -Path $pidDir | Out-Null
  }
  Set-Content -Path $PidPath -Value ([string]$proc.Id) -Encoding ASCII
  Write-Output "$Name started pid=$($proc.Id)"
}

Set-Location $Root

Start-LoopIfMissing `
  -Name "bithumb_axis_autotrade" `
  -Pattern "run_bithumb_axis_autotrade_loop.py" `
  -PidPath "$Root\ops\bithumb_axis_autotrade\bithumb_axis_autotrade_loop.pid" `
  -Command "python C:\AI\run_bithumb_axis_autotrade_loop.py --submit --loop --interval-seconds 300 --entry-scan-cadence always --format json *> C:\AI\Crypto\logs\bithumb_axis_autotrade_loop_stdout.log"

Start-LoopIfMissing `
  -Name "stock_etf_axis_plan" `
  -Pattern "run_kis_daily_trade_window_loop.ps1 -Mode plan" `
  -PidPath "$Root\ops\stock_etf_axis_operation\stock_etf_axis_plan_loop.pid" `
  -Command "powershell -NoProfile -ExecutionPolicy Bypass -File C:\AI\run_kis_daily_trade_window_loop.ps1 -Mode plan -RunHour 15 -RunMinute 40 -WindowMinutes 40"

Start-LoopIfMissing `
  -Name "stock_etf_axis_operation" `
  -Pattern "run_kis_daily_trade_window_loop.ps1 -Mode buy" `
  -PidPath "$Root\ops\stock_etf_axis_operation\stock_etf_axis_operation_loop.pid" `
  -Command "powershell -NoProfile -ExecutionPolicy Bypass -File C:\AI\run_kis_daily_trade_window_loop.ps1 -Mode buy -RunHour 9 -RunMinute 5 -WindowMinutes 20"

Start-LoopIfMissing `
  -Name "kis_position_rebalance" `
  -Pattern "run_kis_daily_trade_window_loop.ps1 -Mode rebalance" `
  -PidPath "$Root\ops\kis_position_rebalance\kis_position_rebalance_loop.pid" `
  -Command "powershell -NoProfile -ExecutionPolicy Bypass -File C:\AI\run_kis_daily_trade_window_loop.ps1 -Mode rebalance -RunHour 9 -RunMinute 5 -WindowMinutes 20"

Start-LoopIfMissing `
  -Name "two_axis_model_factory" `
  -Pattern "run_two_axis_model_factory_loop.py" `
  -PidPath "$Root\ops\model_factory_loop\two_axis_model_factory_loop.pid" `
  -Command "python C:\AI\run_two_axis_model_factory_loop.py --loop --interval-seconds 1800 --step-timeout-seconds 900 --format json *> C:\AI\ops\model_factory_loop\two_axis_model_factory_loop_stdout.log"

Start-LoopIfMissing `
  -Name "pipeline_dashboard" `
  -Pattern "build_simple_pipeline_dashboard.py" `
  -PidPath "$Root\ops\dashboard\pipeline_dashboard_loop.pid" `
  -Command "while (`$true) { python C:\AI\build_simple_pipeline_dashboard.py *> C:\AI\ops\dashboard\pipeline_dashboard_stdout.log; Start-Sleep -Seconds 60 }"

Start-LoopIfMissing `
  -Name "two_axis_operational_health" `
  -Pattern "build_two_axis_operational_health.py" `
  -PidPath "$Root\ops\health\two_axis_operational_health_loop.pid" `
  -Command "while (`$true) { python C:\AI\build_two_axis_operational_health.py *> C:\AI\ops\health\two_axis_operational_health_stdout.log; Start-Sleep -Seconds 300 }"
