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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return _load_json(path)


def resolve_archive_run_dir(run_id: str | None = None) -> tuple[str, Path]:
    manifest = _load_csv(ARCHIVE_DIR / "archive_manifest.csv").sort_values("RunId").reset_index(drop=True)
    if run_id is None:
        row = manifest.iloc[-1].to_dict()
        return str(row["RunId"]), Path(str(row["ArchivePath"]))

    matches = manifest[manifest["RunId"].astype(str) == str(run_id)]
    if matches.empty:
        raise SystemExit(f"archive_run_not_found: {run_id}")
    row = matches.iloc[-1].to_dict()
    return str(row["RunId"]), Path(str(row["ArchivePath"]))


def _resolve_manifest_neighbors(run_id: str) -> tuple[dict[str, object], dict[str, object] | None, dict[str, object] | None]:
    manifest = _load_csv(ARCHIVE_DIR / "archive_manifest.csv").sort_values("RunId").reset_index(drop=True)
    matches = manifest[manifest["RunId"].astype(str) == str(run_id)]
    if matches.empty:
        raise SystemExit(f"archive_run_not_found: {run_id}")
    index = int(matches.index[-1])
    current = manifest.iloc[index].to_dict()
    prior = manifest.iloc[index - 1].to_dict() if index > 0 else None
    next_row = manifest.iloc[index + 1].to_dict() if index < len(manifest) - 1 else None
    return current, prior, next_row


def build_archive_status_payload(run_id: str | None = None) -> dict[str, object]:
    resolved_run_id, run_dir = resolve_archive_run_dir(run_id)
    current_row, prior_row, next_row = _resolve_manifest_neighbors(resolved_run_id)

    summary = _load_json(run_dir / "shadow_summary.json")
    readiness = _load_json(run_dir / "shadow_live_readiness.json")
    drift = _load_json(run_dir / "shadow_drift_report.json")
    transition = _load_json(run_dir / "shadow_live_transition_summary.json")
    runtime_status = _load_json(run_dir / "shadow_operator_runtime_status.json")
    execution = _load_optional_json(run_dir / "shadow_rebalance_execution_summary.json")
    consistency = _load_optional_json(run_dir / "archive_consistency_report.json")
    stability = _load_optional_json(run_dir / "archive_stability_report.json")
    timeline = _load_optional_json(ARCHIVE_DIR / "archive_timeline_report.json")
    timeline_rows = timeline.get("timeline", [])
    timeline_run_ids = [str(row.get("run_id")) for row in timeline_rows]
    timeline_rank = None
    if resolved_run_id in timeline_run_ids:
        timeline_rank = timeline_run_ids.index(resolved_run_id) + 1

    payload: dict[str, object] = {
        "archive_run_id": resolved_run_id,
        "archive_path": str(run_dir),
        "baseline_variant": summary.get("baseline_variant"),
        "live_readiness": readiness.get("live_readiness_verdict"),
        "health_verdict": summary.get("health_verdict"),
        "drift_verdict": drift.get("drift_verdict"),
        "current_holdings": summary.get("current_holdings"),
        "dominant_sector": summary.get("current_dominant_sector"),
        "transition_turnover": transition.get("weight_turnover"),
        "actionable_rows": execution.get("actionable_rows"),
        "operator_gate_verdict": runtime_status.get("operator_gate_verdict"),
        "operator_gate_failures": runtime_status.get("operator_gate_failures", []),
        "archive_consistency_verdict": consistency.get("archive_consistency_verdict"),
        "archive_stability_verdict": stability.get("archive_stability_verdict"),
        "archive_stability_window": stability.get("window"),
        "archive_timeline_verdict": timeline.get("archive_timeline_verdict"),
        "archive_timeline_window": timeline.get("window"),
        "archive_timeline_latest_run_id": timeline.get("latest_run_id"),
        "archive_run_in_timeline": resolved_run_id in timeline_run_ids,
        "archive_run_timeline_rank": timeline_rank,
        "archive_prior_run_id": None if prior_row is None else str(prior_row["RunId"]),
        "archive_next_run_id": None if next_row is None else str(next_row["RunId"]),
        "holdings_change_vs_prior": None
        if prior_row is None
        else int(current_row["CurrentHoldings"]) - int(prior_row["CurrentHoldings"]),
        "dominant_sector_changed_vs_prior": None
        if prior_row is None
        else current_row["CurrentDominantSector"] != prior_row["CurrentDominantSector"],
        "live_readiness_changed_vs_prior": None
        if prior_row is None
        else current_row["LiveReadinessVerdict"] != prior_row["LiveReadinessVerdict"],
        "operator_gate_changed_vs_prior": None
        if prior_row is None
        else current_row.get("OperatorGateVerdict") != prior_row.get("OperatorGateVerdict"),
    }
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = build_archive_status_payload(run_id=args.run_id)
    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"archive_run_id={payload['archive_run_id']}")
    print(f"baseline_variant={payload['baseline_variant']}")
    print(f"live_readiness={payload['live_readiness']}")
    print(f"health_verdict={payload['health_verdict']}")
    print(f"drift_verdict={payload['drift_verdict']}")
    print(f"current_holdings={payload['current_holdings']}")
    print(f"dominant_sector={payload['dominant_sector']}")
    print(f"transition_turnover={float(payload['transition_turnover'] or 0.0):.6f}")
    print(f"actionable_rows={payload['actionable_rows']}")
    print(f"operator_gate_verdict={payload['operator_gate_verdict']}")
    print(f"archive_consistency_verdict={payload['archive_consistency_verdict']}")
    print(f"archive_stability_verdict={payload['archive_stability_verdict']}")
    print(f"archive_timeline_verdict={payload['archive_timeline_verdict']}")
    if payload["archive_stability_window"] is not None:
        print(f"archive_stability_window={payload['archive_stability_window']}")
    if payload["archive_timeline_window"] is not None:
        print(f"archive_timeline_window={payload['archive_timeline_window']}")
        print(f"archive_timeline_latest_run_id={payload['archive_timeline_latest_run_id']}")
    print(f"archive_run_in_timeline={payload['archive_run_in_timeline']}")
    if payload["archive_run_timeline_rank"] is not None:
        print(f"archive_run_timeline_rank={payload['archive_run_timeline_rank']}")
    if payload["archive_prior_run_id"] is not None:
        print(f"archive_prior_run_id={payload['archive_prior_run_id']}")
        print(f"holdings_change_vs_prior={payload['holdings_change_vs_prior']}")
        print(f"dominant_sector_changed_vs_prior={payload['dominant_sector_changed_vs_prior']}")
        print(f"live_readiness_changed_vs_prior={payload['live_readiness_changed_vs_prior']}")
        print(f"operator_gate_changed_vs_prior={payload['operator_gate_changed_vs_prior']}")
    if payload["archive_next_run_id"] is not None:
        print(f"archive_next_run_id={payload['archive_next_run_id']}")
    if payload["operator_gate_failures"]:
        print(f"operator_gate_failures={' | '.join(str(item) for item in payload['operator_gate_failures'])}")


if __name__ == "__main__":
    main()
