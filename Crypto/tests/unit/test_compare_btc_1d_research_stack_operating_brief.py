from __future__ import annotations

from pathlib import Path

from scripts.compare_btc_1d_research_stack_operating_brief import _render_markdown, _write_latest_aliases, build_report


def test_research_stack_operating_brief_keeps_frontier_structure() -> None:
    report = build_report()
    assert report["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert report["standard_check_order_reference"] == ["practical", "research", "contract", "brief"]
    assert report["quick_read_order_version"] == "research_stack_v2"
    assert report["quick_read_order"] == [
        "quick_read",
        "stack_roles",
        "stack",
        "local_ceiling",
        "near_miss_priority",
        "operating_read",
    ]
    assert report["operating_brief"]["attack_frontier"] == "ratio112_tighter_stop_main"
    assert report["operating_brief"]["attack_backup"] == "bridge_28_relief"
    assert (
        report["operating_brief"]["attack_challenger"]
        == "post_spike_trend960_depth055_volume100_hold36"
    )
    assert report["local_ceiling"]["status_band"] == "pressure_watch"
    assert report["local_ceiling"]["do_not_repeat_local_loop"] is True


def test_research_stack_operating_brief_keeps_near_miss_priority() -> None:
    report = build_report()
    assert report["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert report["operating_brief"]["highest_priority_near_miss"] == "trend_dip_reversal_breakout_tighter_stop_mid_hold"
    assert report["operating_brief"]["highest_raw_upside_near_miss"] == "volatility_spike_reversal_continuation_slower_trend"
    assert report["paths"]["quick_read_contract_screen"].endswith("btc_1d_quick_read_contract_screen_latest.json")
    assert report["paths"]["quick_read_contract_screen_md"].endswith("btc_1d_quick_read_contract_screen_md_latest.md")
    assert report["paths"]["meta_contract_screen"].endswith("btc_1d_meta_contract_screen_latest.json")
    assert report["paths"]["meta_contract_screen_md"].endswith("btc_1d_meta_contract_screen_md_latest.md")


def test_research_stack_operating_brief_markdown_starts_with_quick_read() -> None:
    rendered = _render_markdown(build_report())
    quick_read_pos = rendered.index("## Quick Read")
    stack_roles_pos = rendered.index("## Stack Roles")
    local_ceiling_pos = rendered.index("## Local Ceiling")
    operating_read_pos = rendered.index("## Operating Read")
    assert quick_read_pos < stack_roles_pos < local_ceiling_pos < operating_read_pos
    assert "Attack backup: `bridge_28_relief`" in rendered
    assert "Attack challenger: `post_spike_trend960_depth055_volume100_hold36`" in rendered
    assert "Status band: `pressure_watch`" in rendered
    assert "Quick-read contract screen: `analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md`" in rendered
    assert "Meta contract screen: `analysis_results\\btc_1d_meta_contract_screen_md_latest.md`" in rendered


def test_research_stack_operating_brief_writes_latest_aliases(tmp_path: Path) -> None:
    json_path = tmp_path / "btc_1d_research_stack_operating_brief_20260416T000000Z.json"
    md_path = tmp_path / "btc_1d_research_stack_operating_brief_20260416T000000Z.md"
    json_path.write_text('{"ok": true}', encoding="utf-8")
    md_path.write_text("# ok", encoding="utf-8")

    aliases = _write_latest_aliases(json_path, md_path)

    latest_json = Path(aliases["btc_1d_research_stack_operating_brief"])
    latest_md = Path(aliases["btc_1d_research_stack_operating_brief_md"])
    assert latest_json.name == "btc_1d_research_stack_operating_brief_latest.json"
    assert latest_json.read_text(encoding="utf-8") == '{"ok": true}'
    assert latest_md.name == "btc_1d_research_stack_operating_brief_md_latest.md"
    assert latest_md.read_text(encoding="utf-8") == "# ok"
