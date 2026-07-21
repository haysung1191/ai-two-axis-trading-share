from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MOMENTUM_ROOT = ROOT / "momentum"
OPS_DIR = ROOT / "ops" / "stock_etf_axis_operation"
LATEST_PATH = OPS_DIR / "stock_etf_axis_operation_latest.json"

LIMITED_LIVE_POLICY_PATH = ROOT / "ops" / "runstate" / "limited_live_policy.json"
BROKER_POLICY_PATH = ROOT / "ops" / "runstate" / "broker_paper_policy.json"
INVENTORY_PATH = ROOT / "reports" / "operations" / "two_axis_model_inventory_latest.json"
OP_CONVERSION_STATE_PATH = MOMENTUM_ROOT / "output" / "split_models_operational_conversion_current_state.json"
INITIAL_ENTRY_LATEST_PATH = MOMENTUM_ROOT / "output" / "split_models_shadow" / "shadow_live_initial_adaptive_latest.json"
BRIDGE_LATEST_PATH = ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_candidate_bridge_latest.json"
KIS_SUBMIT_LATEST_PATH = OPS_DIR / "kis_stock_etf_order_submit_latest.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_step(label: str, args: list[str], *, cwd: Path) -> dict[str, Any]:
    started = utc_now()
    result = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, check=False)
    return {
        "label": label,
        "command": args,
        "cwd": str(cwd),
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
        "ok": result.returncode == 0,
    }


def load_initial_entry_status() -> dict[str, Any]:
    latest = load_json(INITIAL_ENTRY_LATEST_PATH)
    check_path = latest.get("check_json_path")
    check = load_json(Path(str(check_path))) if check_path else {}
    return {
        "latest_index": latest,
        "check": check,
        "planned_count": int(check.get("planned_count", 0) or 0),
        "planned_symbols": list(check.get("planned_symbols", []) or []),
        "estimated_order_notional_krw_total": float(check.get("estimated_order_notional_krw_total", 0.0) or 0.0),
        "preflight_verdict": check.get("preflight_verdict"),
        "live_readiness": check.get("live_readiness"),
        "operator_gate_verdict": check.get("operator_gate_verdict"),
        "archive_stability_verdict": check.get("archive_stability_verdict"),
    }


def load_bridge_status() -> dict[str, Any]:
    return load_json(BRIDGE_LATEST_PATH)


def stock_submit_blockers(
    *,
    limited_live_policy: dict[str, Any],
    broker_policy: dict[str, Any],
    bridge_status: dict[str, Any] | None = None,
) -> list[str]:
    blockers: list[str] = []
    if bridge_status is not None:
        blockers.extend(list(bridge_status.get("blockers", []) or []))
    if float(limited_live_policy.get("stock_cap_krw", 0.0) or 0.0) <= 0.0:
        blockers.append("STOCK_CAP_KRW_ZERO")
    if not bool(broker_policy.get("broker_submit_allowed", False)):
        blockers.append("BROKER_POLICY_SUBMIT_BLOCKED")
    if not bool(broker_policy.get("live_enabled", False)):
        blockers.append("BROKER_POLICY_LIVE_DISABLED")
    if not bool(broker_policy.get("real_orders_allowed", False)):
        blockers.append("BROKER_POLICY_REAL_ORDERS_BLOCKED")
    return blockers


def kis_operation_status(*, submit_requested: bool, submit_allowed: bool, blockers: list[str]) -> str:
    if submit_requested:
        return "KIS_STOCK_ETF_LIVE_SUBMIT_READY" if submit_allowed else "KIS_STOCK_ETF_LIVE_SUBMIT_BLOCKED"
    return "KIS_STOCK_ETF_DAILY_PLAN_READY" if not blockers else "KIS_STOCK_ETF_DAILY_PLAN_BLOCKED"


def build_status(steps: list[dict[str, Any]], *, submit_requested: bool, submit_execution: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = load_json(INVENTORY_PATH)
    axis = ((inventory.get("axes") or {}).get("KIS_COMBINED_KRW") or {})
    limited_live_policy = load_json(LIMITED_LIVE_POLICY_PATH)
    broker_policy = load_json(BROKER_POLICY_PATH)
    op_state = load_json(OP_CONVERSION_STATE_PATH)
    bridge_status = load_bridge_status()
    blockers = stock_submit_blockers(
        limited_live_policy=limited_live_policy,
        broker_policy=broker_policy,
        bridge_status=bridge_status,
    )
    execution_warnings = list(bridge_status.get("execution_warnings", []) or [])
    submit_allowed = submit_requested and not blockers
    run_mode = "buy_submit" if submit_requested else "daily_close_plan"
    return {
        "generated_at_utc": utc_now(),
        "axis": "KIS_COMBINED_KRW",
        "status": kis_operation_status(
            submit_requested=submit_requested,
            submit_allowed=submit_allowed,
            blockers=blockers,
        ),
        "run_mode": run_mode,
        "submit_requested": bool(submit_requested),
        "submit_enabled": bool(submit_allowed),
        "next_submit_window_action": (
            "execute_kis_order_intents_once"
            if submit_allowed
            else ("await_next_buy_window" if not submit_requested and not blockers else "blocked_until_hard_gates_clear")
        ),
        "blockers": blockers,
        "execution_warnings": execution_warnings,
        "model_development_refreshed": all(step["ok"] for step in steps if step["label"] != "refresh initial entry plan"),
        "operation_plan_refreshed": any(step["label"] == "refresh operating candidate bridge" and step["ok"] for step in steps),
        "steps": steps,
        "universe": axis.get("universe", {}),
        "counts": axis.get("counts", {}),
        "leaders": axis.get("leaders", {}),
        "operational_conversion": {
            "gate_status": op_state.get("gate_status"),
            "promotion_status": op_state.get("promotion_status"),
            "recommended_representative_variant": op_state.get("recommended_representative_variant"),
            "operational_branch_ready_for_live_autotrade": op_state.get("operational_branch_ready_for_live_autotrade"),
            "execution_gate_verdict": op_state.get("execution_gate_verdict"),
        },
        "legacy_initial_entry_excluded": {
            "excluded": True,
            "reason": "shadow_live_initial_adaptive can select affordability-only symbols and is not a verified operating-candidate source",
            "latest_index_path": str(INITIAL_ENTRY_LATEST_PATH),
        },
        "operating_candidate_bridge": bridge_status,
        "kis_order_submit": submit_execution or load_json(KIS_SUBMIT_LATEST_PATH),
        "policy": {
            "limited_live_policy_path": str(LIMITED_LIVE_POLICY_PATH),
            "stock_cap_krw": limited_live_policy.get("stock_cap_krw"),
            "broker_policy_path": str(BROKER_POLICY_PATH),
            "broker_policy_mode": broker_policy.get("policy_mode"),
            "universe_validation_mode": bridge_status.get("universe_validation_mode"),
        },
        "output_path": str(LATEST_PATH),
    }


def write_status(payload: dict[str, Any]) -> None:
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true", help="Request KIS live submit if every hard blocker is clear.")
    parser.add_argument("--skip-model-refresh", action="store_true")
    parser.add_argument("--skip-operation-refresh", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    steps: list[dict[str, Any]] = []
    if not args.skip_model_refresh:
        steps.append(
            run_step(
                "refresh split model pipeline",
                [sys.executable, "tools/pipelines/run_split_models_pipeline.py"],
                cwd=MOMENTUM_ROOT,
            )
        )
        steps.append(
            run_step(
                "refresh operational conversion state",
                [sys.executable, "tools/analysis/refresh_split_models_operational_conversion_state.py"],
                cwd=MOMENTUM_ROOT,
            )
        )
    if not args.skip_operation_refresh:
        steps.append(
            run_step(
                "refresh operating candidate bridge",
                [sys.executable, str(ROOT / "build_stock_etf_operating_candidate_bridge.py"), "--format", "json"],
                cwd=ROOT,
            )
        )

    pre_payload = build_status(steps, submit_requested=args.submit)
    submit_execution: dict[str, Any] | None = None
    if pre_payload["submit_enabled"]:
        submit_step = run_step(
            "submit kis stock etf order intents",
            [sys.executable, str(ROOT / "submit_kis_stock_etf_order_intents.py"), "--execute", "--format", "json"],
            cwd=ROOT,
        )
        steps.append(submit_step)
        if submit_step["ok"]:
            submit_execution = load_json(KIS_SUBMIT_LATEST_PATH) or {
                "status": "KIS_ORDER_SUBMIT_RESULT_MISSING",
                "stdout_tail": submit_step["stdout_tail"],
            }
        else:
            submit_execution = {
                "status": "KIS_ORDER_SUBMIT_PROCESS_FAILED",
                "returncode": submit_step["returncode"],
                "stderr_tail": submit_step["stderr_tail"],
                "stdout_tail": submit_step["stdout_tail"],
            }

    payload = build_status(steps, submit_requested=args.submit, submit_execution=submit_execution)
    write_status(payload)

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return

    print(f"status={payload['status']}")
    print(f"submit_enabled={payload['submit_enabled']}")
    print(f"blockers={','.join(payload['blockers']) if payload['blockers'] else '-'}")
    bridge = payload.get("operating_candidate_bridge", {}) or {}
    target = bridge.get("target_book", {}) or {}
    print(f"candidate_id={bridge.get('candidate_id', '-')}")
    print(f"target_symbols={','.join(target.get('symbols', []) or []) or '-'}")
    print(f"gross_target_weight={float(target.get('gross_target_weight', 0.0) or 0.0):.4f}")
    print(f"output_path={LATEST_PATH}")


if __name__ == "__main__":
    main()
