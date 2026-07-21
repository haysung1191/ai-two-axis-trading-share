# Live Transition Checklist

Current baseline:

- Operating strategy: `Weekly ETF RiskBudget`
- Current status target: preserve `SMALL_LIVE_READY` on the operating candidate while keeping alternatives in paper evaluation

Use this checklist before considering any live deployment.

## 1. Strategy lock

- Keep one operating strategy fixed for the review period.
- Current default: `Weekly ETF RiskBudget`
- Do not rotate the operating strategy frequently during validation.

## 2. Shadow validation window

- Minimum review window: `2 weeks`
- Preferred review window: `4 to 6 weeks`
- Use the same daily review process throughout the window.
- Current status:
  - named-only walk-forward attached
  - operating candidate is `SMALL_LIVE_READY`
  - `Weekly Hybrid RS50 RB50` and `Weekly Score50 RegimeState` remain `PAPER_READY`
  - `ForeignFlow` branch remains research-only

## 3. Daily operational stability

Pass condition:

- `kis_shadow_health.csv` is usually `HealthStatus=OK`
- `kis_shadow_ops_summary.csv` is usually `DailyCheckStatus=GO`
- `REVIEW` cases are rare and clearly explainable
- `STOP` cases are rare and treated as blockers

Fail condition:

- frequent stale runs
- repeated missing prices
- unexplained large turnover
- repeated strategy mismatch

## 4. Strategy stability

Pass condition:

- `kis_live_readiness.csv` does not frequently switch the top recommended strategy
- the operating strategy remains near the top of the leaderboard consistently
- `Weekly ETF RiskBudget` remains ahead of other operational candidates after costs and walk-forward stability screens

Fail condition:

- recommendation changes often
- ranking leadership is unstable week to week

## 5. Turnover discipline

Pass condition:

- turnover after initial bootstrap settles into a repeatable range
- turnover remains acceptable after cost assumptions
- for the current operating strategy, annual turnover remains near the observed low-turnover profile

Review items:

- separate one-time transition turnover from structural turnover
- inspect `kis_shadow_rebalance_diff.csv` on every `REVIEW`

Fail condition:

- repeated high turnover without performance benefit

## 6. Shadow vs backtest consistency

Pass condition:

- daily shadow portfolio behavior is directionally consistent with the backtest logic
- no repeated divergence caused by stale inputs or path inconsistencies

Fail condition:

- shadow output regularly disagrees with expected strategy behavior

## 7. Stress behavior

Pass condition:

- the strategy behaves coherently during high-volatility or drawdown periods
- regime transitions do not create unexplained churn
- cost stress remains positive at base / moderate / severe scenarios
- ETF-only structure remains intentional and understood

Fail condition:

- drawdown control breaks in practice
- regime logic causes unstable position flipping

## 8. Minimum live gate

Consider small-capital live deployment only if all are true:

- shadow review window is complete
- operating strategy remained stable
- health and ops status remained mostly clean
- turnover is acceptable after costs
- no unresolved operational exceptions remain
- the operating strategy remains `Weekly ETF RiskBudget`
- `ForeignFlow` branch is not being promoted on the basis of unstable OOS windows

If one or more conditions fail, remain in paper-shadow mode.
