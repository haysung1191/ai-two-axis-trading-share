from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from tools.analysis import run_offensive_screener_cycle as cycle_mod


def test_build_cycle_payload() -> None:
    payload = cycle_mod.build_cycle_payload(
        "screening.csv",
        "report.json",
        "report.md",
        row_count=3,
        top_n=5,
        etf_mode=False,
        stock_sort_column="offensive_score",
    )

    assert payload["row_count"] == 3
    assert payload["top_n"] == 5
    assert payload["stock_sort_column"] == "offensive_score"


def test_main_runs_cycle_and_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    class FakeScreener:
        def run(self, max_items, etf_mode, stock_sort_column):
            assert max_items == 25
            assert etf_mode is False
            assert stock_sort_column == "offensive_score"
            return pd.DataFrame(
                [
                    {"Code": "B", "Name": "Beta", "offensive_score": 80.0, "MAD_gap_pct": 5.0},
                    {"Code": "A", "Name": "Alpha", "offensive_score": 50.0, "MAD_gap_pct": 10.0},
                ]
            )

    monkeypatch.setattr(cycle_mod, "MomentumScreener", FakeScreener)
    monkeypatch.setattr(cycle_mod, "_timestamp", lambda: "20260419T230000")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/run_offensive_screener_cycle.py",
            "--max-items",
            "25",
            "--top-n",
            "2",
            "--stock-sort-column",
            "offensive_score",
            "--output-dir",
            str(tmp_path),
        ],
    )

    cycle_mod.main()
    output = capsys.readouterr().out
    assert "Offensive Screener Cycle" in output
    assert "row_count=2" in output
    assert (tmp_path / "offensive_screening_20260419T230000.csv").exists()
    assert (tmp_path / "offensive_screening_latest.csv").exists()
    report_json = json.loads((tmp_path / "offensive_screening_report_latest.json").read_text(encoding="utf-8"))
    assert report_json["leaders"][0]["Code"] == "B"
