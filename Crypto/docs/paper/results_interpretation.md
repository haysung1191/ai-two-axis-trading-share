# Results Interpretation Guide

## What the current snapshot supports

The current exported CSVs support these claims:

- The pipeline is active and producing structured candidate-level and run-level outputs.
- The governance stack is conservative and rejects most candidates.
- New and mutation proposals can be compared quantitatively.
- Rejection causes can be audited at scale.
- Registry and lineage artifacts exist.

## What the current snapshot does not yet support

- A publishable claim that mutation improves candidate quality.
- A publishable claim that the full system improves financial performance.
- A publishable claim that approved candidates are consistently robust across broad market periods.

## Why the current snapshot is not final

The raw archive mixes:
- old and new runs
- different metadata quality
- runs that predate cleaner policy settings
- runs affected by the `execution_model` gate due to missing fee/slippage inputs

This means the current CSVs are best used for:
- internal audit
- preliminary narrative
- figure prototypes

They are not yet ideal as the final experimental dataset.

## What to do next

Create a clean benchmark subset with:
- fixed symbols
- fixed timeframe
- fixed period
- fixed fee/slippage settings
- fixed proposal count
- fixed deterministic seed
- enough repeated runs for comparison

Then rerun:

```powershell
python scripts/export_paper_results.py --artifacts-root artifacts --output-dir paper_results --registry-path strategy_registry.json
```

## Safe paper wording for now

Use wording like:

- "In a preliminary audit snapshot of archived runs, the platform showed a highly conservative approval profile."
- "The dominant rejection categories were execution-model compliance and baseline performance thresholds."
- "These results motivated the construction of a cleaner benchmark subset for the final empirical section."

Avoid wording like:

- "The system significantly outperforms alternatives."
- "Mutation improves profitability."
- "The platform discovers alpha reliably."
