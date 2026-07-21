# Split Models Promotion Ledger

## Scope

- retired strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on`
- current strongest branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- purpose:
  - make the latest aggressive promotion legible in one place
  - show which axes actually justified the promotion
  - separate "promote" evidence from remaining caution

## Promotion summary

- promote `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on`
- reason:
  - plateau local best improved full-period CAGR while leaving MDD flat
  - walk-forward stayed positive on CAGR in `3` windows and lost in `0`
  - cost advantage survived through `75 bps`
  - benchmark-relative strength improved again while concentration stayed compact-winner heavy
- caution:
  - the branch is still a mixed-universe aggressive construction rule
  - it is still not a stock-only winner

## Promotion ledger

| Axis | Baseline | Candidate | Delta | Verdict | Note |
| --- | ---: | ---: | ---: | --- | --- |
| Full-period CAGR | `62.69%` | `63.16%` | `+0.46%p` | promote | headline CAGR improved without extra drawdown |
| Full-period Sharpe | `1.6898` | `1.6892` | `-0.0005` | caution | Sharpe gave back slightly while MDD stayed flat |
| Walk-forward avg CAGR delta | `0.00%p` | `+0.47%p` | `+0.47%p` | promote | positive CAGR windows `3`, negative `0` |
| Cost latest CAGR delta | `0.00%p` | `+0.42%p` | `+0.42%p` | promote | still ahead at `75 bps` |
| Candidate avg monthly delta | `0.00%p` | `+0.041%p` | `+0.041%p` | promote | candidate keeps a positive average monthly edge over the retired strongest |
| Top-3 positive symbol share | `74.08%` | `73.07%` | `-1.01%p` | caution | concentration remains elevated but modestly improved versus the retired strongest |
| Hard benchmark CAGR delta at `75 bps` | `+11.07%p` | `+11.49%p` | `+0.42%p` | promote | candidate stays further ahead of `12-1 full-universe top5` under high cost |
| Full-universe CAGR delta vs retired strongest | `0.00%p` | `+0.46%p` | `+0.46%p` | promote | strongest family edge improved where the branch family is actually strongest |
| Stock-only CAGR delta vs retired strongest | `0.00%p` | `0.00%p` | `0.00%p` | caution | branch remains mixed-universe; this promotion still does not create a stock-only edge |

## Interpretation

- this promotion was not based on headline CAGR alone
- the plateau-local-best curved ranked-tail branch improved on the main axes that mattered for promotion:
  - full-period quality
  - walk-forward
  - cost
  - hard benchmark defense
- the main things that did **not** change are:
  - this is still strongest as a mixed-universe aggressive branch
  - concentration is still compact-winner heavy in absolute terms
  - it should not be oversold as a universal stock-only model

## Verdict

- treat the curved ranked-tail branch as a real strongest-branch promotion
- use the ledger together with:
  - `docs/split_models_aggressive_branch_review.md`
  - `docs/split_models_branch_search_history.md`
- keep the caution language intact:
  - strongest aggressive branch
  - mixed-universe construction rule
  - still concentration-aware, not operational baseline material
