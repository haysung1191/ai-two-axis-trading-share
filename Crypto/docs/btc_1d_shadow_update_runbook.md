# BTC 1d Shadow Update Runbook

## Current Baseline

- candidate: `low_vol_cap_050_025_minvol020_p2200`
- scope: `BTC-only`
- carry reference: `2200`
- survivability reference: `2600`

## Single Command

```bash
.venv/bin/python scripts/run_btc_1d_shadow_update.py
```

Windows:

```powershell
.venv\Scripts\python scripts\run_btc_1d_shadow_update.py
```

Windows one-click runner:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_btc_1d_shadow_update_and_open.ps1
```

Windows double-click / `cmd` runner:

```bat
scripts\run_btc_1d_shadow_update_and_open.cmd
```

## What This Refreshes

- `2200` carry paper validation
- `2600` survivability paper validation
- `2200` walk-forward diagnostic
- `20bps` friction sanity
- `ETHUSDT` promoted regression cross-check
- shadow packet
- candidate status board
- baseline freeze
- shadow readiness

## First File To Open

Open this first after each run:

- `analysis_results/btc_1d_operating_index_md_latest.md`

## Final Attack Challenger Handoff Check

Final attack challenger handoff check:

- confirm `attack_challenger_remote_monitoring_deployment_handoff_ready = true`
- confirm `attack_challenger_next_step = deployment monitoring active`
- confirm `deployment_monitoring_active = true` on `btc_1d_operator_dashboard_latest.json`
- confirm `attack_challenger_bridge_report = analysis_results/btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json`

Fast terminal read:

```powershell
.venv\Scripts\python scripts\check_btc_1d_shadow_health.py
```

Fast terminal read as JSON:

```powershell
.venv\Scripts\python scripts\check_btc_1d_shadow_health.py --as-json
```

Fast refresh-only JSON read:

```powershell
.venv\Scripts\python scripts\run_btc_1d_shadow_update.py --refresh-only --sync-passes 2
```

Dedicated refresh JSON read:

```powershell
.venv\Scripts\python scripts\refresh_btc_1d_operator_stack.py --sync-passes 2
```

For both refresh commands, the same three fields are exposed twice:

- top-level payload fields for machine readers
- nested `refresh_summary` fields for the human-oriented refresh block

Top-level keys to confirm first:

- `attack_challenger_remote_monitoring_deployment_handoff_ready`
- `attack_challenger_next_step`
- `attack_challenger_bridge_report`
- `deployment_monitoring_active`

Open these when the handoff is fully advanced:

- `analysis_results/btc_1d_operating_index_md_latest.md`
- `analysis_results/btc_1d_operating_brief_md_latest.md`
- `analysis_results/btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md`

If the handoff is fully advanced, the operator-facing read should show:

- `Attack challenger next step: deployment monitoring active`
- `Deployment monitoring active: true`
- `Attack challenger bridge report: C:\AI\Crypto\analysis_results\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json`

## Standard Check Order

1. Practical

```powershell
.venv\Scripts\python scripts\check_btc_1d_practical_health.py
```

For script integration, print the same practical state as JSON:

```powershell
.venv\Scripts\python scripts\check_btc_1d_practical_health.py --as-json
```

2. Research

```powershell
.venv\Scripts\python scripts\check_btc_1d_research_stack_health.py
```

For script integration, print the same research stack state as JSON:

```powershell
.venv\Scripts\python scripts\check_btc_1d_research_stack_health.py --as-json
```

3. Contract

```powershell
.venv\Scripts\python scripts\check_btc_1d_contract_health.py
```

For script integration, print the same contract state as JSON:

```powershell
.venv\Scripts\python scripts\check_btc_1d_contract_health.py --as-json
```

4. Brief

Print the same state in one short terminal block:

```powershell
.venv\Scripts\python scripts\print_btc_1d_operating_brief.py
```

Or run the fast health gate:

```powershell
.venv\Scripts\python scripts\check_btc_1d_shadow_health.py
```

Or print the same final gate as JSON:

```powershell
.venv\Scripts\python scripts\check_btc_1d_shadow_health.py --as-json
```

For the final attack challenger stage, verify:

- `attack_challenger_remote_monitoring_deployment_handoff_ready: True`
- `attack_challenger_next_step: deployment monitoring active`
- `deployment_monitoring_active: True`
- `attack_challenger_bridge_report: C:\AI\Crypto\analysis_results\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json`

This CLI check order is regression-locked by:

- `tests/unit/test_btc_1d_operating_cli_help_contract.py`

Quick-read contract check:

- open `analysis_results/btc_1d_quick_read_contract_screen_md_latest.md`
- open `analysis_results/btc_1d_execution_contract_screen_md_latest.md`
- open `analysis_results/btc_1d_meta_contract_screen_md_latest.md`
- open `analysis_results/btc_1d_execution_meta_contract_test_index_md_latest.md`
- confirm:
  - `operating_brief = operating_v3`
  - `operating_index = operating_v3`
  - `research_stack_operating_brief = research_stack_v2`
  - execution health / paper nightly / paper execution read stay aligned across latest brief/index
  - meta contract remains fully aligned across latest brief/index/contract/health JSON
  - `health_order_aligned = true` across practical/research/contract health outputs
  - `all_health_standard_order_aligned` = `Deprecated alias for health_order_aligned. Prefer health_order_aligned.`
  - alias migration wording is regression-locked by `tests/unit/test_btc_1d_contract_alias_wording_contract.py`
  - operating order + alias migration help wording is regression-locked by `tests/unit/test_btc_1d_contract_docs_contract.py`
  - use this read order:
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

Shadow update JSON quick-read:

- look for `execution_health_line`
- look for `combined_health_line`
- look for `contract_health_line`
- meaning: practical health + research stack status + paper nightly status in one line
- meaning: practical health + research stack status in one line
- and quick-read contract alignment in one line
- example:
  - `BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ...`
  - `BTC 1d practical health ... || BTC 1d research stack ...`
  - `BTC 1d contract health | operating_brief=operating_v3 | operating_index=operating_v3 | aligned=True | research=research_stack_v2 | distinct=True | partitioned=True | standard_order_aligned=True | health_order_aligned=True | standard_order=practical > research > contract > brief`

Paper nightly summary:

- `analysis_results/btc_1d_paper_nightly_summary_md_latest.md`
- use this right after checking `execution_health_line` when you need the full paper execution detail
- look for `paper_execution_read`
- look for `paper_duplicate_count` when validating rerun-safe nightly behavior
- look for `paper_exit_duplicate_run=True` when the same exit snapshot was re-read as a no-op
- nightly application order is `exit snapshot -> new entry intents`, so a same-cycle close can be replaced without a false `existing_open_position` reject
- a position opened at the same `candle_close_utc` is evaluated from the next candle, so rerunning the same nightly cycle stays a true no-op
- example:
  - `paper execution | track=operating | applied=1 | closed=1 | open=0`

Execution contract summary:

- `analysis_results/btc_1d_execution_contract_screen_md_latest.md`
- use this right after checking `execution_health_line` when you want the short execution-contract read before the full screen
- look for `execution_contract_read`
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
  - `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
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

For the BTC practical candidate scorecard and promotion view, open:

- `analysis_results/btc_1d_practical_scorecard_md_latest.md`
- `analysis_results/btc_1d_practical_promotion_gate_md_latest.md`
- `analysis_results/btc_1d_research_stack_operating_brief_md_latest.md`

The practical scorecard summarizes:

- paper / friction
- benchmark comparison
- statistical defense
- regime stability
- concentration

The practical promotion gate adds the final practical status:

- `promotable_btc_only_practical`
- `btc_only_practical_with_caveats`
- `hold_not_promotable`

The research stack brief adds the current research hierarchy:

- attack frontier
- attack backup
- defensive hold
- next near-miss to revisit
- plus direct pointers to:
  - `btc_1d_quick_read_contract_screen_md_latest.md`
  - `btc_1d_execution_contract_screen_md_latest.md`
  - `btc_1d_meta_contract_screen_md_latest.md`

The quick-read contract screen adds the current JSON contract check:

- operating brief/index should stay on `operating_v3`
- research stack brief should stay on `research_stack_v2`

The execution contract screen adds the execution-layer contract check:

- latest brief/index should publish the same `execution_health_line`
- latest brief/index should publish the same `execution_contract_health_line`
- latest brief/index should publish the same `paper_nightly_health_line`
- latest brief/index should publish the same `paper_execution_read`
- the screen should also expose `regression_lock_test`
- the screen should also expose `wording_regression_test`
- the screen should also expose `symmetry_regression_test`
- the screen should also expose `standard_check_order_reference`
- each `operating_brief` / `operating_index` entry should also expose `regression_lock_test`
- each `operating_brief` / `operating_index` entry should also expose `standard_check_order_reference`
- examples:
  - `tests/unit/test_btc_1d_operating_cli_help_contract.py`
  - `practical > research > contract > brief`
  - `operating_brief -> tests/unit/test_btc_1d_operating_cli_help_contract.py`
  - `operating_index -> practical > research > contract > brief`

The meta contract screen adds the shared meta-contract check:

- latest brief/index/contract/health JSON should share the same regression lock
- published standard check order should remain `practical -> research -> contract -> brief`
- `standard_check_order_scope` should also include:
  - `execution_contract_screen`
  - `execution_contract_screen_operating_brief_entry`
  - `execution_contract_screen_operating_index_entry`
- `execution_contract_screen` should also expose:
  - `wording_regression_test`
  - `symmetry_regression_test`
  - `tests/unit/test_btc_1d_execution_contract_wording_contract.py`
- `execution_contract_entry_scope_included` should be `True`
- `execution_contract_wording_lock_included` should be `True`
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
- `reverse_screen_pointer_lock_included` should be `True`
- `reverse_screen_pointer_lock_scope=['meta_contract_screen_summary']`
- `reverse_screen_pointer_scope_regression_test`
- meta contract verdict should also cover:
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
- meta contract verdict wording is regression-locked by `tests/unit/test_compare_btc_1d_meta_contract_screen.py`
- execution/meta summary wording symmetry is regression-locked by `tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py`

The run also writes stable brief files:

- `analysis_results/btc_1d_operating_brief_latest.json`
- `analysis_results/btc_1d_operating_brief_txt_latest.txt`
- `analysis_results/btc_1d_operating_brief_md_latest.md`

The operating brief now includes:

- `execution_health_line`
- `execution_contract_health_line`
- `combined_health_line`
- `contract_health_line`

Paper execution interpretation:

- `execution_health_line`
- `execution_contract_health_line`
- `execution_contract_read`
- `paper_execution_read`
- `paper_duplicate_count`
- `analysis_results/btc_1d_paper_nightly_summary_md_latest.md`
- example:
  - `BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ...`
  - `BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ... || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
  - `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
  - `paper execution | track=operating | applied=1 | closed=1 | open=0`

The health gate should return exit code `0` only when the current operating baseline still matches the expected BTC-only shadow-ready state.

That index points at the latest stable copies for:

- summary
- shadow packet
- status board
- baseline freeze
- shadow readiness
- walk-forward
- friction

## Primary Output Files

All outputs land in `analysis_results/` with fresh timestamps.

- `btc_1d_shadow_packet_*.json`
- `btc_1d_shadow_packet_*.md`
- `btc_1d_candidate_status_board_*.json`
- `btc_1d_baseline_freeze_*.json`
- `btc_1d_shadow_readiness_*.json`
- `btc_1d_walk_forward_diagnostic_*.json`
- `btc_1d_low_vol_cap_friction_*.json`

Stable pointer files are also refreshed on every run:

- `btc_1d_operating_index_latest.json`
- `btc_1d_operating_index_md_latest.md`
- `btc_1d_execution_meta_contract_test_index_latest.json`
- `btc_1d_execution_meta_contract_test_index_md_latest.md`
- `btc_1d_latest_summary_latest.json`
- `btc_1d_latest_summary_md_latest.md`
- `btc_1d_shadow_packet_latest.json`
- `btc_1d_shadow_packet_md_latest.md`
- `btc_1d_candidate_status_board_latest.json`
- `btc_1d_candidate_status_board_md_latest.md`
- `btc_1d_baseline_freeze_latest.json`
- `btc_1d_baseline_freeze_md_latest.md`
- `btc_1d_shadow_readiness_latest.json`
- `btc_1d_shadow_readiness_md_latest.md`
- `btc_1d_walk_forward_diagnostic_latest.json`
- `btc_1d_walk_forward_diagnostic_md_latest.md`
- `btc_1d_low_vol_cap_friction_latest.json`
- `btc_1d_low_vol_cap_friction_md_latest.md`
- `btc_1d_practical_scorecard_latest.json`
- `btc_1d_practical_scorecard_md_latest.md`
- `btc_1d_practical_promotion_gate_latest.json`
- `btc_1d_practical_promotion_gate_md_latest.md`
- `btc_1d_research_stack_operating_brief_latest.json`
- `btc_1d_research_stack_operating_brief_md_latest.md`
- `btc_1d_quick_read_contract_screen_latest.json`
- `btc_1d_quick_read_contract_screen_md_latest.md`
- `btc_1d_execution_contract_screen_latest.json`
- `btc_1d_execution_contract_screen_md_latest.md`
- `btc_1d_meta_contract_screen_latest.json`
- `btc_1d_meta_contract_screen_md_latest.md`
- `btc_1d_paper_nightly_summary_latest.json`
- `btc_1d_paper_nightly_summary_md_latest.md`

## Current Read

- carry: `PASS`
- survivability: `PASS`
- walk-forward: `PASS`
- friction `20bps`: `PASS`
- ETH cross-check: `0/4 PASS`

Interpretation:

- suitable for `BTC-only` shadow or paper tracking
- not suitable as a general multi-asset crypto baseline

## Quick Validation Checklist

After each run, confirm:

1. `shadow_packet.status == "carryable_candidate"`
2. `shadow_packet.shadow_decision == "shadow_ready_for_btc_only"`
3. `shadow_packet.paper_validation_decision == "PASS"`
4. `shadow_packet.survivability_validation_decision == "PASS"`
5. `shadow_packet.walk_forward.passed == true`
6. `shadow_packet.friction_validation_heaviest_level.decision == "PASS"`
7. `shadow_packet.eth_regression_summary.pass_rate == 0.0`

## Key Numbers To Watch

- carry Sharpe / CAGR / MDD
- survivability Sharpe / CAGR / MDD
- walk-forward OOS Sharpe
- walk-forward sensitivity drift
- friction `20bps` decision
- ETH `2200` and `2600` failure details

## Failure Interpretation

Stop and inspect the new artifacts if any of the following happens:

- carry drops below `PASS`
- survivability drops below `PASS`
- walk-forward no longer passes
- unstable parameters become non-empty
- friction `20bps` no longer passes
- ETH unexpectedly starts passing without an intentional strategy change
