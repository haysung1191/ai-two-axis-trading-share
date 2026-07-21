from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_start_here_after_reboot_validator.py")
SPEC = importlib.util.spec_from_file_location("build_start_here_after_reboot_validator", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class StartHereAfterRebootValidatorTests(unittest.TestCase):
    def test_validator_passes_when_start_file_uses_current_latest_sources(self) -> None:
        start_text = "\n".join(
            [
                str(validator.DASHBOARD_JSON),
                str(validator.HEALTH_MD),
                str(validator.LIMITED_LIVE_POLICY_JSON),
                str(validator.BROKER_POLICY_JSON),
                str(validator.BITHUMB_LATEST_JSON),
                str(validator.KIS_OPERATION_JSON),
                str(validator.KIS_BRIDGE_JSON),
                str(validator.MODEL_FACTORY_JSON),
                str(validator.DIRECT_DEVELOPMENT_JSON),
                str(validator.MODEL_INVENTORY_JSON),
                "Do a read-only state check. Do not stop live loops.",
                "Do not start by reading old",
                "daily_close_presence",
                "PIT/survivorship-free KIS documents may still exist on disk as historical artifacts",
                "Older stage reports may still mention shadow/paper blockers. Treat those as stale",
            ]
        )
        report = validator.build_report(start_text)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["blockers"], [])

    def test_validator_fails_on_missing_latest_source_or_stale_blocker_phrase(self) -> None:
        report = validator.build_report(
            "\n".join(
                [
                    "Do a read-only state check. Do not stop live loops.",
                    "KIS execution as blocked until historical PIT/survivorship-free data is verified",
                ]
            )
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn(f"missing_path:{validator.DASHBOARD_JSON}", report["blockers"])
        self.assertIn(
            "stale_current_blocker_phrase_present:KIS execution as blocked until historical PIT/survivorship-free data is verified",
            report["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
