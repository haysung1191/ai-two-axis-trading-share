# Split Models Promotion Defense Refresh

## Purpose

- freeze the current strongest after another batch of family exploration
- show why the strongest still stays even though several near-miss axes improved

## Current reading

- strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- broader challenger:
  - `hybrid_top2_plus_third00125`
- quality near-miss:
  - `bonus_recipient_top1_third_85_15`
- headline near-miss:
  - `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`
- defensive weighting near-miss:
  - `regime_weight_defensive_if_top2flowsoft`
- stronger-but-more-fragile near-miss:
  - `multi_step_confirm_top1_flowtop2`
- stronger-but-lower-quality near-miss:
  - `tail_release_top50_mid50`

## What changed in this search batch

- stronger / broader / quality / headline / redistribution axes are now all visible at once
- several challengers improved one part of the frontier, but none cleared promotion grade
- the newest redistribution family showed the clearest split between headline strength and quality collapse

## Axis interpretation

- strongest:
  - still the only branch that keeps headline, Sharpe, drawdown, and promotion robustness in balance
- broader:
  - `hybrid_top2_plus_third00125`
  - best "broader-but-weaker" point
- quality:
  - `bonus_recipient_top1_third_85_15`
  - best blended-quality extension
- headline:
  - `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`
  - best lower-turnover headline extension
- defensive weighting:
  - `regime_weight_defensive_if_top2flowsoft`
  - closest defensive weighting point, but still slightly weaker on cost and fragility
- stronger-but-more-fragile:
  - `multi_step_confirm_top1_flowtop2`
  - stronger and cleaner on paper, but concentration worsens too much
- stronger-but-lower-quality:
  - `tail_release_top50_mid50`
  - best redistribution contender: headline and Sharpe both improve, but drawdown is still too weak for promotion
- tail rescue saturation:
  - `tail_rescue_bestflow_if_above_median`
  - effectively the same redistribution saturation zone as `tail_release_top50_mid50`
  - not a separate promotable frontier

## Dead or Saturated Families

- quality-headline hybrid:
  - blended numbers improved, but Sharpe loss stayed too large
- risk-on exposure:
  - no point beat strongest on headline and robustness together
- risk-off tightening:
  - quality improved a little, but headline weakened too much
- entry filter:
  - more stable near-miss shapes, but no strongest replacement
- hold buffer:
  - strongest-equivalent no-op
- position-cap / sector-cap:
  - breadth improved, but alpha was cut too aggressively
- flow filter / soft blacklist / dynamic bonus:
  - they weakened alpha more than they fixed fragility
- aggressive redistribution:
  - headline surged, but drawdown still failed promotion grade
- tail rescue saturation:
  - almost identical to the redistribution frontier, but still weaker than `tail_release_top50_mid50`

## Verdict

- strongest should still stay as-is
- this batch improved the defense map more than it improved the mainline branch
- future search should avoid dead families and focus only on genuinely different structures
