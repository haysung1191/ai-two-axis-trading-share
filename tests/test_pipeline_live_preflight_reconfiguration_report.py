from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_pipeline_live_preflight_reconfiguration_report.py")
SPEC = importlib.util.spec_from_file_location("build_pipeline_live_preflight_reconfiguration_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
reconfig = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconfig)


class PipelineLivePreflightReconfigurationReportTests(unittest.TestCase):
    def test_report_carries_kis_environment_readiness_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            live = base / "live.json"
            crypto = base / "crypto.json"
            crypto_nonzero = base / "crypto_nonzero.json"
            kis = base / "kis.json"
            stock = base / "stock.json"
            risk = base / "risk.json"
            kill = base / "kill.json"
            live.write_text(json.dumps({"status": "ready_for_human_live_review"}), encoding="utf-8")
            crypto.write_text(json.dumps({"blockers": ["CURRENT_CRYPTO_SIGNAL_HAS_NO_NONZERO_ORDER"]}), encoding="utf-8")
            crypto_nonzero.write_text(
                json.dumps(
                    {
                        "status": "BLOCKED",
                        "blockers": ["CURRENT_CRYPTO_TARGET_WEIGHT_ZERO"],
                        "current_order_candidate": {"action": "HOLD", "target_weight": 0.0, "delta_weight": 0.0},
                    }
                ),
                encoding="utf-8",
            )
            kis.write_text(
                json.dumps(
                    {
                        "status": "BLOCKED",
                        "missing_requirements": ["app_secret", "account_no"],
                        "secret_values_inspected": False,
                        "secret_values_written": False,
                    }
                ),
                encoding="utf-8",
            )
            stock.write_text(json.dumps({"blockers": ["KIS_ENV_MISSING"]}), encoding="utf-8")
            risk.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            kill.write_text(json.dumps({"live_enabled": False, "paper_enabled": True}), encoding="utf-8")

            originals = {
                "LIVE_PREFLIGHT": reconfig.LIVE_PREFLIGHT,
                "CRYPTO_PREFLIGHT": reconfig.CRYPTO_PREFLIGHT,
                "CRYPTO_NONZERO_READINESS": reconfig.CRYPTO_NONZERO_READINESS,
                "KIS_ENV_READINESS": reconfig.KIS_ENV_READINESS,
                "STOCK_PREFLIGHT": reconfig.STOCK_PREFLIGHT,
                "RISK_GUARD": reconfig.RISK_GUARD,
                "KILL_SWITCH": reconfig.KILL_SWITCH,
            }
            reconfig.LIVE_PREFLIGHT = live
            reconfig.CRYPTO_PREFLIGHT = crypto
            reconfig.CRYPTO_NONZERO_READINESS = crypto_nonzero
            reconfig.KIS_ENV_READINESS = kis
            reconfig.STOCK_PREFLIGHT = stock
            reconfig.RISK_GUARD = risk
            reconfig.KILL_SWITCH = kill
            try:
                report = reconfig.build_report()
                rendered = json.dumps(report, ensure_ascii=False) + reconfig.render_markdown(report)
            finally:
                for name, value in originals.items():
                    setattr(reconfig, name, value)

        self.assertEqual(report["status"], "RECONFIGURED_WITH_BLOCKERS")
        self.assertEqual(report["current_blockers"]["crypto_nonzero_order"], ["CURRENT_CRYPTO_TARGET_WEIGHT_ZERO"])
        self.assertEqual(report["crypto_nonzero_order_readiness"]["status"], "BLOCKED")
        self.assertEqual(report["current_blockers"]["kis_environment"], ["app_secret", "account_no"])
        self.assertEqual(report["kis_environment_readiness"]["status"], "BLOCKED")
        self.assertFalse(report["kis_environment_readiness"]["secret_values_inspected"])
        self.assertFalse(report["kis_environment_readiness"]["secret_values_written"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertEqual(report["safety"]["real_orders"], 0)
        self.assertNotIn("app-key", rendered)
        self.assertNotIn("app-secret", rendered)


if __name__ == "__main__":
    unittest.main()
