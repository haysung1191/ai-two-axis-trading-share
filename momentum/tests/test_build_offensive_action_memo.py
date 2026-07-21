from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import build_offensive_action_memo as memo_mod


def test_build_action_memo_payload_assigns_action_labels() -> None:
    payload = memo_mod.build_action_memo_payload(
        {
            "shortlist": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "review_priority_score": 120.0,
                    "offensive_score": 88.0,
                    "offensive_rank": 3,
                    "rank_delta_vs_legacy": 12,
                    "is_promotion": True,
                    "is_leader": True,
                    "offensive_component_mom1": 12.0,
                    "offensive_component_volume": 6.0,
                    "offensive_component_breakout": 10.0,
                    "reason_tags": ["recent_strength"],
                },
                {
                    "Code": "B",
                    "Name": "Beta",
                    "review_label": "promotion_probe",
                    "review_priority_score": 100.0,
                    "offensive_score": 75.0,
                    "offensive_rank": 12,
                    "rank_delta_vs_legacy": 8,
                    "is_promotion": True,
                    "is_leader": False,
                    "offensive_component_mom1": 11.0,
                    "offensive_component_volume": 4.0,
                    "offensive_component_breakout": 9.0,
                    "reason_tags": ["volume_confirmation"],
                },
            ]
        }
    )

    assert payload["act_now_count"] == 1
    assert payload["validate_now_count"] == 1
    assert payload["decisions"][0]["action_label"] == "act_now"
    assert payload["decisions"][0]["confirmation_count"] == 3
    assert "volume_support" in payload["decisions"][0]["confirmation_signals"]
    assert "promotion_signal" in payload["decisions"][0]["action_reasons"]
    assert "gate passed" in payload["decisions"][0]["rule_trigger_summary"]
    assert payload["decisions"][0]["missing_signal_gap_summary"] == "none"
    assert payload["decisions"][0]["next_gate_summary"] == "already_cleared"
    assert payload["decisions"][0]["promotion_readiness_score"] == 0.0
    assert payload["decisions"][0]["promotion_watch_status"] == "off"
    assert payload["decisions"][0]["act_now_risk_status"] == "warm"


def test_build_action_memo_payload_demotes_weak_promoted_core() -> None:
    payload = memo_mod.build_action_memo_payload(
        {
            "shortlist": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "review_priority_score": 120.0,
                    "offensive_score": 88.0,
                    "offensive_rank": 3,
                    "rank_delta_vs_legacy": 1,
                    "is_promotion": True,
                    "is_leader": True,
                    "offensive_component_mom1": 12.0,
                    "offensive_component_volume": 4.0,
                    "offensive_component_breakout": 9.6,
                    "reason_tags": ["recent_strength"],
                }
            ]
        }
    )

    assert payload["act_now_count"] == 0
    assert payload["validate_now_count"] == 1
    assert payload["decisions"][0]["action_label"] == "validate_now"
    assert payload["decisions"][0]["confirmation_count"] == 1
    assert "missing=large_rank_upgrade,volume_support" in payload["decisions"][0]["rule_trigger_summary"]
    assert "large_rank_upgrade: current=1.00, threshold=7.00, gap=6.00" in payload["decisions"][0]["missing_signal_gap_summary"]
    assert "needs 1 more confirmation signal for act-now" in payload["decisions"][0]["next_gate_summary"]
    assert payload["decisions"][0]["primary_gap_signal"] == "volume_support"
    assert payload["decisions"][0]["nearest_signal_gap"] == 1.0
    assert payload["decisions"][0]["total_signal_gap"] == 7.0
    assert payload["decisions"][0]["validate_priority_rank"] == 1
    assert payload["decisions"][0]["validate_priority_summary"] == "closest_path=volume_support gap=1.00; total_gap=7.00; confirmations=1/2"
    assert payload["decisions"][0]["promotion_readiness_score"] > 0
    assert payload["decisions"][0]["promotion_watch_status"] == "warm"
    assert payload["decisions"][0]["promotion_watch_summary"].startswith("warm:")
    assert payload["decisions"][0]["act_now_risk_status"] == "off"


def test_build_action_memo_payload_prioritizes_smaller_validate_gap() -> None:
    payload = memo_mod.build_action_memo_payload(
        {
            "shortlist": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "review_priority_score": 130.0,
                    "offensive_score": 95.0,
                    "offensive_rank": 2,
                    "rank_delta_vs_legacy": 1,
                    "is_promotion": True,
                    "is_leader": True,
                    "offensive_component_mom1": 15.0,
                    "offensive_component_volume": 3.8,
                    "offensive_component_breakout": 10.0,
                    "reason_tags": ["recent_strength"],
                },
                {
                    "Code": "B",
                    "Name": "Beta",
                    "review_label": "promoted_core",
                    "review_priority_score": 120.0,
                    "offensive_score": 88.0,
                    "offensive_rank": 3,
                    "rank_delta_vs_legacy": 5,
                    "is_promotion": True,
                    "is_leader": True,
                    "offensive_component_mom1": 9.5,
                    "offensive_component_volume": 4.5,
                    "offensive_component_breakout": 10.0,
                    "reason_tags": ["trend_expansion"],
                },
            ]
        }
    )

    validate_rows = sorted(
        [row for row in payload["decisions"] if row["action_label"] == "validate_now"],
        key=lambda row: row["validate_priority_rank"],
    )
    assert validate_rows[0]["Code"] == "B"
    assert validate_rows[0]["validate_priority_rank"] == 1
    assert validate_rows[0]["nearest_signal_gap"] == 0.5
    assert validate_rows[0]["total_signal_gap"] == 2.5
    assert validate_rows[1]["Code"] == "A"
    assert validate_rows[1]["validate_priority_rank"] == 2


def test_build_action_memo_payload_flags_fragile_act_now() -> None:
    payload = memo_mod.build_action_memo_payload(
        {
            "shortlist": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "review_label": "promoted_core",
                    "review_priority_score": 120.0,
                    "offensive_score": 88.0,
                    "offensive_rank": 3,
                    "rank_delta_vs_legacy": 7.05,
                    "is_promotion": True,
                    "is_leader": True,
                    "offensive_component_mom1": 12.0,
                    "offensive_component_volume": 4.2,
                    "offensive_component_breakout": 9.55,
                    "reason_tags": ["recent_strength"],
                }
            ]
        }
    )

    assert payload["decisions"][0]["action_label"] == "act_now"
    assert payload["decisions"][0]["act_now_risk_status"] == "hot"
    assert payload["decisions"][0]["act_now_risk_summary"].startswith("hot:")
    assert payload["decisions"][0]["weakest_met_signal"] == "breakout_ready"


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    shortlist_path = tmp_path / "shortlist.json"
    out_json = tmp_path / "memo.json"
    out_md = tmp_path / "memo.md"
    shortlist_path.write_text(
        json.dumps(
            {
                "shortlist": [
                    {
                        "Code": "A",
                        "Name": "Alpha",
                        "review_label": "promoted_core",
                        "review_priority_score": 120.0,
                        "offensive_score": 88.0,
                        "offensive_rank": 3,
                        "rank_delta_vs_legacy": 12,
                        "is_promotion": True,
                        "is_leader": True,
                        "offensive_component_mom1": 12.0,
                        "offensive_component_volume": 6.0,
                        "offensive_component_breakout": 10.0,
                        "reason_tags": ["recent_strength"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_action_memo.py",
            "--review-shortlist-json-path",
            str(shortlist_path),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    memo_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Action Memo" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["act_now_count"] == 1
    assert "action_label=act_now" in out_md.read_text(encoding="utf-8")
    assert "next_gate=already_cleared" in out_md.read_text(encoding="utf-8")
