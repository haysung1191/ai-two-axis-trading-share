from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_environment_operator_handoff.py")
SPEC = importlib.util.spec_from_file_location("build_kis_environment_operator_handoff", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class KisEnvironmentOperatorHandoffTests(unittest.TestCase):
    def test_handoff_uses_placeholders_and_never_secret_values(self) -> None:
        report = handoff.build_handoff(
            {"missing_requirements": ["app_key", "app_secret", "account_no", "account_product_code"]},
            {"status": "BLOCKED", "blockers": ["KIS_ENV_MISSING"]},
        )

        self.assertEqual(report["status"], "WAITING_FOR_OPERATOR_ENV_VALUES")
        self.assertFalse(report["safety"]["secret_values_included"])
        self.assertFalse(report["safety"]["secret_values_written"])
        self.assertFalse(report["safety"]["does_set_environment"])
        self.assertFalse(report["safety"]["does_call_kis_api"])
        self.assertTrue(report["operator_setup_template"].endswith("kis_environment_operator_setup_template.ps1"))
        self.assertIn("$env:KIS_APP_KEY = '<KIS_APP_KEY>'", report["powershell_setup_placeholders"])
        self.assertIn("$env:KIS_ACCOUNT_NO = '<KIS_ACCOUNT_NO>'", report["powershell_setup_placeholders"])
        self.assertIn("Set-Location -LiteralPath C:\\AI", report["verification_commands_after_operator_sets_values"])
        self.assertIn("python .\\build_stock_live_preflight_packet.py", report["verification_commands_after_operator_sets_values"])
        self.assertIn(
            "powershell -ExecutionPolicy Bypass -File C:\\AI\\run_goal_model_factory_unblock_recheck.ps1 -IncludeKisVerification -Execute",
            report["verification_commands_after_operator_sets_values"],
        )

        template = handoff.render_setup_template(report)
        self.assertIn("$env:KIS_APP_SECRET = '<KIS_APP_SECRET>'", template)
        self.assertIn("Set-Location -LiteralPath C:\\AI", template)
        self.assertIn("run_goal_model_factory_unblock_recheck.ps1 -IncludeKisVerification -Execute", template)
        self.assertIn("Do not paste real secret values into chat.", template)
        self.assertIn("does not enable paper, live, broker submit", template)
        self.assertNotIn("real_orders = 1", template)

    def test_handoff_ready_when_no_missing_requirements(self) -> None:
        report = handoff.build_handoff({"missing_requirements": []}, {"status": "BLOCKED"})

        self.assertEqual(report["status"], "READY_FOR_PREFLIGHT_RECHECK")
        self.assertEqual(report["powershell_setup_placeholders"], [])
        self.assertIn("No missing KIS environment requirements", handoff.render_setup_template(report))


if __name__ == "__main__":
    unittest.main()
