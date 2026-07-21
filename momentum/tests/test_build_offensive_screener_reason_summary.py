from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import build_offensive_screener_reason_summary as summary_mod


def test_build_reason_summary_payload_counts_tags() -> None:
    payload = summary_mod.build_reason_summary_payload(
        [
            {
                "leaders": [
                    {
                        "reason_tags": ["long_term_momentum", "near_breakout"],
                        "offensive_component_mom12": 30.0,
                        "offensive_component_mom6": 10.0,
                    },
                    {
                        "reason_tags": ["long_term_momentum"],
                        "offensive_component_mom12": 20.0,
                        "offensive_component_mom1": 12.0,
                    },
                ],
                "biggest_promotions": [
                    {
                        "reason_tags": ["volume_confirmation"],
                        "offensive_component_volume": 8.0,
                        "offensive_component_breakout": 7.0,
                    },
                ],
            },
            {
                "leaders": [
                    {
                        "reason_tags": ["near_breakout"],
                        "offensive_component_breakout": 9.0,
                        "offensive_component_mom12": 5.0,
                    },
                ],
                "biggest_promotions": [
                    {
                        "reason_tags": ["volume_confirmation", "near_breakout"],
                        "offensive_component_volume": 9.0,
                        "offensive_component_mom1": 6.0,
                    },
                ],
            },
        ]
    )

    assert payload["report_count"] == 2
    assert payload["leader_reason_frequency"][0] == {"reason_tag": "long_term_momentum", "count": 2}
    assert {"reason_tag": "volume_confirmation", "count": 2} in payload["promotion_reason_frequency"]
    assert payload["leader_component_profile"]["row_count"] == 3
    assert payload["leader_component_profile"]["average_components"][0]["component"] == "offensive_component_mom12"
    assert {"component": "offensive_component_volume", "count": 2} in payload["promotion_component_profile"]["top_component_frequency"]


def test_main_reads_reports_and_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "offensive_screening_report_latest.json").write_text(
        json.dumps(
            {
                "leaders": [{"reason_tags": ["long_term_momentum"], "offensive_component_mom12": 30.0}],
                "biggest_promotions": [{"reason_tags": ["volume_confirmation"], "offensive_component_volume": 8.0}],
            }
        ),
        encoding="utf-8",
    )
    out_json = tmp_path / "summary.json"
    out_md = tmp_path / "summary.md"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_screener_reason_summary.py",
            "--report-dir",
            str(report_dir),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    summary_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Screener Reason Summary" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["report_count"] == 1
    assert "## Promotion Reason Frequency" in out_md.read_text(encoding="utf-8")
    assert "## Leader Component Profile" in out_md.read_text(encoding="utf-8")
