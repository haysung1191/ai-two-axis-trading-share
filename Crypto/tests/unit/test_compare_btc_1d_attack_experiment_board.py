from __future__ import annotations

import json
from pathlib import Path

from scripts import compare_btc_1d_attack_experiment_board as board_script
from scripts.compare_btc_1d_attack_experiment_board import build_report


def test_attack_experiment_board_keeps_stack_and_adds_challenger() -> None:
    report = build_report()
    verdict = report["board_verdict"]

    assert verdict["active_attack_main"] == "ratio112_tighter_stop_main"
    assert verdict["active_attack_backup"] == "bridge_28_relief"
    assert verdict["active_attack_challenger"] == "post_spike_trend960_depth055_volume100_hold36"
    assert verdict["board_ready"] is True


def test_attack_experiment_board_orders_main_backup_challenger() -> None:
    report = build_report()
    rows = report["attack_experiment_board"]

    assert [row["slot"] for row in rows] == [
        "attack_main",
        "attack_backup",
        "attack_challenger",
    ]
    assert rows[2]["board_status"] == "experiment_challenger"


def test_attack_experiment_board_surfaces_next_research_step() -> None:
    report = build_report()

    assert report["board_verdict"]["next_research_step_now"] == "expand_post_spike_trend_family_to_recover_idle_windows"
    assert report["attack_research_focus"]["target_slot"] == "attack_challenger"
    assert report["attack_research_focus"]["target_label"] == "post_spike_trend960_depth055_volume100_hold36"


def test_attack_experiment_board_main_writes_latest_aliases(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(board_script, "ANALYSIS_DIR", tmp_path)

    exit_code = board_script.main()

    assert exit_code == 0
    latest_json = tmp_path / "btc_1d_attack_experiment_board_latest.json"
    latest_md = tmp_path / "btc_1d_attack_experiment_board_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
    payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert payload["board_verdict"]["next_research_step_now"] == "expand_post_spike_trend_family_to_recover_idle_windows"
