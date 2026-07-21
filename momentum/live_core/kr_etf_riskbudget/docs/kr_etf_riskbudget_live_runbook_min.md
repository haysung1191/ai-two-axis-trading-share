# KR ETF RiskBudget Live Runbook Minimum

## Purpose

- define the minimum live operating sequence for the Korea ETF core
- remove research and non-operating content

## Scope

- strategy: `Weekly ETF RiskBudget`
- market: Korea ETF only
- order style: manual only

## Files To Check

1. `backtests\kis_live_readiness.csv`
2. `backtests\kis_shadow_health.csv`
3. `backtests\kis_shadow_ops_summary.csv`
4. `backtests\kis_shadow_portfolio.csv`
5. one order sheet file
6. `backtests\kis_go_stop_report.csv`

## Which Order Sheet To Use

- initial funding from cash:
  - `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
- ongoing funded account rebalance:
  - `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`

## Operating Rule

- use the portfolio as target composition
- use the order sheet as the manual order instruction
- use GO/STOP as the final execution decision
- if GO/STOP is not `GO`, do not place manual orders

## Excluded

- all stock strategies
- all research comparisons
- all US artifacts
- all news artifacts
- all execution-after-the-fact tracking
