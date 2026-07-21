# Split Models Quality Recipient Family Review

## Scope

- freeze the validated `top1 / top3` bonus-recipient family in one place
- strongest reference:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- reviewed family points:
  - `67 / 33`
  - `75 / 25`
  - `80 / 20`
  - `85 / 15`
  - `90 / 10`

## Why this review exists

- the recent quality near-miss line kept improving on headline CAGR
- but it also kept changing its robustness profile
- this review freezes the whole family so the project can stop revisiting the same axis without new information

## Current reading

- `67 / 33` is the best pure quality point
  - highest Sharpe in the family
  - lowest concentration in the family
  - but headline strength is weaker
- `85 / 15` is the best blended point
  - strongest mix of CAGR, cost support, and still-acceptable robustness
  - this is the current quality/blended near-miss truth
- `90 / 10` is the headline boundary point
  - strongest raw CAGR in the family
  - but walk-forward Sharpe robustness is worse than `85 / 15`

## Verdict

- keep `bonus_recipient_top1_third_85_15` as the quality/blended near-miss current truth
- treat `90 / 10` as the stronger-but-less-robust boundary point
- stop pushing this family further unless a new validation axis is introduced
