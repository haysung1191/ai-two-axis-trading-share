from __future__ import annotations

import json

import build_two_axis_direct_model_development as direct


def test_backtest_momentum_generates_metrics_on_synthetic_breakout() -> None:
    candles = []
    price = 100.0
    for index in range(180):
        if index % 15 == 0:
            price *= 1.08
            volume = 5.0
        else:
            price *= 1.002
            volume = 1.0
        candles.append({"close": price, "volume": volume, "traded_value": price * volume})

    metrics = direct.backtest_momentum(
        candles,
        {
            "lookback_bars": 3,
            "hold_bars": 5,
            "volume_window": 10,
            "volume_ratio_floor": 1.2,
            "momentum_threshold": 0.02,
            "stop_loss": 0.08,
            "take_profit": 0.35,
            "round_trip_cost_rate": 0.002,
        },
    )

    assert metrics["trade_count"] > 0
    assert metrics["profit_factor"] > 1.0
    assert metrics["mdd"] <= 0.0


def test_holdout_validation_requires_holdout_and_high_cost_pass() -> None:
    candles = []
    price = 100.0
    for index in range(240):
        if index % 15 == 0:
            price *= 1.08
            volume = 5.0
        else:
            price *= 1.002
            volume = 1.0
        candles.append({"close": price, "volume": volume, "traded_value": price * volume})

    validation = direct.holdout_validation(
        candles,
        {
            "lookback_bars": 3,
            "hold_bars": 5,
            "volume_window": 10,
            "volume_ratio_floor": 1.2,
            "momentum_threshold": 0.02,
            "stop_loss": 0.08,
            "take_profit": 0.35,
            "round_trip_cost_rate": 0.002,
        },
    )

    assert "holdout" in validation
    assert "high_cost_holdout" in validation
    assert isinstance(validation["passed"], bool)


def test_current_momentum_signal_reports_trigger_gap() -> None:
    candles = []
    price = 100.0
    for index in range(40):
        price *= 1.001
        volume = 1.0
        if index == 39:
            price *= 1.08
            volume = 4.0
        candles.append({"close": price, "volume": volume, "traded_value": price * volume})

    signal = direct.current_momentum_signal(
        candles,
        {
            "lookback_bars": 5,
            "hold_bars": 5,
            "volume_window": 20,
            "volume_ratio_floor": 1.2,
            "momentum_threshold": 0.02,
            "stop_loss": 0.08,
            "take_profit": 0.35,
            "round_trip_cost_rate": 0.002,
        },
    )
    gap = direct.current_signal_gap(signal)

    assert signal["triggered"]
    assert gap["eligible_for_gap_ranking"]
    assert gap["nearest_trigger_gap"] >= 0
    assert gap["blocking_conditions"] == []


def test_attach_live_current_signals_keeps_live_signal_separate(monkeypatch) -> None:
    def fake_fetch(market: str):
        candles = []
        price = 100.0
        for index in range(40):
            price *= 1.001
            volume = 1.0
            if index == 39:
                price *= 1.08
                volume = 4.0
            candles.append({"close": price, "volume": volume, "traded_value": price * volume})
        return candles, {"source": "bithumb_public_api", "status": "LIVE_FETCH_OK", "market": market}

    monkeypatch.setattr(direct, "fetch_bithumb_live_candles", fake_fetch)
    candidates = [
        {
            "candidate_id": "eth_a",
            "market": "KRW-ETH",
            "parameters": {
                "lookback_bars": 5,
                "hold_bars": 5,
                "volume_window": 20,
                "volume_ratio_floor": 1.2,
                "momentum_threshold": 0.02,
                "stop_loss": 0.08,
                "take_profit": 0.35,
                "round_trip_cost_rate": 0.002,
            },
        }
    ]

    summary = direct.attach_live_current_signals(candidates)

    assert summary["all_live_verified"]
    assert summary["triggered_count"] == 1
    assert candidates[0]["live_current_signal"]["triggered"]
    assert candidates[0]["live_current_signal_data"]["status"] == "LIVE_FETCH_OK"


def test_attach_live_current_signals_reports_top_near_miss(monkeypatch) -> None:
    def fake_fetch(market: str):
        if market == "KRW-NEAR":
            closes = [100.0] * 21 + [103.0]
            volumes = [100.0] * 21 + [95.0]
        else:
            closes = [100.0] * 21 + [99.0]
            volumes = [100.0] * 21 + [50.0]
        candles = [
            {"close": close, "volume": volume, "traded_value": close * volume}
            for close, volume in zip(closes, volumes)
        ]
        return candles, {"source": "bithumb_public_api", "status": "LIVE_FETCH_OK", "market": market, "latest_timestamp": "2026-05-18T15:00:00"}

    monkeypatch.setattr(direct, "fetch_bithumb_live_candles", fake_fetch)
    candidates = [
        {
            "candidate_id": "far",
            "market": "KRW-FAR",
            "parameters": {
                "lookback_bars": 5,
                "hold_bars": 5,
                "volume_window": 20,
                "volume_ratio_floor": 1.0,
                "momentum_threshold": 0.02,
            },
            "metrics": {"cagr": 0.2},
            "holdout_validation": {"holdout": {"cagr": 0.1}},
        },
        {
            "candidate_id": "near",
            "market": "KRW-NEAR",
            "parameters": {
                "lookback_bars": 5,
                "hold_bars": 5,
                "volume_window": 20,
                "volume_ratio_floor": 1.0,
                "momentum_threshold": 0.02,
            },
            "metrics": {"cagr": 0.1},
            "holdout_validation": {"holdout": {"cagr": 0.1}},
        },
    ]

    summary = direct.attach_live_current_signals(candidates)

    assert summary["triggered_count"] == 0
    assert summary["top_live_near_miss_candidate"]["candidate_id"] == "near"
    assert summary["top_live_near_miss_candidate"]["market"] == "KRW-NEAR"
    assert summary["top_live_near_miss_candidate"]["live_near_miss_rank"] == 1
    assert summary["top_live_near_miss_candidate"]["blocking_conditions"] == ["volume_ratio_below_floor"]


def test_fetch_bithumb_live_candles_reports_latest_timestamp_from_first_api_row(monkeypatch) -> None:
    rows = [
        {"candle_date_time_utc": "2026-05-18T15:00:00", "trade_price": 110.0, "candle_acc_trade_volume": 2.0, "candle_acc_trade_price": 220.0},
        {"candle_date_time_utc": "2026-05-17T15:00:00", "trade_price": 100.0, "candle_acc_trade_volume": 1.0, "candle_acc_trade_price": 100.0},
    ]

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(rows).encode("utf-8")

    monkeypatch.setattr(direct.urllib.request, "urlopen", lambda request, timeout: FakeResponse())

    candles, meta = direct.fetch_bithumb_live_candles("KRW-BTC")

    assert meta["status"] == "LIVE_FETCH_OK"
    assert meta["latest_timestamp"] == "2026-05-18T15:00:00"
    assert [row["close"] for row in candles] == [100.0, 110.0]


def test_diverse_top_crypto_candidates_keeps_best_validated_candidate_per_market() -> None:
    def row(candidate_id: str, market: str, cagr: float) -> dict:
        return {
            "candidate_id": candidate_id,
            "market": market,
            "status": "DIRECT_VALIDATED_PASS",
            "metrics": {"cagr": cagr, "profit_factor": 2.0},
            "walkforward": {"average_fold_cagr": cagr},
            "holdout_validation": {"holdout": {"cagr": cagr}},
            "current_signal": {"triggered": False},
            "current_signal_gap": {"nearest_trigger_gap": -1.0},
        }

    candidates = [
        row("eth_a", "KRW-ETH", 3.0),
        row("eth_b", "KRW-ETH", 2.5),
        row("btc_a", "KRW-BTC", 1.0),
    ]

    selected = direct.diverse_top_crypto_candidates(candidates, limit=2)

    assert [item["candidate_id"] for item in selected] == ["eth_a", "btc_a"]


def test_walkforward_requires_two_full_pass_folds(monkeypatch) -> None:
    fold_metrics = iter(
        [
            {"total_return": 0.2, "cagr": 0.3, "mdd": -0.10, "trade_count": 10, "win_rate": 0.6, "profit_factor": 1.5, "average_holding_bars": 3.0},
            {"total_return": 0.1, "cagr": 0.1, "mdd": -0.10, "trade_count": 10, "win_rate": 0.6, "profit_factor": 1.2, "average_holding_bars": 3.0},
            {"total_return": -0.01, "cagr": -0.02, "mdd": -0.10, "trade_count": 10, "win_rate": 0.4, "profit_factor": 0.9, "average_holding_bars": 3.0},
        ]
    )

    monkeypatch.setattr(direct, "backtest_momentum", lambda candles, params: next(fold_metrics))

    result = direct.walkforward([{"close": 1.0, "volume": 1.0, "traded_value": 1.0}] * 300, {})

    assert result["positive_fold_count"] == 2
    assert result["pass_fold_count"] == 1
    assert not result["passed"]


def test_kis_development_builds_pass_variants_from_queue(monkeypatch) -> None:
    def fake_read_json(path, default):
        if str(path).endswith("stock_etf_operating_candidate_bridge_latest.json"):
            return {
                "generated_at_utc": "2026-05-18T00:00:00+00:00",
                "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
                "candidate_id": "kis_parent",
                "universe_validation_mode": "pit_membership_schema_caveated_not_operation_ready",
                "universe_validation_verifier_status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
                "universe_validation_operation_ready": False,
                "universe_validation_all_verified": False,
                "universe_validation_blockers": ["authoritative_pit_membership_history_missing_for_kis_combined"],
            }
        if str(path).endswith("kis_pit_membership_verifier_latest.json"):
            return {
                "status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
                "operation_ready": False,
                "all_verified": False,
                "blockers": ["authoritative_pit_membership_history_missing_for_kis_combined"],
                "next_evidence_acquisition_targets": [{"axis": "kis_us_stocks", "missing_membership_rows": 7387}],
            }
        if str(path).endswith("kis_axis_wide_membership_worklist_fill_progress_latest.json"):
            return {
                "status": "BLOCK_WORKLIST_FILL_PROGRESS",
                "source_acquisition_remaining_row_count": 16437,
                "source_acquisition_completion_ratio": 0.0,
            }
        if str(path).endswith("kis_pit_source_acquisition_queue_latest.json"):
            return {
                "generated_at_utc": "2026-05-18T22:00:02+00:00",
                "status": "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED",
                "queue_counts": {"total": 4, "axis_wide_operation_ready": 4},
            }
        if str(path).endswith("kis_pit_next_evidence_fill_card_latest.json"):
            return {
                "generated_at_utc": "2026-05-18T22:00:03+00:00",
                "status": "BLOCK_AXIS_WIDE_EVIDENCE_ACQUISITION_REQUIRED",
                "queue_id": "KIS_SRC_001",
                "axis": "kis_us_stocks",
                "pit_missing_membership_rows": 7387,
            }
        return {
            "queue": [
                {
                    "candidate_id": "stock_top",
                    "before": {"cagr": 0.70, "mdd": -0.30, "sharpe": 1.7},
                }
            ]
        }

    monkeypatch.setattr(direct, "read_json", fake_read_json)
    monkeypatch.setattr(
        direct,
        "read_csv_rows",
        lambda path: [
            {
                "Symbol": "069500",
                "Name": "KODEX200",
                "AssetType": "ETF",
                "TargetWeight": "0.10",
                "MomentumRank": "1",
                "MomentumScore": "1.2",
            }
        ],
    )

    report = direct.build_kis_development()

    assert report["status"] == "KIS_DIRECT_DEVELOPMENT_OK"
    assert report["source_bridge"] == {
        "generated_at_utc": "2026-05-18T00:00:00+00:00",
        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
        "candidate_id": "kis_parent",
        "universe_validation_mode": "pit_membership_schema_caveated_not_operation_ready",
        "universe_validation_verifier_status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
    }
    assert report["universe_validation_mode"] == "pit_membership_schema_caveated_not_operation_ready"
    assert report["universe_validation_verifier_status"] == "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE"
    assert not report["universe_validation_operation_ready"]
    assert not report["universe_validation_all_verified"]
    assert not report["universe_validation_pit_survivorship_safe"]
    assert report["pit_verifier_status"] == "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE"
    assert not report["pit_verifier_operation_ready"]
    assert not report["pit_verifier_all_verified"]
    assert report["pit_next_evidence_acquisition_targets"][0]["missing_membership_rows"] == 7387
    assert report["pit_axis_wide_worklist_fill_status"] == "BLOCK_WORKLIST_FILL_PROGRESS"
    assert report["pit_axis_wide_source_acquisition_remaining_row_count"] == 16437
    assert report["pit_source_acquisition_queue_generated_at_utc"] == "2026-05-18T22:00:02+00:00"
    assert report["pit_source_acquisition_queue_status"] == "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED"
    assert report["pit_source_acquisition_queue_counts"]["axis_wide_operation_ready"] == 4
    assert report["pit_next_evidence_fill_card_generated_at_utc"] == "2026-05-18T22:00:03+00:00"
    assert report["pit_next_evidence_fill_card_status"] == "BLOCK_AXIS_WIDE_EVIDENCE_ACQUISITION_REQUIRED"
    assert report["pit_next_evidence_fill_card_queue_id"] == "KIS_SRC_001"
    assert report["pit_next_evidence_fill_card_axis"] == "kis_us_stocks"
    assert report["pit_next_evidence_fill_card_missing_rows"] == 7387
    assert not report["counts_as_live_evidence"]
    assert report["conversion_variant_count"] == 5
    assert report["pass_count"] > 0
    assert report["current_target_symbols"][0]["symbol"] == "069500"


def test_render_md_includes_kis_universe_validation_state() -> None:
    markdown = direct.render_md(
        {
            "status": "TWO_AXIS_DIRECT_DEVELOPMENT_OK",
            "crypto": {
                "evaluated_count": 0,
                "candidate_count": 0,
                "oos_pass_count": 0,
                "validated_pass_count": 0,
                "validated_market_count": 0,
                "top_candidates": [],
                "archive_signal_triggered_count": 0,
                "top_live_signal_triggered_count": 0,
                "top_live_signal_summary": {"all_live_verified": False},
                "top_live_near_miss_candidate": {
                    "candidate_id": "near",
                    "market": "KRW-NEAR",
                    "nearest_trigger_gap": -0.05,
                    "blocking_conditions": ["volume_ratio_below_floor"],
                },
            },
            "kis": {
                "conversion_variant_count": 1,
                "pass_count": 1,
                "universe_validation_mode": "daily_close_presence",
                "universe_validation_verifier_status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
                "universe_validation_operation_ready": False,
                "universe_validation_all_verified": False,
                "universe_validation_pit_survivorship_safe": False,
                "counts_as_live_evidence": False,
                "pit_verifier_status": "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE",
                "pit_axis_wide_source_acquisition_remaining_row_count": 16437,
                "pit_axis_wide_source_acquisition_completion_ratio": 0.0,
                "pit_source_acquisition_queue_generated_at_utc": "2026-05-18T22:00:02+00:00",
                "pit_source_acquisition_queue_status": "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED",
                "pit_next_evidence_fill_card_status": "BLOCK_AXIS_WIDE_EVIDENCE_ACQUISITION_REQUIRED",
                "pit_next_evidence_fill_card_queue_id": "KIS_SRC_001",
                "pit_next_evidence_fill_card_axis": "kis_us_stocks",
                "pit_next_evidence_fill_card_missing_rows": 7387,
                "source_bridge": {
                    "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
                    "generated_at_utc": "2026-05-18T00:00:00+00:00",
                    "candidate_id": "kis_parent",
                },
                "top_variants": [],
            },
        }
    )

    assert "KIS universe validation: `daily_close_presence`; PIT survivorship safe: `False`; live evidence: `False`." in markdown
    assert "KIS PIT verifier: `PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE`; operation ready: `False`; all verified: `False`." in markdown
    assert "KIS PIT worklist: verifier `PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE`; source remaining `16437`; completion `0.0`." in markdown
    assert "KIS PIT source queue: `BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED` generated `2026-05-18T22:00:02+00:00`; next fill card `BLOCK_AXIS_WIDE_EVIDENCE_ACQUISITION_REQUIRED` queue `KIS_SRC_001` axis `kis_us_stocks` missing `7387`." in markdown
    assert "KIS source bridge: `OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY`; generated: `2026-05-18T00:00:00+00:00`; candidate: `kis_parent`." in markdown
    assert "Crypto top live near miss: `near` `KRW-NEAR` gap `-0.05` blockers `volume_ratio_below_floor`." in markdown


def test_write_json_atomic_replaces_with_valid_json(tmp_path) -> None:
    target = tmp_path / "direct_latest.json"
    target.write_text(json.dumps({"status": "OLD"}), encoding="utf-8")

    direct.write_json_atomic(target, {"status": "NEW", "count": 1})

    assert json.loads(target.read_text(encoding="utf-8")) == {"status": "NEW", "count": 1}
    assert not (tmp_path / ".direct_latest.json.tmp").exists()


def test_read_json_returns_default_for_partial_or_missing_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"
    assert direct.read_json(missing, {"fallback": True}) == {"fallback": True}

    partial = tmp_path / "partial.json"
    partial.write_text("{", encoding="utf-8")
    assert direct.read_json(partial, {"fallback": True}) == {"fallback": True}
