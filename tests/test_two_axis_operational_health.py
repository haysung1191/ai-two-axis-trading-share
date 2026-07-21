from __future__ import annotations

import os

import build_two_axis_operational_health as health


def test_log_has_error_detects_python_cannot_open_file() -> None:
    assert health.log_has_error("python.exe: can't open file 'C:\\AI\\missing.py': [Errno 2] No such file or directory")


def test_log_has_error_ignores_empty_log() -> None:
    assert not health.log_has_error("")


def test_build_log_status_hides_error_tail_superseded_by_new_status(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "loop_stderr.log"
    status_path = tmp_path / "loop_latest.json"
    log_path.write_text("Traceback: old dashboard failure", encoding="utf-8")
    status_path.write_text('{"status":"OK"}', encoding="utf-8")
    os.utime(log_path, (1000, 1000))
    os.utime(status_path, (2000, 2000))
    monkeypatch.setattr(health, "LOG_STATUS_FILES", {"dashboard_stderr": status_path})

    result = health.build_log_status("dashboard_stderr", log_path)

    assert result["raw_has_error_text"]
    assert result["superseded_by_success"]
    assert not result["has_error_text"]
    assert result["tail"] == ""


def test_load_json_handles_empty_or_partial_status_file(tmp_path) -> None:
    status_path = tmp_path / "status.json"
    status_path.write_text("", encoding="utf-8")
    findings: list[str] = []

    assert health.load_json(status_path, "test_status", findings) == {}
    assert findings == ["STATUS_JSON_UNREADABLE:test_status"]

    status_path.write_text("{", encoding="utf-8")
    findings = []

    assert health.load_json(status_path, "test_status", findings) == {}
    assert findings == ["STATUS_JSON_UNREADABLE:test_status"]


def test_summarize_no_order_assertions_reports_true_flags() -> None:
    result = health.summarize_no_order_assertions(
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
    assert health.truthy_flag(True)
    assert health.truthy_flag("True")
    assert not health.truthy_flag(False)
    assert not health.truthy_flag("False")
    assert not health.truthy_flag("")


def test_classify_findings_splits_model_and_runtime_attention() -> None:
    result = health.classify_findings(
        [
            "MODEL_FACTORY_LOOP_SUMMARY_ONLY_STALE",
            "MODEL_FACTORY_RUNNING_CONTRACT_STALE",
            "KIS_ACCOUNT_SNAPSHOT_MISSING",
            "UNKNOWN_FINDING",
        ]
    )

    assert result["model_development_or_verification"] == [
        "MODEL_FACTORY_LOOP_SUMMARY_ONLY_STALE",
        "MODEL_FACTORY_RUNNING_CONTRACT_STALE",
    ]
    assert result["live_runtime_or_account"] == ["KIS_ACCOUNT_SNAPSHOT_MISSING"]
    assert result["other"] == ["UNKNOWN_FINDING"]


def test_artifact_not_older_than_compares_iso_timestamps() -> None:
    assert health.artifact_not_older_than("2026-05-18T22:16:03+09:00", "2026-05-18T22:16:04+09:00")
    assert not health.artifact_not_older_than("2026-05-18T22:16:04+09:00", "2026-05-18T22:16:03+09:00")
    assert health.artifact_not_older_than(None, "2026-05-18T22:16:03+09:00") is None


def test_summarize_order_intent_counts_submit_allowed_rows() -> None:
    result = health.summarize_order_intent(
        [
            {"Symbol": "049630", "SubmitAllowed": "True"},
            {"Symbol": "069500", "SubmitAllowed": "False"},
            {"Symbol": "327260", "SubmitAllowed": "yes"},
        ]
    )

    assert result["row_count"] == 3
    assert result["submit_allowed_count"] == 2
    assert result["submit_allowed_symbols"] == ["049630", "327260"]


def test_order_intent_summary_prefers_bridge_current_data() -> None:
    result = health.order_intent_summary_from_bridge(
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


def test_model_factory_runtime_freshness_detects_stale_process(monkeypatch) -> None:
    def fake_mtime(path):
        return "2026-05-18T12:05:00+00:00" if str(path).endswith("two_axis_model_factory_loop_latest.json") else "2026-05-18T12:00:00+00:00"

    monkeypatch.setattr(health, "file_mtime_utc", fake_mtime)
    monkeypatch.setattr(health, "process_creation_time_utc", lambda pid: "2026-05-18T11:59:00+00:00")

    result = health.build_model_factory_runtime_freshness(
        {"model_factory": {"pid": "10796", "detected_pid": "10796"}}
    )

    assert result["pid"] == "10796"
    assert result["process_predates_source"]
    assert result["latest_json_not_older_than_source"]


def test_model_factory_runtime_freshness_allows_current_process(monkeypatch) -> None:
    monkeypatch.setattr(health, "file_mtime_utc", lambda path: "2026-05-18T12:00:00+00:00")
    monkeypatch.setattr(health, "process_creation_time_utc", lambda pid: "2026-05-18T12:01:00+00:00")

    result = health.build_model_factory_runtime_freshness({"model_factory": {"pid": "10796"}})

    assert not result["process_predates_source"]
    assert result["latest_json_not_older_than_source"]


def test_model_factory_cadence_reports_overdue_when_idle_past_due() -> None:
    result = health.build_model_factory_cadence(
        {
            "status": "TWO_AXIS_MODEL_FACTORY_OK",
            "generated_at_utc": "2026-05-18T13:14:00+00:00",
            "cycle_started_at_utc": "2026-05-18T13:13:00+00:00",
            "next_cycle_due_at_utc": "2026-05-18T13:13:15+00:00",
            "completed_step_count": 8,
            "planned_step_count": 8,
        },
        now_utc="2026-05-18T13:14:20+00:00",
    )

    assert result["overdue"]
    assert result["seconds_overdue"] == 65
    assert result["elapsed_seconds"] == 60


def test_model_factory_cadence_does_not_report_running_cycle_overdue() -> None:
    result = health.build_model_factory_cadence(
        {
            "status": "TWO_AXIS_MODEL_FACTORY_RUNNING",
            "generated_at_utc": "2026-05-18T13:13:00+00:00",
            "cycle_started_at_utc": "2026-05-18T13:13:00+00:00",
            "next_cycle_due_at_utc": "2026-05-18T13:13:15+00:00",
            "current_step": "two axis direct model development",
            "step_index": 1,
            "step_count": 8,
        },
        now_utc="2026-05-18T13:14:20+00:00",
    )

    assert not result["overdue"]
    assert result["seconds_overdue"] == 0
    assert result["step_index"] == 1
    assert result["planned_step_count"] == 8
    assert result["elapsed_seconds"] == 80


def test_model_factory_running_contract_detects_current_running_schema() -> None:
    result = health.build_model_factory_running_contract(
        {
            "schema_version": health.EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
            "status": "TWO_AXIS_MODEL_FACTORY_RUNNING",
            "current_step": "bithumb parameter sweep",
            "step_manifest": [{"label": label} for label in health.EXPECTED_MODEL_FACTORY_STEP_LABELS],
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
    result = health.build_model_factory_running_contract({"status": "TWO_AXIS_MODEL_FACTORY_OK"})

    assert not result["contract_current"]
    assert not result["schema_version_current"]
    assert not result["step_manifest_matches_expected"]
    assert not result["model_only_safety_present"]



def test_model_factory_artifact_schema_flags_missing_direct_kis_fields() -> None:
    result = health.build_model_factory_artifact_schema(
        {"artifact_summary": {"direct_development": {"status": "TWO_AXIS_DIRECT_DEVELOPMENT_OK"}}},
        {
            "kis": {
                "source_bridge": {"candidate_id": "kis_parent"},
                "universe_validation_mode": "daily_close_presence",
                "universe_validation_verifier_status": "NOT_REQUIRED",
                "universe_validation_operation_ready": True,
                "universe_validation_all_verified": True,
                "universe_validation_operational": True,
                "counts_as_live_evidence": True,
            }
        },
        {"generated_at": "2026-05-18T22:16:03+09:00", "top_oos": {"candidate_id": "oos1", "market": "KRW-ORCA"}},
        {"generated_at": "2026-05-18T22:16:04+09:00", "source_oos": {"top_candidate_id": "oos1"}},
        {
            "axes": {
                "BITHUMB_KRW": {"verification_sources": {"oos_top_candidate_id": "oos1", "current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00", "current_signal_evaluated_count": 9}},
                "KIS_COMBINED_KRW": {"verification_sources": {"bridge_universe_validation_mode": "daily_close_presence", "bridge_universe_validation_verifier_status": "NOT_REQUIRED", "direct_source_bridge": {"candidate_id": "kis_parent"}}},
            }
        },
    )

    assert not result["direct_kis_validation_fields_present"]
    assert "kis_universe_validation_operational" in result["missing_direct_development_fields"]
    assert result["canonical_child_artifacts_complete"]


def test_model_factory_artifact_schema_accepts_current_direct_kis_fields() -> None:
    model_factory = {
        "schema_version": health.EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
        "step_manifest": [{"label": label} for label in health.EXPECTED_MODEL_FACTORY_STEP_LABELS],
        "model_only_safety": {"command_manifest_has_no_order_flags": True, "order_submission_allowed_by_this_loop": False, "broker_submit_allowed_by_this_loop": False, "real_orders_allowed_by_this_loop": False},
        "artifact_summary": {
            "direct_development": {"kis_source_bridge": {"candidate_id": "kis_parent"}, "kis_universe_validation_mode": "daily_close_presence", "kis_universe_validation_verifier_status": "NOT_REQUIRED", "kis_universe_validation_operation_ready": True, "kis_universe_validation_all_verified": True, "kis_universe_validation_operational": True, "kis_counts_as_live_evidence": True, "crypto_archive_signal_triggered_count": 1, "crypto_top_live_signal_triggered_count": 0, "crypto_top_live_signal_all_verified": True, "crypto_top_live_near_miss_candidate": {"candidate_id": "near"}},
            "bithumb": {"oos_generated_at": "2026-05-18T22:16:03+09:00", "oos_top_candidate_id": "oos1", "oos_top_market": "KRW-ORCA", "robustness_generated_at": "2026-05-18T22:16:04+09:00", "robustness_source_oos": {"top_candidate_id": "oos1"}, "inventory_current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00", "inventory_current_signal_evaluated_count": 9, "inventory_current_signal_triggered_count": 0, "inventory_current_signal_candidate_id": "signal2", "inventory_current_signal_matches_oos_top": False, "inventory_oos_top_candidate_id": "oos1", "inventory_current_signal_selection_policy": {"sort_keys": ["source_conversion.estimated_cagr"]}, "inventory_current_signal_selection_summary": {"selection_rank": 1}, "inventory_oos_top_signal_selection_summary": {"selection_rank": 2}, "inventory_current_signal_top_near_miss": {"candidate_id": "near1"}, "inventory_current_signal_top_near_miss_candidates": [{"candidate_id": "near1"}], "inventory_current_signal_oos_summary": {"average_fold_cagr": 0.8}, "inventory_oos_top_summary": {"average_fold_cagr": 0.9}},
            "kis": {"bridge_universe_validation_mode": "daily_close_presence", "bridge_universe_validation_verifier_status": "NOT_REQUIRED", "direct_source_bridge": {"candidate_id": "kis_parent"}},
        },
    }
    direct = {"crypto": {"archive_signal_triggered_count": 1, "top_live_signal_triggered_count": 0, "top_live_signal_summary": {"all_live_verified": True}, "top_live_near_miss_candidate": {"candidate_id": "near"}}, "kis": {"source_bridge": {"candidate_id": "kis_parent"}, "universe_validation_mode": "daily_close_presence", "universe_validation_verifier_status": "NOT_REQUIRED", "universe_validation_operation_ready": True, "universe_validation_all_verified": True, "universe_validation_operational": True, "counts_as_live_evidence": True}}
    inventory_payload = {"axes": {"BITHUMB_KRW": {"verification_sources": {"oos_top_candidate_id": "oos1", "current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00", "current_signal_evaluated_count": 9, "current_signal_triggered_count": 0, "current_signal_candidate_id": "signal2", "current_signal_matches_oos_top": False, "current_signal_selection_policy": {"sort_keys": ["source_conversion.estimated_cagr"]}, "current_signal_selection_summary": {"selection_rank": 1}, "oos_top_signal_selection_summary": {"selection_rank": 2}, "current_signal_top_near_miss": {"candidate_id": "near1"}, "current_signal_top_near_miss_candidates": [{"candidate_id": "near1"}], "current_signal_oos_summary": {"average_fold_cagr": 0.8}, "oos_top_summary": {"average_fold_cagr": 0.9}}}, "KIS_COMBINED_KRW": {"verification_sources": {"bridge_universe_validation_mode": "daily_close_presence", "bridge_universe_validation_verifier_status": "NOT_REQUIRED", "direct_source_bridge": {"candidate_id": "kis_parent"}}}}}

    result = health.build_model_factory_artifact_schema(model_factory, direct, {"generated_at": "2026-05-18T22:16:03+09:00", "top_oos": {"candidate_id": "oos1", "market": "KRW-ORCA"}}, {"generated_at": "2026-05-18T22:16:04+09:00", "source_oos": {"top_candidate_id": "oos1"}}, inventory_payload)

    assert result["direct_kis_validation_fields_present"]
    assert result["kis_inventory_fields_present"]
    assert result["canonical_child_artifacts_complete"]
def test_build_report_treats_string_false_submit_flags_as_false(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    paths["bithumb"].write_text('{"global_disable_present":"False"}', encoding="utf-8")
    paths["kis"].write_text('{"submit_enabled":"False"}', encoding="utf-8")
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert "BITHUMB_GLOBAL_DISABLE_PRESENT" not in report["findings"]
    assert "KIS_SUBMIT_NOT_ENABLED" in report["findings"]


def test_atomic_write_text_replaces_target_with_complete_content(tmp_path) -> None:
    path = tmp_path / "health.json"
    path.write_text('{"old": true}', encoding="utf-8")

    health.atomic_write_text(path, '{"new": true}')

    assert path.read_text(encoding="utf-8") == '{"new": true}'
    assert not path.with_name(".health.json.tmp").exists()


def test_build_report_flags_model_only_guardrail_attention(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text(
        '{"status":"OK","submit_enabled":true,"operating_candidate_bridge":{"source_order_paths_allowed":true,"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}}',
        encoding="utf-8",
    )
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(
        '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_oos"].write_text(
        '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_robustness"].write_text(
        '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert "MODEL_ONLY_GUARDRAIL_ATTENTION" in report["findings"]
    assert "MODEL_ONLY_GUARDRAIL_ATTENTION" in report["finding_groups"]["model_development_or_verification"]
    assert not report["model_only_guardrails"]["all_known_order_paths_false"]
    assert report["model_only_guardrails"]["kis_bridge"]["all_order_paths_false"]
    assert report["model_only_guardrails"]["kis_true_order_path_flags"] == ["source_order_paths_allowed"]


def test_build_report_prefers_standalone_kis_bridge_for_guardrails(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text(
        '{"status":"OK","submit_enabled":true,"operating_candidate_bridge":{"no_order_assertions":{"live_allowed_by_this_report":true}}}',
        encoding="utf-8",
    )
    paths["kis_bridge"].write_text(
        '{"status":"OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY","generated_at_utc":"2026-05-18T00:00:00+00:00","candidate_id":"kis_parent","execution_warnings":["KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE"],"universe_validation_mode":"daily_close_presence","universe_validation_verifier_status":"NOT_REQUIRED","universe_validation_operation_ready":true,"universe_validation_all_verified":true,"universe_validation_blockers":["authoritative_pit_membership_history_missing_for_kis_combined"],"current_data":{"order_intent_rows":3,"order_intent_submit_allowed_count":2,"order_intent_submit_allowed_symbols":["049630","327260"]},"target_book":{"symbols":["049630","069500"],"tiny_live_buyable_symbol_count":1},"tiny_live_executable_repair":{"status":"TINY_LIVE_REPAIR_RESEARCH_READY","buyable_count":1,"quality":{"status":"TINY_LIVE_REPAIR_QUALITY_PASS"},"historical_oos_validation":{"status":"TINY_LIVE_REPAIR_OOS_PASS","months":62,"summary":{"CAGR":0.1,"MDD":-0.11,"Sharpe":0.8},"holdout_30pct":{"CAGR":0.3},"cost_stress_25bps":{"CAGR":0.09},"walkforward":{"pass_folds":3,"folds":4}}},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text(
        '{"status":"TWO_AXIS_MODEL_FACTORY_OK","next_cycle_due_at_utc":"2026-05-18T00:30:00+00:00"}',
        encoding="utf-8",
    )
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(
        '{"status":"TWO_AXIS_DIRECT_DEVELOPMENT_OK","generated_at_utc":"2026-05-18T00:00:01+00:00","crypto":{"candidate_count":10,"oos_pass_count":6,"validated_pass_count":3,"archive_signal_triggered_count":1,"top_live_signal_triggered_count":0,"top_live_signal_summary":{"all_live_verified":true},"top_live_near_miss_candidate":{"candidate_id":"direct_near1","market":"KRW-BTC","nearest_trigger_gap":-0.4,"momentum_gap":-0.02,"volume_gap":-0.4,"blocking_conditions":["volume_ratio_below_floor"]}},"kis":{"conversion_variant_count":5,"pass_count":2,"source_bridge":{"generated_at_utc":"2026-05-18T00:00:00+00:00","status":"OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY","candidate_id":"kis_parent","universe_validation_mode":"daily_close_presence"},"top_variants":[{"parent_candidate_id":"kis_parent","status":"DIRECT_CONVERSION_PASS"}],"universe_validation_mode":"daily_close_presence","universe_validation_verifier_status":"NOT_REQUIRED","universe_validation_operation_ready":true,"universe_validation_all_verified":true,"universe_validation_pit_survivorship_safe":false,"counts_as_live_evidence":true,"pit_verifier_status":"NOT_REQUIRED","pit_axis_wide_worklist_fill_status":"BLOCK_WORKLIST_FILL_PROGRESS","pit_axis_wide_source_acquisition_remaining_row_count":16437,"pit_axis_wide_source_acquisition_completion_ratio":0.0},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_oos"].write_text(
        '{"status":"OOS_WALKFORWARD_PASS","generated_at":"2026-05-18T22:16:03+09:00","aggregate":{"candidate_count":9,"evaluated_count":9,"pass_count":6},"top_oos":{"candidate_id":"oos1","market":"KRW-ORCA"},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_robustness"].write_text(
        '{"status":"ROBUSTNESS_STRESS_PASS","generated_at":"2026-05-18T22:16:04+09:00","source_oos":{"generated_at":"2026-05-18T22:16:03+09:00","top_candidate_id":"oos1","top_market":"KRW-ORCA"},"candidate_id":"oos1","pass_count":7,"case_count":7,"cost_pass_count":1,"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    if 'kis_pit_verifier' in paths:
        paths["kis_pit_verifier"].write_text(
        '{"single_next_action":"Replace caveated rows.","axis_reports":[{"axis":"kis_us_stocks","row_count":7397,"caveated_row_count":7392,"operation_ready_quality_row_count":5,"replacement_remaining_count":7392,"operation_ready_coverage":0.000676,"source_verified_membership_ready_row_count":5,"source_verified_membership_gap_after_ready_rows":7387,"source_verified_membership_ready_coverage_of_remaining":0.000676,"verified":false}],"remediation_priority":[{"axis":"kis_us_stocks","replacement_remaining_count":7392,"source_verified_membership_gap_after_ready_rows":7387,"row_count":7397,"operation_ready_coverage":0.000676}],"next_evidence_acquisition_targets":[{"rank":1,"axis":"kis_us_stocks","missing_membership_rows":7387,"source_verified_membership_ready_rows":5,"reason":"largest_source_verified_membership_gap"}],"intake_source_package":{"preflight_ready_rows_by_kind":{"membership":7,"event_or_no_event":7,"replay":4},"membership_ready_rows_by_axis":{"kis_us_stocks":5,"kis_korea_etfs":2},"event_ready_rows_by_axis":{"kis_us_stocks":5,"kis_korea_etfs":2},"source_artifact_registry_status":"PASS_SOURCE_ARTIFACT_REGISTRY_VERIFIED","source_artifact_registry_passed_rows":18,"source_provenance_status":"PASS_INTAKE_SOURCE_PROVENANCE_VERIFIED","source_provenance_passed_ready_rows":18,"source_verified_coverage_gap":12426}}',
        encoding="utf-8",
    )
    if 'kis_axis_wide_handoff' in paths:
        paths["kis_axis_wide_handoff"].write_text(
        '{"status":"READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE","generated_at_utc":"2026-05-18T22:00:01+00:00","request_count":4}',
        encoding="utf-8",
    )
    paths["model_inventory"].write_text(
        '{"axes":{"BITHUMB_KRW":{"verification_sources":{"oos_top_candidate_id":"oos1","current_signal_generated_at":"2026-05-19T07:00:00+09:00","current_signal_generated_at_utc":"2026-05-18T22:00:00+00:00","current_signal_evaluated_count":9,"current_signal_triggered_count":0,"current_signal_candidate_id":"oos1","current_signal_matches_oos_top":true,"current_signal_top_near_miss_candidates":[{"candidate_id":"near1","momentum_gap":-0.01,"volume_gap":-0.3},{"candidate_id":"near2","momentum_gap":-0.02,"volume_gap":-0.2}],"current_signal_oos_summary":{"average_fold_cagr":0.8,"total_trade_count":17},"oos_top_summary":{"average_fold_cagr":0.9,"total_trade_count":19}}},"KIS_COMBINED_KRW":{"verification_sources":{"pit_source_acquisition_queue_generated_at_utc":"2026-05-18T22:00:02+00:00","pit_source_acquisition_queue_status":"BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED","pit_source_acquisition_queue_counts":{"total":4,"axis_wide_operation_ready":4},"pit_next_evidence_fill_card_generated_at_utc":"2026-05-18T22:00:03+00:00","pit_next_evidence_fill_card_status":"BLOCK_AXIS_WIDE_EVIDENCE_ACQUISITION_REQUIRED","pit_next_evidence_fill_card_queue_id":"KIS_SRC_001","pit_next_evidence_fill_card_axis":"kis_us_stocks","pit_next_evidence_fill_card_missing_rows":7387}}}}',
        encoding="utf-8",
    )
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    order_intent_csv = tmp_path / "order_intent.csv"
    order_intent_csv.write_text(
        "Symbol,SubmitAllowed\n049630,True\n069500,False\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", order_intent_csv)
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert "MODEL_ONLY_GUARDRAIL_ATTENTION" not in report["findings"]
    assert "KIS_ORDER_INTENT_SUBMIT_ALLOWED_ARTIFACT" in report["findings"]
    assert "KIS_ORDER_INTENT_SUBMIT_ALLOWED_ARTIFACT" in report["finding_groups"]["live_runtime_or_account"]
    assert report["model_only_guardrails"]["kis_bridge"]["all_order_paths_false"]
    assert report["model_only_guardrails"]["source_generated_at_utc"]["kis_bridge"] == "2026-05-18T00:00:00+00:00"
    assert report["model_factory_cadence"]["next_cycle_due_at_utc"] == "2026-05-18T00:30:00+00:00"
    assert report["model_only_guardrails"]["all_known_order_paths_false"]
    assert report["model_only_guardrails"]["model_only_attention"]
    assert report["model_only_guardrails"]["kis_order_intent_submit_allowed_count"] == 2
    assert report["model_only_guardrails"]["kis_order_intent_summary_source"] == "bridge_current_data"
    assert report["model_verification"]["direct_development"]["status"] == "TWO_AXIS_DIRECT_DEVELOPMENT_OK"
    assert report["model_verification"]["direct_development"]["crypto_candidate_count"] == 10
    assert report["model_verification"]["direct_development"]["crypto_oos_pass_count"] == 6
    assert report["model_verification"]["direct_development"]["crypto_validated_pass_count"] == 3
    assert report["model_verification"]["direct_development"]["crypto_archive_signal_triggered_count"] == 1
    assert report["model_verification"]["direct_development"]["crypto_top_live_signal_triggered_count"] == 0
    assert report["model_verification"]["direct_development"]["crypto_top_live_signal_all_verified"]
    assert report["model_verification"]["direct_development"]["crypto_top_live_near_miss_candidate"]["candidate_id"] == "direct_near1"
    assert report["model_verification"]["direct_development"]["kis_pass_count"] == 2
    assert report["model_verification"]["direct_development"]["kis_universe_validation_mode"] == "daily_close_presence"
    assert report["model_verification"]["direct_development"]["kis_universe_validation_verifier_status"] == "NOT_REQUIRED"
    assert report["model_verification"]["direct_development"]["kis_universe_validation_operation_ready"]
    assert report["model_verification"]["direct_development"]["kis_universe_validation_all_verified"]
    assert report["model_verification"]["direct_development"]["kis_counts_as_live_evidence"]
    assert report["model_verification"]["bithumb"]["oos_pass_count"] == 6
    assert report["model_verification"]["bithumb"]["oos_top_candidate_id"] == "oos1"
    assert report["model_verification"]["bithumb"]["oos_top_market"] == "KRW-ORCA"
    assert report["model_verification"]["bithumb"]["inventory_current_signal_generated_at_utc"] == "2026-05-18T22:00:00+00:00"
    assert report["model_verification"]["bithumb"]["inventory_current_signal_evaluated_count"] == 9
    assert report["model_verification"]["bithumb"]["inventory_current_signal_triggered_count"] == 0
    assert report["model_verification"]["bithumb"]["inventory_current_signal_candidate_id"] == "oos1"
    assert report["model_verification"]["bithumb"]["inventory_oos_top_candidate_id"] == "oos1"
    assert report["model_verification"]["bithumb"]["inventory_current_signal_matches_oos_top"]
    assert report["model_verification"]["bithumb"]["inventory_current_signal_oos_average_fold_cagr"] == 0.8
    assert report["model_verification"]["bithumb"]["inventory_current_signal_near_miss_candidates"][1]["candidate_id"] == "near2"
    assert report["model_verification"]["bithumb"]["inventory_oos_top_average_fold_cagr"] == 0.9
    assert report["model_verification"]["bithumb"]["inventory_current_signal_oos_trade_count"] == 17
    assert report["model_verification"]["bithumb"]["inventory_oos_top_trade_count"] == 19
    assert not report["model_verification"]["bithumb"]["oos_order_paths_allowed"]
    assert report["model_verification"]["bithumb"]["robustness_candidate_id"] == "oos1"
    assert report["model_verification"]["bithumb"]["robustness_matches_oos_top"]
    assert report["model_verification"]["bithumb"]["robustness_source_oos_matches_current"]
    assert report["model_verification"]["bithumb"]["robustness_not_older_than_oos"]
    assert not report["model_verification"]["bithumb"]["robustness_order_paths_allowed"]
    assert report["model_verification"]["kis"]["bridge_status"] == "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY"
    assert report["model_verification"]["kis"]["bridge_execution_warnings"] == ["KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE"]
    assert report["model_verification"]["kis"]["direct_top_parent_candidate_id"] == "kis_parent"
    assert report["model_verification"]["kis"]["bridge_matches_direct_top_parent"]
    assert report["model_verification"]["kis"]["universe_validation_mode"] == "daily_close_presence"
    assert report["model_verification"]["kis"]["universe_validation_verifier_status"] == "NOT_REQUIRED"
    assert report["model_verification"]["kis"]["universe_validation_operation_ready"]
    assert report["model_verification"]["kis"]["universe_validation_all_verified"]
    assert report["model_verification"]["kis"]["direct_bridge_universe_validation_match"]
    assert report["model_verification"]["kis"]["direct_not_older_than_bridge"]
    assert report["model_verification"]["kis"]["direct_source_bridge_matches_current"]
    assert not report["model_verification"]["kis"]["repair_order_paths_allowed"]
    assert report["model_verification"]["kis"]["repair_oos_status"] == "TINY_LIVE_REPAIR_OOS_PASS"
    assert not report["model_verification"]["kis"]["repair_oos_order_paths_allowed"]
    assert report["model_verification"]["kis"]["repair_oos_pass_folds"] == 3
    assert report["model_verification"]["kis"]["order_intent_row_count"] == 3
    assert report["model_verification"]["kis"]["order_intent_submit_allowed_count"] == 2
    assert report["model_verification"]["kis"]["order_intent_summary_source"] == "bridge_current_data"

    monkeypatch.setattr(health, "OUT_MD", tmp_path / "health.md")
    health.write_md(report)
    markdown = (tmp_path / "health.md").read_text(encoding="utf-8")

    assert "Direct Bithumb live near miss: `direct_near1`, market `KRW-BTC`, gap `-0.4`, blockers `volume_ratio_below_floor`." in markdown
    assert "Bithumb OOS: `OOS_WALKFORWARD_PASS`, pass `6/9`, top `oos1` `KRW-ORCA`, order paths `False`" in markdown
    assert "Bithumb current signal scout: generated `2026-05-18T22:00:00+00:00`, evaluated `9`, triggered `0`." in markdown
    assert "Bithumb current signal near miss candidates: `2`." in markdown
    assert "Bithumb inventory current signal: `oos1`, inventory OOS top `oos1`, matches OOS top `True`, current signal avg fold CAGR `0.8`, OOS top avg fold CAGR `0.9`, current signal trades `17`, OOS top trades `19`." in markdown
    assert "Bithumb robustness: `ROBUSTNESS_STRESS_PASS`, candidate `oos1`, matches OOS top `True`, source OOS matches current `True`, not older than OOS `True`" in markdown
    assert "KIS bridge: `OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY`, candidate `kis_parent`, buyable `1/2`, warnings `KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE`." in markdown
    assert "KIS bridge/direct top match: `True`, direct top parent `kis_parent`." in markdown
    assert "KIS verification order paths: repair `False`, repair OOS `False`, live evidence `False`, OOS evidence `False`." in markdown
    assert "KIS direct/bridge universe validation match: `True`." in markdown
    assert "Model factory latest artifact freshness: latest not older than source `" in markdown
    assert "Canonical child artifacts:" in markdown
    assert "KIS direct not older than bridge: `True`." in markdown
    assert "KIS direct source bridge matches current: `True`." in markdown
    assert "KIS order intent artifact: rows `3`, submit allowed `2`, symbols `049630, 327260`." in markdown


def test_build_report_flags_robustness_older_than_oos(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text('{"status":"OK","submit_enabled":true}', encoding="utf-8")
    paths["kis_bridge"].write_text(safe_assertions, encoding="utf-8")
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(safe_assertions, encoding="utf-8")
    paths["bithumb_oos"].write_text(
        '{"status":"OOS_WALKFORWARD_PASS","generated_at":"2026-05-18T22:16:04+09:00","top_oos":{"candidate_id":"oos1","market":"KRW-ORCA"},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_robustness"].write_text(
        '{"status":"ROBUSTNESS_STRESS_PASS","generated_at":"2026-05-18T22:16:03+09:00","candidate_id":"oos1","no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert report["model_verification"]["bithumb"]["robustness_matches_oos_top"]
    assert not report["model_verification"]["bithumb"]["robustness_not_older_than_oos"]
    assert "BITHUMB_ROBUSTNESS_OLDER_THAN_OOS" in report["findings"]


def test_build_report_flags_current_signal_oos_top_mismatch(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text('{"status":"OK","submit_enabled":true}', encoding="utf-8")
    paths["kis_bridge"].write_text(safe_assertions, encoding="utf-8")
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(safe_assertions, encoding="utf-8")
    paths["bithumb_oos"].write_text(
        '{"status":"OOS_WALKFORWARD_PASS","generated_at":"2026-05-18T22:16:03+09:00","top_oos":{"candidate_id":"oos1","market":"KRW-ORCA"},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_robustness"].write_text(safe_assertions, encoding="utf-8")
    paths["model_inventory"].write_text(
        '{"axes":{"BITHUMB_KRW":{"verification_sources":{"oos_top_candidate_id":"oos1","current_signal_candidate_id":"signal2","current_signal_matches_oos_top":false}}}}',
        encoding="utf-8",
    )
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert report["model_verification"]["bithumb"]["inventory_current_signal_candidate_id"] == "signal2"
    assert report["model_verification"]["bithumb"]["inventory_oos_top_candidate_id"] == "oos1"
    assert not report["model_verification"]["bithumb"]["inventory_current_signal_matches_oos_top"]
    assert "BITHUMB_CURRENT_SIGNAL_OOS_TOP_MISMATCH" in report["findings"]


def test_build_report_flags_robustness_source_oos_mismatch(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text('{"status":"OK","submit_enabled":true}', encoding="utf-8")
    paths["kis_bridge"].write_text(safe_assertions, encoding="utf-8")
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(safe_assertions, encoding="utf-8")
    paths["bithumb_oos"].write_text(
        '{"status":"OOS_WALKFORWARD_PASS","generated_at":"2026-05-18T22:16:03+09:00","top_oos":{"candidate_id":"oos1","market":"KRW-ORCA"},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_robustness"].write_text(
        '{"status":"ROBUSTNESS_STRESS_PASS","generated_at":"2026-05-18T22:16:04+09:00","source_oos":{"generated_at":"2026-05-18T22:00:00+09:00","top_candidate_id":"old1","top_market":"KRW-BTC"},"candidate_id":"oos1","no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert report["model_verification"]["bithumb"]["robustness_matches_oos_top"]
    assert not report["model_verification"]["bithumb"]["robustness_source_oos_matches_current"]
    assert "BITHUMB_ROBUSTNESS_SOURCE_OOS_MISMATCH" in report["findings"]


def test_build_report_flags_kis_bridge_direct_top_parent_mismatch(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text('{"status":"OK","submit_enabled":true}', encoding="utf-8")
    paths["kis_bridge"].write_text(
        '{"status":"OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY","candidate_id":"bridge_parent","universe_validation_mode":"daily_close_presence","no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(
        '{"kis":{"top_variants":[{"parent_candidate_id":"direct_parent","status":"DIRECT_CONVERSION_PASS"}]},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_oos"].write_text(safe_assertions, encoding="utf-8")
    paths["bithumb_robustness"].write_text(safe_assertions, encoding="utf-8")
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert report["model_verification"]["kis"]["direct_top_parent_candidate_id"] == "direct_parent"
    assert not report["model_verification"]["kis"]["bridge_matches_direct_top_parent"]
    assert "KIS_BRIDGE_DIRECT_TOP_PARENT_MISMATCH" in report["findings"]


def test_build_report_flags_direct_bridge_universe_validation_mismatch(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text('{"status":"OK","submit_enabled":true}', encoding="utf-8")
    paths["kis_bridge"].write_text(
        '{"universe_validation_mode":"daily_close_presence","no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(
        '{"kis":{"universe_validation_mode":"legacy_disabled_mode"},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_oos"].write_text(safe_assertions, encoding="utf-8")
    paths["bithumb_robustness"].write_text(safe_assertions, encoding="utf-8")
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert not report["model_verification"]["kis"]["direct_bridge_universe_validation_match"]
    assert "KIS_DIRECT_BRIDGE_UNIVERSE_VALIDATION_MISMATCH" in report["findings"]


def test_build_report_flags_direct_development_older_than_bridge(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text('{"status":"OK","submit_enabled":true}', encoding="utf-8")
    paths["kis_bridge"].write_text(
        '{"generated_at_utc":"2026-05-18T00:00:02+00:00","universe_validation_mode":"daily_close_presence","no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(
        '{"generated_at_utc":"2026-05-18T00:00:01+00:00","kis":{"universe_validation_mode":"daily_close_presence"},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_oos"].write_text(safe_assertions, encoding="utf-8")
    paths["bithumb_robustness"].write_text(safe_assertions, encoding="utf-8")
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert report["model_verification"]["kis"]["direct_bridge_universe_validation_match"]
    assert not report["model_verification"]["kis"]["direct_not_older_than_bridge"]
    assert "KIS_DIRECT_DEVELOPMENT_OLDER_THAN_BRIDGE" in report["findings"]


def test_build_report_flags_direct_source_bridge_mismatch(monkeypatch, tmp_path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    paths = {}
    for name in health.STATUS_FILES:
        path = status_dir / f"{name}.json"
        path.write_text("{}", encoding="utf-8")
        paths[name] = path

    safe_assertions = '{"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}'
    paths["bithumb"].write_text('{"status":"OK"}', encoding="utf-8")
    paths["kis"].write_text('{"status":"OK","submit_enabled":true}', encoding="utf-8")
    paths["kis_bridge"].write_text(
        '{"generated_at_utc":"2026-05-18T00:00:00+00:00","candidate_id":"kis_parent","universe_validation_mode":"daily_close_presence","no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["model_factory"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["model_factory_running"].write_text('{"status":"TWO_AXIS_MODEL_FACTORY_OK"}', encoding="utf-8")
    paths["limited_policy"].write_text('{"crypto_cap_krw":100000,"crypto_max_daily_loss_krw":20000}', encoding="utf-8")
    paths["direct_development"].write_text(
        '{"generated_at_utc":"2026-05-18T00:00:01+00:00","kis":{"source_bridge":{"generated_at_utc":"2026-05-18T00:00:00+00:00","candidate_id":"old_parent","universe_validation_mode":"daily_close_presence"},"universe_validation_mode":"daily_close_presence"},"no_order_assertions":{"live_allowed_by_this_report":false,"real_orders_allowed_by_this_report":false}}',
        encoding="utf-8",
    )
    paths["bithumb_oos"].write_text(safe_assertions, encoding="utf-8")
    paths["bithumb_robustness"].write_text(safe_assertions, encoding="utf-8")
    paths["dashboard"].write_text('{"model_only_guardrails":{"all_known_order_paths_false":true}}', encoding="utf-8")

    monkeypatch.setattr(health, "STATUS_FILES", paths)
    monkeypatch.setattr(health, "KIS_LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(health, "KIS_ORDER_INTENT_CSV", tmp_path / "order_intent.csv")
    monkeypatch.setattr(health, "PID_FILES", {})
    monkeypatch.setattr(health, "LOG_FILES", {})

    report = health.build_report()

    assert report["model_verification"]["kis"]["direct_bridge_universe_validation_match"]
    assert not report["model_verification"]["kis"]["direct_source_bridge_matches_current"]
    assert "KIS_DIRECT_SOURCE_BRIDGE_MISMATCH" in report["findings"]




