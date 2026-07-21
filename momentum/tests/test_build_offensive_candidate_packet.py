from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from tools.analysis import build_offensive_candidate_packet as packet_mod


def test_build_candidate_packet_payload_merges_report_metadata() -> None:
    filtered_df = pd.DataFrame(
        [
            {
                "Code": "007810",
                "Name": "Alpha",
                "offensive_score": 90.0,
                "offensive_rank": 2,
                "rank_delta_vs_legacy": 1,
                "momentum_1m": 20.0,
                "momentum_6m": 100.0,
                "momentum_12m": 300.0,
                "offensive_component_mom1": 12.0,
                "offensive_component_volume": 4.0,
                "offensive_component_breakout": 9.0,
            },
            {
                "Code": "003230",
                "Name": "Beta",
                "offensive_score": 60.0,
                "offensive_rank": 8,
                "rank_delta_vs_legacy": 0,
                "momentum_1m": 10.0,
                "momentum_6m": 20.0,
                "momentum_12m": 40.0,
                "offensive_component_mom1": 4.0,
                "offensive_component_volume": 5.0,
                "offensive_component_breakout": 8.5,
            },
        ]
    )
    report_payload = {
        "leaders": [{"Code": "007810", "reason_tags": ["recent_strength"]}],
        "biggest_promotions": [{"Code": "003230", "reason_tags": ["volume_confirmation"]}],
    }

    payload = packet_mod.build_candidate_packet_payload(filtered_df, report_payload, top_n=2)

    assert payload["candidate_count"] == 2
    assert payload["core_count"] == 1
    assert payload["leader_count"] == 1
    assert payload["promotion_count"] == 1
    assert payload["candidates"][0]["Code"] == "007810"
    assert payload["candidates"][0]["is_leader"] is True
    assert payload["candidates"][1]["is_promotion"] is True
    assert payload["candidates"][1]["priority_bucket"] == "watch"
    assert payload["candidates"][1]["reason_tags"] == ["volume_confirmation"]


def test_build_candidate_packet_payload_falls_back_to_row_reason_tags() -> None:
    filtered_df = pd.DataFrame(
        [
            {
                "Code": "008350",
                "Name": "Fallback",
                "offensive_score": 73.0,
                "offensive_rank": 18,
                "rank_delta_vs_legacy": -5,
                "momentum_1m": 66.22,
                "momentum_6m": 118.09,
                "momentum_12m": 78.26,
                "MAD_gap_pct": 55.42,
                "volume_ratio_5d_20d": 1.1432,
                "breakout_distance_pct": -20.13,
                "momentum_acceleration": -32.17,
                "offensive_component_mom1": 15.0,
                "offensive_component_volume": 5.72,
                "offensive_component_breakout": 8.0,
            }
        ]
    )

    payload = packet_mod.build_candidate_packet_payload(filtered_df, {"leaders": [], "biggest_promotions": []}, top_n=1)

    assert payload["candidates"][0]["reason_tags"] == [
        "recent_strength",
        "trend_expansion",
        "volume_confirmation",
    ]


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    filtered_path = tmp_path / "filtered.csv"
    report_path = tmp_path / "report.json"
    out_json = tmp_path / "packet.json"
    out_md = tmp_path / "packet.md"

    pd.DataFrame(
        [
            {
                "Code": "007810",
                "Name": "Alpha",
                "offensive_score": 90.0,
                "offensive_rank": 2,
                "rank_delta_vs_legacy": 1,
                "momentum_1m": 20.0,
                "momentum_6m": 100.0,
                "momentum_12m": 300.0,
                "offensive_component_mom1": 12.0,
                "offensive_component_volume": 4.0,
                "offensive_component_breakout": 9.0,
            }
        ]
    ).to_csv(filtered_path, index=False)
    report_path.write_text(
        json.dumps({"leaders": [{"Code": "007810", "reason_tags": ["recent_strength"]}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_candidate_packet.py",
            "--filtered-csv-path",
            str(filtered_path),
            "--report-json-path",
            str(report_path),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    packet_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Candidate Packet" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["leader_count"] == 1
    assert "reason_tags=recent_strength" in out_md.read_text(encoding="utf-8")
