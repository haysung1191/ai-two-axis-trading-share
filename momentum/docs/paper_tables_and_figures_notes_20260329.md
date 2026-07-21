# Paper Tables and Figures Notes

## Table 1

Title:

Full-Sample Performance Comparison

Columns:

- Strategy
- CAGR
- MDD
- Sharpe
- Notes

Source files:

- `backtests/us_momentum_eval_pitwiki_20260329/us_compare.csv`

## Table 2

Title:

Walk-Forward Performance Summary

Columns:

- Strategy
- WindowCount
- MedianCAGR
- WorstCAGR
- WorstMDD
- MedianSharpe

Source files:

- `backtests/us_momentum_eval_pitwiki_20260329/us_walkforward_summary.csv`

## Table 3

Title:

Transaction-Cost Sensitivity of the Stock Momentum Strategy

Columns:

- OneWayCostBps
- CAGR
- MDD
- Sharpe

Source files:

- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_cost.csv`

## Table 4

Title:

Break-Even Transaction Cost Relative to the Same-Universe Benchmark

Columns:

- BreakEvenOneWayBps_MeanExcessZero
- BreakEvenOneWayBps_CAGRMatchBenchmark

Source files:

- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_break_even_cost.csv`

## Table 5

Title:

Minimum Capital for Whole-Share Implementation

Columns:

- RequiredCapitalForAllOneShareUSD
- HoldingsCount at 5,000 USD
- HoldingsCount at 20,000 USD

Source files:

- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_min_capital_summary.csv`
- `backtests/us_stock_mom12_1_pitwiki_20260329/us_stock_mom12_1_order_sheet_5000usd_summary.csv`
- `backtests/us_stock_mom12_1_20260329/us_stock_mom12_1_order_sheet_20000usd_summary.csv`

## Table 6

Title:

Capacity Summary by Participation Threshold

Columns:

- ParticipationThreshold
- CapacityAUMUSD
- BottleneckDate
- BottleneckSymbol

Source files:

- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_capacity_summary.csv`

## Table 7

Title:

Factor Regressions with Newey-West Robust Standard Errors

Columns:

- Strategy
- Model
- AlphaAnnual
- AlphaTstatNW
- AdjR2
- factor betas and t-statistics

Source files:

- `backtests/us_momentum_eval_pitwiki_20260329/us_factor_regressions.csv`

## Figure 1

Caption:

Cumulative net asset value for the stock momentum strategy, the same-universe equal-weight benchmark, and the ETF risk-budget benchmark.

File:

- `docs/figures_us_momentum_20260329/figure_1_cumulative_nav.png`

## Figure 2

Caption:

Drawdown paths for the stock momentum strategy, the same-universe equal-weight benchmark, and the ETF risk-budget benchmark.

File:

- `docs/figures_us_momentum_20260329/figure_2_drawdown.png`

## Figure 3

Caption:

CAGR of the stock momentum strategy across one-way transaction-cost assumptions, with the break-even cost relative to the same-universe benchmark marked as a vertical reference line.

File:

- `docs/figures_us_momentum_20260329/figure_3_cost_curve.png`

## Figure 4

Caption:

Estimated strategy capacity as a function of the allowed participation rate in 60-day median dollar volume.

File:

- `docs/figures_us_momentum_20260329/figure_4_capacity_curve.png`

## Figure 5

Caption:

Walk-forward CAGR by test window for the stock momentum strategy, the same-universe equal-weight benchmark, and the ETF risk-budget benchmark.

File:

- `docs/figures_us_momentum_20260329/figure_5_walkforward_cagr.png`

