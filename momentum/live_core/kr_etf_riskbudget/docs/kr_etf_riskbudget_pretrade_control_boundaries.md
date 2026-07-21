# KR ETF RiskBudget Pre-Trade Control Boundaries

## Purpose

- fix the responsibility split inside `Pre-Trade Control`
- keep the final manual order decision mechanical

## 1. Readiness

Input:

- `backtests\kis_live_readiness.csv`

Output:

- readiness status for `Weekly ETF RiskBudget`

Role:

- confirms the operating strategy is still the live core candidate
- does not inspect portfolio or order sheet details

## 2. Health

Input:

- `backtests\kis_shadow_health.csv`

Output:

- source freshness and readiness freshness status

Role:

- confirms the operating data and readiness state are fresh enough to proceed
- does not decide whether to execute

## 3. Ops

Input:

- `backtests\kis_shadow_ops_summary.csv`

Output:

- daily operating status for the live core

Role:

- gives the daily operating gate before final decision
- does not replace GO/STOP

## 4. GO/STOP

Inputs:

- `backtests\kis_shadow_health.csv`
- `backtests\kis_shadow_ops_summary.csv`
- `backtests\kis_shadow_portfolio.csv`
- one order sheet file
- `docs\kr_etf_riskbudget_live_runbook_min.md`

Output:

- `backtests\kis_go_stop_report.csv`

Role:

- final pre-trade decision layer
- checks input consistency and returns `GO`, `STOP`, or `판단 불가`
- does not generate orders and does not place orders

## Control Rule

- readiness, health, and ops are upstream control artifacts
- GO/STOP is the only final pre-trade decision artifact
- actual order entry is performed by the user
