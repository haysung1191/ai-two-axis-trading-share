# Split Models Dead Family Ledger

## Purpose

- current strongest 아래에서 다시 탐색할 가치가 낮은 dead / no-op family를 고정한다
- 같은 축을 반복해서 다시 여는 search waste를 줄인다
- 다음 탐색은 genuinely different family 위주로만 열도록 guardrail을 만든다

## Current strongest

- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`

## Current reading

- dead:
  - quality-headline hybrid
  - risk-on exposure
  - risk-off tightening
  - entry filter
  - position cap
  - sector cap relaxation
  - flow filter
  - soft blacklist
  - dynamic bonus sizing
  - liquidity gate
  - winner cap
  - mid-book recipient
  - tail penalty shape
  - book ordering
  - rebalance timing
  - risk budget
  - signal smoothing
  - sector rotation trigger
  - cross-market handoff
  - dual-score gating
  - state-mixed ranking
  - two-stage weight map
  - conditional tail count
  - conditional bonus size
  - exposure ladder
  - candidate admission
  - cash sleeve
  - rank stability
- no-op:
  - hold buffer
  - KR unknown exclusion
  - book size
  - cost-aware incumbency
  - symbol memory

## Why this matters

- recent batch는 near-miss 지형은 더 선명하게 만들었지만 strongest는 바꾸지 못했다
- 동시에 여러 family가 dead 또는 no-op로 충분히 확인됐다
- 이제 search는 같은 축 미세조정보다 아직 안 본 구조 family 위주로 열어야 한다

## Verdict

- 위 family들은 현재 strongest 기준 mainline strongest search 우선순위에서 내리는 게 맞다
- 다음 탐색은 dead/no-op ledger 밖 genuinely different family에 집중하는 게 가장 값이 크다
