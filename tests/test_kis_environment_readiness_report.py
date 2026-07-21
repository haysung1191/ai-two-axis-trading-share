from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_stock_live_preflight_packet as stock_preflight


MODULE_PATH = Path(r"C:\AI\build_kis_environment_readiness_report.py")
SPEC = importlib.util.spec_from_file_location("build_kis_environment_readiness_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
kis_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kis_report)


class KisEnvironmentReadinessReportTests(unittest.TestCase):
    def test_report_blocks_without_secret_values_and_order_paths_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(os.environ, {"KIS_APP_KEY": "app-key"}, clear=True),
                patch.object(stock_preflight, "LOCAL_KIS_ENV_FILE", Path(tmp) / ".env"),
            ):
                report = kis_report.build_report()

        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["secret_values_inspected"])
        self.assertFalse(report["secret_values_written"])
        self.assertIn("app_secret", report["missing_requirements"])
        self.assertIn("account_no", report["missing_requirements"])
        self.assertIn("account_product_code", report["missing_requirements"])
        self.assertFalse(report["safety"]["does_call_kis_api"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["safety"]["private_submit_allowed_by_this_report"])
        self.assertFalse(report["safety"]["real_orders_allowed_by_this_report"])

    def test_report_is_ready_for_recheck_when_all_aliases_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "KIS_APP_KEY": "app-key",
                        "KIS_APP_SECRET": "app-secret",
                        "KIS_ACCOUNT_NO": "12345678",
                        "KIS_ACCOUNT_PRODUCT_CODE": "01",
                    },
                    clear=True,
                ),
                patch.object(stock_preflight, "LOCAL_KIS_ENV_FILE", Path(tmp) / ".env"),
            ):
                report = kis_report.build_report()

        self.assertEqual(report["status"], "READY_FOR_STOCK_PREFLIGHT_RECHECK")
        self.assertEqual(report["missing_requirements"], [])
        self.assertEqual(report["checks"]["account_no"]["present_env_names"], ["KIS_ACCOUNT_NO"])
        self.assertEqual(
            report["checks"]["account_product_code"]["present_env_names"],
            ["KIS_ACCOUNT_PRODUCT_CODE"],
        )


if __name__ == "__main__":
    unittest.main()
