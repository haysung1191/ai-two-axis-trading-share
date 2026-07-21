# DeepResearch Request Bundle

Use this file when you want to send a single, concrete request to another research session and get back output that can be merged quickly.

## Send this request

You are helping prepare a conference-style paper on an AI-assisted crypto strategy validation system.

The paper is not about live profitability. It is about a governed validation architecture for AI-generated strategy proposals.

System framing:

- Research generates strategy proposals
- Engineer materializes them into executable strategy modules
- Evaluate computes typed scorecards with:
  - multi-asset metrics
  - regime metrics
  - overfitting flags
  - gate outcomes
- Decision applies approval policy
- Publish writes approval artifacts and updates a strategy registry

The contribution claim is:

"A reproducible, governance-aware validation framework that treats AI-generated crypto strategies as untrusted proposals that must pass multi-asset, regime-aware, and overfitting-aware approval gates before promotion."

Return the following:

### 1. Related work candidates

Find 14-20 papers divided into:
- LLMs in finance
- automated strategy generation/evolution
- robust validation / backtest overfitting
- trustworthy AI / governance in high-stakes systems

For each paper provide:
- citation
- 1-2 sentence summary
- why it matters here
- whether it is foundational or recent

### 2. Writing-ready related work text

Provide 4 short subsections:
- LLMs in finance
- strategy search and mutation
- robust validation in trading research
- trustworthy AI / governance

### 3. Venue recommendation

Rank:
- primary target
- fallback workshop/demo target
- later journal extension

For each:
- scope fit
- why this paper fits
- likely reviewer concerns

### 4. Claim-discipline section

Provide:
- 6 safe claims
- 6 risky claims to avoid

### 5. Mandatory experiment advice

List the minimum additional experiments needed for a credible submission.

## Constraints

- Do not recommend positioning this as a profitable trading system.
- Do not overclaim novelty for walk-forward testing, IS/OOS splits, or standard overfitting controls.
- Treat the contribution as systems integration, governance, reproducibility, and validation architecture.
- Favor papers from top finance/AI systems venues or strong adjacent literature.

## Local files this should align with

- `docs/paper/final_manuscript_compiled.md`
- `docs/paper/related_work.md`
- `docs/paper/submission_packet.md`
- `docs/paper/clean_benchmark_protocol.md`
- `docs/paper/venue_strategy.md`
