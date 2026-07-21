# Korea Aggressive Alpha Plan 2026-03-28

Purpose:

- keep the current operating track intact
- define a separate aggressive research track targeting `15% to 20%+ CAGR`
- avoid mixing a high-turnover alpha search with the current `ETF RiskBudget` operating baseline

## 1. Current split

Operating baseline:

- `Weekly ETF RiskBudget`
- role: stability / low-turnover / current operational candidate
- current operating reference:
  - [D:\AI\모멘텀 투자\backtests\kis_live_readiness.csv](D:\AI\모멘텀 투자\backtests\kis_live_readiness.csv)
  - [D:\AI\모멘텀 투자\backtests\kis_strategy_leaderboard_operational.csv](D:\AI\모멘텀 투자\backtests\kis_strategy_leaderboard_operational.csv)

Aggressive research track:

- role: search for a higher-CAGR engine
- acceptable tradeoff:
  - higher turnover
  - higher drawdown
  - lower readiness at first
- not allowed:
  - overwriting the current operating baseline

## 2. Why a separate aggressive track is required

Current operating candidate:

- `Weekly ETF RiskBudget`
- `MedianCAGR ~= 10.26%`
- `CAGR_net_0.5pct ~= 8.33%`
- `WorstMDD ~= -7.55%`
- `AnnualTurnover ~= 1.41`

This is a good operating profile.
It is not a `20% CAGR` profile.

If the target is `20%+`, the search must move toward:

- stronger concentration
- higher turnover
- stronger stock exposure
- more regime dependence

That is a different research objective.

## 3. Aggressive candidate ranking

### Candidate 1

- `ScoreN30_P2.0_ROE0.6`

Why:

- currently the most aggressive price-only candidate already visible in the grid
- no new data is required
- easiest path to an immediate re-test

Current reference:

- gross `CAGR ~= 13.93%`
- `MDD ~= -23.35%`
- `AnnualTurnover ~= 25.30`

Interpretation:

- highest current upside among existing score candidates
- likely very cost-sensitive
- not ready for live use, but the fastest aggressive challenger to test

### Candidate 2

- `ScoreN30_P2.0_ROE0.4`

Why:

- still aggressive
- slightly better balance than candidate 1

Current reference:

- gross `CAGR ~= 13.38%`
- `MDD ~= -16.60%`
- `AnnualTurnover ~= 20.56`

Interpretation:

- lower upside than candidate 1
- better survival odds
- likely the cleaner first aggressive paper candidate

### Candidate 3

- `ForeignFlow v2`

Why:

- only candidate in the current repo that uses a different input source
- if it works, it can beat a pure price-only ceiling

Current state:

- technically integrated
- baseline can look good
- OOS stability is still weak
- remains research-only

Interpretation:

- highest structural upside
- highest implementation and robustness risk

## 4. Immediate experiment order

### Experiment A

- retest `ScoreN30_P2.0_ROE0.4`
- named strategy treatment
- paper-only

Success condition:

- net `CAGR_net_0.5pct >= 0.12`
- `WorstMDD >= -0.20`
- `WindowCount >= 3`
- no catastrophic collapse in named-only walk-forward

### Experiment B

- retest `ScoreN30_P2.0_ROE0.6`
- paper-only

Success condition:

- net `CAGR_net_0.5pct >= 0.14`
- accept worse drawdown than operating baseline
- only keep it if the higher return survives cost stress

### Experiment C

- continue `ForeignFlow v2` only as research
- do not promote

Success condition:

- OOS median CAGR turns positive
- `WorstMDD` materially improves from current weak state
- it must stop looking like a single-regime artifact

## 5. Hard rejection rules

Reject an aggressive candidate if any of:

- `CAGR_net_0.5pct < 0.10`
- `WorstMDD < -0.25`
- walk-forward still depends on one strong window only
- turnover rises but net return does not compensate
- the result only looks good in baseline and collapses in named-only OOS

## 6. Practical rule

- do not fund the aggressive track live before it beats the current operating baseline on return by a meaningful margin
- do not demote `ETF RiskBudget` until the aggressive candidate has both:
  - higher net return
  - acceptable OOS behavior

## 7. Current recommendation

Do this next:

1. run `ScoreN30_P2.0_ROE0.4` as the first aggressive paper candidate
2. run `ScoreN30_P2.0_ROE0.6` as the higher-risk second candidate
3. keep `ForeignFlow v2` research-only
4. keep `Weekly ETF RiskBudget` as the live/micro-live operating baseline
