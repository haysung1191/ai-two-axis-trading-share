# Split Models Redistribution Family Review

## Scope

- freeze the validated tail-release redistribution family in one place
- strongest reference:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- reviewed family points:
  - `top0 / mid100`
  - `top25 / mid75`
  - `top50 / mid50`

## Why this review exists

- redistribution became the strongest new family explored in the latest search batch
- it produced the biggest headline jumps seen so far
- but it also kept raising the same promotion question:
  - can drawdown be pulled back enough to become promotable?

## Current reading

- `top0 / mid100`
  - strongest raw boundary point
  - very high CAGR
  - but quality collapses too much
- `top25 / mid75`
  - strong compromise point
  - headline remains very high
  - drawdown improves versus `top0 / mid100`, but still fails promotion grade
- `top50 / mid50`
  - best blended redistribution point
  - strongest mix of CAGR, Sharpe, walk-forward, cost support, and lower turnover
  - this is the current redistribution-family truth
- `tail_rescue_bestflow_if_above_median`
  - practically the same saturation zone as `top50 / mid50`
  - numbers stay very close
  - but it does not beat `top50 / mid50` on CAGR, Sharpe, drawdown, cost, or turnover

## Verdict

- keep `tail_release_top50_mid50` as the redistribution-family current truth
- treat the whole redistribution family as a strong but non-promotable aggressive frontier
- treat `tail_rescue_bestflow_if_above_median` as a redistribution saturation variant, not a separate frontier
- stop pushing this family further unless a new drawdown-control axis is introduced
