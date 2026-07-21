# RangeOsc Tuning Plan

Objective:

- evaluate whether `RangeOsc` can improve the current long-only baseline
- reject it quickly if it only adds churn and stopouts

Current interpretation:

- `RangeOsc` is not adopted as the operating strategy
- it remains a tuning candidate only

## Tuning goal

Primary goal:

- improve `CAGR_net_0.5pct` without materially worsening `MDD`

Secondary goals:

- reduce `OscStopCount`
- keep turnover controlled
- avoid false range detection

## Evaluation baseline

Always compare these three:

1. baseline current operating strategy
   - `Weekly Score50 RegimeState`
2. regime-state variant only
3. regime-state plus oscillation sleeve
   - `Weekly Score50 RangeOsc`

## Metrics to watch

- `CAGR`
- `MDD`
- `CAGR_net_0.5pct`
- `AnnualTurnover`
- `OscEntryCount`
- `OscExitCount`
- `OscStopCount`

Interpretation:

- high `OscStopCount` usually means poor range detection or weak re-entry discipline
- higher turnover without better net CAGR is a rejection signal

## Tuning order

### 1. Tighten regime detection first

Tune first:

- `range_slope_threshold`
- `range_dist_threshold`
- `range_breakout_persistence_threshold`
- `range_breadth_tolerance`

Reason:

- if the regime gate is weak, entry tuning will not fix the real problem

### 2. Tighten entry quality

Tune next:

- `osc_z_entry`
- `osc_lookback`
- `osc_band_sigma`

Reason:

- remove shallow or noisy fade entries

### 3. Improve failure handling

Tune next:

- `osc_z_stop`
- `osc_band_break_sigma`
- `osc_reentry_cooldown_days`

Reason:

- reduce repeated failed fades after breakout expansion

### 4. Adjust exit only after the above

Tune last:

- `osc_z_exit`

Reason:

- early profit-taking matters less than regime quality and stop discipline

## Rejection rules

Reject the current parameter set if any of these persist:

- higher turnover with no net CAGR improvement
- no drawdown benefit
- repeated oscillation stopouts
- weak or inconsistent contribution across reruns

## Acceptance rule

Promote `RangeOsc` only if it shows:

- better or similar drawdown
- better cost-adjusted return
- controlled turnover
- lower operational complexity than the extra return justifies

If not, keep `Weekly Score50 RegimeState` as the operating strategy and leave `RangeOsc` in research only.
