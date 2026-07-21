from __future__ import annotations

import json
from pathlib import Path

from scripts.community_hypothesis_harvester import (
    build_report,
    classify_novelty,
    cluster_hypotheses,
    parse_hypothesis_item,
    run_harvester,
)


def test_parse_hypothesis_item_extracts_schema_fields() -> None:
    item = parse_hypothesis_item(
        {
            "source": "sample",
            "title": "KRW premium dislocation mean reversion",
            "text": "KRW-BTC vs Binance BTCUSDT premium spikes look like cross-market dislocation mean reversion and require KRW-USDT plus venue prices.",
        }
    )

    assert item.market_universe == "KRW-BTC single asset"
    assert item.signal_type == "cross-market dislocation"
    assert "cross-venue price series" in item.required_data
    assert item.cluster_id


def test_cluster_hypotheses_groups_similar_non_trend_items() -> None:
    items = [
        parse_hypothesis_item(
            {
                "source": "a",
                "title": "BTC oversold snapback",
                "text": "BTC oversold mean reversion with RSI and Bollinger Band on OHLCV.",
            }
        ),
        parse_hypothesis_item(
            {
                "source": "b",
                "title": "BTC overreaction normalizes",
                "text": "Bitcoin emotional dump mean reversion with RSI and price returning to average using OHLCV.",
            }
        ),
        parse_hypothesis_item(
            {
                "source": "c",
                "title": "Alt breakout basket",
                "text": "Top-20 alt basket breakout momentum on volume expansion.",
            }
        ),
    ]

    clusters = cluster_hypotheses(items)

    assert len(clusters) == 2
    assert clusters[0]["representative_problem_definition"]["signal_type"] == "non-trend mean reversion"
    assert clusters[0]["cluster_size"] == 2


def test_classify_novelty_distinguishes_failed_frozen_and_novel_axes() -> None:
    failed = classify_novelty("KRW-BTC single asset", "non-trend mean reversion", ["ohlcv"])
    frozen = classify_novelty("KRW-BTC single asset", "cross-market dislocation", ["cross-venue price series"])
    novel = classify_novelty("Unspecified crypto market", "event-driven reaction", ["event calendar / headlines"])

    assert failed[0] == "duplicate_failed"
    assert frozen[0] == "descriptive_only_overlap"
    assert novel[0] == "novel_candidate"


def test_run_harvester_generates_ranked_report(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/community_hypotheses_sample.jsonl")
    artifacts = run_harvester(fixture, tmp_path)

    report = artifacts["report"]
    assert artifacts["report_json_path"].exists()
    assert artifacts["report_md_path"].exists()
    assert report["boundary"]["what_it_does_not_do"].startswith("Does not generate trading signals")
    assert len(report["top_problem_definition_candidates"]) == 3
    top_statuses = [item["novelty_status"] for item in report["top_problem_definition_candidates"]]
    assert top_statuses[0] == "novel_candidate"
    assert "duplicate_failed" not in top_statuses[:2]

    loaded = json.loads(artifacts["report_json_path"].read_text(encoding="utf-8"))
    assert loaded["input_summary"]["hypothesis_count"] == 5
    assert "novelty_counts" in loaded["input_summary"]
