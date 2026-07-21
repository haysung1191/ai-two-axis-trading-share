# Final Manuscript

## Working Title

Governance-Aware AI-Silo for Cryptocurrency Strategy Validation

## Compilation Notes

- This file is auto-assembled from `docs/paper/*.md` fragments.
- It is intended as the single-source review draft before venue formatting.
- Citation placeholders still need to be replaced with real references.

## Abstract

We present a personal AI-silo for cryptocurrency strategy research that treats strategy creation as a governed validation problem rather than a direct trading problem. The system combines LLM-assisted proposal generation, mutation-based strategy evolution, deterministic strategy materialization, multi-asset backtesting, market-regime validation, overfitting checks, rule-based governance, and artifact-driven decision logging within a reproducible workflow. Candidate strategies are evaluated across multiple symbols and regimes, filtered through explicit approval gates, ranked by risk-adjusted metrics, and only approved strategies are persisted to a registry with lineage metadata. The platform is implemented as a modular Python system with typed contracts, workflow orchestration, persistent artifacts, and test coverage for key control points. We argue that the main contribution is not a new predictive model, but a reproducible research architecture that reduces unsafe strategy promotion by combining generation, validation, and governance in one system. We outline an evaluation protocol based on ablations over mutation, multi-asset validation, regime validation, and overfitting controls to measure throughput, rejection causes, and candidate robustness.

## Contribution Claims

1. A governance-aware AI research pipeline for crypto strategy validation with explicit approval artifacts and lineage tracking.
2. A unified validation stack that combines multi-asset testing, regime testing, and overfitting controls inside one repeatable scorecard.
3. A practical experiment framework for comparing proposal generation strategies, mutation policies, and validation gates under deterministic execution.

## What not to claim

- Do not claim superior live profitability.
- Do not claim real-money deployment safety.
- Do not claim state-of-the-art forecasting accuracy unless benchmarked directly.

## Introduction

Large language models and agentic systems make it increasingly easy to generate large numbers of trading ideas. In practice, however, strategy generation is the easy part. The hard part is deciding which candidates should be trusted, which should be rejected, and which should be promoted for further experimentation. In quantitative trading research, this problem is amplified by overfitting, regime sensitivity, unstable cross-asset behavior, and poor auditability of iterative experimentation.

Most practical research stacks are built as patchworks of notebooks, backtest scripts, and manually curated rules. Those workflows may be fast for individual experimentation, but they are weak in reproducibility and governance. A candidate strategy that appears promising in a single-symbol or single-regime backtest can still fail under broader validation. This creates a gap between rapid idea generation and disciplined strategy promotion.

This work presents a personal AI-silo for cryptocurrency strategy validation. The system is intentionally framed as a validation platform rather than a live trading engine. Candidate strategies are produced by a ResearchAgent that supports both new proposals and mutation-based evolution from historically successful strategies. Generated candidates are materialized into temporary strategy modules and evaluated through a deterministic pipeline that includes multi-asset testing, market regime validation, overfitting checks, QA placeholders, rule-based risk screening, and final decision gating. Only candidates that pass explicit approval conditions are persisted as approved artifacts and recorded in a strategy registry with lineage metadata.

The main contribution of this work is not a new predictive model or a claim of superior trading profitability. Instead, the contribution is a reproducible architecture for strategy validation that combines proposal generation, robustness evaluation, governance, and artifact persistence in one workflow. The repository implements typed scorecards, deterministic evaluation, persistent run artifacts, approval records, lineage-aware strategy evolution, and test-backed control points. This makes the system suitable as a research platform for studying how validation constraints affect candidate throughput and promotion quality.

The paper argues that AI-assisted financial research should be treated as a governed decision process rather than a pure search process. To support this claim, the system evaluates candidates across multiple symbols, multiple market regimes, and multiple overfitting criteria before promotion. The resulting workflow enables controlled experiments on mutation policies, diversity enforcement, approval gates, and rejection causes. This framing is especially relevant in crypto markets, where non-stationarity and regime shifts make naive candidate promotion particularly risky.

The remainder of the paper is organized as follows. Section 2 describes the architecture of the AI-silo and the roles of proposal generation, evaluation, decision policy, and publication artifacts. Section 3 explains the validation methodology, including multi-asset evaluation, regime testing, and overfitting-aware gating. Section 4 describes implementation details and reproducibility mechanisms. Section 5 presents the experimental protocol, baselines, and ablations required to assess the framework. Section 6 discusses strengths, limitations, and future directions toward broader benchmarking and controlled deployment.

## Related Work

This paper is positioned as a systems and validation contribution rather than a profitability claim. The relevant prior work therefore spans four intersecting areas: large language models in finance, automated strategy search and evolution, robust validation and backtest overfitting, and trustworthy AI or model-governance practices in high-stakes domains. The paper's contribution is not a new predictive model. It is an architecture that treats AI-generated strategies as untrusted proposals and subjects them to typed, reproducible approval gates before promotion.

### 4.1 LLMs and Generative AI in Finance

Recent work has expanded the use of large language models in finance from text understanding and report analysis to broader research assistance and agentic financial workflows. BloombergGPT showed that a finance-specialized language model can achieve strong domain performance while making clear that data curation and evaluation protocol are central to meaningful financial use [@wu2023bloomberggpt]. FinGPT extended this direction through an open-source, data-centric pipeline for financial LLM construction and adaptation, lowering the barrier to financial-domain experimentation while also reinforcing the need for reproducible downstream controls [@yang2023fingpt]. Surveys of LLMs in finance and finance-specific agent systems now emphasize not only capability but also deployment constraints, including reliability, prompt sensitivity, reproducibility, and domain-specific risk [@li2023llmfinancesurvey; @dong2025financeagents].

These studies justify the use of LLMs as research accelerators, but they do not remove the need for strong validation. That is the point of departure for this paper. Instead of treating an LLM-generated strategy as a plausible model to be trusted on its own merits, the current system treats it as an untrusted proposal that must survive deterministic evaluation, multi-asset screening, regime-aware checks, and explicit approval policy. In that sense, the system is closer to a governed research-control architecture than to a pure LLM forecasting paper.

### 4.2 Automated Strategy Search, Mutation, and Evolution

Automated strategy generation has a long history through genetic programming, symbolic search, and evolutionary optimization. Earlier work in foreign exchange and equity markets demonstrated that trading rules can be generated algorithmically rather than manually authored, but also highlighted how search-based rule discovery can overfit data or exploit fragile structures [@neely1997technical; @potvin2004generating]. Later work on grammatical evolution and ensemble-based trading systems reinforced the need to account for structural change, trading frictions, and overtrading when algorithmically generated strategies are evaluated [@martin2019grammatical].

More recent work has begun to combine LLM-based proposal generation with automated strategy discovery in quantitative investment settings [@kou2025automate]. That line of work is close to the front end of the current repository, particularly in its use of LLMs to propose candidate rules. However, the present paper makes a narrower and more defensible claim. Mutation is not introduced as a novel search technique, and strategy generation is not framed as the main contribution. The distinctive element is the integration of mutation-based evolution, lineage-aware registry tracking, typed candidate scorecards, explicit rejection reasons, and rule-based promotion into one governed research workflow.

### 4.3 Robust Validation and Backtest Overfitting

The central statistical risk in strategy research is not just weak performance but false discovery. White's Reality Check formalized the data-snooping problem that arises when many candidate strategies are explored on the same dataset and the apparent winner is treated as meaningful [@white2000reality]. Hansen's Superior Predictive Ability test and Romano and Wolf's work on stepwise multiple testing further sharpened the treatment of multiple comparisons, providing more disciplined ways to evaluate large candidate sets against benchmarks [@hansen2005spa; @romano2005stepwise]. Bailey et al. later made the problem operational for strategy research through the probability of backtest overfitting, giving practitioners a direct way to quantify the likelihood that a selected strategy is a backtest artifact rather than a robust signal [@bailey2017pbo]. Lo's analysis of Sharpe ratio statistics similarly made clear that widely used performance measures can be misinterpreted if serial dependence and estimation error are ignored [@lo2002sharpe].

The present paper is directly aligned with this literature. The system is built on the premise that large-scale proposal generation and mutation intensify multiple-testing and overfitting risks. Accordingly, it combines in-sample and out-of-sample splits, walk-forward evaluation, parameter sensitivity checks, multi-asset consistency checks, regime-aware robustness checks, and explicit approval gates. None of these individual controls is claimed as novel. The contribution is that they are operationalized as first-class outputs of a unified evaluation stack and fed directly into a policy-based decision layer.

### 4.4 Trustworthy AI, Governance, and Auditability

Trustworthy AI work has emphasized that high-stakes systems require more than predictive quality: they require documentation, auditability, risk management, and explicit controls on deployment decisions. In finance, this concern is longstanding. The Federal Reserve's SR 11-7 guidance on model risk management formalized the need for validation, governance, and supervisory control around model use [@frb2011sr117]. More broadly, the NIST AI Risk Management Framework reframed AI deployment as a lifecycle risk-management problem rather than a pure model-performance problem [@nist2023airmf]. Parallel work on model cards, datasheets for datasets, and internal algorithmic auditing highlighted the importance of structured documentation, known limitations, and evidence trails across development and deployment pipelines [@mitchell2019modelcards; @gebru2021datasheets; @raji2020auditing].

Recent finance-specific discussions of responsible LLM adoption reinforce the same point. Reports and workshops from financial regulators and research institutions emphasize robustness, accountability, reproducibility, and controlled adoption paths for LLMs in finance [@esma2025responsible]. General-purpose system cards for frontier LLMs also document the kinds of limitations and failure modes that justify downstream control layers even when the model is capable [@openai2023gpt4card]. This paper fits squarely within that governance tradition. The system contribution is to make approval logic, failure causes, lineage metadata, and publication artifacts explicit and persistent, so that strategy promotion becomes auditable rather than ad hoc.

### 4.5 Positioning of This Paper

The clearest positioning statement is therefore the following. Prior work has studied LLMs in finance, automated strategy generation, robust trading validation, and trustworthy AI governance, but these strands are often handled separately. This paper focuses on the architecture that connects them. The repository contributes a reproducible validation framework that combines LLM-assisted proposal generation, mutation-based evolution, multi-asset evaluation, regime-aware testing, overfitting controls, policy-based approval, and lineage-preserving publication artifacts in one workflow. The appropriate claim is architectural and methodological rather than predictive.

## Method

The system is organized around a validation-centric workflow:

`Research -> Engineer -> Evaluate -> Decision -> Publish`

This design intentionally separates candidate generation from candidate promotion. A strategy proposal is not considered valuable unless it survives the evaluation and decision stages.

## Research

The ResearchAgent generates a fixed number of strategy proposals per run. In the current implementation, the default is ten proposals. The generation policy enforces a balanced mix between newly generated strategies and mutation-derived strategies from the historical strategy registry. Diversity is also enforced across five categories:

- mean_reversion
- momentum
- volatility_breakout
- trend_following
- range_trading

Mutation proposals preserve lineage through `parent_strategy`, allowing the system to model iterative strategy evolution rather than isolated one-shot search.

## Engineering

Each proposal is materialized into a temporary strategy module. This step converts structured proposals into executable strategy logic that conforms to a common strategy protocol. Candidate-level artifacts are written under the run directory to preserve reproducibility.

## Evaluation

Evaluation is performed by a unified `CandidateEvaluator`. For each candidate, the evaluator executes:

1. Single-asset and multi-asset backtesting
2. Market regime validation
3. Overfitting analysis
4. QA placeholder checks
5. Rule-based risk validation

The output is a typed `EvaluationScorecard` that records strategy identity, metrics, gate outcomes, rule violations, and deterministic metadata.

### Multi-asset validation

Candidates are evaluated across multiple symbols, currently including BTCUSDT, ETHUSDT, and SOLUSDT. Aggregate metrics include mean Sharpe, Sharpe dispersion across assets, mean drawdown, and worst drawdown.

### Regime validation

Historical data is partitioned into four regimes:

- trend
- range
- high_volatility
- low_volatility

Regime-specific Sharpe and drawdown values are computed, along with the standard deviation of Sharpe across regimes.

### Overfitting controls

The system evaluates in-sample and out-of-sample metrics, walk-forward windows, and parameter sensitivity. These outputs are converted into explicit flags and gate failures. The goal is to reject candidates that succeed only under narrow parameter or sample conditions.

## Decision

The `DecisionPolicy` ranks validated candidates and applies one source of truth for promotion logic. Candidates may be rejected due to:

- overfitting flags
- low stability score
- excessive cross-asset Sharpe dispersion
- excessive regime Sharpe dispersion
- risk rule violations
- QA failure

Only candidates that pass the policy are eligible for approval.

## Publish

The publish stage persists decision artifacts, approval artifacts, run summaries, and leaderboard outputs. If a candidate is approved, the system also updates a persistent strategy registry containing:

- strategy identifier
- first seen run
- latest run
- best metrics
- lineage metadata
- historical run list

This allows future research runs to generate mutation proposals from historically successful candidates.

## Experimental Setup

Does a governance-aware AI strategy validation pipeline improve the robustness of promoted strategy candidates compared with simpler proposal-and-backtest workflows?

## Main hypotheses

### H1
Mutation plus diversity increases the number of viable candidates without increasing unsafe approvals.

### H2
Multi-asset and regime-aware validation reduces approval of brittle strategies.

### H3
Overfitting and governance gates reduce false positives at the cost of lower pass rate.

## Baselines

1. Proposal + single-symbol backtest only
2. Proposal + multi-asset backtest only
3. Proposal + multi-asset + regime validation
4. Full system without mutation
5. Full system

## Ablations

1. Remove mutation
2. Remove diversity enforcement
3. Remove multi-asset validation
4. Remove regime validation
5. Remove overfitting gate
6. Remove decision policy gates

## Metrics

### Pipeline metrics
- proposals per run
- accepted candidates per run
- rejection reason distribution
- evaluation latency per candidate
- cache hit rate

### Candidate quality metrics
- sharpe mean
- sharpe std across assets
- drawdown worst
- sharpe regime std
- stability score
- overfitting flags count

### Promotion quality metrics
- approval rate
- approval robustness score
- out-of-sample degradation
- false-promotion rate
- rejection efficacy on seeded bad strategies
- search-budget sensitivity

### Governance and systems metrics
- lineage retrieval latency
- artifact coverage rate
- registry update latency
- end-to-end throughput
- bottleneck share by stage

## Tables to produce

### Table 1
System components and responsibilities

### Table 2
Baseline and ablation comparison

Columns:
- setup
- pass rate
- sharpe mean
- cross-asset sharpe std
- regime sharpe std
- overfitting rejection rate

### Table 3
Mutation vs non-mutation proposal quality

Columns:
- source type
- candidates
- pass rate
- median sharpe
- median drawdown

## Figures to produce

1. Full pipeline diagram
2. Candidate funnel:
   proposals -> engineered -> evaluated -> passed -> approved
3. Mutation lineage graph
4. Cross-asset stability plot
5. Regime robustness plot
6. Search-budget vs false-promotion pressure plot
7. End-to-end stage latency breakdown
8. Audit retrieval latency chart

## Minimal publishable empirical package

To make the paper credible, collect at least:
- fixed symbol universe
- fixed timeframe
- fixed historical windows
- at least 30-50 independent runs
- deterministic seeds
- full artifact retention for audit

## Mandatory stress experiments

1. Rejection efficacy:
   - seed intentionally overfit or leaking strategies and verify rejection
2. Search-budget stress:
   - increase proposal/mutation volume and measure selection-bias pressure
3. Cost-friction stress:
   - repeat evaluation under multiple fee/slippage assumptions
4. Cross-asset degeneration:
   - optimize on one asset and test automatic rejection on others
5. Lineage and audit retrieval:
   - measure how quickly the system can reconstruct ancestry and approval evidence
6. Throughput profiling:
   - measure stage-level latency and identify dominant bottlenecks

## Results

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

## Discussion

The most important outcome of the current repository is not a claim about superior trading returns. The stronger contribution is architectural: the system demonstrates how AI-assisted strategy research can be organized as a governed validation process rather than an unconstrained search process. This distinction matters because large language models and mutation-based proposal mechanisms make it easy to generate plausible trading ideas, but they do not by themselves provide a reliable basis for promotion. In this setting, the value of the platform lies in its ability to reject aggressively, preserve artifacts, and make approval decisions auditable.

The current implementation already supports this framing. Proposal generation is separated from evaluation. Evaluation is separated from decision. Decision is separated from publication and registry updates. Typed scorecards and explicit gate failures make candidate outcomes inspectable. From a systems viewpoint, this is a meaningful contribution because it turns a historically ad hoc research workflow into a repeatable pipeline.

### 7.2 Why the Conservative Approval Profile Is Useful

The low approval rate observed in the current snapshot should not automatically be interpreted as a weakness. In a validation-focused research platform, conservative behavior is often desirable. A system that approves too many candidates is likely to be under-constrained or poorly calibrated. By contrast, a system that rejects frequently but records precise reasons creates a clearer experimental environment for improving proposal quality and refining gates.

That said, conservatism must be interpreted carefully. If the rejection profile is dominated by infrastructure or metadata issues rather than model behavior, then low approval rates may reflect protocol noise rather than strong validation. The current prominence of `execution_model` failures suggests that part of the observed conservatism is real governance pressure, but part is also an artifact of inconsistent historical run settings. This reinforces the need for a clean benchmark subset in the final empirical study.

### 7.3 Mutation as an Open Research Question

Mutation is one of the most interesting ideas in the repository, but it is not yet a solved empirical advantage. The lineage mechanism and mutation proposal generation are implemented, and the system can compare mutation-derived candidates against newly generated ones. However, the current registry is still small, and mutation quality is constrained by the limited diversity of approved ancestors. As a result, the present system is better viewed as supporting mutation research than proving mutation superiority.

This is still a useful contribution. In many strategy research stacks, iterative evolution is implicit and poorly tracked. Here, lineage is explicit through `source_type` and `parent_strategy`, and promotion decisions can be connected back to historical ancestry. That makes future mutation studies much easier to run rigorously.

### 7.4 Relationship Between Robustness and Throughput

The repository also highlights a practical tension between robustness and research throughput. Every added validation layer improves candidate scrutiny but also reduces approval rate and increases evaluation cost. Multi-asset testing, regime testing, and overfitting checks are all defensible in isolation, yet their interaction may produce a highly selective funnel. For a paper submission, this tradeoff should be treated as a central discussion point rather than an implementation detail.

One useful way to frame the system is not as a search engine for alpha, but as a configurable filter for candidate robustness. Under that framing, throughput is not just the number of proposals generated; it is the number of candidates that can be evaluated, rejected, and explained in a reproducible way. This makes the system relevant to AI governance and trustworthy finance discussions, not only to trading-specific literature.

### 7.5 What Makes the Paper Credible

The strongest path to credibility is to keep the paper narrowly scoped. The paper should argue that the system provides a reproducible and governance-aware architecture for validating AI-generated strategy candidates. It should not overextend into claims about production deployment safety or superior market performance. If the framing remains disciplined, the current repository supports a coherent systems narrative:

- LLM-assisted proposal generation
- mutation-aware strategy evolution
- diversity-constrained candidate generation
- multi-asset and regime-aware validation
- overfitting-aware decision gates
- artifact persistence and lineage tracking

That is already enough for a respectable applied AI systems paper or finance-AI systems submission.

### 7.6 What Still Needs to Be Done Before Submission

The remaining work is empirical consolidation, not conceptual reinvention. The architecture is already sufficiently concrete. What is missing is a clean, fixed, publication-grade benchmark protocol with repeated runs, baseline comparisons, and ablations. Once those are collected, the paper can move from “promising systems draft” to “credible submission.”

## Limitations

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

## Conclusion

This work presented a governance-aware AI-silo for cryptocurrency strategy validation. Rather than treating LLMs and agentic systems as direct trading engines, the platform treats them as components in a controlled research workflow. Candidate strategies are generated through both new proposals and mutation-based evolution, materialized into executable strategy modules, evaluated across multiple assets and market regimes, filtered through overfitting and rule-based gates, and only then considered for approval and registry promotion.

The central contribution is therefore architectural and methodological. The repository shows how AI-assisted strategy research can be made reproducible, auditable, and explicitly governed through typed scorecards, persistent artifacts, deterministic evaluation, and policy-based promotion logic. The current empirical snapshot already demonstrates that the platform operates as a conservative validation system with traceable rejection causes and explicit approval controls.

At the same time, the present work does not claim to solve the broader problem of profitable live trading. Its stronger claim is that strategy validation itself can be turned into a first-class AI systems problem. By making proposal generation, robustness testing, lineage tracking, and approval logic part of one integrated framework, the platform provides a foundation for more disciplined experimentation in financial AI.

Future work should focus on benchmark consolidation rather than architectural expansion. The most valuable next steps are to fix data windows and execution assumptions, collect repeated controlled runs, expand the strategy registry, and run ablation studies over mutation, diversity, multi-asset validation, regime validation, and overfitting gates. With those additions, the system can support a stronger empirical analysis of how governance-oriented validation affects candidate quality and promotion reliability.

## Figures and Tables

Primary figure and table planning artifacts:

- `docs/paper/figures_plan.md`
- `docs/paper/figure_captions.md`
- `docs/paper/results_tables.md`
- `paper_figures/figure_manifest.json`
- `paper_results/figure_summary.json`

## Submission Readiness

Final pre-submission checks live in:

- `docs/paper/camera_ready_checklist.md`
- `docs/paper/submission_checklist.md`
- `docs/paper/clean_benchmark_protocol.md`
