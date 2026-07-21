# Manuscript Draft

## Title

Governance-Aware AI-Silo for Cryptocurrency Strategy Validation

## Abstract

We present a personal AI-silo for cryptocurrency strategy research that treats strategy creation as a governed validation problem rather than a direct trading problem. The system combines LLM-assisted proposal generation, mutation-based strategy evolution, deterministic strategy materialization, multi-asset backtesting, market-regime validation, overfitting checks, rule-based governance, and artifact-driven decision logging within a reproducible workflow. Candidate strategies are evaluated across multiple symbols and regimes, filtered through explicit approval gates, ranked by risk-adjusted metrics, and only approved strategies are persisted to a registry with lineage metadata. The platform is implemented as a modular Python system with typed contracts, workflow orchestration, persistent artifacts, and test coverage for key control points. We argue that the main contribution is not a new predictive model, but a reproducible research architecture that reduces unsafe strategy promotion by combining generation, validation, and governance in one system. We outline an evaluation protocol based on ablations over mutation, multi-asset validation, regime validation, and overfitting controls to measure throughput, rejection causes, and candidate robustness.

## 1. Introduction

Large language models and agentic systems make it increasingly easy to generate large numbers of trading ideas. In practice, however, strategy generation is the easy part. The hard part is deciding which candidates should be trusted, which should be rejected, and which should be promoted for further experimentation. In quantitative trading research, this problem is amplified by overfitting, regime sensitivity, unstable cross-asset behavior, and poor auditability of iterative experimentation.

Most practical research stacks are built as patchworks of notebooks, backtest scripts, and manually curated rules. Those workflows may be fast for individual experimentation, but they are weak in reproducibility and governance. A candidate strategy that appears promising in a single-symbol or single-regime backtest can still fail under broader validation. This creates a gap between rapid idea generation and disciplined strategy promotion.

This work presents a personal AI-silo for cryptocurrency strategy validation. The system is intentionally framed as a validation platform rather than a live trading engine. Candidate strategies are produced by a ResearchAgent that supports both new proposals and mutation-based evolution from historically successful strategies. Generated candidates are materialized into temporary strategy modules and evaluated through a deterministic pipeline that includes multi-asset testing, market regime validation, overfitting checks, QA placeholders, rule-based risk screening, and final decision gating. Only candidates that pass explicit approval conditions are persisted as approved artifacts and recorded in a strategy registry with lineage metadata.

The main contribution of this work is not a new predictive model or a claim of superior trading profitability. Instead, the contribution is a reproducible architecture for strategy validation that combines proposal generation, robustness evaluation, governance, and artifact persistence in one workflow. The repository implements typed scorecards, deterministic evaluation, persistent run artifacts, approval records, lineage-aware strategy evolution, and test-backed control points. This makes the system suitable as a research platform for studying how validation constraints affect candidate throughput and promotion quality.

## 2. System

The system is organized around a validation-centric workflow:

`Research -> Engineer -> Evaluate -> Decision -> Publish`

The Research stage generates ten proposals per run by combining new strategies and mutation-derived strategies. Diversity is enforced across mean reversion, momentum, volatility breakout, trend following, and range trading categories. Mutation proposals are linked to prior approved strategies through explicit lineage metadata.

The Engineer stage converts each proposal into a temporary executable strategy module. Candidate artifacts are written to per-run candidate directories for auditability and later replay.

The Evaluate stage is implemented through a unified candidate evaluator that computes single-asset metrics, multi-asset metrics, regime metrics, overfitting metrics, QA status, and rule violations. Results are stored in typed scorecards.

The Decision stage ranks candidates and applies governance thresholds. The Publish stage writes approval artifacts, decision summaries, leaderboards, and strategy registry updates.

## 3. Validation Methodology

Candidates are tested across multiple symbols, currently BTCUSDT, ETHUSDT, and SOLUSDT, to detect over-specialization to a single asset. Aggregate metrics include mean Sharpe, Sharpe dispersion across assets, mean drawdown, and worst drawdown.

Market regime testing partitions the data into trend, range, high-volatility, and low-volatility subsets. Each subset is backtested independently and summarized through regime-specific Sharpe and drawdown values, along with regime Sharpe dispersion.

Overfitting controls include in-sample and out-of-sample splits, walk-forward evaluation, and parameter sensitivity checks. Strategies that exhibit unstable behavior under these checks are flagged before promotion.

Promotion logic is centralized in the decision policy. Candidates are rejected if they fail QA, violate risk rules, display overfitting flags, show excessive cross-asset instability, or show excessive regime instability.

## 4. Implementation

The implementation uses typed domain contracts, artifact persistence, and deterministic seeds to support reproducibility. Candidate-level and run-level artifacts are retained under structured run directories. A strategy registry maintains longitudinal information about approved strategies, including best metrics, first and latest appearance, source type, and parent lineage.

This implementation choice supports auditability, replay, and mutation-aware research loops. It also makes the platform suitable for benchmark-style experimentation on validation policy choices.

## 5. Experimental Plan

The intended experiments compare simpler proposal-and-backtest workflows against the full governance-aware stack. Planned baselines include single-symbol-only validation, multi-asset validation without regime testing, and full evaluation without mutation. Planned ablations remove mutation, diversity enforcement, multi-asset validation, regime validation, and overfitting gates one at a time.

Primary evaluation outputs include pass rate, rejection reason distribution, multi-asset Sharpe dispersion, regime Sharpe dispersion, and final approval robustness.

## 6. Results

The current repository snapshot already supports a preliminary empirical audit. The exported archive contains candidate-level scorecards, run-level decisions, rejection reasons, and source-type comparisons. In the present raw snapshot, the platform exhibits a highly conservative approval profile: only a small minority of candidates pass all filters, and most runs terminate through repeated rejection followed by circuit-breaker pause. This indicates that the pipeline is functioning as a strict validation stack rather than as a permissive ranking engine.

The current audit also enables an initial comparison between new and mutation-derived proposals. The archived runs show that the intended 50:50 proposal mix is being generated at scale, although the present snapshot does not yet demonstrate a clear empirical advantage for mutation over new proposals. Rejection logs further show that the dominant failure modes are execution-model compliance and baseline performance thresholds, followed by a smaller but still meaningful set of overfitting-related failures.

These results are sufficient to support the system narrative of the paper: the platform is operational, traceable, and conservative in promotion. However, they should still be treated as preliminary because the raw archive mixes runs produced under heterogeneous metadata conditions.

## 7. Discussion

The key contribution of the system is architectural rather than predictive. The platform shows that AI-assisted strategy research can be organized as a governed validation process with explicit artifacts, typed scorecards, deterministic evaluation, and approval policies. This is a useful reframing because modern proposal-generation systems can generate candidate ideas at high throughput, but they do not by themselves provide a reliable basis for promotion.

The observed conservatism of the current workflow is therefore not necessarily a weakness. In a validation-centered research stack, frequent rejection may indicate that unsafe or brittle candidates are being filtered correctly. At the same time, the empirical archive reveals that some of this conservatism is influenced by heterogeneous execution metadata, which means the final paper must separate raw audit evidence from a clean benchmark subset.

The mutation mechanism should also be interpreted carefully. The system clearly supports lineage-aware strategy evolution, but the present registry is still too small to justify a strong claim that mutation improves candidate quality. Mutation is therefore best presented as an implemented and testable research mechanism whose empirical value remains to be established through controlled experiments.

## 8. Limitations

The current work does not claim live profitability or production deployment safety. Its main value is architectural and methodological: it provides a controlled framework for candidate generation and validation. To support stronger empirical claims, additional benchmarking on fixed real-market datasets, stronger baselines, and larger-scale repeated runs are still required.

## 9. Conclusion

This work reframes AI-assisted crypto strategy research as a governed validation process. By integrating proposal generation, mutation lineage, deterministic evaluation, multi-asset and regime testing, overfitting controls, and artifact-based approval logic, the system provides a practical foundation for reproducible research on strategy selection under uncertainty.
