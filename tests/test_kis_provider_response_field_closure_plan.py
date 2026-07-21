from __future__ import annotations

import importlib.util
import csv
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_field_closure_plan.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_field_closure_plan", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
closure_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(closure_mod)


class KisProviderResponseFieldClosurePlanTests(unittest.TestCase):
    def test_closure_plan_joins_gap_rows_to_source_policy_without_claiming_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gap_path = root / "gap.json"
            policy_path = root / "policy.json"
            gap_path.write_text(
                json.dumps(
                    {
                        "status": "BLOCK_PROVIDER_RESPONSE_GAPS_REMAIN",
                        "missing_counts": {"membership": 1, "event_or_no_event": 0, "replay": 0},
                        "total_missing_response_rows": 1,
                        "missing_rows_by_kind": {
                            "membership": [
                                {
                                    "request_id": "M1",
                                    "symbol": "MU",
                                    "axis": "kis_us_stocks",
                                    "required_response_fields": ["request_id", "active_from", "source"],
                                    "response_file": "membership_response.csv",
                                    "target_intake_file": "membership_intake.csv",
                                }
                            ],
                            "event_or_no_event": [],
                            "replay": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            policy_path.write_text(
                json.dumps(
                    {
                        "status": "EVIDENCE_POLICY_READY_REVIEW_ONLY",
                        "policies_by_kind": {
                            "membership": [
                                {
                                    "request_id": "M1",
                                    "accepted_evidence_quality": ["authoritative", "licensed_vendor"],
                                    "source_family": "US exchange/vendor security master or corporate-action source",
                                    "preferred_sources": ["licensed vendor security master"],
                                    "required_source_content": ["listed_date or active_from"],
                                    "rejected_evidence_quality": ["price_history_only"],
                                    "explicitly_rejected_shortcuts": ["price history existence as proxy"],
                                }
                            ],
                            "event_or_no_event": [],
                            "replay": [],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = closure_mod.build_report(
                "2026-05-14T02:00:00+09:00",
                gap_matrix_path=gap_path,
                evidence_policy_path=policy_path,
            )

        self.assertEqual(report["status"], "BLOCK_PROVIDER_RESPONSE_FIELD_CLOSURE_ROWS_OPEN")
        self.assertEqual(report["closure_row_count"], 1)
        row = report["closure_rows"][0]
        self.assertEqual(row["request_id"], "M1")
        self.assertIn("active_from", row["required_response_fields"])
        self.assertIn("licensed vendor security master", row["preferred_sources"])
        self.assertIn("price_history_only", row["rejected_evidence_quality"])
        self.assertFalse(report["safety"]["order_intent_created"])
        self.assertIn("does_not_fill provider_response rows", report["non_goals"])

    def test_closure_plan_csv_flattens_row_level_fill_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "closure.csv"
            closure_mod.write_closure_csv(
                csv_path,
                [
                    {
                        "kind": "membership",
                        "request_id": "M1",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "required_response_fields": ["request_id", "active_from", "source"],
                        "accepted_evidence_quality": ["authoritative", "licensed_vendor"],
                        "preferred_sources": ["licensed vendor security master"],
                        "rejected_evidence_quality": ["price_history_only"],
                    }
                ],
            )
            with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["request_id"], "M1")
        self.assertIn("active_from", rows[0]["required_response_fields"])
        self.assertIn("licensed_vendor", rows[0]["accepted_evidence_quality"])

    def test_closure_plan_blocks_when_policy_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gap_path = root / "gap.json"
            missing_policy_path = root / "missing_policy.json"
            gap_path.write_text(
                json.dumps(
                    {
                        "status": "PASS_PROVIDER_RESPONSE_GAP_MATRIX_CLOSED",
                        "missing_counts": {"membership": 0, "event_or_no_event": 0, "replay": 0},
                        "total_missing_response_rows": 0,
                        "missing_rows_by_kind": {"membership": [], "event_or_no_event": [], "replay": []},
                    }
                ),
                encoding="utf-8",
            )

            report = closure_mod.build_report(
                "2026-05-14T02:00:00+09:00",
                gap_matrix_path=gap_path,
                evidence_policy_path=missing_policy_path,
            )

        self.assertEqual(report["status"], "BLOCK_PROVIDER_RESPONSE_FIELD_CLOSURE_PLAN")
        self.assertIn("evidence_policy_missing", report["blockers"])


if __name__ == "__main__":
    unittest.main()
