from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from live_core.kis_screener_runner import annotate_stock_ranking_comparison
from tools.analysis import build_offensive_screener_comparison_report as report_mod


def test_annotate_stock_ranking_comparison_adds_rank_columns() -> None:
    df = pd.DataFrame(
        [
            {"Code": "A", "Name": "Alpha", "offensive_score": 50.0, "MAD_gap_pct": 10.0},
            {"Code": "B", "Name": "Beta", "offensive_score": 80.0, "MAD_gap_pct": 5.0},
            {"Code": "C", "Name": "Gamma", "offensive_score": 20.0, "MAD_gap_pct": 30.0},
        ]
    )

    annotated = annotate_stock_ranking_comparison(df)

    assert list(annotated["offensive_rank"]) == [2, 1, 3]
    assert list(annotated["legacy_mad_rank"]) == [2, 3, 1]
    assert list(annotated["rank_delta_vs_legacy"]) == [0, 2, -2]


def test_build_comparison_payload_returns_leaders_and_promotions() -> None:
    df = pd.DataFrame(
        [
            {"Code": "A", "Name": "Alpha", "offensive_score": 50.0, "MAD_gap_pct": 10.0, "momentum_12m": 50.0},
            {
                "Code": "B",
                "Name": "Beta",
                "offensive_score": 80.0,
                "MAD_gap_pct": 5.0,
                "momentum_12m": 250.0,
                "offensive_component_mom12": 30.0,
                "offensive_component_mom6": 18.0,
                "offensive_component_mom1": 12.0,
                "offensive_component_trend": 5.0,
                "offensive_component_breakout": 8.0,
                "offensive_component_volume": 7.0,
            },
            {"Code": "C", "Name": "Gamma", "offensive_score": 20.0, "MAD_gap_pct": 30.0, "momentum_12m": 20.0},
        ]
    )

    payload = report_mod.build_comparison_payload(df, top_n=2)

    assert payload["row_count"] == 3
    assert payload["leaders"][0]["Code"] == "B"
    assert payload["biggest_promotions"][0]["Code"] == "B"
    assert "long_term_momentum" in payload["leaders"][0]["reason_tags"]
    assert payload["leaders"][0]["offensive_component_mom12"] == 30.0


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    csv_path = tmp_path / "screening.csv"
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    pd.DataFrame(
        [
            {"Code": "A", "Name": "Alpha", "offensive_score": 50.0, "MAD_gap_pct": 10.0, "momentum_12m": 50.0},
            {
                "Code": "B",
                "Name": "Beta",
                "offensive_score": 80.0,
                "MAD_gap_pct": 55.0,
                "momentum_12m": 250.0,
                "offensive_component_mom12": 30.0,
                "offensive_component_mom6": 18.0,
                "offensive_component_mom1": 12.0,
                "offensive_component_trend": 5.0,
                "offensive_component_breakout": 8.0,
                "offensive_component_volume": 7.0,
            },
        ]
    ).to_csv(csv_path, index=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_screener_comparison_report.py",
            "--screening-csv",
            str(csv_path),
            "--output-json-path",
            str(json_path),
            "--output-md-path",
            str(md_path),
        ],
    )

    report_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Screener Comparison" in output
    assert json.loads(json_path.read_text(encoding="utf-8"))["leaders"][0]["Code"] == "B"
    assert "## Biggest Promotions" in md_path.read_text(encoding="utf-8")
    assert "reason_tags=" in md_path.read_text(encoding="utf-8")
    assert "score_components=mom12=30.0" in md_path.read_text(encoding="utf-8")
