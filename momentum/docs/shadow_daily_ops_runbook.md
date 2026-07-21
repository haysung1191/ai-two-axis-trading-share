# Shadow Daily Ops Runbook

Current default operating strategy:

- `Weekly ETF RiskBudget`

Research-only strategies that should not become the default shadow target:

- `Weekly ForeignFlow v2`
- `Weekly Hybrid Flow50 RS50`

Check these artifacts in order every day:

1. `kis_shadow_ops_summary.csv`
2. `kis_shadow_health.csv`
3. `kis_shadow_rebalance_diff.csv`
4. `kis_shadow_nav.csv`
5. `kis_shadow_exceptions.csv`

## Daily gate

- `GO`: shadow run is operationally fine. Review diffs, then continue paper-shadow tracking.
- `REVIEW`: not fatal, but inspect the health and exceptions artifacts before trusting the run.
- `STOP`: do not rely on the shadow output for the day. Rebuild or rerun first.

## If `HealthStatus` is not OK

- `WARNING`: inspect `kis_shadow_exceptions.csv` and `kis_shadow_rebalance_diff.csv` first.
- `STALE`: rerun the canonical pipeline; do not use stale shadow outputs.
- `ERROR`: treat the run as invalid until the root cause is fixed and rerun completes.

## If strategy mismatch happens

- Compare `RecommendedStrategy` vs `Strategy` in `kis_shadow_ops_summary.csv`.
- If mismatch is intentional, document it and continue.
- If mismatch is not intentional, rerun with the default recommended strategy.

## If turnover is materially large

- Open `kis_shadow_rebalance_diff.csv`.
- Confirm whether the change is expected from regime shift or data refresh.
- If the turnover looks abnormal, inspect `kis_shadow_exceptions.csv` and the latest research outputs.

## If prices are missing

- Check `MissingPriceCount` in `kis_shadow_health.csv`.
- Open `kis_shadow_portfolio.csv` and identify affected tickers.
- Treat missing prices as operational review items before trusting the shadow diff.

## Default operator sequence

- Open `kis_shadow_ops_summary.csv`.
- If `DailyCheckStatus=GO`, inspect the diff and NAV briefly.
- If `DailyCheckStatus=REVIEW`, inspect health, exceptions, and diff before deciding anything.
- If `DailyCheckStatus=STOP`, rerun the pipeline or investigate freshness/data issues first.

## Current operating interpretation

- `Weekly ETF RiskBudget` is the current operating candidate.
- `Weekly Hybrid RS50 RB50` and `Weekly Score50 RegimeState` remain paper candidates.
- If the shadow output defaults to anything outside this set, treat it as a configuration issue.
