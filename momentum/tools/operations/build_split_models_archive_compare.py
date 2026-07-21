from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.operations import build_split_models_archive_status as archive_status


ROOT = REPO_ROOT
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"


def build_archive_compare_payload(base_run_id: str, target_run_id: str) -> dict[str, object]:
    base = archive_status.build_archive_status_payload(run_id=base_run_id)
    target = archive_status.build_archive_status_payload(run_id=target_run_id)

    return {
        "base_run_id": base["archive_run_id"],
        "target_run_id": target["archive_run_id"],
        "baseline_variant_changed": base["baseline_variant"] != target["baseline_variant"],
        "live_readiness_changed": base["live_readiness"] != target["live_readiness"],
        "health_changed": base["health_verdict"] != target["health_verdict"],
        "drift_changed": base["drift_verdict"] != target["drift_verdict"],
        "operator_gate_changed": base["operator_gate_verdict"] != target["operator_gate_verdict"],
        "archive_consistency_changed": base["archive_consistency_verdict"] != target["archive_consistency_verdict"],
        "archive_stability_changed": base["archive_stability_verdict"] != target["archive_stability_verdict"],
        "archive_timeline_changed": base["archive_timeline_verdict"] != target["archive_timeline_verdict"],
        "holdings_change": int(target["current_holdings"]) - int(base["current_holdings"]),
        "dominant_sector_changed": base["dominant_sector"] != target["dominant_sector"],
        "transition_turnover_change": float(target["transition_turnover"] or 0.0) - float(base["transition_turnover"] or 0.0),
        "actionable_rows_change": int(target["actionable_rows"] or 0) - int(base["actionable_rows"] or 0),
        "base": {
            "baseline_variant": base["baseline_variant"],
            "live_readiness": base["live_readiness"],
            "health_verdict": base["health_verdict"],
            "drift_verdict": base["drift_verdict"],
            "operator_gate_verdict": base["operator_gate_verdict"],
            "archive_consistency_verdict": base["archive_consistency_verdict"],
            "archive_stability_verdict": base["archive_stability_verdict"],
            "archive_timeline_verdict": base["archive_timeline_verdict"],
            "current_holdings": base["current_holdings"],
            "dominant_sector": base["dominant_sector"],
            "transition_turnover": base["transition_turnover"],
            "timeline_rank": base["archive_run_timeline_rank"],
        },
        "target": {
            "baseline_variant": target["baseline_variant"],
            "live_readiness": target["live_readiness"],
            "health_verdict": target["health_verdict"],
            "drift_verdict": target["drift_verdict"],
            "operator_gate_verdict": target["operator_gate_verdict"],
            "archive_consistency_verdict": target["archive_consistency_verdict"],
            "archive_stability_verdict": target["archive_stability_verdict"],
            "archive_timeline_verdict": target["archive_timeline_verdict"],
            "current_holdings": target["current_holdings"],
            "dominant_sector": target["dominant_sector"],
            "transition_turnover": target["transition_turnover"],
            "timeline_rank": target["archive_run_timeline_rank"],
        },
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-run-id", required=True)
    parser.add_argument("--target-run-id", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = build_archive_compare_payload(args.base_run_id, args.target_run_id)
    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"base_run_id={payload['base_run_id']}")
    print(f"target_run_id={payload['target_run_id']}")
    print(f"baseline_variant_changed={payload['baseline_variant_changed']}")
    print(f"live_readiness_changed={payload['live_readiness_changed']}")
    print(f"health_changed={payload['health_changed']}")
    print(f"drift_changed={payload['drift_changed']}")
    print(f"operator_gate_changed={payload['operator_gate_changed']}")
    print(f"archive_consistency_changed={payload['archive_consistency_changed']}")
    print(f"archive_stability_changed={payload['archive_stability_changed']}")
    print(f"archive_timeline_changed={payload['archive_timeline_changed']}")
    print(f"holdings_change={payload['holdings_change']}")
    print(f"dominant_sector_changed={payload['dominant_sector_changed']}")
    print(f"transition_turnover_change={payload['transition_turnover_change']}")
    print(f"actionable_rows_change={payload['actionable_rows_change']}")


if __name__ == "__main__":
    main()
