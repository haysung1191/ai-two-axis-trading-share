from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_blocker_closure_plan.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_blocker_closure_plan", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
plan_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan_mod)


class Cand022Stage6BlockerClosurePlanTests(unittest.TestCase):
    def test_classifies_data_blocker_as_external_not_ai_closable(self) -> None:
        row = plan_mod.classify_blocker("kis_data_operation_ready_not_verified")

        self.assertEqual(row["owner"], "external_provider_or_source_backed_data")
        self.assertFalse(row["can_codex_close_now"])
        self.assertIn("provider_response_validated", row["required_evidence"])

    def test_build_plan_keeps_stage6_unreached_and_orders_next_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage6 = root / "stage6.json"
            operator = root / "operator.json"
            mandate = root / "mandate.json"
            mandate_apply = root / "mandate_apply.json"
            shadow = root / "shadow.json"
            preflight = root / "preflight.json"
            shadow_apply = root / "shadow_apply.json"
            router = root / "router.json"
            mapping = root / "mapping.json"
            prequeue = root / "prequeue.json"
            returned_copy = root / "returned_copy.json"
            loop = root / "run_stage6_shadow_loop.py"
            apply = root / "apply_cand022_shadow_only_exception.py"
            stage6.write_text(
                json.dumps(
                    {
                        "readiness_decision": "BLOCK",
                        "shadow_queue_allowed": False,
                        "shadow_passed": False,
                        "gatekeeper_transition": {"decision": "BLOCK", "written": True},
                        "blockers": [
                            "kis_data_operation_ready_not_verified",
                            "human_mandate_incomplete",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            operator.write_text(json.dumps({"current_decision": "BLOCK"}), encoding="utf-8")
            mandate.write_text(
                json.dumps(
                    {
                        "status": "AWAITING_EXPLICIT_HUMAN_MANDATE_COMPLETION_INSTRUCTION",
                        "do_not_auto_apply": True,
                        "caps_present": True,
                        "can_complete_after_explicit_instruction": True,
                        "missing_fields": ["reporting_policy", "incident_policy_confirmed"],
                        "exact_instruction_to_apply_recommended_values": "UPDATE HUMAN_MANDATE ...",
                        "exact_instruction_file": "C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt",
                        "guarded_dry_run_command": "python .\\apply_human_mandate_completion.py --operator-instruction-file C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt --dry-run",
                        "guarded_apply_command": "python .\\apply_human_mandate_completion.py --operator-instruction-file C:\\AI\\reports\\live_readiness\\human_mandate_completion_instruction.latest.txt",
                        "post_apply_verification_commands": [
                            "python .\\build_human_mandate_completion_packet.py",
                            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
                        ],
                        "explicit_non_approval": "Completing human_mandate.yaml is not PAPER APPROVE and not LIVE APPROVE.",
                        "safety": plan_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            mandate_apply.write_text(
                json.dumps(
                    {
                        "status": "DRY_RUN_READY_TO_APPLY_HUMAN_MANDATE_COMPLETION",
                        "dry_run": True,
                        "wrote_human_mandate": False,
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            shadow.write_text(
                json.dumps({"status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT", "required_explicit_operator_instruction_before_any_contract_change": "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"}),
                encoding="utf-8",
            )
            preflight.write_text(
                json.dumps(
                    {
                        "status": "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION",
                        "can_apply_now": False,
                        "blocked_checks": ["operator_instruction_exact_match"],
                        "guarded_apply_commands": {
                            "dry_run": 'python .\\apply_cand022_shadow_only_exception.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY" --dry-run',
                            "apply": 'python .\\apply_cand022_shadow_only_exception.py --operator-instruction "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"',
                        },
                        "post_apply_verification_commands": [
                            "python .\\build_cand022_stage6_shadow_readiness_packet.py",
                            "python .\\run_stage6_shadow_loop.py --cycles 1 --dry-run",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            shadow_apply.write_text(
                json.dumps(
                    {
                        "status": "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION",
                        "dry_run": True,
                        "wrote_acceptance": False,
                        "appended_shadow_queue": False,
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            router.write_text(
                json.dumps(
                    {
                        "recommended_next_action_id": "send_external_provider_dispatch_packet",
                        "action_router": [
                            {
                                "action_id": "send_external_provider_dispatch_packet",
                                "post_confirmation_watch_command": "python .\\run_cand022_provider_return_watch.py --cycles 180 --sleep-seconds 60 --timeout-seconds 120",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            mapping.write_text(
                json.dumps(
                    {
                        "local_mapping_pass": True,
                        "kis_api_tradability_verified_for_all": True,
                        "kis_order_constraints_verified_for_all": False,
                        "operation_mapping_pass": False,
                        "remaining_blockers": [
                            "kis_order_constraints_not_verified_for_latest_cand022_symbols",
                            "operation_controls_not_verified",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            prequeue.write_text(
                json.dumps(
                    {
                        "status": "PASS_PREQUEUE_SIGNAL_READY",
                        "signal_ok": True,
                        "symbol_count": 7,
                        "writes_files": False,
                        "submit_mode": "no_submit",
                        "latest_position_source": "current_signal_observation",
                        "safety": plan_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )
            returned_copy.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
                        "blockers": ["membership_returned_file_missing"],
                        "manual_copy_plan": [
                            {
                                "kind": "membership",
                                "from": "returned\\cand022_membership_response_draft.csv",
                                "to": "provider_handoff\\CAND-022_latest\\cand022_membership_response_draft.csv",
                                "allowed_only_if_status": "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            loop.write_text(
                'SAFETY={"broker_submit_allowed": False, "order_intent_created": False, "real_orders": 0}\n'
                'CAND022_SHADOW_EXCEPTION_ACCEPTANCE="acceptance.json"\n'
                'def validate_cand022_shadow_exception_acceptance(): return {"reason": "cand022_shadow_exception_accepted_no_submit"}\n'
                'def compute_cand022_signal(cycle_ts): pass\n'
                'def build_dry_run_cycle_report(cycle, cycle_ts): return {"candidate_reports": [], "writes_files": False}\n'
                'if candidate_id == "CAND-022": pass\n',
                encoding="utf-8",
            )
            apply.write_text(
                'SAFETY={"paper_enabled": False, "order_intent_created": False}\n'
                'REQUIRED_INSTRUCTION="APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"\n'
                'status="DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION"\n'
                'path="CAND-022_shadow_only_exception_acceptance.latest.json"\n'
                'write_json(acceptance_latest, acceptance)\n'
                'append_jsonl(queue_path, queue_row)\n'
                'forbidden=["does_not_enable_paper","does_not_create_order_intent"]\n'
                '# --dry-run\n',
                encoding="utf-8",
            )

            plan = plan_mod.build_plan(
                "2026-05-14T09:00:00+09:00",
                stage6_path=stage6,
                operator_packet_path=operator,
                human_mandate_packet_path=mandate,
                human_mandate_apply_report_path=mandate_apply,
                shadow_exception_path=shadow,
                shadow_exception_preflight_path=preflight,
                shadow_exception_apply_report_path=shadow_apply,
                router_path=router,
                tradable_mapping_path=mapping,
                prequeue_dry_run_path=prequeue,
                returned_to_handoff_copy_review_path=returned_copy,
                stage6_loop_path=loop,
                shadow_exception_apply_path=apply,
            )

        self.assertFalse(plan["stage6_reached"])
        self.assertEqual(plan["autonomous_continuation_decision"], "WAIT_FOR_OPERATOR_OR_EXTERNAL_INPUT")
        self.assertEqual(plan["recommended_next_actions_in_order"][0]["action_id"], "send_external_provider_dispatch_packet")
        self.assertEqual(
            plan["recommended_next_actions_in_order"][2]["action_id"],
            "watch_for_returned_provider_rows_after_dispatch_confirmation",
        )
        self.assertIn(
            "run_cand022_provider_return_watch.py",
            plan["recommended_next_actions_in_order"][2]["command"],
        )
        self.assertEqual(
            plan["recommended_next_actions_in_order"][3]["action_id"],
            "review_returned_to_handoff_copy_before_internal_import",
        )
        self.assertEqual(
            plan["recommended_next_actions_in_order"][3]["current_status"],
            "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertIn(
            "membership_returned_file_missing",
            plan["recommended_next_actions_in_order"][3]["current_blockers"],
        )
        self.assertEqual(
            plan["recommended_next_actions_in_order"][4]["action_id"],
            "rerun_safe_refresh_after_returned_rows",
        )
        self.assertEqual(plan["recommended_next_actions_in_order"][5]["required_exact_instruction"], "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY")
        self.assertTrue(plan["stage6_recorder_support"]["cand022_signal_computation_present"])
        self.assertTrue(plan["stage6_recorder_support"]["cand022_dispatch_present"])
        self.assertTrue(plan["stage6_recorder_support"]["per_candidate_dry_run_present"])
        self.assertTrue(plan["stage6_recorder_support"]["cand022_shadow_exception_acceptance_readiness_present"])
        self.assertTrue(plan["stage6_recorder_support"]["no_submit_safety_present"])
        self.assertTrue(plan["stage6_recorder_support"]["prequeue_dry_run_pass"])
        self.assertEqual(plan["stage6_recorder_support"]["prequeue_dry_run_symbol_count"], 7)
        self.assertEqual(
            plan["stage6_recorder_support"]["prequeue_dry_run_latest_position_source"],
            "current_signal_observation",
        )
        self.assertTrue(plan["operation_controls_current_state"]["local_mapping_pass"])
        self.assertTrue(plan["operation_controls_current_state"]["kis_api_tradability_verified_for_all"])
        self.assertFalse(plan["operation_controls_current_state"]["kis_order_constraints_verified_for_all"])
        self.assertFalse(plan["operation_controls_current_state"]["operation_mapping_pass"])
        self.assertIn(
            "kis_order_constraints_not_verified_for_latest_cand022_symbols",
            plan["operation_controls_current_state"]["remaining_blockers"],
        )
        self.assertIn(
            "not no-submit shadow blockers",
            plan["operation_controls_current_state"]["interpretation"],
        )
        self.assertTrue(plan["guarded_shadow_exception_apply_support"]["apply_script_present"])
        self.assertTrue(plan["guarded_shadow_exception_apply_support"]["dry_run_supported"])
        self.assertTrue(plan["guarded_shadow_exception_apply_support"]["acceptance_writer_present"])
        self.assertTrue(plan["guarded_shadow_exception_apply_support"]["queue_append_present"])
        self.assertEqual(
            plan["guarded_shadow_exception_apply_support"]["preflight_blocked_checks"],
            ["operator_instruction_exact_match"],
        )
        self.assertTrue(plan["guarded_shadow_exception_apply_support"]["latest_apply_guard_ready"])
        self.assertEqual(
            plan["guarded_shadow_exception_apply_support"]["latest_apply_status"],
            "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION",
        )
        self.assertFalse(plan["guarded_shadow_exception_apply_support"]["latest_apply_wrote_acceptance"])
        self.assertFalse(plan["guarded_shadow_exception_apply_support"]["latest_apply_appended_shadow_queue"])
        self.assertIn("--dry-run", plan["recommended_next_actions_in_order"][5]["dry_run_command"])
        self.assertIn(
            "python .\\build_cand022_stage6_shadow_readiness_packet.py",
            plan["guarded_shadow_exception_apply_support"]["post_apply_verification_commands"],
        )
        self.assertIn(
            "python .\\run_stage6_shadow_loop.py --cycles 1 --dry-run",
            plan["recommended_next_actions_in_order"][5]["post_apply_verification_commands"],
        )
        self.assertTrue(plan["guarded_human_mandate_apply_support"]["do_not_auto_apply"])
        self.assertTrue(plan["guarded_human_mandate_apply_support"]["safety_preserved"])
        self.assertTrue(plan["guarded_human_mandate_apply_support"]["latest_apply_guard_ready"])
        self.assertEqual(
            plan["guarded_human_mandate_apply_support"]["latest_apply_status"],
            "DRY_RUN_READY_TO_APPLY_HUMAN_MANDATE_COMPLETION",
        )
        self.assertFalse(plan["guarded_human_mandate_apply_support"]["latest_apply_wrote_human_mandate"])
        self.assertIn("--operator-instruction-file", plan["guarded_human_mandate_apply_support"]["dry_run_command"])
        self.assertIn("--dry-run", plan["recommended_next_actions_in_order"][6]["dry_run_command"])
        self.assertIn("not PAPER APPROVE", plan["recommended_next_actions_in_order"][6]["explicit_non_approval"])
        self.assertIn(
            "python .\\run_cand022_provider_response_refresh_stack.py --timeout-seconds 120",
            plan["recommended_next_actions_in_order"][6]["post_apply_verification_commands"],
        )
        self.assertIn("does_not_create_order_intent", plan["non_goals"])
        self.assertFalse(plan["safety"]["live_enabled"])


if __name__ == "__main__":
    unittest.main()
