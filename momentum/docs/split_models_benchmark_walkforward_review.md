# Split Models Benchmark Walk-Forward Review

## Scope

- test whether benchmark-relative superiority survives window-by-window, not just over the full sample
- walk-forward setup:
  - window: `24 months`
  - step: `12 months`
- comparison pairs:
  - `rule_breadth_it_us5_cap` vs `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` vs `benchmark_xs_mom_12_1_top5_eq`

## Why this review exists

- the external benchmark chapter is more credible if benchmark outperformance is not just a full-period average
- this review asks whether the current surviving models still hold up against the hardest simple momentum benchmarks across rolling windows

## Baseline vs US-stock top-5 momentum

- model: `rule_breadth_it_us5_cap`
- benchmark: `benchmark_xs_mom_12_1_us_stock_top5_eq`
- windows compared: `4`
- positive CAGR windows: `2`
- negative CAGR windows: `2`
- average CAGR delta: `-4.70%p`
- average Sharpe delta: `+0.1378`
- average MDD delta: `+4.02%p`

### Interpretation

- the operational baseline does **not** dominate the simpler US-stock-only top-5 momentum benchmark on CAGR window by window
- it wins on quality more consistently than on speed:
  - higher average Sharpe
  - shallower average drawdown
- this reinforces the baseline's role as a more operationally defensible portfolio process, not as a pure return-maximizer

## Aggressive strongest vs full-universe top-5 momentum

- model: `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
- benchmark: `benchmark_xs_mom_12_1_top5_eq`
- windows compared: `4`
- positive CAGR windows: `3`
- negative CAGR windows: `1`
- average CAGR delta: `+1.79%p`
- average Sharpe delta: `+0.7933`
- average MDD delta: `+10.57%p`

### Interpretation

- the aggressive strongest branch survives this harder benchmark test much better than the operational baseline
- it beats the simple full-universe top-5 momentum benchmark in most windows on CAGR
- more importantly, it dominates on quality across the full walk-forward set:
  - much higher average Sharpe
  - meaningfully shallower average drawdown
- the weak spot is the latest window `2023-08-31 -> 2026-01-30`, where the simple benchmark posted a higher CAGR
- that means the aggressive strongest branch is strong, but not universally dominant even against simple momentum harvesting

## Verdict

- keep `rule_breadth_it_us5_cap` as the operational baseline
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` as the strongest aggressive research branch
- treat the aggressive branch's benchmark superiority as materially stronger after this review
- treat the operational baseline's benchmark result as quality-first validation, not full return domination
