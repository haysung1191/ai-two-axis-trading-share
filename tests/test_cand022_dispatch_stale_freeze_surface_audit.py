from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_dispatch_stale_freeze_surface_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_dispatch_stale_freeze_surface_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class Cand022DispatchStaleFreezeSurfaceAuditTests(unittest.TestCase):
    def write_freeze(self, path: Path, current_dir: Path) -> None:
        freeze = {
            "status": "READY_FROZEN_EXTERNAL_DISPATCH_PACKET",
            "freeze_dir": str(current_dir),
            "frozen_files": {
                "email_markdown": {
                    "path": str(current_dir / "kis_provider_handoff_email_draft.md"),
                    "sha256": "a" * 64,
                },
                "attachment": {
                    "path": str(current_dir / "CAND-022_provider_handoff_delivery_latest.zip"),
                    "sha256": "b" * 64,
                },
            },
        }
        path.write_text(json.dumps(freeze), encoding="utf-8")

    def test_passes_when_targets_use_current_freeze_and_no_stale_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_root = root / "external_dispatch"
            current = dispatch_root / "CAND-022_external_dispatch_20260514_125949"
            old = dispatch_root / "CAND-022_external_dispatch_20260514_022535"
            current.mkdir(parents=True)
            old.mkdir(parents=True)
            (old / "old.zip").write_bytes(b"old")
            freeze_path = root / "freeze.json"
            self.write_freeze(freeze_path, current)
            target = root / "surface.md"
            target.write_text(f"Use current packet {current} with hash {'a' * 64}.", encoding="utf-8")

            report = audit_mod.build_report(
                "2026-05-14T13:10:00+09:00",
                targets={"surface": target},
                freeze_path=freeze_path,
                external_dispatch_dir=dispatch_root,
            )

        self.assertEqual(report["status"], "PASS_NO_STALE_FREEZE_SURFACES")
        self.assertEqual(report["blockers"], [])
        self.assertGreater(report["stale_token_count"], 0)
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_blocks_when_target_contains_old_freeze_dir_or_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_root = root / "external_dispatch"
            current = dispatch_root / "CAND-022_external_dispatch_20260514_125949"
            old = dispatch_root / "CAND-022_external_dispatch_20260514_022535"
            current.mkdir(parents=True)
            old.mkdir(parents=True)
            old_file = old / "old.zip"
            old_file.write_bytes(b"old")
            old_hash = audit_mod.sha256_file(old_file)
            freeze_path = root / "freeze.json"
            self.write_freeze(freeze_path, current)
            target = root / "surface.md"
            target.write_text(f"Old packet {old} should not remain. Old hash {old_hash}.", encoding="utf-8")

            report = audit_mod.build_report(
                "2026-05-14T13:10:00+09:00",
                targets={"surface": target},
                freeze_path=freeze_path,
                external_dispatch_dir=dispatch_root,
            )

        self.assertEqual(report["status"], "BLOCK_STALE_FREEZE_SURFACE")
        self.assertTrue(any("stale_freeze_token" in blocker for blocker in report["blockers"]))

    def test_default_targets_include_operator_and_stage6_surfaces(self) -> None:
        self.assertIn("operator_status_brief_md", audit_mod.DEFAULT_TARGETS)
        self.assertIn("manual_dispatch_execution_slip_md", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_entry_path_audit_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_blocker_closure_plan_md", audit_mod.DEFAULT_TARGETS)
        self.assertNotIn("stage6_entry_path_audit_json", audit_mod.CURRENT_TOKEN_REQUIRED_TARGETS)
        self.assertNotIn("stage6_blocker_closure_plan_md", audit_mod.CURRENT_TOKEN_REQUIRED_TARGETS)

    def test_blocks_missing_current_token_on_required_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_root = root / "external_dispatch"
            current = dispatch_root / "CAND-022_external_dispatch_20260514_125949"
            current.mkdir(parents=True)
            freeze_path = root / "freeze.json"
            self.write_freeze(freeze_path, current)
            target = root / "surface.md"
            target.write_text("No current packet identity here.", encoding="utf-8")

            report = audit_mod.build_report(
                "2026-05-14T13:10:00+09:00",
                targets={"send_status_json": target},
                freeze_path=freeze_path,
                external_dispatch_dir=dispatch_root,
            )

        self.assertEqual(report["status"], "BLOCK_STALE_FREEZE_SURFACE")
        self.assertIn("send_status_json:current_freeze_token_missing", report["blockers"])

    def test_does_not_treat_reused_current_attachment_hash_as_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_root = root / "external_dispatch"
            current = dispatch_root / "CAND-022_external_dispatch_20260514_125949"
            old = dispatch_root / "CAND-022_external_dispatch_20260514_022535"
            current.mkdir(parents=True)
            old.mkdir(parents=True)
            reused_hash = "b" * 64
            freeze_path = root / "freeze.json"
            self.write_freeze(freeze_path, current)
            target = root / "surface.md"
            target.write_text(f"Current attachment hash {reused_hash}. Current dir {current}.", encoding="utf-8")

            report = audit_mod.build_report(
                "2026-05-14T13:10:00+09:00",
                targets={"send_status_json": target},
                freeze_path=freeze_path,
                external_dispatch_dir=dispatch_root,
            )

        self.assertEqual(report["status"], "PASS_NO_STALE_FREEZE_SURFACES")


if __name__ == "__main__":
    unittest.main()
