# Experiment Plan

## Core research question

Does a governance-aware AI strategy validation pipeline improve the robustness of promoted strategy candidates compared with simpler proposal-and-backtest workflows?

## Main hypotheses

### H1
Mutation plus diversity increases the number of viable candidates without increasing unsafe approvals.

### H2
Multi-asset and regime-aware validation reduces approval of brittle strategies.

### H3
Overfitting and governance gates reduce false positives at the cost of lower pass rate.

## Baselines

1. Proposal + single-symbol backtest only
2. Proposal + multi-asset backtest only
3. Proposal + multi-asset + regime validation
4. Full system without mutation
5. Full system

## Ablations

1. Remove mutation
2. Remove diversity enforcement
3. Remove multi-asset validation
4. Remove regime validation
5. Remove overfitting gate
6. Remove decision policy gates

## Metrics

### Pipeline metrics
- proposals per run
- accepted candidates per run
- rejection reason distribution
- evaluation latency per candidate
- cache hit rate

### Candidate quality metrics
- sharpe mean
- sharpe std across assets
- drawdown worst
- sharpe regime std
- stability score
- overfitting flags count

### Promotion quality metrics
- approval rate
- approval robustness score
- out-of-sample degradation
- false-promotion rate
- rejection efficacy on seeded bad strategies
- search-budget sensitivity

### Governance and systems metrics
- lineage retrieval latency
- artifact coverage rate
- registry update latency
- end-to-end throughput
- bottleneck share by stage

## Tables to produce

### Table 1
System components and responsibilities

### Table 2
Baseline and ablation comparison

Columns:
- setup
- pass rate
- sharpe mean
- cross-asset sharpe std
- regime sharpe std
- overfitting rejection rate

### Table 3
Mutation vs non-mutation proposal quality

Columns:
- source type
- candidates
- pass rate
- median sharpe
- median drawdown

## Figures to produce

1. Full pipeline diagram
2. Candidate funnel:
   proposals -> engineered -> evaluated -> passed -> approved
3. Mutation lineage graph
4. Cross-asset stability plot
5. Regime robustness plot
6. Search-budget vs false-promotion pressure plot
7. End-to-end stage latency breakdown
8. Audit retrieval latency chart

## Minimal publishable empirical package

To make the paper credible, collect at least:
- fixed symbol universe
- fixed timeframe
- fixed historical windows
- at least 30-50 independent runs
- deterministic seeds
- full artifact retention for audit

## Mandatory stress experiments

1. Rejection efficacy:
   - seed intentionally overfit or leaking strategies and verify rejection
2. Search-budget stress:
   - increase proposal/mutation volume and measure selection-bias pressure
3. Cost-friction stress:
   - repeat evaluation under multiple fee/slippage assumptions
4. Cross-asset degeneration:
   - optimize on one asset and test automatic rejection on others
5. Lineage and audit retrieval:
   - measure how quickly the system can reconstruct ancestry and approval evidence
6. Throughput profiling:
   - measure stage-level latency and identify dominant bottlenecks
