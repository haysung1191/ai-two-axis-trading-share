# KR ETF RiskBudget Live Core Scope

## In Scope

- Korea ETF-only operating inputs
- `Weekly ETF RiskBudget` portfolio generation
- manual order sheet generation
- readiness / health / ops / GO-STOP pre-trade control
- human runbook for manual execution

## Keep

- `backtests\kis_shadow_portfolio.csv`
- `backtests\kis_live_readiness.csv`
- `backtests\kis_shadow_health.csv`
- `backtests\kis_shadow_ops_summary.csv`
- `backtests\kis_go_stop_report.csv`
- `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
- `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`
- `docs\etf_riskbudget_micro_live_runbook.md`

## Out of Scope

- KR Weekly Score50 RegimeState
- KR Flow-based models
- KR Hybrid RS50 RB50
- KR Quality/Profitability sleeve
- KR Aggressive paper eval
- KR Strategy blend / sleeve compare
- all US strategy and research artifacts
- all news artifacts
- all leaderboard / compare / benchmark expansion work

## Scope Rule

- if an artifact does not support `Data Input`, `Portfolio Engine`, `Order Sheet`, `Pre-Trade Control`, or `Runbook`, it is outside the live core
- outside-scope artifacts must not be required to place a manual order decision

## Batch 1 Fix

- inventory document fixes what the live core must read and produce
- schema document fixes the minimum required fields for operation
- scope document fixes what remains inside and what is excluded
