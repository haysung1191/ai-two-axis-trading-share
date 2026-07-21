# KR ETF RiskBudget Daily Operator Entrypoint

## Purpose

- define the single daily operating surface for the live core
- let the operator make a manual order decision using only `live_core`

## Canonical Daily Files To Open

1. `backtests\kis_live_readiness.csv`
2. `backtests\kis_shadow_health.csv`
3. `backtests\kis_go_stop_report.csv`
4. `backtests\kis_shadow_portfolio.csv`
5. one order sheet file
6. `docs\kr_etf_riskbudget_live_runbook_min.md`

## Check Order

### 1. Readiness

- open `backtests\kis_live_readiness.csv`
- confirm `Weekly ETF RiskBudget` is still the live core operating strategy

### 2. Health

- open `backtests\kis_shadow_health.csv`
- use this file as the daily indicator for upstream ETF universe / price freshness
- do not inspect raw external price files unless freshness looks wrong here

### 3. Final Pre-Trade Decision

- open `backtests\kis_go_stop_report.csv`
- this is the final pre-trade decision artifact

### 4. Portfolio

- open `backtests\kis_shadow_portfolio.csv`
- use it as the target portfolio reference only after checking GO/STOP

### 5. Order Sheet

- if starting from cash, open:
  - `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
- if already funded, open:
  - `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`
- open the order sheet only after checking readiness, health, and GO/STOP

### 6. Runbook

- open `docs\kr_etf_riskbudget_live_runbook_min.md`
- use this as the canonical runbook

## STOP Rule

- if `kis_go_stop_report.csv` says `STOP`, do not place manual orders
- do not override GO/STOP using portfolio or order sheet alone
- do not fall back to original project files for daily operating truth

## GO Rule

- if `kis_go_stop_report.csv` says `GO`, the operator may use the portfolio and order sheet to decide whether to manually enter orders
- actual order entry is always performed by the user

## Today Operator Action Summary

1. open readiness
2. open health
3. open GO/STOP
4. if `GO`, open portfolio and the correct order sheet
5. manually decide whether to enter the order sheet
