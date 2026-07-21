# KR ETF RiskBudget Live Sync Policy

## Purpose

- fix when and what must be synchronized from the main project into `live_core`
- keep the live core authoritative without destructive moves

## When Resync Is Required

- when any canonical operating output is regenerated in the main project
- when any canonical live core document changes in the main project
- when a live core file is missing, stale, or inconsistent with current operation date

## Sync Targets

- `backtests\kis_shadow_portfolio.csv`
- `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
- `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`
- `backtests\kis_live_readiness.csv`
- `backtests\kis_shadow_health.csv`
- `backtests\kis_shadow_ops_summary.csv`
- `backtests\kis_go_stop_report.csv`
- `GO_STOP_report_spec.md`
- `docs\kr_etf_riskbudget_live_runbook_min.md`
- `docs\kr_etf_riskbudget_final_operating_checklist.md`
- `docs\kr_etf_riskbudget_pretrade_control_boundaries.md`

## Non-Sync Targets

- research outputs
- US artifacts
- news artifacts
- compare / leaderboard artifacts
- execution-after-the-fact tracking files

## Sync Rule

- sync into `live_core` by copy only
- do not delete original files
- do not use unsynced originals as daily operating truth once a live core copy exists
