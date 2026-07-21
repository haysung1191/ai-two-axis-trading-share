from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_pit_snapshot_manifest.py")
SPEC = importlib.util.spec_from_file_location("build_kis_pit_snapshot_manifest", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
manifest_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest_mod)


class KisPitSnapshotManifestTests(unittest.TestCase):
    def write_json(self, path: Path, status: str) -> None:
        path.write_text(json.dumps({"status": status}), encoding="utf-8")

    def test_manifest_blocks_when_components_are_not_operation_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            membership = tmp_path / "membership.csv"
            membership.write_text("symbol\nAAA\n", encoding="utf-8")
            report_files = {
                "membership_verifier": tmp_path / "membership_verifier.json",
                "delisting_event_verifier": tmp_path / "delisting_event_verifier.json",
                "delisting_no_event_coverage_verifier": tmp_path / "delisting_no_event_coverage_verifier.json",
                "delisting_replay_verifier": tmp_path / "delisting_replay_verifier.json",
                "delisting_symbol_policy": tmp_path / "delisting_policy.json",
                "rebalance_membership_filter_audit": tmp_path / "rebalance.json",
                "upgrade_plan": tmp_path / "upgrade.json",
                "current_snapshot_caveat": tmp_path / "snapshot.json",
            }
            self.write_json(report_files["membership_verifier"], "PASS_SCHEMA_WITH_CAVEATED_OR_NON_OPERATION_READY_EVIDENCE")
            self.write_json(report_files["delisting_event_verifier"], "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED")
            self.write_json(report_files["delisting_no_event_coverage_verifier"], "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED")
            self.write_json(report_files["delisting_replay_verifier"], "BLOCK_DELISTING_REPLAY_NOT_VERIFIED")
            self.write_json(report_files["delisting_symbol_policy"], "BLOCKED_DELISTING_SYMBOL_POLICY_NOT_VERIFIED")
            self.write_json(report_files["rebalance_membership_filter_audit"], "BLOCK_REBALANCE_MEMBERSHIP_FILTER_NOT_PROVEN")
            self.write_json(report_files["upgrade_plan"], "BLOCKED_DATA_UPGRADE_REQUIRED")
            self.write_json(report_files["current_snapshot_caveat"], "CAVEATED_CURRENT_SNAPSHOT_WRITTEN")

            manifest = manifest_mod.build_manifest(
                "2026-05-13T00:00:00+09:00",
                {"kis_us_stocks": membership},
                report_files,
            )

        self.assertEqual(manifest["status"], "BLOCK_OPERATION_READY_MANIFEST")
        self.assertFalse(manifest["operation_ready"])
        self.assertIn("membership_verifier_not_operation_ready", manifest["blockers"])
        self.assertIn("delisting_event_file_or_no_event_coverage_not_operation_ready", manifest["blockers"])
        self.assertIn("delisting_replay_not_operation_ready", manifest["blockers"])
        self.assertFalse(manifest["safety"]["live_enabled"])

    def test_manifest_passes_only_when_all_components_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            membership = tmp_path / "membership.csv"
            membership.write_text("symbol\nAAA\n", encoding="utf-8")
            report_files = {
                "membership_verifier": tmp_path / "membership_verifier.json",
                "delisting_event_verifier": tmp_path / "delisting_event_verifier.json",
                "delisting_no_event_coverage_verifier": tmp_path / "delisting_no_event_coverage_verifier.json",
                "delisting_replay_verifier": tmp_path / "delisting_replay_verifier.json",
                "delisting_symbol_policy": tmp_path / "delisting_policy.json",
                "rebalance_membership_filter_audit": tmp_path / "rebalance.json",
                "upgrade_plan": tmp_path / "upgrade.json",
                "current_snapshot_caveat": tmp_path / "snapshot.json",
            }
            self.write_json(report_files["membership_verifier"], "PASS_MEMBERSHIP_FILES_VERIFIED")
            self.write_json(report_files["delisting_event_verifier"], "PASS_DELISTING_EVENT_FILE_VERIFIED")
            self.write_json(report_files["delisting_no_event_coverage_verifier"], "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED")
            self.write_json(report_files["delisting_replay_verifier"], "PASS_DELISTING_REPLAY_VERIFIED")
            self.write_json(report_files["delisting_symbol_policy"], "PASS_DELISTING_SYMBOL_POLICY_VERIFIED")
            self.write_json(report_files["rebalance_membership_filter_audit"], "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF")
            self.write_json(report_files["upgrade_plan"], "READY_FOR_REGISTRY_REVIEW")
            self.write_json(report_files["current_snapshot_caveat"], "CAVEATED_CURRENT_SNAPSHOT_WRITTEN")

            manifest = manifest_mod.build_manifest(
                "2026-05-13T00:00:00+09:00",
                {"kis_us_stocks": membership},
                report_files,
            )

        self.assertEqual(manifest["status"], "PASS_OPERATION_READY_MANIFEST")
        self.assertTrue(manifest["operation_ready"])
        self.assertEqual(manifest["blockers"], [])
        self.assertFalse(manifest["safety"]["broker_submit_allowed"])

    def test_manifest_can_use_no_event_coverage_instead_of_event_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            membership = tmp_path / "membership.csv"
            membership.write_text("symbol\nAAA\n", encoding="utf-8")
            report_files = {
                "membership_verifier": tmp_path / "membership_verifier.json",
                "delisting_event_verifier": tmp_path / "delisting_event_verifier.json",
                "delisting_no_event_coverage_verifier": tmp_path / "delisting_no_event_coverage_verifier.json",
                "delisting_replay_verifier": tmp_path / "delisting_replay_verifier.json",
                "delisting_symbol_policy": tmp_path / "delisting_policy.json",
                "rebalance_membership_filter_audit": tmp_path / "rebalance.json",
                "upgrade_plan": tmp_path / "upgrade.json",
                "current_snapshot_caveat": tmp_path / "snapshot.json",
            }
            self.write_json(report_files["membership_verifier"], "PASS_MEMBERSHIP_FILES_VERIFIED")
            self.write_json(report_files["delisting_event_verifier"], "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED")
            self.write_json(report_files["delisting_no_event_coverage_verifier"], "PASS_DELISTING_NO_EVENT_COVERAGE_VERIFIED")
            self.write_json(report_files["delisting_replay_verifier"], "PASS_DELISTING_REPLAY_VERIFIED")
            self.write_json(report_files["delisting_symbol_policy"], "PASS_DELISTING_SYMBOL_POLICY_VERIFIED")
            self.write_json(report_files["rebalance_membership_filter_audit"], "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF")
            self.write_json(report_files["upgrade_plan"], "READY_FOR_REGISTRY_REVIEW")
            self.write_json(report_files["current_snapshot_caveat"], "CAVEATED_CURRENT_SNAPSHOT_WRITTEN")

            manifest = manifest_mod.build_manifest(
                "2026-05-13T00:00:00+09:00",
                {"kis_us_stocks": membership},
                report_files,
            )

        self.assertEqual(manifest["status"], "PASS_OPERATION_READY_MANIFEST")
        self.assertEqual(manifest["component_status"]["delisting_no_event_coverage_verifier"], "PASS_DELISTING_NO_EVENT_COVERAGE_VERIFIED")


if __name__ == "__main__":
    unittest.main()
