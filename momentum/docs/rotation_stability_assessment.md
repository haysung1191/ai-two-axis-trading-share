# Rotation Stability Assessment

Current focus:

- operating strategy: `Weekly Score50 Rotation`
- purpose: decide whether paper/shadow accumulation is stable enough to continue and what still blocks future micro live

## 1. Current stability read

- keep `Weekly Score50 Rotation` as the paper/shadow operating strategy
- current status is stable enough to continue paper/shadow accumulation
- current status is not strong enough for immediate live deployment beyond a tightly controlled micro-live experiment

## 2. Why it is stable enough to continue

- latest walk-forward evidence now exists for the operating strategy
  - `WindowCount = 3`
  - `WalkforwardAdequate = 1`
- latest readiness is:
  - `OperationalStatus = fresh`
  - `ReadinessTier = PAPER_READY`
  - `Recommendation = START_PAPER_FIRST`
- latest shadow operations are clean
  - `HealthStatus = OK`
  - `DailyCheckStatus = GO`
  - `RecommendedStrategyMatch = 1`
  - `MissingPriceCount = 0`
  - current diff is stable, not broken

## 3. What still looks fragile

- the edge over `Weekly Score50 RegimeState` is still small
- the strategy remains ETF-heavy on average
  - `AvgEtfSleeve` is materially above `AvgStockSleeve`
- the current stability score is still modest
- `RangeOsc` is still non-contributing and should not be treated as a live candidate

## 4. What blocks a future micro live move

Do not move beyond paper/shadow until these remain clean over repeated review cycles:

- `kis_shadow_ops_summary.csv`
  - mostly `GO`
- `kis_shadow_health.csv`
  - mostly `OK`
- `kis_live_readiness.csv`
  - operating strategy remains `Weekly Score50 Rotation`
- `kis_cost_stress_report.csv`
  - net CAGR remains acceptable under stressed cost scenarios
- `kis_sleeve_compare_report.csv`
  - current rotation remains preferable to trivial sleeve-only alternatives

## 5. Current conclusion

- continue paper/shadow accumulation with `Weekly Score50 Rotation`
- do not treat current status as full live approval
- if shadow stays clean across additional review cycles, then revisit a micro-live rule set using `Weekly Score50 Rotation` as the fixed operating strategy
