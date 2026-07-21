from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"
REPORT_PATH = ARCHIVE_DIR / "archive_consistency_report.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return _load_json(path)


def _bool(value: bool) -> str:
    return "PASS" if value else "FAIL"


def build_archive_consistency_report() -> dict[str, object]:
    manifest_path = ARCHIVE_DIR / "archive_manifest.csv"
    delta_path = ARCHIVE_DIR / "archive_latest_delta.json"
    runtime_status_path = SHADOW_DIR / "shadow_operator_runtime_status.json"

    manifest = pd.read_csv(manifest_path).sort_values("RunId").reset_index(drop=True)
    delta = _load_json(delta_path)
    runtime_status = _load_json(runtime_status_path)

    latest_row = manifest.iloc[-1].to_dict()
    prior_row = manifest.iloc[-2].to_dict() if len(manifest) > 1 else None
    latest_dir = Path(str(latest_row["ArchivePath"]))
    prior_dir = Path(str(prior_row["ArchivePath"])) if prior_row is not None else None

    latest_archived_runtime = _load_optional_json(latest_dir / "shadow_operator_runtime_status.json")
    prior_archived_runtime = _load_optional_json(prior_dir / "shadow_operator_runtime_status.json") if prior_dir else {}
    latest_archived_summary = _load_optional_json(latest_dir / "shadow_summary.json")

    checks = [
        ("ManifestLatestMatchesDelta", str(latest_row["RunId"]) == str(delta.get("latest_run_id"))),
        (
            "ManifestPriorMatchesDelta",
            prior_row is None or str(prior_row["RunId"]) == str(delta.get("prior_run_id")),
        ),
        (
            "RuntimeLatestRunMatchesDelta",
            str(runtime_status.get("archive_latest_run_id")) == str(delta.get("latest_run_id")),
        ),
        (
            "RuntimePriorRunMatchesDelta",
            prior_row is None or str(runtime_status.get("archive_prior_run_id")) == str(delta.get("prior_run_id")),
        ),
        (
            "ArchivedRuntimeLatestRunMatchesDelta",
            str(latest_archived_runtime.get("archive_latest_run_id")) == str(delta.get("latest_run_id")),
        ),
        (
            "ArchivedRuntimePriorRunMatchesDelta",
            prior_row is None
            or str(prior_archived_runtime.get("archive_latest_run_id")) == str(delta.get("prior_run_id")),
        ),
        ("ArchivedRuntimeEqualsCanonical", latest_archived_runtime == runtime_status),
        (
            "DeltaLatestRuntimeRunMatchesDelta",
            str(delta.get("latest_runtime_status", {}).get("archive_latest_run_id")) == str(delta.get("latest_run_id")),
        ),
        (
            "DeltaPriorRuntimeRunMatchesDelta",
            prior_row is None
            or str(delta.get("prior_runtime_status", {}).get("archive_latest_run_id")) == str(delta.get("prior_run_id")),
        ),
        (
            "LatestSummaryMatchesManifestHoldings",
            latest_archived_summary.get("current_holdings") == latest_row.get("CurrentHoldings"),
        ),
        (
            "LatestSummaryMatchesManifestSector",
            latest_archived_summary.get("current_dominant_sector") == latest_row.get("CurrentDominantSector"),
        ),
        (
            "LatestSummaryMatchesRuntimeBaseline",
            latest_archived_summary.get("baseline_variant") == runtime_status.get("baseline_variant"),
        ),
    ]

    verdict = "PASS" if all(passed for _, passed in checks) else "FAIL"
    payload = {
        "archive_consistency_verdict": verdict,
        "latest_run_id": str(latest_row["RunId"]),
        "prior_run_id": str(prior_row["RunId"]) if prior_row is not None else None,
        "checks": [{"Check": name, "Passed": passed} for name, passed in checks],
    }
    return payload


def main() -> None:
    payload = build_archive_consistency_report()
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"archive_consistency_verdict={payload['archive_consistency_verdict']}")
    for check in payload["checks"]:
        print(f"{check['Check']}={_bool(bool(check['Passed']))}")


if __name__ == "__main__":
    main()
