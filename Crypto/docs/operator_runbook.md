# Operator Runbook

## Install (Ubuntu 22.04/24.04)

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv git sqlite3 util-linux

sudo mkdir -p /opt/crypto-scanner
sudo chown -R $USER:$USER /opt/crypto-scanner
```

### Get The Code (Pick One)

Git clone:

```bash
cd /opt/crypto-scanner
git clone <YOUR_REPO_URL> .
```

Zip upload (scp):

```bash
scp crypto-scanner.zip <user>@<vm_ip>:/tmp/
ssh <user>@<vm_ip>
cd /opt/crypto-scanner
unzip -o /tmp/crypto-scanner.zip
```

Then install deps:

```bash
cd /opt/crypto-scanner
python3.11 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
```

## systemd

```bash
sudo cp deploy/systemd/crypto-scanner-hourly.service /etc/systemd/system/
sudo cp deploy/systemd/crypto-scanner-hourly.timer /etc/systemd/system/
sudo cp deploy/systemd/crypto-scanner-daily.service /etc/systemd/system/
sudo cp deploy/systemd/crypto-scanner-daily.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now crypto-scanner-hourly.timer
sudo systemctl enable --now crypto-scanner-daily.timer
```

## Status / Logs

```bash
systemctl status crypto-scanner-hourly.timer
journalctl -u crypto-scanner-hourly.service -n 200 --no-pager

systemctl status crypto-scanner-daily.timer
journalctl -u crypto-scanner-daily.service -n 200 --no-pager
```

## Health (Single Command)

```bash
.venv/bin/python -m jobs.health
```

## DB Health

```bash
sqlite3 state.db "select status, count(*) from runs group by status;"
sqlite3 state.db "select run_id, candle_close_ts_ms, status, started_at, completed_at from runs order by candle_close_ts_ms desc limit 5;"
sqlite3 state.db "select count(*) from email_outbox where status='FAILED';"
sqlite3 state.db "select count(*) from positions;"
```

## Safe Rerun

Rerunning the hourly job is safe because:
- OS lock prevents concurrent instances
- DB `UNIQUE` constraints prevent duplicates
- `runs.status='COMPLETED'` makes the run a no-op

```bash
.venv/bin/python -m jobs.hourly_job
```

## Disable Emails Quickly

1. Set `email.enabled: false` in `config/config.yaml`, or
2. Clear `SMTP_TO` or `SMTP_FROM` in `.env`

## What To Paste Back Daily

1. `logs/daily_report_YYYY-MM-DD.json`
2. Output of `.venv/bin/python -m jobs.health`
3. `journalctl -u crypto-scanner-hourly.service -n 300 --no-pager`

## BTC 1d Shadow Baseline

For the current BTC 1d promoted baseline workflow, use:

```bash
.venv/bin/python scripts/run_btc_1d_shadow_update.py
```

That single command refreshes:

- `2200` carry paper validation
- `2600` survivability paper validation
- `2200` walk-forward diagnostic
- `20bps` friction sanity
- `ETHUSDT` cross-check regression
- shadow packet
- status board / baseline freeze / shadow readiness docs

Open this first after the run:

- `analysis_results/btc_1d_operating_index_md_latest.md`

Final attack challenger handoff check:

- confirm `attack_challenger_remote_monitoring_deployment_handoff_ready = true`
- confirm `attack_challenger_next_step = deployment monitoring active`
- confirm `deployment_monitoring_active = true` on `btc_1d_operator_dashboard_latest.json`
- confirm `attack_challenger_bridge_report = analysis_results/btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json`

Fast read:

```bash
.venv/bin/python scripts/check_btc_1d_shadow_health.py
```

Fast read as JSON:

```bash
.venv/bin/python scripts/check_btc_1d_shadow_health.py --as-json
```

Fast refresh-only JSON read:

```bash
.venv/bin/python scripts/run_btc_1d_shadow_update.py --refresh-only --sync-passes 2
```

Dedicated refresh JSON read:

```bash
.venv/bin/python scripts/refresh_btc_1d_operator_stack.py --sync-passes 2
```

For both refresh commands, the handoff keys are exposed in two places:

- top-level payload fields for machine consumers
- nested `refresh_summary` fields for the human-readable refresh block

Check these top-level keys first:

- `attack_challenger_remote_monitoring_deployment_handoff_ready`
- `attack_challenger_next_step`
- `attack_challenger_bridge_report`
- `deployment_monitoring_active`

Open these when the handoff is fully advanced:

- `analysis_results/btc_1d_operating_index_md_latest.md`
- `analysis_results/btc_1d_operating_brief_md_latest.md`
- `analysis_results/btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md`

Standard operating check order:

1. Practical

```bash
.venv/bin/python scripts/check_btc_1d_practical_health.py
```

```bash
.venv/bin/python scripts/check_btc_1d_practical_health.py --as-json
```

2. Research

```bash
.venv/bin/python scripts/check_btc_1d_research_stack_health.py
```

```bash
.venv/bin/python scripts/check_btc_1d_research_stack_health.py --as-json
```

3. Contract

```bash
.venv/bin/python scripts/check_btc_1d_contract_health.py
```

```bash
.venv/bin/python scripts/check_btc_1d_contract_health.py --as-json
```

4. Brief

- `analysis_results/btc_1d_operating_index_md_latest.md`
- `.venv/bin/python scripts/print_btc_1d_operating_brief.py`
- `.venv/bin/python scripts/check_btc_1d_shadow_health.py`
- `.venv/bin/python scripts/check_btc_1d_shadow_health.py --as-json`

For the final attack challenger stage, verify:

- `attack_challenger_remote_monitoring_deployment_handoff_ready: True`
- `attack_challenger_next_step: deployment monitoring active`
- `deployment_monitoring_active: True`
- `attack_challenger_bridge_report: C:\AI\Crypto\analysis_results\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json`

This CLI check order is regression-locked by:

- `tests/unit/test_btc_1d_operating_cli_help_contract.py`

Shadow update output quick-read:

- `execution_health_line` = practical health + research stack status + paper nightly status in one line
- `execution_contract_health_line` = execution health + execution contract read in one line
- `combined_health_line` = practical health + research stack status in one line
- `contract_health_line` = quick-read contract alignment in one line

Paper nightly summary:

- `analysis_results/btc_1d_paper_nightly_summary_md_latest.md`
- use this after `execution_health_line` when you want the full paper execution summary behind the one-line status
- look for `paper_execution_read`
- look for `paper_duplicate_count` when confirming a rerun was safely skipped instead of re-applied
- look for `paper_exit_duplicate_run=True` when the same exit snapshot was re-read as a no-op
- nightly application order is `exit snapshot -> new entry intents`, so a position that closes on the latest candle does not block the same-cycle replacement entry
- a position opened at the same `candle_close_utc` is evaluated from the next candle, so rerunning the same nightly cycle stays a true no-op
- example:
  - `paper execution | track=operating | applied=1 | closed=1 | open=0`

Execution contract summary:

- `analysis_results/btc_1d_execution_contract_screen_md_latest.md`
- use this after `execution_health_line` when you want the combined execution-contract verdict before the short read and full screen
- look for `execution_contract_health_line`
- look for `execution_contract_read`
- look for `regression_lock_test`
- look for `wording_regression_test`
- look for `symmetry_regression_test`
- look for `symmetry_fields`
- look for `symmetry_field_set`
- look for `symmetry_field_map`
- look for `symmetry_contract_bundle`
- look for `symmetry_contract_ready`
- look for `symmetry_contract_stack_complete`
- look for `symmetry_reason_scope`
- look for `symmetry_reason_range_summary`
- look for `symmetry_reason_final_summary`
- look for `symmetry_contract_status`
- look for `symmetry_contract_summary_ready`
- look for `symmetry_contract_topline_verdict`
  - look for `execution_meta_contract_test_index_symmetry_fields`
- look for `standard_check_order_reference`
- look for entry-level `regression_lock_test`
- look for entry-level `standard_check_order_reference`
- look for `reverse_screen_pointer_lock_included`
- look for `reverse_screen_pointer_lock_included=True`
- look for `reverse_screen_pointer_lock_scope=['execution_contract_screen_summary']`
- look for `reverse_screen_pointer_scope_regression_test`
- execution contract summary wording is regression-locked by `tests/unit/test_btc_1d_execution_contract_wording_contract.py`
- look for `meta_contract_topline_regression_test`
- look for `meta_contract_topline_reason_wording_included=True`
- look for `meta_contract_topline_status`
- look for `meta_contract_topline_quick_status`
- look for `meta_contract_topline_highlight`
- look for `meta_contract_reason_highlight_summary`
- look for `meta_contract_reason_final_verdict`
- look for `meta_contract_integrated_topline_verdict`
- execution contract screen should also expose `meta_contract_integrated_topline_verdict`
- execution contract screen should also expose `execution_meta_quick_status`
- execution contract screen should also expose `execution_meta_integrated_quick_verdict`
- execution contract screen should also expose `execution_meta_topline_bundle`
- execution contract screen should also expose `execution_meta_bundle_ready_verdict`
- execution contract screen should also expose `execution_meta_topline_ready`
- execution contract screen should also expose `execution_meta_stack_complete`
- meta contract screen should also expose `execution_meta_quick_status`
- meta contract screen should also expose `execution_meta_integrated_quick_verdict`
- meta contract screen should also expose `execution_meta_topline_bundle`
- meta contract screen should also expose `execution_meta_bundle_ready_verdict`
- meta contract screen should also expose `execution_meta_topline_ready`
- meta contract screen should also expose `execution_meta_stack_complete`
- meta contract topline wording is regression-locked by `tests/unit/test_btc_1d_meta_contract_wording_contract.py`
- execution/meta summary wording symmetry is regression-locked by `tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py`
- example:
  - `BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ... || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
  - `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
  - `tests/unit/test_btc_1d_operating_cli_help_contract.py`
  - `tests/unit/test_btc_1d_execution_contract_wording_contract.py`
  - `meta_contract_topline_status=meta topline status | regression_test=tests/unit/test_btc_1d_meta_contract_wording_contract.py | reason_included=True`
  - `meta_contract_topline_quick_status=meta topline quick | lock=ok | reason=included`
  - `meta_contract_topline_highlight=topline highlight | lock=ok | reason=included`
  - `meta_contract_reason_highlight_summary=reason+highlight | summary_ready | reason=included`
  - `meta_contract_reason_final_verdict=reason final verdict | complete | reason=included`
  - `meta_contract_integrated_topline_verdict=meta contract integrated | topline=complete | reason=complete`
  - `execution_meta_quick_status=execution+meta quick | execution=complete | meta=complete`
  - `execution_meta_integrated_quick_verdict=execution+meta integrated | execution=complete | meta=complete`
  - `execution_meta_topline_bundle=execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete`
  - `execution_meta_bundle_ready_verdict=execution+meta bundle ready | complete`
  - `execution_meta_topline_ready=execution+meta topline ready | complete`
  - `execution_meta_stack_complete=execution+meta stack complete | complete`
  - `execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete should stay aligned across the execution contract summary`
  - `execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete`
  - `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`
  - `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`
  - `['symmetry_regression_test', 'execution_contract_symmetry_lock_included']`
  - `symmetry_field_set=['symmetry_regression_test', 'execution_contract_symmetry_lock_included', 'execution_contract_symmetry_regression_test', 'execution_meta_contract_test_index_symmetry_fields']`
  - `symmetry_field_map=symmetry field map | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields`
  - `symmetry_contract_bundle=symmetry contract bundle | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields`
  - `symmetry_contract_ready=True`
  - `symmetry_contract_stack_complete=True`
  - `symmetry_reason_scope=symmetry reason scope | key | set | map | bundle | ready`
  - `symmetry_reason_range_summary=symmetry reason range | key | set | map | bundle | ready | stack_complete`
  - `symmetry_reason_final_summary=symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready`
  - `symmetry_contract_status=symmetry contract status | ready=True | symmetry reason scope | key | set | map | bundle | ready`
  - `symmetry_contract_summary_ready=True`
  - `symmetry_contract_topline_verdict=symmetry contract topline | complete`
  - `execution_meta_contract_test_index_symmetry_fields=['symmetry_regression_test', 'execution_contract_symmetry_lock_included']`
  - `practical > research > contract > brief`
  - `operating_brief -> tests/unit/test_btc_1d_operating_cli_help_contract.py`
  - `operating_index -> practical > research > contract > brief`

Quick-read contract check:

- `analysis_results/btc_1d_quick_read_contract_screen_md_latest.md`
- `analysis_results/btc_1d_execution_contract_screen_md_latest.md`
- `analysis_results/btc_1d_meta_contract_screen_md_latest.md`
- `analysis_results/btc_1d_execution_meta_contract_test_index_md_latest.md`
- use this when you need to verify:
  - operating brief/index still share `operating_v3`
  - execution health + paper nightly + paper execution read still align across latest brief/index
  - research stack brief still stays on `research_stack_v2`
  - latest brief/index/contract/health JSON still share the same regression lock and standard check order
  - meta contract scope also includes:
    - `execution_contract_screen`
    - `execution_contract_screen_operating_brief_entry`
    - `execution_contract_screen_operating_index_entry`
  - execution contract screen should also expose:
    - `wording_regression_test`
    - `symmetry_regression_test`
    - `tests/unit/test_btc_1d_execution_contract_wording_contract.py`
  - `execution_contract_entry_scope_included=True`
  - `execution_contract_wording_lock_included=True`
  - `execution_contract_symmetry_lock_included=True`
  - `execution_contract_symmetry_regression_test`
  - `execution_contract_symmetry_fields`
  - `execution_contract_symmetry_field_set`
  - `execution_contract_symmetry_field_map`
  - `execution_contract_symmetry_contract_bundle`
  - `execution_contract_symmetry_ready=True`
  - `execution_contract_symmetry_stack_complete=True`
  - `execution_contract_symmetry_reason_scope`
  - `execution_contract_symmetry_reason_range_summary`
  - `execution_contract_symmetry_reason_final_summary`
  - `execution_contract_symmetry_status`
  - `execution_contract_symmetry_summary_ready=True`
  - `execution_contract_symmetry_topline_verdict=symmetry contract topline | complete`
  - `execution_meta_contract_test_index_symmetry_fields`
  - `execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata`
  - `reverse_screen_pointer_lock_included`
  - `reverse_screen_pointer_lock_included=True`
  - `reverse_screen_pointer_lock_scope=['meta_contract_screen_summary']`
  - `reverse_screen_pointer_scope_regression_test`
  - meta contract verdict should cover:
    - `execution contract summary`
    - `execution contract entry scope`
    - `execution contract wording lock`
    - `execution contract wording lock, meta_contract_topline_regression_test, and execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata`
  - latest meta-contract reason scope wording is regression-locked by `tests/unit/test_btc_1d_meta_contract_runbook_wording_contract.py`
  - `meta_contract_topline_regression_test=tests/unit/test_btc_1d_meta_contract_wording_contract.py`
  - `meta_contract_topline_reason_wording_included=True`
  - `execution_meta_quick_status=execution+meta quick | execution=complete | meta=complete`
  - `execution_meta_integrated_quick_verdict=execution+meta integrated | execution=complete | meta=complete`
  - `execution_meta_topline_bundle=execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete`
  - `execution_meta_bundle_ready_verdict=execution+meta bundle ready | complete`
  - `execution_meta_topline_ready=execution+meta topline ready | complete`
  - `execution_meta_stack_complete=execution+meta stack complete | complete`
  - `execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete should stay aligned across the execution contract summary`
  - `execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata, and execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete.`
  - `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`
  - `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`
  - meta contract topline wording is regression-locked by `tests/unit/test_btc_1d_meta_contract_wording_contract.py`
  - `health_order_aligned=True` for practical/research/contract health outputs
  - `all_health_standard_order_aligned` = `Deprecated alias for health_order_aligned. Prefer health_order_aligned.`
  - alias migration wording is regression-locked by `tests/unit/test_btc_1d_contract_alias_wording_contract.py`
  - operating order + alias migration help wording is regression-locked by `tests/unit/test_btc_1d_contract_docs_contract.py`
  - meta contract verdict wording is regression-locked by `tests/unit/test_compare_btc_1d_meta_contract_screen.py`
  - execution/meta summary wording symmetry is regression-locked by `tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py`
- read in this order:
  - `btc_1d_quick_read_contract_screen_md_latest.md`
  - `btc_1d_execution_contract_screen_md_latest.md`
  - `btc_1d_meta_contract_screen_md_latest.md`
  - `btc_1d_execution_meta_contract_test_index_md_latest.md`
- this contract read order is regression-locked by `tests/unit/test_btc_1d_contract_read_order_runbook_contract.py`
- the execution/meta contract test map also includes `tests/unit/test_btc_1d_contract_read_order_runbook_contract.py`
- the execution/meta contract test map also points back to:
  - `analysis_results/btc_1d_quick_read_contract_screen_md_latest.md`
  - `analysis_results/btc_1d_execution_contract_screen_md_latest.md`
  - `analysis_results/btc_1d_meta_contract_screen_md_latest.md`

What to look for immediately in the `run_btc_1d_shadow_update.py` JSON output:

- `execution_health_line`
- `execution_contract_health_line`
- `execution_contract_read`
- `paper_execution_read`
- `paper_duplicate_count`
- `combined_health_line`
- `contract_health_line`
- example:
  - `BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ...`
  - `BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ... || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
  - `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
  - `paper execution | track=operating | applied=1 | closed=1 | open=0`
  - `BTC 1d practical health ... || BTC 1d research stack ...`
  - `BTC 1d contract health | operating_brief=operating_v3 | operating_index=operating_v3 | aligned=True | research=research_stack_v2 | distinct=True | partitioned=True | standard_order_aligned=True | health_order_aligned=True | standard_order=practical > research > contract > brief`

Windows launcher:

- `scripts\run_btc_1d_shadow_update_and_open.cmd`

Useful stable pointers:

- `analysis_results/btc_1d_latest_summary_md_latest.md`
- `analysis_results/btc_1d_execution_meta_contract_test_index_md_latest.md`
- `analysis_results/btc_1d_paper_nightly_summary_md_latest.md`
- `analysis_results/btc_1d_shadow_packet_md_latest.md`
- `analysis_results/btc_1d_candidate_status_board_md_latest.md`
- `analysis_results/btc_1d_baseline_freeze_md_latest.md`
- `analysis_results/btc_1d_shadow_readiness_md_latest.md`
- `analysis_results/btc_1d_practical_scorecard_md_latest.md`
- `analysis_results/btc_1d_practical_promotion_gate_md_latest.md`
- `analysis_results/btc_1d_research_stack_operating_brief_md_latest.md`
- `analysis_results/btc_1d_quick_read_contract_screen_md_latest.md`
- `analysis_results/btc_1d_execution_contract_screen_md_latest.md`
- `analysis_results/btc_1d_meta_contract_screen_md_latest.md`

Practical candidate interpretation:

- `btc_1d_practical_scorecard_md_latest.md` = evidence pack
- `btc_1d_practical_promotion_gate_md_latest.md` = final practical gate result
- `scripts/check_btc_1d_practical_health.py` = one-line terminal read

Research stack interpretation:

- `btc_1d_research_stack_operating_brief_md_latest.md` = attack frontier / backup / defensive hold / near-miss priority
- `scripts/check_btc_1d_research_stack_health.py` = one-line research stack read
- `btc_1d_quick_read_contract_screen_md_latest.md` = quick-read JSON contract check for operating vs research latest files
- `btc_1d_execution_contract_screen_md_latest.md` = execution-layer contract check for latest brief/index + paper nightly read
- `btc_1d_meta_contract_screen_md_latest.md` = shared meta-contract check across latest brief/index/contract/health JSON

Operating brief interpretation:

- `scripts/print_btc_1d_operating_brief.py` = one-block operating read
- now includes:
  - `execution_health_line`
  - `combined_health_line`
  - `contract_health_line`

Paper execution interpretation:

- `analysis_results/btc_1d_paper_nightly_summary_md_latest.md` = full paper execution summary
- read in this order:
  - `execution_health_line`
  - `execution_contract_read`
  - `paper_execution_read`
  - full paper nightly summary

Reference:

- `docs/btc_1d_shadow_update_runbook.md`
- `docs/crypto_research_infra_backlog.md`
