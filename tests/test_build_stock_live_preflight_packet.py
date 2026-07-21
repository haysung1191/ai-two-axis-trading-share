from __future__ import annotations

import importlib.util
import os
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_stock_live_preflight_packet.py")
SPEC = importlib.util.spec_from_file_location("build_stock_live_preflight_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
stock_preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stock_preflight)


class StockLivePreflightPacketTests(unittest.TestCase):
    def write_plan(self, path: Path, notional: float) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "Market",
                    "Symbol",
                    "ResolvedSymbol",
                    "ExecutionSide",
                    "Name",
                    "DeltaNotional",
                    "Status",
                    "Reason",
                    "ResolvedExchange",
                    "ResolvedPrice",
                    "FXRate",
                    "Quantity",
                    "EstimatedOrderNotionalKRW",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "Market": "US",
                    "Symbol": "DOW",
                    "ResolvedSymbol": "DOW",
                    "ExecutionSide": "BUY",
                    "Name": "Dow",
                    "DeltaNotional": "100000",
                    "Status": "PLANNED",
                    "Reason": "",
                    "ResolvedExchange": "NYSE",
                    "ResolvedPrice": "40.895",
                    "FXRate": "1469.9",
                    "Quantity": "1",
                    "EstimatedOrderNotionalKRW": str(notional),
                }
            )

    def test_env_presence_accepts_kis_config_account_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "KIS_APP_KEY": "app-key",
                        "KIS_APP_SECRET": "app-secret",
                        "KIS_CANO": "12345678",
                        "KIS_ACNT_PRDT_CD": "01",
                    },
                    clear=True,
                ),
                patch.object(stock_preflight, "LOCAL_KIS_ENV_FILE", Path(tmp) / ".env"),
            ):
                env = stock_preflight.env_presence()

        self.assertEqual(stock_preflight.missing_env_requirements(env), [])
        self.assertTrue(env["account_no"]["present"])
        self.assertEqual(env["account_no"]["present_env_names"], ["KIS_CANO"])
        self.assertTrue(env["account_product_code"]["present"])
        self.assertEqual(env["account_product_code"]["present_env_names"], ["KIS_ACNT_PRDT_CD"])

    def test_env_presence_accepts_legacy_account_aliases(self) -> None:
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
                env = stock_preflight.env_presence()

        self.assertEqual(stock_preflight.missing_env_requirements(env), [])
        self.assertEqual(env["account_no"]["present_env_names"], ["KIS_ACCOUNT_NO"])
        self.assertEqual(env["account_product_code"]["present_env_names"], ["KIS_ACCOUNT_PRODUCT_CODE"])

    def test_build_packet_reports_missing_requirements_not_secret_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(os.environ, {"KIS_APP_KEY": "app-key"}, clear=True),
                patch.object(stock_preflight, "LOCAL_KIS_ENV_FILE", Path(tmp) / ".env"),
            ):
                packet = stock_preflight.build_packet(
                    {"status": "ready_for_human_live_review", "approval_caps": {"max_krw": 100000}},
                    {"status": "READY_FOR_NEXT_MARKET_REVIEW", "candidates": [{"account_weight_from_portfolio_review": 0.1}]},
                    {},
                    {"status": "PASS"},
                    {"live_enabled": False},
                )

        self.assertIn("KIS_ENV_MISSING", packet["blockers"])
        self.assertIn("app_secret", packet["kis_environment"]["missing_requirements"])
        self.assertIn("account_no", packet["kis_environment"]["missing_requirements"])
        self.assertIn("account_product_code", packet["kis_environment"]["missing_requirements"])
        self.assertFalse(packet["safety"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(packet["safety"]["real_orders_allowed_by_this_report"])

    def test_stock_plan_excludes_order_above_max_order_without_submit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.csv"
            latest_path = tmp_path / "latest.json"
            self.write_plan(plan_path, 60111.56)
            latest_path.write_text(json.dumps({"plan_path": str(plan_path)}), encoding="utf-8")
            with patch.object(stock_preflight, "STOCK_LIVE_LATEST_INDEX", latest_path):
                check = stock_preflight.stock_live_execution_plan_check(max_order_krw=10000, stock_cap_krw=100000)

        self.assertEqual(check["planned_count"], 1)
        self.assertEqual(check["cap_compliant_order_count"], 0)
        self.assertEqual(check["excluded_order_count"], 1)
        self.assertIn("STOCK_LIVE_EXECUTION_PLAN_HAS_NO_CAP_COMPLIANT_ORDERS", check["blockers"])
        self.assertEqual(check["excluded_orders"][0]["exclude_reason"], "MIN_LOT_NOTIONAL_EXCEEDS_MAX_ORDER_KRW")

    def test_stock_plan_accepts_order_below_max_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.csv"
            latest_path = tmp_path / "latest.json"
            self.write_plan(plan_path, 9000.0)
            latest_path.write_text(json.dumps({"plan_path": str(plan_path)}), encoding="utf-8")
            with patch.object(stock_preflight, "STOCK_LIVE_LATEST_INDEX", latest_path):
                check = stock_preflight.stock_live_execution_plan_check(max_order_krw=10000, stock_cap_krw=100000)

        self.assertEqual(check["planned_count"], 1)
        self.assertEqual(check["cap_compliant_order_count"], 1)
        self.assertEqual(check["excluded_order_count"], 0)
        self.assertEqual(check["blockers"], [])

    def test_missing_max_order_blocks_stock_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.csv"
            latest_path = tmp_path / "latest.json"
            self.write_plan(plan_path, 60111.56)
            latest_path.write_text(json.dumps({"plan_path": str(plan_path)}), encoding="utf-8")
            with patch.object(stock_preflight, "STOCK_LIVE_LATEST_INDEX", latest_path):
                check = stock_preflight.stock_live_execution_plan_check(max_order_krw=0, stock_cap_krw=100000)

        self.assertEqual(check["planned_count"], 1)
        self.assertEqual(check["cap_compliant_order_count"], 0)
        self.assertEqual(check["excluded_order_count"], 1)
        self.assertIn("MAX_ORDER_KRW_MISSING", check["blockers"])
        self.assertIn("STOCK_LIVE_EXECUTION_PLAN_HAS_NO_CAP_COMPLIANT_ORDERS", check["blockers"])
        self.assertEqual(check["excluded_orders"][0]["exclude_reason"], "MAX_ORDER_KRW_MISSING")


if __name__ == "__main__":
    unittest.main()
