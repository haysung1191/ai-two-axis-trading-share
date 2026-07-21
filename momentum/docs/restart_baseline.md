# Momentum Restart Baseline

This note defines the default restart scope when the mixed-market momentum research lane is resumed from a cold start.

Next document:

- use [first_backtest_runbook.md](C:\AI\momentum\docs\first_backtest_runbook.md) for the actual first-pass execution order after the scope is fixed.

## Default Data Window

- Primary operating window: latest `10-15 years`.
- Recommended default for most work in this repo: `12 years`.
- Minimum acceptable operating window: `8 years`, and even that should be treated as compressed evidence.
- Do not promote a branch from only `3-5 years` of history; use that only as a recency diagnostic.

## Required Validation Cuts

Inside the main window, keep separate readouts for:

- latest `3 years`
- latest `5 years`
- full operating window
- known stress / weak-period diagnostics

The full window should decide whether a branch is viable. The shorter windows should decide whether the branch is currently aligned or deteriorating.

## Market Scope

Default market scope should remain cross-market:

- `US` stocks and ETFs
- `KR` stocks and ETFs

Do not collapse the repo to a single-country universe as the default operating truth.

## Default Role Split

Use this role split when restarting:

1. `US` market as the primary design and operating reference
2. `KR` market as the required cross-check and practical secondary market

That means:

- the main branch can still be led by US behavior,
- but promotion should not ignore KR failure,
- and a rule that only works in one market should be treated as market-specific unless proven otherwise.

## Scope Rules

- Do not promote from `US only` evidence when the repo's purpose is still mixed-market momentum.
- Do not promote from `KR only` evidence either.
- Do not mix the markets blindly in analysis summaries; preserve the ability to see whether strength comes from US, KR, or both.

## Promotion Standard

A candidate is interesting when:

- it clears the full `10-15 year` operating window,
- it does not break the baseline drawdown standard,
- and it remains directionally acceptable across both `US` and `KR` sleeves.

If one market carries the whole result while the other market persistently degrades drawdown or fragility, treat that as a portability problem.

## Practical Restart Recommendation

If the repo is resumed from scratch, start with:

1. full-window mixed-market baseline replay over the latest `12 years`
2. separate `US` and `KR` attribution / contribution readout
3. latest `3 year` and `5 year` recency diagnostics
4. only then decide whether the next step is offensive refinement, operating defense, or market-scope adjustment
