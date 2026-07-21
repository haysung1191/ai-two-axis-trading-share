# KR ETF RiskBudget Live Core Authority

## Purpose

- fix the single authoritative usage rule for the live core
- prevent ambiguity between original files and live core copies

## Canonical Operating Path

- use only `D:\AI\모멘텀 투자\live_core\kr_etf_riskbudget\backtests\`
- use only `D:\AI\모멘텀 투자\live_core\kr_etf_riskbudget\docs\`

## Canonical Files

- portfolio: `backtests\kis_shadow_portfolio.csv`
- order sheet: one of
  - `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
  - `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`
- pre-trade decision: `backtests\kis_go_stop_report.csv`
- readiness: `backtests\kis_live_readiness.csv`
- health: `backtests\kis_shadow_health.csv`
- ops: `backtests\kis_shadow_ops_summary.csv`

## Canonical Document Priority

1. `docs\kr_etf_riskbudget_live_runbook_min.md`
2. `docs\kr_etf_riskbudget_final_operating_checklist.md`
3. `docs\kr_etf_riskbudget_pretrade_control_boundaries.md`
4. `docs\GO_STOP_report_spec.md`

## Runbook Rule

- canonical runbook: `docs\kr_etf_riskbudget_live_runbook_min.md`
- reference only: `docs\etf_riskbudget_micro_live_runbook.md`

## Original vs Live Core Rule

- if original and live core differ, use the live core copy for actual operation
- original files are source history, not daily operating truth
- if a required live core file is stale or missing, refresh the live core before use
