from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_non_orca_family_pass_fold_repair_spec.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_non_orca_family_pass_fold_repair_spec", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
spec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spec)


class BithumbNonOrcaFamilyPassFoldRepairSpecTests(unittest.TestCase):
    def test_builds_research_only_spec_from_queue_and_failure_evidence(self) -> None:
        queue = {
            "status": "PASS",
            "queue": [
                {
                    "experiment_id": "bithumb_non_orca_family_pass_fold_repair__orca",
                    "source_decision_id": "bithumb_current_actionable_family_diversity_failure_review",
                    "queue_rank": 13,
                    "status": "READY",
                    "no_order_assertions": dict(spec.NO_ORDER_ASSERTIONS),
                }
            ],
        }
        family = {
            "status": "FAMILY_DIVERSITY_ITERATE",
            "candidate_results": [
                {
                    "candidate_id": "pola",
                    "market": "KRW-POLA",
                    "timeframe": "1d",
                    "parameters": {
                        "hold_bars": 7,
                        "stop_loss": 0.12,
                        "take_profit": 0.35,
                        "lookback_bars": 3,
                    },
                    "folds": [
                        {"fold": 1, "pass": False},
                        {"fold": 2, "pass": False},
                        {"fold": 3, "pass": True},
                    ],
                }
            ],
        }
        failure = {
            "status": "FAMILY_DIVERSITY_FAILURE_REVIEW_READY",
            "dominant_failure_dimension": "enough_pass_folds",
            "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
            "candidate_gaps": [
                {
                    "candidate_id": "pola",
                    "market": "KRW-POLA",
                    "failure_dimensions": ["enough_pass_folds", "enough_positive_folds"],
                }
            ],
        }

        report = spec.build_spec(queue, family, failure)

        self.assertEqual(report["status"], "READY_FOR_RESEARCH_SPEC_REVIEW")
        self.assertEqual(report["repair_target_count"], 1)
        self.assertEqual(report["repair_targets"][0]["failed_fold_indices"], [1, 2])
        self.assertEqual(report["repair_targets"][0]["parameter_grid"]["hold_bars"], [4, 5, 6])
        self.assertEqual(report["repair_targets"][0]["parameter_grid"]["stop_loss"], [0.06, 0.08])
        self.assertEqual(report["repair_targets"][0]["parameter_grid"]["take_profit"], [0.2, 0.25])
        self.assertEqual(
            report["frozen_scope"]["scope"],
            "non_orca_family_pass_fold_repair_research_only_no_order_paths",
        )
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_unsafe_queue_item(self) -> None:
        queue = {
            "status": "PASS",
            "queue": [
                {
                    "source_decision_id": "bithumb_current_actionable_family_diversity_failure_review",
                    "status": "READY",
                    "no_order_assertions": {
                        **spec.NO_ORDER_ASSERTIONS,
                        "broker_submit_allowed_by_this_report": True,
                    },
                }
            ],
        }
        report = spec.build_spec(
            queue,
            {"status": "FAMILY_DIVERSITY_ITERATE", "candidate_results": []},
            {"status": "FAMILY_DIVERSITY_FAILURE_REVIEW_READY", "candidate_gaps": []},
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("QUEUE_ITEM_ORDER_PATH_NOT_SAFE", report["blockers"])
        self.assertFalse(report["no_order_assertions"]["live_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
