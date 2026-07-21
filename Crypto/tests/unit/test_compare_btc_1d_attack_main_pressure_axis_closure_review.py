from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_attack_main_pressure_axis_closure_review as mod


def test_axis_closure_review_builds_from_latest_axis_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_escalation_review",
        lambda: {
            "escalation_reference": {
                "attack_main": "main_a",
                "promoted_attack_backup": "backup_b",
                "monitoring_candidate": "backup_b::hold36",
            },
            "watch_status": {
                "primary_blocker": "base_cagr_gap",
            },
            "remaining_to_open": {
                "remaining_base_cagr_gap": 0.037,
                "remaining_cost20_cagr_gap": 0.0,
            },
        },
    )

    for axis_name, prefix in mod.AXIS_FILES.items():
        payload = {
            "best_variant": {
                "variant_label": "active_anchor" if axis_name in {"challenger_reopen", "base_gap_recovery"} else "hold36_anchor",
                "base_cagr_gap_to_main": 0.08,
                "cost20_cagr_gap_to_main": 0.05,
                "quality_pressure_passed": axis_name != "entry_timing",
                "replacement_open_passed": False,
            }
        }
        (tmp_path / f"{prefix}20260419T000000Z.json").write_text(json.dumps(payload), encoding="utf-8")

    report = mod.build_report()

    assert report["axis_closure_summary"]["evaluated_axis_count"] == len(mod.AXIS_FILES)
    assert report["axis_closure_summary"]["all_current_hold36_axes_closed"] is True
    assert report["axis_closure_summary"]["next_step_now"] == "formalize_hold36_pressure_watch_ceiling"
    assert "entry_timing" in report["axis_closure_summary"]["quality_failed_axes"]
