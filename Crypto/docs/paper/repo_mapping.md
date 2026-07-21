# Repo to Paper Mapping

This file maps the current implementation to publishable paper sections.

## System architecture section

Use these modules:
- `app/domains/research/research_agent.py`
- `app/domains/evaluation/candidate_evaluator.py`
- `app/domains/evaluation/decision_policy.py`
- `app/domains/governance/workflow.py`
- `app/domains/strategy/registry.py`

Claim supported:
- the platform is an artifact-driven AI-assisted research pipeline with explicit validation and approval logic

## Reproducibility section

Use these mechanisms:
- deterministic seeds in evaluation
- artifact persistence under `artifacts/{run_id}/`
- logs under `logs/{run_id}.jsonl`
- typed scorecards and contracts
- unit and integration tests in `tests/`

Claim supported:
- experiment results are reproducible and auditable

## Robustness section

Use these components:
- multi-symbol evaluation
- regime validation
- overfitting evaluation
- decision policy gates

Claim supported:
- the system promotes only candidates that survive multiple robustness filters

## Evolution section

Use these components:
- mutation proposals
- strategy diversity
- strategy registry with lineage

Claim supported:
- the system supports iterative research rather than one-shot proposal generation

## Limits section

Be explicit:
- synthetic data fallback exists in the evaluator
- live market profitability is not established
- real-world execution and slippage realism are still limited
- current evidence is stronger for systems validity than for alpha validity
