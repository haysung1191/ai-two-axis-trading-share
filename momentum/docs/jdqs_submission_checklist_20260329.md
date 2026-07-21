# JDQS Submission Checklist

## Status

- manuscript angle fixed: `U.S. implementable large-cap 12-1 momentum`
- draft manuscript created
- submission package created
- deep-research prompt created

## Mandatory Before Submission

- rebuild the stock universe with historical constituent membership
- remove survivorship and benchmark look-ahead bias explicitly
- document delistings and ticker changes
- use point-in-time sector classifications
- re-run all headline performance outputs after universe cleanup
- replace provisional literature section with citation-backed review
- add factor-adjusted regression table
- use Newey-West robust standard errors in regression tables
- add a same-universe large-cap market benchmark
- add unconstrained momentum comparison to identify the effect of the sector cap
- add break-even transaction cost analysis
- add a capacity-aware trading-cost diagnostic
- generate clean figures:
  - cumulative NAV
  - drawdown
  - walk-forward CAGR by window
  - CAGR versus cost
  - sector exposure through time
  - regime or crash-state performance

## Strongly Recommended

- add subperiod breakdowns
- add turnover decomposition
- explain cost assumptions clearly
- write one paragraph on economic intuition for the sector cap
- standardize table formatting and rounding
- state execution timing explicitly:
  - signal date
  - execution date
  - price basis used for fills

## Nice To Have

- create a single script that builds all paper tables
- create a single script that builds all paper figures
- prepare a short cover letter for JDQS
- prepare a shorter alternate version for a domestic Korean journal
- prepare an alternate submission version for `APJFS` only after the econometric section is strengthened

## Current Go / No-Go View

- current state for private draft circulation: `GO`
- current state for real submission: `NO-GO`

Reason:

- the current result is strong enough to justify writing
- the current bias control is not strong enough to justify actual submission
- the current econometric evidence is not strong enough to justify actual submission

## Immediate Next Best Step

- literature and venue-positioning support received
- next: rebuild the universe historically
- then: add factor regressions and same-universe benchmark comparisons
- then: refresh the manuscript numbers and figures
