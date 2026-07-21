from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
FLOAT_TOLERANCE = 1e-9


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _lte(value: float, threshold: float) -> bool:
    return float(value) <= float(threshold) + FLOAT_TOLERANCE


def main() -> None:
    summary = _load_json(SHADOW_DIR / "shadow_summary.json")
    drift = _load_json(SHADOW_DIR / "shadow_drift_report.json")
    transition = _load_json(SHADOW_DIR / "shadow_live_transition_summary.json")
    execution = _load_json(SHADOW_DIR / "shadow_rebalance_execution_summary.json")

    checks = [
        {
            "Check": "HealthPass",
            "Passed": summary.get("health_verdict") == "PASS",
            "Value": summary.get("health_verdict"),
            "Threshold": "PASS",
        },
        {
            "Check": "DriftPass",
            "Passed": drift.get("drift_verdict") == "PASS",
            "Value": drift.get("drift_verdict"),
            "Threshold": "PASS",
        },
        {
            "Check": "MinHoldings",
            "Passed": int(summary.get("current_holdings", 0)) >= 4,
            "Value": int(summary.get("current_holdings", 0)),
            "Threshold": ">=4",
        },
        {
            "Check": "Top1Weight",
            "Passed": _lte(float(summary.get("current_top1_weight", 0.0)), 0.25),
            "Value": float(summary.get("current_top1_weight", 0.0)),
            "Threshold": "<=0.25",
        },
        {
            "Check": "Top3Weight",
            "Passed": _lte(float(summary.get("current_top3_weight", 0.0)), 0.60),
            "Value": float(summary.get("current_top3_weight", 0.0)),
            "Threshold": "<=0.60",
        },
        {
            "Check": "RecentTurnover",
            "Passed": _lte(float(summary.get("recent_avg_turnover", 0.0)), 1.50),
            "Value": float(summary.get("recent_avg_turnover", 0.0)),
            "Threshold": "<=1.50",
        },
        {
            "Check": "TransitionTurnover",
            "Passed": _lte(float(transition.get("weight_turnover", 0.0)), 0.20),
            "Value": float(transition.get("weight_turnover", 0.0)),
            "Threshold": "<=0.20",
        },
    ]

    verdict = "GO" if all(row["Passed"] for row in checks) else "HOLD"
    payload = {
        "baseline_variant": summary.get("baseline_variant"),
        "live_readiness_verdict": verdict,
        "checks_passed": sum(1 for row in checks if row["Passed"]),
        "checks_total": len(checks),
        "current_holdings": summary.get("current_holdings"),
        "current_dominant_sector": summary.get("current_dominant_sector"),
        "transition_weight_turnover": transition.get("weight_turnover"),
        "actionable_rows": execution.get("actionable_rows"),
        "checks": checks,
    }

    (SHADOW_DIR / "shadow_live_readiness.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"live_readiness_verdict={verdict}")
    print(f"checks_passed={payload['checks_passed']}/{payload['checks_total']}")


if __name__ == "__main__":
    main()
