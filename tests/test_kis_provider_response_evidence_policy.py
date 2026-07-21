from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_response_evidence_policy.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_response_evidence_policy", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
policy_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy_mod)


class KisProviderResponseEvidencePolicyTests(unittest.TestCase):
    def test_policy_marks_current_snapshot_and_price_history_as_rejected_shortcuts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_files = self.write_requests(root)
            report = policy_mod.build_report("2026-05-14T01:50:00+09:00", request_files=request_files)

        self.assertEqual(report["status"], "EVIDENCE_POLICY_READY_REVIEW_ONLY")
        self.assertEqual(report["request_counts"], {"membership": 1, "event_or_no_event": 1, "replay": 1})
        membership_policy = report["policies_by_kind"]["membership"][0]
        replay_policy = report["policies_by_kind"]["replay"][0]
        self.assertIn("current_snapshot_caveated", report["rejected_evidence_quality"])
        self.assertIn("price history existence as proxy for listing or membership", membership_policy["explicitly_rejected_shortcuts"])
        self.assertIn("successor_symbol", replay_policy["required_source_content"])
        self.assertFalse(report["safety"]["order_intent_created"])

    def write_requests(self, root: Path) -> dict[str, Path]:
        request_files = {
            "membership": root / "membership.csv",
            "event_or_no_event": root / "event.csv",
            "replay": root / "replay.csv",
        }
        self.write_csv(
            request_files["membership"],
            ["request_id", "symbol", "axis", "accepted_evidence_quality"],
            [["M1", "MU", "kis_us_stocks", "authoritative|licensed_vendor"]],
        )
        self.write_csv(
            request_files["event_or_no_event"],
            ["request_id", "symbol", "axis", "accepted_evidence_quality"],
            [["E1", "MU", "kis_us_stocks", "authoritative|licensed_vendor"]],
        )
        self.write_csv(
            request_files["replay"],
            ["request_id", "scenario", "event_type", "required_fields", "accepted_evidence_quality"],
            [["R1", "ticker_change", "ticker_change", "case_id,symbol,successor_symbol", "replay_test_authoritative"]],
        )
        return request_files

    def write_csv(self, path: Path, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
