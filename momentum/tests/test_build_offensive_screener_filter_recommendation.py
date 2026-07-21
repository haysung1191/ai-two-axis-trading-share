from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import build_offensive_screener_filter_recommendation as rec_mod


def test_build_filter_recommendation_payload_flags_weak_promotions() -> None:
    payload = rec_mod.build_filter_recommendation_payload(
        {
            "leaders": [
                {
                    "Code": "L1",
                    "offensive_component_mom1": 10.0,
                    "offensive_component_volume": 4.0,
                    "offensive_component_breakout": 8.5,
                },
                {
                    "Code": "L2",
                    "offensive_component_mom1": 12.0,
                    "offensive_component_volume": 5.0,
                    "offensive_component_breakout": 9.0,
                },
            ],
            "biggest_promotions": [
                {
                    "Code": "P1",
                    "Name": "Pass",
                    "offensive_score": 80.0,
                    "offensive_component_mom1": 11.0,
                    "offensive_component_volume": 4.2,
                    "offensive_component_breakout": 9.3,
                },
                {
                    "Code": "P2",
                    "Name": "Fail",
                    "offensive_score": 75.0,
                    "offensive_component_mom1": 6.0,
                    "offensive_component_volume": 3.0,
                    "offensive_component_breakout": 7.0,
                },
            ],
        }
    )

    assert payload["recommended_thresholds"]["offensive_component_mom1"] == 10.0
    assert payload["promotion_pass_count"] == 1
    assert payload["promotion_fail_count"] == 1
    assert payload["promotion_assessments"][1]["passes_filter"] is False
    assert payload["promotion_assessments"][1]["failed_metrics"][0]["metric"] == "offensive_component_mom1"


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "report.json"
    out_json = tmp_path / "recommendation.json"
    out_md = tmp_path / "recommendation.md"
    report_path.write_text(
        json.dumps(
            {
                "leaders": [
                    {
                        "Code": "L1",
                        "offensive_component_mom1": 10.0,
                        "offensive_component_volume": 4.0,
                        "offensive_component_breakout": 8.5,
                    }
                ],
                "biggest_promotions": [
                    {
                        "Code": "P1",
                        "Name": "Promo",
                        "offensive_score": 70.0,
                        "offensive_component_mom1": 8.0,
                        "offensive_component_volume": 4.5,
                        "offensive_component_breakout": 8.5,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_screener_filter_recommendation.py",
            "--report-json-path",
            str(report_path),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    rec_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Screener Filter Recommendation" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["promotion_fail_count"] == 1
    assert "failed_metrics=offensive_component_mom1=8.0<10.0" in out_md.read_text(encoding="utf-8")
