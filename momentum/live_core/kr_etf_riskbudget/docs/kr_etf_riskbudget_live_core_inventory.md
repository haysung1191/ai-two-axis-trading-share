# KR ETF RiskBudget Live Core Inventory

## Purpose

- fix the minimum inputs and outputs required to operate the Korea ETF live core
- remove research and comparison artifacts from the operating path

## Top-Level Blocks

### 1. Data Input

- Korea ETF universe and price input only
- no stock, US, news, or research-side inputs

### 2. Portfolio Engine

- produce the target portfolio for `Weekly ETF RiskBudget`
- primary operating output: `backtests\kis_shadow_portfolio.csv`

### 3. Order Sheet

- produce manual order sheets from the target portfolio
- primary operating outputs:
  - `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
  - `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`

### 4. Pre-Trade Control

- check readiness, health, ops, and final GO/STOP decision before any manual order
- primary operating outputs:
  - `backtests\kis_live_readiness.csv`
  - `backtests\kis_shadow_health.csv`
  - `backtests\kis_shadow_ops_summary.csv`
  - `backtests\kis_go_stop_report.csv`

### 5. Runbook

- define the human operating sequence and file priority
- primary operating document:
  - `docs\etf_riskbudget_micro_live_runbook.md`

## Minimum Required Inputs

- operating Korea ETF universe and prices from the existing operating price flow
- no research-only prices, no stock-only data, no flow/news/fundamental side inputs

## Minimum Required Outputs

- `backtests\kis_shadow_portfolio.csv`
- `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
- `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`
- `backtests\kis_live_readiness.csv`
- `backtests\kis_shadow_health.csv`
- `backtests\kis_shadow_ops_summary.csv`
- `backtests\kis_go_stop_report.csv`
- `docs\etf_riskbudget_micro_live_runbook.md`

## Out of Operating Path

- all stock strategies
- all research leaderboards and compare reports
- all US artifacts
- all news artifacts
- all flow artifacts
