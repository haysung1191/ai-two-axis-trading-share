from __future__ import annotations

from scripts.publish_btc_1d_hold36_local_ceiling_latest import publish_latest


def test_publish_hold36_local_ceiling_latest_copies_latest_files(tmp_path) -> None:
    handoff_json = tmp_path / "btc_1d_hold36_local_ceiling_handoff_20260420T000000Z.json"
    handoff_md = tmp_path / "btc_1d_hold36_local_ceiling_handoff_20260420T000000Z.md"
    ceiling_json = tmp_path / "btc_1d_hold36_pressure_watch_ceiling_20260420T000000Z.json"
    ceiling_md = tmp_path / "btc_1d_hold36_pressure_watch_ceiling_20260420T000000Z.md"

    handoff_json.write_text('{"kind":"handoff"}', encoding="utf-8")
    handoff_md.write_text("# handoff", encoding="utf-8")
    ceiling_json.write_text('{"kind":"ceiling"}', encoding="utf-8")
    ceiling_md.write_text("# ceiling", encoding="utf-8")

    result = publish_latest(analysis_dir=tmp_path)

    assert result["handoff_latest_json"].endswith("btc_1d_hold36_local_ceiling_handoff_latest.json")
    assert result["ceiling_latest_json"].endswith("btc_1d_hold36_pressure_watch_ceiling_latest.json")
    assert (tmp_path / "btc_1d_hold36_local_ceiling_handoff_latest.json").read_text(encoding="utf-8") == '{"kind":"handoff"}'
    assert (tmp_path / "btc_1d_hold36_pressure_watch_ceiling_latest.json").read_text(encoding="utf-8") == '{"kind":"ceiling"}'
