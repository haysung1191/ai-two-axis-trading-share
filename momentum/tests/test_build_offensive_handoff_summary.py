from __future__ import annotations

from tools.analysis import build_offensive_handoff_summary as handoff_mod


def test_build_handoff_summary_payload_includes_cycle_guard() -> None:
    payload = handoff_mod.build_handoff_summary_payload(
        {
            "screening_row_count": 10,
            "filtered_row_count": 4,
            "shortlist_count": 2,
            "latest_update": {"status": "advance_latest", "reason": "none"},
            "screening_quality": {
                "attempted_ticker_count": 12,
                "price_fetch_success_count": 10,
                "valid_momentum_count": 10,
                "empty_price_count": 2,
                "invalid_momentum_count": 0,
                "price_fetch_coverage": 0.8333,
                "success_coverage": 0.8333,
                "empty_price_codes_sample": ["X1", "X2"],
                "invalid_momentum_codes_sample": [],
                "quality_summary": "attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83",
            },
        },
        {
            "act_now_count": 1,
            "validate_now_count": 2,
            "decisions": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "action_label": "act_now",
                    "action_reasons": ["top_rank_leader"],
                    "demotion_edge_summary": "breaks_first_on=large_rank_upgrade margin=0.05",
                    "rule_trigger_summary": "promoted_core gate passed with confirmation_count=2/2; met=volume_support,breakout_ready",
                    "next_gate_summary": "already_cleared",
                    "act_now_risk_status": "hot",
                    "act_now_risk_summary": "hot: weakest_margin=0.05, weakest_signal=large_rank_upgrade",
                },
                {
                    "Code": "B",
                    "Name": "Beta",
                    "action_label": "validate_now",
                    "action_reasons": ["promotion_signal"],
                    "rule_trigger_summary": "promoted_core kept but act-now confirmation_count=1/2; met=breakout_ready; missing=large_rank_upgrade,volume_support",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now; gaps=large_rank_upgrade: current=5.0, threshold=7.0, gap=2.0, volume_support: current=4.0, threshold=5.0, gap=1.0",
                    "promotion_readiness_score": 86.0,
                    "primary_gap_signal": "volume_support",
                    "nearest_signal_gap": 1.0,
                    "total_signal_gap": 3.0,
                    "promotion_trigger_signal": "none",
                    "promotion_path_summary": "one_signal_to_act_now: primary=volume_support gap=1.0; alternates=large_rank_upgrade",
                    "validate_priority_summary": "closest_path=volume_support gap=1.0; total_gap=3.0; confirmations=1/2",
                    "missing_signal_count": 2,
                    "validate_priority_rank": 2,
                    "promotion_watch_status": "warm",
                    "promotion_watch_summary": "warm: nearest_gap=1.0, primary_gap=volume_support",
                },
                {
                    "Code": "C",
                    "Name": "Gamma",
                    "action_label": "validate_now",
                    "action_reasons": ["promotion_signal"],
                    "rule_trigger_summary": "promoted_core kept but act-now confirmation_count=1/2; met=breakout_ready; missing=large_rank_upgrade,volume_support",
                    "next_gate_summary": "needs 1 more confirmation signal for act-now; gaps=large_rank_upgrade: current=5.0, threshold=7.0, gap=2.0, volume_support: current=4.0, threshold=5.0, gap=1.0",
                    "promotion_readiness_score": 92.0,
                    "primary_gap_signal": "large_rank_upgrade",
                    "nearest_signal_gap": 0.5,
                    "total_signal_gap": 2.5,
                    "promotion_trigger_signal": "large_rank_upgrade",
                    "promotion_path_summary": "one_signal_to_act_now: primary=large_rank_upgrade gap=0.5; alternates=volume_support",
                    "validate_priority_summary": "closest_path=large_rank_upgrade gap=0.5; total_gap=2.5; confirmations=1/2",
                    "missing_signal_count": 1,
                    "validate_priority_rank": 1,
                    "promotion_watch_status": "hot",
                    "promotion_watch_summary": "hot: nearest_gap=0.5, primary_gap=large_rank_upgrade",
                },
            ],
        },
        {
            "candidates": [
                {"Code": "A", "Name": "Alpha", "priority_bucket": "core", "reason_tags": ["recent_strength"]}
            ]
        },
        {
            "previous_label": "prev",
            "current_label": "curr",
            "act_now_added": ["A"],
            "act_now_removed": ["C"],
            "validate_now_removed": ["A"],
            "action_state_changes": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "previous_action_label": "validate_now",
                    "current_action_label": "act_now",
                    "confirmation_count_change": 1,
                    "signals_added": ["volume_support"],
                    "signals_removed": [],
                    "previous_rule_trigger_summary": "promoted_core kept but act-now confirmation_count=1/2; met=breakout_ready; missing=large_rank_upgrade,volume_support",
                    "current_rule_trigger_summary": "promoted_core gate passed with confirmation_count=2/2; met=volume_support,breakout_ready",
                }
            ],
            "validate_priority_changes": [
                {
                    "Code": "B",
                    "Name": "Beta",
                    "previous_action_label": "validate_now",
                    "current_action_label": "validate_now",
                    "previous_validate_priority_rank": 2,
                    "current_validate_priority_rank": 1,
                    "validate_priority_rank_change": -1,
                    "previous_readiness_score": 81.0,
                    "current_readiness_score": 92.0,
                    "readiness_score_change": 11.0,
                    "previous_gap_count": 2,
                    "current_gap_count": 1,
                    "gap_count_change": -1,
                    "previous_primary_gap_signal": "volume_support",
                    "current_primary_gap_signal": "large_rank_upgrade",
                }
            ],
            "act_now_risk_changes": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "previous_action_label": "act_now",
                    "current_action_label": "act_now",
                    "previous_act_now_risk_status": "off",
                    "current_act_now_risk_status": "hot",
                    "previous_act_now_risk_summary": "none",
                    "current_act_now_risk_summary": "hot: weakest_margin=0.05, weakest_signal=large_rank_upgrade",
                    "previous_weakest_met_signal": "none",
                    "current_weakest_met_signal": "large_rank_upgrade",
                }
            ],
            "top_candidate_score_changes": [
                {
                    "Code": "A",
                    "score_change": 0.3,
                    "rank_change": 0,
                    "component_changes": [{"component": "volume", "change": 0.1}],
                },
                {
                    "Code": "C",
                    "score_change": -0.4,
                    "rank_change": 1,
                    "component_changes": [{"component": "mom1", "change": -0.2}],
                }
            ],
        },
        {
            "guard_status": "stable",
            "guard_summary": "No material offensive-cycle instability detected.",
            "act_now_stability": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "stability_status": "stable",
                    "score_change": 0.0,
                    "rank_change": 0,
                    "support_summary": "top_rank_leader, recent_strength_confirmed",
                    "component_summary": "volume=0.5, breakout=0.1",
                    "component_drift_severity": "benign",
                    "component_drift_reason": "Component drift is flat-to-positive.",
                    "reason": "Act-now member held its slot with only small score and rank movement.",
                }
            ],
            "caution_flags": [],
            "review_flags": [],
            "breaches": [],
            "screening_quality": {
                "quality_status": "stable",
                "quality_summary": "status=stable; attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83",
                "codes": {
                    "empty_price_codes_sample": ["X1", "X2"],
                    "invalid_momentum_codes_sample": [],
                },
            },
        },
    )

    assert payload["cycle_guard"]["guard_status"] == "stable"
    assert payload["cycle_guard"]["previous_label"] == "prev"
    assert payload["cycle_guard"]["current_label"] == "curr"
    assert payload["cycle_guard"]["metrics"] == {
        "act_now_count_change_abs": 0,
        "validate_now_count_change_abs": 0,
        "act_now_membership_change": 2,
        "validate_now_membership_change": 1,
        "largest_score_change": 0.4,
        "largest_rank_change": 1.0,
    }
    assert payload["cycle_guard"]["act_now_stability"][0]["Code"] == "A"
    assert payload["act_now_demotions"][0]["Code"] == "C"
    assert payload["act_now_promotions"][0]["Code"] == "A"
    assert payload["act_now_live_count"] == 1
    assert payload["act_now_dormant_count"] == 0
    assert [row["Code"] for row in payload["act_now"]] == ["A"]
    assert [row["Code"] for row in payload["validate_now"]] == ["C", "B"]
    assert payload["focus_queue"][0]["focus_type"] == "promotion_watch"
    assert payload["focus_queue"][0]["operator_action"] == "check rank follow-through"
    assert "closest to promotion on rank follow-through" in payload["focus_queue"][0]["operator_note"]
    assert "Priority view: closest_path=large_rank_upgrade gap=0.5; total_gap=2.5; confirmations=1/2" in payload["focus_queue"][0]["operator_note"]
    assert "Promotion path: one_signal_to_act_now: primary=large_rank_upgrade gap=0.5; alternates=volume_support" in payload["focus_queue"][0]["operator_note"]
    assert payload["focus_queue"][1]["operator_action"] == "verify rank follow-through"
    assert "thinnest support is rank follow-through" in payload["focus_queue"][1]["operator_note"]
    assert "Demotion edge: breaks_first_on=large_rank_upgrade margin=0.05" in payload["focus_queue"][1]["operator_note"]
    assert payload["validate_competition"]["leader_code"] == "C"
    assert payload["validate_competition"]["challenger_code"] == "B"
    assert payload["validate_competition"]["leader_next_gate"] == "needs 1 more confirmation signal for act-now"
    assert payload["validate_competition"]["leader_gap_summary"].startswith("large_rank_upgrade:")
    assert payload["validate_competition"]["nearest_gap_edge"] == 0.5
    assert payload["validate_competition"]["total_gap_edge"] == 0.5
    assert payload["validate_competition"]["summary_contract"] == "mode=ordered; leader=C; challenger=B; nearest_gap_edge=0.50; total_gap_edge=0.50; readiness_edge=6.00"
    assert payload["validate_competition"]["rationale_contract"] == "mode=ordered; leader=C; challenger=B; ordering_basis=nearest_gap_then_total_gap_then_readiness; leader_primary_gap=large_rank_upgrade; leader_nearest_gap=0.50; leader_total_gap=2.50; challenger_primary_gap=volume_support; challenger_nearest_gap=1.00; challenger_total_gap=3.00; nearest_gap_edge=0.50; total_gap_edge=0.50; readiness_edge=6.00"
    assert payload["act_now_competition"]["leader_code"] == "A"
    assert payload["act_now_competition"]["summary"] == "single act-now name remains: A Alpha"
    assert payload["act_now_competition"]["summary_contract"] == "mode=single; leader=A; challenger=none"
    assert payload["act_now_competition"]["rationale_contract"] == "mode=single; leader=A; challenger=none; ordering_basis=only_act_now_candidate; leader_risk_status=hot; leader_weakest_signal=large_rank_upgrade; leader_weakest_margin=0.05"
    assert payload["act_now_defense_ladder"][0]["Code"] == "A"
    assert payload["act_now_defense_ladder"][0]["defense_rank"] == 1
    assert payload["operator_runbook"][0]["Code"] == "C"
    assert payload["operator_runbook"][0]["step_type"] == "promotion_check"
    assert payload["operator_runbook"][1]["Code"] == "B"
    assert payload["operator_runbook"][2]["Code"] == "A"
    assert payload["operator_board"]["headline"] == "act_now=1, validate_now=2, watch_hot=1, risk_hot=1, data_quality=0, top_focus=promotion_watch:C Gamma"
    assert payload["operator_board"]["primary_call"] == "check rank follow-through on C Gamma"
    assert payload["operator_board"]["priority_scan"] == "top_focus=promotion_watch:C; gate_blocker=needs 1 more confirmation signal for act-now; action=check rank follow-through; reason=closest_path=large_rank_upgrade gap=0.5; total_gap=2.5; confirmations=1/2"
    assert payload["operator_board"]["watch_summary"] == "promotion_watch: hot=1, warm=1"
    assert payload["operator_board"]["data_quality_focus_summary"] == "data_quality_guard: count=0, status=stable"
    assert payload["operator_board"]["compare_summary"] == "C Gamma leads B Beta: nearest_gap_edge=0.5, total_gap_edge=0.5, readiness_edge=6.0"
    assert payload["operator_board"]["compare_summary_contract"] == "mode=ordered; leader=C; challenger=B; nearest_gap_edge=0.50; total_gap_edge=0.50; readiness_edge=6.00"
    assert payload["operator_board"]["risk_compare_summary"] == "single act-now name remains: A Alpha"
    assert payload["operator_board"]["risk_compare_summary_contract"] == "mode=single; leader=A; challenger=none"
    assert payload["operator_board"]["risk_summary"] == "act_now_risk: hot=1, warm=0"
    assert payload["operator_board"]["live_summary"] == "act_now_live: live=1, dormant=0"
    assert payload["operator_board"]["dormant_summary"] == "act_now_dormant: none"
    assert payload["operator_board"]["data_quality_summary"] == "attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83"
    assert payload["operator_board"]["guard_summary"] == "cycle_guard=stable; breaches=none"
    assert payload["operator_board"]["cycle_diff_labels"] == "previous=prev; current=curr"
    assert payload["operator_board"]["cycle_guard_context"] == "status=stable; previous=prev; current=curr"
    assert payload["operator_board"]["guard_delta_summary"] == "previous=prev; current=curr; act_now_delta=0; validate_now_delta=0; membership=act_now:2,validate_now:1; top_move=score:0.40,rank:1.00"
    assert payload["operator_board"]["guard_note"] == "No material offensive-cycle instability detected."
    assert payload["operator_board"]["guard_breach_summary"] == "none"
    assert payload["operator_board"]["guard_quality_status"] == "stable"
    assert payload["operator_board"]["guard_quality_summary"] == "status=stable; attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83"
    assert payload["operator_board"]["latest_update_summary"] == "status=advance_latest; reason=none"
    report = handoff_mod.render_handoff_summary(payload)
    assert "screening_quality: attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83" in report
    assert "screening_quality_codes: empty_price=X1,X2, invalid_momentum=none" in report
    assert "## Operator Board" in report
    assert "headline: act_now=1, validate_now=2, watch_hot=1, risk_hot=1, data_quality=0, top_focus=promotion_watch:C Gamma" in report
    assert "primary_call: check rank follow-through on C Gamma" in report
    assert "priority_scan: top_focus=promotion_watch:C; gate_blocker=needs 1 more confirmation signal for act-now; action=check rank follow-through; reason=closest_path=large_rank_upgrade gap=0.5; total_gap=2.5; confirmations=1/2" in report
    assert "data_quality_focus_summary: data_quality_guard: count=0, status=stable" in report
    assert "compare_summary: C Gamma leads B Beta: nearest_gap_edge=0.5, total_gap_edge=0.5, readiness_edge=6.0" in report
    assert "compare_summary_contract: mode=ordered; leader=C; challenger=B; nearest_gap_edge=0.50; total_gap_edge=0.50; readiness_edge=6.00" in report
    assert "risk_compare_summary: single act-now name remains: A Alpha" in report
    assert "risk_compare_summary_contract: mode=single; leader=A; challenger=none" in report
    assert "live_summary: act_now_live: live=1, dormant=0" in report
    assert "dormant_summary: act_now_dormant: none" in report
    assert "data_quality_summary: attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83" in report
    assert "cycle_diff_labels: previous=prev; current=curr" in report
    assert "cycle_guard_context: status=stable; previous=prev; current=curr" in report
    assert "guard_note: No material offensive-cycle instability detected." in report
    assert "guard_delta_summary: previous=prev; current=curr; act_now_delta=0; validate_now_delta=0; membership=act_now:2,validate_now:1; top_move=score:0.40,rank:1.00" in report
    assert "guard_breach_summary: none" in report
    assert "guard_quality_status: stable" in report
    assert "guard_quality_summary: status=stable; attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83" in report
    assert "latest_update_summary: status=advance_latest; reason=none" in report
    assert "## Validate Competition" in report
    assert "summary: C Gamma leads B Beta: nearest_gap_edge=0.5, total_gap_edge=0.5, readiness_edge=6.0" in report
    assert "summary_contract: mode=ordered; leader=C; challenger=B; nearest_gap_edge=0.50; total_gap_edge=0.50; readiness_edge=6.00" in report
    assert "rationale: C stays ahead because its closest missing trigger is large_rank_upgrade at 0.50, versus B at 1.00; total unfinished gap is 2.50 versus 3.00." in report
    assert "rationale_contract: mode=ordered; leader=C; challenger=B; ordering_basis=nearest_gap_then_total_gap_then_readiness; leader_primary_gap=large_rank_upgrade; leader_nearest_gap=0.50; leader_total_gap=2.50; challenger_primary_gap=volume_support; challenger_nearest_gap=1.00; challenger_total_gap=3.00; nearest_gap_edge=0.50; total_gap_edge=0.50; readiness_edge=6.00" in report
    assert "## Act Now Competition" in report
    assert "summary: single act-now name remains: A Alpha" in report
    assert "summary_contract: mode=single; leader=A; challenger=none" in report
    assert "rationale_contract: mode=single; leader=A; challenger=none; ordering_basis=only_act_now_candidate; leader_risk_status=hot; leader_weakest_signal=large_rank_upgrade; leader_weakest_margin=0.05" in report
    assert "## Act Now Defense Ladder" in report
    assert "rank=1 A Alpha: risk_status=hot, weakest_margin=0.05, weakest_signal=large_rank_upgrade, offensive_rank=-, offensive_score=-, demotion_edge=breaks_first_on=large_rank_upgrade margin=0.05" in report
    assert "## Operator Runbook" in report
    assert "step=1 type=promotion_check C Gamma: action=check rank follow-through, reason=closest_path=large_rank_upgrade gap=0.5; total_gap=2.5; confirmations=1/2" in report
    assert "step=2 type=promotion_backup B Beta: action=keep warm watch on volume confirmation, reason=closest_path=volume_support gap=1.0; total_gap=3.0; confirmations=1/2" in report
    assert "step=3 type=defense_watch A Alpha: action=verify rank follow-through, reason=weakest_margin=0.05, demotion_edge=breaks_first_on=large_rank_upgrade margin=0.05" in report
    assert "## Focus Queue" in report
    assert "## Cycle Guard" in report
    assert "previous_label: prev" in report
    assert "current_label: curr" in report
    assert "delta_summary: previous=prev; current=curr; act_now_delta=0; validate_now_delta=0; membership=act_now:2,validate_now:1; top_move=score:0.40,rank:1.00" in report
    assert "summary: No material offensive-cycle instability detected." in report
    assert "breaches: none" in report
    assert "quality_status: stable" in report
    assert "quality_summary: status=stable; attempted=12; fetched=10; valid=10; empty_price=2; invalid_momentum=0; fetch_coverage=0.83; success_coverage=0.83" in report
    assert "quality_codes: empty_price=X1,X2, invalid_momentum=none" in report
    assert "flags: none" in report
    assert "## Act Now Demotions" in report
    assert "## Act Now Promotions" in report
    assert "## Act Now Stability" in report
    assert "## Rule State Changes" in report
    assert "## Validate Priority Trend" in report
    assert "## Act Now Risk Trend" in report
    assert "## Promotion Watch" in report
    assert "## Act Now Risk" in report
    assert "## Validate Priority" in report
    assert "support=top_rank_leader, recent_strength_confirmed" in report
    assert "components=volume=0.5, breakout=0.1" in report
    assert "action_label=validate_now->act_now" in report
    assert "new_action_label=validate_now" in report
    assert "previous_action_label=validate_now" in report
    assert "rule_trigger=promoted_core gate passed with confirmation_count=2/2; met=volume_support,breakout_ready" in report
    assert "rule_trigger=promoted_core kept but act-now confirmation_count=1/2; met=breakout_ready; missing=large_rank_upgrade,volume_support" in report
    assert "next_gate=already_cleared" in report
    assert "next_gate=needs 1 more confirmation signal for act-now; gaps=large_rank_upgrade: current=5.0, threshold=7.0, gap=2.0, volume_support: current=4.0, threshold=5.0, gap=1.0" in report
    assert "rank=1 C Gamma: readiness_score=92.0, primary_gap=large_rank_upgrade, nearest_gap=0.5, total_gap=2.5, priority_view=closest_path=large_rank_upgrade gap=0.5; total_gap=2.5; confirmations=1/2, promotion_trigger=large_rank_upgrade, promotion_path=one_signal_to_act_now: primary=large_rank_upgrade gap=0.5; alternates=volume_support, gap_count=1" in report
    assert "rank=2 B Beta: readiness_score=86.0, primary_gap=volume_support, nearest_gap=1.0, total_gap=3.0, priority_view=closest_path=volume_support gap=1.0; total_gap=3.0; confirmations=1/2, promotion_trigger=none, promotion_path=one_signal_to_act_now: primary=volume_support gap=1.0; alternates=large_rank_upgrade, gap_count=2" in report
    assert "status=hot rank=1 C Gamma: readiness_score=92.0, watch=hot: nearest_gap=0.5, primary_gap=large_rank_upgrade, promotion_path=one_signal_to_act_now: primary=large_rank_upgrade gap=0.5; alternates=volume_support" in report
    assert "status=warm rank=2 B Beta: readiness_score=86.0, watch=warm: nearest_gap=1.0, primary_gap=volume_support, promotion_path=one_signal_to_act_now: primary=volume_support gap=1.0; alternates=large_rank_upgrade" in report
    assert "status=hot A Alpha: offensive_rank=-, offensive_score=-, risk=hot: weakest_margin=0.05, weakest_signal=large_rank_upgrade, demotion_edge=breaks_first_on=large_rank_upgrade margin=0.05" in report
    assert "rank=1 type=promotion_watch severity=hot C Gamma: reference_rank=1, summary=hot: nearest_gap=0.5, primary_gap=large_rank_upgrade, action=check rank follow-through" in report
    assert "rank=2 type=act_now_risk severity=hot A Alpha: reference_rank=-, summary=hot: weakest_margin=0.05, weakest_signal=large_rank_upgrade, action=verify rank follow-through" in report
    assert "note=Validate-now candidate C is closest to promotion on rank follow-through" in report
    assert "note=Act-now candidate A is still live, but its thinnest support is rank follow-through" in report
    assert "priority_rank=2->1, readiness_score_change=11.0, gap_count_change=-1, primary_gap=volume_support->large_rank_upgrade" in report
    assert "risk_status=off->hot, weakest_signal=none->large_rank_upgrade, current_risk=hot: weakest_margin=0.05, weakest_signal=large_rank_upgrade" in report
    assert "## Act Now" in report
    assert report.index("## Validate Now") < report.index("- C Gamma: offensive_score=")
    assert report.index("- C Gamma: offensive_score=") < report.index("- B Beta: offensive_score=")
    assert "## Validate Now" in report
    assert "component_drift=benign (Component drift is flat-to-positive.)" in report
    assert "guard_status: stable" in report


def test_promotion_probe_focus_uses_gate_first_operator_guidance() -> None:
    payload = handoff_mod.build_handoff_summary_payload(
        {
            "screening_row_count": 5,
            "filtered_row_count": 3,
            "shortlist_count": 2,
            "latest_update": {"status": "preserved_previous_latest", "reason": "guard_review"},
        },
        {
            "act_now_count": 0,
            "validate_now_count": 1,
            "decisions": [
                {
                    "Code": "006400",
                    "Name": "Samsung",
                    "action_label": "validate_now",
                    "review_label": "promotion_probe",
                    "review_priority_score": 109.73,
                    "action_reasons": ["promotion_signal", "top_rank_leader"],
                    "primary_gap_signal": "volume_support",
                    "nearest_signal_gap": 1.13,
                    "total_signal_gap": 1.13,
                    "promotion_trigger_signal": "none",
                    "promotion_path_summary": "already_cleared",
                    "validate_priority_summary": "closest_path=volume_support gap=1.13; total_gap=1.13; confirmations=2/2",
                    "missing_signal_gap_summary": "volume_support: current=3.87, threshold=5.0, gap=1.13",
                    "missing_signal_count": 1,
                    "validate_priority_rank": 1,
                    "next_gate_summary": "review_label gate blocks promotion before confirmation thresholds matter.",
                    "rule_trigger_summary": "promotion_probe remains in validation bucket by review_label gate.",
                    "promotion_readiness_score": 126.7,
                    "promotion_watch_status": "hot",
                    "promotion_watch_summary": "hot: nearest_gap=1.13, primary_gap=volume_support",
                }
            ],
        },
        {"candidates": []},
        None,
        {"guard_status": "stable", "guard_summary": "No material offensive-cycle instability detected."},
    )

    assert payload["focus_queue"][0]["operator_action"] == "review promotion-probe gate"
    assert "review_label=promotion_probe still blocks promotion" in payload["focus_queue"][0]["operator_note"]
    assert payload["operator_board"]["primary_call"] == "review promotion-probe gate on 006400 Samsung"
    assert payload["operator_board"]["priority_scan"] == "top_focus=promotion_watch:006400; gate_blocker=review_label=promotion_probe; action=review promotion-probe gate; reason=review_label=promotion_probe still blocks promotion"
    assert payload["operator_board"]["latest_update_summary"] == "status=preserved_previous_latest; reason=guard_review"
    assert payload["operator_runbook"][0]["action"] == "review promotion-probe gate"
    report = handoff_mod.render_handoff_summary(payload)
    assert "step=1 type=promotion_check 006400 Samsung: action=review promotion-probe gate" in report


def test_build_handoff_summary_payload_surfaces_guard_quality_review() -> None:
    payload = handoff_mod.build_handoff_summary_payload(
        {
            "screening_row_count": 10,
            "filtered_row_count": 4,
            "shortlist_count": 2,
            "latest_update": {"status": "preserved_previous_latest", "reason": "screening_quality_review"},
            "screening_quality": {
                "quality_summary": "status=review; attempted=10; fetched=6; valid=5",
            },
        },
        {
            "act_now_count": 0,
            "validate_now_count": 0,
            "decisions": [],
        },
        {"candidates": []},
        None,
        {
            "guard_status": "review",
            "guard_summary": "Screening quality degraded enough that offensive-cycle continuity should be reviewed before trusting the latest run.",
            "act_now_stability": [],
            "caution_flags": [],
            "review_flags": ["screening_quality_review"],
            "breaches": ["screening_quality_review"],
            "screening_quality": {
                "quality_status": "review",
                "quality_summary": "status=review; attempted=10; fetched=6; valid=5",
                "codes": {
                    "empty_price_codes_sample": ["111111"],
                    "invalid_momentum_codes_sample": ["222222"],
                },
            },
        },
    )

    assert payload["cycle_guard"]["screening_quality"]["quality_status"] == "review"
    assert payload["operator_board"]["guard_summary"] == "cycle_guard=review; breaches=screening_quality_review"
    assert payload["operator_board"]["cycle_diff_labels"] == "previous=none; current=none"
    assert payload["operator_board"]["cycle_guard_context"] == "status=review; previous=none; current=none"
    assert payload["operator_board"]["guard_delta_summary"] == "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=act_now:none,validate_now:none; top_move=score:none,rank:none"
    assert payload["operator_board"]["guard_quality_status"] == "review"
    assert payload["operator_board"]["headline"] == "act_now=0, validate_now=0, watch_hot=0, risk_hot=0, data_quality=1, top_focus=data_quality_guard:screening_quality Screening Quality"
    assert payload["operator_board"]["priority_scan"] == "top_focus=data_quality_guard:screening_quality; gate_blocker=status=review; attempted=10; fetched=6; valid=5; action=review screening quality; reason=status=review; attempted=10; fetched=6; valid=5"
    assert payload["operator_board"]["latest_update_summary"] == "status=preserved_previous_latest; reason=screening_quality_review"
    assert payload["focus_queue"][0]["focus_type"] == "data_quality_guard"
    assert payload["focus_queue"][0]["operator_action"] == "review screening quality"
    assert payload["operator_runbook"][0]["step_type"] == "data_quality_check"
    report = handoff_mod.render_handoff_summary(payload)
    assert "guard_breach_summary: screening_quality_review" in report
    assert "cycle_diff_labels: previous=none; current=none" in report
    assert "cycle_guard_context: status=review; previous=none; current=none" in report
    assert "guard_delta_summary: previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=act_now:none,validate_now:none; top_move=score:none,rank:none" in report
    assert "data_quality_focus_summary: data_quality_guard: count=1, status=review" in report
    assert "latest_update_summary: status=preserved_previous_latest; reason=screening_quality_review" in report
    assert "rank=1 type=data_quality_guard severity=review screening_quality Screening Quality: reference_rank=0" in report
    assert "step=1 type=data_quality_check screening_quality Screening Quality: action=review screening quality, reason=status=review; attempted=10; fetched=6; valid=5" in report
    assert "previous_label: none" in report
    assert "current_label: none" in report
    assert "delta_summary: previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=act_now:none,validate_now:none; top_move=score:none,rank:none" in report
    assert "quality_status: review" in report
    assert "quality_codes: empty_price=111111, invalid_momentum=222222" in report
    assert "review=screening_quality_review" in report


def test_act_now_competition_rationale_matches_status_and_signal_difference() -> None:
    competition = handoff_mod._build_act_now_competition(
        [
            {
                "Code": "080220",
                "Name": "Gamma",
                "act_now_risk_status": "hot",
                "act_now_risk_summary": "hot: weakest_margin=0.0, weakest_signal=large_rank_upgrade",
                "weakest_met_signal": "large_rank_upgrade",
                "offensive_rank": 6,
                "offensive_score": 85.92,
            },
            {
                "Code": "006400",
                "Name": "Alpha",
                "act_now_risk_status": "warm",
                "act_now_risk_summary": "warm: weakest_margin=0.34, weakest_signal=volume_support",
                "weakest_met_signal": "volume_support",
                "offensive_rank": 2,
                "offensive_score": 94.77,
            },
            {
                "Code": "095610",
                "Name": "Delta",
                "act_now_risk_status": "warm",
                "act_now_risk_summary": "warm: weakest_margin=0.2, weakest_signal=breakout_ready",
                "weakest_met_signal": "breakout_ready",
                "offensive_rank": 5,
                "offensive_score": 86.51,
            },
        ]
    )

    assert competition["leader_code"] == "080220"
    assert competition["challenger_code"] == "006400"
    assert competition["summary"] == "act-now defense order: 080220 Gamma (large_rank_upgrade, margin=0.0, rank=6) -> 006400 Alpha (volume_support, margin=0.34, rank=2) -> 095610 Delta (breakout_ready, margin=0.2, rank=5)"
    assert competition["rationale"] == "080220 comes first because its risk status is hot versus warm; weakest supports are large_rank_upgrade margin 0.00 and volume_support margin 0.34."


def test_build_handoff_summary_payload_excludes_dormant_act_now_from_risk_competition() -> None:
    payload = handoff_mod.build_handoff_summary_payload(
        {
            "screening_row_count": 10,
            "filtered_row_count": 4,
            "shortlist_count": 2,
        },
        {
            "act_now_count": 3,
            "validate_now_count": 0,
            "decisions": [
                {
                    "Code": "006400",
                    "Name": "Alpha",
                    "action_label": "act_now",
                    "offensive_rank": 1,
                    "offensive_score": 95.0,
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.5, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                    "demotion_edge_summary": "breaks_first_on=breakout_ready margin=0.50",
                    "rule_trigger_summary": "promoted_core gate passed with confirmation_count=3/2; met=large_rank_upgrade,volume_support,breakout_ready",
                    "next_gate_summary": "already_cleared",
                },
                {
                    "Code": "095610",
                    "Name": "Delta",
                    "action_label": "act_now",
                    "offensive_rank": 4,
                    "offensive_score": 87.0,
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.3, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                    "demotion_edge_summary": "breaks_first_on=breakout_ready margin=0.30",
                    "rule_trigger_summary": "promoted_core gate passed with confirmation_count=2/2; met=large_rank_upgrade,breakout_ready",
                    "next_gate_summary": "already_cleared",
                },
                {
                    "Code": "080220",
                    "Name": "Gamma",
                    "action_label": "act_now",
                    "offensive_rank": 5,
                    "offensive_score": 86.0,
                    "act_now_risk_status": "off",
                    "act_now_risk_summary": "none",
                    "primary_gap_signal": "breakout_ready",
                    "nearest_signal_gap": 0.29,
                    "missing_signal_gap_summary": "breakout_ready: current=9.21, threshold=9.50, gap=0.29",
                    "weakest_met_signal": "large_rank_upgrade",
                    "demotion_edge_summary": "breaks_first_on=large_rank_upgrade margin=1.00",
                    "rule_trigger_summary": "promoted_core gate passed with confirmation_count=2/2; met=large_rank_upgrade,volume_support",
                    "next_gate_summary": "already_cleared",
                },
            ],
        },
        {"candidates": []},
        None,
        {"guard_status": "stable", "guard_summary": "No material offensive-cycle instability detected."},
    )

    assert [row["Code"] for row in payload["act_now"]] == ["006400", "095610", "080220"]
    assert [row["Code"] for row in payload["act_now_dormant"]] == ["080220"]
    assert [row["Code"] for row in payload["act_now_risk"]] == ["006400", "095610"]
    assert [row["Code"] for row in payload["act_now_defense_ladder"]] == ["006400", "095610"]
    assert [row["focus_type"] for row in payload["focus_queue"]] == ["act_now_risk", "act_now_risk", "act_now_dormant"]
    assert payload["focus_queue"][2]["operator_action"] == "recover breakout hold"
    assert "closest re-activation trigger is breakout hold" in payload["focus_queue"][2]["operator_note"]
    assert payload["focus_queue"][2]["next_gate_summary"] == "breakout_ready: current=9.21, threshold=9.50, gap=0.29"
    assert payload["act_now_competition"]["summary"] == "act-now defense order: 006400 Alpha (breakout_ready, margin=0.5, rank=1) -> 095610 Delta (breakout_ready, margin=0.3, rank=4)"
    assert payload["operator_board"]["risk_compare_summary"] == "act-now defense order: 006400 Alpha (breakout_ready, margin=0.5, rank=1) -> 095610 Delta (breakout_ready, margin=0.3, rank=4)"
    assert payload["operator_board"]["dormant_summary"] == "act_now_dormant: 080220 Gamma"
    assert payload["operator_runbook"][1]["step_type"] == "dormant_watch"
    assert payload["operator_runbook"][1]["Code"] == "080220"
    assert payload["operator_runbook"][1]["action"] == "recover breakout hold"
    report = handoff_mod.render_handoff_summary(payload)
    assert "step=2 type=dormant_watch 080220 Gamma: action=recover breakout hold, reason=breakout_ready: current=9.21, threshold=9.50, gap=0.29" in report
    assert "rank=3 type=act_now_dormant severity=dormant 080220 Gamma: reference_rank=5, summary=dormant: primary_gap=breakout_ready, nearest_gap=0.29, action=recover breakout hold" in report


def test_validate_competition_rationale_describes_single_candidate_gate() -> None:
    competition = handoff_mod._build_validate_competition(
        [
            {
                "Code": "402340",
                "Name": "Beta",
                "primary_gap_signal": "volume_support",
                "nearest_signal_gap": 1.11,
                "total_signal_gap": 5.11,
                "next_gate_summary": "needs 1 more confirmation signal for act-now; gaps=large_rank_upgrade: current=3.0, threshold=7.0, gap=4.0, volume_support: current=3.89, threshold=5.0, gap=1.11",
            }
        ]
    )

    assert competition["leader_code"] == "402340"
    assert competition["summary"] == "single validate-now candidate remains: 402340 Beta"
    assert competition["rationale"] == "402340 is the only validate-now candidate, and its closest unfinished trigger is volume_support at 1.11; total unfinished gap is 5.11. Current gate: needs 1 more confirmation signal for act-now; gaps=large_rank_upgrade: current=3.0, threshold=7.0, gap=4.0, volume_support: current=3.89, threshold=5.0, gap=1.11."
