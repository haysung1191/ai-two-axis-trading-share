from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.analysis import build_offensive_review_shortlist as shortlist_mod


def test_build_review_shortlist_payload_prioritizes_promoted_core() -> None:
    payload = shortlist_mod.build_review_shortlist_payload(
        {
            "candidates": [
                {
                    "Code": "A",
                    "Name": "Alpha",
                    "offensive_score": 88.0,
                    "offensive_rank": 3,
                    "rank_delta_vs_legacy": 12,
                    "priority_bucket": "core",
                    "is_leader": True,
                    "is_promotion": True,
                    "offensive_component_mom1": 12.0,
                    "offensive_component_volume": 5.0,
                    "reason_tags": ["recent_strength"],
                },
                {
                    "Code": "B",
                    "Name": "Beta",
                    "offensive_score": 92.0,
                    "offensive_rank": 1,
                    "rank_delta_vs_legacy": 0,
                    "priority_bucket": "core",
                    "is_leader": True,
                    "is_promotion": False,
                    "offensive_component_mom1": 14.0,
                    "offensive_component_volume": 4.0,
                    "reason_tags": ["trend_expansion"],
                },
            ]
        },
        top_n=2,
    )

    assert payload["shortlist_count"] == 2
    assert payload["shortlist"][0]["Code"] == "A"
    assert payload["shortlist"][0]["review_label"] == "promoted_core"


def test_main_writes_outputs(monkeypatch, tmp_path: Path, capsys) -> None:
    packet_path = tmp_path / "packet.json"
    out_json = tmp_path / "shortlist.json"
    out_md = tmp_path / "shortlist.md"
    packet_path.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "Code": "A",
                        "Name": "Alpha",
                        "offensive_score": 88.0,
                        "offensive_rank": 3,
                        "rank_delta_vs_legacy": 12,
                        "priority_bucket": "core",
                        "is_leader": True,
                        "is_promotion": True,
                        "offensive_component_mom1": 12.0,
                        "offensive_component_volume": 5.0,
                        "reason_tags": ["recent_strength"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/build_offensive_review_shortlist.py",
            "--candidate-packet-json-path",
            str(packet_path),
            "--output-json-path",
            str(out_json),
            "--output-md-path",
            str(out_md),
        ],
    )

    shortlist_mod.main()
    output = capsys.readouterr().out
    assert "# Offensive Review Shortlist" in output
    assert json.loads(out_json.read_text(encoding="utf-8"))["shortlist_count"] == 1
    assert "review_label=promoted_core" in out_md.read_text(encoding="utf-8")
