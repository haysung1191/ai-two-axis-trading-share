# KR ETF RiskBudget Drop Boundary

## Purpose

- fix what is fully outside the live core rebuild
- prevent research and non-operating artifacts from re-entering the operating path

## Fully Out of Scope

- KR Weekly Score50 RegimeState
- KR Flow-based models
- KR Hybrid RS50 RB50
- KR Quality/Profitability sleeve
- KR Aggressive paper eval
- KR Strategy blend / sleeve compare
- all US strategy and research artifacts
- all news artifacts
- all leaderboard artifacts
- all compare artifacts
- all benchmark expansion artifacts
- all execution-after-the-fact tracking expansions

## Boundary Rule

- an out-of-scope artifact must not be an input to portfolio generation, order sheet generation, pre-trade control, or the live runbook
- out-of-scope artifacts may remain in the repository, but they are not part of the operating core
