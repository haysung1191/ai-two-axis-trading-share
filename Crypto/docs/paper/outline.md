# Paper Outline

## 1. Introduction
- Problem: LLMs can generate many trading ideas, but uncontrolled promotion of candidate strategies is unsafe and noisy.
- Gap: Existing work often focuses on alpha generation, not governed validation pipelines.
- Thesis: A research-oriented AI-silo should prioritize reproducible validation and approval logic over raw strategy generation.

## 2. System Overview
- ResearchAgent
- Engineer/materializer
- CandidateEvaluator
- DecisionPolicy
- Governance workflow
- Artifact store and registry

## 3. Method
- Strategy proposal generation
- Mutation and lineage
- Diversity enforcement
- Multi-asset evaluation
- Regime-based validation
- Overfitting detection
- Rule-based decision policy

## 4. Implementation
- Python/FastAPI architecture
- Typed contracts
- Artifact persistence
- Deterministic evaluation
- Parallel candidate evaluation

## 5. Experimental Protocol
- Datasets and symbols
- Time windows
- Candidate count per run
- Baselines
- Ablations
- Metrics

## 6. Results
- Throughput
- Pass/reject distribution
- Cross-asset stability
- Regime stability
- Effect of mutation
- Effect of gates

## 7. Discussion
- Strengths
- Failure modes
- Limits of LLM-generated strategies
- Threats to validity

## 8. Conclusion
- Research validation as the main contribution
- Future work toward stronger benchmarking and controlled live deployment
