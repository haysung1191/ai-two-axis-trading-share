# ETF RiskBudget Micro-Live Runbook

Purpose:

- define the operator sequence for micro-live execution of `Weekly ETF RiskBudget`
- keep execution mechanical
- separate first funding from ongoing rebalance

## 1. Current scope

- operating strategy: `Weekly ETF RiskBudget`
- deployment tier: micro-live only
- order style: manual
- asset scope: Korea ETF-only
- do not use this runbook for research-only strategies

## 2. Preconditions before any order

All must be true:

- [kis_live_readiness.csv](D:\AI\모멘텀 투자\backtests\kis_live_readiness.csv) shows `Weekly ETF RiskBudget`
- `Recommendation = START_SMALL_LIVE_FIRST` or `START_PAPER_FIRST`
- [kis_shadow_health.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_health.csv) shows `HealthStatus = OK`
- [kis_shadow_ops_summary.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_ops_summary.csv) shows `DailyCheckStatus = GO` or an explicitly explained `REVIEW`
- [kis_shadow_portfolio.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_portfolio.csv) is fresh for the same `RunId`
- no unresolved exceptions in [kis_shadow_exceptions.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_exceptions.csv)

If any fail, do not place live orders.

## 3. Files to open in order

1. [kis_live_readiness.csv](D:\AI\모멘텀 투자\backtests\kis_live_readiness.csv)
2. [kis_shadow_ops_summary.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_ops_summary.csv)
3. [kis_shadow_health.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_health.csv)
4. [kis_shadow_rebalance_diff.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_rebalance_diff.csv)
5. [kis_shadow_portfolio.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_portfolio.csv)

## 4. Which order sheet to use

Use exactly one of these, depending on the situation:

- first funding from zero holdings:
  - [etf_riskbudget_micro_live_initial_sheet_3000000krw.csv](D:\AI\모멘텀 투자\backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv)
  - [etf_riskbudget_micro_live_initial_sheet_3000000krw_summary.csv](D:\AI\모멘텀 투자\backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw_summary.csv)
- ongoing rebalance of an already funded account:
  - [etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv](D:\AI\모멘텀 투자\backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv)
  - [etf_riskbudget_micro_live_rebalance_sheet_3000000krw_summary.csv](D:\AI\모멘텀 투자\backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw_summary.csv)

Current status on `2026-03-30` sizing:

- initial sheet: valid for starting from cash
- rebalance sheet: zero trades at `3,000,000 KRW` because current weight deltas are too small after share rounding

## 5. What to execute for rebalance

Use [kis_shadow_rebalance_diff.csv](D:\AI\모멘텀 투자\backtests\kis_shadow_rebalance_diff.csv).

Only trade rows where:

- `Strategy = Weekly ETF RiskBudget`
- `Action != HOLD`

Execution order:

1. exits
2. decreases
3. increases
4. buys

Reason:

- this reduces accidental over-allocation during manual execution

## 6. Position sizing rule

- micro-live capital must stay within the micro-live cap from the deployment playbook
- target notional per ETF = live capital x target weight or weight change, depending on sheet type
- if exact sizing is not possible, round down
- do not force full allocation by overriding weights manually

## 7. Price discipline

- prefer liquid session execution
- avoid chasing the open in disorderly conditions
- if spread or opening gap is abnormal, delay within the session instead of forcing immediate execution

This strategy is low-turnover by design.

## 8. After execution

Record:

- actual fill time
- actual fill price
- filled quantity
- any skipped or partially filled order
- reason for deviation from target

Use these files:

- [etf_riskbudget_micro_live_order_log_template.csv](D:\AI\모멘텀 투자\backtests\etf_riskbudget_micro_live_order_log_template.csv)
- [etf_riskbudget_micro_live_tracker.csv](D:\AI\모멘텀 투자\backtests\etf_riskbudget_micro_live_tracker.csv)

## 9. Abort conditions

Do not execute if any of:

- live readiness no longer points to `Weekly ETF RiskBudget`
- shadow health is not `OK`
- shadow ops is `STOP`
- target portfolio has missing prices
- market is disorderly and ETF spreads are clearly abnormal

## 10. Current interpretation

- `Weekly ETF RiskBudget` is the operational candidate
- `Weekly Hybrid RS50 RB50` is the paper fallback candidate
- `Weekly Score50 RegimeState` remains a paper candidate
- `ForeignFlow` branch is research-only and must not be traded live from this runbook
