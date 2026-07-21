# Crypto Research / Infra Backlog

This note reflects external review feedback and translates it into the current `C:\AI\Crypto` codebase context.

The repository currently has two different execution styles:

- Operational / paper path:
  - `jobs/hourly_job.py`
  - `src/paper/broker.py`
  - `src/db.py`
- BTC 1d research path:
  - `app/domains/backtesting/*`
  - `app/domains/evaluation/*`
  - `app/domains/experiments/*`
  - `scripts/validate_btc_1d_*`

The key point is that not every infra improvement belongs in the same lane. Some items should improve the research loop, while others should improve paper/live realism.

## Priority Summary

### P1. Vectorized backtester for research batches

Status:
- Needed for research scale-up
- Not required for the current hourly operational loop

Why this matters:
- Current operational paths are event-loop friendly and appropriate for hourly paper trading.
- However, research now spans a large number of BTC 1d batch experiments and follow-up validations.
- A vectorized backtesting path would reduce iteration cost for:
  - family exploration
  - sensitivity sweeps
  - long-span defensive searches
  - benchmark generation

Where it applies:
- `app/domains/backtesting/*`
- `app/domains/experiments/*`
- BTC 1d batch scripts under `scripts/`

What to build:
- A separate research-only backtester using Pandas/Polars-style columnar execution.
- It should not replace `jobs/hourly_job.py` or `src/paper/broker.py`.
- It should produce the same scorecard-facing metrics already used today:
  - CAGR
  - MDD
  - Sharpe
  - trade count
  - exposure
  - walk-forward inputs

Acceptance goal:
- Same strategy parameters produce materially similar results versus the current research backtester.
- Batch runtime drops enough to make wide parameter sweeps cheap.

Recommended next step:
- Prototype one vectorized BTC 1d runner for the current practical family:
  - `volatility_expansion_reclaim`

### P1. Slippage model upgrade

Status:
- High-value realism upgrade
- Especially important if the project returns to broader KRW alt universes

Why this matters:
- Current paper/live logic still relies on simple slippage assumptions in several places.
- The current model is adequate for coarse BTC 1d research but too flat for:
  - Bithumb KRW alts
  - small-cap names
  - thin books
  - live shadow confidence

Current relevant code:
- `src/paper/broker.py`
- various validation scripts using `fee_bps` / `slippage_bps`

What to improve:
- Replace flat slippage with a liquidity-aware penalty function.
- Candidate features:
  - quote volume
  - recent KRW turnover
  - volatility
  - orderbook depth if available
  - market-cap proxy when direct depth is unavailable

Suggested model shape:
- Base slippage floor for BTC / liquid names
- Penalty increasing as liquidity falls
- Optional regime multiplier during high-volatility periods

Practical note:
- For the current BTC-only 1d work, this is more about making validation conservative.
- For the original KRW multi-asset scanner, this is a much bigger priority.

Acceptance goal:
- Paper validations can report both:
  - flat-cost result
  - liquidity-aware result

Recommended next step:
- Add a `liquidity_adjusted_slippage_bps(...)` helper and wire it into paper validation before changing live-like broker behavior.

### P2. Database migration readiness (SQLite -> PostgreSQL)

Status:
- Not urgent for current BTC 1d daily research
- Worth preparing for if the project returns to higher-frequency or multi-worker operation

Why this matters:
- `src/db.py` currently uses SQLite with WAL and busy timeout.
- That is perfectly reasonable for the current scope.
- But lock contention becomes more likely if the project evolves toward:
  - minute or tick research
  - multiple parallel workers
  - heavier live/paper event ingestion
  - concurrent dashboards / services

Current evidence:
- Runtime DB layer: `src/db.py`
- Container stack already includes PostgreSQL wiring in `docker-compose.yml`

Implication:
- The project is not starting from zero on PostgreSQL readiness.
- But the runtime path still behaves like a SQLite-first app.

What to do now:
- Keep SQLite as the default for local and current ops.
- Avoid unnecessary migration work while the main focus remains BTC 1d model research.
- Prepare portability boundaries:
  - isolate SQL usage
  - avoid SQLite-only assumptions in new code
  - document migration checkpoints

When to promote this item to P1:
- minute/tick data becomes active
- concurrent workers become standard
- shadow/live infra grows beyond single-writer patterns

Recommended next step:
- Add a small DB portability checklist before any new runtime persistence work.

## How this changes project priorities

### For the current BTC 1d project

Immediate focus should be:
1. Practical validation quality
2. Research iteration speed
3. Conservative cost realism

That means:
- vectorized research backtester: yes, high leverage
- adaptive slippage in validations: yes, high leverage
- PostgreSQL migration: prepare, but do not let it steal focus from model work

### For the older hourly KRW scanner / paper loop

Immediate focus should be:
1. slippage realism
2. DB readiness if worker concurrency grows
3. vectorized tooling only if large offline search becomes part of that workflow

## Recommended action order

1. Build a research-only vectorized BTC 1d backtester prototype.
2. Add liquidity-aware slippage to paper validation outputs.
3. Keep SQLite in place, but add DB portability guardrails before further runtime expansion.

## Non-goals for now

- Do not replace the hourly event loop with a vectorized engine.
- Do not migrate to PostgreSQL just because it is available in Docker.
- Do not redesign the entire persistence layer before model validation needs it.

## Bottom line

The review feedback is directionally correct, but the right application is:

- vectorization for research speed
- adaptive slippage for realism
- PostgreSQL readiness for future scale

not a blanket rewrite of the current operational path.
