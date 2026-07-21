from __future__ import annotations

from pathlib import Path

from scripts.compare_btc_1d_recent_family_screen import build_recent_family_screen


def test_recent_family_screen_builds_outputs(tmp_path: Path) -> None:
    result = build_recent_family_screen(analysis_results_dir=tmp_path)

    assert result["summary"]["total_families"] >= 20
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_md"]).exists()
    assert result["rows"][0]["cagr"] >= result["rows"][-1]["cagr"]


def test_recent_family_screen_has_pattern_summary(tmp_path: Path) -> None:
    result = build_recent_family_screen(analysis_results_dir=tmp_path)

    assert "compression_reset" in result["pattern_summary"]
    assert "reclaim_grab" in result["pattern_summary"]
    assert result["summary"]["low_alpha_or_kill"] >= result["summary"]["defensive_holds"]
