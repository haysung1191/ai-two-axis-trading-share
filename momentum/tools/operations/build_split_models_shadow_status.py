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
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _load_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return _load_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return _load_json(path)


def derive_operator_gate(payload: dict[str, object]) -> tuple[str, list[str]]:
    failures: list[str] = []
    if payload.get("live_readiness") != "GO":
        failures.append(f"live_readiness={payload.get('live_readiness')}")
    if payload.get("health_verdict") != "PASS":
        failures.append(f"health_verdict={payload.get('health_verdict')}")
    if payload.get("drift_verdict") != "PASS":
        failures.append(f"drift_verdict={payload.get('drift_verdict')}")
    if payload.get("archive_consistency_verdict") != "PASS":
        failures.append(f"archive_consistency_verdict={payload.get('archive_consistency_verdict')}")
    if payload.get("archive_timeline_verdict") != "PASS":
        failures.append(f"archive_timeline_verdict={payload.get('archive_timeline_verdict')}")
    verdict = "PASS" if not failures else "FAIL"
    return verdict, failures


def build_status_payload() -> dict[str, object]:
    summary = _load_json(SHADOW_DIR / "shadow_summary.json")
    backtest = _load_json(SHADOW_DIR / "split_models_backtest_summary.json")
    drift = _load_json(SHADOW_DIR / "shadow_drift_report.json")
    readiness = _load_json(SHADOW_DIR / "shadow_live_readiness.json")
    transition = _load_json(SHADOW_DIR / "shadow_live_transition_summary.json")
    execution = _load_json(SHADOW_DIR / "shadow_rebalance_execution_summary.json")
    market_summary = _load_optional_csv(SHADOW_DIR / "shadow_rebalance_market_summary.csv")
    archive_delta = _load_optional_json(ARCHIVE_DIR / "archive_latest_delta.json")
    archive_consistency = _load_optional_json(ARCHIVE_DIR / "archive_consistency_report.json")
    archive_stability = _load_optional_json(ARCHIVE_DIR / "archive_stability_report.json")
    archive_timeline = _load_optional_json(ARCHIVE_DIR / "archive_timeline_report.json")

    trading_book = backtest.get("trading_book", {})
    payload: dict[str, object] = {
        "baseline_variant": summary.get("baseline_variant"),
        "live_readiness": readiness.get("live_readiness_verdict"),
        "health_verdict": summary.get("health_verdict"),
        "drift_verdict": drift.get("drift_verdict"),
        "current_holdings": summary.get("current_holdings"),
        "dominant_sector": summary.get("current_dominant_sector"),
        "cagr": float(trading_book.get("CAGR", 0.0)),
        "mdd": float(trading_book.get("MDD", 0.0)),
        "sharpe": float(trading_book.get("Sharpe", 0.0)),
        "transition_turnover": float(transition.get("weight_turnover", 0.0)),
        "actionable_rows": execution.get("actionable_rows"),
        "archive_comparison_available": archive_delta.get("comparison_available", False),
        "archive_latest_run_id": archive_delta.get("latest_run_id"),
        "archive_prior_run_id": archive_delta.get("prior_run_id"),
        "archive_holdings_change": archive_delta.get("holdings_change"),
        "archive_dominant_sector_changed": archive_delta.get("dominant_sector_changed"),
        "archive_live_readiness_changed": archive_delta.get("live_readiness_changed"),
        "archive_operator_gate_changed": archive_delta.get("operator_gate_changed"),
        "archive_transition_turnover_change": archive_delta.get("transition_turnover_change"),
        "archive_consistency_verdict": archive_consistency.get("archive_consistency_verdict"),
        "archive_consistency_latest_run_id": archive_consistency.get("latest_run_id"),
        "archive_stability_verdict": archive_stability.get("archive_stability_verdict"),
        "archive_stability_window": archive_stability.get("window"),
        "archive_stability_latest_run_id": archive_stability.get("latest_run_id"),
        "archive_timeline_verdict": archive_timeline.get("archive_timeline_verdict"),
        "archive_timeline_window": archive_timeline.get("window"),
        "archive_timeline_latest_run_id": archive_timeline.get("latest_run_id"),
    }
    for _, row in market_summary.iterrows():
        payload[f"market_{row['Market']}_{row['ExecutionSide'].lower()}_orders"] = int(row["OrderCount"])
    operator_gate_verdict, operator_gate_failures = derive_operator_gate(payload)
    payload["operator_gate_verdict"] = operator_gate_verdict
    payload["operator_gate_failures"] = operator_gate_failures
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-runtime-status", action="store_true")
    args = parser.parse_args(argv)

    payload = build_status_payload()
    if args.write_runtime_status:
        runtime_status_path = SHADOW_DIR / "shadow_operator_runtime_status.json"
        runtime_status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"baseline_variant={payload['baseline_variant']}")
    print(f"live_readiness={payload['live_readiness']}")
    print(f"health_verdict={payload['health_verdict']}")
    print(f"drift_verdict={payload['drift_verdict']}")
    print(f"current_holdings={payload['current_holdings']}")
    print(f"dominant_sector={payload['dominant_sector']}")
    print(f"cagr={float(payload['cagr']):.4f}")
    print(f"mdd={float(payload['mdd']):.4f}")
    print(f"sharpe={float(payload['sharpe']):.4f}")
    print(f"transition_turnover={float(payload['transition_turnover']):.6f}")
    print(f"actionable_rows={payload['actionable_rows']}")
    print(f"operator_gate_verdict={payload['operator_gate_verdict']}")
    if payload["operator_gate_failures"]:
        print(f"operator_gate_failures={' | '.join(str(item) for item in payload['operator_gate_failures'])}")
    print(f"archive_comparison_available={payload['archive_comparison_available']}")
    print(f"archive_consistency_verdict={payload['archive_consistency_verdict']}")
    print(f"archive_stability_verdict={payload['archive_stability_verdict']}")
    print(f"archive_timeline_verdict={payload['archive_timeline_verdict']}")
    if payload["archive_comparison_available"]:
        print(f"archive_latest_run_id={payload['archive_latest_run_id']}")
        print(f"archive_prior_run_id={payload['archive_prior_run_id']}")
        print(f"archive_holdings_change={payload['archive_holdings_change']}")
        print(f"archive_dominant_sector_changed={payload['archive_dominant_sector_changed']}")
        print(f"archive_live_readiness_changed={payload['archive_live_readiness_changed']}")
        print(f"archive_operator_gate_changed={payload['archive_operator_gate_changed']}")
        print(f"archive_transition_turnover_change={payload['archive_transition_turnover_change']}")
    if payload["archive_consistency_latest_run_id"] is not None:
        print(f"archive_consistency_latest_run_id={payload['archive_consistency_latest_run_id']}")
    if payload["archive_stability_latest_run_id"] is not None:
        print(f"archive_stability_latest_run_id={payload['archive_stability_latest_run_id']}")
        print(f"archive_stability_window={payload['archive_stability_window']}")
    if payload["archive_timeline_latest_run_id"] is not None:
        print(f"archive_timeline_latest_run_id={payload['archive_timeline_latest_run_id']}")
        print(f"archive_timeline_window={payload['archive_timeline_window']}")

    for key, value in payload.items():
        if key.startswith("market_"):
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
