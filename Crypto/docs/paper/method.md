# Method Draft

## Overview

The system is organized around a validation-centric workflow:

`Research -> Engineer -> Evaluate -> Decision -> Publish`

This design intentionally separates candidate generation from candidate promotion. A strategy proposal is not considered valuable unless it survives the evaluation and decision stages.

## Research

The ResearchAgent generates a fixed number of strategy proposals per run. In the current implementation, the default is ten proposals. The generation policy enforces a balanced mix between newly generated strategies and mutation-derived strategies from the historical strategy registry. Diversity is also enforced across five categories:

- mean_reversion
- momentum
- volatility_breakout
- trend_following
- range_trading

Mutation proposals preserve lineage through `parent_strategy`, allowing the system to model iterative strategy evolution rather than isolated one-shot search.

## Engineering

Each proposal is materialized into a temporary strategy module. This step converts structured proposals into executable strategy logic that conforms to a common strategy protocol. Candidate-level artifacts are written under the run directory to preserve reproducibility.

## Evaluation

Evaluation is performed by a unified `CandidateEvaluator`. For each candidate, the evaluator executes:

1. Single-asset and multi-asset backtesting
2. Market regime validation
3. Overfitting analysis
4. QA placeholder checks
5. Rule-based risk validation

The output is a typed `EvaluationScorecard` that records strategy identity, metrics, gate outcomes, rule violations, and deterministic metadata.

### Multi-asset validation

Candidates are evaluated across multiple symbols, currently including BTCUSDT, ETHUSDT, and SOLUSDT. Aggregate metrics include mean Sharpe, Sharpe dispersion across assets, mean drawdown, and worst drawdown.

### Regime validation

Historical data is partitioned into four regimes:

- trend
- range
- high_volatility
- low_volatility

Regime-specific Sharpe and drawdown values are computed, along with the standard deviation of Sharpe across regimes.

### Overfitting controls

The system evaluates in-sample and out-of-sample metrics, walk-forward windows, and parameter sensitivity. These outputs are converted into explicit flags and gate failures. The goal is to reject candidates that succeed only under narrow parameter or sample conditions.

## Decision

The `DecisionPolicy` ranks validated candidates and applies one source of truth for promotion logic. Candidates may be rejected due to:

- overfitting flags
- low stability score
- excessive cross-asset Sharpe dispersion
- excessive regime Sharpe dispersion
- risk rule violations
- QA failure

Only candidates that pass the policy are eligible for approval.

## Publish

The publish stage persists decision artifacts, approval artifacts, run summaries, and leaderboard outputs. If a candidate is approved, the system also updates a persistent strategy registry containing:

- strategy identifier
- first seen run
- latest run
- best metrics
- lineage metadata
- historical run list

This allows future research runs to generate mutation proposals from historically successful candidates.
