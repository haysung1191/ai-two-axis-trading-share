# Split Models Overnight Guardrail

## Purpose

- freeze the overnight triage rule before another search run
- stop the project from re-litigating the same near-miss patterns every morning

## Current truth

- strongest:
  - `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
- broader challenger:
  - `hybrid_top2_plus_third00125`
- quality near-miss:
  - `bonus_recipient_top1_third_85_15`
- headline near-miss:
  - `tail_skip_entry_flowweakest_new_bottom4_top25_mid75`

## Guardrail

- kill immediately if:
  - full-period CAGR falls behind the strongest by more than `0.50%p`
  - walk-forward CAGR windows are net negative
  - `75 bps` cost CAGR delta vs strongest is worse than `-0.25%p`
  - residual ex `PLTR/NVDA/MU` is clearly negative
- send to deeper validation if:
  - full-period CAGR delta vs strongest is non-negative
  - walk-forward is at least `3 positive / 1 negative`
  - `75 bps` cost CAGR delta is non-negative
  - residual ex `PLTR/NVDA/MU` is non-negative
- document as near-miss if:
  - the candidate clearly wins one axis such as broader / quality / headline
  - but still fails promotion robustness

## Reading rule

- `stronger` means headline CAGR plus promotion robustness
- `broader` means lower concentration with only small CAGR give-up
- `quality` means better Sharpe / MDD even if turnover or cost-adjusted CAGR weakens
- `headline` means better CAGR / turnover even if Sharpe weakens

## Verdict

- keep the current strongest unless a new candidate clears the stronger-axis gate across full-period, walk-forward, cost, and residual together
