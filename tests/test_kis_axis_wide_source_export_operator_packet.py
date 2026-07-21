from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_axis_wide_source_export_operator_packet.py")
SPEC = importlib.util.spec_from_file_location("build_kis_axis_wide_source_export_operator_packet", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class KisAxisWideSourceExportOperatorPacketTests(unittest.TestCase):
    def test_packet_is_ready_when_templates_exist_and_no_exports_present(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            intake_contract={
                "valid_export_count": 0,
                "required_manifest_columns": ["export_id"],
                "required_normalized_columns": ["axis", "symbol"],
            },
            feasibility_matrix={"blocked_worklist_row_count": 16444},
            krx_access_probe={"status": "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS"},
            exports_to_worklist={"status": "BLOCK_SOURCE_EXPORTS_TO_REPLACEMENT_WORKLIST"},
            inbox_status={
                "status": "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX",
                "actionable_file_count": 0,
                "raw_drop_dir": r"C:\AI\data_snapshots\kis_pit_membership\axis_wide_source_exports\raw",
                "normalized_export_dir": r"C:\AI\data_snapshots\kis_pit_membership\axis_wide_source_exports\exports",
            },
            next_command={"status": "BLOCK_NO_ACTIONABLE_SOURCE_EXPORT_FILE", "command_kind": "none"},
        )

        self.assertEqual(report["status"], "READY_OPERATOR_SOURCE_EXPORT_PACKET")
        self.assertEqual(report["blocked_worklist_row_count"], 16444)
        self.assertEqual(report["inbox_status"], "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX")
        self.assertIn("axis_wide_source_exports\\raw", report["raw_drop_dir"])
        self.assertEqual(report["next_command_status"], "BLOCK_NO_ACTIONABLE_SOURCE_EXPORT_FILE")
        self.assertTrue(report["krx_unattended_access_blocked"])
        self.assertIn("README.md", report["paths"]["runbook"])
        self.assertIn("licensed_vendor", report["accepted_evidence_quality"])
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_packet_switches_status_when_valid_exports_are_present(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            intake_contract={"valid_export_count": 1},
            feasibility_matrix={"blocked_worklist_row_count": 16444},
            krx_access_probe={"status": "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS"},
            exports_to_worklist={},
        )

        self.assertEqual(report["status"], "READY_VALID_EXPORTS_PRESENT_REVIEW_MAPPER_DRY_RUN")

    def test_render_md_surfaces_guarded_confirmation_commands(self) -> None:
        report = module.build_report(
            "2026-05-16T00:00:00+09:00",
            intake_contract={"valid_export_count": 0, "required_normalized_columns": ["axis"]},
            feasibility_matrix={"blocked_worklist_row_count": 16444},
            krx_access_probe={"status": "BLOCK_KRX_DATA_MARKETPLACE_UNATTENDED_ACCESS"},
            exports_to_worklist={},
        )
        md = module.render_md(report)

        self.assertIn("normalize_kis_axis_wide_source_export.py", md)
        self.assertIn("README.md", md)
        self.assertIn("upsert_kis_axis_wide_source_export_manifest_row.py", md)
        self.assertIn("Current Planned Next Command", md)
        self.assertIn("APPLY KIS AXIS WIDE SOURCE EXPORTS TO WORKLIST REVIEWED NO_TRADING", md)
        self.assertIn("APPLY KIS AXIS WIDE WORKLIST TO SHARDS REVIEWED NO_TRADING", md)
        self.assertIn("APPLY KIS AXIS WIDE MEMBERSHIP IMPORT REVIEWED NO_TRADING", md)


if __name__ == "__main__":
    unittest.main()
