# KR ETF RiskBudget Final Operating Checklist

## Purpose

- fix the final daily checks required before a manual order decision
- keep the operator focused on the live core only

## Daily Checklist

1. Confirm `backtests\kis_live_readiness.csv` still points to `Weekly ETF RiskBudget`
2. Confirm `backtests\kis_shadow_health.csv` is fresh enough for live use
3. Confirm `backtests\kis_shadow_ops_summary.csv` is not blocking operation
4. Confirm `backtests\kis_shadow_portfolio.csv` exists for the current run
5. Confirm the correct order sheet exists for the current operating case
6. Confirm `backtests\kis_go_stop_report.csv` exists and is the final pre-trade result
7. If `Decision != GO`, do not place manual orders
8. If `Decision = GO`, user decides whether to manually enter the order sheet

## Checklist Rule

- the final pre-trade control result is the direct input to the user’s order decision
- this checklist ends before any order execution, fill tracking, or post-trade work
