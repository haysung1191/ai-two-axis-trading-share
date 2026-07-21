# Limitations and Threats to Validity

## What this system does not prove

- It does not prove long-term live profitability.
- It does not prove that LLM-generated strategies outperform expert-designed strategies.
- It does not prove deployment safety in real-money execution.

## Current empirical limits

- Some evaluation paths support synthetic OHLCV fallback, which is useful for deterministic testing but weaker for publishable empirical claims.
- The current implementation is strongest as a systems and validation framework, not as an alpha benchmark.
- The live execution path is intentionally out of scope.

## Threats to validity

### External validity
- Results on a small symbol universe may not generalize to broader markets.
- Crypto market structure changes quickly, so robustness claims must be tested across rolling windows.

### Construct validity
- Sharpe, drawdown, and regime dispersion are reasonable but incomplete proxies for strategy quality.
- QA is currently represented by a placeholder-style validation layer and should be strengthened for stronger claims.

### Internal validity
- Strategy templates are simple and may bias the search space toward interpretable heuristics.
- Mutation quality depends on the quality of the strategy registry and the chosen mutation rules.

### Reproducibility risk
- LLM-backed proposal generation can vary depending on model configuration unless prompts, model versions, and outputs are explicitly archived.

## Recommended mitigation before submission

1. Run all main experiments on real OHLCV data only.
2. Freeze symbols, intervals, and evaluation windows.
3. Record model version and prompt configuration for each research run.
4. Add ablation experiments for each validation gate.
