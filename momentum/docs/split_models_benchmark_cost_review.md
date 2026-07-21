# Split Models Benchmark Cost Review

## Scope

- test whether the current benchmark-relative edge survives under heavier transaction-cost assumptions
- cost grid:
  - `10 bps`
  - `20 bps`
  - `30 bps`
  - `50 bps`
  - `75 bps`
- comparison pairs:
  - `rule_breadth_it_us5_cap` vs `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` vs `benchmark_xs_mom_12_1_top5_eq`

## Why this review exists

- the benchmark chapter is more defensible if benchmark outperformance is not just a low-cost artifact
- this review asks whether the surviving model edges remain after costs are stepped up materially

## Baseline vs US-stock top-5 momentum

- model: `rule_breadth_it_us5_cap`
- benchmark: `benchmark_xs_mom_12_1_us_stock_top5_eq`
- positive CAGR cost points: `1`
- negative CAGR cost points: `4`

### At `75 bps`

- model CAGR: `23.95%`
- benchmark CAGR: `26.80%`
- CAGR delta: `-2.86%p`
- model Sharpe: `1.1090`
- benchmark Sharpe: `0.9762`
- Sharpe delta: `+0.1328`
- model MDD: `-32.14%`
- benchmark MDD: `-29.19%`

### Interpretation

- the operational baseline does not preserve a return edge versus the simpler US-stock top-5 momentum benchmark once costs are pushed high
- however, it still preserves a quality edge through Sharpe
- this makes the baseline look even more like a quality-first operational process rather than a headline-return optimizer

## Aggressive strongest vs full-universe top-5 momentum

- model: `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
- benchmark: `benchmark_xs_mom_12_1_top5_eq`
- positive CAGR cost points: `3`
- negative CAGR cost points: `2`

### At `75 bps`

- model CAGR: `38.26%`
- benchmark CAGR: `38.97%`
- CAGR delta: `-0.71%p`
- model Sharpe: `1.3626`
- benchmark Sharpe: `0.7051`
- Sharpe delta: `+0.6575`
- model MDD: `-34.25%`
- benchmark MDD: `-35.48%`

### Interpretation

- the aggressive strongest branch keeps a CAGR edge over the hard benchmark through `30 bps`
- by `50 bps` and `75 bps`, the simple benchmark slightly overtakes it on CAGR
- even there, the aggressive strongest branch keeps a very large quality advantage:
  - much higher Sharpe
  - slightly shallower drawdown
- this is a strong result, but not a clean domination result: the branch remains robust on quality under cost stress, while its return edge compresses materially

## Verdict

- keep `rule_breadth_it_us5_cap` as the operational baseline
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` as the strongest aggressive research branch
- treat the aggressive branch's benchmark edge as quality-robust but not infinitely cost-insensitive
- treat the baseline as even more clearly a practical-quality model than a pure return-maximizing model
