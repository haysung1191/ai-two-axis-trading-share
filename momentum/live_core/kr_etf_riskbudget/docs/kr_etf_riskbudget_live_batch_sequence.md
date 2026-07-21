# KR ETF RiskBudget Live Batch Sequence

## Purpose

- fix the operating order of the live core
- keep the path from signal to manual decision unambiguous

## Sequence

### 1. Data Input

- load Korea ETF universe and operating prices only

### 2. Portfolio Engine

- produce `backtests\kis_shadow_portfolio.csv`

### 3. Order Sheet

- produce one manual order sheet for the current operating case

### 4. Pre-Trade Control

- read readiness, health, ops, portfolio, order sheet, and runbook
- produce `backtests\kis_go_stop_report.csv`

### 5. User Manual Order Decision

- user reads `backtests\kis_go_stop_report.csv`
- user manually decides whether to enter the order sheet

## Sequence Rule

- the next step must not run on missing upstream outputs
- no research artifact is part of this batch
- no execution logging is part of this batch
