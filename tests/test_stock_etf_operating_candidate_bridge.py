from __future__ import annotations

import json

import build_stock_etf_operating_candidate_bridge as bridge
import pandas as pd


def test_default_candidate_prefers_connectable_direct_development_parent(monkeypatch) -> None:
    direct_parent = "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim20_gap02_top2"
    fallback = "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim21_gap02_top2"

    monkeypatch.setattr(
        bridge,
        "top_direct_kis_variant",
        lambda: {
            "candidate_id": "kis_direct_exposure",
            "parent_candidate_id": direct_parent,
            "status": "DIRECT_CONVERSION_PASS",
        },
    )
    monkeypatch.setattr(
        bridge,
        "candidate_rows",
        lambda: [{"candidate_id": fallback}, {"candidate_id": direct_parent}],
    )

    assert bridge.default_candidate_id() == direct_parent


def test_load_json_returns_empty_dict_for_partial_or_non_object_file(tmp_path) -> None:
    partial = tmp_path / "partial.json"
    partial.write_text("{", encoding="utf-8")
    assert bridge.load_json(partial) == {}

    non_object = tmp_path / "list.json"
    non_object.write_text("[1, 2, 3]", encoding="utf-8")
    assert bridge.load_json(non_object) == {}


def test_truthy_flag_treats_false_string_as_false() -> None:
    assert bridge.truthy_flag(True)
    assert bridge.truthy_flag("True")
    assert not bridge.truthy_flag(False)
    assert not bridge.truthy_flag("False")
    assert not bridge.truthy_flag("")


def test_default_candidate_falls_back_when_direct_parent_not_connectable(monkeypatch) -> None:
    fallback = "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim21_gap02_top2"

    monkeypatch.setattr(
        bridge,
        "top_direct_kis_variant",
        lambda: {
            "candidate_id": "kis_direct_exposure",
            "parent_candidate_id": "not_connectable",
            "status": "DIRECT_CONVERSION_PASS",
        },
    )
    monkeypatch.setattr(bridge, "candidate_rows", lambda: [{"candidate_id": fallback}])

    assert bridge.default_candidate_id() == fallback


def test_add_tiny_live_affordability_marks_one_share_buyable_rows() -> None:
    target = pd.DataFrame(
        [
            {"Symbol": "A", "TargetNotionalKRW": 20000.0, "CurrentPrice": 12000.0},
            {"Symbol": "B", "TargetNotionalKRW": 20000.0, "CurrentPrice": 90000.0},
        ]
    )

    out = bridge.add_tiny_live_affordability(target)

    assert out.loc[0, "EstimatedTargetQuantityAtLastClose"] == 1
    assert bool(out.loc[0, "TinyLiveBuyableAtLastClose"])
    assert out.loc[1, "EstimatedTargetQuantityAtLastClose"] == 0
    assert not bool(out.loc[1, "TinyLiveBuyableAtLastClose"])


def test_tiny_live_execution_warnings_report_low_buyable_coverage() -> None:
    target = pd.DataFrame(
        [
            {"Symbol": "A", "TargetNotionalKRW": 20000.0, "CurrentPrice": 12000.0},
            {"Symbol": "B", "TargetNotionalKRW": 20000.0, "CurrentPrice": 90000.0},
        ]
    )
    evaluated = bridge.add_tiny_live_affordability(target)

    assert bridge.tiny_live_execution_warnings(evaluated) == ["KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE"]


def test_summarize_order_intent_frame_reports_submit_allowed_rows() -> None:
    order_intent = pd.DataFrame(
        [
            {"Symbol": "049630", "SubmitAllowed": True},
            {"Symbol": "069500", "SubmitAllowed": False},
            {"Symbol": "327260", "SubmitAllowed": "True"},
            {"Symbol": "402340", "SubmitAllowed": "False"},
            {"Symbol": "319400", "SubmitAllowed": "0"},
            {"Symbol": "058610", "SubmitAllowed": "yes"},
        ]
    )

    summary = bridge.summarize_order_intent_frame(order_intent)

    assert summary["rows"] == 6
    assert summary["submit_allowed_count"] == 3
    assert summary["submit_allowed_symbols"] == ["049630", "327260", "058610"]


def test_kis_universe_validation_state_uses_daily_close_presence_policy() -> None:
    state = bridge.kis_universe_validation_state()

    assert state["mode"] == "daily_close_presence"
    assert state["source"] == "operator_policy_daily_close_presence"
    assert state["verifier_status"] == "NOT_REQUIRED"
    assert state["operation_ready"]
    assert state["all_verified"]
    assert state["blockers"] == []


def test_build_tiny_live_executable_repair_selects_affordable_candidates() -> None:
    current_candidates = pd.DataFrame(
        [
            {"Market": "KR", "AssetType": "STOCK", "Symbol": "A", "Name": "A", "Sector": "IT", "CurrentPrice": 12000.0, "MomentumScore": 3.0, "LiquidityOK": 1, "CandidateState": "ENTRY"},
            {"Market": "KR", "AssetType": "STOCK", "Symbol": "B", "Name": "B", "Sector": "IT", "CurrentPrice": 18000.0, "MomentumScore": 2.0, "LiquidityOK": 1, "CandidateState": "ENTRY"},
            {"Market": "KR", "AssetType": "STOCK", "Symbol": "C", "Name": "C", "Sector": "IT", "CurrentPrice": 90000.0, "MomentumScore": 9.0, "LiquidityOK": 1, "CandidateState": "ENTRY"},
        ]
    )

    repair = bridge.build_tiny_live_executable_repair(
        current_candidates,
        candidate_id="repair",
        total_capital_krw=100000.0,
        fixed_exposure=0.64,
        desired_positions=2,
    )

    assert repair["status"] == "TINY_LIVE_REPAIR_RESEARCH_READY"
    assert repair["order_paths_allowed"] is False
    assert repair["candidate_symbols"] == ["A", "B"]
    assert repair["buyable_count"] == 2
    assert repair["quality"]["status"] == "TINY_LIVE_REPAIR_QUALITY_PASS"


def test_tiny_live_repair_quality_checks_catches_sector_overconcentration() -> None:
    rows = [
        {"symbol": "A", "sector": "IT", "momentum_score": 1.0, "target_notional_krw": 20000.0, "estimated_quantity": 1},
        {"symbol": "B", "sector": "IT", "momentum_score": 1.0, "target_notional_krw": 20000.0, "estimated_quantity": 1},
        {"symbol": "C", "sector": "IT", "momentum_score": 1.0, "target_notional_krw": 20000.0, "estimated_quantity": 1},
    ]

    quality = bridge.tiny_live_repair_quality_checks(rows)

    assert quality["status"] == "TINY_LIVE_REPAIR_QUALITY_ATTENTION"
    assert not quality["checks"]["max_sector_count_at_most_2"]


def test_tiny_live_repair_quality_allows_one_slot_minimum() -> None:
    rows = [
        {"symbol": "A", "sector": "IT", "momentum_score": 1.0, "target_notional_krw": 64000.0, "estimated_quantity": 4},
    ]

    quality = bridge.tiny_live_repair_quality_checks(rows, min_buyable_count=1)

    assert quality["status"] == "TINY_LIVE_REPAIR_QUALITY_PASS"
    assert quality["checks"]["buyable_count_at_least_minimum"]


def test_repair_candidates_to_target_frame_builds_buyable_execution_book() -> None:
    repair = {
        "candidates": [
            {
                "market": "KR",
                "asset_type": "STOCK",
                "symbol": "49630",
                "name": "Jaeyoung Solutec",
                "sector": "IT",
                "momentum_score": 2.5,
                "current_price": 13880.0,
                "target_weight": 0.64,
                "target_notional_krw": 64000.0,
            }
        ]
    }

    target = bridge.repair_candidates_to_target_frame(repair, candidate_id="repair", total_capital_krw=100000.0)

    assert target["Symbol"].tolist() == ["049630"]
    assert target["ExecutionTargetSource"].tolist() == ["tiny_live_affordability_repair"]
    assert target["EstimatedTargetQuantityAtLastClose"].tolist() == [4]
    assert bool(target.loc[0, "TinyLiveBuyableAtLastClose"])


def test_build_candidate_book_uses_repair_when_model_book_is_not_buyable(monkeypatch, tmp_path) -> None:
    candidate_id = "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim20_gap02_top2"
    limited_policy = tmp_path / "limited.json"
    broker_policy = tmp_path / "broker.json"
    limited_policy.write_text('{"stock_cap_krw": 100000}', encoding="utf-8")
    broker_policy.write_text(
        '{"broker_submit_allowed": true, "live_enabled": true, "real_orders_allowed": true}',
        encoding="utf-8",
    )
    monkeypatch.setattr(bridge, "LIMITED_LIVE_POLICY_PATH", limited_policy)
    monkeypatch.setattr(bridge, "BROKER_POLICY_PATH", broker_policy)
    monkeypatch.setattr(
        bridge,
        "select_candidate",
        lambda cid: {
            "candidate_id": cid,
            "status": "DIRECT_CONVERSION_PASS",
            "safe_experiment_scope": "tiny_live",
            "proposed_conversion": {"fixed_exposure_cap": 0.64},
        },
    )
    monkeypatch.setattr(bridge, "top_direct_kis_variant", lambda: {"parent_candidate_id": candidate_id, "status": "DIRECT_CONVERSION_PASS"})
    monkeypatch.setattr(bridge, "_baseline_variant_map", lambda: {bridge.STRONGEST_VARIANT: "variant"})
    monkeypatch.setattr(bridge, "_compose_micro_patch", lambda trim: (lambda frame: frame))
    monkeypatch.setattr(
        bridge,
        "_build_momentum_candidates_for_date",
        lambda *args, **kwargs: pd.DataFrame(
            [
                {
                    "Market": "KR",
                    "AssetType": "STOCK",
                    "Symbol": "069500",
                    "Name": "KODEX 200",
                    "Sector": "ETF",
                    "TargetWeight": 0.5,
                    "CurrentPrice": 90000.0,
                    "MomentumScore": 2.0,
                },
                {
                    "Market": "KR",
                    "AssetType": "STOCK",
                    "Symbol": "402340",
                    "Name": "SK Square",
                    "Sector": "IT",
                    "TargetWeight": 0.5,
                    "CurrentPrice": 80000.0,
                    "MomentumScore": 1.5,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        bridge,
        "run_pipeline",
        lambda: {
            "momentum_trade_candidates": pd.DataFrame(
                [
                    {
                        "Market": "KR",
                        "AssetType": "STOCK",
                        "Symbol": "049630",
                        "Name": "Jaeyoung Solutec",
                        "Sector": "IT",
                        "CurrentPrice": 13880.0,
                        "MomentumScore": 3.0,
                        "LiquidityOK": 1,
                        "CandidateState": "ENTRY",
                        "AsOfDate": "2026-05-18",
                    }
                ]
            ),
            "flow_regime_snapshot": pd.DataFrame([{"AsOfDate": "2026-05-18"}]),
        },
    )
    monkeypatch.setattr(
        bridge,
        "validate_tiny_live_repair_oos",
        lambda **kwargs: {
            "status": "TINY_LIVE_REPAIR_OOS_PASS",
            "checks": {"ok": True},
            "walkforward": {"pass_folds": 3, "folds": 4},
        },
    )

    target, order_intent, summary = bridge.build_candidate_book(candidate_id, 100000.0)

    assert summary["execution_target_source"] == "tiny_live_affordability_repair"
    assert summary["model_target_book"]["symbols"] == ["069500", "402340"]
    assert summary["target_book"]["symbols"] == ["049630"]
    assert summary["target_book"]["tiny_live_buyable_symbol_count"] == 1
    assert summary["execution_warnings"] == []
    assert target["Symbol"].tolist() == ["049630"]
    assert order_intent["Symbol"].tolist() == ["049630"]
    assert order_intent["SubmitAllowed"].map(bridge.truthy_flag).tolist() == [True]


def test_stock_submit_blockers_treats_false_strings_as_blocked(monkeypatch, tmp_path) -> None:
    limited_policy = tmp_path / "limited.json"
    broker_policy = tmp_path / "broker.json"
    limited_policy.write_text('{"stock_cap_krw": 100000}', encoding="utf-8")
    broker_policy.write_text(
        '{"broker_submit_allowed": "False", "live_enabled": "False", "real_orders_allowed": "False"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(bridge, "LIMITED_LIVE_POLICY_PATH", limited_policy)
    monkeypatch.setattr(bridge, "BROKER_POLICY_PATH", broker_policy)

    blockers = bridge.stock_submit_blockers(pd.DataFrame([{"CurrentPrice": 1000.0}]))

    assert "BROKER_POLICY_SUBMIT_BLOCKED" in blockers
    assert "BROKER_POLICY_LIVE_DISABLED" in blockers
    assert "BROKER_POLICY_REAL_ORDERS_BLOCKED" in blockers


def test_validate_tiny_live_repair_oos_passes_on_positive_historical_path(monkeypatch) -> None:
    dates = pd.date_range("2020-01-31", periods=40, freq="ME")
    columns = ["KR:STOCK:000001", "KR:STOCK:000002", "KR:STOCK:000003"]
    monthly_close = pd.DataFrame(
        {column: [100.0 + idx * 2.0 for idx in range(len(dates))] for column in columns},
        index=dates,
    )
    candidate_frame = pd.DataFrame(
        [
            {"Market": "KR", "AssetType": "STOCK", "Symbol": "000001", "Name": "A", "Sector": "IT", "CurrentPrice": 100.0, "MomentumScore": 3.0, "FlowScore": 1.0, "MedianDailyValue60D": 3_000_000_000.0, "TrendOK": 1},
            {"Market": "KR", "AssetType": "STOCK", "Symbol": "000002", "Name": "B", "Sector": "IT", "CurrentPrice": 100.0, "MomentumScore": 2.0, "FlowScore": 1.0, "MedianDailyValue60D": 3_000_000_000.0, "TrendOK": 1},
            {"Market": "KR", "AssetType": "STOCK", "Symbol": "000003", "Name": "C", "Sector": "Industrials", "CurrentPrice": 100.0, "MomentumScore": 1.0, "FlowScore": 1.0, "MedianDailyValue60D": 3_000_000_000.0, "TrendOK": 1},
        ]
    )

    monkeypatch.setattr(bridge, "_load_us_universe", lambda: (pd.DataFrame(), pd.DataFrame()))
    monkeypatch.setattr(bridge, "_load_kr_universe", lambda: pd.DataFrame({"AssetKey": columns}))
    monkeypatch.setattr(bridge, "_build_daily_caches", lambda universe: ({}, {}))
    monkeypatch.setattr(bridge, "_build_monthly_close_matrix", lambda universe, price_cache: monthly_close)
    monkeypatch.setattr(bridge, "_signal_dates", lambda close, start: list(close.index))
    monkeypatch.setattr(bridge, "_historical_metrics", lambda universe, price_cache, flow_cache, signal_date: candidate_frame)
    monkeypatch.setattr(
        bridge,
        "_historical_flow_snapshot",
        lambda metrics, close, signal_date, cfg: pd.DataFrame(
            [
                {"Market": "KR", "ScopeType": "COUNTRY", "Label": "Korea", "Rank": 1, "Score": 1.0},
                {"Market": "KR", "ScopeType": "SECTOR", "Label": "IT", "Rank": 1, "Score": 1.0},
                {"Market": "KR", "ScopeType": "SECTOR", "Label": "Industrials", "Rank": 2, "Score": 1.0},
            ]
        ),
    )

    validation = bridge.validate_tiny_live_repair_oos(total_capital_krw=100000.0, fixed_exposure=0.64)

    assert validation["status"] == "TINY_LIVE_REPAIR_OOS_PASS"
    assert validation["checks"]["holdout_cagr_positive"]
    assert validation["checks"]["cost_25bps_cagr_positive"]
    assert validation["walkforward"]["pass_folds"] >= 2


def test_write_outputs_replaces_artifacts_with_valid_files(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(bridge, "OPS_DIR", tmp_path)
    monkeypatch.setattr(bridge, "TARGET_BOOK_CSV", tmp_path / "target.csv")
    monkeypatch.setattr(bridge, "ORDER_INTENT_CSV", tmp_path / "order.csv")
    monkeypatch.setattr(bridge, "TINY_LIVE_REPAIR_CSV", tmp_path / "repair.csv")
    monkeypatch.setattr(bridge, "LATEST_JSON", tmp_path / "latest.json")

    target = pd.DataFrame([{"Symbol": "049630", "TargetWeight": 0.64}])
    order_intent = pd.DataFrame([{"Symbol": "049630", "ExecutionSide": "BUY"}])
    summary = {
        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
        "tiny_live_executable_repair": {
            "candidates": [{"symbol": "049630", "name": "재영솔루텍", "estimated_quantity": 4}],
        },
    }

    bridge.write_outputs(target, order_intent, summary)

    assert pd.read_csv(tmp_path / "target.csv", dtype={"Symbol": str})["Symbol"].tolist() == ["049630"]
    assert pd.read_csv(tmp_path / "order.csv")["ExecutionSide"].tolist() == ["BUY"]
    assert pd.read_csv(tmp_path / "repair.csv", dtype={"symbol": str})["symbol"].tolist() == ["049630"]
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["status"] == "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY"
    assert latest["tiny_live_executable_repair"]["candidates"][0]["name"] == "재영솔루텍"
    assert "\\uc7ac\\uc601\\uc194\\ub8e8\\ud14d" in (tmp_path / "latest.json").read_text(encoding="utf-8")
    assert latest["artifacts"]["tiny_live_repair_csv"] == str(tmp_path / "repair.csv")
    assert not list(tmp_path.glob(".*.tmp"))


def test_preserve_generated_at_for_same_bridge_keeps_stable_timestamp() -> None:
    existing = {
        "generated_at_utc": "2026-05-18T20:00:00+00:00",
        "candidate_id": "candidate-a",
        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
        "current_data": {"target_book_rows": 6},
    }
    regenerated = {
        "generated_at_utc": "2026-05-18T20:30:00+00:00",
        "candidate_id": "candidate-a",
        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
        "current_data": {"target_book_rows": 6},
    }

    result = bridge.preserve_generated_at_for_same_bridge(regenerated, existing)

    assert result["generated_at_utc"] == "2026-05-18T20:00:00+00:00"


def test_preserve_generated_at_for_changed_bridge_keeps_new_timestamp() -> None:
    existing = {
        "generated_at_utc": "2026-05-18T20:00:00+00:00",
        "candidate_id": "candidate-a",
        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
        "current_data": {"target_book_rows": 6},
    }
    regenerated = {
        "generated_at_utc": "2026-05-18T20:30:00+00:00",
        "candidate_id": "candidate-b",
        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
        "current_data": {"target_book_rows": 6},
    }

    result = bridge.preserve_generated_at_for_same_bridge(regenerated, existing)

    assert result["generated_at_utc"] == "2026-05-18T20:30:00+00:00"


def test_no_order_assertions_keep_all_order_paths_false() -> None:
    assert bridge.NO_ORDER_ASSERTIONS
    assert not any(bridge.NO_ORDER_ASSERTIONS.values())
