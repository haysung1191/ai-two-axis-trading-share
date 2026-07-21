from __future__ import annotations

import json
from pathlib import Path

from scripts import compare_btc_1d_attack_main_backup_screen as screen_script
from scripts.compare_btc_1d_attack_main_backup_screen import build_report


def test_compare_btc_1d_attack_main_backup_screen_keeps_ratio112_as_main() -> None:
    report = build_report()
    assert report["stack_top"]["attack_main"] == "ratio112_tighter_stop_main"
    assert report["backup_verdict"]["preferred_main"] == "ratio112_tighter_stop_main"
    assert report["backup_verdict"]["main_backup_roles_are_distinct"] is True


def test_compare_btc_1d_attack_main_backup_screen_promotes_post_spike_as_backup() -> None:
    report = build_report()
    assert report["stack_top"]["attack_backup"] == "bridge_28_relief"
    assert report["stack_top"]["attack_challenger"] == "post_spike_trend960_depth055_volume100_hold36"
    backup = next(item for item in report["compared_models"] if item["label"] == "bridge_28_relief")
    assert backup["role"] == "attack_backup"


def test_compare_btc_1d_attack_main_backup_screen_surfaces_research_focus() -> None:
    report = build_report()

    assert report["attack_research_focus"]["target_slot"] == "attack_challenger"
    assert report["attack_research_focus"]["target_label"] == "post_spike_trend960_depth055_volume100_hold36"
    assert report["attack_research_focus"]["next_research_step_now"] == "expand_post_spike_trend_family_to_recover_idle_windows"


def test_compare_btc_1d_attack_main_backup_screen_main_writes_latest_aliases(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(screen_script, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        screen_script,
        "build_report",
        lambda: {
            "stack_top": {
                "attack_main": "ratio112_tighter_stop_main",
                "attack_backup": "bridge_28_relief",
                "attack_challenger": "post_spike_trend960_depth055_volume100_hold36",
            },
            "compared_models": [],
            "attack_research_focus": {
                "target_slot": "attack_challenger",
                "target_label": "depth055_volume100_hold36",
                "focus_area": "attack_challenger_promotion_review",
                "next_research_step_now": "apply_approved_attack_challenger_rotation",
            },
            "backup_verdict": {
                "main_backup_roles_are_distinct": True,
                "reason": "ok",
            },
        },
    )

    exit_code = screen_script.main()

    assert exit_code == 0
    latest_json = tmp_path / "btc_1d_attack_main_backup_screen_latest.json"
    latest_md = tmp_path / "btc_1d_attack_main_backup_screen_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
    payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert payload["attack_research_focus"]["target_slot"] == "attack_challenger"
