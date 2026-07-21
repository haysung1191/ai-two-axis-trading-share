# BTC 1d First Backtest Runbook

This runbook defines the first backtest flow to use after a cold restart.

Use this together with [restart_baseline.md](C:\AI\Crypto\docs\restart_baseline.md).

## Goal

The first run is not for broad family expansion.

The goal is:

1. confirm the repo is healthy,
2. replay the current BTC 1d operating and research surface,
3. establish whether the active mechanism still looks portable beyond BTC.

## Step 0: Environment

From repo root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\pip install -e ".[dev]"
```

## Step 1: Health Check Before Any New Search

Run the existing operating checks first.

```powershell
.venv\Scripts\python scripts\check_btc_1d_practical_health.py
.venv\Scripts\python scripts\check_btc_1d_research_stack_health.py
.venv\Scripts\python scripts\check_btc_1d_contract_health.py
.venv\Scripts\python scripts\check_btc_1d_shadow_health.py --as-json
```

If these already fail, fix the pipeline surface before reopening model mutation work.

## Step 2: Refresh The Current BTC 1d Operating Surface

Rebuild the current operator-facing artifacts before any new hypothesis work.

```powershell
.venv\Scripts\python scripts\run_btc_1d_shadow_update.py
```

Read these first after the refresh:

1. `analysis_results\btc_1d_operating_index_latest.json`
2. `analysis_results\btc_1d_operator_dashboard_latest.json`
3. `analysis_results\btc_1d_research_stack_operating_brief_latest.json`

## Step 3: BTC Main Replay

Treat BTC as the main design target.

The first replay should use the latest `8 years` of daily data, or the nearest supported equivalent in the active script path.

What matters in the first replay:

- current active attack anchor
- current backup behavior
- candidate survival through validation order
- drawdown shape, not just headline CAGR

If the repo already exposes a queue-style active lane, use the queue artifact as the authoritative next step:

1. `analysis_results\btc_1d_attack_execution_queue_latest.md`
2. `analysis_results\btc_1d_attack_pivot_screen_latest.md`
3. `analysis_results\btc_1d_new_family_search_queue_latest.md`

## Step 4: ETH Cross-Check

Do not stop at BTC.

The first cross-check after BTC should be `ETHUSDT` on the same date window.

The question is not whether ETH has equal headline performance. The question is:

- does the mechanism remain directionally coherent,
- or does it break cleanly outside BTC.

If ETH breaks the mechanism materially, freeze promotion and label the edge as `BTC-specific until proven portable`.

## Step 5: Optional Liquid-Major Check

Only after BTC and ETH are understood, add `2-3` liquid majors from the restart basket:

- `SOLUSDT`
- `BNBUSDT`
- optionally `XRPUSDT`

Do not tune directly on this basket. Use it only as a portability screen.

## Step 6: Write The First Verdict

After the first replay, force the result into one of these buckets:

- `portable_enough_for_further_research`
- `btc_led_but_needs_cross_asset_repair`
- `btc_specific_only`
- `not_robust_enough_to_reopen`

That one-line verdict should be written before any new family expansion.

## What Not To Do First

- do not start with a wide altcoin universe
- do not reopen execution plumbing before the research replay is current
- do not treat a short recent window as primary evidence
- do not mutate new families before the active queue and pivot artifacts are refreshed
