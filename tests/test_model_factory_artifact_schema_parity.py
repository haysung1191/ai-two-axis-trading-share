from __future__ import annotations

import build_simple_pipeline_dashboard as dashboard
import build_two_axis_operational_health as health


def _current_payloads() -> tuple[dict, dict, dict, dict, dict]:
    model_factory = {
        "schema_version": 2,
        "model_only_safety": {
            "mode": "model_development_and_verification_only",
            "command_manifest_has_no_order_flags": True,
            "order_submission_allowed_by_this_loop": False,
            "broker_submit_allowed_by_this_loop": False,
            "real_orders_allowed_by_this_loop": False,
        },
        "step_manifest": [{"label": label} for label in health.EXPECTED_MODEL_FACTORY_STEP_LABELS],
        "artifact_summary": {
            "direct_development": {
                "kis_source_bridge": {"candidate_id": "kis-parent"},
                "kis_universe_validation_mode": "daily_close_presence",
                "kis_universe_validation_verifier_status": "NOT_REQUIRED",
                "kis_universe_validation_operation_ready": True,
                "kis_universe_validation_all_verified": True,
                "kis_universe_validation_operational": True,
                "kis_counts_as_live_evidence": True,
                "crypto_archive_signal_triggered_count": 1,
                "crypto_top_live_signal_triggered_count": 0,
                "crypto_top_live_signal_all_verified": True,
                "crypto_top_live_near_miss_candidate": {"candidate_id": "near-direct"},
            },
            "bithumb": {
                "oos_generated_at": "2026-05-18T22:16:03+09:00",
                "oos_top_candidate_id": "oos1",
                "oos_top_market": "KRW-ORCA",
                "robustness_generated_at": "2026-05-18T22:16:04+09:00",
                "robustness_source_oos": {"top_candidate_id": "oos1"},
                "inventory_current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00",
                "inventory_current_signal_evaluated_count": 9,
                "inventory_current_signal_triggered_count": 0,
                "inventory_current_signal_candidate_id": "signal1",
                "inventory_current_signal_matches_oos_top": False,
                "inventory_oos_top_candidate_id": "oos1",
                "inventory_current_signal_selection_policy": {"sort_keys": ["source_conversion.estimated_cagr"]},
                "inventory_current_signal_selection_summary": {"selection_rank": 1},
                "inventory_oos_top_signal_selection_summary": {"selection_rank": 2},
                "inventory_current_signal_top_near_miss": {"candidate_id": "near1"},
                "inventory_current_signal_oos_summary": {"average_fold_cagr": 0.8},
                "inventory_oos_top_summary": {"average_fold_cagr": 0.9},
            },
            "kis": {
                "bridge_universe_validation_mode": "daily_close_presence",
                "bridge_universe_validation_verifier_status": "NOT_REQUIRED",
                "direct_source_bridge": {"candidate_id": "kis-parent"},
            },
        },
    }
    direct_development = {
        "crypto": {
            "archive_signal_triggered_count": 1,
            "top_live_signal_triggered_count": 0,
            "top_live_signal_summary": {"all_live_verified": True},
            "top_live_near_miss_candidate": {"candidate_id": "near-direct"},
        },
        "kis": {
            "source_bridge": {"candidate_id": "kis-parent"},
            "universe_validation_mode": "daily_close_presence",
            "universe_validation_verifier_status": "NOT_REQUIRED",
            "universe_validation_operation_ready": True,
            "universe_validation_all_verified": True,
            "universe_validation_operational": True,
            "counts_as_live_evidence": True,
        },
    }
    bithumb_oos = {"generated_at": "2026-05-18T22:16:03+09:00", "top_oos": {"candidate_id": "oos1", "market": "KRW-ORCA"}}
    bithumb_robustness = {"generated_at": "2026-05-18T22:16:04+09:00", "source_oos": {"top_candidate_id": "oos1"}}
    model_inventory = {
        "axes": {
            "BITHUMB_KRW": {
                "verification_sources": {
                    "oos_top_candidate_id": "oos1",
                    "current_signal_generated_at_utc": "2026-05-18T22:16:05+00:00",
                    "current_signal_evaluated_count": 9,
                    "current_signal_triggered_count": 0,
                    "current_signal_candidate_id": "signal1",
                    "current_signal_matches_oos_top": False,
                    "current_signal_selection_policy": {"sort_keys": ["source_conversion.estimated_cagr"]},
                    "current_signal_selection_summary": {"selection_rank": 1},
                    "oos_top_signal_selection_summary": {"selection_rank": 2},
                    "current_signal_top_near_miss": {"candidate_id": "near1"},
                    "current_signal_oos_summary": {"average_fold_cagr": 0.8},
                    "oos_top_summary": {"average_fold_cagr": 0.9},
                }
            },
            "KIS_COMBINED_KRW": {
                "verification_sources": {
                    "bridge_universe_validation_mode": "daily_close_presence",
                    "bridge_universe_validation_verifier_status": "NOT_REQUIRED",
                    "direct_source_bridge": {"candidate_id": "kis-parent"},
                }
            },
        }
    }
    return model_factory, direct_development, bithumb_oos, bithumb_robustness, model_inventory


def test_model_factory_artifact_schema_health_dashboard_parity() -> None:
    payloads = _current_payloads()

    health_result = health.build_model_factory_artifact_schema(*payloads)
    dashboard_result = dashboard.build_model_factory_artifact_schema(*payloads)

    assert dashboard_result == health_result
    assert health_result["stale_reasons"] == []
    assert health_result["stale_scope"] == "none"
    assert health_result["kis_inventory_fields_present"]


def test_model_factory_artifact_schema_reports_stale_reasons_for_old_loop_summary() -> None:
    _, direct_development, bithumb_oos, bithumb_robustness, model_inventory = _current_payloads()
    result = health.build_model_factory_artifact_schema(
        {"artifact_summary": {"direct_development": {}, "bithumb": {}, "kis": {}}},
        direct_development,
        bithumb_oos,
        bithumb_robustness,
        model_inventory,
    )

    assert result["stale_reasons"] == [
        "schema_version_missing_or_old",
        "step_manifest_missing_or_mismatch",
        "model_only_safety_missing",
        "direct_development_summary_missing_fields",
        "bithumb_summary_missing_fields",
        "kis_inventory_summary_missing_fields",
    ]
    assert result["stale_scope"] == "loop_summary_only"


def test_model_factory_running_contract_health_dashboard_parity() -> None:
    payload = {
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

    assert dashboard.build_model_factory_running_contract(payload) == health.build_model_factory_running_contract(payload)


def test_model_factory_running_contract_old_schema_health_dashboard_parity() -> None:
    payload = {"status": "TWO_AXIS_MODEL_FACTORY_OK"}

    assert dashboard.build_model_factory_running_contract(payload) == health.build_model_factory_running_contract(payload)
