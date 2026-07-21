# BTC 1d Operator Dashboard

- Dashboard ready: `False`
- Candidate: `low_vol_cap_050_025_minvol020_p2200`
- Shadow decision: `shadow_ready_for_btc_only`
- Practical status: `btc_only_practical_with_caveats`
- Quick-read contract partitioned: `True`
- Contract health aligned: `False`
- Execution contract aligned: `True`
- Paper execution contract aligned: `False`
- Paper ledger consistent: `False`
- Paper exit duplicate run: `False`

## Development
- Project direction: `ops hardening`
- Current work: `candidate=low_vol_cap_050_025_minvol020_p2200 | practical_status=btc_only_practical_with_caveats | shadow_decision=shadow_ready_for_btc_only | research_stack=BTC 1d research stack | frontier=ratio112_tighter_stop_main | cagr=42.43% | mdd=16.09% | sharpe=1.5613 | backup=ratio111_tighter_stop_backup | backup_drift=0.4172 | defensive=volatility_expansion_pullthrough_shorter_hold (candidate_stage_hold) | next_near_miss=trend_dip_reversal_breakout_tighter_stop_mid_hold (validated_fail_hold)`
- Next actions: `contract_health drift recovery | paper execution contract alignment recovery | paper ledger consistency recovery`

## Performance
- Carry: `PASS` | sharpe `1.16798884` | cagr `0.143529` | mdd `0.10931171`
- Survivability: `PASS` | sharpe `1.14501096` | cagr `0.15303622` | mdd `0.13213551`
- Walk-forward: `passed=True` | oos_sharpe `0.82219649` | oos_cagr `0.05588628` | oos_mdd `0.06155691`
- Friction: `continue` | bps `20.0` | sharpe `1.04850218`
- ETH cross-check: `ETHUSDT` | pass_rate `0.0`

## Overview
- Combined health: `BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=volatility_expansion_reclaim_lower_atr_window_tighter_stop | sharpe=1.3946 | cagr=37.72% | mdd=16.09% | caveats=4 || BTC 1d research stack | frontier=ratio112_tighter_stop_main | cagr=42.43% | mdd=16.09% | sharpe=1.5613 | backup=ratio111_tighter_stop_backup | backup_drift=0.4172 | defensive=volatility_expansion_pullthrough_shorter_hold (candidate_stage_hold) | next_near_miss=trend_dip_reversal_breakout_tighter_stop_mid_hold (validated_fail_hold)`
- Research stack: `BTC 1d research stack | frontier=ratio112_tighter_stop_main | cagr=42.43% | mdd=16.09% | sharpe=1.5613 | backup=ratio111_tighter_stop_backup | backup_drift=0.4172 | defensive=volatility_expansion_pullthrough_shorter_hold (candidate_stage_hold) | next_near_miss=trend_dip_reversal_breakout_tighter_stop_mid_hold (validated_fail_hold)`
- Contract health line: `BTC 1d contract health | operating_brief=operating_v3 | operating_index=operating_v3 | aligned=True | research=research_stack_v2 | distinct=True | partitioned=True | standard_order_aligned=True | health_order_aligned=True | standard_order=practical > research > contract > brief`
- Execution contract health: `BTC 1d practical health | status=btc_only_practical_with_caveats | ok=True | candidate=volatility_expansion_reclaim_lower_atr_window_tighter_stop | sharpe=1.3946 | cagr=37.72% | mdd=16.09% | caveats=4 || BTC 1d research stack | frontier=ratio112_tighter_stop_main | cagr=42.43% | mdd=16.09% | sharpe=1.5613 | backup=ratio111_tighter_stop_backup | backup_drift=0.4172 | defensive=volatility_expansion_pullthrough_shorter_hold (candidate_stage_hold) | next_near_miss=trend_dip_reversal_breakout_tighter_stop_mid_hold (validated_fail_hold) || BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0 || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`
- Execution contract read: `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`

## Paper Execution
- Paper execution read: `paper execution | track=operating | applied=1 | closed=1 | open=0`
- intent_count: `1`
- signed_request_count: `1`
- paper_applied_count: `1`
- paper_duplicate_count: `None`
- paper_closed_count: `1`
- paper_open_count: `0`
- paper_ledger_snapshot_read: ``

## Contracts
- quick_read_operating_contract_aligned: `True`
- quick_read_paper_execution_contract_aligned: `False`
- quick_read_contract_health_aligned: `False`
- execution_contract_paper_ledger_snapshot_summary_aligned: `False`
- execution_contract_paper_execution_contract_aligned_summary_aligned: `False`

## Artifacts
- latest_summary_json: `analysis_results\btc_1d_latest_summary_latest.json`
- operating_index_json: `analysis_results\btc_1d_operating_index_latest.json`
- operating_brief_json: `analysis_results\btc_1d_operating_brief_latest.json`
- quick_read_contract_json: `analysis_results\btc_1d_quick_read_contract_screen_latest.json`
- execution_contract_json: `analysis_results\btc_1d_execution_contract_screen_latest.json`
- paper_nightly_summary_json: `analysis_results\btc_1d_paper_nightly_summary_latest.json`

## Attention
- shadow_decision=shadow_ready_for_btc_only
- contract_health=drifted
- paper_execution_contract=drifted
- paper_ledger=inconsistent