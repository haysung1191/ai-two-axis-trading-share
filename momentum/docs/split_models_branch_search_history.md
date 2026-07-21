# Split Models Branch Search History

## Purpose

- document the realized branch-search path for the split-model research program
- make model selection less opaque
- provide a first defense against "you tested many things and just kept the lucky one" criticism

## Search policy used in practice

- weak branches were killed quickly
- cosmetic refinements were not preserved
- branches that improved only by narrow-period effects were not promoted
- operational baseline and aggressive research branch were evaluated separately
- a branch needed at least one structurally meaningful improvement before promotion:
  - full-period improvement
  - or better weak-period behavior
  - or better cost / walk-forward / regime robustness

## Operational track history

### Internal progression

1. `equal_weight_no_mad_min4`
   - simple equal-weight reference branch
   - used as an internal baseline for later refinements

2. `rule_breadth_risk_off`
   - first major operational improvement
   - reduced drawdown meaningfully with limited CAGR sacrifice

3. `rule_breadth_it_risk_off`
   - added IT concentration control
   - improved drawdown further

4. `rule_breadth_it_us5_cap`
   - added US position cap
   - promoted as the current operational baseline

### Operational branch verdict

- surviving operational baseline: `rule_breadth_it_us5_cap`
- retired operational candidates:
  - `equal_weight_no_mad_min4`
  - `rule_breadth_risk_off`
  - `rule_breadth_it_risk_off`
- reason for final promotion:
  - better robustness / tradability balance than prior operational branches
  - lower dependence on narrow US winner concentration than aggressive branches

## Aggressive research track history

### Internal progression

1. `rule_sector_cap2`
   - introduced sector-constrained aggressive selection

2. `rule_sector_cap2_breadth_risk_off`
   - added breadth control

3. `rule_sector_cap2_breadth_it_risk_off`
   - added IT concentration control

4. `rule_sector_cap2_breadth_it_us5_cap`
   - added US position cap

5. `rule_sector_cap2_breadth_it_us5_risk_on`
   - first risk-on aggressive strong branch

6. `rule_sector_cap2_breadth_it_us5_top2_risk_on`
   - concentrated extra exposure into top two winners
   - promoted over plain `risk_on`

7. `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
   - funded top-two overweight by cutting the tail more aggressively
   - promoted over plain `top2_risk_on`

8. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
   - kept the same top-two winner target
   - improved the convex source by penalizing the weakest tail names more than the rest of the tail
   - promoted over `top2_convex_risk_on`

9. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35_risk_on`
   - deepened the ranked-tail source one level further
   - widened the bottom slice to `count=4` and lowered the penalty floor to `0.35`
   - promoted over `top2_convex_ranked_tail_risk_on`

10. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_floor40_risk_on`
   - broadened the ranked-tail source one level further
   - widened the bottom slice to `count=5` and eased the penalty floor to `0.40`
   - promoted over `top2_convex_ranked_tail_count4_floor35_risk_on`

11. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on`
   - kept the broader `count=5` source but softened the tail penalty to `0.55`
   - lowered the floor to `0.35` so the weakest tail names still absorb the deepest cut
   - promoted over `top2_convex_ranked_tail_count5_floor40_risk_on`

12. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on`
   - kept the broader `count=5` source again but softened the tail penalty one step further to `0.50`
   - lowered the floor to `0.30` so the weakest tail names still absorb the deepest cut
   - promoted over `top2_convex_ranked_tail_count5_pen55_floor35_risk_on`

13. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_risk_on`
   - widened the ranked-tail source much further to `count=7`
   - softened the tail penalty to `0.40` and lowered the floor to `0.20`
   - promoted over `top2_convex_ranked_tail_count5_pen50_floor30_risk_on`

14. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on`
   - kept the deeper softer `count=7 / pen=0.40 / floor=0.20` source
   - increased top-slice bonus exposure from `0.15` to `0.18`
   - promoted over `top2_convex_ranked_tail_count7_pen40_floor20_risk_on`

15. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on`
   - kept the deeper softer `count=7 / pen=0.40 / floor=0.20` source and the `0.18` top-slice bonus
   - changed the tail-penalty curve from linear to `power=0.5`
   - promoted over `top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on`

16. `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
   - kept the curved `power=0.5` tail penalty and `0.18` top-slice bonus
   - tightened the ranked-tail source from `count=7 / pen=0.40` to `count=6 / pen=0.35`
   - promoted over `top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on`

### Aggressive branch verdict

- surviving aggressive strong branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- retired aggressive branches:
  - `rule_sector_cap2`
  - `rule_sector_cap2_breadth_risk_off`
  - `rule_sector_cap2_breadth_it_risk_off`
  - `rule_sector_cap2_breadth_it_us5_cap`
  - `rule_sector_cap2_breadth_it_us5_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_floor40_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on`

## Killed exploratory branches

These were tested and not preserved because they failed one or more of:
- stronger full-period performance
- better weak-period behavior
- better robustness
- non-cosmetic structural contribution

### Killed as weak or dominated

- `rule_sector_cap2_us5_cap`
  - slightly higher CAGR than prior branch, but worse MDD / Sharpe

- `rule_sector_cap2_it_us5_cap`
  - higher CAGR, but worse MDD / Sharpe / turnover

- `rule_sector_cap2_breadth_it_us5_mad`
  - lower CAGR and weaker overall quality

- `rule_sector_cap2_no_sector_filter_it_us5_cap`
  - lower CAGR and much weaker Sharpe

- `rule_sector_cap2_no_flow_it_us5_cap`
  - substantially weaker CAGR / Sharpe

- `rule_sector_cap2_breadth_it_us5_top1_country`
  - over-concentrated and weaker

- `rule_sector_cap1_breadth_it_us5_cap`
  - too restrictive, large CAGR collapse

- `rule_sector_cap2_breadth_it_us5_turnover_risk_on`
  - slightly lower turnover but clearly weaker CAGR / Sharpe

- `rule_sector_cap2_breadth_it_us5_sector_leaders_risk_on`
  - concentration improvement came at too much CAGR cost

- `rule_sector_cap2_breadth_it_us5_newhigh_risk_on`
  - weaker than both `risk_on` and `top2_risk_on`

- `rule_sector_cap2_breadth_it_us5_us_top2_risk_on`
  - close, but still inferior to `top2_risk_on`

- `rule_sector_cap2_breadth_it_us5_top1_risk_on`
  - higher CAGR, but weaker weak-period behavior and worse concentration

- `rule_sector_cap2_breadth_it_us5_top2_persist_risk_on`
  - slightly lower turnover but dominated by `top2_risk_on`

- `rule_sector_cap2_breadth_it_us5_top3_risk_on`
  - lower CAGR / Sharpe than `top2_risk_on`

- `rule_sector_cap2_breadth_it_us5_cross_sector_top2_risk_on`
  - lower CAGR / Sharpe than `top2_risk_on`

- `rule_sector_cap3_breadth_it_us5_top2_convex_risk_on`
  - lower CAGR / Sharpe than `top2_convex_risk_on`

- `rule_sector_cap2_breadth_it_us5_top2_convex_gross_risk_on`
  - higher headline CAGR, but treated as leverage-like micro-tuning and worse weak-period loss-month behavior

- `hybrid_top2_plus_third01`
  - best recent broader challenger
  - improved Sharpe and concentration, but still gave up too much CAGR and degraded to a `2-2` walk-forward split

- `top2_split_49_51`
  - mild top-two internal rebalance
  - slightly broadened the edge beyond the familiar winner basket, but stayed weaker than both the strongest branch and the hybrid challenger

- `alt_family_top3_flat_bonus18`
  - explicit broad-family boundary check
  - much broader and less concentrated, but far too weak on CAGR / Sharpe / walk-forward to remain a live aggressive promotion candidate

### Killed as cosmetic or effectively identical

- `rule_sector_cap2_breadth_it_us5_buffer4`
  - no material difference vs surviving branch at the time

- `rule_sector_cap2_breadth_it_us5_selective_risk_on`
  - effectively identical to existing strong branch

- `rule_sector_cap2_breadth_it_us5_risk_on_momentum_weighted`
  - no effective difference vs existing branch

## Current interpretation

- operational baseline selection is relatively defensible:
  - the live candidate is not just the highest CAGR branch
  - it was chosen for robustness and tradability

- aggressive branch selection is more vulnerable:
  - the final branch is genuinely stronger than its predecessors on several checks
  - but it also came from a non-trivial search process and remains concentration-heavy
- recent broader-challenger work adds a useful nuance:
  - the project can produce less concentrated aggressive candidates
  - but they have not yet matched the strongest branch on full-period plus walk-forward plus cost

- the branch history therefore supports two claims at once:
  1. the final aggressive branch was not selected from a trivial or cosmetic search
  2. the final aggressive branch still requires caution because it emerged from a meaningful branch-search tree

## What this document does not prove

- it does not statistically eliminate data-snooping bias
- it does not replace DSR, White's Reality Check, or SPA-style tests
- it does not prove the final aggressive branch is a publishable standalone result

## Verdict

- use this document as a transparent branch-search log
- treat it as a first-line qualitative defense against selection-bias criticism
- do not oversell it as a full statistical correction
