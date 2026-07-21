# JDQS Submission Package

## Working Title

Implementable 12-1 Momentum in Large-Cap U.S. Equities:
Evidence from Sector-Constrained, Liquidity-Filtered Portfolio Construction

## Target Journal

- Primary target: `Journal of Derivatives and Quantitative Studies (JDQS)`
- Secondary target after major strengthening: `Asia-Pacific Journal of Financial Studies (APJFS)`
- Fit:
  - quantitative portfolio construction
  - performance measurement
  - portfolio management
  - implementable investment rules under trading frictions
- Why not `Korean Journal of Financial Studies`:
  - the current empirical design is entirely U.S. large-cap equity based
  - this creates a scope mismatch for a journal that is more naturally aligned with Korean-market empirical work

## Core Claim

This paper tests whether a simple and implementable `12-1` momentum strategy on large-cap U.S. equities can outperform a lower-turnover ETF allocation baseline after imposing practical trading constraints. The current evidence in this repository suggests that the stock momentum strategy materially exceeds the ETF baseline in return, remains positive across walk-forward windows, and is not highly fragile to moderate transaction-cost stress. The static present-day S&P 100 universe has now been replaced with a Wikipedia-revision-based point-in-time approximation, but the result should still be framed as a strong research result rather than a publication-ready final estimate.

## Why This Is The Best Current Paper Angle

- the signal is simple and academically legible: `12-1 momentum`
- the implementation constraints are concrete:
  - top `20` names
  - max `3` names per sector
  - 60-day median dollar-volume filter
  - minimum price filter
  - explicit one-way transaction costs
- the empirical separation versus baselines is currently the clearest in the repo
- the Korea operating strategies are more deployable, but less novel as an academic contribution
- the Korea quality/news/flow sidecars are not yet robust enough to support a main-paper claim

## Current Evidence To Use

### Main comparison

Source:

- `backtests/us_momentum_eval_20260329/us_compare.csv`

Current values:

- `US ETF RiskBudget`
  - `CAGR = 4.82%`
  - `MDD = -14.05%`
  - `Sharpe = 0.81`
- `US Same-Universe EW Benchmark`
  - `CAGR = 12.18%`
  - `MDD = -35.80%`
  - `Sharpe = 0.75`
- `US Residual Sector Rotation`
  - `CAGR = 7.43%`
  - `MDD = -32.79%`
  - `Sharpe = 0.49`
- `US Stock Mom12_1`
  - `CAGR = 14.85%`
  - `MDD = -30.67%`
  - `Sharpe = 0.88`

### Walk-forward evidence

Source:

- `backtests/us_momentum_eval_20260329/us_walkforward_summary.csv`

Current values:

- `US ETF RiskBudget`
  - `WindowCount = 5`
  - `MedianCAGR = 6.34%`
  - `WorstCAGR = -2.52%`
  - `WorstMDD = -14.05%`
- `US Residual Sector Rotation`
  - `WindowCount = 5`
  - `MedianCAGR = 11.51%`
  - `WorstCAGR = -1.03%`
  - `WorstMDD = -32.79%`
- `US Stock Mom12_1`
  - `WindowCount = 5`
  - `MedianCAGR = 20.38%`
  - `WorstCAGR = 3.29%`
  - `WorstMDD = -30.67%`

Interpretation:

- the stock momentum strategy is not only a full-sample winner
- it also stays positive in the worst walk-forward CAGR window
- the point-in-time approximation reduces the headline return versus the earlier static-universe build, but the result remains strong enough to keep the paper alive
- the same-universe equal-weight benchmark is now the most important comparison, because it narrows the raw-return gap materially

### Cost robustness

Source:

- `backtests/us_momentum_eval_20260329/us_stock_mom12_1_cost.csv`
- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_break_even_cost.csv`

Current values:

- `5 bps` one-way: `CAGR = 18.54%`
- `7 bps` one-way: `CAGR = 18.41%`
- `10 bps` one-way: `CAGR = 18.21%`
- `15 bps` one-way: `CAGR = 17.89%`
- `25 bps` one-way: `CAGR = 17.24%`

Interpretation:

- the strategy is not collapsing under moderate cost stress
- this supports an implementability narrative better than a pure frictionless backtest
- versus the same-universe equal-weight benchmark, the break-even one-way cost is about `42.8 bps` on a CAGR-match basis
- that is materially above the currently tested `7 bps` one-way assumption

### Capacity practicality

Sources:

- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_capacity_summary.csv`

Current values:

- capacity at `0.1%` participation threshold:
  - about `2.2M USD`
- capacity at `0.5%` participation threshold:
  - about `11.1M USD`
- capacity at `1.0%` participation threshold:
  - about `22.2M USD`

Interpretation:

- the strategy looks plausible for smaller separate accounts and research-scale capital
- capacity is meaningful but not unlimited

### Capital practicality

Sources:

- `backtests/us_momentum_eval_20260329/us_stock_mom12_1_min_capital_summary.csv`
- `backtests/us_stock_mom12_1_20260329/us_stock_mom12_1_order_sheet_5000usd_summary.csv`
- `backtests/us_stock_mom12_1_20260329/us_stock_mom12_1_order_sheet_20000usd_summary.csv`

Current values:

- required capital to hold at least one share of every target position:
  - about `17,462 USD`
- with `5,000 USD` planned capital:
  - only `11` holdings are currently implementable
- with `20,000 USD` planned capital:
  - full `20` holdings become implementable

Interpretation:

- this gives the paper a practical angle that many academic momentum papers skip
- the paper can discuss the interaction between alpha and retail-scale implementation constraints

## Proposed Contribution

This paper does not claim to invent a new momentum factor. The contribution is narrower and more defensible:

- test a transparent `12-1` momentum rule on a liquid large-cap universe
- impose portfolio-level implementation rules that a real allocator would face
- compare the stock strategy against lower-turnover ETF alternatives
- evaluate robustness with walk-forward splits and cost stress rather than one in-sample result only
- quantify the minimum capital needed to approximate the intended target portfolio

Refined contribution statement:

- bridge the gap between canonical momentum evidence and implementable portfolio design
- show whether momentum survives after sector caps, liquidity filters, trading frictions, and capital constraints are imposed jointly
- treat the paper as an implementation study, not a factor-discovery study
- do not claim statistically significant independent alpha beyond standard momentum exposure unless later regressions support it

## Recommended Paper Structure

### 1. Introduction

- motivate the gap between textbook momentum and implementable momentum
- state that many practical allocators face:
  - sector concentration limits
  - liquidity filters
  - transaction costs
  - minimum ticket-size constraints
- present the research question:
  - does a constrained large-cap `12-1` momentum portfolio still dominate simpler ETF allocation baselines?

### 2. Related Literature

- cross-sectional momentum
- implementable or friction-aware momentum
- sector-neutral or sector-constrained equity selection
- portfolio capacity and retail implementation constraints

### 3. Data

- U.S. stock universe:
  - current implementation uses static current `S&P 100` membership
- U.S. ETF baseline universe:
  - broad equity, duration, credit, gold, REIT, sector ETFs
- sample period:
  - stock strategy summary currently spans `2015-01-02` to `2026-03-26`
  - ETF strategy summary currently spans `2014-12-31` to `2026-03-26`
- daily adjusted close data

### 4. Strategy Design

- signal:
  - `12-1 momentum`
- universe filters:
  - large-cap universe
  - liquidity threshold via 60-day median dollar volume
  - minimum price filter
- portfolio construction:
  - top `20`
  - equal weight
  - max `3` names per sector
- trading:
  - month-end rebalance
  - one-way cost assumption tested across multiple levels

### 5. Benchmarks

- `US ETF RiskBudget`
- `US Residual Sector Rotation`

### 6. Empirical Results

- full-sample performance table
- walk-forward performance table
- transaction-cost sensitivity figure
- minimum-capital implementation table

### 7. Discussion

- higher return comes with materially deeper drawdown than ETF allocation
- return robustness is encouraging, but capacity and investability matter
- the sector cap likely improves diversification versus naive momentum concentration

### 8. Limitations

- current stock universe has survivorship bias:
  - `STATIC_CURRENT_SP100_MEMBERSHIP`
- no historical constituent reconstruction yet
- no delisting return treatment documented yet
- current comparison is strategy-level, not factor-regression attribution

### 9. Conclusion

- constrained large-cap momentum remains attractive in this sample
- practical frictions reduce but do not erase the return edge
- publication-grade confirmation requires bias-cleaned universe reconstruction

## Tables And Figures To Prepare

### Tables

- Table 1: point-in-time universe construction, data coverage, and delisting treatment
- Table 2: strategy definitions and portfolio construction rules
- Table 3: full-sample performance comparison including large-cap market benchmark
- Table 4: walk-forward performance summary
- Table 5: cost sensitivity and break-even transaction cost analysis
- Table 6: factor regressions with Newey-West t-statistics
- Table 7: implementation feasibility by capital level
- Table 8: sector-cap versus unconstrained momentum comparison

### Figures

- Figure 1: cumulative NAV comparison
- Figure 2: drawdown comparison
- Figure 3: walk-forward CAGR by window
- Figure 4: CAGR versus transaction cost
- Figure 5: sector weights through time
- Figure 6: performance versus AUM or ADV-based capacity assumptions
- Figure 7: crash-state or high-volatility regime performance

## Abstract Draft

This study evaluates whether a simple but implementable `12-1` momentum strategy on large-cap U.S. equities can outperform lower-turnover ETF allocation alternatives after realistic portfolio constraints are imposed. The tested strategy selects the top 20 stocks by lagged momentum, applies a sector cap of three names per sector, uses a liquidity filter based on 60-day median dollar volume, and rebalances monthly. Using the current research build in this repository, the constrained stock momentum portfolio delivers materially higher full-sample CAGR than ETF-based benchmarks while remaining positive across five walk-forward test windows. The return advantage persists under moderate transaction-cost stress, although drawdowns remain substantially larger than those of the ETF allocation baseline. The study also quantifies a practical minimum-capital threshold needed to approximate the intended target portfolio, linking empirical asset-pricing evidence to retail-scale implementation feasibility. The main limitation is that the present stock universe uses static current S&P 100 membership, so the findings should be interpreted as strong research evidence rather than a final publication-grade estimate until constituent-history bias is removed.

## What Must Be Fixed Before Actual Submission

### Tier 1: mandatory

- replace the current Wikipedia-revision approximation with a stronger point-in-time constituent source
- document delistings, symbol changes, and missing-price handling
- use point-in-time sector labels
- re-run all results after bias cleanup
- add a same-universe large-cap market benchmark
- add publication-quality figures and regression-style summary tables

### Tier 2: strongly recommended

- add risk-adjusted comparison versus market and common factors
- add Carhart 4-factor and FF5 regressions with Newey-West standard errors
- add break-even transaction cost analysis
- add a capacity-aware cost diagnostic
- add turnover decomposition and holding-period distribution
- compare against a naive unconstrained momentum portfolio
- quantify the effect of the sector cap directly

### Tier 3: polish

- add subperiod analysis:
  - pre-COVID
  - COVID shock/recovery
  - post-2022 rate regime
- add bootstrap or block-bootstrap confidence checks
- convert all outputs into a single reproducible paper artifact bundle

## Submission Recommendation

- if submitting soon:
  - target `JDQS`
  - frame as an implementable quantitative portfolio study
- in the current repo state:
  - use the Wikipedia-revision point-in-time build only as an intermediate anti-bias upgrade
  - do not present it as final institutional-grade constituent history
- if aiming above `JDQS` later:
  - only consider `APJFS` after the paper includes point-in-time universe reconstruction, factor-regression evidence, and stronger theoretical framing
- do not pitch this as a new factor-discovery paper
- the current factor regressions show strong `UMD` loading but not yet conventionally significant alpha in `FF5 + UMD`
- do not submit the quality/news sidecar work as the main paper yet
