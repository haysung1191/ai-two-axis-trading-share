# DeepResearch Handoff Packet

This document is the external handoff packet for a separate research session.

## Objective

Convert the current paper kit into a citeable conference-style manuscript with grounded related work, venue-fit justification, and a sharper experimental positioning.

## Repository Positioning

The project is not a live trading paper and not an alpha-discovery claim. The paper position is:

- governance-aware AI-assisted strategy validation
- reproducible candidate evaluation
- mutation-aware strategy lineage
- multi-asset, regime-aware, and overfitting-aware approval gating

Core system framing:

`Research -> Engineer -> Evaluate -> Decision -> Publish`

## What the external research pass should produce

1. Related work map with 12-20 papers:
   - LLMs in finance
   - automated strategy generation/evolution
   - overfitting-aware trading validation
   - trustworthy AI / governance in finance
2. Venue recommendation with reasons:
   - ICAIF-like systems/finance positioning
   - workshop fallback options
   - journal extension options
3. Reviewer-risk analysis:
   - likely objections
   - how to narrow claims
   - what experiments are mandatory
4. Citation-ready paragraph suggestions:
   - 2-4 paragraphs for related work
   - 1 positioning paragraph for introduction

## Constraints for the research pass

- Do not frame this as a profitable live-trading claim.
- Do not overclaim novelty for standard validation ideas such as walk-forward or IS/OOS splits.
- Treat the contribution as systems integration, governance, reproducibility, and validation architecture.
- Prefer recent finance/AI systems literature, but include foundational validation references where necessary.

## Local source documents to align with

- `docs/paper/manuscript_draft.md`
- `docs/paper/results_section.md`
- `docs/paper/related_work.md`
- `docs/paper/venue_strategy.md`
- `docs/paper/experiment_plan.md`
- `docs/paper/clean_benchmark_protocol.md`

## Required output format from external research

Return a structured package with:

### A. Venue shortlist

For each venue:
- scope fit
- estimated review bar
- risks
- recommendation level

### B. Related work table

Columns:
- citation
- main contribution
- relevance to this paper
- how this paper differs

### C. Writing-ready text

- one introduction positioning paragraph
- one related-work subsection on LLMs in finance
- one related-work subsection on validation/governance

### D. Claim discipline

- list of safe claims
- list of risky claims to avoid

## Suggested prompt seed

Use the prompts already prepared in:

- `docs/paper/deepresearch_prompts.md`

This handoff supersedes ad hoc prompts because it anchors the paper position more tightly.
