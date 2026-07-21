from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import build_offensive_cycle_diff as diff_mod


def test_build_cycle_diff_payload_tracks_action_changes() -> None:
    payload = diff_mod.build_cycle_diff_payload(
        {
            "act_now_count": 1,
            "validate_now_count": 1,
            "act_now": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "action_label": "act_now",
                    "confirmation_count": 1,
                    "confirmation_signals": ["breakout_ready"],
                    "rule_trigger_summary": "promoted_core kept but act-now confirmation_count=1/2; met=breakout_ready; missing=large_rank_upgrade,volume_support",
                    "act_now_risk_status": "off",
                    "act_now_risk_summary": "none",
                    "weakest_met_signal": "none",
                }
            ],
            "validate_now": [
                {
                    "Code": "B",
                    "Name": "Beta",
                    "action_label": "validate_now",
                    "confirmation_count": 1,
                    "confirmation_signals": ["breakout_ready"],
                    "rule_trigger_summary": "promoted_core kept but act-now confirmation_count=1/2; met=breakout_ready; missing=large_rank_upgrade,volume_support",
                    "validate_priority_rank": 2,
                    "promotion_readiness_score": 81.0,
                    "missing_signal_count": 2,
                    "primary_gap_signal": "volume_support",
                }
            ],
            "top_candidates": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "offensive_score": 80.0,
                    "offensive_rank": 2,
                    "offensive_component_mom1": 10.0,
                    "offensive_component_volume": 4.0,
                    "offensive_component_breakout": 8.0,
                }
            ],
        },
        {
            "act_now_count": 2,
            "validate_now_count": 0,
            "act_now": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "action_label": "act_now",
                    "confirmation_count": 3,
                    "confirmation_signals": ["large_rank_upgrade", "volume_support", "breakout_ready"],
                    "rule_trigger_summary": "promoted_core gate passed with confirmation_count=3/2; met=large_rank_upgrade,volume_support,breakout_ready",
                    "act_now_risk_status": "warm",
                    "act_now_risk_summary": "warm: weakest_margin=0.5, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                },
                {
                    "Code": "C",
                    "Name": "Gamma",
                    "action_label": "act_now",
                    "confirmation_count": 2,
                    "confirmation_signals": ["volume_support", "breakout_ready"],
                    "rule_trigger_summary": "core_leader gate passed with review_priority_score=120.0 and confirmation_count=2/2; met=volume_support,breakout_ready",
                    "act_now_risk_status": "hot",
                    "act_now_risk_summary": "hot: weakest_margin=0.1, weakest_signal=breakout_ready",
                    "weakest_met_signal": "breakout_ready",
                },
            ],
            "validate_now": [],
            "top_candidates": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "offensive_score": 85.0,
                    "offensive_rank": 1,
                    "offensive_component_mom1": 12.0,
                    "offensive_component_volume": 5.5,
                    "offensive_component_breakout": 9.0,
                }
            ],
        },
        previous_label="prev",
        current_label="curr",
    )

    assert payload["act_now_count_change"] == 1
    assert payload["validate_now_count_change"] == -1
    assert payload["act_now_added"] == ["C"]
    assert payload["validate_now_removed"] == ["B"]
    assert payload["top_candidate_score_changes"][0]["score_change"] == 5.0
    assert payload["top_candidate_score_changes"][0]["component_changes"][0]["component"] == "mom1"
    codes = [row["Code"] for row in payload["action_state_changes"]]
    assert set(codes) == {"A", "B", "C"}
    alpha_change = next(row for row in payload["action_state_changes"] if row["Code"] == "A")
    beta_change = next(row for row in payload["action_state_changes"] if row["Code"] == "B")
    gamma_change = next(row for row in payload["action_state_changes"] if row["Code"] == "C")
    assert alpha_change["confirmation_count_change"] == 2
    assert alpha_change["signals_added"] == ["large_rank_upgrade", "volume_support"]
    assert beta_change["current_action_label"] == "outside_watchlist"
    assert gamma_change["previous_action_label"] == "outside_watchlist"
    validate_change = payload["validate_priority_changes"][0]
    assert validate_change["Code"] == "B"
    assert validate_change["previous_validate_priority_rank"] == 2
    assert validate_change["current_validate_priority_rank"] is None
    assert validate_change["readiness_score_change"] == -81.0
    risk_changes = payload["act_now_risk_changes"]
    assert any(row["Code"] == "A" and row["current_act_now_risk_status"] == "warm" for row in risk_changes)
    assert any(row["Code"] == "C" and row["current_act_now_risk_status"] == "hot" for row in risk_changes)


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    prev_path = tmp_path / "prev.json"
    curr_path = tmp_path / "curr.json"
    out_json = tmp_path / "diff.json"
    out_md = tmp_path / "diff.md"
    prev_path.write_text(json.dumps({"act_now_count": 0, "validate_now_count": 1, "act_now": [], "validate_now": [{"Code": "B"}], "top_candidates": []}), encoding="utf-8")
    curr_path.write_text(json.dumps({"act_now_count": 1, "validate_now_count": 0, "act_now": [{"Code": "A"}], "validate_now": [], "top_candidates": []}), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_cycle_diff.py",
            "--previous-json-path",
            str(prev_path),
            "--current-json-path",
            str(curr_path),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    diff_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Cycle Diff" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["act_now_added"] == ["A"]
    assert "## Validate Now Removed" in out_md.read_text(encoding="utf-8")
    assert "## Action State Changes" in out_md.read_text(encoding="utf-8")
    assert "## Validate Priority Changes" in out_md.read_text(encoding="utf-8")
    assert "## Act Now Risk Changes" in out_md.read_text(encoding="utf-8")
