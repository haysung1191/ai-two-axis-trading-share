# Split Models Nightly Safe Summary

## Purpose

- freeze the current strongest / challenger truth before another overnight research push
- make it easy to answer three questions quickly:
  - what is the current strongest branch
  - what is the current best broader challenger
  - why is the strongest still staying alive

## Current truth

- repo: `momentum`
- asset class: `stocks_etfs`
- operational baseline: `rule_breadth_it_us5_cap`
- aggressive strongest: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- broader challenger: `hybrid_top2_plus_third00125`

## Strongest snapshot

- CAGR: `63.16%`
- MDD: `-29.27%`
- Sharpe: `1.6892`
- Annual turnover: `15.32`

## Broader challenger snapshot

- variant: `hybrid_top2_plus_third00125`
- CAGR: `63.12%`
- MDD: `-29.27%`
- Sharpe: `1.6895`
- Annual turnover: `15.32`

## Why strongest still stays

- broader challenger still gives up headline strength:
  - CAGR delta vs strongest: `-0.04%p`
  - `75 bps` cost CAGR delta: `-0.04%p`
  - walk-forward: `2` positive CAGR windows, `2` negative
- broader challenger is still interesting:
  - Sharpe delta vs strongest: `+0.0003`
  - MDD delta vs strongest: `+0.00%p`
  - concentration is meaningfully lower than the strongest
- interpretation:
  - strongest is still the `stronger` branch
  - broader challenger is still the `broader-but-weaker` branch

## Benchmark guardrail

- benchmark: `benchmark_xs_mom_12_1_top5_eq`
- strongest `75 bps` CAGR delta vs benchmark: `+11.49%p`
- strongest start-date shift record: `5` positive CAGR windows, `0` negative

## Bonus Near-Miss

- variant: `bonus_schedule_first55_second45`
- CAGR: `63.58%`
- MDD: `-29.33%`
- Sharpe: `1.6902`
- `75 bps` cost CAGR delta vs strongest: `+0.37%p`
- walk-forward: `2` positive CAGR windows, `2` negative
- verdict: `headline-strong but still below promotion grade because walk-forward stays mixed and drawdown is slightly worse`

## Nightly verdict

- keep the current strongest as the mainline aggressive branch
- do not promote the broader challenger yet
- do not promote the bonus near-miss yet either
- if more overnight work is run, prefer broader-challenger exploration over disturbing the strongest baseline again
