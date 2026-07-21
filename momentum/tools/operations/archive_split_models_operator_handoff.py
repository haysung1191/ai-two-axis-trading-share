from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import shutil

import pandas as pd


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"

ARCHIVE_FILES = [
    "shadow_operator_runtime_status.json",
    "shadow_summary.json",
    "shadow_drift_report.json",
    "shadow_live_transition_summary.json",
    "shadow_live_transition_diff.csv",
    "shadow_rebalance_orders.csv",
    "shadow_rebalance_market_summary.csv",
    "shadow_rebalance_execution_summary.json",
    "shadow_live_readiness.json",
    "shadow_live_transition_packet.md",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _backfill_operator_gate_verdicts(manifest: pd.DataFrame) -> pd.DataFrame:
    if "OperatorGateVerdict" not in manifest.columns:
        manifest["OperatorGateVerdict"] = None
    else:
        manifest["OperatorGateVerdict"] = manifest["OperatorGateVerdict"].astype(object)

    for index, row in manifest.iterrows():
        current = row.get("OperatorGateVerdict")
        if pd.notna(current):
            continue
        archive_path = row.get("ArchivePath")
        if not archive_path:
            continue
        runtime_path = Path(str(archive_path)) / "shadow_operator_runtime_status.json"
        if not runtime_path.exists():
            continue
        runtime_status = _load_json(runtime_path)
        manifest.at[index, "OperatorGateVerdict"] = runtime_status.get("operator_gate_verdict")
    return manifest


def _copy_archive_files(target_dir: Path, file_names: list[str]) -> None:
    for name in file_names:
        src = SHADOW_DIR / name
        if src.exists():
            shutil.copy2(src, target_dir / name)


def _current_manifest_row(run_id: str, archive_path: Path) -> dict[str, object]:
    summary = _load_json(SHADOW_DIR / "shadow_summary.json")
    drift = _load_json(SHADOW_DIR / "shadow_drift_report.json")
    readiness = _load_json(SHADOW_DIR / "shadow_live_readiness.json")
    transition = _load_json(SHADOW_DIR / "shadow_live_transition_summary.json")
    runtime_status = _load_json(SHADOW_DIR / "shadow_operator_runtime_status.json")
    return {
        "RunId": run_id,
        "BaselineVariant": summary.get("baseline_variant"),
        "HealthVerdict": summary.get("health_verdict"),
        "DriftVerdict": drift.get("drift_verdict"),
        "LiveReadinessVerdict": readiness.get("live_readiness_verdict"),
        "OperatorGateVerdict": runtime_status.get("operator_gate_verdict"),
        "CurrentHoldings": summary.get("current_holdings"),
        "CurrentDominantSector": summary.get("current_dominant_sector"),
        "TransitionWeightTurnover": transition.get("weight_turnover"),
        "ArchivePath": str(archive_path),
    }


def sync_latest_archive(file_names: list[str] | None = None) -> Path:
    manifest_path = ARCHIVE_DIR / "archive_manifest.csv"
    manifest = pd.read_csv(manifest_path).sort_values("RunId").reset_index(drop=True)
    latest_row = manifest.iloc[-1].to_dict()
    latest_dir = Path(str(latest_row["ArchivePath"]))
    latest_dir.mkdir(parents=True, exist_ok=True)
    _copy_archive_files(latest_dir, file_names or ARCHIVE_FILES)
    refreshed_row = _current_manifest_row(str(latest_row["RunId"]), latest_dir)
    for key, value in refreshed_row.items():
        manifest.at[manifest.index[-1], key] = value
    manifest = _backfill_operator_gate_verdicts(manifest)
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")
    return latest_dir


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sync-latest-only", action="store_true")
    args = parser.parse_args(argv or [])

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if args.sync_latest_only:
        latest_dir = sync_latest_archive()
        print(f"archive_sync_path={latest_dir}")
        return

    run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    target_dir = ARCHIVE_DIR / run_id
    target_dir.mkdir(parents=True, exist_ok=False)

    _copy_archive_files(target_dir, ARCHIVE_FILES)

    row = _current_manifest_row(run_id, target_dir)

    manifest_path = ARCHIVE_DIR / "archive_manifest.csv"
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
        manifest = _backfill_operator_gate_verdicts(manifest)
        manifest = pd.concat([manifest, pd.DataFrame([row])], ignore_index=True)
    else:
        manifest = pd.DataFrame([row])
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig")

    print(f"archive_run_id={run_id}")
    print(f"archive_path={target_dir}")
    print(f"manifest_path={manifest_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
