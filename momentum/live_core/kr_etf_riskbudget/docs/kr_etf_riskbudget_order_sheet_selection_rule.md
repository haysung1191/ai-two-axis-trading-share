# KR ETF RiskBudget Order Sheet Selection Rule

## Purpose

- fix a single operator rule for choosing the correct order sheet
- prevent confusion between initial funding and rebalance

## Initial Sheet Rule

Use `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv` only when:

- the account is starting from cash
- there are no existing live holdings to rebalance

## Rebalance Sheet Rule

Use `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv` only when:

- the account is already funded
- the operator is adjusting existing holdings to the new target portfolio

## Truth Priority

1. actual account state as known by the user
2. `backtests\kis_go_stop_report.csv`
3. `docs\kr_etf_riskbudget_live_runbook_min.md`
4. the selected order sheet file

## Ambiguous Cases

- if both sheets exist:
  - choose by actual account state, not by file existence alone
- if both sheets are missing:
  - do not place manual orders
- if account state is unclear:
  - do not place manual orders
- if GO/STOP is not `GO`:
  - do not use either order sheet

## Operator Rule Summary

1. check `kis_go_stop_report.csv` first
2. if it is not `GO`, stop
3. decide whether the account is starting from cash or already funded
4. open the matching order sheet only
5. manually enter orders only from that selected sheet
