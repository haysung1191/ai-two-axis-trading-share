# Submission Packet

## Working title

Governance-Aware AI-Silo for Cryptocurrency Strategy Validation

## One-sentence thesis

This paper presents a reproducible, governance-aware validation framework that treats AI-generated crypto strategies as untrusted proposals that must pass multi-asset, regime-aware, and overfitting-aware approval gates before promotion.

## Primary contribution framing

1. A validation-centric AI research workflow for crypto strategy experimentation
2. A unified evaluation stack that combines multi-asset, regime, and overfitting controls inside typed scorecards
3. An artifact-driven promotion process with explicit rejection causes, approval artifacts, and lineage-aware registry updates

## Safe claims

- the system is operational and reproducible
- the system supports mutation-aware proposal evolution
- the system enforces explicit approval gates
- the current archive shows conservative promotion behavior
- the repository provides a benchmarkable framework for validation-policy studies

## Claims to avoid

- superior live trading performance
- market-beating alpha
- production safety for real-money execution
- novelty of standard validation components such as walk-forward testing

## Venue strategy

### Primary

- ACM ICAIF
- finance + AI systems positioning
- strongest fit when framed around validation, governance, and reproducibility

### Secondary

- KDD Workshop on Machine Learning in Finance
- fallback if the empirical package is still more demonstrative than definitive

### Later extension

- The Journal of Finance and Data Science
- use after controlled benchmark reruns, stronger baselines, and repeated clean experiments

## Evidence already in repository

- candidate-level evaluation artifacts in `artifacts/{run_id}/candidates/`
- run-level decisions in `artifacts/{run_id}/decision_record.json`
- registry history in `strategy_registry.json`
- exported audit tables in `paper_results/`
- preliminary clean benchmark manifest in `paper_results/clean_benchmark_manifest_prelim.json`
- preliminary grouped benchmark summary in `paper_results/clean_benchmark_summary.csv`
- generated figures in `paper_figures/`
- compiled review draft in `docs/paper/final_manuscript_compiled.md`

## Hard blockers before submission

1. regenerate results under the clean benchmark protocol
2. tighten abstract/results wording to clean-benchmark numbers
3. venue-specific formatting and reference style conversion
4. add mandatory validation experiments around false-promotion suppression and cost/regime stress
5. validate lineage/audit retrieval and stage-latency measurements

## Immediate operator workflow

1. collect external literature using `docs/paper/deepresearch_handoff.md`
2. rerun benchmark protocol
3. run `python scripts/build_paper_package.py`
4. review `docs/paper/final_manuscript_compiled.md`
5. convert to venue-specific template

## Minimum additional experiments

1. Approval-gate ablation to measure how each gate affects false promotion and OOS degradation
2. Search-budget stress test to show how more candidate attempts increase data-snooping risk
3. PBO-backed reporting or equivalent overfitting-probability analysis in the approval policy
4. Regime-conditional reporting rather than only full-period aggregate metrics
5. Fee/slippage and overtrading stress across multiple cost assumptions
6. Deterministic reproducibility check across repeated clean runs
7. LLM-induced failure-case study for hallucinated, leaking, or non-executable strategies
8. Governance-artifact coverage audit for cards, reports, and approval documentation
