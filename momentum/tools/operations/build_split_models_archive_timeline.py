from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd


ROOT = REPO_ROOT
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"
REPORT_PATH = ARCHIVE_DIR / "archive_timeline_report.json"


def _load_manifest() -> pd.DataFrame:
    path = ARCHIVE_DIR / "archive_manifest.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_operator_gate_verdict(row: pd.Series) -> object:
    value = row.get("OperatorGateVerdict")
    if value is None:
        runtime = _load_optional_json(Path(str(row.get("ArchivePath", ""))) / "shadow_operator_runtime_status.json")
        return runtime.get("operator_gate_verdict")
    if isinstance(value, float) and math.isnan(value):
        runtime = _load_optional_json(Path(str(row.get("ArchivePath", ""))) / "shadow_operator_runtime_status.json")
        return runtime.get("operator_gate_verdict")
    return value


def build_timeline_payload(window: int = 8) -> dict[str, object]:
    manifest = _load_manifest()
    if manifest.empty:
        return {
            "archive_timeline_verdict": "HOLD",
            "window": window,
            "available_runs": 0,
            "latest_run_id": None,
            "timeline": [],
        }

    ordered = manifest.sort_values("RunId", ascending=False).head(window).copy()
    latest_run_id = str(ordered.iloc[0]["RunId"])
    ordered["RunId"] = ordered["RunId"].astype(str)

    timeline = []
    for _, row in ordered.iterrows():
        timeline.append(
            {
                "run_id": row["RunId"],
                "baseline_variant": row.get("BaselineVariant"),
                "health_verdict": row.get("HealthVerdict"),
                "drift_verdict": row.get("DriftVerdict"),
                "live_readiness_verdict": row.get("LiveReadinessVerdict"),
                "operator_gate_verdict": _normalized_operator_gate_verdict(row),
                "current_holdings": int(row.get("CurrentHoldings", 0)),
                "dominant_sector": row.get("CurrentDominantSector"),
                "transition_weight_turnover": float(row.get("TransitionWeightTurnover", 0.0)),
            }
        )

    verdict = "PASS"
    if not all(item["health_verdict"] == "PASS" for item in timeline):
        verdict = "FAIL"
    if not all(item["drift_verdict"] == "PASS" for item in timeline):
        verdict = "FAIL"
    if not all(item["live_readiness_verdict"] == "GO" for item in timeline):
        verdict = "FAIL"
    prior_timeline = timeline[1:] if len(timeline) > 1 else []
    if prior_timeline and not all(item["operator_gate_verdict"] == "PASS" for item in prior_timeline):
        verdict = "FAIL"

    return {
        "archive_timeline_verdict": verdict,
        "window": window,
        "available_runs": int(len(manifest)),
        "latest_run_id": latest_run_id,
        "timeline": timeline,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=8)
    args = parser.parse_args(argv)

    payload = build_timeline_payload(window=args.window)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
