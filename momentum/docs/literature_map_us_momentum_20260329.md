# Literature Map for Implementable U.S. Large-Cap Momentum

## Positioning Summary

This paper should be positioned as an `implementability` paper, not a `new factor` paper. The literature support falls into five clusters:

- canonical cross-sectional momentum
- friction-aware and cost-aware momentum
- sector or industry-neutral momentum construction
- liquidity and capacity constraints
- capital-constrained implementability

## 1. Canonical Momentum

### Jegadeesh and Titman (1993)

- role in this paper:
  - foundational evidence for cross-sectional momentum
- why it matters:
  - justifies using a standard momentum signal instead of claiming novelty
- how to use it:
  - introduction
  - signal-definition motivation

### Ken French momentum library conventions

- role in this paper:
  - practical standard for `12-1` momentum construction
- why it matters:
  - supports the skip-one-month convention
- how to use it:
  - methods section
  - signal-definition footnote

## 2. Friction-Aware Momentum

### Lesmond, Schill, and Zhou (2004)

- role in this paper:
  - classic skeptical argument that momentum profits may be illusory after costs
- why it matters:
  - motivates explicit trading-friction treatment
- how to use it:
  - introduction
  - motivation for liquidity filters

### Korajczyk and Sadka (2004)

- role in this paper:
  - capacity and market-impact critique of momentum
- why it matters:
  - justifies adding a capacity-aware cost section
- how to use it:
  - robustness section
  - benchmark for break-even cost analysis

### Novy-Marx and Velikov (2016)

- role in this paper:
  - anomaly profitability after realistic trading costs
- why it matters:
  - supports break-even transaction cost analysis
- how to use it:
  - robustness section
  - cost-analysis framing

## 3. Sector And Industry Effects

### Moskowitz and Grinblatt (1999)

- role in this paper:
  - industry momentum explains part of stock momentum
- why it matters:
  - sector cap must be framed as an economically meaningful design choice
- how to use it:
  - motivation for sector-cap rule
  - design and benchmark-comparison section

### Ehsani, Harvey, and Li (2021)

- role in this paper:
  - sector-neutral factor construction can improve risk-adjusted results
- why it matters:
  - supports the claim that sector caps are not arbitrary
- how to use it:
  - design motivation
  - discussion of unconstrained versus constrained momentum

### Blitz, Huij, and Martens (2011)

- role in this paper:
  - residual momentum as a cleaner signal after removing common-factor effects
- why it matters:
  - supports the residual sector rotation benchmark already used in the repo
- how to use it:
  - benchmark section
  - discussion of common-factor contamination

## 4. Liquidity And Capacity

### Amihud (2002)

- role in this paper:
  - liquidity as a priced characteristic
- why it matters:
  - provides academic support for a liquidity filter beyond pure implementation convenience
- how to use it:
  - data and methods section

### Pastor and Stambaugh (2003)

- role in this paper:
  - liquidity risk as an asset-pricing variable
- why it matters:
  - motivates optional liquidity-risk regression extensions
- how to use it:
  - robustness section

## 5. Crash Risk And Dynamic Risk

### Daniel and Moskowitz (2016)

- role in this paper:
  - momentum crashes during sharp market rebounds
- why it matters:
  - crash-state analysis is mandatory for reviewer credibility
- how to use it:
  - robustness section
  - discussion of left-tail risk

### Barroso and Santa-Clara (2015)

- role in this paper:
  - risk-managed momentum through volatility scaling
- why it matters:
  - optional extension if a risk-managed appendix is added
- how to use it:
  - appendix or extension section

## 6. Bias Control

### Shumway (1997)

- role in this paper:
  - delisting bias in return databases
- why it matters:
  - current manuscript is not submission-ready without delisting treatment
- how to use it:
  - data section
  - limitations section

### Point-in-time S&P constituent reconstruction references

- role in this paper:
  - historical universe construction
- why it matters:
  - current static S&P 100 membership is the main desk-rejection risk
- how to use it:
  - data section
  - reproducibility appendix

## What The Literature Implies The Paper Must Add

- point-in-time S&P 100 membership
- delisting-return treatment
- same-universe large-cap benchmark
- unconstrained momentum benchmark
- Carhart and FF5 regressions
- Newey-West t-statistics
- break-even transaction cost analysis
- capacity-aware cost diagnostics
- crash-state analysis

## Venue Implication

- `JDQS` is the best current fit because the paper is strongest as an applied quantitative portfolio-management study.
- `APJFS` is only realistic after the econometric section is materially stronger.
- `KJFS` is not a strong fit for a U.S.-only empirical design.

