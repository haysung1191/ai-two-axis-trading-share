from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import build_offensive_cycle_guard as guard_mod


def test_build_cycle_guard_payload_marks_stable_when_changes_are_small() -> None:
    payload = guard_mod.build_cycle_guard_payload(
        {
            "previous_label": "prev",
            "current_label": "curr",
            "act_now_count_change": 0,
            "validate_now_count_change": 0,
            "act_now_added": [],
            "act_now_removed": [],
            "validate_now_added": [],
            "validate_now_removed": [],
            "top_candidate_score_changes": [
                {
                    "Code": "A",
                    "score_change": 0.45,
                    "rank_change": 0,
                    "component_changes": [{"component": "volume", "change": 1.5}],
                }
            ],
        },
        {
            "decisions": [
                {"Code": "A", "Name": "Alpha", "action_label": "act_now", "action_reasons": ["top_rank_leader", "breakout_ready"]},
            ]
        },
        {
            "quality_status": "stable",
            "quality_summary": "status=stable; attempted=10; fetched=10; valid=10",
            "attempted_ticker_count": 10,
            "price_fetch_success_count": 10,
            "valid_momentum_count": 10,
            "empty_price_count": 0,
            "invalid_momentum_count": 0,
            "price_fetch_coverage": 1.0,
            "success_coverage": 1.0,
        },
    )

    assert payload["guard_status"] == "stable"
    assert payload["breaches"] == []
    assert payload["metrics"]["largest_score_change"] == 0.45
    assert payload["metrics"]["screening_quality_status"] == "stable"
    assert payload["act_now_stability"][0]["stability_status"] == "stable"
    assert payload["act_now_stability"][0]["support_summary"] == "top_rank_leader, breakout_ready"
    assert payload["act_now_stability"][0]["component_summary"] == "volume=1.5"
    assert payload["act_now_stability"][0]["component_drift_severity"] == "benign"
    assert payload["screening_quality"]["quality_summary"] == "status=stable; attempted=10; fetched=10; valid=10"


def test_build_cycle_guard_payload_marks_caution_on_secondary_change() -> None:
    payload = guard_mod.build_cycle_guard_payload(
        {
            "previous_label": "prev",
            "current_label": "curr",
            "act_now_count_change": 0,
            "validate_now_count_change": 1,
            "act_now_added": [],
            "act_now_removed": [],
            "validate_now_added": ["B"],
            "validate_now_removed": [],
            "top_candidate_score_changes": [{"Code": "A", "score_change": 0.2, "rank_change": 0}],
        }
    )

    assert payload["guard_status"] == "caution"
    assert payload["review_flags"] == []
    assert "validate_now_count_change" in payload["caution_flags"]
    assert "validate_now_membership_change" in payload["caution_flags"]


def test_build_cycle_guard_payload_marks_review_on_act_now_membership_change() -> None:
    payload = guard_mod.build_cycle_guard_payload(
        {
            "previous_label": "prev",
            "current_label": "curr",
            "act_now_count_change": 1,
            "validate_now_count_change": 0,
            "act_now_added": ["A"],
            "act_now_removed": [],
            "validate_now_added": [],
            "validate_now_removed": [],
            "top_candidate_score_changes": [{"Code": "A", "score_change": 0.2, "rank_change": 0}],
        },
        {
            "decisions": [
                {"Code": "A", "Name": "Alpha", "action_label": "act_now", "action_reasons": ["top_rank_leader"]},
            ]
        },
    )

    assert payload["guard_status"] == "review"
    assert "act_now_count_change" in payload["review_flags"]
    assert "act_now_membership_change" in payload["review_flags"]
    assert payload["act_now_stability"][0]["stability_status"] == "review"


def test_build_cycle_guard_payload_marks_watch_on_negative_mom1_drift() -> None:
    payload = guard_mod.build_cycle_guard_payload(
        {
            "previous_label": "prev",
            "current_label": "curr",
            "act_now_count_change": 0,
            "validate_now_count_change": 0,
            "act_now_added": [],
            "act_now_removed": [],
            "validate_now_added": [],
            "validate_now_removed": [],
            "top_candidate_score_changes": [
                {
                    "Code": "A",
                    "score_change": -0.2,
                    "rank_change": 0,
                    "component_changes": [{"component": "mom1", "change": -0.1}],
                }
            ],
        },
        {
            "decisions": [
                {"Code": "A", "Name": "Alpha", "action_label": "act_now", "action_reasons": ["top_rank_leader"]},
            ]
        },
    )

    assert payload["act_now_stability"][0]["component_drift_severity"] == "watch"


def test_build_cycle_guard_payload_marks_caution_on_screening_quality_caution() -> None:
    payload = guard_mod.build_cycle_guard_payload(
        {
            "previous_label": "prev",
            "current_label": "curr",
            "act_now_count_change": 0,
            "validate_now_count_change": 0,
            "act_now_added": [],
            "act_now_removed": [],
            "validate_now_added": [],
            "validate_now_removed": [],
            "top_candidate_score_changes": [],
        },
        None,
        {
            "quality_status": "caution",
            "quality_summary": "status=caution; attempted=30; fetched=27; valid=26",
            "attempted_ticker_count": 30,
            "price_fetch_success_count": 27,
            "valid_momentum_count": 26,
            "empty_price_count": 3,
            "invalid_momentum_count": 1,
            "price_fetch_coverage": 0.9,
            "success_coverage": 0.87,
            "empty_price_codes_sample": ["111111"],
            "invalid_momentum_codes_sample": ["222222"],
        },
    )

    assert payload["guard_status"] == "caution"
    assert "screening_quality_caution" in payload["caution_flags"]
    assert payload["screening_quality"]["codes"]["empty_price_codes_sample"] == ["111111"]
    assert payload["metrics"]["screening_empty_price_count"] == 3


def test_build_cycle_guard_payload_marks_review_on_screening_quality_review() -> None:
    payload = guard_mod.build_cycle_guard_payload(
        {
            "previous_label": "prev",
            "current_label": "curr",
            "act_now_count_change": 0,
            "validate_now_count_change": 0,
            "act_now_added": [],
            "act_now_removed": [],
            "validate_now_added": [],
            "validate_now_removed": [],
            "top_candidate_score_changes": [],
        },
        None,
        {
            "quality_status": "review",
            "quality_summary": "status=review; attempted=30; fetched=20; valid=18",
            "attempted_ticker_count": 30,
            "price_fetch_success_count": 20,
            "valid_momentum_count": 18,
            "empty_price_count": 10,
            "invalid_momentum_count": 2,
            "price_fetch_coverage": 0.67,
            "success_coverage": 0.6,
        },
    )

    assert payload["guard_status"] == "review"
    assert "screening_quality_review" in payload["review_flags"]
    assert "degraded enough" in payload["guard_summary"]


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    diff_path = tmp_path / "diff.json"
    action_path = tmp_path / "action.json"
    quality_path = tmp_path / "quality.json"
    out_json = tmp_path / "guard.json"
    out_md = tmp_path / "guard.md"
    diff_path.write_text(
        json.dumps(
            {
                "previous_label": "prev",
                "current_label": "curr",
                "act_now_count_change": 0,
                "validate_now_count_change": 0,
                "act_now_added": [],
                "act_now_removed": [],
                "validate_now_added": [],
                "validate_now_removed": [],
                "top_candidate_score_changes": [],
            }
        ),
        encoding="utf-8",
    )
    action_path.write_text(
        json.dumps(
            {
                "decisions": [
                    {"Code": "A", "Name": "Alpha", "action_label": "act_now", "action_reasons": ["top_rank_leader"]}
                ]
            }
        ),
        encoding="utf-8",
    )
    quality_path.write_text(
        json.dumps(
            {
                "quality_status": "stable",
                "quality_summary": "status=stable; attempted=1; fetched=1; valid=1",
                "attempted_ticker_count": 1,
                "price_fetch_success_count": 1,
                "valid_momentum_count": 1,
                "empty_price_count": 0,
                "invalid_momentum_count": 0,
                "price_fetch_coverage": 1.0,
                "success_coverage": 1.0,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_cycle_guard.py",
            "--cycle-diff-json-path",
            str(diff_path),
            "--action-memo-json-path",
            str(action_path),
            "--screening-quality-json-path",
            str(quality_path),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    guard_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Cycle Guard" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["guard_status"] == "stable"
    assert "## Act Now Stability" in out_md.read_text(encoding="utf-8")
    assert "## Screening Quality" in out_md.read_text(encoding="utf-8")
    assert "support=" in out_md.read_text(encoding="utf-8")
    assert "## Breaches" in out_md.read_text(encoding="utf-8")
