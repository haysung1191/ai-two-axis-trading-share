from __future__ import annotations

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
DELTA_PATH = ARCHIVE_DIR / "archive_latest_delta.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return _load_json(path)


def _normalized_operator_gate_verdict(row: dict, runtime_status: dict) -> object:
    value = row.get("OperatorGateVerdict")
    if value is None:
        return runtime_status.get("operator_gate_verdict")
    if isinstance(value, float) and math.isnan(value):
        return runtime_status.get("operator_gate_verdict")
    return value


def build_archive_delta() -> dict[str, object]:
    manifest_path = ARCHIVE_DIR / "archive_manifest.csv"
    manifest = pd.read_csv(manifest_path)
    manifest = manifest.sort_values("RunId").reset_index(drop=True)
    latest = manifest.iloc[-1].to_dict()

    if len(manifest) == 1:
        payload = {
            "latest_run_id": latest["RunId"],
            "prior_run_id": None,
            "comparison_available": False,
        }
        return payload

    prior = manifest.iloc[-2].to_dict()
    latest_dir = Path(str(latest["ArchivePath"]))
    prior_dir = Path(str(prior["ArchivePath"]))

    latest_runtime = _load_optional_json(latest_dir / "shadow_operator_runtime_status.json")
    prior_runtime = _load_optional_json(prior_dir / "shadow_operator_runtime_status.json")
    latest_summary = _load_optional_json(latest_dir / "shadow_summary.json")
    prior_summary = _load_optional_json(prior_dir / "shadow_summary.json")
    latest_operator_gate = _normalized_operator_gate_verdict(latest, latest_runtime)
    prior_operator_gate = _normalized_operator_gate_verdict(prior, prior_runtime)

    payload = {
        "latest_run_id": latest["RunId"],
        "prior_run_id": prior["RunId"],
        "comparison_available": True,
        "baseline_variant_changed": latest["BaselineVariant"] != prior["BaselineVariant"],
        "live_readiness_changed": latest["LiveReadinessVerdict"] != prior["LiveReadinessVerdict"],
        "operator_gate_changed": latest_operator_gate != prior_operator_gate,
        "health_changed": latest["HealthVerdict"] != prior["HealthVerdict"],
        "drift_changed": latest["DriftVerdict"] != prior["DriftVerdict"],
        "holdings_change": int(latest["CurrentHoldings"]) - int(prior["CurrentHoldings"]),
        "transition_turnover_change": float(latest["TransitionWeightTurnover"]) - float(prior["TransitionWeightTurnover"]),
        "dominant_sector_changed": latest["CurrentDominantSector"] != prior["CurrentDominantSector"],
        "latest_live_readiness": latest["LiveReadinessVerdict"],
        "prior_live_readiness": prior["LiveReadinessVerdict"],
        "latest_operator_gate": latest_operator_gate,
        "prior_operator_gate": prior_operator_gate,
        "latest_health": latest["HealthVerdict"],
        "prior_health": prior["HealthVerdict"],
        "latest_drift": latest["DriftVerdict"],
        "prior_drift": prior["DriftVerdict"],
        "latest_runtime_status": latest_runtime,
        "prior_runtime_status": prior_runtime,
        "latest_summary": {
            "current_holdings": latest_summary.get("current_holdings"),
            "current_dominant_sector": latest_summary.get("current_dominant_sector"),
            "recent_avg_turnover": latest_summary.get("recent_avg_turnover"),
        },
        "prior_summary": {
            "current_holdings": prior_summary.get("current_holdings"),
            "current_dominant_sector": prior_summary.get("current_dominant_sector"),
            "recent_avg_turnover": prior_summary.get("recent_avg_turnover"),
        },
    }
    return payload


def main() -> None:
    payload = build_archive_delta()
    DELTA_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"archive_delta_path={DELTA_PATH}")
    print(f"comparison_available={payload['comparison_available']}")


if __name__ == "__main__":
    main()
