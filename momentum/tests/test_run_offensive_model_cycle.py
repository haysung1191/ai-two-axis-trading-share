from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from tools.analysis import run_offensive_model_cycle as cycle_mod


def test_build_model_cycle_payload() -> None:
    payload = cycle_mod.build_model_cycle_payload(
        screening_row_count=30,
        filtered_row_count=10,
        shortlist_count=5,
        act_now_count=3,
        validate_now_count=2,
        output_dir="output/offensive_screener_cycle",
        operator_snapshot={
            "guard_status": "stable",
            "operator_headline": "act_now=3; validate_now=2; watch_hot=1; risk_hot=0; data_quality=0; top_focus=focus_type=promotion_watch; code=402340; name=Alpha",
            "operator_scan": {
                "state_scan": "act_now=3; validate_now=2; hot_watch=402340; live_risk=327260; guard=stable",
                "promotion_scan": "hot_code=402340; hot_name=Alpha; hot_gate=confirmation; hot_action=check volume confirmation | warm_code=007810; warm_name=Beta; warm_gate=confirmation; warm_action=keep warm watch on volume confirmation",
                "defense_scan": "code=327260; name=Gamma; risk_status=warm; weakest_signal=breakout_ready; action=verify breakout hold",
                "primary_call_scan": "focus_type=promotion_check; code=402340; gate_blocker=confirmation; action=check volume confirmation",
                "priority_scan": "top_focus=promotion_check:402340; gate_blocker=confirmation; action=check volume confirmation; reason=closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2",
                "runbook_scan": "rank=1; step_type=promotion_check; code=402340; gate_blocker=confirmation; action=check volume confirmation | rank=2; step_type=promotion_backup; code=007810; gate_blocker=confirmation; action=keep warm watch on volume confirmation | rank=3; step_type=defense_watch; code=327260; gate_blocker=cleared; action=verify breakout hold",
                "compare_scan": "mode=ordered; leader=402340; challenger=007810",
                "risk_compare_scan": "mode=single; leader=327260; challenger=none",
                "live_scan": "act_now_live: live=1, dormant=0 | act_now_dormant: none",
                "guard_scan": "status=stable; breaches=none; quality=unknown; note=none",
                "cycle_diff_labels": "previous=none; current=none",
                "cycle_guard_context": "status=none; previous=none; current=none",
                "guard_delta_scan": "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none",
                "quality_scan": "status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00",
                "data_quality_focus_scan": "data_quality_guard: count=0, status=unknown",
                "latest_update_scan": "status=none; reason=none",
            },
            "operator_steps": [
                {"step_rank": 1, "step_type": "promotion_check", "Code": "402340", "Name": "Alpha", "gate_blocker": "confirmation", "action": "check volume confirmation"},
                {"step_rank": 2, "step_type": "promotion_backup", "Code": "007810", "Name": "Beta", "gate_blocker": "confirmation", "action": "keep warm watch on volume confirmation"},
                {"step_rank": 3, "step_type": "defense_watch", "Code": "327260", "Name": "Gamma", "gate_blocker": "cleared", "action": "verify breakout hold"},
            ],
            "hot_promotion_watch": "402340 Alpha",
            "hot_promotion_watch_code": "402340",
            "hot_promotion_watch_name": "Alpha",
            "hot_promotion_watch_review_label": "promoted_core",
            "hot_promotion_watch_gate_status": "needs 1 more confirmation signal for act-now",
            "hot_promotion_watch_gate_status_short": "needs 1 more confirmation signal for act-now",
            "hot_promotion_watch_gap_summary": "none",
            "hot_promotion_watch_gate_blocker": "confirmation",
            "hot_promotion_watch_action": "check volume confirmation",
            "hot_promotion_watch_reason": "closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2",
            "warm_promotion_watch": "007810 Beta",
            "warm_promotion_watch_code": "007810",
            "warm_promotion_watch_name": "Beta",
            "warm_promotion_watch_review_label": "promoted_core",
            "warm_promotion_watch_gate_status": "needs 1 more confirmation signal for act-now",
            "warm_promotion_watch_gate_status_short": "needs 1 more confirmation signal for act-now",
            "warm_promotion_watch_gap_summary": "none",
            "warm_promotion_watch_gate_blocker": "confirmation",
            "warm_promotion_watch_action": "keep warm watch on volume confirmation",
            "warm_promotion_watch_reason": "closest_path=volume_support gap=1.16; total_gap=7.16; confirmations=1/2",
            "primary_defense_watch": "327260 Gamma",
            "primary_defense_watch_code": "327260",
            "primary_defense_watch_name": "Gamma",
            "primary_defense_watch_review_label": "core_leader",
            "primary_defense_watch_gate_status": "already_cleared",
            "primary_defense_watch_gate_blocker": "cleared",
            "primary_defense_watch_action": "verify breakout hold",
            "primary_defense_watch_reason": "weakest_margin=0.5, demotion_edge=breaks_first_on=breakout_ready margin=0.5",
            "primary_call_type": "promotion_check",
            "primary_call_code": "402340",
            "primary_call_reason": "closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2",
            "primary_call": "check volume confirmation on 402340 Alpha",
            "primary_call_review_label": "promoted_core",
            "primary_call_gate_status": "needs 1 more confirmation signal for act-now",
            "primary_call_gate_status_short": "needs 1 more confirmation signal for act-now",
            "primary_call_gap_summary": "none",
            "primary_call_gate_blocker": "confirmation",
            "watch_summary": "hot=1; warm=1",
            "compare_summary": "402340 Alpha leads 007810 Beta",
            "compare_summary_contract": "mode=ordered; leader=402340; challenger=007810",
            "risk_compare_summary": "single act-now candidate remains: 327260 Gamma",
            "risk_compare_summary_contract": "mode=single; leader=327260; challenger=none",
            "live_summary": "act_now_live: live=1, dormant=0",
            "dormant_summary": "act_now_dormant: none",
            "data_quality_summary": "status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00",
            "validate_gate_summary": "review_label=0; confirmation=2; cleared=0; other=0",
                "validate_gate_lineup": "code=402340; review_label=promoted_core; gate_blocker=confirmation | code=007810; review_label=promoted_core; gate_blocker=confirmation",
            "act_now_gate_summary": "review_label=0; confirmation=0; cleared=1; other=0",
                "act_now_gate_lineup": "code=327260; review_label=core_leader; gate_blocker=cleared; risk_status=warm",
            "act_now_live_count": 1,
            "act_now_dormant_count": 0,
            "act_now_live_gate_summary": "review_label=0; confirmation=0; cleared=1; other=0",
                "act_now_live_gate_lineup": "code=327260; review_label=core_leader; gate_blocker=cleared; risk_status=warm",
            "validate_now_members": [
                {"Code": "402340", "Name": "Alpha", "review_label": "promoted_core", "gate_blocker": "confirmation", "gate_status": "needs 1 more confirmation signal for act-now", "gap_summary": "none", "promotion_watch_status": "hot", "promotion_watch_summary": "hot: nearest_gap=0.52, primary_gap=volume_support", "promotion_readiness_score": 98.72, "next_gate_summary": "needs 1 more confirmation signal for act-now"},
                {"Code": "007810", "Name": "Beta", "review_label": "promoted_core", "gate_blocker": "confirmation", "gate_status": "needs 1 more confirmation signal for act-now", "gap_summary": "none", "promotion_watch_status": "warm", "promotion_watch_summary": "warm: nearest_gap=1.16, primary_gap=volume_support", "promotion_readiness_score": 52.77, "next_gate_summary": "needs 1 more confirmation signal for act-now"},
            ],
            "act_now_members": [
                {"Code": "327260", "Name": "Gamma", "review_label": "core_leader", "gate_blocker": "cleared", "gate_status": "already_cleared", "gap_summary": "none", "act_now_risk_status": "warm", "act_now_risk_summary": "warm: weakest_margin=0.5, weakest_signal=breakout_ready", "next_gate_summary": "already_cleared"},
            ],
            "act_now_live_members": [
                {"Code": "327260", "Name": "Gamma", "review_label": "core_leader", "gate_blocker": "cleared", "gate_status": "already_cleared", "gap_summary": "none", "act_now_risk_status": "warm", "act_now_risk_summary": "warm: weakest_margin=0.5, weakest_signal=breakout_ready", "next_gate_summary": "already_cleared"},
            ],
            "validate_competition_summary": "mode=ordered; leader=402340; challenger=007810; nearest_gap_edge=0.64; total_gap_edge=4.64; readiness_edge=45.95",
            "validate_competition_rationale": "mode=ordered; leader=402340; challenger=007810; ordering_basis=nearest_gap_then_total_gap_then_readiness; leader_primary_gap=volume_support; leader_nearest_gap=0.52; leader_total_gap=2.52; challenger_primary_gap=volume_support; challenger_nearest_gap=1.16; challenger_total_gap=7.16; nearest_gap_edge=0.64; total_gap_edge=4.64; readiness_edge=45.95",
            "validate_competition_leader_code": "402340",
            "validate_competition_challenger_code": "007810",
            "validate_competition_nearest_gap_edge": 0.64,
            "validate_competition_total_gap_edge": 4.64,
            "validate_competition_readiness_edge": 45.95,
            "validate_competition_leader_primary_gap": "volume_support",
            "validate_competition_leader_nearest_gap": 0.52,
            "validate_competition_leader_total_gap": 2.52,
            "validate_competition_leader_next_gate": "needs 1 more confirmation signal for act-now",
            "validate_competition_leader_gap_summary": "none",
            "validate_competition_challenger_primary_gap": "volume_support",
            "validate_competition_challenger_nearest_gap": 1.16,
            "validate_competition_challenger_total_gap": 7.16,
            "validate_competition_challenger_next_gate": "needs 1 more confirmation signal for act-now",
            "validate_competition_challenger_gap_summary": "none",
            "act_now_competition_summary": "mode=single; leader=327260; challenger=none",
            "act_now_competition_rationale": "mode=single; leader=327260; challenger=none; ordering_basis=only_act_now_candidate; leader_risk_status=warm; leader_weakest_signal=breakout_ready; leader_weakest_margin=0.50",
            "act_now_competition_leader_code": "327260",
            "act_now_competition_challenger_code": "none",
            "act_now_competition_margin_edge": "none",
            "act_now_competition_score_edge": "none",
            "act_now_competition_leader_risk_status": "warm",
            "act_now_competition_leader_weakest_signal": "breakout_ready",
            "act_now_competition_leader_weakest_margin": 0.5,
            "act_now_competition_challenger_risk_status": "off",
            "act_now_competition_challenger_weakest_signal": "none",
            "act_now_competition_challenger_weakest_margin": "none",
            "risk_summary": "hot=0; warm=1",
            "guard_scan": "status=stable; breaches=none; quality=unknown; note=none",
            "cycle_diff_labels": "previous=none; current=none",
            "cycle_guard_context": "status=none; previous=none; current=none",
            "guard_delta_summary": "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none",
            "guard_summary": "status=stable",
            "primary_call_note": "Validate-now candidate 402340 is closest to promotion on volume confirmation.",
            "operator_focuses": [
                {"focus_rank": 1, "focus_type": "promotion_watch", "Code": "402340", "Name": "Alpha", "severity": "hot", "summary": "hot: nearest_gap=0.52, primary_gap=volume_support", "review_label": "promoted_core", "gate_status": "needs 1 more confirmation signal for act-now", "gate_status_short": "needs 1 more confirmation signal for act-now", "gap_summary": "none", "gate_blocker": "confirmation", "action": "check volume confirmation", "reason": "closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2", "next_gate": "needs 1 more confirmation signal for act-now"},
                {"focus_rank": 2, "focus_type": "promotion_watch", "Code": "007810", "Name": "Beta", "severity": "warm", "summary": "warm: nearest_gap=1.16, primary_gap=volume_support", "review_label": "promoted_core", "gate_status": "needs 1 more confirmation signal for act-now", "gate_status_short": "needs 1 more confirmation signal for act-now", "gap_summary": "none", "gate_blocker": "confirmation", "action": "keep warm watch on volume confirmation", "reason": "closest_path=volume_support gap=1.16; total_gap=7.16; confirmations=1/2", "next_gate": "needs 1 more confirmation signal for act-now"},
                {"focus_rank": 3, "focus_type": "act_now_risk", "Code": "327260", "Name": "Gamma", "severity": "warm", "summary": "warm: weakest_margin=0.5, weakest_signal=breakout_ready", "review_label": "core_leader", "gate_status": "already_cleared", "gate_status_short": "already_cleared", "gap_summary": "none", "gate_blocker": "cleared", "action": "verify breakout hold", "reason": "weakest_margin=0.5, demotion_edge=breaks_first_on=breakout_ready margin=0.5", "next_gate": "already_cleared"},
            ],
        },
    )

    assert payload["screening_row_count"] == 30
    assert payload["filtered_row_count"] == 10
    assert payload["act_now_count"] == 3
    assert payload["validate_now_count"] == 2
    assert payload["operator_snapshot"]["guard_status"] == "stable"
    assert payload["screening_quality"] == {}
    assert payload["operator_snapshot"]["operator_headline"].startswith("act_now=3")
    assert payload["operator_snapshot"]["operator_scan"]["state_scan"] == "act_now=3; validate_now=2; hot_watch=402340; live_risk=327260; guard=stable"
    assert payload["operator_snapshot"]["operator_scan"]["priority_scan"] == "top_focus=promotion_check:402340; gate_blocker=confirmation; action=check volume confirmation; reason=closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2"
    assert payload["operator_snapshot"]["operator_scan"]["runbook_scan"].startswith("rank=1; step_type=promotion_check; code=402340; gate_blocker=confirmation")
    assert payload["operator_snapshot"]["operator_scan"]["compare_scan"] == "mode=ordered; leader=402340; challenger=007810"
    assert payload["operator_snapshot"]["operator_scan"]["risk_compare_scan"] == "mode=single; leader=327260; challenger=none"
    assert payload["operator_snapshot"]["operator_scan"]["live_scan"] == "act_now_live: live=1, dormant=0 | act_now_dormant: none"
    assert payload["operator_snapshot"]["operator_scan"]["guard_scan"] == "status=stable; breaches=none; quality=unknown; note=none"
    assert payload["operator_snapshot"]["operator_scan"]["cycle_diff_labels"] == "previous=none; current=none"
    assert payload["operator_snapshot"]["operator_scan"]["cycle_guard_context"] == "status=none; previous=none; current=none"
    assert payload["operator_snapshot"]["operator_scan"]["guard_delta_scan"] == "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none"
    assert payload["operator_snapshot"]["operator_scan"]["quality_scan"] == "status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00"
    assert payload["operator_snapshot"]["operator_scan"]["data_quality_focus_scan"] == "data_quality_guard: count=0, status=unknown"
    assert payload["operator_snapshot"]["operator_scan"]["latest_update_scan"] == "status=none; reason=none"
    assert payload["operator_snapshot"]["operator_steps"][0]["Code"] == "402340"
    assert payload["operator_snapshot"]["hot_promotion_watch_code"] == "402340"
    assert payload["operator_snapshot"]["hot_promotion_watch_review_label"] == "promoted_core"
    assert payload["operator_snapshot"]["hot_promotion_watch_gate_blocker"] == "confirmation"
    assert payload["operator_snapshot"]["validate_gate_summary"].startswith("review_label=")
    assert payload["operator_snapshot"]["act_now_gate_summary"].startswith("review_label=")
    assert payload["operator_snapshot"]["validate_now_members"][0]["Code"] == "402340"
    assert payload["operator_snapshot"]["act_now_members"][0]["Code"] == "327260"
    assert payload["operator_snapshot"]["act_now_live_count"] == 1
    assert payload["operator_snapshot"]["act_now_dormant_count"] == 0
    assert payload["operator_snapshot"]["act_now_live_gate_summary"] == "review_label=0; confirmation=0; cleared=1; other=0"
    assert payload["operator_snapshot"]["act_now_live_gate_lineup"] == "code=327260; review_label=core_leader; gate_blocker=cleared; risk_status=warm"
    assert payload["operator_snapshot"]["act_now_live_members"][0]["Code"] == "327260"
    assert payload["operator_snapshot"]["cycle_diff_labels"] == "previous=none; current=none"
    assert payload["operator_snapshot"]["cycle_guard_context"] == "status=none; previous=none; current=none"
    assert payload["operator_snapshot"]["primary_call_type"] == "promotion_check"
    assert payload["operator_snapshot"]["primary_call_gate_blocker"] == "confirmation"
    assert payload["operator_snapshot"]["hot_promotion_watch_reason"].startswith("closest_path=")
    assert payload["operator_snapshot"]["operator_focuses"][0]["focus_type"] == "promotion_watch"
    assert payload["operator_snapshot"]["operator_focuses"][0]["severity"] == "hot"
    assert payload["operator_snapshot"]["operator_focuses"][0]["review_label"] == "promoted_core"
    assert payload["operator_snapshot"]["operator_focuses"][0]["gate_blocker"] == "confirmation"
    assert payload["operator_snapshot"]["operator_focuses"][0]["next_gate"] == "needs 1 more confirmation signal for act-now"
    rendered = cycle_mod.render_model_cycle(payload)
    assert "cycle_diff_labels=previous:none; current:none" in rendered
    assert "cycle_guard_context=status:none; previous:none; current:none" in rendered
    assert "operator_headline=act_now=3; validate_now=2; watch_hot=1; risk_hot=0; data_quality=0; top_focus=focus_type=promotion_watch; code=402340; name=Alpha" in rendered
    assert "state_scan=act_now=3; validate_now=2; hot_watch=402340; live_risk=327260; guard=stable" in rendered
    assert "promotion_scan=hot_code=402340; hot_name=Alpha; hot_gate=confirmation; hot_action=check volume confirmation | warm_code=007810; warm_name=Beta; warm_gate=confirmation; warm_action=keep warm watch on volume confirmation" in rendered
    assert "defense_scan=code=327260; name=Gamma; risk_status=warm; weakest_signal=breakout_ready; action=verify breakout hold" in rendered
    assert "primary_call_scan=focus_type=promotion_check; code=402340; gate_blocker=confirmation; action=check volume confirmation" in rendered
    assert "priority_scan=top_focus=promotion_check:402340; gate_blocker=confirmation; action=check volume confirmation; reason=closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2" in rendered
    assert "runbook_scan=rank=1; step_type=promotion_check; code=402340; gate_blocker=confirmation; action=check volume confirmation | rank=2; step_type=promotion_backup; code=007810; gate_blocker=confirmation; action=keep warm watch on volume confirmation | rank=3; step_type=defense_watch; code=327260; gate_blocker=cleared; action=verify breakout hold" in rendered
    assert "compare_scan=mode=ordered; leader=402340; challenger=007810" in rendered
    assert "risk_compare_scan=mode=single; leader=327260; challenger=none" in rendered
    assert "live_scan=act_now_live: live=1, dormant=0 | act_now_dormant: none" in rendered
    assert "guard_scan=status=stable; breaches=none; quality=unknown; note=none" in rendered
    assert "cycle_diff_labels=previous:none; current:none" in rendered
    assert "cycle_guard_context=status:none; previous:none; current:none" in rendered
    assert "guard_delta_scan=previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none" in rendered
    assert "quality_scan=status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00" in rendered
    assert "data_quality_focus_scan=data_quality_guard: count=0, status=unknown" in rendered
    assert "latest_update_scan=status=none; reason=none" in rendered
    assert "validate_now_brief=code=402340; name=Alpha; watch_status=hot; gate_blocker=confirmation | code=007810; name=Beta; watch_status=warm; gate_blocker=confirmation" in rendered
    assert "act_now_brief=code=327260; name=Gamma; risk_status=warm; gate_blocker=cleared" in rendered
    assert "act_now_live_summary=live=1; dormant=0" in rendered
    assert "act_now_live_brief=code=327260; name=Gamma; risk_status=warm; gate_blocker=cleared" in rendered
    assert "watch_summary=hot=1; warm=1" in rendered
    assert "compare_summary=402340 Alpha leads 007810 Beta" in rendered
    assert "compare_summary_contract=mode=ordered; leader=402340; challenger=007810" in rendered
    assert "risk_compare_summary=single act-now candidate remains: 327260 Gamma" in rendered
    assert "risk_compare_summary_contract=mode=single; leader=327260; challenger=none" in rendered
    assert "live_summary=act_now_live: live=1, dormant=0" in rendered
    assert "dormant_summary=act_now_dormant: none" in rendered
    assert "data_quality_summary=status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00" in rendered
    assert "validate_gate_summary=review_label=0; confirmation=2; cleared=0; other=0" in rendered
    assert "validate_gate_lineup=code=402340; review_label=promoted_core; gate_blocker=confirmation | code=007810; review_label=promoted_core; gate_blocker=confirmation" in rendered
    assert "act_now_gate_summary=review_label=0; confirmation=0; cleared=1; other=0" in rendered
    assert "act_now_gate_lineup=code=327260; review_label=core_leader; gate_blocker=cleared; risk_status=warm" in rendered
    assert "act_now_live_gate_summary=review_label=0; confirmation=0; cleared=1; other=0" in rendered
    assert "act_now_live_gate_lineup=code=327260; review_label=core_leader; gate_blocker=cleared; risk_status=warm" in rendered
    assert "validate_now_member_1=code=402340; name=Alpha; review_label=promoted_core; gate_blocker=confirmation; watch_status=hot; readiness=98.72; summary=hot: nearest_gap=0.52, primary_gap=volume_support; next_gate=needs 1 more confirmation signal for act-now; gap_summary=none" in rendered
    assert "validate_now_member_2=code=007810; name=Beta; review_label=promoted_core; gate_blocker=confirmation; watch_status=warm; readiness=52.77; summary=warm: nearest_gap=1.16, primary_gap=volume_support; next_gate=needs 1 more confirmation signal for act-now; gap_summary=none" in rendered
    assert "act_now_member_1=code=327260; name=Gamma; review_label=core_leader; gate_blocker=cleared; risk_status=warm; risk_summary=warm: weakest_margin=0.5, weakest_signal=breakout_ready; next_gate=already_cleared" in rendered
    assert "act_now_live_member_1=code=327260; name=Gamma; review_label=core_leader; gate_blocker=cleared; risk_status=warm; risk_summary=warm: weakest_margin=0.5, weakest_signal=breakout_ready; next_gate=already_cleared" in rendered
    assert "screening_quality=status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00" in rendered
    assert "screening_quality_codes=empty_price=none; invalid_momentum=none" in rendered
    assert "validate_competition=mode=ordered; leader=402340; challenger=007810; nearest_gap_edge=0.64; total_gap_edge=4.64; readiness_edge=45.95" in rendered
    assert "validate_competition_rationale=mode=ordered; leader=402340; challenger=007810; ordering_basis=nearest_gap_then_total_gap_then_readiness; leader_primary_gap=volume_support; leader_nearest_gap=0.52; leader_total_gap=2.52; challenger_primary_gap=volume_support; challenger_nearest_gap=1.16; challenger_total_gap=7.16; nearest_gap_edge=0.64; total_gap_edge=4.64; readiness_edge=45.95" in rendered
    assert "validate_competition_basis=leader=402340; leader_primary_gap=volume_support; leader_nearest_gap=0.52; leader_total_gap=2.52; leader_next_gate=needs 1 more confirmation signal for act-now; leader_gap_summary=none; challenger=007810; challenger_primary_gap=volume_support; challenger_nearest_gap=1.16; challenger_total_gap=7.16; challenger_next_gate=needs 1 more confirmation signal for act-now; challenger_gap_summary=none; nearest_gap_edge=0.64; total_gap_edge=4.64; readiness_edge=45.95" in rendered
    assert "act_now_competition=mode=single; leader=327260; challenger=none" in rendered
    assert "act_now_competition_rationale=mode=single; leader=327260; challenger=none; ordering_basis=only_act_now_candidate; leader_risk_status=warm; leader_weakest_signal=breakout_ready; leader_weakest_margin=0.50" in rendered
    assert "act_now_competition_basis=leader=327260; leader_risk_status=warm; leader_weakest_signal=breakout_ready; leader_weakest_margin=0.50; challenger=none; challenger_risk_status=off; challenger_weakest_signal=none; challenger_weakest_margin=none; margin_edge=none; score_edge=none" in rendered
    assert "risk_summary=hot=0; warm=1" in rendered
    assert "guard_summary=status=stable" in rendered
    assert "guard_delta_summary=previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none" in rendered
    assert "hot_promotion_review_label=promoted_core" in rendered
    assert "hot_promotion_gate_blocker=confirmation" in rendered
    assert "hot_promotion_gap_summary=none" in rendered
    assert "primary_call_review_label=promoted_core" in rendered
    assert "primary_call_gate_blocker=confirmation" in rendered
    assert "primary_call_gap_summary=none" in rendered
    assert "hot_promotion_action=check volume confirmation" in rendered
    assert "warm_promotion_action=keep warm watch on volume confirmation" in rendered
    assert "primary_defense_action=verify breakout hold" in rendered
    assert "primary_call_note=Validate-now candidate 402340 is closest to promotion on volume confirmation." in rendered
    assert "operator_focuses=rank=1; type=promotion_watch; code=402340; severity=hot; review_label=promoted_core; gate_blocker=confirmation; action=check volume confirmation; summary=hot: nearest_gap=0.52, primary_gap=volume_support; next_gate=needs 1 more confirmation signal for act-now; gap_summary=none" in rendered
    assert "operator_focus_1=type=promotion_watch; code=402340; severity=hot; review_label=promoted_core; gate_blocker=confirmation; action=check volume confirmation; summary=hot: nearest_gap=0.52, primary_gap=volume_support; next_gate=needs 1 more confirmation signal for act-now; gap_summary=none" in rendered
    assert "operator_focus_2=type=promotion_watch; code=007810; severity=warm; review_label=promoted_core; gate_blocker=confirmation; action=keep warm watch on volume confirmation; summary=warm: nearest_gap=1.16, primary_gap=volume_support; next_gate=needs 1 more confirmation signal for act-now; gap_summary=none" in rendered
    assert "operator_step_1=type=promotion_check; code=402340; name=Alpha; gate_blocker=confirmation; action=check volume confirmation" in rendered
    assert "operator_step_2=type=promotion_backup; code=007810; name=Beta; gate_blocker=confirmation; action=keep warm watch on volume confirmation" in rendered


def test_operator_snapshot_primary_call_tracks_top_focus_when_defense_leads() -> None:
    payload = cycle_mod._operator_snapshot_from_handoff(
        {
            "operator_board": {
                "headline": "act_now=3, validate_now=1, watch_hot=0, risk_hot=2, top_focus=act_now_risk:006400 Alpha",
                "primary_call": "verify volume confirmation on 006400 Alpha",
                "watch_summary": "promotion_watch: hot=0, warm=1",
                "compare_summary": "single validate-now candidate remains: 402340 Beta",
                "risk_compare_summary": "act-now defense order: 006400 Alpha -> 080220 Gamma",
                "risk_summary": "act_now_risk: hot=2, warm=1",
                "guard_summary": "cycle_guard=review",
                "data_quality_focus_summary": "data_quality_guard: count=0, status=unknown",
            },
            "operator_runbook": [
                {"step_type": "promotion_check", "Code": "402340", "Name": "Beta", "action": "check volume confirmation", "reason": "closest_path=volume_support gap=1.17; total_gap=6.17; confirmations=1/2"},
                {"step_type": "defense_watch", "Code": "006400", "Name": "Alpha", "action": "verify volume confirmation", "reason": "weakest_margin=0.1, demotion_edge=breaks_first_on=volume_support margin=0.1"},
            ],
            "focus_queue": [
                {"focus_rank": 1, "focus_type": "act_now_risk", "Code": "006400", "Name": "Alpha", "severity": "hot", "summary": "hot: weakest_margin=0.1, weakest_signal=volume_support", "operator_action": "verify volume confirmation", "operator_note": "Act-now candidate 006400 is still live, but its thinnest support is volume confirmation."},
                {"focus_rank": 2, "focus_type": "promotion_watch", "Code": "402340", "Name": "Beta", "severity": "warm", "summary": "warm: nearest_gap=1.17, primary_gap=volume_support", "operator_action": "check volume confirmation", "operator_note": "Validate-now candidate 402340 is closest to promotion on volume confirmation."},
            ],
            "validate_now": [
                {
                    "Code": "402340",
                    "Name": "Beta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now; gaps=large_rank_upgrade: current=2.00, threshold=7.00, gap=5.00, volume_support: current=3.83, threshold=5.00, gap=1.17",
                    "promotion_watch_status": "warm",
                    "promotion_watch_summary": "warm: nearest_gap=1.17, primary_gap=volume_support",
                    "promotion_readiness_score": 61.96,
                    "act_now_risk_status": "off",
                }
            ],
            "act_now": [
                {
                    "Code": "006400",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "hot",
                    "act_now_risk_summary": "hot: weakest_margin=0.1, weakest_signal=volume_support",
                    "weakest_met_signal": "volume_support",
                }
            ],
        },
        {"guard_status": "review"},
    )

    assert payload["primary_call"] == "verify volume confirmation on 006400 Alpha"
    assert payload["primary_call_type"] == "act_now_risk"
    assert payload["primary_call_code"] == "006400"
    assert payload["primary_call_review_label"] == "promoted_core"
    assert payload["primary_call_gate_blocker"] == "cleared"
    assert payload["primary_call_note"].startswith("Act-now candidate 006400")
    assert payload["primary_call_reason"] == "weakest_margin=0.1, demotion_edge=breaks_first_on=volume_support margin=0.1"
    assert payload["operator_scan"]["primary_call_scan"] == "focus_type=act_now_risk; code=006400; gate_blocker=cleared; action=verify volume confirmation"
    assert payload["operator_scan"]["priority_scan"] == "top_focus=act_now_risk:006400; gate_blocker=cleared; action=verify volume confirmation; reason=weakest_margin=0.1, demotion_edge=breaks_first_on=volume_support margin=0.1"
    assert payload["operator_scan"]["cycle_diff_labels"] == "previous=none; current=none"
    assert payload["operator_scan"]["cycle_guard_context"] == "status=review; previous=none; current=none"
    assert payload["operator_scan"]["quality_scan"] == "status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00"
    assert payload["operator_scan"]["latest_update_scan"] == "status=none; reason=none"
    assert payload["validate_competition_leader_code"] == "402340"
    assert payload["validate_competition_leader_primary_gap"] == "none"
    assert payload["validate_competition_leader_next_gate"] == "needs 1 more confirmation signal for act-now"
    assert payload["validate_competition_leader_gap_summary"].startswith("large_rank_upgrade:")
    assert payload["validate_now_members"][0]["gate_status"] == "needs 1 more confirmation signal for act-now"
    assert payload["validate_now_members"][0]["gap_summary"].startswith("large_rank_upgrade:")
    assert payload["operator_focuses"][1]["gate_status_short"] == "needs 1 more confirmation signal for act-now"
    assert payload["operator_focuses"][1]["gap_summary"].startswith("large_rank_upgrade:")
    assert payload["act_now_competition_leader_code"] == "006400"
    assert payload["act_now_competition_leader_risk_status"] == "hot"
    assert payload["act_now_competition_leader_weakest_signal"] == "volume_support"
    rendered = cycle_mod.render_model_cycle({"operator_snapshot": payload})
    assert "validate_competition_basis=leader=402340; leader_primary_gap=none; leader_nearest_gap=none; leader_total_gap=none; leader_next_gate=needs 1 more confirmation signal for act-now; leader_gap_summary=large_rank_upgrade: current=2.00, threshold=7.00, gap=5.00, volume_support: current=3.83, threshold=5.00, gap=1.17; challenger=none; challenger_primary_gap=none; challenger_nearest_gap=none; challenger_total_gap=none; challenger_next_gate=none; challenger_gap_summary=none; nearest_gap_edge=none; total_gap_edge=none; readiness_edge=none" in rendered
    assert "validate_now_member_1=code=402340; name=Beta; review_label=promoted_core; gate_blocker=confirmation; watch_status=warm; readiness=61.96; summary=warm: nearest_gap=1.17, primary_gap=volume_support; next_gate=needs 1 more confirmation signal for act-now; gap_summary=large_rank_upgrade: current=2.00, threshold=7.00, gap=5.00, volume_support: current=3.83, threshold=5.00, gap=1.17" in rendered
    assert "operator_focus_2=type=promotion_watch; code=402340; severity=warm; review_label=promoted_core; gate_blocker=confirmation; action=check volume confirmation; summary=warm: nearest_gap=1.17, primary_gap=volume_support; next_gate=needs 1 more confirmation signal for act-now; gap_summary=large_rank_upgrade: current=2.00, threshold=7.00, gap=5.00, volume_support: current=3.83, threshold=5.00, gap=1.17" in rendered
    assert "act_now_competition_basis=leader=006400; leader_risk_status=hot; leader_weakest_signal=volume_support; leader_weakest_margin=0.10; challenger=none; challenger_risk_status=off; challenger_weakest_signal=none; challenger_weakest_margin=none; margin_edge=none; score_edge=none" in rendered
    assert payload["operator_focuses"][0]["focus_type"] == "act_now_risk"
    assert payload["operator_focuses"][0]["Code"] == "006400"
    assert payload["operator_focuses"][1]["focus_type"] == "promotion_watch"
    assert payload["operator_focuses"][1]["Code"] == "402340"


def test_operator_snapshot_watch_slots_follow_actual_hot_and_warm_severity() -> None:
    payload = cycle_mod._operator_snapshot_from_handoff(
        {
            "operator_board": {
                "headline": "act_now=3, validate_now=1, watch_hot=0, risk_hot=2, top_focus=act_now_risk:006400 Alpha",
                "primary_call": "verify volume confirmation on 006400 Alpha",
                "watch_summary": "promotion_watch: hot=0, warm=1",
                "compare_summary": "single validate-now candidate remains: 402340 Beta",
                "risk_compare_summary": "act-now defense order: 006400 Alpha -> 080220 Gamma",
                "risk_summary": "act_now_risk: hot=2, warm=1",
                "guard_summary": "cycle_guard=stable",
            },
            "operator_runbook": [
                {"step_type": "promotion_check", "Code": "402340", "Name": "Beta", "action": "check volume confirmation", "reason": "closest_path=volume_support gap=1.16; total_gap=6.16; confirmations=1/2"},
                {"step_type": "defense_watch", "Code": "006400", "Name": "Alpha", "action": "verify volume confirmation", "reason": "weakest_margin=0.13, demotion_edge=breaks_first_on=volume_support margin=0.13"},
            ],
            "focus_queue": [
                {"focus_rank": 1, "focus_type": "act_now_risk", "Code": "006400", "Name": "Alpha", "severity": "hot", "summary": "hot: weakest_margin=0.13, weakest_signal=volume_support", "operator_action": "verify volume confirmation", "operator_note": "Act-now candidate 006400 is still live."},
                {"focus_rank": 2, "focus_type": "promotion_watch", "Code": "402340", "Name": "Beta", "severity": "warm", "summary": "warm: nearest_gap=1.16, primary_gap=volume_support", "operator_action": "check volume confirmation", "operator_note": "Validate-now candidate 402340 is closest to promotion on volume confirmation."},
            ],
            "validate_now": [
                {
                    "Code": "402340",
                    "Name": "Beta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now",
                    "promotion_watch_status": "warm",
                    "promotion_watch_summary": "warm: nearest_gap=1.16, primary_gap=volume_support",
                    "promotion_readiness_score": 62.07,
                    "act_now_risk_status": "off",
                }
            ],
            "act_now": [
                {
                    "Code": "006400",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "hot",
                    "act_now_risk_summary": "hot: weakest_margin=0.13, weakest_signal=volume_support",
                    "weakest_met_signal": "volume_support",
                }
            ],
        },
        {"guard_status": "stable"},
    )

    assert payload["operator_scan"]["state_scan"] == "act_now=1; validate_now=1; hot_watch=none; live_risk=006400; guard=stable; dormant=none"
    assert payload["operator_scan"]["promotion_scan"] == "hot_code=none; hot_name=none; hot_gate=active; hot_action=none | warm_code=402340; warm_name=Beta; warm_gate=confirmation; warm_action=check volume confirmation"
    assert payload["operator_scan"]["guard_scan"] == "status=stable; breaches=none; quality=unknown; note=none"
    assert payload["operator_scan"]["quality_scan"] == "status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00"
    assert payload["operator_scan"]["data_quality_focus_scan"] == "data_quality_guard: count=0, status=unknown"
    assert payload["operator_scan"]["latest_update_scan"] == "status=none; reason=none"
    assert payload["hot_promotion_watch"] == "none"
    assert payload["hot_promotion_watch_code"] == "none"
    assert payload["hot_promotion_watch_action"] == "none"
    assert payload["warm_promotion_watch"] == "402340 Beta"
    assert payload["warm_promotion_watch_code"] == "402340"
    assert payload["warm_promotion_watch_gate_blocker"] == "confirmation"
    assert payload["operator_headline"] == "act_now=1; validate_now=1; watch_hot=0; risk_hot=1; data_quality=0; top_focus=focus_type=act_now_risk; code=006400; name=Alpha"
    assert payload["watch_summary"] == "hot=0; warm=1"
    assert payload["data_quality_focus_summary"] == "data_quality_guard: count=0, status=unknown"
    assert payload["risk_summary"] == "hot=1; warm=0"
    assert payload["guard_summary"] == "cycle_guard=stable"
    assert payload["guard_scan"] == "status=stable; breaches=none; quality=unknown; note=none"
    assert payload["guard_breach_summary"] == "none"
    assert payload["guard_quality_status"] == "unknown"


def test_operator_snapshot_operator_focuses_keep_full_focus_queue_order() -> None:
    payload = cycle_mod._operator_snapshot_from_handoff(
        {
            "operator_board": {
                "headline": "act_now=3, validate_now=1, watch_hot=0, risk_hot=1, top_focus=act_now_risk:080220 Gamma",
                "primary_call": "verify rank follow-through on 080220 Gamma",
                "watch_summary": "promotion_watch: hot=0, warm=1",
                "compare_summary": "single validate-now candidate remains: 402340 Beta",
                "risk_compare_summary": "act-now defense order: 080220 Gamma -> 006400 Alpha -> 095610 Delta",
                "risk_summary": "act_now_risk: hot=1, warm=2",
                "guard_summary": "cycle_guard=stable",
                "data_quality_focus_summary": "data_quality_guard: count=0, status=unknown",
            },
            "operator_runbook": [
                {"step_type": "promotion_check", "Code": "402340", "Name": "Beta", "action": "check volume confirmation", "reason": "closest_path=volume_support gap=1.14; total_gap=6.14; confirmations=1/2"},
                {"step_type": "defense_watch", "Code": "080220", "Name": "Gamma", "action": "verify rank follow-through", "reason": "weakest_margin=0.0, demotion_edge=breaks_first_on=large_rank_upgrade margin=0.0"},
            ],
            "focus_queue": [
                {"focus_rank": 1, "focus_type": "act_now_risk", "Code": "080220", "Name": "Gamma", "severity": "hot", "summary": "hot: weakest_margin=0.0, weakest_signal=large_rank_upgrade", "next_gate_summary": "promoted_core gate passed with confirmation_count=2/2; met=large_rank_upgrade,volume_support", "operator_action": "verify rank follow-through", "operator_note": "Act-now candidate 080220 is still live."},
                {"focus_rank": 2, "focus_type": "promotion_watch", "Code": "402340", "Name": "Beta", "severity": "warm", "summary": "warm: nearest_gap=1.14, primary_gap=volume_support", "next_gate_summary": "needs 1 more confirmation signal for act-now", "operator_action": "check volume confirmation", "operator_note": "Validate-now candidate 402340 is closest to promotion on volume confirmation."},
                {"focus_rank": 3, "focus_type": "act_now_risk", "Code": "006400", "Name": "Alpha", "severity": "warm", "summary": "warm: weakest_margin=0.16, weakest_signal=volume_support", "next_gate_summary": "promoted_core gate passed with confirmation_count=3/2; met=large_rank_upgrade,volume_support,breakout_ready", "operator_action": "verify volume confirmation", "operator_note": "Act-now candidate 006400 is still live."},
                {"focus_rank": 4, "focus_type": "act_now_risk", "Code": "095610", "Name": "Delta", "severity": "warm", "summary": "warm: weakest_margin=0.26, weakest_signal=breakout_ready", "next_gate_summary": "promoted_core gate passed with confirmation_count=2/2; met=large_rank_upgrade,breakout_ready", "operator_action": "verify breakout hold", "operator_note": "Act-now candidate 095610 is still live."},
            ],
            "validate_now": [
                {
                    "Code": "402340",
                    "Name": "Beta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now",
                    "promotion_watch_status": "warm",
                    "promotion_watch_summary": "warm: nearest_gap=1.14, primary_gap=volume_support",
                    "promotion_readiness_score": 62.27,
                }
            ],
            "act_now": [
                {
                    "Code": "080220",
                    "Name": "Gamma",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "hot",
                    "act_now_risk_summary": "hot: weakest_margin=0.0, weakest_signal=large_rank_upgrade",
                    "weakest_met_signal": "large_rank_upgrade",
                },
                {
                    "Code": "006400",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.16, weakest_signal=volume_support",
                    "weakest_met_signal": "volume_support",
                },
                {
                    "Code": "095610",
                    "Name": "Delta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.26, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                }
            ],
        },
        {"guard_status": "stable"},
    )

    assert [row["Code"] for row in payload["operator_focuses"]] == ["080220", "402340", "006400", "095610"]
    assert payload["operator_focuses"][0]["focus_type"] == "act_now_risk"
    assert payload["operator_focuses"][2]["focus_type"] == "act_now_risk"
    assert payload["operator_focuses"][3]["Code"] == "095610"
    assert [row["Code"] for row in payload["act_now_members"]] == ["080220", "006400", "095610"]


def test_operator_snapshot_gate_lineups_follow_focus_priority_order() -> None:
    payload = cycle_mod._operator_snapshot_from_handoff(
        {
            "operator_board": {
                "headline": "act_now=3, validate_now=2, watch_hot=1, risk_hot=1, top_focus=promotion_watch:402340 Beta",
                "primary_call": "check volume confirmation on 402340 Beta",
                "watch_summary": "promotion_watch: hot=1, warm=1",
                "compare_summary": "402340 Beta leads 007810 Epsilon",
                "risk_compare_summary": "act-now defense order: 080220 Gamma -> 006400 Alpha -> 095610 Delta",
                "risk_summary": "act_now_risk: hot=1, warm=2",
                "guard_summary": "cycle_guard=stable",
            },
            "operator_runbook": [
                {"step_type": "promotion_check", "Code": "402340", "Name": "Beta", "action": "check volume confirmation", "reason": "closest_path=volume_support gap=1.12; total_gap=5.12; confirmations=1/2"},
                {"step_type": "promotion_backup", "Code": "007810", "Name": "Epsilon", "action": "keep warm watch on volume confirmation", "reason": "closest_path=volume_support gap=1.85; total_gap=6.85; confirmations=1/2"},
                {"step_type": "defense_watch", "Code": "080220", "Name": "Gamma", "action": "verify rank follow-through", "reason": "weakest_margin=0.0, demotion_edge=breaks_first_on=large_rank_upgrade margin=0.0"},
            ],
            "focus_queue": [
                {"focus_rank": 1, "focus_type": "promotion_watch", "Code": "402340", "Name": "Beta", "severity": "hot", "summary": "hot: nearest_gap=1.12, primary_gap=volume_support", "operator_action": "check volume confirmation", "operator_note": "Validate-now candidate 402340 is closest to promotion on volume confirmation."},
                {"focus_rank": 2, "focus_type": "promotion_watch", "Code": "007810", "Name": "Epsilon", "severity": "warm", "summary": "warm: nearest_gap=1.85, primary_gap=volume_support", "operator_action": "keep warm watch on volume confirmation", "operator_note": "Validate-now candidate 007810 remains secondary."},
                {"focus_rank": 3, "focus_type": "act_now_risk", "Code": "080220", "Name": "Gamma", "severity": "hot", "summary": "hot: weakest_margin=0.0, weakest_signal=large_rank_upgrade", "operator_action": "verify rank follow-through", "operator_note": "Act-now candidate 080220 is still live."},
                {"focus_rank": 4, "focus_type": "act_now_risk", "Code": "006400", "Name": "Alpha", "severity": "warm", "summary": "warm: weakest_margin=0.25, weakest_signal=volume_support", "operator_action": "verify volume confirmation", "operator_note": "Act-now candidate 006400 is still live."},
                {"focus_rank": 5, "focus_type": "act_now_risk", "Code": "095610", "Name": "Delta", "severity": "warm", "summary": "warm: weakest_margin=0.21, weakest_signal=breakout_ready", "operator_action": "verify breakout hold", "operator_note": "Act-now candidate 095610 is still live."},
            ],
            "validate_now": [
                {
                    "Code": "007810",
                    "Name": "Epsilon",
                    "review_label": "promoted_core",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now",
                    "promotion_watch_status": "warm",
                    "promotion_watch_summary": "warm: nearest_gap=1.85, primary_gap=volume_support",
                    "promotion_readiness_score": 61.03,
                    "validate_priority_rank": 2,
                },
                {
                    "Code": "402340",
                    "Name": "Beta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now",
                    "promotion_watch_status": "hot",
                    "promotion_watch_summary": "hot: nearest_gap=1.12, primary_gap=volume_support",
                    "promotion_readiness_score": 72.47,
                    "validate_priority_rank": 1,
                },
            ],
            "act_now": [
                {
                    "Code": "006400",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.25, weakest_signal=volume_support",
                    "weakest_met_signal": "volume_support",
                    "offensive_rank": 2,
                },
                {
                    "Code": "095610",
                    "Name": "Delta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.21, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                    "offensive_rank": 5,
                },
                {
                    "Code": "080220",
                    "Name": "Gamma",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "hot",
                    "act_now_risk_summary": "hot: weakest_margin=0.0, weakest_signal=large_rank_upgrade",
                    "weakest_met_signal": "large_rank_upgrade",
                    "offensive_rank": 6,
                },
            ],
        },
        {"guard_status": "stable"},
    )

    assert [row["Code"] for row in payload["validate_now_members"]] == ["402340", "007810"]
    assert [row["Code"] for row in payload["act_now_members"]] == ["080220", "006400", "095610"]
    assert [row["Code"] for row in payload["act_now_live_members"]] == ["080220", "006400", "095610"]
    assert payload["validate_gate_lineup"] == "code=402340; review_label=promoted_core; gate_blocker=confirmation | code=007810; review_label=promoted_core; gate_blocker=confirmation"
    assert payload["act_now_gate_lineup"] == "code=080220; review_label=promoted_core; gate_blocker=cleared; risk_status=hot | code=006400; review_label=promoted_core; gate_blocker=cleared; risk_status=warm | code=095610; review_label=promoted_core; gate_blocker=cleared; risk_status=warm"
    assert payload["operator_headline"] == "act_now=3; validate_now=2; watch_hot=1; risk_hot=1; data_quality=0; top_focus=focus_type=promotion_watch; code=402340; name=Beta"
    assert payload["watch_summary"] == "hot=1; warm=1"
    assert payload["data_quality_focus_summary"] == "data_quality_guard: count=0, status=unknown"
    assert payload["validate_gate_summary"] == "review_label=0; confirmation=2; cleared=0; other=0"
    assert payload["act_now_gate_summary"] == "review_label=0; confirmation=0; cleared=3; other=0"
    assert payload["act_now_live_count"] == 3
    assert payload["act_now_dormant_count"] == 0
    assert payload["act_now_live_gate_summary"] == "review_label=0; confirmation=0; cleared=3; other=0"
    assert payload["act_now_live_gate_lineup"] == "code=080220; review_label=promoted_core; gate_blocker=cleared; risk_status=hot | code=006400; review_label=promoted_core; gate_blocker=cleared; risk_status=warm | code=095610; review_label=promoted_core; gate_blocker=cleared; risk_status=warm"
    assert payload["risk_summary"] == "hot=1; warm=2"
    assert payload["guard_summary"] == "cycle_guard=stable"
    assert payload["guard_scan"] == "status=stable; breaches=none; quality=unknown; note=none"
    assert payload["guard_breach_summary"] == "none"
    assert payload["guard_quality_status"] == "unknown"
    assert payload["validate_competition_leader_code"] == "402340"
    assert payload["validate_competition_challenger_code"] == "007810"
    assert payload["validate_competition_leader_primary_gap"] == "none"
    assert payload["validate_competition_challenger_primary_gap"] == "none"
    assert payload["validate_competition_leader_gap_summary"] == "none"
    assert payload["validate_competition_challenger_gap_summary"] == "none"
    assert payload["validate_competition_nearest_gap_edge"] == 0.0
    assert payload["validate_competition_total_gap_edge"] == 0.0
    assert payload["act_now_competition_leader_code"] == "080220"
    assert payload["act_now_competition_challenger_code"] == "006400"
    assert payload["act_now_competition_leader_risk_status"] == "hot"
    assert payload["act_now_competition_challenger_risk_status"] == "warm"
    assert payload["act_now_competition_leader_weakest_signal"] == "large_rank_upgrade"
    assert payload["act_now_competition_challenger_weakest_signal"] == "volume_support"
    assert payload["act_now_competition_margin_edge"] == 0.25
    assert payload["act_now_competition_score_edge"] == 0.0

    rendered = cycle_mod.render_model_cycle({"operator_snapshot": payload})
    assert "operator_headline=act_now=3; validate_now=2; watch_hot=1; risk_hot=1; data_quality=0; top_focus=focus_type=promotion_watch; code=402340; name=Beta" in rendered
    assert "validate_now_brief=code=402340; name=Beta; watch_status=hot; gate_blocker=confirmation | code=007810; name=Epsilon; watch_status=warm; gate_blocker=confirmation" in rendered
    assert "act_now_brief=code=080220; name=Gamma; risk_status=hot; gate_blocker=cleared | code=006400; name=Alpha; risk_status=warm; gate_blocker=cleared | code=095610; name=Delta; risk_status=warm; gate_blocker=cleared" in rendered
    assert "act_now_live_summary=live=3; dormant=0" in rendered
    assert "act_now_live_brief=code=080220; name=Gamma; risk_status=hot; gate_blocker=cleared | code=006400; name=Alpha; risk_status=warm; gate_blocker=cleared | code=095610; name=Delta; risk_status=warm; gate_blocker=cleared" in rendered
    assert "watch_summary=hot=1; warm=1" in rendered
    assert "data_quality_focus_summary=data_quality_guard: count=0, status=unknown" in rendered
    assert "validate_gate_summary=review_label=0; confirmation=2; cleared=0; other=0" in rendered
    assert "validate_gate_lineup=code=402340; review_label=promoted_core; gate_blocker=confirmation | code=007810; review_label=promoted_core; gate_blocker=confirmation" in rendered
    assert "act_now_gate_summary=review_label=0; confirmation=0; cleared=3; other=0" in rendered
    assert "act_now_gate_lineup=code=080220; review_label=promoted_core; gate_blocker=cleared; risk_status=hot | code=006400; review_label=promoted_core; gate_blocker=cleared; risk_status=warm | code=095610; review_label=promoted_core; gate_blocker=cleared; risk_status=warm" in rendered
    assert "act_now_live_gate_summary=review_label=0; confirmation=0; cleared=3; other=0" in rendered
    assert "act_now_live_gate_lineup=code=080220; review_label=promoted_core; gate_blocker=cleared; risk_status=hot | code=006400; review_label=promoted_core; gate_blocker=cleared; risk_status=warm | code=095610; review_label=promoted_core; gate_blocker=cleared; risk_status=warm" in rendered
    assert "risk_summary=hot=1; warm=2" in rendered
    assert "act_now_live_member_1=code=080220; name=Gamma; review_label=promoted_core; gate_blocker=cleared; risk_status=hot; risk_summary=hot: weakest_margin=0.0, weakest_signal=large_rank_upgrade; next_gate=already_cleared" in rendered
    assert "guard_summary=cycle_guard=stable" in rendered
    assert "guard_scan=status=stable; breaches=none; quality=unknown; note=none" in rendered
    assert "guard_breach_summary=none" in rendered
    assert "guard_quality_status=unknown" in rendered
    assert rendered.count("guard_scan=status=stable; breaches=none; quality=unknown; note=none") == 1


def test_operator_snapshot_splits_live_act_now_subset_from_dormant_members() -> None:
    payload = cycle_mod._operator_snapshot_from_handoff(
        {
            "operator_board": {
                "headline": "act_now=3, validate_now=1, watch_hot=0, risk_hot=0, top_focus=promotion_watch:402340 Beta",
                "primary_call": "check volume confirmation on 402340 Beta",
                "watch_summary": "promotion_watch: hot=0, warm=1",
                "compare_summary": "single validate-now candidate remains: 402340 Beta",
                "risk_compare_summary": "act-now defense order: 006400 Alpha -> 095610 Delta",
                "risk_summary": "act_now_risk: hot=0, warm=2",
                "guard_summary": "cycle_guard=stable",
                "data_quality_focus_summary": "data_quality_guard: count=0, status=unknown",
            },
            "operator_runbook": [
                {"step_type": "promotion_check", "Code": "402340", "Name": "Beta", "action": "check volume confirmation", "reason": "closest_path=volume_support gap=0.87; total_gap=6.87; confirmations=1/2"},
                {"step_type": "defense_watch", "Code": "006400", "Name": "Alpha", "action": "verify breakout hold", "reason": "weakest_margin=0.5, demotion_edge=breaks_first_on=breakout_ready margin=0.50"},
                {"step_type": "dormant_watch", "Code": "080220", "Name": "Gamma", "action": "recover breakout hold", "reason": "breakout_ready: current=9.21, threshold=9.50, gap=0.29"},
            ],
            "focus_queue": [
                {"focus_rank": 1, "focus_type": "promotion_watch", "Code": "402340", "Name": "Beta", "severity": "warm", "summary": "warm: nearest_gap=0.87, primary_gap=volume_support", "next_gate_summary": "needs 1 more confirmation signal for act-now", "operator_action": "check volume confirmation", "operator_note": "Validate-now candidate 402340 is closest to promotion on volume confirmation."},
                {"focus_rank": 2, "focus_type": "act_now_risk", "Code": "006400", "Name": "Alpha", "severity": "warm", "summary": "warm: weakest_margin=0.5, weakest_signal=breakout_ready", "next_gate_summary": "promoted_core gate passed with confirmation_count=3/2; met=large_rank_upgrade,volume_support,breakout_ready", "operator_action": "verify breakout hold", "operator_note": "Act-now candidate 006400 is still live."},
                {"focus_rank": 3, "focus_type": "act_now_risk", "Code": "095610", "Name": "Delta", "severity": "warm", "summary": "warm: weakest_margin=0.3, weakest_signal=breakout_ready", "next_gate_summary": "promoted_core gate passed with confirmation_count=2/2; met=large_rank_upgrade,breakout_ready", "operator_action": "verify breakout hold", "operator_note": "Act-now candidate 095610 is still live."},
                {"focus_rank": 4, "focus_type": "act_now_dormant", "Code": "080220", "Name": "Gamma", "severity": "dormant", "summary": "dormant: primary_gap=breakout_ready, nearest_gap=0.29", "next_gate_summary": "breakout_ready: current=9.21, threshold=9.50, gap=0.29", "operator_action": "recover breakout readiness", "operator_note": "Act-now candidate 080220 is currently dormant, and the closest re-activation trigger is breakout readiness."},
            ],
            "validate_now": [
                {
                    "Code": "402340",
                    "Name": "Beta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now; gaps=large_rank_upgrade: current=1.00, threshold=7.00, gap=6.00, volume_support: current=4.13, threshold=5.00, gap=0.87",
                    "promotion_watch_status": "warm",
                    "promotion_watch_summary": "warm: nearest_gap=0.87, primary_gap=volume_support",
                    "promotion_readiness_score": 54.97,
                    "act_now_risk_status": "off",
                }
            ],
            "act_now": [
                {
                    "Code": "006400",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.5, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                    "offensive_rank": 1,
                },
                {
                    "Code": "095610",
                    "Name": "Delta",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.3, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                    "offensive_rank": 4,
                },
                {
                    "Code": "080220",
                    "Name": "Gamma",
                    "review_label": "promoted_core",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "off",
                    "act_now_risk_summary": "none",
                    "weakest_met_signal": "large_rank_upgrade",
                    "offensive_rank": 5,
                },
            ],
        },
        {"guard_status": "stable"},
    )

    assert [row["Code"] for row in payload["act_now_members"]] == ["006400", "095610", "080220"]
    assert [row["Code"] for row in payload["act_now_live_members"]] == ["006400", "095610"]
    assert [row["Code"] for row in payload["act_now_dormant_members"]] == ["080220"]
    assert payload["act_now_live_count"] == 2
    assert payload["act_now_dormant_count"] == 1
    assert payload["act_now_dormant_brief"] == "code=080220; name=Gamma; gate_blocker=cleared"
    assert payload["act_now_gate_summary"] == "review_label=0; confirmation=0; cleared=3; other=0"
    assert payload["act_now_live_gate_summary"] == "review_label=0; confirmation=0; cleared=2; other=0"
    assert payload["act_now_live_gate_lineup"] == "code=006400; review_label=promoted_core; gate_blocker=cleared; risk_status=warm | code=095610; review_label=promoted_core; gate_blocker=cleared; risk_status=warm"
    assert payload["operator_scan"]["state_scan"] == "act_now=3; validate_now=1; hot_watch=none; live_risk=006400; guard=stable; dormant=080220"
    assert payload["operator_scan"]["runbook_scan"] == "rank=1; step_type=promotion_check; code=402340; gate_blocker=confirmation; action=check volume confirmation | rank=2; step_type=defense_watch; code=006400; gate_blocker=cleared; action=verify breakout hold | rank=3; step_type=dormant_watch; code=080220; gate_blocker=cleared; action=recover breakout hold"
    assert payload["operator_scan"]["quality_scan"] == "status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00"
    assert payload["operator_scan"]["data_quality_focus_scan"] == "data_quality_guard: count=0, status=unknown"
    assert payload["operator_scan"]["latest_update_scan"] == "status=none; reason=none"
    assert payload["operator_steps"][2]["step_type"] == "dormant_watch"
    assert payload["operator_steps"][2]["Code"] == "080220"

    rendered = cycle_mod.render_model_cycle({"operator_snapshot": payload})
    assert "state_scan=act_now=3; validate_now=1; hot_watch=none; live_risk=006400; guard=stable; dormant=080220" in rendered
    assert "runbook_scan=rank=1; step_type=promotion_check; code=402340; gate_blocker=confirmation; action=check volume confirmation | rank=2; step_type=defense_watch; code=006400; gate_blocker=cleared; action=verify breakout hold | rank=3; step_type=dormant_watch; code=080220; gate_blocker=cleared; action=recover breakout hold" in rendered
    assert "quality_scan=status=unknown; attempted=0; fetched=0; valid=0; empty_price=0; invalid_momentum=0; fetch_coverage=0.00; success_coverage=0.00" in rendered
    assert "data_quality_focus_scan=data_quality_guard: count=0, status=unknown" in rendered
    assert "latest_update_scan=status=none; reason=none" in rendered
    assert "act_now_live_summary=live=2; dormant=1" in rendered
    assert "act_now_live_brief=code=006400; name=Alpha; risk_status=warm; gate_blocker=cleared | code=095610; name=Delta; risk_status=warm; gate_blocker=cleared" in rendered
    assert "act_now_dormant_brief=code=080220; name=Gamma; gate_blocker=cleared" in rendered
    assert "operator_focus_4=type=act_now_dormant; code=080220; severity=dormant; review_label=promoted_core; gate_blocker=cleared; action=recover breakout readiness; summary=dormant: primary_gap=breakout_ready, nearest_gap=0.29; next_gate=already_cleared; gap_summary=none" in rendered
    assert "act_now_live_gate_summary=review_label=0; confirmation=0; cleared=2; other=0" in rendered
    assert "act_now_live_gate_lineup=code=006400; review_label=promoted_core; gate_blocker=cleared; risk_status=warm | code=095610; review_label=promoted_core; gate_blocker=cleared; risk_status=warm" in rendered
    assert "act_now_live_member_1=code=006400; name=Alpha; review_label=promoted_core; gate_blocker=cleared; risk_status=warm; risk_summary=warm: weakest_margin=0.5, weakest_signal=breakout_ready; next_gate=already_cleared" in rendered


def test_sync_readme_thread_handoff_text_updates_snapshot_blocks() -> None:
    original = """## Thread Handoff

### Latest Verified Offensive State

Latest offensive cycle artifacts were regenerated on `2026-04-21 13:47`:

Latest verified headline state:

- `screening_row_count = 30`
- `filtered_row_count = 25`
- `shortlist_count = 5`
- `act_now_count = 3`
- `validate_now_count = 1`
- `operator_headline = act_now=3; validate_now=1; watch_hot=0; risk_hot=0; data_quality=0; top_focus=promotion_watch:402340 Alpha`
- `compare_scan = mode=single; leader=402340; challenger=none`
- `risk_compare_scan = mode=ordered; leader=006400; challenger=095610; margin_edge=-0.19; score_edge=8.62`
- `live_scan = act_now_live: live=2, dormant=1 | act_now_dormant: 080220 Gamma`
- `guard_scan = status=stable; breaches=none; quality=unknown; note=none`
- `guard_status = stable`
- `guard_breach_summary = none`
- `guard_quality_status = unknown`

Latest verified top focus:

- warm promotion watch: `402340`
- hot promotion watch: `none`
- hot act-now risk names: `none`
- warm act-now risk names: `006400`, `095610`
- dormant act-now names: `080220`
- dormant act-now action: `recover breakout hold`
- dormant act-now gap: `breakout_ready: current=9.21, threshold=9.50, gap=0.29`
- guard breach summary: `none`
- guard quality status: `unknown`
- guard quality summary: `none`
- primary call: `check volume confirmation on 402340 Alpha`
- primary call reason: `closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2`
- runbook next actions: `promotion_check:402340:check volume confirmation | defense_watch:006400:verify breakout hold | dormant_watch:080220:recover breakout hold`

### New Thread Starter Prompt

```text
理쒓렐 offensive ?곹깭:
- act_now=3
- validate_now=1
- act_now_live=2
- act_now_dormant=1
- hot promotion watch=none
- warm promotion watch=402340
- hot act-now risk=none
- warm act-now risk=006400,095610
- dormant act-now=080220
- dormant act-now action=recover breakout hold
- dormant act-now gap=breakout_ready: current=9.21, threshold=9.50, gap=0.29
- guard breach summary=none
- guard quality status=unknown
- operator headline=act_now=3; validate_now=1; watch_hot=0; risk_hot=0; data_quality=0; top_focus=promotion_watch:402340 Alpha
- compare scan=mode=single; leader=402340; challenger=none
- risk compare scan=mode=ordered; leader=006400; challenger=095610; margin_edge=-0.19; score_edge=8.62
- live scan=act_now_live: live=2, dormant=1 | act_now_dormant: 080220 Gamma
- guard scan=status=stable; breaches=none; quality=unknown; note=none
- primary call=check volume confirmation on 402340 Alpha
- primary call reason=closest_path=volume_support gap=0.52; total_gap=2.52; confirmations=1/2
- next actions=promotion_check:402340:check volume confirmation | defense_watch:006400:verify breakout hold | dormant_watch:080220:recover breakout hold
- operator board? focus queue媛 ?대? 遺숈뼱 ?덉쓬
- validate/act-now competition summary? rationale? root cycle怨?handoff summary ?묒そ 紐⑤몢 key-value contract濡??뺣젹???덉쓬
```
"""
    cycle_payload = {
        "screening_row_count": 31,
        "filtered_row_count": 26,
        "shortlist_count": 6,
        "act_now_count": 2,
        "validate_now_count": 2,
        "screening_quality": {
            "quality_status": "caution",
            "quality_summary": "attempted=38; fetched=31; valid=31; empty_price=7; invalid_momentum=0; fetch_coverage=0.82; success_coverage=0.82",
            "empty_price_codes_sample": ["111111", "222222"],
            "invalid_momentum_codes_sample": [],
        },
        "latest_update": {
            "status": "advance_latest",
        },
        "operator_snapshot": {
            "guard_status": "review",
            "operator_headline": "act_now=2; validate_now=2; watch_hot=1; risk_hot=1; data_quality=0; top_focus=act_now_risk:006400 삼성SDI",
            "guard_breach_summary": "screening_quality_review",
            "guard_quality_status": "review",
            "guard_quality_summary": "status=review; attempted=38; fetched=31; valid=31; empty_price=7; invalid_momentum=0; fetch_coverage=0.82; success_coverage=0.82",
            "primary_call": "verify breakout hold on 006400 삼성SDI",
            "primary_call_reason": "weakest_margin=0.14, demotion_edge=breaks_first_on=breakout_ready margin=0.14",
                "operator_scan": {
                    "compare_scan": "mode=ordered; leader=007810; challenger=402340; nearest_gap_edge=0.51; total_gap_edge=3.22; readiness_edge=8.50",
                    "risk_compare_scan": "mode=ordered; leader=006400; challenger=095610; margin_edge=-0.14; score_edge=6.10",
                    "live_scan": "act_now_live: live=2, dormant=1 | act_now_dormant: 080220 제주반도체",
                    "guard_scan": "status=review; breaches=screening_quality_review; quality=review; note=Screening quality fell enough to require review.",
                    "guard_delta_scan": "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none",
                },
            "hot_promotion_watch_code": "007810",
            "warm_promotion_watch_code": "402340",
            "act_now_members": [
                {"Code": "006400", "act_now_risk_status": "hot"},
                {"Code": "095610", "act_now_risk_status": "warm"},
                {"Code": "080220", "act_now_risk_status": "off"},
            ],
            "operator_focuses": [
                {
                    "focus_type": "act_now_dormant",
                    "Code": "080220",
                    "action": "recover breakout hold",
                    "reason": "breakout_ready: current=9.21, threshold=9.50, gap=0.29",
                }
            ],
            "operator_steps": [
                {"step_type": "promotion_check", "Code": "402340", "action": "check volume confirmation"},
                {"step_type": "defense_watch", "Code": "006400", "action": "verify breakout hold"},
                {"step_type": "dormant_watch", "Code": "080220", "action": "recover breakout hold"},
            ],
        },
    }

    updated, replaced_sections = cycle_mod._sync_readme_thread_handoff_text(
        original,
        refreshed_at="2026-04-21 14:05",
        cycle_payload=cycle_payload,
    )

    assert replaced_sections == {
        "artifact_timestamp": True,
        "headline_state": True,
        "top_focus": True,
        "starter_prompt_state": True,
    }
    assert "Latest offensive cycle artifacts were regenerated on `2026-04-21 14:05`:" in updated
    assert "- `screening_row_count = 31`" in updated
    assert "- `filtered_row_count = 26`" in updated
    assert "- `shortlist_count = 6`" in updated
    assert "- `act_now_count = 2`" in updated
    assert "- `validate_now_count = 2`" in updated
    assert "- `act_now_live_count = 2`" in updated
    assert "- `act_now_dormant_count = 1`" in updated
    assert "- `screening_quality = attempted=38; fetched=31; valid=31; empty_price=7; invalid_momentum=0; fetch_coverage=0.82; success_coverage=0.82`" in updated
    assert "- `screening_quality_status = caution`" in updated
    assert "- `latest_update_status = advance_latest`" in updated
    assert "- `latest_update_reason = none`" in updated
    assert "- `guard_status = review`" in updated
    assert "- `operator_headline = act_now=2; validate_now=2; watch_hot=1; risk_hot=1; data_quality=0; top_focus=act_now_risk:006400 삼성SDI`" in updated
    assert "- `compare_scan = mode=ordered; leader=007810; challenger=402340; nearest_gap_edge=0.51; total_gap_edge=3.22; readiness_edge=8.50`" in updated
    assert "- `risk_compare_scan = mode=ordered; leader=006400; challenger=095610; margin_edge=-0.14; score_edge=6.10`" in updated
    assert "- `live_scan = act_now_live: live=2, dormant=1 | act_now_dormant: 080220 제주반도체`" in updated
    assert "- `guard_scan = status=review; breaches=screening_quality_review; quality=review; note=Screening quality fell enough to require review.`" in updated
    assert "- `cycle_diff_labels = previous=none; current=none`" in updated
    assert "- `cycle_guard_context = status=none; previous=none; current=none`" in updated
    assert "- `guard_delta_scan = previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none`" in updated
    assert "- `guard_breach_summary = screening_quality_review`" in updated
    assert "- `guard_quality_status = review`" in updated
    assert "- warm promotion watch: `402340`" in updated
    assert "- hot promotion watch: `007810`" in updated
    assert "- hot act-now risk names: `006400`" in updated
    assert "- warm act-now risk names: `095610`" in updated
    assert "- dormant act-now names: `080220`" in updated
    assert "- dormant act-now action: `recover breakout hold`" in updated
    assert "- dormant act-now gap: `breakout_ready: current=9.21, threshold=9.50, gap=0.29`" in updated
    assert "- screening quality codes: `empty_price=111111,222222; invalid_momentum=none`" in updated
    assert "- guard breach summary: `screening_quality_review`" in updated
    assert "- guard quality status: `review`" in updated
    assert "- guard quality summary: `status=review; attempted=38; fetched=31; valid=31; empty_price=7; invalid_momentum=0; fetch_coverage=0.82; success_coverage=0.82`" in updated
    assert "- primary call: `verify breakout hold on 006400 삼성SDI`" in updated
    assert "- primary call reason: `weakest_margin=0.14, demotion_edge=breaks_first_on=breakout_ready margin=0.14`" in updated
    assert "- runbook next actions: `promotion_check:402340:check volume confirmation | defense_watch:006400:verify breakout hold | dormant_watch:080220:recover breakout hold`" in updated
    assert "- act_now=2" in updated
    assert "- validate_now=2" in updated
    assert "- act_now_live=2" in updated
    assert "- act_now_dormant=1" in updated
    assert "- screening quality=attempted=38; fetched=31; valid=31; empty_price=7; invalid_momentum=0; fetch_coverage=0.82; success_coverage=0.82" in updated
    assert "- screening quality status=caution" in updated
    assert "- guard breach summary=screening_quality_review" in updated
    assert "- guard quality status=review" in updated
    assert "- operator headline=act_now=2; validate_now=2; watch_hot=1; risk_hot=1; data_quality=0; top_focus=act_now_risk:006400 삼성SDI" in updated
    assert "- compare scan=mode=ordered; leader=007810; challenger=402340; nearest_gap_edge=0.51; total_gap_edge=3.22; readiness_edge=8.50" in updated
    assert "- risk compare scan=mode=ordered; leader=006400; challenger=095610; margin_edge=-0.14; score_edge=6.10" in updated
    assert "- live scan=act_now_live: live=2, dormant=1 | act_now_dormant: 080220 제주반도체" in updated
    assert "- guard scan=status=review; breaches=screening_quality_review; quality=review; note=Screening quality fell enough to require review." in updated
    assert "- primary call=verify breakout hold on 006400 삼성SDI" in updated
    assert "- primary call reason=weakest_margin=0.14, demotion_edge=breaks_first_on=breakout_ready margin=0.14" in updated
    assert "- latest update status=advance_latest" in updated
    assert "- hot promotion watch=007810" in updated
    assert "- warm promotion watch=402340" in updated
    assert "- hot act-now risk=006400" in updated
    assert "- warm act-now risk=095610" in updated
    assert "- dormant act-now=080220" in updated
    assert "- dormant act-now action=recover breakout hold" in updated
    assert "- dormant act-now gap=breakout_ready: current=9.21, threshold=9.50, gap=0.29" in updated
    assert "- next actions=promotion_check:402340:check volume confirmation | defense_watch:006400:verify breakout hold | dormant_watch:080220:recover breakout hold" in updated


def test_sync_readme_thread_handoff_text_reports_missing_markers() -> None:
    updated, replaced_sections = cycle_mod._sync_readme_thread_handoff_text(
        "## Thread Handoff\n\nNo matching sections here.\n",
        refreshed_at="2026-04-21 14:05",
        cycle_payload={
            "screening_row_count": 1,
            "filtered_row_count": 1,
            "shortlist_count": 1,
            "act_now_count": 1,
            "validate_now_count": 0,
            "operator_snapshot": {
                "guard_status": "stable",
                "hot_promotion_watch_code": "none",
                "warm_promotion_watch_code": "none",
                "act_now_members": [],
            },
        },
    )
    assert updated == "## Thread Handoff\n\nNo matching sections here.\n"
    assert replaced_sections["artifact_timestamp"] is False
    assert replaced_sections["headline_state"] is False
    assert replaced_sections["top_focus"] is False
    assert replaced_sections["starter_prompt_state"] is False


def test_sync_readme_thread_handoff_uses_cycle_stamp_for_timestamp(tmp_path: Path) -> None:
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        """## Thread Handoff

### Latest Verified Offensive State

Latest offensive cycle artifacts were regenerated on `old`:

Latest verified headline state:

- `screening_row_count = 0`
- `filtered_row_count = 0`
- `shortlist_count = 0`
- `act_now_count = 0`
- `validate_now_count = 0`
- `operator_headline = none`
- `compare_scan = none`
- `risk_compare_scan = none`
- `live_scan = none`
- `guard_scan = none`
- `guard_status = unknown`
- `guard_breach_summary = none`
- `guard_quality_status = unknown`

Latest verified top focus:

- warm promotion watch: `none`
- hot promotion watch: `none`
- hot act-now risk names: `none`
- warm act-now risk names: `none`
- guard breach summary: `none`
- guard quality status: `unknown`
- guard quality summary: `none`
- primary call: `none`
- primary call reason: `none`

### New Thread Starter Prompt

```text
理쒓렐 offensive ?곹깭:
- act_now=0
- validate_now=0
- act_now_live=0
- act_now_dormant=0
- hot promotion watch=none
- warm promotion watch=none
- hot act-now risk=none
- warm act-now risk=none
- guard breach summary=none
- guard quality status=unknown
- primary call=none
- primary call reason=none
- operator board? focus queue媛 ?대? 遺숈뼱 ?덉쓬
- validate/act-now competition summary? rationale? root cycle怨?handoff summary ?묒そ 紐⑤몢 key-value contract濡??뺣젹???덉쓬
```
""",
        encoding="utf-8",
    )
    cycle_mod._sync_readme_thread_handoff(
        readme_path,
        cycle_payload={
            "stamp": "20260421T140512",
            "screening_row_count": 30,
            "filtered_row_count": 25,
            "shortlist_count": 5,
            "act_now_count": 3,
            "validate_now_count": 1,
            "screening_quality": {
                "quality_status": "caution",
                "quality_summary": "attempted=38; fetched=30; valid=30; empty_price=8; invalid_momentum=0; fetch_coverage=0.79; success_coverage=0.79",
                "empty_price_codes_sample": ["101010"],
                "invalid_momentum_codes_sample": ["none"],
            },
            "latest_update": {
                "status": "advance_latest",
            },
            "operator_snapshot": {
                "guard_status": "stable",
                "operator_headline": "act_now=3; validate_now=1; watch_hot=0; risk_hot=0; data_quality=0; top_focus=promotion_watch:402340 SK스퀘어",
                "guard_breach_summary": "none",
                "guard_quality_status": "stable",
                "guard_quality_summary": "attempted=38; fetched=30; valid=30; empty_price=8; invalid_momentum=0; fetch_coverage=0.79; success_coverage=0.79",
                "primary_call": "check volume confirmation on 402340 SK스퀘어",
                "primary_call_reason": "closest_path=volume_support gap=0.79; total_gap=6.79; confirmations=1/2",
                "operator_scan": {
                    "compare_scan": "mode=single; leader=402340; challenger=none",
                    "risk_compare_scan": "mode=ordered; leader=006400; challenger=095610; margin_edge=-0.19; score_edge=8.62",
                    "live_scan": "act_now_live: live=2, dormant=1 | act_now_dormant: 080220 제주반도체",
                    "guard_scan": "status=stable; breaches=none; quality=stable; note=No material offensive-cycle instability detected.",
                    "guard_delta_scan": "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none",
                },
                "hot_promotion_watch_code": "none",
                "warm_promotion_watch_code": "402340",
                "act_now_members": [
                    {"Code": "006400", "act_now_risk_status": "warm"},
                    {"Code": "095610", "act_now_risk_status": "warm"},
                ],
            },
        },
    )
    updated = readme_path.read_text(encoding="utf-8")
    assert "Latest offensive cycle artifacts were regenerated on `2026-04-21 14:05`:" in updated
    assert "- `act_now_live_count = 2`" in updated
    assert "- `act_now_dormant_count = 1`" in updated
    assert "- `screening_quality = attempted=38; fetched=30; valid=30; empty_price=8; invalid_momentum=0; fetch_coverage=0.79; success_coverage=0.79`" in updated
    assert "- `screening_quality_status = caution`" in updated
    assert "- `latest_update_status = advance_latest`" in updated
    assert "- `latest_update_reason = none`" in updated
    assert "- `operator_headline = act_now=3; validate_now=1; watch_hot=0; risk_hot=0; data_quality=0; top_focus=promotion_watch:402340 SK스퀘어`" in updated
    assert "- `compare_scan = mode=single; leader=402340; challenger=none`" in updated
    assert "- `risk_compare_scan = mode=ordered; leader=006400; challenger=095610; margin_edge=-0.19; score_edge=8.62`" in updated
    assert "- `live_scan = act_now_live: live=2, dormant=1 | act_now_dormant: 080220 제주반도체`" in updated
    assert "- `guard_scan = status=stable; breaches=none; quality=stable; note=No material offensive-cycle instability detected.`" in updated
    assert "- `cycle_diff_labels = previous=none; current=none`" in updated
    assert "- `cycle_guard_context = status=none; previous=none; current=none`" in updated
    assert "- `guard_delta_scan = previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none`" in updated
    assert "- `guard_breach_summary = none`" in updated
    assert "- `guard_quality_status = stable`" in updated
    assert "- primary call: `check volume confirmation on 402340 SK스퀘어`" in updated
    assert "- primary call reason: `closest_path=volume_support gap=0.79; total_gap=6.79; confirmations=1/2`" in updated


def test_sync_readme_thread_handoff_raises_when_required_sections_are_missing(tmp_path: Path) -> None:
    readme_path = tmp_path / "README.md"
    readme_path.write_text("## Thread Handoff\n\nBroken structure.\n", encoding="utf-8")
    try:
        cycle_mod._sync_readme_thread_handoff(
            readme_path,
            cycle_payload={
                "stamp": "20260421T140512",
                "screening_row_count": 30,
                "filtered_row_count": 25,
                "shortlist_count": 5,
                "act_now_count": 3,
                "validate_now_count": 1,
                "operator_snapshot": {
                    "guard_status": "stable",
                    "hot_promotion_watch_code": "none",
                    "warm_promotion_watch_code": "402340",
                    "act_now_members": [],
                },
            },
        )
    except RuntimeError as exc:
        assert "artifact_timestamp" in str(exc)
        assert "headline_state" in str(exc)
        assert "top_focus" in str(exc)
        assert "starter_prompt_state" in str(exc)
    else:
        raise AssertionError("Expected README sync to fail when required sections are missing")


def test_main_runs_full_cycle(monkeypatch, tmp_path: Path, capsys) -> None:
    readme_sync_calls: list[tuple[Path, dict[str, object]]] = []

    class FakeScreener:
        def run(self, max_items, etf_mode, stock_sort_column):
            assert max_items == 25
            assert etf_mode is False
            assert stock_sort_column == "offensive_score"
            return pd.DataFrame(
                [
                    {
                        "Code": "007810",
                        "Name": "Alpha",
                        "offensive_score": 90.0,
                        "offensive_rank": 1,
                        "rank_delta_vs_legacy": 5,
                        "momentum_1m": 25.0,
                        "momentum_6m": 150.0,
                        "momentum_12m": 300.0,
                        "MAD_gap_pct": 60.0,
                        "volume_ratio_5d_20d": 1.2,
                        "breakout_distance_pct": -1.0,
                        "momentum_acceleration": 5.0,
                        "offensive_component_mom12": 30.0,
                        "offensive_component_mom6": 20.0,
                        "offensive_component_mom1": 12.0,
                        "offensive_component_trend": 15.0,
                        "offensive_component_breakout": 9.9,
                        "offensive_component_volume": 6.0,
                    },
                    {
                        "Code": "006400",
                        "Name": "Beta",
                        "offensive_score": 78.0,
                        "offensive_rank": 2,
                        "rank_delta_vs_legacy": 8,
                        "momentum_1m": 24.0,
                        "momentum_6m": 90.0,
                        "momentum_12m": 190.0,
                        "MAD_gap_pct": 45.0,
                        "volume_ratio_5d_20d": 1.0,
                        "breakout_distance_pct": 0.0,
                        "momentum_acceleration": 4.0,
                        "offensive_component_mom12": 23.0,
                        "offensive_component_mom6": 15.0,
                        "offensive_component_mom1": 10.0,
                        "offensive_component_trend": 14.0,
                        "offensive_component_breakout": 10.0,
                        "offensive_component_volume": 5.0,
                    },
                ]
            )

    monkeypatch.setattr(cycle_mod, "MomentumScreener", FakeScreener)
    monkeypatch.setattr(cycle_mod, "_timestamp", lambda: "20260420T010000")
    monkeypatch.setattr(
        cycle_mod,
        "_sync_readme_thread_handoff",
        lambda readme_path, *, cycle_payload: readme_sync_calls.append((readme_path, cycle_payload)),
    )
    (tmp_path / "offensive_handoff_summary_20260420T000000.json").write_text(
        json.dumps(
            {
                "act_now_count": 0,
                "validate_now_count": 1,
                "act_now": [],
                "validate_now": [{"Code": "006400", "Name": "Beta"}],
                "top_candidates": [{"Code": "006400", "Name": "Beta", "offensive_score": 70.0, "offensive_rank": 2}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/run_offensive_model_cycle.py",
            "--max-items",
            "25",
            "--top-n",
            "2",
            "--shortlist-top-n",
            "2",
            "--stock-sort-column",
            "offensive_score",
            "--output-dir",
            str(tmp_path),
        ],
    )

    cycle_mod.main()
    output = capsys.readouterr().out
    assert "Offensive Model Cycle" in output
    assert "screening_row_count=2" in output
    assert "validate_now_count=" in output
    assert "guard_status=review" in output
    assert "operator_headline=" in output
    assert "state_scan=" in output
    assert "promotion_scan=" in output
    assert "defense_scan=" in output
    assert "primary_call_scan=" in output
    assert "runbook_scan=" in output
    assert "validate_now_brief=" in output
    assert "act_now_brief=" in output
    assert "watch_summary=" in output
    assert "validate_gate_summary=" in output
    assert "validate_gate_lineup=" in output
    assert "act_now_gate_summary=" in output
    assert "act_now_gate_lineup=" in output
    assert "validate_competition=" in output
    assert "validate_competition_rationale=" in output
    assert "act_now_competition=" in output
    assert "act_now_competition_rationale=" in output
    assert "risk_summary=" in output
    assert "guard_summary=" in output
    assert "hot_promotion_review_label=" in output
    assert "hot_promotion_gate_blocker=" in output
    assert "primary_call_review_label=" in output
    assert "primary_call_gate_blocker=" in output
    assert "hot_promotion_action=" in output
    assert "warm_promotion_action=" in output
    assert "primary_defense_action=" in output
    assert "hot_promotion_reason=" in output
    assert "primary_defense_reason=" in output
    assert "operator_focuses=" in output
    assert "operator_focus_1=" in output
    assert "operator_step_1=" in output
    assert "validate_now_member_1=" in output
    assert "act_now_member_1=" in output
    assert "promotion_check" in output
    assert "risk_status=" in output
    assert json.loads((tmp_path / "offensive_model_cycle_latest.json").read_text(encoding="utf-8"))["filtered_row_count"] >= 1
    assert (tmp_path / "offensive_action_memo_latest.md").exists()
    assert (tmp_path / "offensive_handoff_summary_latest.md").exists()
    assert (tmp_path / "offensive_reason_summary_20260420T010000.json").exists()
    assert (tmp_path / "offensive_filter_recommendation_20260420T010000.json").exists()
    assert (tmp_path / "offensive_screening_filtered_20260420T010000.csv").exists()
    assert (tmp_path / "offensive_candidate_packet_20260420T010000.md").exists()
    assert (tmp_path / "offensive_action_memo_20260420T010000.md").exists()
    assert (tmp_path / "offensive_handoff_summary_20260420T010000.md").exists()
    assert (tmp_path / "offensive_cycle_diff_20260420T010000.json").exists()
    assert (tmp_path / "offensive_cycle_guard_20260420T010000.json").exists()
    cycle_payload = json.loads((tmp_path / "offensive_model_cycle_latest.json").read_text(encoding="utf-8"))
    assert cycle_payload["validate_now_count"] >= 0
    assert cycle_payload["cycle_diff"]["previous_label"] == "20260420T000000"
    assert cycle_payload["cycle_diff"]["current_label"] == "20260420T010000"
    assert cycle_payload["cycle_guard"]["guard_status"] == "review"
    assert cycle_payload["cycle_guard"]["previous_label"] == "20260420T000000"
    assert cycle_payload["cycle_guard"]["current_label"] == "20260420T010000"
    assert cycle_payload["operator_snapshot"]["guard_status"] == "review"
    assert cycle_payload["operator_snapshot"]["operator_headline"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_scan"]["state_scan"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_scan"]["promotion_scan"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_scan"]["defense_scan"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_scan"]["primary_call_scan"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_scan"]["runbook_scan"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_steps"][0]["step_type"] == "promotion_check"
    assert cycle_payload["operator_snapshot"]["watch_summary"] != "none"
    assert cycle_payload["operator_snapshot"]["validate_gate_summary"] != "none"
    assert cycle_payload["operator_snapshot"]["validate_gate_lineup"] != "none"
    assert cycle_payload["operator_snapshot"]["act_now_gate_summary"] != "none"
    assert cycle_payload["operator_snapshot"]["act_now_gate_lineup"] != "none"
    assert cycle_payload["operator_snapshot"]["validate_now_members"]
    assert cycle_payload["operator_snapshot"]["act_now_members"]
    assert cycle_payload["operator_snapshot"]["validate_competition_summary"] != "none"
    assert cycle_payload["operator_snapshot"]["validate_competition_rationale"] != "none"
    assert cycle_payload["operator_snapshot"]["act_now_competition_summary"] != "none"
    assert cycle_payload["operator_snapshot"]["act_now_competition_rationale"] != "none"
    assert cycle_payload["operator_snapshot"]["risk_summary"] != "none"
    assert cycle_payload["operator_snapshot"]["guard_summary"].startswith("cycle_guard=review; breaches=")
    assert cycle_payload["operator_snapshot"]["guard_breach_summary"] != "none"
    assert cycle_payload["operator_snapshot"]["guard_quality_status"] in {"unknown", "stable", "caution", "review"}
    assert cycle_payload["operator_snapshot"]["hot_promotion_watch"] != "none"
    assert cycle_payload["operator_snapshot"]["hot_promotion_watch_code"] != "none"
    assert cycle_payload["operator_snapshot"]["hot_promotion_watch_review_label"] != "none"
    assert cycle_payload["operator_snapshot"]["hot_promotion_watch_gate_blocker"] != "none"
    assert cycle_payload["operator_snapshot"]["hot_promotion_watch_reason"] != "none"
    assert cycle_payload["operator_snapshot"]["warm_promotion_watch"] == "none"
    assert cycle_payload["operator_snapshot"]["warm_promotion_watch_code"] == "none"
    assert cycle_payload["operator_snapshot"]["warm_promotion_watch_reason"] == "none"
    assert cycle_payload["operator_snapshot"]["primary_defense_watch"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_defense_watch_code"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_defense_watch_reason"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_call_type"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_call_code"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_call_reason"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_call"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_call_review_label"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_call_gate_blocker"] != "none"
    assert cycle_payload["operator_snapshot"]["primary_call_note"] != "none"
    assert len(cycle_payload["operator_snapshot"]["operator_focuses"]) >= 2
    assert cycle_payload["operator_snapshot"]["operator_focuses"][0]["focus_type"] in {"promotion_watch", "act_now_risk"}
    assert cycle_payload["operator_snapshot"]["operator_focuses"][0]["severity"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_focuses"][0]["review_label"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_focuses"][0]["gate_blocker"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_focuses"][0]["summary"] != "none"
    assert cycle_payload["operator_snapshot"]["operator_focuses"][0]["next_gate"] != "none"
    stems = [entry["stem"] for entry in cycle_payload["artifact_manifest"]]
    assert "offensive_cycle_diff" in stems
    assert "offensive_cycle_guard" in stems
    assert len(readme_sync_calls) == 1
    assert readme_sync_calls[0][0] == cycle_mod.REPO_ROOT / "README.md"
    synced_cycle_payload = readme_sync_calls[0][1]
    assert synced_cycle_payload["stamp"] == "20260420T010000"
    assert synced_cycle_payload["operator_snapshot"]["guard_status"] == "review"
    handoff_payload = json.loads((tmp_path / "offensive_handoff_summary_latest.json").read_text(encoding="utf-8"))
    assert handoff_payload["cycle_diff"]["previous_label"] == "20260420T000000"
    assert handoff_payload["cycle_guard"]["guard_status"] == "review"
    assert handoff_payload["cycle_guard"]["act_now_stability"]
    validate_rows = handoff_payload["validate_priority"]
    if validate_rows:
        assert all("promotion_path_summary" in row for row in validate_rows)
    assert handoff_payload["act_now_risk"][0]["demotion_edge_summary"].startswith("breaks_first_on=")


def test_main_updates_readme_thread_handoff_file(monkeypatch, tmp_path: Path, capsys) -> None:
    class FakeScreener:
        def run(self, max_items, etf_mode, stock_sort_column):
            return pd.DataFrame(
                [
                    {
                        "Code": "007810",
                        "Name": "Alpha",
                        "offensive_score": 90.0,
                        "offensive_rank": 1,
                        "rank_delta_vs_legacy": 5,
                        "momentum_1m": 25.0,
                        "momentum_6m": 150.0,
                        "momentum_12m": 300.0,
                        "MAD_gap_pct": 60.0,
                        "volume_ratio_5d_20d": 1.2,
                        "breakout_distance_pct": -1.0,
                        "momentum_acceleration": 5.0,
                        "offensive_component_mom12": 30.0,
                        "offensive_component_mom6": 20.0,
                        "offensive_component_mom1": 12.0,
                        "offensive_component_trend": 15.0,
                        "offensive_component_breakout": 9.9,
                        "offensive_component_volume": 6.0,
                    },
                    {
                        "Code": "006400",
                        "Name": "Beta",
                        "offensive_score": 78.0,
                        "offensive_rank": 2,
                        "rank_delta_vs_legacy": 8,
                        "momentum_1m": 24.0,
                        "momentum_6m": 90.0,
                        "momentum_12m": 190.0,
                        "MAD_gap_pct": 45.0,
                        "volume_ratio_5d_20d": 1.0,
                        "breakout_distance_pct": 0.0,
                        "momentum_acceleration": 4.0,
                        "offensive_component_mom12": 23.0,
                        "offensive_component_mom6": 15.0,
                        "offensive_component_mom1": 10.0,
                        "offensive_component_trend": 14.0,
                        "offensive_component_breakout": 10.0,
                        "offensive_component_volume": 5.0,
                    },
                ]
            )

    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        """## Thread Handoff

### Latest Verified Offensive State

Latest offensive cycle artifacts were regenerated on `old`:

Latest verified headline state:

- `screening_row_count = 0`
- `filtered_row_count = 0`
- `shortlist_count = 0`
- `act_now_count = 0`
- `validate_now_count = 0`
- `operator_headline = none`
- `compare_scan = none`
- `risk_compare_scan = none`
- `live_scan = none`
- `guard_scan = none`
- `guard_status = unknown`

Latest verified top focus:

- warm promotion watch: `none`
- hot promotion watch: `none`
- hot act-now risk names: `none`
- warm act-now risk names: `none`

### New Thread Starter Prompt

```text
理쒓렐 offensive ?곹깭:
- act_now=0
- validate_now=0
- act_now_live=0
- act_now_dormant=0
- hot promotion watch=none
- warm promotion watch=none
- hot act-now risk=none
- warm act-now risk=none
- operator board? focus queue媛 ?대? 遺숈뼱 ?덉쓬
- validate/act-now competition summary? rationale? root cycle怨?handoff summary ?묒そ 紐⑤몢 key-value contract濡??뺣젹???덉쓬
```
""",
        encoding="utf-8",
    )
    (tmp_path / "offensive_handoff_summary_20260420T000000.json").write_text(
        json.dumps(
            {
                "act_now_count": 0,
                "validate_now_count": 1,
                "act_now": [],
                "validate_now": [{"Code": "006400", "Name": "Beta"}],
                "top_candidates": [{"Code": "006400", "Name": "Beta", "offensive_score": 70.0, "offensive_rank": 2}],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(cycle_mod, "MomentumScreener", FakeScreener)
    monkeypatch.setattr(cycle_mod, "_timestamp", lambda: "20260420T010000")
    monkeypatch.setattr(cycle_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/run_offensive_model_cycle.py",
            "--max-items",
            "25",
            "--top-n",
            "2",
            "--shortlist-top-n",
            "2",
            "--stock-sort-column",
            "offensive_score",
            "--output-dir",
            str(tmp_path),
        ],
    )

    cycle_mod.main()
    capsys.readouterr()
    updated = readme_path.read_text(encoding="utf-8")
    assert "Latest offensive cycle artifacts were regenerated on `2026-04-20 01:00`:" in updated
    assert "- `screening_row_count = 2`" in updated
    assert "- `filtered_row_count = 2`" in updated
    assert "- `shortlist_count = 2`" in updated


def test_main_preserves_latest_aliases_on_detected_screening_collapse(monkeypatch, tmp_path: Path, capsys) -> None:
    class FakeScreener:
        def run(self, max_items, etf_mode, stock_sort_column):
            frame = pd.DataFrame(
                [
                    {
                        "Code": "007810",
                        "Name": "Collapsed",
                        "offensive_score": 91.0,
                        "offensive_rank": 1,
                        "rank_delta_vs_legacy": 0,
                        "momentum_1m": 20.0,
                        "momentum_6m": 120.0,
                        "momentum_12m": 250.0,
                        "MAD_gap_pct": 50.0,
                        "volume_ratio_5d_20d": 0.9,
                        "breakout_distance_pct": -0.2,
                        "momentum_acceleration": 2.0,
                        "offensive_component_mom12": 24.0,
                        "offensive_component_mom6": 18.0,
                        "offensive_component_mom1": 10.0,
                        "offensive_component_trend": 15.0,
                        "offensive_component_breakout": 9.0,
                        "offensive_component_volume": 2.0,
                    }
                ]
            )
            frame.attrs["screening_quality"] = {
                "quality_status": "review",
                "attempted_ticker_count": 25,
                "price_fetch_success_count": 6,
                "valid_momentum_count": 1,
                "empty_price_count": 19,
                "invalid_momentum_count": 5,
                "price_fetch_coverage": 0.24,
                "success_coverage": 0.04,
                "empty_price_codes_sample": ["000001", "000002"],
                "invalid_momentum_codes_sample": ["000003"],
                "quality_summary": "attempted=25; fetched=6; valid=1; empty_price=19; invalid_momentum=5; fetch_coverage=0.24; success_coverage=0.04",
            }
            return frame

    previous_stamp = "20260420T000000"
    previous_cycle_latest = {"stamp": previous_stamp, "act_now_count": 3, "validate_now_count": 2}
    previous_handoff_latest = {
        "screening_row_count": 30,
        "filtered_row_count": 10,
        "shortlist_count": 5,
        "act_now_count": 3,
        "validate_now_count": 2,
        "act_now": [
            {"Code": "006400", "Name": "Alpha"},
            {"Code": "080220", "Name": "Beta"},
            {"Code": "095610", "Name": "Gamma"},
        ],
        "validate_now": [
            {"Code": "402340", "Name": "Hot"},
            {"Code": "007810", "Name": "Warm"},
        ],
        "top_candidates": [
            {"Code": "402340", "Name": "Hot", "offensive_score": 99.0, "offensive_rank": 1},
            {"Code": "007810", "Name": "Warm", "offensive_score": 91.0, "offensive_rank": 2},
        ],
    }
    (tmp_path / f"offensive_model_cycle_{previous_stamp}.json").write_text(
        json.dumps(previous_cycle_latest),
        encoding="utf-8",
    )
    (tmp_path / f"offensive_model_cycle_{previous_stamp}.md").write_text("stable cycle", encoding="utf-8")
    (tmp_path / f"offensive_handoff_summary_{previous_stamp}.json").write_text(
        json.dumps(previous_handoff_latest),
        encoding="utf-8",
    )
    (tmp_path / f"offensive_handoff_summary_{previous_stamp}.md").write_text("stable handoff", encoding="utf-8")
    (tmp_path / f"offensive_screening_{previous_stamp}.csv").write_text(
        "Code,Name\ngood,stable\n",
        encoding="utf-8",
    )

    readme_sync_calls: list[dict[str, object]] = []
    monkeypatch.setattr(cycle_mod, "MomentumScreener", FakeScreener)
    monkeypatch.setattr(cycle_mod, "_timestamp", lambda: "20260420T010000")
    monkeypatch.setattr(cycle_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        cycle_mod,
        "_sync_readme_thread_handoff",
        lambda readme_path, *, cycle_payload: readme_sync_calls.append(cycle_payload),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/run_offensive_model_cycle.py",
            "--max-items",
            "25",
            "--top-n",
            "2",
            "--shortlist-top-n",
            "2",
            "--stock-sort-column",
            "offensive_score",
            "--output-dir",
            str(tmp_path),
        ],
    )

    cycle_mod.main()
    output = capsys.readouterr().out

    assert "latest_update_status=preserved_previous_latest" in output
    assert readme_sync_calls == []

    latest_cycle = json.loads((tmp_path / "offensive_model_cycle_latest.json").read_text(encoding="utf-8"))
    latest_handoff = json.loads((tmp_path / "offensive_handoff_summary_latest.json").read_text(encoding="utf-8"))
    latest_screening = (tmp_path / "offensive_screening_latest.csv").read_text(encoding="utf-8")
    current_cycle = json.loads((tmp_path / "offensive_model_cycle_20260420T010000.json").read_text(encoding="utf-8"))

    assert latest_cycle == previous_cycle_latest
    assert latest_handoff == previous_handoff_latest
    assert latest_screening == "Code,Name\ngood,stable\n"
    assert current_cycle["latest_update"]["status"] == "preserved_previous_latest"
    assert "previous_screening=30" in current_cycle["latest_update"]["reason"]
    assert "current_screening=1" in current_cycle["latest_update"]["reason"]


def test_main_writes_offensive_model_cycle_once_after_finalize(monkeypatch, tmp_path: Path, capsys) -> None:
    class FakeScreener:
        def run(self, max_items, etf_mode, stock_sort_column):
            return pd.DataFrame(
                [
                    {
                        "Code": "007810",
                        "Name": "Alpha",
                        "offensive_score": 90.0,
                        "offensive_rank": 1,
                        "rank_delta_vs_legacy": 5,
                        "momentum_1m": 25.0,
                        "momentum_6m": 150.0,
                        "momentum_12m": 300.0,
                        "MAD_gap_pct": 60.0,
                        "volume_ratio_5d_20d": 1.2,
                        "breakout_distance_pct": -1.0,
                        "momentum_acceleration": 5.0,
                        "offensive_component_mom12": 30.0,
                        "offensive_component_mom6": 20.0,
                        "offensive_component_mom1": 12.0,
                        "offensive_component_trend": 15.0,
                        "offensive_component_breakout": 9.9,
                        "offensive_component_volume": 6.0,
                    },
                    {
                        "Code": "006400",
                        "Name": "Beta",
                        "offensive_score": 78.0,
                        "offensive_rank": 2,
                        "rank_delta_vs_legacy": 8,
                        "momentum_1m": 24.0,
                        "momentum_6m": 90.0,
                        "momentum_12m": 190.0,
                        "MAD_gap_pct": 45.0,
                        "volume_ratio_5d_20d": 1.0,
                        "breakout_distance_pct": 0.0,
                        "momentum_acceleration": 4.0,
                        "offensive_component_mom12": 23.0,
                        "offensive_component_mom6": 15.0,
                        "offensive_component_mom1": 10.0,
                        "offensive_component_trend": 14.0,
                        "offensive_component_breakout": 10.0,
                        "offensive_component_volume": 5.0,
                    },
                ]
            )

    (tmp_path / "README.md").write_text("", encoding="utf-8")
    (tmp_path / "offensive_handoff_summary_20260420T000000.json").write_text(
        json.dumps(
            {
                "act_now_count": 0,
                "validate_now_count": 1,
                "act_now": [],
                "validate_now": [{"Code": "006400", "Name": "Beta"}],
                "top_candidates": [{"Code": "006400", "Name": "Beta", "offensive_score": 70.0, "offensive_rank": 2}],
            }
        ),
        encoding="utf-8",
    )

    json_write_calls: list[tuple[str, tuple[str, ...]]] = []
    md_write_calls: list[str] = []
    original_write_json_pair = cycle_mod._write_json_pair
    original_write_md_pair = cycle_mod._write_md_pair

    def tracking_write_json_pair(output_dir, stem, stamp, payload):
        manifest_stems = tuple(entry["stem"] for entry in payload.get("artifact_manifest", []))
        json_write_calls.append((stem, manifest_stems))
        original_write_json_pair(output_dir, stem, stamp, payload)

    def tracking_write_md_pair(output_dir, stem, stamp, text):
        md_write_calls.append(stem)
        original_write_md_pair(output_dir, stem, stamp, text)

    monkeypatch.setattr(cycle_mod, "MomentumScreener", FakeScreener)
    monkeypatch.setattr(cycle_mod, "_timestamp", lambda: "20260420T010000")
    monkeypatch.setattr(cycle_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cycle_mod, "_sync_readme_thread_handoff", lambda *args, **kwargs: None)
    monkeypatch.setattr(cycle_mod, "_write_json_pair", tracking_write_json_pair)
    monkeypatch.setattr(cycle_mod, "_write_md_pair", tracking_write_md_pair)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/run_offensive_model_cycle.py",
            "--max-items",
            "25",
            "--top-n",
            "2",
            "--shortlist-top-n",
            "2",
            "--stock-sort-column",
            "offensive_score",
            "--output-dir",
            str(tmp_path),
        ],
    )

    cycle_mod.main()
    capsys.readouterr()

    offensive_model_cycle_json_calls = [entry for entry in json_write_calls if entry[0] == "offensive_model_cycle"]
    offensive_model_cycle_md_calls = [stem for stem in md_write_calls if stem == "offensive_model_cycle"]
    assert len(offensive_model_cycle_json_calls) == 1
    assert len(offensive_model_cycle_md_calls) == 1
    assert "offensive_handoff_summary" in offensive_model_cycle_json_calls[0][1]
    assert "offensive_cycle_diff" in offensive_model_cycle_json_calls[0][1]
    assert "offensive_cycle_guard" in offensive_model_cycle_json_calls[0][1]
