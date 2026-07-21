# C:\AI Current Pipeline Structure

Last verified: 2026-05-18 KST

This document is the current operator map for `C:\AI`. It describes what is
running now, how it restarts, which files are authoritative, and how the trading
pipeline is split between Bithumb crypto, KIS stock/ETF, model development, and
monitoring.

## 1. Current Objective

`C:\AI` is a two-axis tiny-live trading system:

- `BITHUMB_KRW`: Bithumb KRW crypto universe.
- `KIS_COMBINED_KRW`: KIS stock/ETF universe.

The operational target is not a single-symbol model. The target is an
account-level capital-growth pipeline with limited KRW caps, live execution
logs, and a separate model-development loop.

## 2. Current Runtime Design

The current runtime split is:

| Loop | Purpose | Cadence | Current command authority |
| --- | --- | --- | --- |
| Bithumb autotrade | Crypto signal scan, entry, and open-position management | Every 300 seconds | `run_bithumb_axis_autotrade_loop.py --submit --loop --interval-seconds 300 --entry-scan-cadence always` |
| KIS plan | Refresh stock/ETF target book and order plan after daily close | Daily 15:40 KST window | `run_kis_daily_trade_window_loop.ps1 -Mode plan -RunHour 15 -RunMinute 40 -WindowMinutes 40` |
| KIS buy | Submit prepared KIS buy plan near market open | Daily 09:05 KST window | `run_kis_daily_trade_window_loop.ps1 -Mode buy -RunHour 9 -RunMinute 5 -WindowMinutes 20` |
| KIS rebalance | Check managed stock/ETF positions and rebalance | Daily 09:05 KST window | `run_kis_daily_trade_window_loop.ps1 -Mode rebalance -RunHour 9 -RunMinute 5 -WindowMinutes 20` |
| Model factory | Build and verify candidates for both axes | Every 1800 seconds | `run_two_axis_model_factory_loop.py --loop --interval-seconds 1800 --step-timeout-seconds 900` |
| Dashboard | Korean status dashboard refresh | Every 60 seconds | `build_simple_pipeline_dashboard.py` |
| Health | Operational health and warning summary | Every 300 seconds | `build_two_axis_operational_health.py` |

Design rule:

- Bithumb monitors continuously because crypto trades continuously and volatility
  is high.
- KIS should not poll aggressively all day for new entries. It should create the
  plan after the close is settled, then execute the next morning once in the
  configured opening window.

## 3. Current Live Process Evidence

Verified running process set on 2026-05-18 KST:

- `bithumb_axis_autotrade`: PowerShell wrapper PID `10876`, Python child PID
  `18732`.
- `kis_plan`: wrapper PID `16000`, child PID `16076`.
- `kis_buy`: wrapper PID `18268`, child PID `15768`.
- `kis_rebalance`: wrapper PID `14908`, child PID `4640`.
- `two_axis_model_factory`: PID `10796`.
- `pipeline_dashboard`: PID `17396`.
- `two_axis_operational_health`: PID `22492`.

Current health file:

- `ops/health/two_axis_operational_health_latest.json`

Current health status is `HEALTH_ATTENTION` because KIS has execution warnings,
not because the loops are stopped. The current warning is
`KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE`.

## 4. Autostart And Supervisor

Windows startup entry:

- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CodexFullPipelineSafeSupervisor.cmd`

That startup file runs:

```bat
cd /d C:\AI
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\AI\start_full_pipeline_safe_supervisor.ps1" -Watchdog -RunOnceSafeEachCycle -ReopenResearchLoops -Cycles 0
```

Current supervisor:

- `start_full_pipeline_safe_supervisor.ps1`

The supervisor is idempotent: it checks whether each loop is already running and
only starts a missing loop.

Do not treat `run_full_pipeline_safe_supervisor.py` as the current runtime
authority. It is older than the active PowerShell supervisor and can contain
stale safety assumptions.

## 5. Authoritative Policy And Contract Files

Primary current files:

- `AGENTS.md`: operator contract for this workspace.
- `START_HERE_AFTER_REBOOT.md`: read-only reentry and reboot recovery checklist.
- `contracts/human_mandate.yaml`: approved human mandate and stop rule.
- `ops/runstate/limited_live_policy.json`: current limited-live policy.
- `ops/runstate/broker_paper_policy.json`: current broker submit policy.

Current policy state:

- `live_enabled`: true.
- `broker_submit_allowed`: true.
- `paper_enabled`: false.
- `private_submit_used`: false.
- `DISABLE_ALL_TRADING`: absent.
- `overnight_runs/DISABLE_DUAL_REPO_RESEARCH_LOOP`: present, blocking only the
  old broad dual-repo research loop.

Hard rule:

- Do not stop, kill, pause, replace, or disable live submit/execute loops unless
  the operator explicitly requests that stop action.
- Do not create `ops/runstate/DISABLE_ALL_TRADING` unless the operator explicitly
  asks to stop trading or activate the kill guard.

## 6. Current Stage Model

Older files may still mention Stage 6 shadow and Stage 7 paper. They are no
longer operational gates.

Current practical path:

```text
Stage 1 -> Stage 3 -> Stage 4 -> Stage 5 -> Stage 8/9 tiny live
```

Meaning:

- Stage 1: candidate/model discovery.
- Stage 3: candidate filtering and evidence consolidation.
- Stage 4: robustness and risk conversion.
- Stage 5: OOS or walkforward verification.
- Stage 8/9: tiny-live operation under KRW caps and live execution logs.

Shadow/paper files can still exist as historical artifacts. Do not let stale
shadow/paper blockers override current live policy files and current process
evidence.

## 7. Bithumb Axis

Primary runtime script:

- `run_bithumb_axis_autotrade_loop.py`

Current runtime mode:

```powershell
python C:\AI\run_bithumb_axis_autotrade_loop.py --submit --loop --interval-seconds 300 --entry-scan-cadence always --format json
```

Primary status files:

- `ops/bithumb_axis_autotrade/bithumb_axis_autotrade_latest.json`
- `ops/bithumb_axis_autotrade/bithumb_axis_autotrade_latest.md`
- `Crypto/logs/bithumb_axis_portfolio_events/`
- `Crypto/logs/bithumb_live_orca_portfolio_state.json`

Latest verified status:

- `status`: `BITHUMB_AXIS_AUTOTRADE_NO_NEW_SIGNAL`
- `submit_enabled`: true
- `entry_scan.cadence`: `always`
- `global_disable_present`: false
- scanned markets: 457
- OOS markets: `KRW-BTC`, `KRW-ETH`, `KRW-ONDO`, `KRW-ORCA`, `KRW-POLA`,
  `KRW-SOL`
- current open positions: 0
- current estimated exposure: 0 KRW
- remaining cap estimate: 100000 KRW

## 8. KIS Axis

Primary wrapper:

- `run_kis_daily_trade_window_loop.ps1`

Modes:

- `plan`: runs after close and refreshes the stock/ETF candidate bridge and
  order plan.
- `buy`: runs in the morning window and submits the prepared plan.
- `rebalance`: runs in the morning window and checks managed positions.

Primary implementation scripts:

- `build_stock_etf_operating_candidate_bridge.py`
- `run_stock_etf_axis_operation_loop.py`
- `submit_kis_stock_etf_order_intents.py`
- `run_kis_position_rebalance_loop.py`

Primary status files:

- `ops/stock_etf_axis_operation/stock_etf_axis_operation_latest.json`
- `ops/stock_etf_axis_operation/kis_stock_etf_order_submit_latest.json`
- `ops/stock_etf_axis_operation/kis_stock_etf_order_ledger.jsonl`
- `ops/stock_etf_axis_operation/kis_daily_plan_window_state.json`
- `ops/kis_position_rebalance/kis_position_rebalance_latest.json`

Current KIS execution evidence:

- A real submitted KIS order exists in
  `ops/stock_etf_axis_operation/kis_stock_etf_order_ledger.jsonl`.
- Submitted at `2026-05-18T00:04:14.978315+00:00`.
- Symbol `049630`, side `BUY`, quantity `1`, estimated notional `11880 KRW`.
- KIS response `rt_cd=0`, order number `0005953800`.

Current KIS warning:

- `KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE`.

This warning means the KIS tiny-live book has low buyable coverage. It is not a
reason to stop the active KIS wrappers.

## 9. Model Factory

Primary runtime script:

- `run_two_axis_model_factory_loop.py`

Primary status files:

- `ops/model_factory_loop/two_axis_model_factory_loop_latest.json`
- `ops/model_factory_loop/two_axis_model_factory_loop_running.json`
- `ops/model_factory_loop/two_axis_model_factory_loop_history.jsonl`

Primary model evidence outputs:

- `reports/model_factory/two_axis_direct_model_development_latest.json`
- `reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json`
- `reports/model_factory/bithumb_current_actionable_robustness_stress_latest.json`
- `reports/operations/two_axis_model_inventory_latest.json`

Latest verified model-factory status:

- `status`: `TWO_AXIS_MODEL_FACTORY_OK`
- completed steps: 8 of 8
- error count: 0
- crypto candidates: 192
- crypto OOS pass: 165
- crypto validated pass: 67
- KIS variants: 25
- KIS pass: 16

## 10. Dashboard And Health

Dashboard:

- Builder: `build_simple_pipeline_dashboard.py`
- Output: `ops/dashboard/pipeline_dashboard_simple.html`
- JSON: `ops/dashboard/pipeline_dashboard_simple_latest.json`
- Refresh cadence: 60 seconds.

Health:

- Builder: `build_two_axis_operational_health.py`
- JSON: `ops/health/two_axis_operational_health_latest.json`
- Markdown: `ops/health/two_axis_operational_health_latest.md`
- Refresh cadence: 300 seconds.

The health builder has process-scan fallback logic. If a PID file is stale, it
can still detect a running loop by process command line.

## 11. Top-Level Folder Roles

Important folders:

- `Crypto/`: Bithumb crypto research, logs, live portfolio state, crypto-side
  artifacts.
- `momentum/`: stock/ETF model and split-model pipeline.
- `ops/`: current runtime status, PID files, live execution logs, dashboards,
  health files, runstate.
- `contracts/`: human mandate and current operating contract artifacts.
- `reports/model_factory/`: current model-development evidence.
- `reports/operations/`: model inventory and operational summaries.
- `candidate_registry/` and `registry/`: candidate and evidence registry files.
- `data/`, `data_readiness/`, `data_snapshots/`: market data inputs and
  readiness artifacts.
- `overnight_runs/`: older overnight run artifacts and old broad-loop disable
  guard.
- `tests/`: regression tests for live-loop and operation scripts.

Cleanup rule:

- Preserve latest pointers, candidate evidence, runstate files, PID files, live
  execution logs, dashboards, health outputs, and current model evidence.
- Cleanup candidates are timestamped duplicate reports, generated old run
  folders, caches, and stale logs only after verifying they are not referenced by
  the current loops.

## 12. Reboot Recovery

After reboot:

1. Read `AGENTS.md` and `START_HERE_AFTER_REBOOT.md`.
2. Check live processes read-only.
3. Confirm `ops/runstate/DISABLE_ALL_TRADING` is absent.
4. Confirm `start_full_pipeline_safe_supervisor.ps1` has started missing loops.
5. Check `ops/health/two_axis_operational_health_latest.json`.
6. Check Bithumb latest status, KIS order ledger/latest status, and model-factory
   latest status.
7. Do not stop a live loop during state reconstruction.

Useful read-only process check:

```powershell
cd C:\AI
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -match 'C:\\AI' -and
  $_.CommandLine -match 'run_bithumb_axis_autotrade_loop.py|run_kis_daily_trade_window_loop.ps1|run_stock_etf_axis_operation_loop.py|run_kis_position_rebalance_loop.py|run_two_axis_model_factory_loop.py|build_simple_pipeline_dashboard.py|build_two_axis_operational_health.py'
} | Select-Object ProcessId,Name,CommandLine
```

## 13. Known Risks And Stale Areas

- Old shadow/paper/stage reports can conflict with current live state. Current
  authority is policy files plus running processes plus latest execution logs.
- `run_full_pipeline_safe_supervisor.py` is stale relative to
  `start_full_pipeline_safe_supervisor.ps1`.
- Some scheduled tasks from older workflows still exist. Current startup route is
  the Startup cmd file and PowerShell supervisor.
- KIS has `KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE`; keep it visible, but do not stop
  loops because of it.
- `overnight_runs/DISABLE_DUAL_REPO_RESEARCH_LOOP` is present and should remain
  unless the operator explicitly asks to restart the old broad dual-repo research
  loop.

