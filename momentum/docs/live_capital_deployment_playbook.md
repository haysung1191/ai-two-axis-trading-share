# Live Capital Deployment Playbook

Purpose:

- define when capital can be deployed
- define how much can be deployed
- define when capital must be reduced or removed
- keep deployment rules mechanical and conservative

This is a deployment playbook for the current local research system.
It is not a claim of guaranteed profit. Investor education sources such as Investor.gov note that all investments carry risk, diversification reduces but does not remove risk, and risk tolerance matters when deciding how much capital to expose. Sources: [Investor.gov diversification](https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/diversify-your-investments), [Investor.gov risk tolerance](https://www.investor.gov/introduction-investing/investing-basics/glossary/risk-tolerance), [Investor.gov asset allocation](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset).

## 1. Current operating assumptions

- operating strategy: `Weekly ETF RiskBudget`
- execution mode: manual only
- review frequency: weekday evening, after market data is settled
- current system role: research + paper/shadow first, live only in staged size
- current evidence snapshot:
  - `ReadinessTier = SMALL_LIVE_READY`
  - `WindowCount = 3`
  - `WalkforwardAdequate = 1`
  - `CAGR_net_0.5pct ~= 0.0833`
  - `WorstMDD ~= -0.0755`
  - `AvgEtfSleeve = 1.0`

Research-only strategies:

- `Weekly ForeignFlow v2`
- `Weekly Hybrid Flow50 RS50`

These are not operating candidates until they show stable out-of-sample behavior.

## 2. Capital bucket rule

Never use:

- emergency cash
- rent or living-expense cash
- debt-funded cash
- money that cannot tolerate a material drawdown

Live capital must come from a separate risk bucket only.

## 3. Deployment ladder

Use staged size only.

### Stage 0: paper only

Stay here until all are true:

- shadow review window completed
- operating strategy stable
- no unresolved operational issues
- turnover behavior understood
- the operating candidate remains the top recommended strategy
- walk-forward evidence remains attached to the strategy

### Stage 1: micro live

Deploy:

- the smaller of:
  - `5%` of the dedicated trading bucket
  - `2,000,000 KRW`

Use this stage to validate:

- operational discipline
- ability to follow signals
- execution friction vs expected cost

### Stage 2: small live

Increase only if Stage 1 remains clean for at least:

- `20 trading days`

and all are true:

- no unresolved `STOP`
- no repeated unexplained `REVIEW`
- shadow and live decisions remain aligned
- realized turnover is still acceptable

Deploy:

- the smaller of:
  - `10% to 15%` of the dedicated trading bucket
  - `5,000,000 KRW`

### Stage 3: controlled scale-up

Increase only if Stage 2 remains clean for at least:

- `40 trading days`

and all are true:

- drawdown remains within expected range
- no major process failures
- strategy remains the recommended operating strategy

Deploy:

- move in steps of `+5%` of the dedicated trading bucket
- never increase more than once per month

## 4. When to put money in

Only add capital when all are true:

- latest local pipeline run completed successfully
- latest shadow artifacts are fresh
- `DailyCheckStatus = GO`
- `HealthStatus = OK`
- `RecommendedStrategyMatch = 1`
- operating strategy is still `Weekly ETF RiskBudget`
- `WindowCount >= 3`
- `WalkforwardAdequate = 1`

Do not add capital:

- on `REVIEW`
- on `STOP`
- on stale runs
- during unresolved strategy changes

## 5. When to reduce or pull capital out

### Immediate freeze: no new capital

Freeze additions immediately if any of:

- `DailyCheckStatus = REVIEW`
- `HealthStatus = WARNING`
- recommendation changes away from the operating strategy
- missing prices appear
- turnover jumps above the normal range and is unexplained

### Partial reduction

Cut live capital by `50%` if any of:

- two consecutive review cycles with unresolved issues
- one realized drawdown that is materially worse than expected
- strategy recommendation changes and stays changed for more than one review cycle

### Full exit to paper only

Move back to paper only if any of:

- `DailyCheckStatus = STOP`
- `HealthStatus = STALE` or `ERROR`
- repeated data integrity issues
- execution behavior materially diverges from the modeled process
- strategy loses leadership and no longer has a convincing readiness case

## 6. When to take profits

Do not invent discretionary profit-taking outside the system.

Use two profit rules only:

- leave signal-level exits to the strategy engine
- manage account-level de-risking only through the deployment ladder

Practical account-level rule:

- if live capital grows to `2x` the current stage cap, withdraw the excess back to cash rather than automatically compounding it

Reason:

- this keeps scale-up deliberate instead of accidental

## 7. Daily operator checklist before any live action

Check in order:

1. `kis_shadow_ops_summary.csv`
2. `kis_shadow_health.csv`
3. `kis_shadow_rebalance_diff.csv`
4. `kis_shadow_nav.csv`
5. `kis_shadow_exceptions.csv`

Only act if the first two are clean.

## 8. Current recommendation

Right now:

- do not jump straight to meaningful live size
- the correct next state is:
  - keep `Weekly ETF RiskBudget` as the operating strategy
  - treat `Weekly Hybrid RS50 RB50` and `Weekly Score50 RegimeState` as paper candidates
  - keep `Weekly ForeignFlow v2` research-only
  - move to micro live only after the live transition checklist is satisfied

## 9. What not to do

Do not:

- average down manually
- override exits emotionally
- add capital after a weak review just because the strategy looks cheap
- scale up because of a short good streak
- change operating strategy frequently

The objective is not maximum speed. The objective is survival plus repeatability.
