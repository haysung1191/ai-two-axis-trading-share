# Camera-Ready Checklist

This checklist assumes the current repository is being prepared for a serious submission round.

## Manuscript

- [ ] Final title selected from `title_candidates.md`
- [ ] Abstract rewritten to match target venue length limit
- [ ] Introduction merged into final manuscript
- [ ] Method section aligned with actual implementation state
- [ ] Results section updated with clean benchmark numbers
- [ ] Discussion section aligned with final experimental evidence
- [ ] Limitations section kept conservative and explicit
- [ ] Conclusion shortened to venue-appropriate length

## Related Work

- [ ] `related_work.md` replaced with real citations
- [ ] Introduction references synchronized with bibliography
- [ ] Distinction from prior automated-strategy and LLM-finance work made explicit

## Empirical Package

- [ ] Clean benchmark protocol executed
- [ ] No synthetic fallback used in final reported runs
- [ ] Fixed symbols, windows, fee, and slippage documented
- [ ] All benchmark runs exported via `scripts/export_paper_results.py`
- [ ] Baseline and ablation tables finalized

## Figures

- [ ] Figure 1 system overview
- [ ] Figure 2 candidate funnel
- [ ] Figure 3 rejection reason distribution
- [ ] Figure 4 new vs mutation comparison
- [ ] Figure 5 cross-asset stability
- [ ] Figure 6 regime stability
- [ ] Optional lineage and category figures if page budget allows

## Artifact Hygiene

- [ ] No sensitive deployment details exposed
- [ ] No private keys, secrets, or production endpoints in manuscript or appendix
- [ ] No confidential strategy parameters exposed beyond what is intended
- [ ] All public artifact examples sanitized if needed

## Repo Hygiene

- [ ] Root `README.md` repaired or replaced if external reviewers will see it
- [ ] Public-facing docs are English-clean and encoding-safe
- [ ] Reproducibility steps are documented
- [ ] Final paper scripts run successfully from a clean environment

## Submission Packaging

- [ ] Venue template applied
- [ ] Author list and affiliations finalized
- [ ] Anonymous version prepared if required
- [ ] Appendix prepared for implementation detail and extra tables
- [ ] PDF passes formatting and page-limit checks

## Final sanity questions

Before submission, confirm:

1. Is the paper claiming a governed validation framework rather than secret alpha?
2. Are all strong claims backed by the clean benchmark subset rather than the raw archive?
3. Are negative results and limitations stated clearly?
4. Could a reviewer reproduce the core pipeline logic from the manuscript and repo?
