from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def find_latest_approved_strategy(artifacts_root: Path) -> Path:
    candidates = []
    for run_dir in artifacts_root.iterdir():
        if not run_dir.is_dir():
            continue
        candidate = run_dir / "approved_strategy.json"
        if candidate.exists():
            candidates.append(candidate)
    if not candidates:
        raise FileNotFoundError("No approved_strategy.json found in artifacts directories.")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def publish_to_gcs(local_path: Path, bucket: str, object_name: str = "approved_strategy.json") -> None:
    destination = f"gs://{bucket}/{object_name}"
    cmd = ["gcloud", "storage", "cp", str(local_path), destination]
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish latest approved strategy to Google Cloud Storage.")
    parser.add_argument("--bucket", required=True, help="Target GCS bucket name (without gs://).")
    parser.add_argument("--artifacts-dir", default="artifacts", help="Artifacts root directory.")
    parser.add_argument("--object-name", default="approved_strategy.json", help="Destination object name.")
    args = parser.parse_args()

    artifacts_root = Path(args.artifacts_dir)
    latest = find_latest_approved_strategy(artifacts_root)
    publish_to_gcs(latest, bucket=args.bucket, object_name=args.object_name)
    print(f"Published {latest} -> gs://{args.bucket}/{args.object_name}")


if __name__ == "__main__":
    main()
