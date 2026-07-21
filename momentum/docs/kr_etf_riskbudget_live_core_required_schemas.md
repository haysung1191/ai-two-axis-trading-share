# KR ETF RiskBudget Live Core Required Schemas

## Purpose

- fix the minimum schema required for the three core operating outputs
- keep the live core readable by a human operator without research context

## 1. Portfolio Engine Output

File:

- `backtests\kis_shadow_portfolio.csv`

Minimum required fields:

- `AsOfDate`
- `Strategy`
- `Symbol`
- `Name`
- `Weight`

Role:

- the single source for target portfolio composition

## 2. Order Sheet Output

Files:

- `backtests\etf_riskbudget_micro_live_initial_sheet_3000000krw.csv`
- `backtests\etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv`

Minimum required fields:

- `TradeDate`
- `Strategy`
- `Symbol`
- `Name`
- `Action`
- `TargetWeight`
- `OrderQuantity`

Role:

- the manual execution sheet used by the human operator

## 3. GO/STOP Output

File:

- `backtests\kis_go_stop_report.csv`

Required fields:

- `Decision`
- `DecisionDate`
- `PortfolioAsOfDate`
- `OrderSheetTradeDate`
- `HealthStatus`
- `DailyCheckStatus`
- `SourceFresh`
- `ReadinessFresh`
- `PortfolioFile`
- `OrderSheetFile`
- `RunbookVersion`
- `MismatchSummary`
- `BlockingReason`

Role:

- the final pre-trade decision artifact for manual execution

## Schema Rule

- if these minimum fields are not present, the artifact is not part of the live core
- extra research fields are allowed outside the live core, but not required for operation
