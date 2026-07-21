from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_stock_portfolio_sleeve_constraint_envelope_review.py")
SPEC = importlib.util.spec_from_file_location("build_stock_portfolio_sleeve_constraint_envelope_review", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StockPortfolioSleeveConstraintEnvelopeReviewTests(unittest.TestCase):
    def safe_assertions(self) -> dict[str, bool]:
        return {
            "promotion_allowed_by_this_report": False,
            "paper_enabled_by_this_report": False,
            "live_allowed_by_this_report": False,
            "broker_submit_allowed_by_this_report": False,
            "private_submit_allowed_by_this_report": False,
            "real_orders_allowed_by_this_report": False,
        }

    def ready_packet(self, status: str, **extra: object) -> dict:
        packet = {
            "status": status,
            "ready_for_gatekeeper_review": True,
            "counts_as_paper_or_live_evidence": False,
            "no_order_assertions": self.safe_assertions(),
        }
        packet.update(extra)
        return packet

    def packets(self) -> dict[str, dict]:
        repair_scenario = {
            "scenario_id": "repair_scenario",
            "estimated_sleeve_cagr": 0.36,
            "weighted_mdd_proxy": -0.19,
            "max_lane_weight": 0.8,
            "max_effective_component_exposure": 0.26,
            "residual_cash_weight": 0.2,
            "component_count": 2,
            "source_fragile": True,
            "repaired_viable": True,
        }
        return {
            "base": self.ready_packet(
                "PORTFOLIO_SLEEVE_REVIEW_READY",
                sleeve_policy={
                    "component_count": 5,
                    "max_lane_weight": 0.6,
                    "max_effective_component_exposure": 0.13,
                },
                sleeve_metrics={
                    "estimated_sleeve_cagr": 0.44,
                    "weighted_mdd_proxy": -0.19,
                },
            ),
            "pairwise_repair": self.ready_packet(
                "PORTFOLIO_SLEEVE_PAIRWISE_FRAGILITY_REPAIR_REVIEW_READY",
                scenarios=[dict(repair_scenario)],
            ),
            "tail_drop_repair": self.ready_packet(
                "PORTFOLIO_SLEEVE_TAIL_DROP_FRAGILITY_REPAIR_REVIEW_READY",
                scenarios=[dict(repair_scenario)],
            ),
            "ladder": self.ready_packet(
                "PORTFOLIO_SLEEVE_RESILIENCE_LADDER_REVIEW_READY",
                ladder_stage_count=7,
                ready_stage_count=7,
                repair_closure={"all_source_fragility_repaired": True},
            ),
        }

    def test_builds_constraint_envelope_without_order_paths(self) -> None:
        report = review.build_report(self.packets())

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_CONSTRAINT_ENVELOPE_REVIEW_READY")
        self.assertTrue(report["ready_for_gatekeeper_review"])
        self.assertEqual(report["scenario_count"], 3)
        self.assertEqual(report["constraint_pass_scenario_count"], 3)
        self.assertEqual(report["constraint_fail_scenario_count"], 0)
        self.assertLessEqual(report["max_observed_lane_weight"], 0.8)
        self.assertLessEqual(report["max_observed_component_effective_exposure"], 0.35)
        self.assertLessEqual(report["max_observed_residual_cash_weight"], 0.25)
        self.assertFalse(report["counts_as_paper_or_live_evidence"])
        self.assertFalse(report["no_order_assertions"]["broker_submit_allowed_by_this_report"])
        self.assertFalse(report["no_order_assertions"]["real_orders_allowed_by_this_report"])

    def test_blocks_constraint_breach(self) -> None:
        packets = self.packets()
        packets["tail_drop_repair"]["scenarios"][0]["max_lane_weight"] = 0.9

        report = review.build_report(packets)

        self.assertEqual(report["status"], "PORTFOLIO_SLEEVE_CONSTRAINT_ENVELOPE_REVIEW_BLOCKED")
        self.assertEqual(report["constraint_fail_scenario_count"], 1)
        self.assertIn("CONSTRAINT_ENVELOPE_SCENARIOS_FAILED", report["blockers"])
        self.assertFalse(report["ready_for_gatekeeper_review"])


if __name__ == "__main__":
    unittest.main()
