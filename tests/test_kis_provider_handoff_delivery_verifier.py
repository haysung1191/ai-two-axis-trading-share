from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_kis_provider_handoff_delivery_verifier.py")
SPEC = importlib.util.spec_from_file_location("build_kis_provider_handoff_delivery_verifier", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
verifier_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier_mod)


class KisProviderHandoffDeliveryVerifierTests(unittest.TestCase):
    def test_verifier_passes_when_zip_entries_match_manifest_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "delivery.zip"
            data = b"review-only\n"
            manifest = {
                "files": [
                    {
                        "relative_path": "README.md",
                        "size_bytes": len(data),
                        "sha256": verifier_mod.sha256_bytes(data),
                    }
                ]
            }
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("CAND-022_latest/README.md", data)
                zf.writestr("CAND-022_latest/DELIVERY_MANIFEST.json", json.dumps(manifest))
            package_report = root / "package.json"
            package_report.write_text(
                json.dumps({"status": "PROVIDER_HANDOFF_DELIVERY_PACKAGE_READY", "latest_zip": str(zip_path)}),
                encoding="utf-8",
            )
            report = verifier_mod.build_report("2026-05-14T03:45:00+09:00", package_report_path=package_report)

        self.assertEqual(report["status"], "PASS_PROVIDER_HANDOFF_DELIVERY_VERIFIED")
        self.assertEqual(report["verified_file_count"], 1)
        self.assertFalse(report["safety"]["order_intent_created"])

    def test_verifier_blocks_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "delivery.zip"
            manifest = {"files": [{"relative_path": "README.md", "size_bytes": 4, "sha256": "bad"}]}
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("CAND-022_latest/README.md", b"good")
                zf.writestr("CAND-022_latest/DELIVERY_MANIFEST.json", json.dumps(manifest))
            package_report = root / "package.json"
            package_report.write_text(
                json.dumps({"status": "PROVIDER_HANDOFF_DELIVERY_PACKAGE_READY", "latest_zip": str(zip_path)}),
                encoding="utf-8",
            )
            report = verifier_mod.build_report("2026-05-14T03:45:00+09:00", package_report_path=package_report)

        self.assertEqual(report["status"], "BLOCK_PROVIDER_HANDOFF_DELIVERY_VERIFICATION")
        self.assertIn("delivery_zip_hash_or_size_mismatch", report["blockers"])


if __name__ == "__main__":
    unittest.main()
