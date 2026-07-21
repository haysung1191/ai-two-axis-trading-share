# Draft Abstract

## Abstract v1

We present a personal AI-silo for cryptocurrency strategy research that treats strategy creation as a governed validation problem rather than a direct trading problem. The system combines LLM-assisted proposal generation, mutation-based strategy evolution, deterministic strategy materialization, multi-asset backtesting, market-regime validation, overfitting checks, rule-based governance, and artifact-driven decision logging within a reproducible workflow. Candidate strategies are evaluated across multiple symbols and regimes, filtered through explicit approval gates, ranked by risk-adjusted metrics, and only approved strategies are persisted to a registry with lineage metadata. The platform is implemented as a modular Python system with typed contracts, workflow orchestration, persistent artifacts, and test coverage for key control points. We argue that the main contribution is not a new predictive model, but a reproducible research architecture that reduces unsafe strategy promotion by combining generation, validation, and governance in one system. We outline an evaluation protocol based on ablations over mutation, multi-asset validation, regime validation, and overfitting controls to measure throughput, rejection causes, and candidate robustness.

## Contribution Claims

1. A governance-aware AI research pipeline for crypto strategy validation with explicit approval artifacts and lineage tracking.
2. A unified validation stack that combines multi-asset testing, regime testing, and overfitting controls inside one repeatable scorecard.
3. A practical experiment framework for comparing proposal generation strategies, mutation policies, and validation gates under deterministic execution.

## What not to claim

- Do not claim superior live profitability.
- Do not claim real-money deployment safety.
- Do not claim state-of-the-art forecasting accuracy unless benchmarked directly.
