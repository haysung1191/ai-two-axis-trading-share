# Clean Benchmark Protocol

This document defines the minimum experiment protocol required to convert the current raw audit snapshot into a submission-grade empirical section.

## Objective

Construct a clean benchmark subset that:
- uses one fixed experimental configuration
- removes mixed metadata artifacts
- produces comparable runs
- supports baseline and ablation analysis

## Fixed configuration

Use exactly one benchmark profile for the first paper draft:

- Symbols: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`
- Interval: `1h`
- Evaluation horizon: fixed historical window
- Proposal count per run: `10`
- Deterministic seed: `42`
- Fee: fixed
- Slippage: fixed
- Evaluation workers: fixed
- Real OHLCV only
- Synthetic fallback: disabled

## Required metadata freeze

Every benchmark run should explicitly define:

- `symbols`
- `ohlcv_interval`
- `ohlcv_start_ts`
- `ohlcv_end_ts`
- `proposal_count`
- `fee_bps`
- `slippage_bps`
- `evaluation_workers`
- `allow_synthetic_ohlcv_fallback = false`

## Required benchmark groups

Run each group under the same fixed data window.

### Group A: full system
- mutation on
- diversity on
- multi-asset on
- regime validation on
- overfitting gates on

### Group B: no mutation
- mutation off

### Group C: no regime validation
- regime gate removed

### Group D: no multi-asset gate
- cross-asset gate removed

### Group E: no overfitting gate
- overfitting gate removed

### Group F: search-budget stress
- same policy as full system
- vary proposal count or mutation depth under fixed data

### Group G: cost-friction stress
- same policy as full system
- repeat with multiple fee/slippage settings

## Minimum repetitions

Collect at least:
- `30` runs per group for workshop/demo quality
- `50+` runs per group for stronger conference submission

## Required exports after each benchmark batch

```powershell
python scripts/export_paper_results.py --artifacts-root artifacts --output-dir paper_results --registry-path strategy_registry.json
```

## Required final tables

1. Baseline/ablation comparison
2. New vs mutation comparison
3. Rejection reason distribution
4. Category-level outcomes
5. Registry/lineage summary
6. Search-budget stress summary
7. Cost-friction sensitivity summary
8. Stage-latency summary

## Required final figures

1. Full pipeline figure
2. Candidate funnel
3. Rejection reason histogram
4. New vs mutation comparison chart
5. Regime instability plot
6. Cross-asset instability plot
7. Search-budget sensitivity plot
8. Stage latency breakdown
9. Audit retrieval latency plot

## Benchmark hygiene rules

- Do not mix ad hoc runs into the benchmark subset.
- Do not change thresholds mid-batch.
- Do not change symbols mid-batch.
- Archive raw artifacts for every run.
- Record LLM model version and prompt settings.
- Record registry and lineage retrieval timings when audit tests are included.

## Additional mandatory checks

1. Seed at least one intentionally flawed strategy family:
   - lookahead leakage
   - unstable high-parameter rule
   - single-asset over-specialized rule
2. Verify that these strategies are rejected and that failure causes are logged.
3. Run at least one repeated clean batch with the same seed and data snapshot to confirm deterministic outcomes.

## Safe paper wording

Use:
- "clean benchmark subset"
- "controlled run batch"
- "fixed execution assumptions"

Avoid:
- "production deployment evaluation"
- "live trading validation"
