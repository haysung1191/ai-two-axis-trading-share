# Split Models External Benchmark Review

## Scope

- compare the current operational baseline and strongest aggressive research branch against simple external equity/ETF benchmarks
- model variants:
  - `rule_breadth_it_us5_cap`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- benchmark set:
  - `benchmark_spy_buy_hold`
  - `benchmark_kospi200_buy_hold`
  - `benchmark_spy_kospi_equal_weight`
  - `benchmark_spy_sma10`
  - `benchmark_xs_mom_12_1_top5_eq`
  - `benchmark_xs_mom_12_1_us_stock_top5_eq`

## Why this review exists

- internal branch comparisons alone are not enough for research defense
- this review asks whether the live baseline and strongest aggressive branch beat simple, recognizable external standards

## Benchmark metrics

- `benchmark_spy_buy_hold`
  - CAGR: `15.10%`
  - MDD: `-21.05%`
  - Sharpe: `0.9921`
- `benchmark_kospi200_buy_hold`
  - CAGR: `21.76%`
  - MDD: `-35.58%`
  - Sharpe: `0.9253`
- `benchmark_spy_kospi_equal_weight`
  - CAGR: `19.08%`
  - MDD: `-26.16%`
  - Sharpe: `1.0971`
- `benchmark_spy_sma10`
  - CAGR: `11.01%`
  - MDD: `-15.36%`
  - Sharpe: `1.0227`
- `benchmark_xs_mom_12_1_top5_eq`
  - CAGR: `49.10%`
  - MDD: `-32.83%`
  - Sharpe: `0.7958`
- `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - CAGR: `33.12%`
  - MDD: `-26.74%`
  - Sharpe: `1.1441`

## Model metrics

- `rule_breadth_it_us5_cap`
  - CAGR: `33.43%`
  - MDD: `-25.24%`
  - Sharpe: `1.4482`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR: `63.16%`
  - MDD: `-29.27%`
  - Sharpe: `1.6892`

## Relative comparison

### Operational baseline: `rule_breadth_it_us5_cap`

- versus `benchmark_spy_buy_hold`
  - average monthly delta: `+1.62%p`
  - positive months: `35`
  - negative months: `26`
- versus `benchmark_kospi200_buy_hold`
  - average monthly delta: `+0.86%p`
  - positive months: `35`
  - negative months: `26`
- versus `benchmark_spy_kospi_equal_weight`
  - average monthly delta: `+1.24%p`
  - positive months: `33`
  - negative months: `28`
- versus `benchmark_spy_sma10`
  - average monthly delta: `+2.05%p`
  - positive months: `35`
  - negative months: `26`
- versus `benchmark_xs_mom_12_1_top5_eq`
  - average monthly delta: `-2.99%p`
  - positive months: `34`
  - negative months: `27`
- versus `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - average monthly delta: `-0.18%p`
  - positive months: `30`
  - negative months: `31`

### Aggressive strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`

- versus `benchmark_spy_buy_hold`
  - average monthly delta: `+3.97%p`
  - positive months: `36`
  - negative months: `25`
- versus `benchmark_kospi200_buy_hold`
  - average monthly delta: `+3.21%p`
  - positive months: `34`
  - negative months: `27`
- versus `benchmark_spy_kospi_equal_weight`
  - average monthly delta: `+3.59%p`
  - positive months: `37`
  - negative months: `24`
- versus `benchmark_spy_sma10`
  - average monthly delta: `+4.40%p`
  - positive months: `38`
  - negative months: `23`
- versus `benchmark_xs_mom_12_1_top5_eq`
  - average monthly delta: `-0.64%p`
  - positive months: `34`
  - negative months: `27`
- versus `benchmark_xs_mom_12_1_us_stock_top5_eq`
  - average monthly delta: `+2.17%p`
  - positive months: `33`
  - negative months: `28`

## Benchmark Walk-Forward Review

### Operational baseline vs `12-1 US-stock top5 momentum`

- windows compared: `4`
- positive CAGR windows: `2`
- negative CAGR windows: `2`
- average walk-forward CAGR delta: `-4.70%p`
- average walk-forward Sharpe delta: `+0.1378`
- average walk-forward MDD delta: `+4.02%p`

### Aggressive strongest vs `12-1 full-universe top5 momentum`

- windows compared: `4`
- positive CAGR windows: `3`
- negative CAGR windows: `1`
- average walk-forward CAGR delta: `+15.57%p`
- average walk-forward Sharpe delta: `+0.8070`
- average walk-forward MDD delta: `+9.76%p`
- best relative window: `2022-07-29 -> 2024-11-29`
- worst relative window: `2023-08-31 -> 2026-01-30`

## Benchmark Cost Review

### Operational baseline vs `12-1 US-stock top5 momentum`

- at `75 bps` one-way cost:
  - baseline CAGR: `23.95%`
  - benchmark CAGR: `26.80%`
  - CAGR delta: `-2.86%p`
  - baseline Sharpe: `1.1090`
  - benchmark Sharpe: `0.9762`
  - Sharpe delta: `+0.1328`

### Aggressive strongest vs `12-1 full-universe top5 momentum`

- at `75 bps` one-way cost:
  - strongest CAGR: `50.46%`
  - benchmark CAGR: `38.97%`
  - CAGR delta: `+11.49%p`
  - strongest Sharpe: `1.4345`
  - benchmark Sharpe: `0.7051`
  - Sharpe delta: `+0.7294`
- positive CAGR cost points: `5`
- negative CAGR cost points: `0`

## Benchmark Start-Date Shift Review

### Aggressive strongest vs `12-1 full-universe top5 momentum`

- start shifts tested: `5`
- positive CAGR shifts: `5`
- negative CAGR shifts: `0`
- positive Sharpe shifts: `5`
- negative Sharpe shifts: `0`
- average start-shift CAGR delta: `+14.57%p`
- average start-shift Sharpe delta: `+0.9362`
- tested start dates:
  - `2020-01-31`: CAGR delta `+14.07%p`, Sharpe delta `+0.8934`
  - `2020-08-31`: CAGR delta `+19.60%p`, Sharpe delta `+0.9489`
  - `2021-04-30`: CAGR delta `+16.47%p`, Sharpe delta `+0.8947`
  - `2021-11-30`: CAGR delta `+8.16%p`, Sharpe delta `+0.8098`
  - `2022-07-29`: CAGR delta `+14.57%p`, Sharpe delta `+1.1342`
- interpretation:
  - benchmark-relative Sharpe superiority is stable even when the start date moves forward
  - benchmark-relative CAGR superiority is now positive in every tested late-start window
  - the deeper softer ranked-tail strongest improved this axis again enough that both CAGR and Sharpe stay positive across all tested shifts

## Interpretation

- both current live baseline and current strongest aggressive branch still beat passive and simple timing benchmarks on both CAGR and Sharpe over the same `61`-month window
- the added `12-1` cross-sectional momentum benchmarks are the first genuinely hard external comparators
- `rule_breadth_it_us5_cap` does **not** beat the simple full-universe top-5 momentum benchmark on CAGR, but it does beat it meaningfully on Sharpe (`1.4482` vs `0.7958`) and on drawdown (`-25.24%` vs `-32.83%`)
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on` beats the simple full-universe top-5 momentum benchmark on CAGR (`63.16%` vs `49.10%`) and Sharpe (`1.6892` vs `0.7958`) while also keeping drawdown tighter (`-29.27%` vs `-32.83%`)
- the aggressive strongest branch also beats the simpler US-stock-only top-5 momentum benchmark on CAGR, Sharpe, and average monthly delta
- benchmark-relative walk-forward also improved again: the new strongest branch keeps `3` positive CAGR windows and lifts average walk-forward CAGR delta to `+15.57%p`
- benchmark-relative cost robustness also improved again: at `75 bps` one-way cost the new strongest branch beats full-universe top5 momentum by `+11.49%p` CAGR and `+0.7294` Sharpe
- benchmark-relative start-date-shift is cleaner again: every tested shift is now positive on both CAGR and Sharpe, and the average start-shift CAGR delta widened to `+14.57%p`
- this benchmark chapter is now materially stronger: the surviving models are no longer only beating passive baselines, they are also competing against simple literature-like momentum rules

## Verdict

- keep `rule_breadth_it_us5_cap` as the operational baseline
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on` as the strongest aggressive research branch
- treat benchmark superiority as supportive evidence, not final proof: the next research step should make the benchmark chapter more statistically defensible, not merely broader
