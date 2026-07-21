# Results Draft

## 6. Results

This section reports the current repository snapshot as a preliminary empirical audit rather than the final benchmark study. The present artifact archive already supports candidate-level and run-level analysis, but it still mixes runs generated under heterogeneous metadata conditions. In particular, several historical runs appear to have been filtered by execution-model requirements rather than purely by strategy behavior. Accordingly, the results below should be interpreted as an audit of the current system behavior and not as the final evidence package for submission.

### 6.1 Pipeline Behavior

The exported audit snapshot contains 843 candidate-level records and 24 run-level decision records. Across this snapshot, only 13 candidates passed all currently recorded validation filters, corresponding to an overall candidate pass rate of approximately 1.54%. At the run level, only one run reached a `PASS` decision, while the remaining runs ended in `PAUSE` after repeated rejection and activation of the circuit-breaker logic.

This outcome indicates that the platform is highly conservative in its current form. From a systems perspective, this is an important result: the pipeline does not promote candidate strategies easily. Instead, the workflow behaves as a strict filter that prioritizes rejection under uncertainty over permissive approval. For a validation-centric research platform, such behavior is preferable to a system that approves a large number of weak or poorly audited candidates.

### 6.2 New vs. Mutation Proposals

The current snapshot allows a preliminary comparison between newly generated candidates and mutation-derived candidates. The archive contains 423 new candidates and 420 mutation candidates, indicating that the intended 50:50 proposal mix is being realized at scale. New candidates achieved 7 passes with a pass rate of 0.016548, while mutation candidates achieved 6 passes with a pass rate of 0.014286. Mean Sharpe in the exported snapshot was also higher for new candidates (0.274759) than for mutation candidates (0.141902).

At face value, this suggests that mutation is not yet outperforming direct proposal generation. However, this result should not be overinterpreted. The mutation pool is strongly influenced by the current strategy registry, which remains small and dominated by a limited number of approved ancestors. As a result, the mutation mechanism may still be exploring a narrow lineage space. The appropriate interpretation is therefore that mutation support is operational and measurable, but its empirical advantage remains an open question that requires a cleaner benchmark and a richer registry.

### 6.3 Rejection Reasons

The rejection-reason export provides one of the strongest empirical views into current system behavior. The most frequent failed gate is `execution_model`, affecting 802 candidates across 79 runs. This is followed by `backtest_sharpe` (630 candidates), `backtest_cagr` (554 candidates), `backtest_trades` (471 candidates), and `backtest_win_rate` (365 candidates). Overfitting-related failures are also substantial: `overfitting_flags`, `overfitting_pass`, and `overfitting_sensitivity` each occur in 106 candidate records across 37 runs. QA-related failure appears only in a single run.

Two conclusions follow. First, the dominant source of failure is currently not the proposal engine but the validation stack, especially execution-model compliance and baseline performance thresholds. Second, overfitting controls are materially active: they do not dominate all rejections, but they consistently remove a meaningful subset of candidates. This supports the claim that the system is functioning as a governed validation framework rather than a simple ranking engine.

At the same time, the prominence of `execution_model` also reveals a limitation of the current archive: multiple runs were likely executed under inconsistent fee/slippage metadata. For a final conference or journal submission, the empirical section should therefore distinguish between a raw audit view and a clean benchmark subset in which execution settings are fixed across all runs.

### 6.4 Run-Level Outcomes

The run-level decision records show that the most common terminal state is repeated rejection followed by circuit-breaker pause. Most archived runs have `reject_count = 3`, which is consistent with the configured pause behavior. Only one run reached `PASS`, while no run ended in a final `FAIL` without subsequent pause escalation. This pattern reinforces the interpretation that the platform is currently calibrated for cautious promotion.

From a systems perspective, this is a defensible property. In a research setting, a low approval rate is acceptable if it indicates that the platform is effective at filtering unstable candidates. However, from a methodological perspective, this also means that the final paper must report not only approval rate but also the reasons for conservative behavior. Otherwise, a low promotion rate could be mistaken for poor proposal quality rather than a deliberate design choice in the decision policy.

### 6.5 Registry and Lineage

The strategy registry snapshot currently contains a small number of approved strategies. This confirms that lineage tracking and longitudinal bookkeeping are working, but it is not yet sufficient for a strong lineage analysis section. In particular, the current registry does not yet contain enough approved descendants to support robust claims about mutation-driven strategy evolution over time.

Therefore, the registry should be treated as an enabling mechanism rather than a fully developed result in the current draft. Its research value lies in making longitudinal mutation studies possible, not yet in conclusively demonstrating them.

### 6.6 What the Current Results Support

Taken together, the present results support three claims. First, the platform is operational as a full candidate-validation system rather than a collection of isolated scripts. Second, the validation stack is meaningfully active, with explicit rejection causes traceable across candidate and run levels. Third, the system is conservative by construction, promoting only a very small number of candidates under current rules.

These are useful results for a systems paper because they demonstrate that the architecture is not merely aspirational. The repository already produces measurable candidate throughput, measurable gate behavior, measurable lineage metadata, and measurable final decisions.

### 6.7 What Still Needs to Be Strengthened

The current snapshot does not yet support strong claims about comparative financial performance or the superiority of mutation-driven search. To make the paper submission-ready, a clean benchmark subset should be constructed with fixed symbols, fixed timeframe, fixed evaluation windows, fixed fee/slippage settings, fixed deterministic seeds, and repeated runs under controlled conditions. The same export pipeline can then be reused to produce the final tables and figures.

In other words, the present evidence is strong enough to support the paper's systems narrative, but not yet strong enough to support a final empirical claim about strategy quality improvements. The next step is not architectural redesign but controlled experimental consolidation.

### 6.8 Preliminary Clean Benchmark Batch

The repository now includes a dedicated clean-benchmark runner and grouped summary export. A preliminary controlled batch was executed across five groups: `full_system`, `no_mutation`, `no_regime_validation`, `no_multi_asset_gate`, and `no_overfitting_gate`. The batch manifest is stored in `paper_results/clean_benchmark_manifest_prelim.json`, and the grouped summary is stored in `paper_results/clean_benchmark_summary.csv`.

The current preliminary batch should be interpreted as a protocol-validation result rather than as the final comparative experiment. All groups converged to conservative outcomes with zero approvals, and the top-candidate summary metrics remained nearly identical across groups. This indicates that the benchmark harness is working end-to-end, but the present controlled slice is not yet discriminative enough to separate the ablations. In practical terms, the system can now run repeatable grouped evaluations, but the benchmark design still needs stronger stressors.

This is still a useful systems result. It shows that the repository has moved beyond a mixed historical artifact archive and now supports explicit benchmark groups with reproducible metadata. However, the next empirical step must focus on benchmark difficulty rather than more infrastructure. The immediate priorities are seeded bad-strategy families, stronger fee and slippage stress, search-budget stress, and cleaner regime separation so that the ablations produce measurable divergence rather than uniform pause outcomes.

## Suggested Figure References

The following figures should accompany this section:

1. Candidate funnel: proposals -> evaluated -> passed -> approved
2. Rejection reason distribution across candidates
3. New vs. mutation pass-rate comparison
4. Run-level terminal state distribution

## Suggested Safe Summary Sentence

In its current audited state, the platform behaves as a strict governance-oriented strategy filter: it produces large numbers of candidate evaluations, records explicit rejection causes, and promotes only a small minority of candidates, indicating that the validation stack is functioning conservatively as designed.
