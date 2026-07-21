from __future__ import annotations

import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_bithumb_current_actionable_nonzero_signal_scout.py")
SPEC = importlib.util.spec_from_file_location("build_bithumb_current_actionable_nonzero_signal_scout", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
scout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scout)


def candles(trigger: bool) -> list[dict]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    closes = [100.0, 100.0, 100.0, 104.0 if trigger else 101.0]
    volumes = [100.0, 100.0, 100.0, 130.0]
    return [
        {
            "timestamp": start + timedelta(days=index),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": volume,
        }
        for index, (close, volume) in enumerate(zip(closes, volumes))
    ]


def oos() -> dict:
    return {
        "evaluations": [
            {
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep2118",
                "market": "KRW-ORCA",
                "timeframe": "1d",
                "parameters": {
                    "lookback_bars": 3,
                    "hold_bars": 3,
                    "volume_window": 3,
                    "volume_ratio_floor": 0.8,
                    "momentum_threshold": 0.02,
                },
                "source_conversion": {
                    "recommended_exposure_cap": 0.59,
                    "estimated_cagr": 1.2,
                    "estimated_mdd": -0.2,
                },
                "aggregate": {"pass_fold_count": 2, "total_trade_count": 11},
            }
        ]
    }


def multi_oos() -> dict:
    base = oos()["evaluations"][0]
    rows = []
    for index, threshold in enumerate([0.02, 0.025, 0.03], start=1):
        row = {
            **base,
            "candidate_id": f"candidate_{index}",
            "parameters": {**base["parameters"], "momentum_threshold": threshold},
            "source_conversion": {**base["source_conversion"], "estimated_cagr": 1.2 - index * 0.1},
            "aggregate": {**base["aggregate"], "pass_fold_count": index},
        }
        rows.append(row)
    return {"evaluations": rows}


class BithumbCurrentActionableNonzeroSignalScoutTests(unittest.TestCase):
    def test_finds_triggered_nonzero_shadow_candidate_without_order_paths(self) -> None:
        report = scout.build_report(oos(), {"KRW-ORCA": candles(trigger=True)})

        self.assertEqual(report["status"], "NONZERO_SIGNAL_CANDIDATE_READY_FOR_REVIEW")
        self.assertIn("generated_at_utc", report)
        self.assertEqual(report["evaluated_count"], report["evaluated_candidate_count"])
        self.assertEqual(report["triggered_count"], report["triggered_candidate_count"])
        self.assertEqual(report["triggered_candidate_count"], 1)
        self.assertEqual(report["near_miss_count"], 0)
        self.assertEqual(report["near_miss_blocking_condition_counts"], {})
        self.assertEqual(report["near_miss_gap_summary"]["candidate_count"], 0)
        self.assertIsNone(report["near_miss_gap_summary"]["momentum_gap"]["closest_to_trigger"])
        self.assertEqual(report["top_triggered_candidate"]["candidate_id"], "bithumb_current_actionable_orca_1d_long_freeze001_sweep2118")
        self.assertEqual(report["selection_policy"]["sort_keys"], ["source_conversion.estimated_cagr", "aggregate.pass_fold_count"])
        self.assertFalse(report["selection_policy"]["uses_oos_average_fold_cagr_as_primary_key"])
        self.assertEqual(report["top_triggered_candidate"]["selection_rank"], 1)
        self.assertEqual(report["top_triggered_selection"]["selection_key"]["estimated_cagr"], 1.2)
        self.assertEqual(report["triggered_rank_by_candidate"]["bithumb_current_actionable_orca_1d_long_freeze001_sweep2118"], 1)
        self.assertIsNone(report["top_near_miss_candidate"])
        self.assertFalse(report["safety"]["does_emit_order_signal"])
        self.assertFalse(report["safety"]["live_allowed_by_this_report"])
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])
        self.assertEqual(report["safety"]["real_orders"], 0)

    def test_blocks_when_no_current_nonzero_signal_is_found(self) -> None:
        report = scout.build_report(oos(), {"KRW-ORCA": candles(trigger=False)})

        self.assertEqual(report["status"], "NO_CURRENT_NONZERO_SIGNAL_FOUND")
        self.assertEqual(report["triggered_candidate_count"], 0)
        self.assertEqual(report["top_near_miss_candidate"]["candidate_id"], "bithumb_current_actionable_orca_1d_long_freeze001_sweep2118")
        self.assertEqual(report["top_near_miss"]["candidate_id"], "bithumb_current_actionable_orca_1d_long_freeze001_sweep2118")
        self.assertEqual(report["near_miss_count"], 1)
        self.assertEqual(report["near_miss_blocking_condition_counts"]["momentum_below_threshold"], 1)
        self.assertEqual(report["near_miss_gap_summary"]["candidate_count"], 1)
        self.assertEqual(report["near_miss_gap_summary"]["blocking_condition_counts"]["momentum_below_threshold"], 1)
        self.assertLess(report["near_miss_gap_summary"]["momentum_gap"]["closest_to_trigger"], 0)
        self.assertGreater(report["near_miss_gap_summary"]["volume_gap"]["closest_to_trigger"], 0)
        self.assertEqual(report["top_near_miss_candidates"][0]["candidate_id"], "bithumb_current_actionable_orca_1d_long_freeze001_sweep2118")
        self.assertEqual(report["top_near_miss_limit"], 5)
        self.assertIn("momentum_below_threshold", report["top_near_miss_candidate"]["signal_gap"]["blocking_conditions"])
        self.assertIn("momentum_below_threshold", report["top_near_miss"]["blocking_conditions"])
        self.assertEqual(report["top_near_miss"]["blockers"], report["top_near_miss"]["blocking_conditions"])
        self.assertLess(report["top_near_miss"]["nearest_trigger_gap"], 0)
        self.assertEqual(report["top_near_miss_candidate"]["near_miss_rank"], 1)
        self.assertIn("NO_CURRENT_NONZERO_BITHUMB_SIGNAL_CANDIDATE_FOUND", report["blockers"])
        self.assertFalse(report["safety"]["does_write_order_intent"])

    def test_lists_ranked_near_miss_candidates_for_model_review(self) -> None:
        report = scout.build_report(multi_oos(), {"KRW-ORCA": candles(trigger=False)})

        self.assertEqual(report["status"], "NO_CURRENT_NONZERO_SIGNAL_FOUND")
        self.assertEqual(report["near_miss_count"], 3)
        self.assertEqual(report["near_miss_blocking_condition_counts"]["momentum_below_threshold"], 3)
        self.assertEqual(report["near_miss_gap_summary"]["momentum_gap"]["count"], 3)
        self.assertEqual(
            report["near_miss_gap_summary"]["momentum_gap"]["closest_to_trigger"],
            report["top_near_miss_candidates"][0]["momentum_gap"],
        )
        self.assertEqual([row["near_miss_rank"] for row in report["top_near_miss_candidates"]], [1, 2, 3])
        self.assertEqual(report["top_near_miss_candidates"][0]["candidate_id"], "candidate_1")
        self.assertLess(report["top_near_miss_candidates"][0]["nearest_trigger_gap"], 0)
        self.assertFalse(report["safety"]["broker_submit_allowed_by_this_report"])


if __name__ == "__main__":
    unittest.main()
