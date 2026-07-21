# Momentum First Backtest Runbook

This runbook defines the first backtest flow to use after a cold restart.

Use this together with [restart_baseline.md](C:\AI\momentum\docs\restart_baseline.md).

## Goal

The first run is not for opening a new branch swarm.

The goal is:

1. re-establish the mixed-market baseline,
2. separate `US` and `KR` contribution clearly,
3. decide whether the next step should be offensive refinement, operating defense, or no promotion.

## Step 0: Baseline Scope

Default restart scope:

- primary window: latest `12 years`
- minimum serious window: `10 years`
- markets: `US + KR`
- role split: `US` as primary design reference, `KR` as mandatory cross-check

## Step 1: Read The Current Truth First

Before rerunning anything large, read:

1. `README.md`
2. `output\split_models_operational_conversion_current_state.md`
3. `output\offensive_screener_cycle\offensive_model_cycle_latest.md`

That tells you whether the repo is currently blocked by drawdown, focused on offensive ranking, or both.

## Step 2: Refresh The Offensive Cycle

Refresh the current offensive operator-facing cycle first.

```powershell
python tools/analysis/run_offensive_model_cycle.py --max-items 30 --top-n 10 --shortlist-top-n 5 --stock-sort-column offensive_score --output-dir output/offensive_screener_cycle
```

Then read:

1. `output\offensive_screener_cycle\offensive_model_cycle_latest.md`
2. `output\offensive_screener_cycle\offensive_handoff_summary_latest.md`
3. `output\offensive_screener_cycle\offensive_action_memo_latest.md`

## Step 3: Refresh The Operational Conversion State

Refresh the mixed-market operating-conversion chain before opening new branch work.

```powershell
python tools/analysis/refresh_split_models_operational_conversion_state.py
python tools/analysis/doctor_split_models_operational_conversion_state.py
```

Then read:

1. `output\split_models_operational_conversion_current_state.md`
2. `output\split_models_operational_conversion_handoff\handoff.md`
3. `output\split_models_operational_conversion_verdict\operational_conversion_verdict.md`

## Step 4: Mixed-Market Backtest Readout

The first serious readout should be over the latest `12 years`.

Do not accept a single blended summary. The first readout must separate:

- full mixed-market result
- `US` sleeve contribution
- `KR` sleeve contribution
- latest `5 years`
- latest `3 years`
- known weak-period diagnostics

If one market carries the full result while the other repeatedly damages drawdown or fragility, mark the branch as market-dependent.

## Step 5: Promotion Decision Discipline

Force the first restart verdict into one of these buckets:

- `mixed_market_viable`
- `us_led_but_kr_fragile`
- `kr_led_but_not_general`
- `blocked_by_drawdown`
- `not_ready_for_new_branch_expansion`

Do not reopen a large sweep before writing that verdict.

## Step 6: Choose Only One Next Lane

After the first pass, choose only one of:

1. offensive refinement
2. operating defense / drawdown repair
3. market-scope repair

Do not open all three in parallel from a cold restart.

## What Not To Do First

- do not collapse the repo to `US only`
- do not collapse the repo to `KR only`
- do not treat the latest `3 years` as the main operating proof
- do not jump straight to autotrade or live-execution questions
- do not reopen large parameter sweeps before the current state, handoff, and offensive cycle are refreshed
