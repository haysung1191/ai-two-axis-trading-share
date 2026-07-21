# US ETF Research Track

Purpose:

- keep US-market research separate from Korean live operations
- reuse the existing ETF allocation engine with a liquid US ETF universe
- avoid mixing Korean operating decisions with US research output

## Scope

- market: US ETFs only
- cadence: daily bars
- first model family: ETF allocation / risk budget
- role: research only

## Core universe

Broad equity:

- `SPY`
- `QQQ`
- `IWM`
- `DIA`

Rates and defensive assets:

- `TLT`
- `IEF`
- `SHY`
- `GLD`
- `VNQ`
- `HYG`
- `LQD`

Sector sleeves:

- `XLK`
- `XLF`
- `XLE`
- `XLV`
- `XLI`
- `XLP`
- `XLY`

## Data layout

- prices:
  - [D:\AI\모멘텀 투자\data\prices_us_etf_core](D:\AI\모멘텀 투자\data\prices_us_etf_core)
- universe report:
  - [D:\AI\모멘텀 투자\backtests\us_etf_core_universe.csv](D:\AI\모멘텀 투자\backtests\us_etf_core_universe.csv)
- coverage report:
  - [D:\AI\모멘텀 투자\backtests\us_etf_core_coverage.csv](D:\AI\모멘텀 투자\backtests\us_etf_core_coverage.csv)

## Design rule

- do not let US research outputs overwrite Korean `backtests` canonical operating files
- keep US smoke outputs in separate `tmp_us_etf` or dedicated US artifact paths
- do not promote a US strategy into live operation until it has its own walk-forward and cost review

## First candidate

- `Weekly ETF RiskBudget`

Reason:

- it already behaves best on the Korean operating track under low-turnover constraints
- the US ETF universe is liquid and structurally compatible with the same allocation logic

## Current stance

- Korea remains the active operating track
- US ETFs are now a parallel research track only

## New Candidate

- `Residual Sector Rotation`

Design:

- universe: `XLE`, `XLF`, `XLI`, `XLK`, `XLP`, `XLV`, `XLY`
- safe asset: `SHY`
- signal: 36-month rolling FF5 daily regression alpha
- rebalance: month-end
- hold top 3 sectors with positive residual alpha
- if fewer than 3 sectors have positive alpha, keep the remainder in `SHY`

Artifacts:

- [D:\AI\모멘텀 투자\backtests\us_residual_sector_rotation_20260328\us_residual_sector_rotation_summary.csv](D:\AI\모멘텀 투자\backtests\us_residual_sector_rotation_20260328\us_residual_sector_rotation_summary.csv)
- [D:\AI\모멘텀 투자\backtests\us_residual_sector_rotation_20260328\us_residual_sector_rotation_portfolio.csv](D:\AI\모멘텀 투자\backtests\us_residual_sector_rotation_20260328\us_residual_sector_rotation_portfolio.csv)

## New Stock Candidate

- `US Stock Mom12_1`

Design:

- universe: S&P 100 large-cap stocks
- liquidity filter: 60-day median dollar volume
- signal: `12-1` momentum
- rebalance: month-end
- construction: top 20, equal weight, max 3 names per sector

Artifacts:

- [D:\AI\모멘텀 투자\backtests\us_stock_mom12_1_20260328\us_stock_mom12_1_summary.csv](D:\AI\모멘텀 투자\backtests\us_stock_mom12_1_20260328\us_stock_mom12_1_summary.csv)
- [D:\AI\모멘텀 투자\backtests\us_stock_mom12_1_20260328\us_stock_mom12_1_portfolio.csv](D:\AI\모멘텀 투자\backtests\us_stock_mom12_1_20260328\us_stock_mom12_1_portfolio.csv)
- [D:\AI\모멘텀 투자\backtests\us_alpha_compare_20260328.csv](D:\AI\모멘텀 투자\backtests\us_alpha_compare_20260328.csv)
