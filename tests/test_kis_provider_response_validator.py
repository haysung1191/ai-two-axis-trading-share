from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_validator.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_validator", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
validator_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator_mod)


class KisProviderResponseValidatorTests(unittest.TestCase):
    def test_empty_response_templates_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            request = tmp_path / "membership_request.csv"
            response = tmp_path / "membership_response.csv"
            self.write_rows(
                request,
                ["request_id", "accepted_evidence_quality"],
                [{"request_id": "REQ1", "accepted_evidence_quality": "authoritative|licensed_vendor"}],
            )
            inspection = validator_mod.inspect_response("membership", request, response)

        self.assertFalse(inspection["passed"])
        self.assertTrue(inspection["template_created"])
        self.assertIn("membership_response_empty", inspection["blockers"])
        self.assertIn("REQ1", inspection["missing_request_ids"])

    def test_complete_membership_response_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            request = tmp_path / "membership_request.csv"
            response = tmp_path / "membership_response.csv"
            self.write_rows(
                request,
                ["request_id", "accepted_evidence_quality"],
                [{"request_id": "REQ1", "accepted_evidence_quality": "authoritative|licensed_vendor"}],
            )
            self.write_rows(
                response,
                validator_mod.MEMBERSHIP_RESPONSE_HEADERS,
                [
                    {
                        "request_id": "REQ1",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "active_from": "2000-01-01",
                        "listed_date": "2000-01-01",
                        "source": "vendor",
                        "snapshot_id": "snap",
                        "evidence_quality": "licensed_vendor",
                    }
                ],
            )
            inspection = validator_mod.inspect_response("membership", request, response)

        self.assertTrue(inspection["passed"])
        self.assertEqual(inspection["blockers"], [])

    def test_unsupported_quality_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            request = tmp_path / "membership_request.csv"
            response = tmp_path / "membership_response.csv"
            self.write_rows(
                request,
                ["request_id", "accepted_evidence_quality"],
                [{"request_id": "REQ1", "accepted_evidence_quality": "authoritative|licensed_vendor"}],
            )
            self.write_rows(
                response,
                validator_mod.MEMBERSHIP_RESPONSE_HEADERS,
                [
                    {
                        "request_id": "REQ1",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "active_from": "2000-01-01",
                        "listed_date": "2000-01-01",
                        "source": "manual",
                        "snapshot_id": "snap",
                        "evidence_quality": "manual_review_caveated",
                    }
                ],
            )
            inspection = validator_mod.inspect_response("membership", request, response)

        self.assertFalse(inspection["passed"])
        self.assertIn("membership_response_unsupported_evidence_quality", inspection["blockers"])

    def test_rejected_source_marker_blocks_even_with_allowed_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            request = tmp_path / "membership_request.csv"
            response = tmp_path / "membership_response.csv"
            self.write_rows(
                request,
                ["request_id", "accepted_evidence_quality"],
                [{"request_id": "REQ1", "accepted_evidence_quality": "authoritative|licensed_vendor"}],
            )
            self.write_rows(
                response,
                validator_mod.MEMBERSHIP_RESPONSE_HEADERS,
                [
                    {
                        "request_id": "REQ1",
                        "symbol": "MU",
                        "axis": "kis_us_stocks",
                        "active_from": "2000-01-01",
                        "listed_date": "2000-01-01",
                        "source": "current_full_market_universe_snapshot",
                        "snapshot_id": "snap",
                        "evidence_quality": "authoritative",
                        "notes": "current_snapshot_caveated",
                    }
                ],
            )
            inspection = validator_mod.inspect_response("membership", request, response)

        self.assertFalse(inspection["passed"])
        self.assertIn("membership_response_rejected_source_marker", inspection["blockers"])
        rejected = inspection["rejected_source_rows"][0]["rejected_markers"]
        self.assertIn("current_full_market_universe_snapshot", rejected)
        self.assertIn("current_snapshot_caveated", rejected)

    def write_rows(self, path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "") for header in headers})


if __name__ == "__main__":
    unittest.main()
