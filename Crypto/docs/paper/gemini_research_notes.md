# Gemini Research Notes

This file captures useful planning signals from an external Gemini session without treating every cited item as verified source material.

## Use policy

- Treat this document as research planning input, not as a citation source.
- Do not move references from here into the paper bibliography unless separately verified.
- Safe to reuse:
  - venue framing ideas
  - reviewer objection patterns
  - experiment suggestions
- Not safe to reuse blindly:
  - exact venue formatting rules
  - exact paper metadata
  - any citation not independently checked

## Useful takeaways

### Venue positioning

- Strongest fit remains an AI-in-finance systems framing rather than an alpha-generation framing.
- The paper should continue to emphasize:
  - validation
  - governance
  - reproducibility
  - approval controls

### Reviewer objections to expect

1. "This is just pipeline glue."
2. "Where is the finance-specific empirical contribution?"
3. "Backtest results do not imply live trading validity."
4. "Mutation/evolution is not novel."

### Recommended response strategy

- Keep the contribution framed as:
  - governed promotion control
  - typed and reproducible evaluation
  - artifact persistence and auditability
  - rejection of brittle or overfit strategies
- Avoid turning the paper into a profitability claim.

## Experiment ideas worth retaining

1. Rejection-efficacy experiments:
   - show that the framework rejects intentionally overfit strategies
2. Search-budget stress:
   - increase proposal count and measure false-promotion pressure
3. Cost-friction stress:
   - repeat approval under multiple fee/slippage settings
4. Regime sensitivity:
   - show that regime gates catch strategies optimized for one period only
5. Cross-asset degeneration:
   - show that single-asset over-specialization is rejected
6. Lineage retrieval / auditability:
   - measure cost and latency of recovering strategy ancestry and approval evidence
7. End-to-end throughput:
   - identify whether LLM generation or evaluation is the main bottleneck

## Writing signals worth keeping

- The strongest thesis is still:
  - AI-generated strategies are untrusted proposals
  - promotion requires deterministic validation and policy enforcement
- The strongest systems message is:
  - optimize falsification and rejection quality, not only candidate generation
