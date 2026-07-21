from __future__ import annotations

import build_simple_pipeline_dashboard as dashboard


def test_load_json_returns_empty_dict_for_empty_or_partial_status_file(tmp_path) -> None:
    path = tmp_path / "status.json"

    path.write_text("", encoding="utf-8")
    assert dashboard.load_json(path) == {}

    path.write_text("{", encoding="utf-8")
    assert dashboard.load_json(path) == {}

    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert dashboard.load_json(path) == {}


def test_atomic_write_text_replaces_target_with_complete_content(tmp_path) -> None:
    path = tmp_path / "dashboard.json"
    path.write_text('{"old": true}', encoding="utf-8")

    dashboard.atomic_write_text(path, '{"new": true}')

    assert path.read_text(encoding="utf-8") == '{"new": true}'
    assert not path.with_name("dashboard.json.tmp").exists()


def test_summarize_no_order_assertions_reports_true_flags() -> None:
    result = dashboard.summarize_no_order_assertions(
        {
            "no_order_assertions": {
                "live_allowed_by_this_report": "False",
                "real_orders_allowed_by_this_report": True,
            }
        }
    )

    assert result["present"]
    assert not result["all_order_paths_false"]
    assert result["true_flags"] == ["real_orders_allowed_by_this_report"]


def test_truthy_flag_treats_false_string_as_false() -> None:
    assert dashboard.truthy_flag(True)
    assert dashboard.truthy_flag("True")
    assert not dashboard.truthy_flag(False)
    assert not dashboard.truthy_flag("False")
    assert not dashboard.truthy_flag("")


def test_artifact_not_older_than_compares_iso_timestamps() -> None:
    assert dashboard.artifact_not_older_than("2026-05-18T22:16:03+09:00", "2026-05-18T22:16:04+09:00")
    assert not dashboard.artifact_not_older_than("2026-05-18T22:16:04+09:00", "2026-05-18T22:16:03+09:00")
    assert dashboard.artifact_not_older_than("2026-05-18T22:16:03+09:00", None) is None


def test_summarize_order_intent_counts_submit_allowed_rows() -> None:
    result = dashboard.summarize_order_intent(
        [
            {"Symbol": "049630", "SubmitAllowed": "True"},
            {"Symbol": "069500", "SubmitAllowed": "False"},
            {"Symbol": "327260", "SubmitAllowed": "1"},
        ]
    )

    assert result["row_count"] == 3
    assert result["submit_allowed_count"] == 2
    assert result["submit_allowed_symbols"] == ["049630", "327260"]


def test_order_intent_summary_prefers_bridge_current_data() -> None:
    result = dashboard.order_intent_summary_from_bridge(
        {
            "current_data": {
                "order_intent_rows": 2,
                "order_intent_submit_allowed_count": 1,
                "order_intent_submit_allowed_symbols": ["049630"],
            }
        },
        [{"Symbol": "069500", "SubmitAllowed": "True"}],
    )

    assert result == {
        "row_count": 2,
        "submit_allowed_count": 1,
        "submit_allowed_symbols": ["049630"],
        "source": "bridge_current_data",
    }


def test_summarize_top_candidates_keeps_review_metrics_only() -> None:
    result = dashboard.summarize_top_candidates(
        [
            {
                "candidate_id": "c1",
                "parent_candidate_id": "parent1",
                "market": "KRW-BTC",
                "status": "PASS",
                "fixed_exposure_cap": 0.64,
                "metrics": {"cagr": 0.2, "mdd": -0.1, "profit_factor": 2.0, "trade_count": 9},
                "holdout_validation": {"holdout": {"cagr": 0.1}},
                "parameters": {"large": "payload"},
                "walkforward": {"folds": [{"large": "payload"}]},
                "current_signal": {"triggered": True},
                "current_signal_gap": {"nearest_trigger_gap": 0.12},
                "live_current_signal": {"triggered": False},
                "live_current_signal_gap": {"nearest_trigger_gap": -0.34},
                "live_current_signal_data": {"status": "LIVE_FETCH_OK", "latest_timestamp": "2026-05-18T15:00:00"},
                "order_paths_allowed": False,
            }
        ]
    )

    assert result == [
        {
            "candidate_id": "c1",
            "parent_candidate_id": "parent1",
            "market": "KRW-BTC",
            "symbol": None,
            "status": "PASS",
            "fixed_exposure_cap": 0.64,
            "cagr": 0.2,
            "mdd": -0.1,
            "sharpe": None,
            "profit_factor": 2.0,
            "trade_count": 9,
            "holdout_cagr": 0.1,
            "archive_signal_triggered": True,
            "archive_signal_nearest_gap": 0.12,
            "live_signal_triggered": False,
            "live_signal_nearest_gap": -0.34,
            "live_signal_data_status": "LIVE_FETCH_OK",
            "live_signal_latest_timestamp": "2026-05-18T15:00:00",
            "order_paths_allowed": False,
            "counts_as_live_evidence": False,
        }
    ]


def test_model_factory_runtime_freshness_detects_stale_process(monkeypatch) -> None:
    def fake_mtime(path):
        return "2026-05-18T12:05:00+00:00" if str(path).endswith("two_axis_model_factory_loop_latest.json") else "2026-05-18T12:00:00+00:00"

    monkeypatch.setattr(dashboard, "file_mtime_utc", fake_mtime)
    monkeypatch.setattr(dashboard, "process_creation_time_utc", lambda pid: "2026-05-18T11:59:00+00:00")

    result = dashboard.build_model_factory_runtime_freshness(
        {"model_factory": {"pid": "10796", "running": True, "source": "pid_file"}}
    )

    assert result["pid"] == "10796"
    assert result["process_predates_source"]
    assert result["latest_json_not_older_than_source"]


def test_model_factory_cadence_reports_overdue_when_idle_past_due() -> None:
    result = dashboard.build_model_factory_cadence(
        {
            "status": "TWO_AXIS_MODEL_FACTORY_OK",
            "generated_at_utc": "2026-05-18T13:14:00+00:00",
            "cycle_started_at_utc": "2026-05-18T13:13:00+00:00",
            "next_cycle_due_at_utc": "2026-05-18T13:13:15+00:00",
        },
        now_utc="2026-05-18T13:14:20+00:00",
    )

    assert result["overdue"]
    assert result["seconds_overdue"] == 65
    assert result["elapsed_seconds"] == 60


def test_model_factory_cadence_maps_running_step_counts() -> None:
    result = dashboard.build_model_factory_cadence(
        {
            "status": "TWO_AXIS_MODEL_FACTORY_RUNNING",
            "generated_at_utc": "2026-05-18T13:13:00+00:00",
            "cycle_started_at_utc": "2026-05-18T13:13:00+00:00",
            "current_step": "two axis direct model development",
            "step_index": 1,
            "step_count": 8,
        },
        now_utc="2026-05-18T13:14:20+00:00",
    )

    assert result["step_index"] == 1
    assert result["planned_step_count"] == 8
    assert result["elapsed_seconds"] == 80


def test_model_factory_running_contract_detects_current_running_schema() -> None:
    result = dashboard.build_model_factory_running_contract(
        {
            "schema_version": dashboard.EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
            "status": "TWO_AXIS_MODEL_FACTORY_RUNNING",
            "current_step": "bithumb parameter sweep",
            "step_manifest": [{"label": label} for label in dashboard.EXPECTED_MODEL_FACTORY_STEP_LABELS],
            "model_only_safety": {
                "command_manifest_has_no_order_flags": True,
                "order_submission_allowed_by_this_loop": False,
                "broker_submit_allowed_by_this_loop": False,
                "real_orders_allowed_by_this_loop": False,
            },
        }
    )

    assert result["contract_current"]
    assert result["model_only_safety_present"]
    assert result["model_only_safety_no_order_flags"]
    assert result["model_only_safety_no_submit"]


def test_model_factory_running_contract_flags_old_running_schema() -> None:
    result = dashboard.build_model_factory_running_contract({"status": "TWO_AXIS_MODEL_FACTORY_OK"})

    assert not result["contract_current"]
    assert not result["schema_version_current"]
    assert not result["step_manifest_matches_expected"]
    assert not result["model_only_safety_present"]



def test_model_factory_artifact_schema_flags_missing_direct_kis_fields() -> None:
    result = dashboard.build_model_factory_artifact_schema(
        {"artifact_summary": {"direct_development": {"status": "TWO_AXIS_DIRECT_DEVELOPMENT_OK"}}},
        {"kis": {"source_bridge": {"candidate_id": "kis_parent"}, "universe_validation_mode": "daily_close_presence", "universe_validation_verifier_status": "NOT_REQUIRED", "universe_validation_operation_ready": True, "universe_validation_all_verified": True, "universe_validation_operational": True, "counts_as_live_evidence": True}},
        {"generated_at": "2026-05-18T22:16:03+09:00", "top_oos": {"candidate_id": "oos1", "market": "KRW-ORCA"}},
        {"generated_at": "2026-05-18T22:16:04+09:00", "source_oos": {"top_candidate_id": "oos1"}},
        {"axes": {"BITHUMB_KRW": {"verification_sources": {"oos_top_candidate_id": "oos1", "current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00", "current_signal_evaluated_count": 9}}, "KIS_COMBINED_KRW": {"verification_sources": {"bridge_universe_validation_mode": "daily_close_presence", "bridge_universe_validation_verifier_status": "NOT_REQUIRED", "direct_source_bridge": {"candidate_id": "kis_parent"}}}}},
    )

    assert not result["direct_kis_validation_fields_present"]
    assert "kis_universe_validation_operational" in result["missing_direct_development_fields"]


def test_model_factory_artifact_schema_accepts_current_direct_and_bithumb_fields() -> None:
    model_factory = {
        "schema_version": dashboard.EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
        "step_manifest": [{"label": label} for label in dashboard.EXPECTED_MODEL_FACTORY_STEP_LABELS],
        "model_only_safety": {"command_manifest_has_no_order_flags": True, "order_submission_allowed_by_this_loop": False, "broker_submit_allowed_by_this_loop": False, "real_orders_allowed_by_this_loop": False},
        "artifact_summary": {
            "direct_development": {"kis_source_bridge": {"candidate_id": "kis_parent"}, "kis_universe_validation_mode": "daily_close_presence", "kis_universe_validation_verifier_status": "NOT_REQUIRED", "kis_universe_validation_operation_ready": True, "kis_universe_validation_all_verified": True, "kis_universe_validation_operational": True, "kis_counts_as_live_evidence": True, "crypto_archive_signal_triggered_count": 1, "crypto_top_live_signal_triggered_count": 0, "crypto_top_live_signal_all_verified": True, "crypto_top_live_near_miss_candidate": {"candidate_id": "near"}},
            "bithumb": {"oos_generated_at": "2026-05-18T22:16:03+09:00", "oos_top_candidate_id": "oos1", "oos_top_market": "KRW-ORCA", "robustness_generated_at": "2026-05-18T22:16:04+09:00", "robustness_source_oos": {"top_candidate_id": "oos1"}, "inventory_current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00", "inventory_current_signal_evaluated_count": 9, "inventory_current_signal_triggered_count": 0, "inventory_current_signal_candidate_id": "signal2", "inventory_current_signal_matches_oos_top": False, "inventory_oos_top_candidate_id": "oos1", "inventory_current_signal_selection_policy": {"sort_keys": ["source_conversion.estimated_cagr"]}, "inventory_current_signal_selection_summary": {"selection_rank": 1}, "inventory_oos_top_signal_selection_summary": {"selection_rank": 2}, "inventory_current_signal_top_near_miss": {"candidate_id": "near1"}, "inventory_current_signal_top_near_miss_candidates": [{"candidate_id": "near1"}], "inventory_current_signal_oos_summary": {"average_fold_cagr": 0.8}, "inventory_oos_top_summary": {"average_fold_cagr": 0.9}},
            "kis": {"bridge_universe_validation_mode": "daily_close_presence", "bridge_universe_validation_verifier_status": "NOT_REQUIRED", "direct_source_bridge": {"candidate_id": "kis_parent"}},
        },
    }
    direct = {"crypto": {"archive_signal_triggered_count": 1, "top_live_signal_triggered_count": 0, "top_live_signal_summary": {"all_live_verified": True}, "top_live_near_miss_candidate": {"candidate_id": "near"}}, "kis": {"source_bridge": {"candidate_id": "kis_parent"}, "universe_validation_mode": "daily_close_presence", "universe_validation_verifier_status": "NOT_REQUIRED", "universe_validation_operation_ready": True, "universe_validation_all_verified": True, "universe_validation_operational": True, "counts_as_live_evidence": True}}
    inventory_payload = {"axes": {"BITHUMB_KRW": {"verification_sources": {"oos_top_candidate_id": "oos1", "current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00", "current_signal_evaluated_count": 9, "current_signal_triggered_count": 0, "current_signal_candidate_id": "signal2", "current_signal_matches_oos_top": False, "current_signal_selection_policy": {"sort_keys": ["source_conversion.estimated_cagr"]}, "current_signal_selection_summary": {"selection_rank": 1}, "oos_top_signal_selection_summary": {"selection_rank": 2}, "current_signal_top_near_miss": {"candidate_id": "near1"}, "current_signal_top_near_miss_candidates": [{"candidate_id": "near1"}], "current_signal_oos_summary": {"average_fold_cagr": 0.8}, "oos_top_summary": {"average_fold_cagr": 0.9}}}, "KIS_COMBINED_KRW": {"verification_sources": {"bridge_universe_validation_mode": "daily_close_presence", "bridge_universe_validation_verifier_status": "NOT_REQUIRED", "direct_source_bridge": {"candidate_id": "kis_parent"}}}}}

    result = dashboard.build_model_factory_artifact_schema(model_factory, direct, {"generated_at": "2026-05-18T22:16:03+09:00", "top_oos": {"candidate_id": "oos1", "market": "KRW-ORCA"}}, {"generated_at": "2026-05-18T22:16:04+09:00", "source_oos": {"top_candidate_id": "oos1"}}, inventory_payload)

    assert result["direct_kis_validation_fields_present"]
    assert result["kis_inventory_fields_present"]
    assert result["canonical_child_artifacts_complete"]

def test_render_html_includes_model_only_guardrails() -> None:
    summary = {
        "generated_at_utc": "2026-05-18T00:00:00+00:00",
        "overall_completion": 1.0,
        "completion": {"model_development_loop": 1.0, "model_verification_loop": 1.0, "promotion_to_live_loop": 1.0, "autotrade_position_loop": 1.0, "performance_dashboard": 1.0},
        "loops": {name: {"status": "OK", "pid": "1", "detail": "ok"} for name in ["direct_development", "model_factory", "bithumb", "kis_buy", "kis_plan", "kis_rebalance", "dashboard"]},
        "trading": {"bithumb": {"status": "OK", "exposure_krw": 0, "cap_krw": 100000, "markets": [], "open_positions": [], "position_status": "NONE", "last_reason": "", "realized_pnl_krw": 0, "realized_return_pct": 0}, "kis": {"order_submit_status": "OK", "tiny_live_buyable_symbol_count": 0, "symbols": [], "ledger_submitted_count": 0, "ledger_submitted_notional_krw": 0, "estimated_buyable_notional_krw": 0, "execution_warnings": [], "gross_target_weight": 0, "cash_weight": 1, "rebalance_status": "OK", "submitted_count": 0}},
        "account_engine": {"bithumb": {}, "kis": {}},
        "model_only_guardrails": {"all_known_order_paths_false": True, "direct_development": {"all_order_paths_false": True}, "bithumb_oos": {"all_order_paths_false": True}, "bithumb_robustness": {"all_order_paths_false": True}, "kis_bridge": {"all_order_paths_false": True}, "kis_true_order_path_flags": [], "kis_order_intent_submit_allowed_count": 6},
        "model_factory_runtime": {"pid": "1", "process_predates_source": True, "process_created_at_utc": "2026-05-18T00:00:00+00:00", "source_mtime_utc": "2026-05-18T00:01:00+00:00", "latest_json_not_older_than_source": True, "latest_json_mtime_utc": "2026-05-18T00:02:00+00:00"},
        "model_factory_cadence": {"next_cycle_due_at_utc": "2026-05-18T00:30:00+00:00", "overdue": True, "seconds_overdue": 60, "elapsed_seconds": 120},
        "model_factory_running_contract": {"contract_current": False},
        "model_factory_artifact_schema": {"schema_version_current": False, "canonical_child_artifacts_complete": True, "canonical_direct_development_fields_present": True, "canonical_missing_direct_development_fields": [], "canonical_bithumb_sources_present": True, "canonical_kis_inventory_sources_present": True},
        "performance": {"direct_development": {"crypto_candidates": 0, "crypto_oos_pass": 0, "crypto_validated_pass": 0, "crypto_validated_market_count": 0, "kis_variants": 0, "kis_pass": 0, "kis_universe_validation_mode": "daily_close_presence", "kis_universe_validation_verifier_status": "NOT_REQUIRED", "kis_universe_validation_operation_ready": True, "kis_universe_validation_all_verified": True, "kis_universe_validation_operational": True, "kis_counts_as_live_evidence": True, "top_crypto": [], "top_kis": []}, "kis_backtest": {"before_cagr": 0, "before_mdd": 0, "before_sharpe": 0, "estimated_cagr": 0, "estimated_mdd": 0}, "kis_verification": {"bridge_status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY", "universe_validation_mode": "daily_close_presence", "universe_validation_operational": True, "universe_validation_verifier_status": "NOT_REQUIRED", "universe_validation_operation_ready": True, "universe_validation_all_verified": True, "universe_validation_blockers": [], "repair_status": "TINY_LIVE_REPAIR_RESEARCH_READY", "repair_order_paths_allowed": False, "repair_counts_as_live_evidence": False, "repair_oos_status": "TINY_LIVE_REPAIR_OOS_PASS", "repair_oos_order_paths_allowed": False, "repair_oos_counts_as_live_evidence": False, "repair_oos_pass_folds": 3, "repair_oos_folds": 4, "order_intent_row_count": 6, "order_intent_submit_allowed_count": 6, "order_intent_submit_allowed_symbols": ["049630", "327260"], "order_intent_summary_source": "bridge_current_data", "direct_bridge_universe_validation_match": True, "direct_not_older_than_bridge": True, "direct_source_bridge_matches_current": True, "direct_top_parent_candidate_id": "parent1", "bridge_matches_direct_top_parent": True}, "bithumb_verification": {"oos_status": "OOS_WALKFORWARD_PASS", "oos_generated_at": "2026-05-18T22:16:03+09:00", "oos_pass_count": 6, "oos_evaluated_count": 9, "oos_top_candidate_id": "oos1", "oos_top_market": "KRW-ORCA", "oos_order_paths_allowed": False, "robustness_status": "ROBUSTNESS_STRESS_PASS", "robustness_candidate_id": "oos1", "robustness_matches_oos_top": True, "robustness_source_oos_matches_current": True, "robustness_not_older_than_oos": True, "robustness_pass_count": 7, "robustness_case_count": 7, "robustness_cost_pass_count": 1, "robustness_order_paths_allowed": False}},
    }

    html = dashboard.render_html(summary)

    assert "Model-Only Guardrails" in html
    assert "All known order paths false: True" in html
    assert "KIS universe validation: daily_close_presence" in html
    assert "PIT" not in html

def test_build_summary_prefers_standalone_kis_bridge_for_guardrails(monkeypatch, tmp_path) -> None:
    def fake_load_json(path):
        if path == dashboard.KIS_BRIDGE_STATUS:
            return {"generated_at_utc": "2026-05-18T00:00:00+00:00", "candidate_id": "kis_parent", "universe_validation_mode": "daily_close_presence", "universe_validation_verifier_status": "NOT_REQUIRED", "universe_validation_operation_ready": True, "universe_validation_all_verified": True, "universe_validation_blockers": [], "no_order_assertions": {"live_allowed_by_this_report": False, "real_orders_allowed_by_this_report": False}, "target_book": {"symbols": ["049630"], "tiny_live_buyable_symbol_count": 1}, "current_data": {"order_intent_rows": 3, "order_intent_submit_allowed_count": 2, "order_intent_submit_allowed_symbols": ["049630", "327260"]}}
        if path == dashboard.KIS_STATUS:
            return {"submit_enabled": True, "operating_candidate_bridge": {"no_order_assertions": {"live_allowed_by_this_report": True}}}
        if path == dashboard.DIRECT_DEVELOPMENT_STATUS:
            return {"status": "TWO_AXIS_DIRECT_DEVELOPMENT_OK", "generated_at_utc": "2026-05-18T00:00:01+00:00", "crypto": {}, "kis": {"source_bridge": {"generated_at_utc": "2026-05-18T00:00:00+00:00", "candidate_id": "kis_parent", "universe_validation_mode": "daily_close_presence"}, "universe_validation_mode": "daily_close_presence", "universe_validation_verifier_status": "NOT_REQUIRED", "universe_validation_operation_ready": True, "universe_validation_all_verified": True, "universe_validation_operational": True, "counts_as_live_evidence": True, "top_variants": [{"parent_candidate_id": "kis_parent", "status": "DIRECT_CONVERSION_PASS"}]}, "no_order_assertions": {"live_allowed_by_this_report": False, "real_orders_allowed_by_this_report": False}}
        if path in {dashboard.BITHUMB_OOS_STATUS, dashboard.BITHUMB_ROBUSTNESS_STATUS}:
            return {"no_order_assertions": {"live_allowed_by_this_report": False, "real_orders_allowed_by_this_report": False}}
        if path == dashboard.MODEL_INVENTORY_STATUS:
            return {"axes": {"BITHUMB_KRW": {"verification_sources": {}}, "KIS_COMBINED_KRW": {"verification_sources": {"bridge_universe_validation_mode": "daily_close_presence", "bridge_universe_validation_verifier_status": "NOT_REQUIRED", "direct_source_bridge": {"candidate_id": "kis_parent"}}}}}
        return {}

    monkeypatch.setattr(dashboard, "load_json", fake_load_json)
    monkeypatch.setattr(dashboard, "load_jsonl", lambda path: [])
    monkeypatch.setattr(dashboard, "load_csv_rows", lambda path: [{"Symbol": "049630", "SubmitAllowed": "True"}, {"Symbol": "069500", "SubmitAllowed": "False"}])
    monkeypatch.setattr(dashboard, "loop_pid", lambda path, name: {"pid": "1", "running": True, "source": "test"})
    monkeypatch.setattr(dashboard, "build_model_factory_runtime_freshness", lambda loop_state: {"pid": "1", "process_predates_source": False})
    monkeypatch.setattr(dashboard, "build_model_factory_cadence", lambda model_factory_running: {"next_cycle_due_at_utc": "2026-05-18T00:30:00+00:00", "overdue": False})

    summary = dashboard.build_summary()

    assert summary["model_only_guardrails"]["kis_bridge"]["all_order_paths_false"]
    assert summary["model_only_guardrails"]["kis_universe_validation_operational"]
    assert summary["performance"]["kis_verification"]["universe_validation_mode"] == "daily_close_presence"
