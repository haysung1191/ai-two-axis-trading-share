from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_krx_data_marketplace_access_probe.py")
SPEC = importlib.util.spec_from_file_location("build_krx_data_marketplace_access_probe", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KrxDataMarketplaceAccessProbeTests(unittest.TestCase):
    def test_logout_response_blocks_unattended_access(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            probe={"ok": True, "http_status": 200, "body_prefix": "LOGOUT"},
        )

        self.assertEqual(report["status"], "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS")
        self.assertIn("krx_generate_otp_requires_login_or_session", report["blockers"])
        self.assertFalse(report["operation_ready"])
        self.assertFalse(report["safety"]["live_enabled"])

    def test_error_response_blocks_unattended_access(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            probe={"ok": False, "error_type": "TimeoutError", "error": "timed out"},
        )

        self.assertEqual(report["status"], "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS")
        self.assertIn("krx_generate_otp_request_failed", report["blockers"])

    def test_otp_like_response_is_review_required_not_auto_import(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            probe={"ok": True, "http_status": 200, "body_prefix": "a" * 40},
        )

        self.assertEqual(report["status"], "KRX_GENERATE_OTP_ACCESSIBLE_REVIEW_REQUIRED")
        self.assertTrue(report["operation_ready"])
        self.assertIn("does_not_download_krx_csv", report["non_goals"])


if __name__ == "__main__":
    unittest.main()
