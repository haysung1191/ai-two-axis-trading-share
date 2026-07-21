# KR ETF RiskBudget Live Relayout Plan

## Purpose

- fix where live core artifacts belong during partial rebuild
- separate live operating artifacts from research artifacts

## Live Core Placement Rule

- only artifacts required by `Data Input`, `Portfolio Engine`, `Order Sheet`, `Pre-Trade Control`, and `Runbook` remain in the live core
- all other artifacts are outside the live operating path

## Live Core Artifact Groups

### 1. Data Input

- operating Korea ETF universe and operating price inputs

### 2. Portfolio Engine

- `backtests\kis_shadow_portfolio.csv`

### 3. Order Sheet

- `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
- `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`

### 4. Pre-Trade Control

- `backtests\kis_live_readiness.csv`
- `backtests\kis_shadow_health.csv`
- `backtests\kis_shadow_ops_summary.csv`
- `backtests\kis_go_stop_report.csv`

### 5. Runbook

- `docs\kr_etf_riskbudget_live_runbook_min.md`
- `docs\kr_etf_riskbudget_live_batch_sequence.md`
- `docs\kr_etf_riskbudget_pretrade_control_boundaries.md`

## Relayout Rule

- live core documents stay under `docs\`
- live core operating outputs stay under `backtests\`
- research and comparison outputs must not be required by the live runbook or GO/STOP flow
