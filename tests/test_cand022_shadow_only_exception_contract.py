from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_shadow_only_exception_contract.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_shadow_only_exception_contract", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
contract_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract_mod)


class Cand022ShadowOnlyExceptionContractTests(unittest.TestCase):
    def test_contract_is_review_only_no_submit_and_preserves_safety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            operator_packet = root / "operator_packet.json"
            tiny_audit = root / "tiny.json"
            pit_audit = root / "pit.json"
            shadow = root / "shadow.json"
            operator_packet.write_text(
                json.dumps(
                    {
                        "decision_groups": [
                            {
                                "group_id": "kis_pit_survivorship_policy",
                                "operator_choices": [
                                    {"choice_id": "data_upgrade_required"},
                                    {"choice_id": "shadow_only_exception"},
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            tiny_audit.write_text(json.dumps({"completion_decision": "NOT_COMPLETE"}), encoding="utf-8")
            pit_audit.write_text(json.dumps({"status": "DATA_BLOCKED"}), encoding="utf-8")
            shadow.write_text(json.dumps({"status": "BLOCK_STAGE6_SHADOW_READINESS"}), encoding="utf-8")

            contract = contract_mod.build_contract(
                "2026-05-14T06:00:00+09:00",
                operator_packet_path=operator_packet,
                tiny_live_audit_path=tiny_audit,
                pit_audit_path=pit_audit,
                shadow_readiness_path=shadow,
            )

        self.assertEqual(contract["status"], "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT")
        self.assertFalse(contract["is_approval"])
        self.assertFalse(contract["auto_apply_allowed"])
        self.assertFalse(contract["contract_changes_allowed_by_this_file"])
        self.assertEqual(contract["recommended_policy_choice"], "shadow_only_exception")
        self.assertIn("record_no_submit_shadow_observation_only", contract["allowed_scope_if_operator_explicitly_accepts_later"])
        self.assertIn("do_not_create_order_intent", contract["forbidden_actions"])
        self.assertIn("do_not_enable_live", contract["forbidden_actions"])
        self.assertIn("do_not_submit_orders", contract["forbidden_actions"])
        self.assertIn(
            "run_cand022_shadow_only_exception_apply_and_verify.py",
            contract["preferred_guarded_apply_and_verify_commands"]["dry_run"],
        )
        self.assertIn("--execute", contract["preferred_guarded_apply_and_verify_commands"]["execute"])
        self.assertIn(
            "--i-confirm-apply-shadow-only-exception",
            contract["preferred_guarded_apply_and_verify_commands"]["execute"],
        )
        self.assertEqual(
            contract["confirm_flag_required_for_real_apply"],
            "--i-confirm-apply-shadow-only-exception",
        )
        self.assertTrue(contract["real_apply_requires_execute_flag"])
        self.assertTrue(contract["low_level_apply_script_is_not_operator_surface"])
        self.assertEqual(contract["safety"], contract_mod.SAFETY)
        self.assertFalse(contract["safety"]["paper_enabled"])
        self.assertFalse(contract["safety"]["broker_submit_allowed"])
        self.assertEqual(contract["safety"]["pretrade_firewall_default_decision"], "BLOCK")

    def test_contract_blocks_when_operator_choice_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            operator_packet = root / "operator_packet.json"
            tiny_audit = root / "tiny.json"
            operator_packet.write_text(
                json.dumps(
                    {
                        "decision_groups": [
                            {
                                "group_id": "kis_pit_survivorship_policy",
                                "operator_choices": [{"choice_id": "data_upgrade_required"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            tiny_audit.write_text(json.dumps({"completion_decision": "NOT_COMPLETE"}), encoding="utf-8")

            contract = contract_mod.build_contract(
                "2026-05-14T06:00:00+09:00",
                operator_packet_path=operator_packet,
                tiny_live_audit_path=tiny_audit,
                pit_audit_path=root / "missing_pit.json",
                shadow_readiness_path=root / "missing_shadow.json",
            )

        self.assertEqual(contract["status"], "BLOCK_SHADOW_EXCEPTION_CONTRACT_INPUTS")
        self.assertIn("shadow_only_exception_choice_missing", contract["blockers"])
        self.assertFalse(contract["auto_apply_allowed"])

    def test_markdown_surfaces_non_approval_and_forbidden_actions(self) -> None:
        contract = contract_mod.build_contract("2026-05-14T06:00:00+09:00")
        md = contract_mod.render_md(contract)

        self.assertIn("This file is approval: `false`", md)
        self.assertIn("Auto-apply allowed: `false`", md)
        self.assertIn("Contract changes allowed by this file: `false`", md)
        self.assertIn("APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY", md)
        self.assertIn("run_cand022_shadow_only_exception_apply_and_verify.py", md)
        self.assertIn("--execute --i-confirm-apply-shadow-only-exception", md)
        self.assertIn("Low-level apply script is not the operator surface: `true`", md)
        self.assertIn("do_not_create_order_intent", md)
        self.assertIn("do_not_enable_paper", md)
        self.assertIn("do_not_enable_live", md)
        self.assertIn("do_not_enable_broker_submit", md)
        self.assertIn('"pretrade_firewall_default_decision": "BLOCK"', md)


if __name__ == "__main__":
    unittest.main()
