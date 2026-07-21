from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd


ROOT = REPO_ROOT
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"
REPORT_PATH = ARCHIVE_DIR / "archive_stability_report.json"


def build_archive_stability_report(window: int = 5) -> dict[str, object]:
    manifest_path = ARCHIVE_DIR / "archive_manifest.csv"
    delta_path = ARCHIVE_DIR / "archive_latest_delta.json"
    consistency_path = ARCHIVE_DIR / "archive_consistency_report.json"

    manifest = pd.read_csv(manifest_path).sort_values("RunId").reset_index(drop=True)
    trailing = manifest.tail(window).copy()

    checks: list[dict[str, object]] = []
    checks.append(
        {
            "Check": "MinWindowRows",
            "Passed": len(trailing) >= min(window, len(manifest)),
            "Value": int(len(trailing)),
            "Threshold": f">={min(window, len(manifest))}",
        }
    )
    checks.append(
        {
            "Check": "AllHealthPass",
            "Passed": bool((trailing["HealthVerdict"] == "PASS").all()),
            "Value": trailing["HealthVerdict"].tolist(),
            "Threshold": "all PASS",
        }
    )
    checks.append(
        {
            "Check": "AllDriftPass",
            "Passed": bool((trailing["DriftVerdict"] == "PASS").all()),
            "Value": trailing["DriftVerdict"].tolist(),
            "Threshold": "all PASS",
        }
    )
    checks.append(
        {
            "Check": "AllReadinessGo",
            "Passed": bool((trailing["LiveReadinessVerdict"] == "GO").all()),
            "Value": trailing["LiveReadinessVerdict"].tolist(),
            "Threshold": "all GO",
        }
    )
    operator_gate_values = trailing["OperatorGateVerdict"].fillna("MISSING").tolist()
    checks.append(
        {
            "Check": "AllOperatorGatePass",
            "Passed": all(value == "PASS" for value in operator_gate_values),
            "Value": operator_gate_values,
            "Threshold": "all PASS",
        }
    )
    if delta_path.exists():
        delta = json.loads(delta_path.read_text(encoding="utf-8"))
        checks.append(
            {
                "Check": "LatestDeltaNoChange",
                "Passed": not any(
                    bool(delta.get(name, False))
                    for name in [
                        "baseline_variant_changed",
                        "live_readiness_changed",
                        "operator_gate_changed",
                        "health_changed",
                        "drift_changed",
                        "dominant_sector_changed",
                    ]
                ) and float(delta.get("transition_turnover_change", 0.0)) == 0.0,
                "Value": {
                    "baseline_variant_changed": delta.get("baseline_variant_changed"),
                    "live_readiness_changed": delta.get("live_readiness_changed"),
                    "operator_gate_changed": delta.get("operator_gate_changed"),
                    "health_changed": delta.get("health_changed"),
                    "drift_changed": delta.get("drift_changed"),
                    "dominant_sector_changed": delta.get("dominant_sector_changed"),
                    "transition_turnover_change": delta.get("transition_turnover_change"),
                },
                "Threshold": "all false and turnover_change == 0",
            }
        )

    if consistency_path.exists():
        consistency = json.loads(consistency_path.read_text(encoding="utf-8"))
        checks.append(
            {
                "Check": "LatestConsistencyPass",
                "Passed": consistency.get("archive_consistency_verdict") == "PASS",
                "Value": consistency.get("archive_consistency_verdict"),
                "Threshold": "PASS",
            }
        )

    verdict = "PASS" if all(bool(check["Passed"]) for check in checks) else "FAIL"
    payload = {
        "archive_stability_verdict": verdict,
        "window": window,
        "latest_run_id": trailing.iloc[-1]["RunId"] if not trailing.empty else None,
        "runs_considered": trailing["RunId"].tolist(),
        "checks": checks,
    }
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args(argv)

    payload = build_archive_stability_report(window=args.window)
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"archive_stability_verdict={payload['archive_stability_verdict']}")
    print(f"window={payload['window']}")
    print(f"latest_run_id={payload['latest_run_id']}")


if __name__ == "__main__":
    main()
