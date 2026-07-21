from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_non_orca_family_widened_repair_stop_condition_review.py")
SPEC = importlib.util.spec_from_file_location(
    "build_bithumb_non_orca_family_widened_repair_stop_condition_review",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
stop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stop)


class BithumbNonOrcaFamilyWidenedRepairStopConditionReviewTests(unittest.TestCase):
    def test_ready_when_full_widened_sweep_has_no_oos_or_robustness_pass(self) -> None:
        spec = {
            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": dict(stop.SAFE_ASSERTIONS),
        }
        sweep = {
            "status": "NON_ORCA_WIDENED_REPAIR_SWEEP_ITERATE",
            "repair_target_count": 2,
            "trial_count": 2,
            "evaluated_trial_count": 2,
            "oos_pass_trial_count": 0,
            "robustness_pass_trial_count": 0,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": dict(stop.SAFE_ASSERTIONS),
            "trial_results": [
                {"aggregate": {"pass_fold_count": 1, "positive_fold_count": 1, "worst_fold_mdd": -0.20, "total_trade_count": 9}},
                {"aggregate": {"pass_fold_count": 0, "positive_fold_count": 1, "worst_fold_mdd": -0.30, "total_trade_count": 10}},
            ],
        }

        report = stop.build_report(spec, sweep)

        self.assertEqual(report["status"], "NON_ORCA_WIDENED_REPAIR_STOP_CONDITION_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["recommended_branch_action"], "STOP_NON_ORCA_WIDENED_REPAIR_GRID")
        self.assertEqual(report["recommended_next_research_action"], "REBUILD_NON_ORCA_ENTRY_FAMILY_OR_SOURCE_DATA_EVIDENCE")
        self.assertEqual(report["dominant_failure_dimensions"][0]["dimension"], "enough_pass_folds")
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertEqual(report["no_order_assertions"], stop.SAFE_ASSERTIONS)

    def test_blocks_unsafe_widened_sweep(self) -> None:
        spec = {
            "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": dict(stop.SAFE_ASSERTIONS),
        }
        sweep = {
            "status": "NON_ORCA_WIDENED_REPAIR_SWEEP_ITERATE",
            "trial_count": 1,
            "evaluated_trial_count": 1,
            "oos_pass_trial_count": 0,
            "robustness_pass_trial_count": 0,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": {**stop.SAFE_ASSERTIONS, "broker_submit_allowed_by_this_report": True},
        }

        report = stop.build_report(spec, sweep)

        self.assertEqual(report["status"], "NON_ORCA_WIDENED_REPAIR_STOP_CONDITION_BLOCKED")
        self.assertIn("SOURCE_SWEEP_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
