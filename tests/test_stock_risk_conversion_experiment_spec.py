from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_risk_conversion_experiment_spec.py")
SPEC = importlib.util.spec_from_file_location("build_stock_risk_conversion_experiment_spec", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)


class StockRiskConversionExperimentSpecTests(unittest.TestCase):
    def test_build_spec_freezes_sizing_overlay_without_order_paths(self) -> None:
        report = spec.build_spec(
            {
                "gatekeeper_action_packet": {
                    "risk_conversion_targets": [
                        {
                            "candidate_id": "stock_aggressive",
                            "lane": "kis_etfs",
                            "cagr": 0.706,
                            "mdd": -0.306,
                            "sharpe": 1.74,
                            "required_mdd_reduction_to_20pct": 0.106,
                            "fixed_exposure_recipe": {
                                "recommended_fixed_exposure_cap": 0.65,
                                "target_mdd_abs": 0.20,
                                "estimated_capped_cagr": 0.459,
                                "estimated_capped_mdd": -0.199,
                                "estimated_return_retention": 0.65,
                            },
                        }
                    ]
                }
            }
        )

        self.assertEqual(report["status"], "READY_FOR_CONVERSION_BACKTEST")
        self.assertEqual(report["frozen_scope"]["allowed_change"], "position_sizing_overlay_only")
        self.assertFalse(report["frozen_scope"]["signal_logic_change_allowed"])
        self.assertFalse(report["frozen_scope"]["order_paths_allowed"])
        self.assertFalse(report["frozen_scope"]["broker_submit_allowed"])
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertEqual(report["safety"]["real_orders"], 0)
        self.assertEqual(report["sizing_overlay"]["recommended_fixed_exposure_cap"], 0.65)

    def test_build_spec_reports_no_target_cleanly(self) -> None:
        report = spec.build_spec({"gatekeeper_action_packet": {"risk_conversion_targets": []}})

        self.assertEqual(report["status"], "NO_TARGET")
        self.assertEqual(report["safety"]["real_orders"], 0)
        self.assertFalse(report["safety"]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
