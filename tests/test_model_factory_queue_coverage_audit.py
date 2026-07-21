from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_model_factory_queue_coverage_audit.py")
SPEC = importlib.util.spec_from_file_location("build_model_factory_queue_coverage_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class ModelFactoryQueueCoverageAuditTests(unittest.TestCase):
    def test_passes_when_all_ready_decisions_have_safe_queue_items(self) -> None:
        report = audit.build_audit(
            {
                "ready_decisions": [
                    {
                        "decision_id": "paper_smoke_review",
                        "candidate_id": "small_account_growth_paper",
                        "ready_for_human_review": True,
                        "priority_score": 100,
                    },
                    {
                        "decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                        "candidate_id": "pola_entrysource_029",
                        "ready_for_human_review": True,
                        "priority_score": 84,
                    },
                ]
            },
            {
                "queue": [
                    {
                        "experiment_id": "paper",
                        "source_decision_id": "paper_smoke_review",
                        "frozen_scope": {"scope": "review_only_no_paper_activation_no_order_paths"},
                        "no_order_assertions": dict(audit.NO_ORDER_ASSERTIONS),
                    },
                    {
                        "experiment_id": "entrysource",
                        "source_decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                        "frozen_scope": {"scope": "entry_source_rebuild_evidence_review_only_no_order_paths"},
                        "no_order_assertions": dict(audit.NO_ORDER_ASSERTIONS),
                    },
                ]
            },
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["summary"]["ready_decision_count"], 2)
        self.assertEqual(report["summary"]["covered_ready_decision_count"], 2)
        self.assertEqual(report["summary"]["missing_ready_decision_count"], 0)
        self.assertEqual(report["missing_ready_decision_ids"], [])
        entry = next(
            row
            for row in report["coverage_rows"]
            if row["decision_id"] == "bithumb_non_orca_entry_source_rebuild_review"
        )
        self.assertTrue(entry["covered"])
        self.assertEqual(entry["queue_scopes"], ["entry_source_rebuild_evidence_review_only_no_order_paths"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_on_missing_ready_decision(self) -> None:
        report = audit.build_audit(
            {
                "ready_decisions": [
                    {
                        "decision_id": "bithumb_current_actionable_dependency_relief_review",
                        "ready_for_human_review": True,
                    }
                ]
            },
            {"queue": []},
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(
            report["missing_ready_decision_ids"],
            ["bithumb_current_actionable_dependency_relief_review"],
        )

    def test_blocks_on_unsafe_queue_item(self) -> None:
        unsafe_assertions = dict(audit.NO_ORDER_ASSERTIONS)
        unsafe_assertions["broker_submit_allowed_by_this_report"] = True

        report = audit.build_audit(
            {
                "ready_decisions": [
                    {
                        "decision_id": "paper_smoke_review",
                        "ready_for_human_review": True,
                    }
                ]
            },
            {
                "queue": [
                    {
                        "experiment_id": "paper",
                        "source_decision_id": "paper_smoke_review",
                        "no_order_assertions": unsafe_assertions,
                    }
                ]
            },
        )

        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["unsafe_queue_experiment_ids"], ["paper"])

    def test_allows_multiple_stock_conversion_children(self) -> None:
        report = audit.build_audit(
            {
                "ready_decisions": [
                    {
                        "decision_id": "stock_conversion_review",
                        "ready_for_human_review": True,
                    }
                ]
            },
            {
                "queue": [
                    {
                        "experiment_id": "stock_review",
                        "source_decision_id": "stock_conversion_review",
                        "no_order_assertions": dict(audit.NO_ORDER_ASSERTIONS),
                    },
                    {
                        "experiment_id": "stock_child",
                        "source_decision_id": "stock_conversion_review",
                        "no_order_assertions": dict(audit.NO_ORDER_ASSERTIONS),
                    },
                ]
            },
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["unexpected_duplicate_source_decisions"], {})


if __name__ == "__main__":
    unittest.main()
