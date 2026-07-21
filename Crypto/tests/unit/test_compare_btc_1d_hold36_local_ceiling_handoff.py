from __future__ import annotations

from scripts.compare_btc_1d_hold36_local_ceiling_handoff import build_report


def test_hold36_local_ceiling_handoff_marks_local_loop_closed() -> None:
    report = build_report()
    status = report["local_ceiling_status"]

    assert report["handoff_reference"]["active_backup"] == "post_spike_trend92_depth058_volume105_hold36"
    assert status["ceiling_confirmed"] is True
    assert status["do_not_repeat_local_loop"] is True
    assert status["next_step_now"] == "open_only_new_family_or_wider_frame_search"


def test_hold36_local_ceiling_handoff_lists_closed_axes() -> None:
    report = build_report()
    status = report["local_ceiling_status"]
    rules = report["handoff_rules"]

    assert "entry_timing" in status["closed_local_axes"]
    assert "entry_strength" in status["closed_local_axes"]
    assert "structure" in status["closed_local_axes"]
    assert "base_gap_recovery" in rules["do_not_restart"]
