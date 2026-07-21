from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_membership_handoff_package.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_membership_handoff_package", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
package_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package_mod)


class KisAxisWideMembershipHandoffPackageTests(unittest.TestCase):
    def test_build_report_creates_four_axis_requests_without_trading(self) -> None:
        queue = {
            "status": "BLOCK_AXIS_WIDE_SOURCE_ACQUISITION_REQUIRED",
            "queue": [
                {
                    "queue_id": "KIS_SRC_000",
                    "lane": "minimal_cand022_unblock",
                    "axis": "kis_us_stocks",
                    "blocking_reason": "already_closed",
                },
                {
                    "queue_id": "KIS_SRC_001",
                    "lane": "axis_wide_operation_ready",
                    "axis": "kis_us_stocks",
                    "blocking_reason": "operation_ready_quality_incomplete",
                },
                {
                    "queue_id": "KIS_SRC_002",
                    "lane": "axis_wide_operation_ready",
                    "axis": "kis_us_etfs",
                    "blocking_reason": "operation_ready_quality_rows_missing",
                },
                {
                    "queue_id": "KIS_SRC_003",
                    "lane": "axis_wide_operation_ready",
                    "axis": "kis_korea_stocks",
                    "blocking_reason": "operation_ready_quality_rows_missing",
                },
                {
                    "queue_id": "KIS_SRC_004",
                    "lane": "axis_wide_operation_ready",
                    "axis": "kis_korea_etfs",
                    "blocking_reason": "operation_ready_quality_incomplete",
                },
            ],
        }
        membership_verifier = {
            "axis_reports": [
                {
                    "axis": "kis_us_stocks",
                    "row_count": 10,
                    "caveated_row_count": 9,
                    "operation_ready_quality_row_count": 1,
                    "source_verified_membership_ready_row_count": 2,
                    "source_verified_membership_gap_after_ready_rows": 7,
                },
                {"axis": "kis_us_etfs", "row_count": 20, "caveated_row_count": 20, "operation_ready_quality_row_count": 0},
                {"axis": "kis_korea_stocks", "row_count": 30, "caveated_row_count": 30, "operation_ready_quality_row_count": 0},
                {"axis": "kis_korea_etfs", "row_count": 40, "caveated_row_count": 39, "operation_ready_quality_row_count": 1},
            ]
        }

        report = package_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            queue=queue,
            membership_verifier=membership_verifier,
            gap_matrix={},
        )

        self.assertEqual(report["status"], "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE")
        self.assertEqual(report["generated_at"], "2026-05-16T10:30:00+09:00")
        self.assertEqual(report["generated_at_utc"], "2026-05-16T01:30:00+00:00")
        self.assertEqual(report["request_count"], 4)
        self.assertEqual(report["axis_count"], 4)
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["operation_ready"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])
        self.assertIn("authoritative", report["request_rows"][0]["accepted_evidence_quality"])
        self.assertIn("current_snapshot_caveated", report["request_rows"][0]["rejected_shortcuts"])
        self.assertEqual(report["request_rows"][0]["required_replacement_row_count"], 9)
        self.assertEqual(report["request_rows"][0]["source_verified_ready_row_count"], 2)
        self.assertEqual(report["request_rows"][0]["required_source_acquisition_row_count"], 7)
        self.assertEqual(report["response_shards"][0]["source_verified_gap_after_ready_rows"], 7)
        self.assertEqual(report["response_shards"][0]["remaining_source_acquisition_row_count"], 7)
        self.assertEqual(report["response_template_rows"][0]["request_id"], "KIS_AXIS_001")
        self.assertEqual([row["request_id"] for row in report["request_rows"]], [
            "KIS_AXIS_001",
            "KIS_AXIS_002",
            "KIS_AXIS_003",
            "KIS_AXIS_004",
        ])

    def test_blocks_when_axis_queue_is_not_current(self) -> None:
        report = package_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            queue={"status": "BLOCK_SOURCE_ACQUISITION_REQUIRED", "queue": []},
            membership_verifier={},
            gap_matrix={},
        )

        self.assertEqual(report["status"], "BLOCK_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE")
        self.assertIn("axis_wide_source_queue_not_active", report["blockers"])
        self.assertIn("expected_four_axis_wide_requests", report["blockers"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_allows_broad_source_queue_status_when_four_axis_items_exist(self) -> None:
        queue = {
            "status": "BLOCK_SOURCE_ACQUISITION_REQUIRED",
            "queue_counts": {"total": 22, "minimal_cand022_unblock": 18, "axis_wide_operation_ready": 4},
            "queue": [
                {"queue_id": "KIS_SRC_019", "lane": "axis_wide_operation_ready", "axis": "kis_us_stocks"},
                {"queue_id": "KIS_SRC_020", "lane": "axis_wide_operation_ready", "axis": "kis_us_etfs"},
                {"queue_id": "KIS_SRC_021", "lane": "axis_wide_operation_ready", "axis": "kis_korea_stocks"},
                {"queue_id": "KIS_SRC_022", "lane": "axis_wide_operation_ready", "axis": "kis_korea_etfs"},
            ],
        }

        report = package_mod.build_report(
            "2026-05-16T10:30:00+09:00",
            queue=queue,
            membership_verifier={},
            gap_matrix={},
        )

        self.assertEqual(report["status"], "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE")
        self.assertEqual([row["request_id"] for row in report["request_rows"]], [
            "KIS_AXIS_001",
            "KIS_AXIS_002",
            "KIS_AXIS_003",
            "KIS_AXIS_004",
        ])

    def test_merge_existing_response_rows_preserves_nonblank_rows_and_remaps_by_axis(self) -> None:
        request_rows = [
            {"request_id": "KIS_AXIS_001", "axis": "kis_us_stocks"},
            {"request_id": "KIS_AXIS_002", "axis": "kis_us_etfs"},
        ]
        existing_rows = [
            {
                "request_id": "KIS_AXIS_019",
                "axis": "kis_us_stocks",
                "symbol": "ABC",
                "asset_type": "STOCK",
                "active_from": "2000-01-01",
                "source": "licensed_vendor_security_master:dataset",
                "snapshot_id": "snap",
                "evidence_quality": "licensed_vendor",
            },
            {
                "request_id": "KIS_AXIS_020",
                "axis": "kis_us_etfs",
                "symbol": "",
                "asset_type": "",
                "active_from": "",
                "source": "",
                "snapshot_id": "",
                "evidence_quality": "",
            },
        ]

        merged = package_mod.merge_existing_response_rows(request_rows, existing_rows)

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["request_id"], "KIS_AXIS_001")
        self.assertEqual(merged[0]["symbol"], "ABC")
        self.assertEqual(merged[1]["request_id"], "KIS_AXIS_002")
        self.assertEqual(merged[1]["symbol"], "")

    def test_merge_existing_response_rows_does_not_add_blank_seed_when_request_has_content(self) -> None:
        request_rows = [{"request_id": "KIS_AXIS_001", "axis": "kis_us_stocks"}]
        existing_rows = [
            {
                "request_id": "KIS_AXIS_001",
                "axis": "kis_us_stocks",
                "symbol": "ABC",
                "asset_type": "STOCK",
                "active_from": "2000-01-01",
                "source": "licensed_vendor_security_master:dataset",
                "snapshot_id": "snap",
                "evidence_quality": "licensed_vendor",
            },
            {
                "request_id": "KIS_AXIS_001",
                "axis": "kis_us_stocks",
                "symbol": "DEF",
                "asset_type": "STOCK",
                "active_from": "2001-01-01",
                "source": "licensed_vendor_security_master:dataset",
                "snapshot_id": "snap",
                "evidence_quality": "licensed_vendor",
            },
        ]

        merged = package_mod.merge_existing_response_rows(request_rows, existing_rows)

        self.assertEqual([row["symbol"] for row in merged], ["ABC", "DEF"])

    def test_response_shard_path_is_stable_per_request_and_axis(self) -> None:
        path = package_mod.response_shard_path({"request_id": "KIS_AXIS_001", "axis": "kis_us_stocks"})

        self.assertEqual(path.name, "KIS_AXIS_001_kis_us_stocks_response.csv")
        self.assertEqual(path.parent.name, "response_shards")

    def test_build_shard_manifest_rows_reports_remaining_replacement_count(self) -> None:
        rows = package_mod.build_shard_manifest_rows(
            [
                {
                    "request_id": "KIS_AXIS_001",
                    "axis": "kis_us_stocks",
                    "path": r"C:\AI\response.csv",
                    "required_replacement_row_count": 10,
                    "source_verified_ready_row_count": 2,
                    "source_verified_gap_after_ready_rows": 8,
                    "preserved_response_row_count": 3,
                    "blank_seed_response_row_count": 0,
                    "remaining_replacement_row_count": 7,
                    "remaining_source_acquisition_row_count": 5,
                }
            ]
        )

        self.assertEqual(rows[0]["required_replacement_row_count"], 10)
        self.assertEqual(rows[0]["source_verified_ready_row_count"], 2)
        self.assertEqual(rows[0]["source_verified_gap_after_ready_rows"], 8)
        self.assertEqual(rows[0]["remaining_replacement_row_count"], 7)
        self.assertEqual(rows[0]["remaining_source_acquisition_row_count"], 5)


if __name__ == "__main__":
    unittest.main()
