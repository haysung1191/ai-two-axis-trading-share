from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_handoff_delivery_package.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_handoff_delivery_package", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
package_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package_mod)


class KisProviderHandoffDeliveryPackageTests(unittest.TestCase):
    def test_package_contains_handoff_files_and_manifest_without_trading_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            package_dir = root / "packages"
            handoff.mkdir()
            (handoff / "README.md").write_text("review-only\n", encoding="utf-8")
            (handoff / "draft.csv").write_text("request_id,source\nR1,\n", encoding="utf-8")
            report = package_mod.build_report(
                "2026-05-14T03:30:00+09:00",
                handoff_dir=handoff,
                package_dir=package_dir,
                run_stamp="20260514_033000",
            )
            latest_zip = Path(report["latest_zip"])
            with zipfile.ZipFile(latest_zip) as zf:
                names = set(zf.namelist())

        self.assertEqual(report["status"], "PROVIDER_HANDOFF_DELIVERY_PACKAGE_READY")
        self.assertEqual(report["file_count"], 2)
        self.assertIn("CAND-022_latest/README.md", names)
        self.assertIn("CAND-022_latest/draft.csv", names)
        self.assertIn("CAND-022_latest/DELIVERY_MANIFEST.json", names)
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_package_blocks_when_handoff_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = package_mod.build_report(
                "2026-05-14T03:30:00+09:00",
                handoff_dir=root / "missing",
                package_dir=root / "packages",
                run_stamp="20260514_033000",
            )

        self.assertEqual(report["status"], "BLOCK_PROVIDER_HANDOFF_DELIVERY_PACKAGE")
        self.assertIn("handoff_dir_missing", report["blockers"])


if __name__ == "__main__":
    unittest.main()
