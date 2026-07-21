# Rotation Stability Test 2026-03-24

Purpose:

- record the current stability read on `Weekly Score50 Rotation`
- explain why it remains the operating strategy
- explain why it is still paper-first

## Current status

- `RunId = 20260324T040334Z_kis_pipeline`
- operating strategy: `Weekly Score50 Rotation`
- readiness: `PAPER_READY`
- walk-forward:
  - `WindowCount = 3`
  - `WalkforwardAdequate = 1`
- shadow:
  - `HealthStatus = OK`
  - `DailyCheckStatus = GO`

## What looks stable

- top strategy is still `Weekly Score50 Rotation`
- walk-forward evidence now exists for the operating strategy
- OOS summary:
  - `MedianCAGR = 0.082563`
  - `WorstCAGR = 0.064397`
  - `WorstMDD = -0.080958`
  - `WinRate_vs_Benchmark = 1.0`
- cost stress remains positive:
  - base `0.20%`: `CAGR_net = 0.101738`
  - moderate `0.50%`: `CAGR_net = 0.088892`
  - severe `1.00%`: `CAGR_net = 0.067803`
- current shadow run is clean:
  - no missing prices
  - strategy match is intact
  - turnover is `0.0`

## What still looks fragile

- `Rotation` only beats `RegimeState` by a very small margin
- readiness is still `PAPER_READY`, not `SMALL_LIVE_READY`
- strategy is strongly ETF-heavy:
  - `AvgEtfSleeve = 0.827411`
  - `AvgStockSleeve = 0.172589`
- `RangeOsc` still contributes nothing:
  - `OscEntryCount = 0`

## Sleeve comparison

- `Rotation`
  - `CAGR = 0.103462`
  - `MDD = -0.121947`
  - `Sharpe = 1.115492`
- `ETFOnly`
  - `CAGR = 0.064489`
  - `MDD = -0.084176`
  - `Sharpe = 1.003371`
- `StockOnly`
  - `CAGR = 0.103634`
  - `MDD = -0.144867`
  - `Sharpe = 0.997119`

Interpretation:

- ETF-only is safer but leaves too much return on the table
- stock-only keeps return but worsens drawdown and turnover
- current `Rotation` remains the better practical compromise

## Current conclusion

- keep `Weekly Score50 Rotation` as the operating strategy
- keep accumulating paper/shadow evidence
- do not treat the current edge as decisive enough for immediate size deployment
- if micro live is ever attempted, treat it as an execution and discipline test, not strategy validation
