# Results Tables Draft

This file translates the current `paper_results/` CSV exports into paper-ready tables.

Important:
- These numbers are a raw audit snapshot from the current artifact store.
- They should not be treated as the final experimental section.
- A clean benchmark subset should be produced before submission.

## Snapshot Notes

The current raw exports show a strong confound:
- `execution_model` is the most common rejection reason.

This likely reflects mixed historical runs with different metadata quality rather than a stable experimental protocol. For the final paper, report:
- raw audit snapshot
- filtered benchmark subset

## Table 1. Pipeline Snapshot Summary

Source files:
- `paper_results/candidate_metrics.csv`
- `paper_results/decision_outcomes.csv`

Current snapshot:

| Metric | Value |
|---|---:|
| Candidate rows exported | 843 |
| Run decisions exported | 24 |
| Mutation candidates | 420 |
| New candidates | 423 |
| Candidate pass count | 13 |
| Candidate pass rate | 1.54% |
| PASS run count | 1 |
| Non-PASS run count | 23 |

## Table 2. Source Type Comparison

Source file:
- `paper_results/source_type_stats.csv`

Current snapshot:

| Source Type | Candidate Count | Pass Count | Pass Rate | Mean Sharpe |
|---|---:|---:|---:|---:|
| new | 423 | 7 | 0.016548 | 0.274759 |
| mutation | 420 | 6 | 0.014286 | 0.141902 |

Interpretation:
- In the current raw snapshot, newly generated candidates slightly outperform mutation candidates in both average Sharpe and pass rate.
- This is not yet publishable as a final result because the sample mixes heterogeneous runs.

## Table 3. Rejection Reason Distribution

Source file:
- `paper_results/rejection_reasons.csv`

Current snapshot:

| Failed Gate | Candidate Count | Run Count |
|---|---:|---:|
| execution_model | 802 | 79 |
| backtest_sharpe | 630 | 83 |
| backtest_cagr | 554 | 83 |
| backtest_trades | 471 | 83 |
| backtest_win_rate | 365 | 83 |
| overfitting_flags | 106 | 37 |
| overfitting_pass | 106 | 37 |
| overfitting_sensitivity | 106 | 37 |
| qa | 24 | 1 |

Interpretation:
- The dominant failure source is `execution_model`, which suggests many historical runs lacked consistent fee/slippage metadata.
- Performance gates (`backtest_sharpe`, `backtest_cagr`, `backtest_trades`) are the second main filter.
- Overfitting-related failures are material but currently smaller than core performance-rule failures.

## Table 4. Run-Level Outcome Snapshot

Source file:
- `paper_results/decision_outcomes.csv`

Current snapshot:

| Metric | Value |
|---|---:|
| PASS runs | 1 |
| PAUSE runs | 23 |
| FAIL runs | 0 |
| Median reject_count among non-PASS runs | 3 |
| Common terminal mode | circuit-breaker pause after repeated rejection |

Interpretation:
- The current system is conservative.
- Most runs terminate through repeated rejection rather than permissive promotion.
- This is a strong systems result for governance, but it requires cleaner experimental framing before publication.

## Table 5. Registry and Lineage Snapshot

Source file:
- `paper_results/lineage_stats.csv`

Current snapshot:

| Strategy ID | Source Type | Parent Strategy | Best Sharpe | Best CAGR | Best Drawdown | Run Count |
|---|---|---|---:|---:|---:|---:|
| beta_approved | new |  | 1.3 | 0.08 | 0.1 | 18 |
| low_stability_approved | new |  | 1.8 | 0.15 | 0.08 | 1 |

Interpretation:
- Registry functionality works, but the current registry snapshot is too small for a strong lineage analysis section.
- A stronger paper should deliberately collect more approved mutations.

## Table 6. Preliminary Clean Benchmark Summary

Source file:
- `paper_results/clean_benchmark_summary.csv`

Current preliminary batch:

| Group | Runs | Pass Count | Pause Count | Pass Rate | Mean Top Sharpe | Mean Top Drawdown | Mean Top Sharpe Std | Mean Top Regime Std |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full_system | 4 | 0 | 3 | 0.0000 | 1.810266 | 0.232985 | 1.278874 | 2.263685 |
| no_mutation | 4 | 0 | 3 | 0.0000 | 1.810266 | 0.232985 | 1.278874 | 2.263685 |
| no_regime_validation | 3 | 0 | 3 | 0.0000 | 1.810266 | 0.232985 | 1.278874 | 2.263685 |
| no_multi_asset_gate | 3 | 0 | 3 | 0.0000 | 1.810266 | 0.232985 | 1.278874 | 2.263685 |
| no_overfitting_gate | 3 | 0 | 3 | 0.0000 | 1.810266 | 0.232985 | 1.278874 | 2.263685 |

Interpretation:
- The clean benchmark harness is operational and produces grouped outputs.
- The present controlled slice is not yet discriminative enough for a final ablation table.
- This table should be replaced by a stronger batch with seeded bad strategies and cost/search-budget stress before submission.

## Recommended Final Paper Tables

Do not rely on the raw snapshot alone. Build final paper tables from a clean experimental subset:

1. Baseline vs full system
- setup
- candidate pass rate
- approved run rate
- mean Sharpe
- cross-asset Sharpe std
- regime Sharpe std

2. New vs mutation
- source type
- candidate count
- pass rate
- median Sharpe
- median drawdown

3. Rejection reason breakdown
- failed gate
- candidate frequency
- run frequency

4. Category diversity outcomes
- category
- candidate count
- pass count
- mean Sharpe

5. Lineage outcomes
- parent strategy
- mutation count
- mutation pass rate
- best descendant Sharpe
