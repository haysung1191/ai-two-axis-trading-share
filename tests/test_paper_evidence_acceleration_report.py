from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_paper_evidence_acceleration_report.py")
SPEC = importlib.util.spec_from_file_location("build_paper_evidence_acceleration_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
accel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(accel)


class PaperEvidenceAccelerationReportTests(unittest.TestCase):
    def test_ready_market_paths_defaults_to_all_ready_markets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_rows = []
            for idx in range(25):
                path = root / f"KRW-{idx:03d}.json"
                path.write_text("[]", encoding="utf-8")
                ready_rows.append({"market": f"KRW-{idx:03d}", "raw_path": str(path)})
            availability = root / "availability.json"
            availability.write_text(
                '{"summary": {"ready_markets": ' + __import__("json").dumps(ready_rows) + "}}",
                encoding="utf-8",
            )
            accel.AVAILABILITY = availability

            all_rows = accel.ready_market_paths()
            limited_rows = accel.ready_market_paths(limit=20)

        self.assertEqual(len(all_rows), 25)
        self.assertEqual(len(limited_rows), 20)

    def test_intraday_paths_use_latest_dir_that_contains_intraday_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "20260502T205347Z"
            newer_1d_only = root / "20260502T212445Z"
            (older / "candles" / "1h").mkdir(parents=True)
            (older / "candles" / "4h").mkdir(parents=True)
            (newer_1d_only / "candles" / "1d").mkdir(parents=True)
            (older / "candles" / "1h" / "KRW-BTC.json").write_text("[]", encoding="utf-8")
            (older / "candles" / "4h" / "KRW-ETH.json").write_text("[]", encoding="utf-8")
            (newer_1d_only / "candles" / "1d" / "KRW-BTC.json").write_text("[]", encoding="utf-8")

            accel.ARCHIVE_RAW = root
            rows = accel.intraday_paths()

        self.assertEqual({(market, timeframe) for market, timeframe, _ in rows}, {("KRW-BTC", "1h"), ("KRW-ETH", "4h")})

    def test_evidence_velocity_queue_ranks_non_flat_then_near_trigger_without_submit(self) -> None:
        signals = [
            {
                "market": "KRW-AAA",
                "timeframe": "1d",
                "side": "flat",
                "reason": "momentum_filter_flat",
                "target_weight": 0.0,
                "latest_timestamp": "2026-05-03T00:00:00",
                "lookback_return": 0.005,
                "short_return": 0.001,
                "momentum_threshold": 0.02,
                "volume_ok": True,
                "volume_ratio": 2.0,
                "non_flat_trigger_gap": 0.015,
                "counts_as_live_paper_evidence": True,
            },
            {
                "market": "KRW-BBB",
                "timeframe": "1h",
                "side": "flat",
                "reason": "momentum_filter_flat",
                "target_weight": 0.0,
                "latest_timestamp": "2026-05-03T00:00:00",
                "lookback_return": 0.0014,
                "short_return": 0.001,
                "momentum_threshold": 0.0015,
                "volume_ok": True,
                "volume_ratio": 1.0,
                "non_flat_trigger_gap": 0.0001,
                "counts_as_live_paper_evidence": True,
            },
            {
                "market": "KRW-CCC",
                "timeframe": "1d",
                "side": "long",
                "reason": "multi_asset_momentum_positive",
                "target_weight": 0.02,
                "latest_timestamp": "2026-05-03T00:00:00",
                "lookback_return": 0.03,
                "short_return": 0.01,
                "momentum_threshold": 0.02,
                "volume_ok": True,
                "volume_ratio": 1.0,
                "non_flat_trigger_gap": 0.0,
                "counts_as_live_paper_evidence": True,
            },
        ]

        queue = accel.evidence_velocity_queue(signals)

        self.assertEqual([row["market"] for row in queue], ["KRW-CCC", "KRW-BBB", "KRW-AAA"])
        self.assertTrue(all(row["broker_submit_allowed"] is False for row in queue))
        self.assertEqual(queue[0]["velocity_rank_reason"], "already_non_flat")
        self.assertEqual(queue[1]["velocity_rank_reason"], "nearest_to_non_flat_trigger")

    def test_update_state_tracks_lost_non_flat_snapshot_without_order_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            accel.STATE_PATH = Path(tmp) / "state.json"
            first = [
                {
                    "market": "KRW-AAA",
                    "timeframe": "1d",
                    "side": "long",
                    "target_weight": 0.02,
                    "latest_timestamp": "2026-05-03T00:00:00",
                    "signal_id": "aaa-long",
                    "non_flat_trigger_gap": 0.0,
                    "counts_as_live_paper_evidence": True,
                },
                {
                    "market": "KRW-BBB",
                    "timeframe": "1d",
                    "side": "long",
                    "target_weight": 0.02,
                    "latest_timestamp": "2026-05-03T00:00:00",
                    "signal_id": "bbb-long",
                    "non_flat_trigger_gap": 0.0,
                    "counts_as_live_paper_evidence": True,
                },
            ]
            second = [
                {
                    "market": "KRW-AAA",
                    "timeframe": "1d",
                    "side": "long",
                    "target_weight": 0.02,
                    "latest_timestamp": "2026-05-03T01:00:00",
                    "signal_id": "aaa-long",
                    "non_flat_trigger_gap": 0.0,
                    "counts_as_live_paper_evidence": True,
                },
                {
                    "market": "KRW-BBB",
                    "timeframe": "1d",
                    "side": "flat",
                    "target_weight": 0.0,
                    "latest_timestamp": "2026-05-03T01:00:00",
                    "signal_id": "bbb-flat",
                    "non_flat_trigger_gap": 0.01,
                    "counts_as_live_paper_evidence": True,
                },
            ]

            accel.update_state(first)
            state = accel.update_state(second)

        comparison = state["signal_state_comparison"]
        self.assertTrue(comparison["previous_snapshot_available"])
        self.assertTrue(comparison["non_flat_regression_detected_in_snapshot"])
        self.assertEqual(comparison["previous_non_flat_count"], 2)
        self.assertEqual(comparison["current_non_flat_count"], 1)
        self.assertEqual(comparison["lost_non_flat_signal_count"], 1)
        self.assertEqual(comparison["lost_non_flat_signals"][0]["market"], "KRW-BBB")
        self.assertFalse(comparison["lost_non_flat_signals"][0]["broker_submit_allowed"])


if __name__ == "__main__":
    unittest.main()
