# Citation Tracker

This file exists to turn placeholder-heavy paper text into a citation-grounded draft quickly.

## Placeholder groups

### LLM-FIN

- `LLM-FIN-1`
- `LLM-FIN-2`
- `LLM-FIN-3`
- `LLM-FIN-4`
- `LLM-FIN-5`

Use for:
- LLMs in finance
- generative AI in financial analysis
- LLM-assisted hypothesis or strategy generation

### AUTO-STRAT

- `AUTO-STRAT-1`
- `AUTO-STRAT-2`
- `AUTO-STRAT-3`

Use for:
- evolutionary trading strategy search
- symbolic strategy generation
- genetic programming for quantitative finance

### VALID

- `VALID-1`
- `VALID-2`
- `VALID-3`
- `VALID-4`

Use for:
- backtest overfitting
- walk-forward evaluation
- parameter sensitivity
- cross-regime robustness

### TAI

- `TAI-1`
- `TAI-2`
- `TAI-3`

Use for:
- trustworthy AI
- governance and auditability
- controlled promotion in high-stakes systems

## Replacement rule

When external literature results arrive:

1. map each placeholder to a real paper
2. update `related_work.md`
3. update `final_manuscript_compiled.md` by rerunning:

```bash
python scripts/build_paper_package.py
```

## Minimum citation target

- 4-5 references for LLM/finance
- 3-4 references for automated strategy search
- 4-6 references for validation/overfitting
- 3-4 references for governance/trustworthy AI

Anything materially below this will make the related work section look thin.
