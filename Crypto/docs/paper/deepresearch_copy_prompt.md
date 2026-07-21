# DeepResearch Copy Prompt

Paste the following into the external research session.

```text
You are assisting with a conference-style paper on an AI-assisted crypto strategy validation system.

This is not a live trading paper and not an alpha-generation claim.
The paper's thesis is:

"A reproducible, governance-aware validation framework that treats AI-generated crypto strategies as untrusted proposals that must pass multi-asset, regime-aware, and overfitting-aware approval gates before promotion."

System structure:
- Research -> Engineer -> Evaluate -> Decision -> Publish

Current system capabilities:
- LLM-assisted proposal generation
- mutation-based strategy evolution with lineage
- multi-asset evaluation
- market regime validation
- overfitting checks
- rule-based approval policy
- artifact persistence and registry updates

What I need from you:

1. Related work candidates
- Find 14-20 papers across:
  - LLMs in finance
  - automated strategy generation / evolutionary search
  - backtest overfitting / robust validation
  - trustworthy AI / governance in high-stakes systems

For each paper return:
- full citation
- 1-2 sentence summary
- why it matters to this paper
- whether it is foundational or recent

2. Venue recommendation
- Recommend:
  - one primary venue
  - one fallback workshop/demo venue
  - one later journal extension
- For each:
  - scope fit
  - reviewer bar
  - likely objections

3. Writing-ready related work text
- Write 4 short subsections:
  - LLMs in finance
  - strategy search and mutation
  - robust validation in trading research
  - trustworthy AI and governance

4. Claim discipline
- Provide:
  - 6 safe claims
  - 6 risky claims to avoid

5. Mandatory experiments
- List the minimum additional experiments required for a credible submission.

Constraints:
- Do not position this as a profitable trading system.
- Do not overclaim novelty for walk-forward testing, IS/OOS splits, or parameter sensitivity checks.
- Treat the paper as a systems/integration/governance contribution.
- Prefer papers that are recent and relevant, but include foundational validation literature where needed.

Output format:
- Section A: Venue shortlist
- Section B: Related work table
- Section C: Writing-ready paragraphs
- Section D: Safe vs risky claims
- Section E: Mandatory experiments
```

After you get the result back, it can be merged into:

- `docs/paper/related_work.md`
- `docs/paper/references_template.bib`
- `docs/paper/submission_packet.md`
