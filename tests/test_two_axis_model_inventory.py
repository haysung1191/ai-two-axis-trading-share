from __future__ import annotations

import build_two_axis_model_inventory as inventory


def test_atomic_write_text_replaces_target_with_complete_content(tmp_path) -> None:
    path = tmp_path / "inventory.json"
    path.write_text('{"old": true}', encoding="utf-8")

    inventory.atomic_write_text(path, '{"new": true}')

    assert path.read_text(encoding="utf-8") == '{"new": true}'
    assert not path.with_name(".inventory.json.tmp").exists()


def test_read_json_returns_empty_dict_for_partial_file(monkeypatch, tmp_path) -> None:
    partial = tmp_path / "partial.json"
    partial.write_text("{", encoding="utf-8")
    monkeypatch.setattr(inventory, "ROOT", tmp_path)

    assert inventory.read_json("partial.json") == {}


def test_inventory_records_bithumb_and_kis_verification_sources(monkeypatch) -> None:
    payloads = {
        "reports/operations/bithumb_verified_crypto_model_factory_latest.json": {"data": {}, "leaderboard": []},
        "reports/operations/bithumb_verified_crypto_model_factory_longhistory_latest.json": {"leaderboard": [], "research_watchlist": []},
        "reports/operations/bithumb_current_actionable_nonzero_signal_scout_latest.json": {
            "generated_at": "2026-05-18T09:00:00+09:00",
            "generated_at_utc": "2026-05-18T00:00:00+00:00",
            "evaluated_count": 9,
            "triggered_count": 1,
            "selection_policy": {
                "sort_keys": ["source_conversion.estimated_cagr", "aggregate.pass_fold_count"],
                "uses_oos_average_fold_cagr_as_primary_key": False,
            },
            "top_triggered_candidate": {
                "candidate_id": "oos1",
                "selection_rank": 1,
                "selection_key": {
                    "estimated_cagr": 1.2,
                    "pass_fold_count": 2,
                    "average_fold_cagr": 0.8,
                    "total_trade_count": 10,
                },
            },
            "triggered_candidates": [
                {
                    "candidate_id": "oos1",
                    "selection_rank": 1,
                    "selection_key": {
                        "estimated_cagr": 1.2,
                        "pass_fold_count": 2,
                        "average_fold_cagr": 0.8,
                        "total_trade_count": 10,
                    },
                }
            ],
            "top_near_miss": {
                "candidate_id": "near1",
                "market": "KRW-ORCA",
                "near_miss_rank": 1,
                "signal": {
                    "momentum": 0.01,
                    "momentum_threshold": 0.02,
                    "volume_ratio": 0.7,
                    "volume_ratio_floor": 1.0,
                },
                "signal_gap": {
                    "momentum_gap": -0.01,
                    "volume_gap": -0.3,
                    "nearest_trigger_gap": -0.3,
                    "blocking_conditions": ["momentum_below_threshold", "volume_ratio_below_floor"],
                },
            },
            "top_near_miss_candidates": [
                {
                    "candidate_id": "near1",
                    "market": "KRW-ORCA",
                    "near_miss_rank": 1,
                    "signal": {
                        "momentum": 0.01,
                        "momentum_threshold": 0.02,
                        "volume_ratio": 0.7,
                        "volume_ratio_floor": 1.0,
                    },
                    "signal_gap": {
                        "momentum_gap": -0.01,
                        "volume_gap": -0.3,
                        "nearest_trigger_gap": -0.3,
                        "blocking_conditions": ["momentum_below_threshold", "volume_ratio_below_floor"],
                    },
                },
                {
                    "candidate_id": "near2",
                    "market": "KRW-ORCA",
                    "near_miss_rank": 2,
                    "signal": {
                        "momentum": 0.0,
                        "momentum_threshold": 0.02,
                        "volume_ratio": 1.1,
                        "volume_ratio_floor": 1.0,
                    },
                    "signal_gap": {
                        "momentum_gap": -0.02,
                        "volume_gap": 0.1,
                        "nearest_trigger_gap": -0.02,
                        "blocking_conditions": ["momentum_below_threshold"],
                    },
                },
            ],
        },
        "reports/model_factory/bithumb_current_actionable_parameter_sweep_latest.json": {"sweeps": []},
        "reports/model_factory/bithumb_current_actionable_risk_conversion_latest.json": {"conversions": []},
        "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json": {
            "generated_at": "2026-05-18T22:16:03+09:00",
            "top_oos": {"candidate_id": "oos1", "market": "KRW-ORCA"},
            "evaluations": [
                {
                    "candidate_id": "oos1",
                    "status": "OOS_CANDIDATE_PASS",
                    "market": "KRW-ORCA",
                    "conversion": {
                        "estimated_cagr": 1.2,
                        "estimated_mdd": -0.2,
                        "source_cagr": 2.0,
                        "source_mdd": -0.3,
                        "source_profit_factor": 3.0,
                    },
                    "summary": {"average_fold_cagr": 0.8, "worst_fold_mdd": -0.1, "total_trade_count": 10},
                }
            ],
            "aggregate": {"pass_count": 6},
        },
        "reports/model_factory/bithumb_current_actionable_robustness_stress_latest.json": {
            "generated_at": "2026-05-18T22:16:04+09:00",
            "candidate_id": "oos1",
            "source_oos": {"top_candidate_id": "oos1"},
        },
        "reports/model_factory/two_axis_direct_model_development_latest.json": {
            "generated_at_utc": "2026-05-18T00:00:01+00:00",
            "crypto": {
                "candidate_count": 10,
                "oos_pass_count": 6,
                "validated_pass_count": 3,
                "archive_signal_triggered_count": 1,
                "top_live_signal_triggered_count": 0,
                "top_live_signal_summary": {"all_live_verified": True},
                "top_live_near_miss_candidate": {
                    "candidate_id": "direct_near1",
                    "market": "KRW-BTC",
                    "momentum_gap": -0.02,
                    "volume_gap": -0.4,
                    "blocking_conditions": ["volume_ratio_below_floor"],
                },
            },
            "kis": {
                "source_bridge": {"candidate_id": "kis_parent"},
                "top_variants": [{"parent_candidate_id": "kis_parent", "status": "DIRECT_CONVERSION_PASS"}],
                "universe_validation_mode": "daily_close_presence",
            },
        },
        "reports/operations/verified_candidate_registry/verified_candidate_registry_latest.json": {
            "summary": {},
            "candidates": [],
            "verified_data_guard": {},
        },
        "reports/model_factory/stock_risk_conversion_queue_latest.json": {"queue": []},
        "reports/model_factory/stock_conversion_gatekeeper_review_packet_latest.json": {},
        "reports/model_factory/model_factory_experiment_queue_latest.json": {"queue": [], "summary": {}},
        "ops/stock_etf_operating_candidate_bridge/stock_etf_operating_candidate_bridge_latest.json": {
            "generated_at_utc": "2026-05-18T00:00:00+00:00",
            "candidate_id": "kis_parent",
            "universe_validation_mode": "daily_close_presence",
            "universe_validation_verifier_status": "NOT_REQUIRED",
        },
    }

    monkeypatch.setattr(inventory, "read_json", lambda rel_path: payloads.get(rel_path, {}))
    monkeypatch.setattr(inventory, "maybe_read_json", lambda rel_path: payloads.get(rel_path))

    bithumb = inventory.summarize_bithumb()
    kis = inventory.summarize_kis()

    assert bithumb["verification_sources"]["oos_top_candidate_id"] == "oos1"
    assert bithumb["verification_sources"]["oos_top_market"] == "KRW-ORCA"
    assert bithumb["verification_sources"]["current_signal_generated_at_utc"] == "2026-05-18T00:00:00+00:00"
    assert bithumb["verification_sources"]["current_signal_evaluated_count"] == 9
    assert bithumb["verification_sources"]["current_signal_triggered_count"] == 1
    assert bithumb["verification_sources"]["current_signal_candidate_id"] == "oos1"
    assert bithumb["verification_sources"]["current_signal_matches_oos_top"]
    assert bithumb["verification_sources"]["current_signal_selection_policy"]["sort_keys"] == [
        "source_conversion.estimated_cagr",
        "aggregate.pass_fold_count",
    ]
    assert bithumb["verification_sources"]["current_signal_selection_summary"]["selection_rank"] == 1
    assert bithumb["verification_sources"]["oos_top_signal_selection_summary"]["estimated_cagr"] == 1.2
    assert bithumb["verification_sources"]["current_signal_top_near_miss"]["candidate_id"] == "near1"
    assert bithumb["verification_sources"]["current_signal_top_near_miss"]["volume_gap"] == -0.3
    assert [row["candidate_id"] for row in bithumb["verification_sources"]["current_signal_top_near_miss_candidates"]] == [
        "near1",
        "near2",
    ]
    assert bithumb["verification_sources"]["current_signal_top_near_miss_candidates"][1]["nearest_trigger_gap"] == -0.02
    assert bithumb["verification_sources"]["current_signal_oos_summary"]["average_fold_cagr"] == 0.8
    assert bithumb["verification_sources"]["oos_top_summary"]["total_trade_count"] == 10
    assert bithumb["verification_sources"]["robustness_source_oos"]["top_candidate_id"] == "oos1"
    assert bithumb["verification_sources"]["direct_generated_at_utc"] == "2026-05-18T00:00:01+00:00"
    assert bithumb["verification_sources"]["direct_crypto_candidate_count"] == 10
    assert bithumb["verification_sources"]["direct_crypto_oos_pass_count"] == 6
    assert bithumb["verification_sources"]["direct_crypto_validated_pass_count"] == 3
    assert bithumb["verification_sources"]["direct_crypto_archive_signal_triggered_count"] == 1
    assert bithumb["verification_sources"]["direct_crypto_top_live_signal_triggered_count"] == 0
    assert bithumb["verification_sources"]["direct_crypto_top_live_signal_all_verified"]
    assert bithumb["verification_sources"]["direct_crypto_top_live_near_miss_candidate"]["candidate_id"] == "direct_near1"
    assert bithumb["verification_sources"]["direct_crypto_top_live_near_miss_candidate"]["volume_gap"] == -0.4
    assert kis["verification_sources"]["direct_source_bridge"]["candidate_id"] == "kis_parent"
    assert kis["verification_sources"]["direct_top_parent_candidate_id"] == "kis_parent"
    assert kis["verification_sources"]["bridge_matches_direct_top_parent"]
    assert kis["verification_sources"]["bridge_universe_validation_mode"] == "daily_close_presence"
    assert kis["verification_sources"]["bridge_universe_validation_verifier_status"] == "NOT_REQUIRED"

    out_md = inventory.ROOT / "test_inventory.md"
    monkeypatch.setattr(inventory, "OUT_MD", out_md)
    inventory.write_markdown(
        {
            "generated_at_utc": "2026-05-18T00:00:00+00:00",
            "scope": "test",
            "axes": {"BITHUMB_KRW": bithumb, "KIS_COMBINED_KRW": kis},
            "safety": {
                "global_disable_all_trading_present": False,
                "tiny_live_firewall_decision": "ALLOW_LIMITED_LIVE",
                "tiny_live_broker_submit_attempt_status": "READY_FOR_EXPLICIT_SUBMIT_CALL",
                "real_orders": 0,
                "private_submit_used": False,
            },
            "completion_audit": {"status": "INCOMPLETE"},
        }
    )
    markdown = out_md.read_text(encoding="utf-8")

    assert "Direct crypto live near miss: `direct_near1` market `KRW-BTC`" in markdown
    assert "volume gap `-0.4000`" in markdown
    assert "PIT source queue" not in markdown


def test_oos_candidate_summary_accepts_current_oos_schema() -> None:
    row = {
        "candidate_id": "sweep1",
        "status": "OOS_CANDIDATE_PASS",
        "source_conversion": {
            "estimated_cagr": 1.5,
            "estimated_mdd": -0.2,
            "source_cagr": 2.0,
            "source_mdd": -0.3,
            "source_profit_factor": 3.2,
        },
        "aggregate": {
            "average_fold_cagr": 0.75,
            "worst_fold_mdd": -0.12,
            "total_trade_count": 17,
        },
    }

    summary = inventory.oos_candidate_summary(row)

    assert summary["estimated_cagr"] == 1.5
    assert summary["average_fold_cagr"] == 0.75
    assert summary["total_trade_count"] == 17


def test_build_report_completion_audit_tracks_verification_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        inventory,
        "summarize_bithumb",
        lambda: {
            "counts": {"latest_verified_leaderboard_models": 1},
            "leaders": {"current_actionable_top_signal": {"candidate_id": "oos1"}},
            "evidence_files": ["bithumb.json"],
            "verification_sources": {
                "oos_top_candidate_id": "oos1",
                "robustness_source_oos": {"top_candidate_id": "oos1"},
            },
        },
    )
    monkeypatch.setattr(
        inventory,
        "summarize_kis",
        lambda: {
            "counts": {"verified_registry_candidates_all_axes": 1},
            "leaders": {"stock_risk_conversion_top": [{"id": "kis1"}]},
            "evidence_files": ["kis.json"],
            "verification_sources": {
                "direct_source_bridge": {"candidate_id": "kis_parent"},
                "direct_top_parent_candidate_id": "kis_parent",
                "bridge_matches_direct_top_parent": True,
                "bridge_universe_validation_mode": "daily_close_presence",
                "bridge_universe_validation_verifier_status": "NOT_REQUIRED",
            },
        },
    )
    monkeypatch.setattr(inventory, "summarize_safety", lambda: {"real_orders": 0})

    report = inventory.build_report()

    assert report["completion_audit"]["bithumb_verification_sources_recorded"]
    assert report["completion_audit"]["kis_verification_sources_recorded"]
    assert report["completion_audit"]["status"] == "COMPLETE"
