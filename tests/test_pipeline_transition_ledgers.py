from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_pipeline_transition_ledgers.py")
SPEC = importlib.util.spec_from_file_location("build_pipeline_transition_ledgers", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
ledgers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledgers)


class PipelineTransitionLedgerTests(unittest.TestCase):
    def test_cand019_style_kis_axis_record_is_account_level(self) -> None:
        record = {
            "candidate_id": "CAND-019",
            "candidate_name": "sector_cap2_top2_aggressive",
            "candidate_state": "COMPRESSION_CANDIDATE",
            "universe": "KIS_COMBINED_KRW",
            "axis": "KIS_MOMENTUM",
            "metrics": {"cagr": 0.673, "mdd": -0.261, "sharpe": 1.739},
        }

        decision = ledgers.classify_research_to_compression(record, "2026-05-14T00:00:00+09:00")

        self.assertTrue(ledgers.is_account_level_record(record))
        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision["decision"], "PASS_TO_NEXT_QUEUE")
        self.assertIn("account_level_true", decision["passed_checks"])
        self.assertNotIn("not_account_level", decision["failed_checks"])

    def test_btc_only_record_does_not_become_account_level_by_account_name(self) -> None:
        record = {
            "candidate_id": "CAND-020",
            "candidate_state": "RESEARCH_CANDIDATE",
            "account": "Bithumb",
            "asset_scope": "crypto_btc_only",
            "universe_id": "BITHUMB_KRW_LONGHISTORY_PRE2020",
        }

        self.assertFalse(ledgers.is_account_level_record(record))

    def test_main_writes_stage_queue_artifacts(self) -> None:
        candidates = [
            {
                "candidate_id": "CAND-019",
                "candidate_name": "sector_cap2_top2_aggressive",
                "candidate_state": "COMPRESSION_CANDIDATE",
                "universe": "KIS_COMBINED_KRW",
                "axis": "KIS_MOMENTUM",
                "metrics": {"cagr": 0.673, "mdd": -0.261, "sharpe": 1.739},
            },
            {
                "candidate_id": "CAND-100",
                "candidate_name": "ready_for_stage5",
                "candidate_state": "ROBUSTNESS_CANDIDATE",
                "universe_id": "KIS_COMBINED_KRW",
                "is_account_level": True,
                "metrics": {"cagr": 0.4, "mdd": -0.2, "sharpe": 1.5},
            },
        ]
        robustness = [
            {
                "candidate_id": "CAND-001",
                "candidate_name": "stage5_passed",
                "evidence_status": "PASSED",
                "is_account_level": True,
                "is_component_signal": False,
                "paper_blocked": True,
                "live_blocked": True,
                "broker_submit_blocked": True,
            }
        ]
        stage6_ready = {
            "safety": {
                "paper_enabled": False,
                "live_enabled": False,
                "broker_submit_allowed": False,
                "order_intent_created": False,
            },
            "operation_controls_evidence": {
                "tradable_symbol_mapping_verified_for_current_shadow_universe": True,
                "operation_controls_verified_for_current_shadow_universe": True,
            },
            "passed_checks": [
                "cand001_stage5_evidence_passed",
                "kis_price_refresh_fresh",
                "tradable_symbol_mapping_verified_for_current_shadow_universe",
                "operation_controls_verified_for_current_shadow_universe",
            ],
            "failed_checks": [],
        }

        files: dict[str, str] = {}

        def fake_read_json(path, default):
            if str(path).endswith("CAND-001_stage6_shadow_readiness.latest.json"):
                return stage6_ready
            return default

        def fake_write_json(path, data):
            files[str(path)] = json.dumps(data)

        def fake_write_jsonl(path, rows):
            files[str(path)] = "\n".join(json.dumps(row) for row in rows)

        with (
            patch.object(ledgers, "read_jsonl", side_effect=[candidates, robustness, []]),
            patch.object(ledgers, "read_json", side_effect=fake_read_json),
            patch.object(ledgers, "read_text", return_value="mandate_status: CAPS_PROVIDED\n"),
            patch.object(ledgers, "write_json", side_effect=fake_write_json),
            patch.object(ledgers, "write_jsonl", side_effect=fake_write_jsonl),
            patch.object(ledgers, "write_audit"),
            patch("pathlib.Path.mkdir"),
        ):
            ledgers.main()

        compression_key = next(path for path in files if path.endswith("risk_compression_queue.jsonl"))
        robustness_key = next(path for path in files if path.endswith("robustness_validation_queue.jsonl"))
        shadow_key = next(path for path in files if path.endswith("shadow_queue.jsonl"))
        summary_key = next(path for path in files if path.endswith("latest_transition_ledger_summary.json"))

        self.assertIn("CAND-019", files[compression_key])
        self.assertIn("CAND-100", files[robustness_key])
        self.assertIn("CAND-001", files[shadow_key])
        summary = json.loads(files[summary_key])
        self.assertEqual(summary["risk_compression_queue_records"], 1)
        self.assertEqual(summary["robustness_validation_queue_records"], 1)
        self.assertEqual(summary["shadow_queue_records"], 1)
        self.assertEqual(summary["local_sim_paper_queue_records"], 0)
        self.assertEqual(summary["stage8_or_stage9_request_queue_records"], 0)

    def test_shadow_to_local_sim_passes_when_local_sim_evidence_exists(self) -> None:
        decision = ledgers.classify_shadow_to_local_sim(
            {
                "candidate_id": "CAND-001",
                "candidate_name": "rule_breadth_it_us5_cap (KIS baseline)",
                "decision": "LOCAL_SIM_EVIDENCE_RECORDED",
                "cycles_processed": 306,
                "trades_recorded": 4,
                "safety": {
                    "paper_enabled": False,
                    "live_enabled": False,
                    "broker_submit_allowed": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_intent_created": False,
                    "submit_mode": "local_sim_no_submit",
                },
            },
            "2026-05-14T00:00:00+09:00",
        )

        self.assertEqual(decision["decision"], "PASS_TO_NEXT_QUEUE")
        self.assertEqual(decision["from_stage"], "STAGE6_SHADOW")
        self.assertEqual(decision["to_stage"], "STAGE7_LOCAL_SIM_PAPER")
        self.assertIn("local_sim_no_submit_safety_passed", decision["passed_checks"])
        self.assertEqual(
            decision["next_queue"],
            "C:\\AI\\pipeline_orchestration\\queues\\local_sim_paper_queue.jsonl",
        )

    def test_shadow_to_local_sim_blocks_dirty_safety(self) -> None:
        decision = ledgers.classify_shadow_to_local_sim(
            {
                "candidate_id": "CAND-001",
                "decision": "LOCAL_SIM_EVIDENCE_RECORDED",
                "cycles_processed": 1,
                "trades_recorded": 1,
                "safety": {
                    "paper_enabled": False,
                    "live_enabled": False,
                    "broker_submit_allowed": True,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_intent_created": False,
                    "submit_mode": "local_sim_no_submit",
                },
            },
            "2026-05-14T00:00:00+09:00",
        )

        self.assertEqual(decision["decision"], "BLOCK")
        self.assertIn("local_sim_safety_not_clean", decision["failed_checks"])

    def test_shadow_to_local_sim_accepts_cand012_notional_allocation_mode(self) -> None:
        decision = ledgers.classify_shadow_to_local_sim(
            {
                "candidate_id": "CAND-012",
                "candidate_name": "stage2 materialized",
                "decision": "LOCAL_SIM_EVIDENCE_RECORDED",
                "simulation_mode": "notional_allocation_no_price",
                "cycles_processed": 1,
                "trades_recorded": 50,
                "safety": {
                    "paper_enabled": False,
                    "live_enabled": False,
                    "broker_submit_allowed": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_intent_created": False,
                    "submit_mode": "local_sim_no_submit",
                },
            },
            "2026-05-14T00:00:00+09:00",
        )

        self.assertEqual(decision["decision"], "PASS_TO_NEXT_QUEUE")
        self.assertEqual(decision["to_stage"], "STAGE7_LOCAL_SIM_PAPER")
        self.assertIn("local_sim_trades_recorded", decision["passed_checks"])

    def test_local_sim_to_stage8_or_9_blocks_when_approval_and_mandate_missing(self) -> None:
        decision = ledgers.classify_local_sim_to_broker_or_tiny_request(
            {
                "candidate_id": "CAND-012",
                "candidate_name": "stage2 materialized",
                "decision": "LOCAL_SIM_EVIDENCE_RECORDED",
                "cycles_processed": 3,
                "blocked_cycles": [],
                "trades_recorded": 100,
                "positions": [{"code": "kr_stock:131760", "market_value_krw": 3999.88}],
                "safety": {
                    "paper_enabled": False,
                    "live_enabled": False,
                    "broker_submit_allowed": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_intent_created": False,
                    "submit_mode": "local_sim_no_submit",
                },
            },
            "2026-05-14T00:00:00+09:00",
            {
                "mandate_status": "CAPS_PROVIDED",
                "max_order_krw": 100000,
                "max_daily_loss_krw": 20000,
                "max_total_loss_krw": 100000,
                "reporting_policy_present": False,
                "incident_policy_confirmed_present": False,
            },
            [
                {
                    "approval_type": "live",
                    "expires_at_utc": "2026-05-13T14:16:05+00:00",
                    "single_use": True,
                    "used": False,
                    "revoked": False,
                }
            ],
            {"paper_approved": False, "approval_valid": False},
            datetime(2026, 5, 14, tzinfo=timezone.utc),
        )

        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["from_stage"], "STAGE7_LOCAL_SIM_PAPER")
        self.assertEqual(decision["to_stage"], "STAGE8_OR_STAGE9")
        self.assertIn("local_sim_paper_passed", decision["passed_checks"])
        self.assertIn("risk_caps_dry_run_ok", decision["passed_checks"])
        self.assertIn("human_mandate_incomplete", decision["failed_checks"])
        self.assertIn("paper_approval_missing_for_broker_paper", decision["failed_checks"])
        self.assertIn("live_approval_expired_for_tiny_live", decision["failed_checks"])
        self.assertIn("pretrade_firewall_default_block", decision["failed_checks"])

    def test_local_sim_to_stage8_or_9_flags_max_order_exceeded(self) -> None:
        decision = ledgers.classify_local_sim_to_broker_or_tiny_request(
            {
                "candidate_id": "CAND-001",
                "decision": "LOCAL_SIM_EVIDENCE_RECORDED",
                "cycles_processed": 317,
                "blocked_cycles": [],
                "trades_recorded": 4,
                "positions": [{"code": "360750", "market_value_krw": 323760.0}],
                "safety": {
                    "paper_enabled": False,
                    "live_enabled": False,
                    "broker_submit_allowed": False,
                    "private_submit_used": False,
                    "real_orders": 0,
                    "order_intent_created": False,
                    "submit_mode": "local_sim_no_submit",
                },
            },
            "2026-05-14T00:00:00+09:00",
            {
                "mandate_status": "CAPS_PROVIDED",
                "max_order_krw": 100000,
                "max_daily_loss_krw": 20000,
                "max_total_loss_krw": 100000,
                "reporting_policy_present": False,
                "incident_policy_confirmed_present": False,
            },
            [],
            {"paper_approved": False, "approval_valid": False},
            datetime(2026, 5, 14, tzinfo=timezone.utc),
        )

        self.assertEqual(decision["decision"], "BLOCK")
        self.assertIn("risk_caps_dry_run_not_ok", decision["failed_checks"])
        self.assertIn("max_order_krw_exceeded", decision["failed_checks"])

    def test_passed_stage5_record_with_operation_blockers_is_blocked_with_clear_note(self) -> None:
        decision = ledgers.classify_robustness_to_shadow(
            {
                "candidate_id": "CAND-022",
                "candidate_name": "compressed_broe60_sroe80",
                "evidence_status": "PASSED",
                "is_account_level": True,
                "is_component_signal": False,
                "paper_blocked": True,
                "live_blocked": True,
                "broker_submit_blocked": True,
                "blockers": [
                    "data_operation_ready_not_verified",
                    "kis_order_constraints_not_verified_for_latest_cand022_symbols",
                ],
            },
            "2026-05-14T00:00:00+09:00",
        )

        self.assertEqual(decision["decision"], "BLOCK")
        self.assertIn("evidence_status_passed", decision["passed_checks"])
        self.assertIn("shadow_data_blockers_present", decision["failed_checks"])
        self.assertNotIn("shadow_operation_controls_blockers_present", decision["failed_checks"])
        self.assertIn("order_constraints_are_paper_live_blockers_not_no_submit_shadow", decision["passed_checks"])
        self.assertNotIn("stage5_blockers_present", decision["failed_checks"])
        self.assertEqual(
            decision["notes"],
            "Stage 5 evidence passed, but no-submit shadow handoff is blocked by data blockers.",
        )

    def test_passed_stage5_record_with_true_operation_control_blockers_has_specific_note(self) -> None:
        decision = ledgers.classify_robustness_to_shadow(
            {
                "candidate_id": "CAND-023",
                "candidate_name": "missing_mapping_controls",
                "evidence_status": "PASSED",
                "is_account_level": True,
                "is_component_signal": False,
                "paper_blocked": True,
                "live_blocked": True,
                "broker_submit_blocked": True,
                "blockers": [
                    "operation_controls_not_verified",
                    "tradable_symbol_mapping_not_verified",
                ],
            },
            "2026-05-14T00:00:00+09:00",
        )

        self.assertEqual(decision["decision"], "BLOCK")
        self.assertNotIn("shadow_data_blockers_present", decision["failed_checks"])
        self.assertIn("shadow_operation_controls_blockers_present", decision["failed_checks"])
        self.assertEqual(
            decision["notes"],
            "Stage 5 evidence passed, but no-submit shadow handoff is blocked by operation-control blockers.",
        )

    def test_paper_live_only_blockers_do_not_block_no_submit_shadow_handoff(self) -> None:
        decision = ledgers.classify_robustness_to_shadow(
            {
                "candidate_id": "CAND-022",
                "candidate_name": "compressed_broe60_sroe80",
                "evidence_status": "PASSED",
                "is_account_level": True,
                "is_component_signal": False,
                "paper_blocked": True,
                "live_blocked": True,
                "broker_submit_blocked": True,
                "blockers": ["human_mandate_incomplete", "approval_missing", "paper_live_broker_flags_false"],
            },
            "2026-05-14T00:00:00+09:00",
        )

        self.assertEqual(decision["decision"], "PASS_TO_NEXT_QUEUE")
        self.assertIn("paper_live_only_blockers_do_not_block_no_submit_shadow", decision["passed_checks"])
        self.assertEqual(decision["failed_checks"], [])

    def test_cand012_stage5_materialized_allows_no_submit_shadow_handoff(self) -> None:
        with patch.object(
            ledgers,
            "cand012_shadow_specific_readiness",
            return_value={
                "ready": True,
                "reason": "cand012_stage5_materialized_no_submit_readiness_passed",
                "residual_failed_checks": ["data_operation_ready_not_verified"],
            },
        ):
            decision = ledgers.classify_robustness_to_shadow(
                {
                    "candidate_id": "CAND-012",
                    "candidate_name": "stage2 materialized",
                    "evidence_status": "PASSED",
                    "is_account_level": True,
                    "is_component_signal": False,
                    "paper_blocked": True,
                    "live_blocked": True,
                    "broker_submit_blocked": True,
                    "blockers": ["data_operation_ready_not_verified"],
                },
                "2026-05-14T00:00:00+09:00",
            )

        self.assertEqual(decision["decision"], "PASS_TO_NEXT_QUEUE")
        self.assertIn("cand012_stage5_materialized_no_submit_readiness_passed", decision["passed_checks"])
        self.assertEqual(decision["to_stage"], "STAGE6_SHADOW")


if __name__ == "__main__":
    unittest.main()
