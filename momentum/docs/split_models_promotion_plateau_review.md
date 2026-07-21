# Split Models Promotion Plateau Review

## Scope

- map a local parameter grid around the current aggressive strongest branch
- current strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on`
- local axes:
  - `breadth_bottom_slice_count`
  - `breadth_bottom_slice_penalty`
  - `breadth_bottom_slice_penalty_floor`
  - `breadth_top_slice_bonus_exposure`
  - `breadth_bottom_slice_penalty_power`

## Why this review exists

- recent exploratory candidates repeatedly showed the same pattern:
  - weaker fragility is possible
  - but strongest-level performance is hard to keep
- this review asks whether the current strongest sits on a usable local plateau or on an isolated spike

## Result

- combos tested: `32`
- current strongest:
  - `count=7`
  - `penalty=0.40`
  - `floor=0.20`
  - `bonus=0.18`
  - `power=0.50`
  - CAGR `62.69%`
  - Sharpe `1.6898`
- local best by CAGR:
  - `count=6`
  - `penalty=0.35`
  - `floor=0.20`
  - `bonus=0.18`
  - `power=0.50`
  - CAGR `63.16%`
  - Sharpe `1.6892`
- current strongest rank by CAGR: `8`
- near-best combos within `1.00%p` CAGR of best: `14`
- near-best combos within `1.00%p` CAGR and `0.005` Sharpe of best: `14`
- CAGR range across local plateau grid: `2.16%p`
- Sharpe range across local plateau grid: `0.0221`
- axis takeaways:
  - `count=6` and `count=7` are effectively identical in this local grid
  - `bonus=0.18` dominates `bonus=0.17` on CAGR
  - `power=0.50` dominates `power=0.65` on CAGR
  - `penalty=0.35 / floor=0.20` is the local CAGR best point
  - current strongest is slightly below the local CAGR best, but with better Sharpe

## Interpretation

- the current strongest is **not** an isolated spike
- it sits inside a usable local plateau with many nearby combinations that stay close on both CAGR and Sharpe
- that is good news for promotion defense:
  - the strongest branch is not winning only because of a single brittle cell
  - nearby settings remain competitive
- the more important nuance is:
  - local CAGR best does not equal global promotion best
  - the current strongest still matters because it was already validated through walk-forward, cost, benchmark, and promotion-ledger work
- the plateau result therefore supports a careful reading:
  - local parameter sensitivity is acceptable
  - but any move from current strongest to the local CAGR best still needs the full promotion stack, not just headline CAGR

## Verdict

- keep `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on` as the current aggressive strongest branch
- treat the local plateau result as **supportive robustness evidence**
- do not auto-promote the local CAGR best point until it clears walk-forward / cost / fragility checks
