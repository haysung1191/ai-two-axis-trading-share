# Split Models Universe Split Review

## Scope

- test the two current surviving models across simple universe splits
- models:
  - `rule_breadth_it_us5_cap`
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`

## Why this review exists

- the strongest aggressive branch may still be a US winner-cluster strategy in disguise
- the operational baseline may be more general than the aggressive branch
- this review asks where each model survives and where it weakens

## Universe-split results

### Full universe

- `rule_breadth_it_us5_cap`
  - CAGR: `33.43%`
  - MDD: `-25.24%`
  - Sharpe: `1.4482`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR: `63.16%`
  - MDD: `-29.27%`
  - Sharpe: `1.6892`
- aggressive minus baseline:
  - CAGR delta: `+29.72%p`
  - Sharpe delta: `+0.2410`

### US only

- `rule_breadth_it_us5_cap`
  - CAGR: `36.47%`
  - MDD: `-22.18%`
  - Sharpe: `1.4896`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR: `46.43%`
  - MDD: `-18.92%`
  - Sharpe: `1.7108`
- aggressive minus baseline:
  - CAGR delta: `+9.96%p`
  - Sharpe delta: `+0.2212`

### KR only

- `rule_breadth_it_us5_cap`
  - CAGR: `-2.07%`
  - MDD: `-50.36%`
  - Sharpe: `0.0576`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR: `-0.42%`
  - MDD: `-50.52%`
  - Sharpe: `0.1206`
- aggressive minus baseline:
  - CAGR delta: `+1.65%p`
  - Sharpe delta: `+0.0630`

### ETF only

- `rule_breadth_it_us5_cap`
  - CAGR: `7.21%`
  - MDD: `-30.10%`
  - Sharpe: `0.6804`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR: `7.69%`
  - MDD: `-30.10%`
  - Sharpe: `0.7146`
- aggressive minus baseline:
  - CAGR delta: `+0.48%p`
  - Sharpe delta: `+0.0342`

### Stock only

- `rule_breadth_it_us5_cap`
  - CAGR: `25.49%`
  - MDD: `-24.62%`
  - Sharpe: `1.0217`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR: `24.89%`
  - MDD: `-24.13%`
  - Sharpe: `0.9822`
- aggressive minus baseline:
  - CAGR delta: `-0.60%p`
  - Sharpe delta: `-0.0394`

## Interpretation

- the strongest aggressive branch is not broad-based across every slice
- it is strongest in the full mixed universe and still strong in the `US only` split
- it is almost flat in `ETF only`
- it is weak in `KR only`
- most importantly, it does **not** beat the operational baseline in `stock only`

- this implies the convex aggressive edge is not a universal stock-selection improvement
- it appears to rely on the mixed cross-market structure, especially the interaction between US winner concentration and the broader mixed universe construction
- this is useful academically because it narrows the real claim:
  - the aggressive branch is strongest as a mixed-universe portfolio construction rule
  - not as a standalone pure-stock or Korea-only model

## Verdict

- keep `rule_breadth_it_us5_cap` as the operational baseline
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on` as the strongest aggressive research branch
- but narrow the interpretation:
  - it is a strong mixed-universe aggressive branch
  - it is not a universally dominant stock-only or Korea-only rule
