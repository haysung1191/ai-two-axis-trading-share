# Start Here After Reboot

## Current Objective

Keep the existing two-axis tiny-live automation running and let the model-development loop improve candidates in parallel.

- `BITHUMB_KRW`: Bithumb crypto live/autotrade loop.
- `KIS_COMBINED_KRW`: stock/ETF live operation and KIS rebalance loops.
- `run_two_axis_model_factory_loop.py`: AI/model development loop.

## First Action

Do a read-only state check. Do not stop live loops.

```powershell
cd C:\AI
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -match 'C:\\AI' -and
  $_.CommandLine -match 'run_bithumb_axis_autotrade_loop.py|run_stock_etf_axis_operation_loop.py|run_kis_position_rebalance_loop.py|run_two_axis_model_factory_loop.py|build_simple_pipeline_dashboard.py|build_two_axis_operational_health.py'
} | Select-Object ProcessId,Name,CommandLine
```

Expected live/ops loops:

- `run_bithumb_axis_autotrade_loop.py --submit --loop --entry-scan-cadence always`
- `run_kis_daily_trade_window_loop.ps1 -Mode plan`
- `run_kis_daily_trade_window_loop.ps1 -Mode buy`
- `run_kis_daily_trade_window_loop.ps1 -Mode rebalance`
- `run_two_axis_model_factory_loop.py --loop`
- dashboard and operational-health refresh loops

## Read These Files First

After confirming the process list, read only the current `latest` state files first:

1. `ops/dashboard/pipeline_dashboard_simple_latest.json`
2. `ops/health/two_axis_operational_health_latest.md`
3. `ops/bithumb_axis_autotrade/bithumb_axis_autotrade_latest.json`
4. `ops/stock_etf_axis_operation/stock_etf_axis_operation_latest.json`
5. `ops/stock_etf_operating_candidate_bridge/stock_etf_operating_candidate_bridge_latest.json`
6. `ops/model_factory_loop/two_axis_model_factory_loop_latest.json`
7. `reports/model_factory/two_axis_direct_model_development_latest.json`
8. `reports/operations/two_axis_model_inventory_latest.json`

Do not start by reading old `reports/operations/kis_pit_*`, `kis_axis_wide_*`, `CAND-*`, shadow, paper, blocked-state, or disabled-state reports. Those are historical evidence only unless the user explicitly asks about them.

Cadence:

- Bithumb: 5-minute signal and position monitoring.
- KIS plan: daily 15:40 KST after close, then wait.
- KIS buy/rebalance: daily 09:05 KST execution window, then wait.

## Safety Guard Check

`ops/runstate/DISABLE_ALL_TRADING` must be absent during normal tiny-live automation.

Do not create that file unless the user explicitly asks to stop trading, disable live loops, or activate the kill guard.

## Current Policy Sources

Use these files as the current live policy sources:

- `ops/runstate/limited_live_policy.json`
- `ops/runstate/broker_paper_policy.json`
- `contracts/human_mandate.yaml`

Older stage reports may still mention shadow/paper blockers. Treat those as stale if they conflict with the live policy files and current process list.

PIT/survivorship-free KIS documents may still exist on disk as historical artifacts. Current KIS operation uses `daily_close_presence` universe validation; do not restore PIT/survivorship blockers unless the current `latest` runtime artifacts say they are active again.

## Current Model Evidence

Main model-development outputs:

- `reports/model_factory/two_axis_direct_model_development_latest.json`
- `reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json`
- `reports/model_factory/bithumb_current_actionable_robustness_stress_latest.json`
- `reports/operations/two_axis_model_inventory_latest.json`

## Work Rules

- Keep live loops running unless the user explicitly asks to stop them.
- Do not restart broad research as a substitute for checking current live operation.
- Do not add new report or contract layers just to describe state.
- If something looks unsafe, report the exact file/process evidence first before taking action.
