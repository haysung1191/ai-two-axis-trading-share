from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from tools.analysis import apply_offensive_screener_filter as filter_mod


def test_build_filter_application_payload_counts_passed_and_failed() -> None:
    df = pd.DataFrame(
        [
            {
                "Code": "A",
                "offensive_component_mom1": 4.0,
                "offensive_component_volume": 4.0,
                "offensive_component_breakout": 8.0,
            },
            {
                "Code": "B",
                "offensive_component_mom1": 2.0,
                "offensive_component_volume": 4.0,
                "offensive_component_breakout": 8.0,
            },
        ]
    )
    recommendation = {
        "recommended_thresholds": {
            "offensive_component_mom1": 3.5,
            "offensive_component_volume": 3.8,
            "offensive_component_breakout": 8.0,
        }
    }

    payload = filter_mod.build_filter_application_payload(df, recommendation)

    assert payload["input_row_count"] == 2
    assert payload["passed_row_count"] == 1
    assert payload["failed_row_count"] == 1
    assert payload["passed_codes"] == ["A"]
    assert payload["failed_codes"] == ["B"]


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    screening_path = tmp_path / "screening.csv"
    recommendation_path = tmp_path / "recommendation.json"
    out_passed = tmp_path / "passed.csv"
    out_failed = tmp_path / "failed.csv"
    out_json = tmp_path / "summary.json"
    out_md = tmp_path / "summary.md"

    pd.DataFrame(
        [
            {
                "Code": "A",
                "offensive_component_mom1": 4.0,
                "offensive_component_volume": 4.0,
                "offensive_component_breakout": 8.0,
            },
            {
                "Code": "B",
                "offensive_component_mom1": 2.0,
                "offensive_component_volume": 4.0,
                "offensive_component_breakout": 8.0,
            },
        ]
    ).to_csv(screening_path, index=False)
    recommendation_path.write_text(
        json.dumps(
            {
                "recommended_thresholds": {
                    "offensive_component_mom1": 3.5,
                    "offensive_component_volume": 3.8,
                    "offensive_component_breakout": 8.0,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/apply_offensive_screener_filter.py",
            "--screening-csv-path",
            str(screening_path),
            "--recommendation-json-path",
            str(recommendation_path),
            "--output-passed-csv-path",
            str(out_passed),
            "--output-failed-csv-path",
            str(out_failed),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    filter_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Screener Filter Application" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["passed_row_count"] == 1
    assert pd.read_csv(out_passed)["Code"].astype(str).tolist() == ["A"]
    assert pd.read_csv(out_failed)["Code"].astype(str).tolist() == ["B"]


def test_build_filter_application_payload_preserves_leading_zero_codes() -> None:
    df = pd.DataFrame(
        [
            {
                "Code": "007810",
                "offensive_component_mom1": 4.0,
                "offensive_component_volume": 4.0,
                "offensive_component_breakout": 8.0,
            }
        ]
    )
    recommendation = {
        "recommended_thresholds": {
            "offensive_component_mom1": 3.5,
            "offensive_component_volume": 3.8,
            "offensive_component_breakout": 8.0,
        }
    }

    payload = filter_mod.build_filter_application_payload(df, recommendation)

    assert payload["passed_codes"] == ["007810"]
