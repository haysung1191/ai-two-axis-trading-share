from __future__ import annotations

import importlib.util
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\record_paper_approval.py")
SPEC = importlib.util.spec_from_file_location("record_paper_approval", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
approval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(approval)


class RecordPaperApprovalTests(unittest.TestCase):
    def test_accepts_existing_paper_only_broker_scope_without_enabling_live(self) -> None:
        def fake_read_json(path: Path) -> dict:
            if path == approval.ACTIVATION_PACKET:
                return {
                    "profile": "small_account_growth_paper",
                    "status": "ready_for_explicit_paper_activation",
                    "blockers": [],
                    "does_enable_trading": False,
                }
            if path == approval.PAPER_AUTOTRADE:
                return {
                    "status": "pass",
                    "real_orders": 0,
                    "private_submit_used": False,
                    "broker_submit_allowed": True,
                    "broker_submit_scope": "paper_only",
                    "simulated_orders": [{"action": "HOLD", "target_weight": 0.0}],
                }
            if path == approval.PAPER_SIM:
                return {"status": "pass"}
            if path == approval.SHADOW_CONTROL:
                return {"contract_count": 1, "planned_count": 1}
            if path == approval.KILL_SWITCH:
                return {"live_enabled": False}
            return {}

        with patch.object(approval, "read_json", side_effect=fake_read_json), patch.object(
            approval, "GLOBAL_DISABLE", SimpleNamespace(exists=lambda: True)
        ):
            record = approval.build_record("PAPER APPROVE small_account_growth_paper")

        self.assertTrue(record["approval_valid"])
        self.assertTrue(record["paper_approved"])
        self.assertEqual(record["blockers"], [])
        self.assertTrue(record["safety"]["broker_submit_allowed"])
        self.assertEqual(record["safety"]["broker_submit_scope"], "paper_only")
        self.assertFalse(record["does_enable_live"])
        self.assertFalse(record["does_enable_broker_submit"])
        self.assertEqual(record["safety"]["real_orders"], 0)

    def test_blocks_broker_scope_that_is_not_paper_only(self) -> None:
        def fake_read_json(path: Path) -> dict:
            if path == approval.ACTIVATION_PACKET:
                return {
                    "profile": "small_account_growth_paper",
                    "status": "ready_for_explicit_paper_activation",
                    "blockers": [],
                    "does_enable_trading": False,
                }
            if path == approval.PAPER_AUTOTRADE:
                return {
                    "status": "pass",
                    "real_orders": 0,
                    "private_submit_used": False,
                    "broker_submit_allowed": True,
                    "broker_submit_scope": "live",
                    "simulated_orders": [{"action": "HOLD", "target_weight": 0.0}],
                }
            if path == approval.PAPER_SIM:
                return {"status": "pass"}
            if path == approval.SHADOW_CONTROL:
                return {"contract_count": 1, "planned_count": 1}
            if path == approval.KILL_SWITCH:
                return {"live_enabled": False}
            return {}

        with patch.object(approval, "read_json", side_effect=fake_read_json), patch.object(
            approval, "GLOBAL_DISABLE", SimpleNamespace(exists=lambda: True)
        ):
            record = approval.build_record("PAPER APPROVE small_account_growth_paper")

        self.assertFalse(record["approval_valid"])
        self.assertIn("paper_autotrade_broker_submit_scope_not_paper_only", record["blockers"])


if __name__ == "__main__":
    unittest.main()
