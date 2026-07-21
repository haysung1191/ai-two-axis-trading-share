# Submission Checklist

## Must finish before writing Related Work

- [ ] Fix or replace the root `README.md` if it will be shared externally.
- [ ] Freeze the exact paper title direction.
- [ ] Freeze the venue target.
- [ ] Freeze the experimental scope:
  - symbols
  - timeframe
  - historical window
  - proposal count
  - evaluation workers

## Must finish before submission

- [ ] Collect 30-50 reproducible runs.
- [ ] Export a final benchmark table for baselines and ablations.
- [ ] Produce at least 4 figures:
  - system diagram
  - candidate funnel
  - cross-asset robustness
  - regime robustness
- [ ] Write related work with real citations.
- [ ] Add a threats-to-validity section grounded in actual experiments.
- [ ] Confirm no confidential deployment details are exposed.

## Code-side items

- [ ] Add a script that exports run-level statistics for the paper.
- [ ] Add a script that aggregates rejection reasons across runs.
- [ ] Add a script that builds paper-ready tables from artifacts.
- [ ] Verify real-data evaluation path is used for final experiments.

## Paper-side items

- [ ] Introduction
- [ ] Method
- [ ] Related Work
- [ ] Experimental Setup
- [ ] Results
- [ ] Discussion
- [ ] Conclusion

## Recommended next coding task

Implemented:
- `scripts/export_paper_results.py`

Usage:

```powershell
python scripts/export_paper_results.py --artifacts-root artifacts --output-dir paper_results --registry-path strategy_registry.json
```

Current outputs:
- `paper_results/candidate_metrics.csv`
- `paper_results/decision_outcomes.csv`
- `paper_results/rejection_reasons.csv`
- `paper_results/lineage_stats.csv`
- `paper_results/source_type_stats.csv`
