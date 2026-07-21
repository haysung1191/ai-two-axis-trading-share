from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_local_source_audit.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_local_source_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class KisProviderResponseLocalSourceAuditTests(unittest.TestCase):
    def test_local_source_audit_rejects_caveated_current_snapshot_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_files = self.write_requests(root)
            membership_files = {"kis_us_stocks": root / "us_membership.csv", "kis_korea_etfs": root / "kr_etf_membership.csv"}
            event_files = {
                "event_or_no_event": root / "no_event.csv",
                "event": root / "events.csv",
                "replay": root / "replay.csv",
            }
            self.write_csv(
                membership_files["kis_us_stocks"],
                ["symbol", "axis", "evidence_quality", "source"],
                [["MU", "kis_us_stocks", "current_snapshot_caveated", "snapshot"]],
            )
            self.write_csv(membership_files["kis_korea_etfs"], ["symbol", "axis", "evidence_quality"], [])
            self.write_csv(event_files["event_or_no_event"], ["symbol", "evidence_quality"], [])
            self.write_csv(event_files["event"], ["symbol", "evidence_quality"], [])
            self.write_csv(event_files["replay"], ["scenario", "evidence_quality"], [])

            report = audit_mod.build_report(
                "2026-05-14T01:40:00+09:00",
                request_files=request_files,
                membership_files=membership_files,
                event_files=event_files,
            )

        self.assertEqual(report["status"], "LOCAL_SOURCE_EVIDENCE_NOT_OPERATION_READY")
        self.assertEqual(report["total_usable_rows"], 0)
        self.assertEqual(report["audits"]["membership"][0]["local_match_count"], 1)
        self.assertEqual(report["audits"]["membership"][0]["operation_ready_match_count"], 0)
        self.assertIn("current_snapshot_caveated", report["audits"]["membership"][0]["local_evidence_qualities"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_local_source_audit_counts_operation_ready_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_files = self.write_requests(root)
            membership_files = {"kis_us_stocks": root / "us_membership.csv", "kis_korea_etfs": root / "kr_etf_membership.csv"}
            event_files = {
                "event_or_no_event": root / "no_event.csv",
                "event": root / "events.csv",
                "replay": root / "replay.csv",
            }
            self.write_csv(
                membership_files["kis_us_stocks"],
                ["symbol", "axis", "evidence_quality", "source"],
                [["MU", "kis_us_stocks", "authoritative", "exchange"]],
            )
            self.write_csv(membership_files["kis_korea_etfs"], ["symbol", "axis", "evidence_quality"], [])
            self.write_csv(event_files["event_or_no_event"], ["symbol", "evidence_quality"], [["MU", "licensed_vendor"]])
            self.write_csv(event_files["event"], ["symbol", "evidence_quality"], [])
            self.write_csv(event_files["replay"], ["scenario", "evidence_quality"], [["ticker_change", "replay_test_authoritative"]])

            report = audit_mod.build_report(
                "2026-05-14T01:40:00+09:00",
                request_files=request_files,
                membership_files=membership_files,
                event_files=event_files,
            )

        self.assertEqual(report["status"], "LOCAL_SOURCE_EVIDENCE_OPERATION_READY")
        self.assertEqual(report["total_usable_rows"], 3)

    def write_requests(self, root: Path) -> dict[str, Path]:
        request_files = {
            "membership": root / "membership_request.csv",
            "event_or_no_event": root / "event_request.csv",
            "replay": root / "replay_request.csv",
        }
        self.write_csv(request_files["membership"], ["request_id", "symbol", "axis"], [["M1", "MU", "kis_us_stocks"]])
        self.write_csv(request_files["event_or_no_event"], ["request_id", "symbol", "axis"], [["E1", "MU", "kis_us_stocks"]])
        self.write_csv(request_files["replay"], ["request_id", "scenario"], [["R1", "ticker_change"]])
        return request_files

    def write_csv(self, path: Path, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
