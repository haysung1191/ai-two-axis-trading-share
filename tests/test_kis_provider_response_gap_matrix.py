from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_gap_matrix.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_gap_matrix", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
gap_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gap_mod)


class KisProviderResponseGapMatrixTests(unittest.TestCase):
    def test_gap_matrix_lists_missing_request_ids_without_claiming_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_files, response_files, validator_path = self.write_fixture(root, with_response=False)
            report = gap_mod.build_report(
                "2026-05-14T01:00:00+09:00",
                request_files=request_files,
                response_files=response_files,
                validator_path=validator_path,
            )

        self.assertEqual(report["status"], "BLOCK_PROVIDER_RESPONSE_GAPS_REMAIN")
        self.assertEqual(report["missing_counts"], {"membership": 1, "event_or_no_event": 1, "replay": 1})
        self.assertEqual(report["total_missing_response_rows"], 3)
        self.assertEqual(report["missing_rows_by_kind"]["membership"][0]["request_id"], "M1")
        self.assertIn("active_from", report["missing_rows_by_kind"]["membership"][0]["required_response_fields"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_gap_matrix_passes_only_when_all_response_request_ids_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_files, response_files, validator_path = self.write_fixture(root, with_response=True)
            report = gap_mod.build_report(
                "2026-05-14T01:00:00+09:00",
                request_files=request_files,
                response_files=response_files,
                validator_path=validator_path,
            )

        self.assertEqual(report["status"], "PASS_PROVIDER_RESPONSE_GAP_MATRIX_CLOSED")
        self.assertEqual(report["total_missing_response_rows"], 0)
        self.assertEqual(report["missing_rows_by_kind"]["replay"], [])

    def write_fixture(self, root: Path, with_response: bool) -> tuple[dict[str, Path], dict[str, Path], Path]:
        request_files = {
            "membership": root / "membership_request.csv",
            "event_or_no_event": root / "event_request.csv",
            "replay": root / "replay_request.csv",
        }
        response_files = {
            "membership": root / "membership_response.csv",
            "event_or_no_event": root / "event_response.csv",
            "replay": root / "replay_response.csv",
        }
        self.write_csv(
            request_files["membership"],
            ["request_id", "symbol", "axis", "accepted_evidence_quality", "target_intake_file"],
            [["M1", "MU", "kis_us_stocks", "authoritative|licensed_vendor", "membership_intake.csv"]],
        )
        self.write_csv(
            request_files["event_or_no_event"],
            ["request_id", "symbol", "axis", "accepted_evidence_quality", "target_intake_file"],
            [["E1", "MU", "kis_us_stocks", "authoritative|licensed_vendor", "event_intake.csv"]],
        )
        self.write_csv(
            request_files["replay"],
            ["request_id", "scenario", "event_type", "required_fields", "accepted_evidence_quality", "target_intake_file"],
            [["R1", "ticker_change", "ticker_change", "case_id,symbol,successor_symbol", "replay_test_authoritative", "replay_intake.csv"]],
        )
        response_headers = {
            "membership": ["request_id", "symbol"],
            "event_or_no_event": ["request_id", "symbol"],
            "replay": ["request_id", "scenario"],
        }
        for kind, path in response_files.items():
            row = []
            if with_response:
                row = [["M1", "MU"]] if kind == "membership" else [["E1", "MU"]] if kind == "event_or_no_event" else [["R1", "ticker_change"]]
            self.write_csv(path, response_headers[kind], row)

        validator_path = root / "validator.json"
        validator_path.write_text(
            json.dumps(
                {
                    "status": "READY_TO_IMPORT_PROVIDER_RESPONSE_TO_INTAKE_REVIEW" if with_response else "BLOCK_PROVIDER_RESPONSE_NOT_READY",
                    "inspections": {
                        "membership": {"missing_request_ids": [] if with_response else ["M1"]},
                        "event_or_no_event": {"missing_request_ids": [] if with_response else ["E1"]},
                        "replay": {"missing_request_ids": [] if with_response else ["R1"]},
                    },
                }
            ),
            encoding="utf-8",
        )
        return request_files, response_files, validator_path

    def write_csv(self, path: Path, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
