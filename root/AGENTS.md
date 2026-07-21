# C:\AI Operating Contract

Speak Korean to the user.

## Current Operating State

This workspace is already running tiny-live automation for both axes:

- `BITHUMB_KRW`: Bithumb crypto tiny-live/autotrade loop.
- `KIS_COMBINED_KRW`: stock/ETF tiny-live operation and KIS rebalance loops.
- Model development runs separately through `run_two_axis_model_factory_loop.py`.

Do not treat live trading as disabled just because older handoff or stage files say so. The current authority for live permission is:

- `ops/runstate/limited_live_policy.json`
- `ops/runstate/broker_paper_policy.json`
- live process list
- latest broker/execution logs

## Reentry Source Priority

When a new AI/Codex session starts, read current runtime sources in this order:

1. `AGENTS.md`
2. `START_HERE_AFTER_REBOOT.md`
3. current process list for `C:\AI`
4. `ops/dashboard/pipeline_dashboard_simple_latest.json`
5. `ops/health/two_axis_operational_health_latest.md`
6. `ops/runstate/limited_live_policy.json`
7. `ops/runstate/broker_paper_policy.json`
8. `ops/bithumb_axis_autotrade/bithumb_axis_autotrade_latest.json`
9. `ops/stock_etf_axis_operation/stock_etf_axis_operation_latest.json`
10. `ops/stock_etf_operating_candidate_bridge/stock_etf_operating_candidate_bridge_latest.json`
11. `ops/model_factory_loop/two_axis_model_factory_loop_latest.json`
12. `reports/model_factory/two_axis_direct_model_development_latest.json`
13. `reports/operations/two_axis_model_inventory_latest.json`

Do not reconstruct current state from older timestamped reports before reading the current `latest` runtime sources above.

## Stale Document Rule

The following families are historical evidence only unless the user explicitly asks about them:

- `reports/operations/kis_pit_*`
- `reports/operations/kis_axis_wide_*`
- `reports/live_readiness/CAND-*`
- old shadow/paper stage reports
- old blocked-state or disabled-state reports

Do not treat these files as current blockers if they conflict with current live policy, current process list, current dashboard, current health, or current `latest` KIS/Bithumb artifacts.

## Hard Rule: Do Not Stop Live Loops

Do not stop, kill, pause, replace, or disable any live submit or execute loop unless the user explicitly asks for that exact stop action.

Protected live loops include:

- `run_bithumb_axis_autotrade_loop.py --submit`
- `run_kis_daily_trade_window_loop.ps1 -Mode buy`
- `run_kis_daily_trade_window_loop.ps1 -Mode rebalance`
- any PowerShell wrapper that restarts the above loops

Do not create `ops/runstate/DISABLE_ALL_TRADING` unless the user explicitly asks to stop trading or activate the kill guard.

## Loop Cadence

Bithumb should keep 5-minute monitoring active for both signal detection and position management because crypto volatility is continuous.

KIS stock/ETF should use a two-step daily flow:

- After close: `run_kis_daily_trade_window_loop.ps1 -Mode plan` refreshes the candidate bridge and order plan.
- Next morning: `run_kis_daily_trade_window_loop.ps1 -Mode buy` submits the prepared plan in the 09:05 KST window.
- Next morning: `run_kis_daily_trade_window_loop.ps1 -Mode rebalance` checks managed positions in the same window.

Outside those windows the KIS wrappers only wait.

## Current Pipeline Shape

Shadow and paper stages are no longer operational gates. Backtest, OOS walkforward, robustness, live policy caps, and tiny-live execution logs are the relevant evidence.

Current pipeline:

Stage 1 -> Stage 3 -> Stage 4 -> Stage 5 -> Stage 8/9 tiny live

## Work Split

Autotrade loops own live monitoring and execution. Codex/AI model work should focus on:

- improving Bithumb and KIS model candidates,
- refreshing OOS and robustness evidence,
- checking dashboards, health, and execution logs,
- fixing code that directly advances the trading pipeline.

Do not add new safety/report/contract layers just to explain state.

## Cleanup Rule

Keep files that affect live operation, latest pointers, candidate evidence, policy state, runstate, logs, and dashboards.

Cleanup candidates are only stale generated duplicates, historical run folders, caches, and obsolete reports that do not affect current live loops or latest candidate evidence.

Before deleting anything, verify it is not referenced by:

- current live loop scripts,
- `latest` pointers,
- `ops/runstate`,
- `reports/model_factory`,
- `reports/operations`,
- `Crypto/logs`,
- `momentum` outputs.

## Human Mandate Caps

- crypto max_order_krw: 100000
- crypto max_daily_loss_krw: 20000
- crypto max_total_loss_krw: 100000
- stock max_order_krw: 100000
- stock max_daily_loss_krw: 100000
- stock max_total_loss_krw: 100000
- mandate_status: COMPLETE

## First Check On Reentry

Read-only check first:

1. Confirm live submit/execute loops are still running.
2. Confirm `ops/runstate/DISABLE_ALL_TRADING` is absent unless the user requested a stop.
3. Confirm `run_two_axis_model_factory_loop.py` is running for model development.
4. Check latest execution logs and model-factory outputs.

Never turn off a live loop during state reconstruction.
