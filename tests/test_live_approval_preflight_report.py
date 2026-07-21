from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_live_approval_preflight_report.py")
SPEC = importlib.util.spec_from_file_location("build_live_approval_preflight_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class LiveApprovalPreflightReportTests(unittest.TestCase):
    def test_existing_approval_caps_round_trip_to_approval_text(self) -> None:
        report = {
            "approval_text_supplied": True,
            "approval_caps": {
                "max_krw": 100000.0,
                "max_daily_loss_krw": 10000.0,
                "max_total_loss_krw": 30000.0,
            },
        }

        self.assertEqual(
            preflight.approval_text_from_existing_report(report),
            "LIVE APPROVE 100000 10000 30000",
        )

    def test_existing_approval_caps_are_not_reused_when_not_explicitly_supplied(self) -> None:
        report = {
            "approval_text_supplied": False,
            "approval_caps": {
                "max_krw": 100000.0,
                "max_daily_loss_krw": 10000.0,
                "max_total_loss_krw": 30000.0,
            },
        }

        self.assertIsNone(preflight.approval_text_from_existing_report(report))

    def test_existing_approval_caps_are_not_reused_when_incomplete(self) -> None:
        report = {
            "approval_text_supplied": True,
            "approval_caps": {
                "max_krw": 100000.0,
                "max_daily_loss_krw": 10000.0,
            },
        }

        self.assertIsNone(preflight.approval_text_from_existing_report(report))

    def test_structured_live_approval_with_axis_caps_parses(self) -> None:
        caps, blockers = preflight.parse_approval(
            "\n".join(
                [
                    "LIVE APPROVE small_account_growth_paper",
                    "TOTAL_CAP_KRW=200000",
                    "CRYPTO_CAP_KRW=100000",
                    "STOCK_CAP_KRW=100000",
                    "MAX_ORDER_KRW=10000",
                    "DAILY_LOSS_STOP_KRW=10000",
                ]
            )
        )

        self.assertEqual(blockers, [])
        self.assertEqual(caps["profile"], "small_account_growth_paper")
        self.assertEqual(caps["max_krw"], 200000.0)
        self.assertEqual(caps["crypto_cap_krw"], 100000.0)
        self.assertEqual(caps["stock_cap_krw"], 100000.0)
        self.assertEqual(caps["max_order_krw"], 10000.0)
        self.assertEqual(caps["max_daily_loss_krw"], 10000.0)
        self.assertEqual(caps["max_total_loss_krw"], 10000.0)

    def test_structured_axis_caps_cannot_exceed_total_cap(self) -> None:
        _, blockers = preflight.parse_approval(
            "\n".join(
                [
                    "LIVE APPROVE small_account_growth_paper",
                    "TOTAL_CAP_KRW=100000",
                    "CRYPTO_CAP_KRW=100000",
                    "STOCK_CAP_KRW=100000",
                    "MAX_ORDER_KRW=10000",
                    "DAILY_LOSS_STOP_KRW=10000",
                ]
            )
        )

        self.assertIn("axis_caps_exceed_total_cap", blockers)


if __name__ == "__main__":
    unittest.main()
