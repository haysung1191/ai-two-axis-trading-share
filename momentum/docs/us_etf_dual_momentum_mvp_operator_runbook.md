# US ETF Dual Momentum MVP v1 Monthly Operator Runbook

## Purpose

This is the canonical operator document for the monthly manual workflow.

It closes the operator loop for the existing MVP pipeline:
- Batch 1 = data and signal check
- Batch 2 = target portfolio decision
- Batch 3 = account-state sizing and manual order sheet

This document is for operation only. It does not change model rules.

## What The Operator Must Update First Each Month

Update this file first:
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\account_state_template.csv`

This is the live account-state input for Batch 3.

Do not run Batch 3 for live monthly use until this file contains real account values.

## Minimum Live Account-State Input

Required columns:
- `Ticker`
- `CurrentShares`
- `CurrentCash`
- `Notes`

How to fill them:
- `Ticker`
  - must be one of the canonical ETF tickers only
  - one row per canonical ETF
- `CurrentShares`
  - actual whole shares currently held in that ETF
  - use `0` if the ETF is not currently held
- `CurrentCash`
  - total cash currently available in the account
  - this is account-level cash, not ticker-level cash
  - keep it consistent across the file
- `Notes`
  - optional operator notes only

## How To Treat Different Account States

### All-Cash Initial Entry

Use:
- all `CurrentShares = 0`
- positive `CurrentCash`

This is valid.

### Already-Invested Account

Use:
- real share counts in `CurrentShares`
- real available cash in `CurrentCash`

This is valid.

### Invalid Input That Should Lead To STOP

The account-state input is invalid if:
- a ticker outside the canonical universe appears
- required columns are missing
- `CurrentCash` is blank everywhere
- `CurrentCash` is inconsistent across rows
- total account capital is not positive
- share values are not usable numeric values

## Inputs vs Outputs

### Inputs

- price data source:
  - `D:\AI\모멘텀 투자\data\prices_us_etf_dm_v1\etf\`
- live account-state input:
  - `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\account_state_template.csv`

### Outputs

Batch 1:
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch1\universe_snapshot.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch1\momentum_score_table.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch1\eligibility_table.csv`

Batch 2:
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\defensive_sleeve_decision.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\target_portfolio.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\decision_summary.csv`

Batch 3:
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\order_sheet.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\manual_execution_review.csv`

## Monthly Operating Sequence

### Step 1. Use The Correct Date

Operate monthly only.

The model uses:
- signal date = last trading day of the completed month
- execution date = next trading day

Do not treat partial-month data as the signal month.

### Step 2. Check Batch 1

Open:
- `universe_snapshot.csv`
- `momentum_score_table.csv`
- `eligibility_table.csv`

Confirm:
- latest completed month-end is correct
- all required ETFs are present
- Batch 1 did not fail from missing or stale data

### Step 3. Check Batch 2

Open:
- `decision_summary.csv`
- `target_portfolio.csv`
- `defensive_sleeve_decision.csv`

Confirm:
- `Decision = GO`
- target weights sum to 1
- the monthly holdings target is clear

### Step 4. Update The Live Account-State Input

Open:
- `account_state_template.csv`

Enter:
- actual current ETF shares
- actual current cash

This step is mandatory before live monthly manual use.

### Step 5. Check Batch 3

Open:
- `manual_execution_review.csv`
- `order_sheet.csv`

Confirm:
- `manual_execution_review.csv` says `GO`
- `OrderSheetStatus = READY`
- the order sheet contains practical share deltas

### Step 6. Final Order Review

Before placing manual trades, open:
- `decision_summary.csv`
- `target_portfolio.csv`
- `manual_execution_review.csv`
- `order_sheet.csv`

Use:
- `decision_summary.csv` for the final model decision
- `target_portfolio.csv` for target holdings and weights
- `manual_execution_review.csv` for final operational readiness
- `order_sheet.csv` for manual trade actions and share deltas

## What GO Means Operationally

`GO` means all of the following are true:
- Batch 1 data and signal artifacts are valid
- Batch 2 target portfolio is valid
- Batch 3 account-state sizing is valid
- the order sheet is ready for human manual entry

If both Batch 2 and Batch 3 are `GO`, the operator may place the listed ETF orders manually.

## What STOP Means Operationally

`STOP` means do not place orders.

Read the blocking reason from:
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\decision_summary.csv`
- or `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\manual_execution_review.csv`

Fix the blocking issue first, then rerun the affected batch.

## What Must Never Be Overridden Manually

Do not manually override:
- the canonical ETF universe
- the Batch 2 target portfolio weights
- the Batch 3 share deltas
- the `GO` / `STOP` decision state
- the monthly-only timing rule

If the system says `STOP`, do not place trades.

## Canonical Monthly Operator File Set

This is the smallest practical file set for live monthly operation:

- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\account_state_template.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\decision_summary.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch2\target_portfolio.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\manual_execution_review.csv`
- `D:\AI\모멘텀 투자\backtests\us_etf_dual_momentum_mvp_v1_batch3\order_sheet.csv`
- `D:\AI\모멘텀 투자\docs\us_etf_dual_momentum_mvp_operator_runbook.md`

## Current Official State

Current official Batch 2 state:
- `GO`

Current official Batch 3 state:
- `STOP`

Current official Batch 3 stop reason:
- `total account capital must be positive for practical sizing`

This is not a model failure.

It means the live account-state file is still an empty template and has not yet been populated with real shares and/or real cash.
