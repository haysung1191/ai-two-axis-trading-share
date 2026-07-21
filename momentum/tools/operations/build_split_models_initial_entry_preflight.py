from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config
import pandas as pd


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"
RUNTIME_STATUS_PATH = SHADOW_DIR / "shadow_operator_runtime_status.json"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_preflight_payload(
    runtime_status: dict[str, object],
    execution_summary: dict[str, object],
    execution_plan: pd.DataFrame,
) -> dict[str, object]:
    failures: list[str] = []

    if config.ENV != "PROD":
        failures.append(f"KIS_ENV={config.ENV}")
    if runtime_status.get("live_readiness") != "GO":
        failures.append(f"live_readiness={runtime_status.get('live_readiness')}")
    if runtime_status.get("operator_gate_verdict") != "PASS":
        failures.append(f"operator_gate_verdict={runtime_status.get('operator_gate_verdict')}")
    if execution_summary.get("submit_mode") != "dry_run":
        failures.append(f"submit_mode={execution_summary.get('submit_mode')}")
    if int(execution_summary.get("planned_count", 0)) <= 0:
        failures.append("planned_count=0")
    if int(execution_summary.get("skipped_count", 0)) != 0:
        failures.append(f"skipped_count={execution_summary.get('skipped_count')}")

    planned = execution_plan[execution_plan["Status"] == "PLANNED"].copy()
    markets = sorted(planned["Market"].dropna().astype(str).unique().tolist()) if not planned.empty else []
    symbols = planned["Symbol"].dropna().astype(str).tolist() if not planned.empty else []
    quantity_total = int(pd.to_numeric(planned["Quantity"], errors="coerce").fillna(0).sum()) if not planned.empty else 0
    estimated_total_krw = (
        float(pd.to_numeric(planned["EstimatedOrderNotionalKRW"], errors="coerce").fillna(0.0).sum())
        if not planned.empty
        else 0.0
    )

    payload = {
        "preflight_verdict": "PASS" if not failures else "FAIL",
        "preflight_failures": failures,
        "kis_env": config.ENV,
        "live_readiness": runtime_status.get("live_readiness"),
        "operator_gate_verdict": runtime_status.get("operator_gate_verdict"),
        "archive_stability_verdict": runtime_status.get("archive_stability_verdict"),
        "plan_mode": execution_summary.get("plan_mode"),
        "submit_mode": execution_summary.get("submit_mode"),
        "planned_count": int(execution_summary.get("planned_count", 0)),
        "skipped_count": int(execution_summary.get("skipped_count", 0)),
        "adaptive_selection_enabled": bool(execution_summary.get("adaptive_selection_enabled", False)),
        "adaptive_selected_symbols": execution_summary.get("adaptive_selected_symbols", []),
        "planned_markets": markets,
        "planned_symbols": symbols,
        "planned_quantity_total": quantity_total,
        "estimated_order_notional_krw_total": estimated_total_krw,
    }
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-status-path", default=str(RUNTIME_STATUS_PATH))
    parser.add_argument("--execution-summary-path", required=True)
    parser.add_argument("--execution-plan-path", required=True)
    parser.add_argument("--out-path", required=True)
    args = parser.parse_args(argv)

    runtime_status = _load_json(Path(args.runtime_status_path))
    execution_summary = _load_json(Path(args.execution_summary_path))
    execution_plan = pd.read_csv(Path(args.execution_plan_path))

    summary_path = Path(args.execution_summary_path)
    plan_path = Path(args.execution_plan_path)
    payload = build_preflight_payload(runtime_status, execution_summary, execution_plan)
    payload["execution_summary_path"] = str(summary_path)
    payload["execution_plan_path"] = str(plan_path)
    payload["execution_plan_sha256"] = _sha256_file(plan_path)
    payload["execution_summary_sha256"] = _sha256_file(summary_path)
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"preflight_path={out_path}")
    print(f"preflight_verdict={payload['preflight_verdict']}")


if __name__ == "__main__":
    main()
