from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from src.policy.loader import PolicyBundleLoader
from src.policy.models import PolicyFlags


def main() -> int:
    parser = argparse.ArgumentParser(description="Install a policy bundle with manifest validation and atomic rename.")
    parser.add_argument("--bundle", required=True, help="Source policy_bundle.json path")
    parser.add_argument("--manifest", required=True, help="Source manifest.json path")
    parser.add_argument("--target-dir", required=True, help="Target directory, e.g. policy/current")
    args = parser.parse_args()

    source_bundle = Path(args.bundle)
    source_manifest = Path(args.manifest)
    target_dir = Path(args.target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    loader = PolicyBundleLoader(bundle_path=str(source_bundle), manifest_path=str(source_manifest))
    state = loader.load(PolicyFlags(trace_enabled=True))
    if state.bundle is None:
        raise SystemExit(f"Bundle validation failed: {state.error}")

    temp_dir = Path(tempfile.mkdtemp(prefix="policy_bundle_", dir=str(target_dir.parent)))
    backup_dir = target_dir.parent / f"{target_dir.name}.bak"
    try:
        shutil.copy2(source_bundle, temp_dir / "policy_bundle.json")
        shutil.copy2(source_manifest, temp_dir / "manifest.json")
        staged_state = PolicyBundleLoader(
            bundle_path=str(temp_dir / "policy_bundle.json"),
            manifest_path=str(temp_dir / "manifest.json"),
        ).load(PolicyFlags(trace_enabled=True))
        if staged_state.bundle is None:
            raise SystemExit(f"Staged bundle validation failed: {staged_state.error}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        if target_dir.exists():
            target_dir.replace(backup_dir)
        temp_dir.replace(target_dir)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
