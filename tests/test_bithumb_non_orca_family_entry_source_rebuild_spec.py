from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_non_orca_family_entry_source_rebuild_spec.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_non_orca_family_entry_source_rebuild_spec", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)


class BithumbNonOrcaFamilyEntrySourceRebuildSpecTests(unittest.TestCase):
    def test_builds_entry_source_rebuild_spec_without_order_paths(self) -> None:
        stop = {
            "status": "NON_ORCA_WIDENED_REPAIR_STOP_CONDITION_READY",
            "recommended_branch_action": "STOP_NON_ORCA_WIDENED_REPAIR_GRID",
            "recommended_next_research_action": "REBUILD_NON_ORCA_ENTRY_FAMILY_OR_SOURCE_DATA_EVIDENCE",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": dict(spec.SAFE_ASSERTIONS),
        }
        family = {
            "status": "FAMILY_DIVERSITY_ITERATE",
            "current_oos_market": "KRW-ORCA",
            "candidate_results": [
                {
                    "candidate_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "status": "OOS_CANDIDATE_ITERATE",
                    "parameters": {
                        "hold_bars": 7,
                        "round_trip_cost_rate": 0.002,
                        "stop_loss": 0.12,
                        "take_profit": 0.35,
                    },
                    "aggregate": {
                        "pass_fold_count": 1,
                        "positive_fold_count": 1,
                        "worst_fold_mdd": -0.2,
                        "total_trade_count": 11,
                    },
                }
            ],
        }

        report = spec.build_spec(stop, family)

        self.assertEqual(report["status"], "READY_FOR_RESEARCH_SPEC_REVIEW")
        self.assertEqual(report["rebuild_target_count"], 1)
        grid = report["rebuild_targets"][0]["rebuild_grid"]
        self.assertIn("range_breakout_retest", grid["entry_signal_family"])
        self.assertIn("hlc3", grid["price_source"])
        self.assertIn("volume_zscore", grid["confirmation_feature"])
        self.assertIn("recent_regime_365d", grid["data_window_policy"])
        self.assertIn("market", report["frozen_scope"]["fixed_parameters"])
        self.assertIn("order_execution_path", report["frozen_scope"]["forbidden_changes"])
        self.assertIn("market_universe", report["frozen_scope"]["forbidden_changes"])
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertEqual(report["no_order_assertions"], spec.SAFE_ASSERTIONS)

    def test_blocks_unsafe_stop_condition(self) -> None:
        stop = {
            "status": "NON_ORCA_WIDENED_REPAIR_STOP_CONDITION_READY",
            "recommended_next_research_action": "REBUILD_NON_ORCA_ENTRY_FAMILY_OR_SOURCE_DATA_EVIDENCE",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {**spec.SAFE_ASSERTIONS, "real_orders_allowed_by_this_report": True},
        }
        report = spec.build_spec(stop, {"status": "FAMILY_DIVERSITY_ITERATE", "candidate_results": []})

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("WIDENED_STOP_CONDITION_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
