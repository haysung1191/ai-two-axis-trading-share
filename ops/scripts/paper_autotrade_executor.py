from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\AI")
sys.path.insert(0, str(ROOT))

from verified_data_guard import verified_data_guard_status

OPS = ROOT / "ops"
REGISTRY_DB = OPS / "registry" / "ops_registry.sqlite"
REPORTS = OPS / "reports"
PAPER_DIR = OPS / "paper_autotrade"
ACTIVATION_PACKET = ROOT / "overnight_runs" / "small_autotrade_activation_packet_latest.json"
SHADOW_CONTROL = REPORTS / "shadow_control_plane_latest.json"
KILL_SWITCH = OPS / "runstate" / "kill_switch.json"
GLOBAL_DISABLE = OPS / "runstate" / "DISABLE_ALL_TRADING"
BROKER_PAPER_POLICY = OPS / "runstate" / "broker_paper_policy.json"
STOCK_PLAN = ROOT / "momentum" / "output" / "split_models_shadow" / "shadow_live_initial_adaptive_plan_1000000.csv"

BTC_CURRENT_CONTRACT = "crypto.shadow.bridge_28_relief_current_signal_source"


def utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def latest_shadow_payload(order_intent_id: str) -> dict[str, Any]:
    if not REGISTRY_DB.exists() or not order_intent_id:
        return {}
    with sqlite3.connect(REGISTRY_DB) as conn:
        row = conn.execute(
            """
            SELECT payload_json
            FROM execution_events
            WHERE event_type='ShadowIntentPlanned' AND order_intent_id=?
            ORDER BY created_at_utc DESC
            LIMIT 1
            """,
            (order_intent_id,),
        ).fetchone()
    return json.loads(row[0]) if row else {}


def current_positions() -> dict[str, float]:
    report = read_json(PAPER_DIR / "paper_autotrade_latest.json", default={})
    positions = report.get("simulated_positions") if isinstance(report, dict) else {}
    if not isinstance(positions, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in positions.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            out[str(key)] = 0.0
    return out


def broker_paper_policy() -> dict[str, Any]:
    policy = read_json(BROKER_PAPER_POLICY, default={})
    return policy if isinstance(policy, dict) else {}


def broker_paper_allowed(policy: dict[str, Any], kill_switch: dict[str, Any]) -> bool:
    return (
        policy.get("policy_mode") == "paper_only"
        and policy.get("paper_enabled") is True
        and policy.get("broker_submit_allowed") is True
        and policy.get("broker_submit_scope") == "paper_only"
        and policy.get("live_enabled") is False
        and kill_switch.get("live_enabled") is not True
    )


def target_from_crypto_sleeve(sleeve: dict[str, Any], shadow_payload: dict[str, Any]) -> dict[str, Any]:
    signal = shadow_payload.get("signal") or {}
    decision = shadow_payload.get("risk_decision") or {}
    intent = shadow_payload.get("order_intent") or {}
    sleeve_weight = float(sleeve.get("target_weight") or 0.0)
    signal_target = float(signal.get("target_weight") or 0.0)
    approved = (
        decision.get("decision") == "approved_shadow_intent"
        and intent.get("status") == "shadow_planned_no_submit"
        and intent.get("broker_submit_allowed") is False
    )
    if not approved:
        target = 0.0
        reason = "crypto_shadow_signal_not_approved"
    elif signal.get("side") == "flat" or signal_target <= 0:
        target = 0.0
        reason = "btc_model_signal_flat"
    else:
        target = min(sleeve_weight, signal_target)
        reason = "btc_model_signal_long_contract_cap_applied"
    return {
        "asset": "crypto",
        "symbol": signal.get("market") or "KRW-BTC",
        "variant": sleeve.get("variant"),
        "sleeve_weight": sleeve_weight,
        "signal_target_weight": signal_target,
        "target_account_weight": target,
        "signal_side": signal.get("side"),
        "signal_id": signal.get("signal_id"),
        "reason": reason,
        "executable": approved,
    }


def targets_from_stock_sleeve(sleeve: dict[str, Any]) -> list[dict[str, Any]]:
    sleeve_weight = float(sleeve.get("target_weight") or 0.0)
    if not STOCK_PLAN.exists():
        return [
            {
                "asset": "stock",
                "symbol": "KIS_STOCK_BASKET",
                "variant": sleeve.get("variant"),
                "sleeve_weight": sleeve_weight,
                "signal_target_weight": None,
                "target_account_weight": 0.0,
                "signal_side": "not_wired",
                "signal_id": None,
                "reason": "stock_plan_missing",
                "executable": False,
            }
        ]
    with STOCK_PLAN.open("r", encoding="utf-8-sig", newline="") as f:
        rows = [
            row
            for row in csv.DictReader(f)
            if row.get("ExecutionSide") == "BUY" and row.get("Status") == "PLANNED"
        ]
    total_notional = sum(float(row.get("EstimatedOrderNotionalKRW") or 0.0) for row in rows)
    if not rows or total_notional <= 0:
        return [
            {
                "asset": "stock",
                "symbol": "KIS_STOCK_BASKET",
                "variant": sleeve.get("variant"),
                "sleeve_weight": sleeve_weight,
                "signal_target_weight": None,
                "target_account_weight": 0.0,
                "signal_side": "flat",
                "signal_id": None,
                "reason": "stock_plan_has_no_planned_buys",
                "executable": True,
            }
        ]
    targets: list[dict[str, Any]] = []
    for row in rows:
        notional = float(row.get("EstimatedOrderNotionalKRW") or 0.0)
        target = sleeve_weight * notional / total_notional
        targets.append(
            {
                "asset": "stock",
                "symbol": row.get("ResolvedSymbol") or row.get("Symbol"),
                "variant": sleeve.get("variant"),
                "sleeve_weight": sleeve_weight,
                "signal_target_weight": notional / total_notional,
                "target_account_weight": target,
                "signal_side": "long",
                "signal_id": f"stock_plan:{STOCK_PLAN.name}",
                "reason": "stock_shadow_plan_buy_allocated_to_sleeve",
                "executable": True,
                "source_plan": str(STOCK_PLAN),
                "estimated_order_notional_krw": notional,
                "quantity": row.get("Quantity"),
                "resolved_price": row.get("ResolvedPrice"),
            }
        )
    return targets


PAPER_COLLECTION_BLOCKERS = {
    "paper_promotion_evidence_not_ready",
    "paper_promotion_evidence_has_gaps",
}


def approved_paper_collection(activation: dict[str, Any], allow_approved_paper_collection: bool) -> bool:
    activation_blockers = set(str(item) for item in (activation.get("blockers") or []))
    return (
        allow_approved_paper_collection
        and activation.get("status") == "blocked"
        and bool(activation_blockers)
        and activation_blockers <= PAPER_COLLECTION_BLOCKERS
    )


def build_report(*, activate: bool, asset_scope: str, allow_approved_paper_collection: bool = False) -> dict[str, Any]:
    activation = read_json(ACTIVATION_PACKET)
    shadow_control = read_json(SHADOW_CONTROL)
    kill_switch = read_json(KILL_SWITCH)
    policy = broker_paper_policy()
    verified_guard = verified_data_guard_status()
    policy_allows_broker_paper = broker_paper_allowed(policy, kill_switch) and not verified_guard["active"]
    paper_collection_approved = approved_paper_collection(activation, allow_approved_paper_collection)
    blockers: list[str] = []
    if verified_guard["active"]:
        blockers.extend(f"verified_data_guard:{item}" for item in verified_guard["blockers"])
    if activation.get("status") != "ready_for_explicit_paper_activation" and not paper_collection_approved:
        blockers.append("activation_packet_not_ready")
    if activation.get("blockers") and not paper_collection_approved:
        blockers.append("activation_packet_has_blockers")
    global_disable_file_present = GLOBAL_DISABLE.exists()
    if kill_switch.get("live_enabled"):
        blockers.append("live_enabled_unexpectedly")
    if shadow_control.get("contract_count") != 1 or shadow_control.get("planned_count") != 1:
        blockers.append("shadow_control_not_single_current_source")
    if shadow_control.get("include_pending_validation") is not False:
        blockers.append("pending_validation_included")

    outputs = shadow_control.get("outputs") or []
    shadow_payload = latest_shadow_payload(str(outputs[0].get("order_intent_id"))) if outputs else {}
    strategy = activation.get("selected_strategy") or {}
    targets: list[dict[str, Any]] = []
    for sleeve in strategy.get("sleeves") or []:
        repo = sleeve.get("repo")
        if asset_scope in {"all", "crypto"} and repo == "crypto" and sleeve.get("variant") == "bridge_28_relief":
            targets.append(target_from_crypto_sleeve(sleeve, shadow_payload))
        elif asset_scope in {"all", "stock"} and repo == "momentum":
            targets.extend(targets_from_stock_sleeve(sleeve))

    all_positions = current_positions()
    target_symbols = {str(target["symbol"]) for target in targets}
    positions = all_positions if asset_scope == "all" else {k: v for k, v in all_positions.items() if k in target_symbols}
    simulated_orders = []
    next_positions = dict(positions)
    for target in targets:
        symbol = str(target["symbol"])
        current_weight = float(positions.get(symbol, 0.0))
        target_weight = float(target["target_account_weight"] or 0.0)
        delta = target_weight - current_weight
        action = "HOLD" if abs(delta) < 1e-9 else "BUY" if delta > 0 else "SELL"
        order = {
            "symbol": symbol,
            "asset": target["asset"],
            "variant": target["variant"],
            "action": action,
            "current_weight": current_weight,
            "target_weight": target_weight,
            "delta_weight": delta,
            "signal_id": target.get("signal_id"),
            "reason": target["reason"],
            "executable": bool(target["executable"]),
            "real_order_submitted": False,
            "broker_submit_allowed": bool(
                policy_allows_broker_paper
                and target["executable"]
                and action in {"BUY", "SELL"}
                and abs(delta) >= 1e-9
            ),
            "broker_submit_scope": "paper_only" if policy_allows_broker_paper else "disabled",
        }
        simulated_orders.append(order)
        if activate and not blockers and target["executable"]:
            next_positions[symbol] = target_weight

    mode = "paper_autotrade_active_simulated" if activate else "paper_autotrade_plan"
    status = "blocked" if blockers else "pass"
    return {
        "generated_at_utc": utc_now(),
        "mode": mode,
        "status": status,
        "activate_requested": activate,
        "asset_scope": asset_scope,
        "blockers": blockers,
        "paper_collection_approval": {
            "approved": paper_collection_approved,
            "approval_text_stored": False,
            "allowed_blockers": sorted(PAPER_COLLECTION_BLOCKERS),
        },
        "profile": activation.get("profile"),
        "paper_enabled_flag": bool(kill_switch.get("paper_enabled")),
        "live_enabled_flag": bool(kill_switch.get("live_enabled")),
        "broker_paper_policy": {
            "policy_file": str(BROKER_PAPER_POLICY),
            "paper_enabled": bool(policy.get("paper_enabled")),
            "broker_submit_allowed": bool(policy.get("broker_submit_allowed")),
            "broker_submit_scope": policy.get("broker_submit_scope"),
            "policy_allows_broker_paper": policy_allows_broker_paper,
        },
        "verified_data_guard": verified_guard,
        "broker_submit_allowed": policy_allows_broker_paper,
        "broker_submit_scope": "paper_only" if policy_allows_broker_paper else "disabled",
        "real_orders": 0,
        "private_submit_used": False,
        "global_disable_file_present": global_disable_file_present,
        "selected_strategy": {
            "cash_weight": strategy.get("cash_weight"),
            "model_weight": strategy.get("total_model_weight"),
            "expected_account_cagr_linear": strategy.get("expected_account_cagr_linear"),
            "conservative_account_mdd_sum": strategy.get("conservative_account_mdd_sum"),
        },
        "targets": targets,
        "simulated_orders": simulated_orders,
        "simulated_positions": next_positions if activate and not blockers else positions,
        "note": "Paper-only policy may allow broker-paper routing for nonzero orders; live trading remains disabled.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    strategy = report["selected_strategy"]
    lines = [
        "# Paper Autotrade Executor",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- mode: `{report['mode']}`",
        f"- status: `{report['status']}`",
        f"- profile: `{report['profile']}`",
        f"- broker_submit_allowed: `{report['broker_submit_allowed']}`",
        f"- broker_submit_scope: `{report.get('broker_submit_scope')}`",
        f"- verified_data_guard_active: `{report.get('verified_data_guard', {}).get('active')}`",
        f"- real_orders: `{report['real_orders']}`",
        f"- expected_account_cagr_linear: `{pct(strategy.get('expected_account_cagr_linear'))}`",
        f"- conservative_account_mdd_sum: `-{pct(strategy.get('conservative_account_mdd_sum'))}`",
        "",
        "## Orders",
        "",
    ]
    for order in report["simulated_orders"]:
        lines.append(
            f"- `{order['symbol']}` `{order['action']}` | current=`{pct(order['current_weight'])}` | "
            f"target=`{pct(order['target_weight'])}` | delta=`{pct(order['delta_weight'])}` | "
            f"reason=`{order['reason']}` | executable=`{order['executable']}` | "
            f"broker_submit_allowed=`{order.get('broker_submit_allowed')}`"
        )
    lines.extend(["", "## Blockers", ""])
    if report["blockers"]:
        lines.extend(f"- `{item}`" for item in report["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", report["note"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activate", action="store_true", help="Persist paper positions.")
    parser.add_argument(
        "--allow-approved-paper-collection",
        action="store_true",
        help="Allow active local paper cycle collection when the exact approval was already verified by the runner.",
    )
    parser.add_argument(
        "--asset-scope",
        choices=["all", "crypto", "stock"],
        default="all",
        help="Limit paper automation targets. Broker submission can be paper-only if broker_paper_policy allows it.",
    )
    args = parser.parse_args()
    report = build_report(
        activate=args.activate,
        asset_scope=args.asset_scope,
        allow_approved_paper_collection=args.allow_approved_paper_collection,
    )
    suffix = "latest" if args.activate else "plan_latest"
    json_path = PAPER_DIR / f"paper_autotrade_{suffix}.json"
    md_path = PAPER_DIR / f"paper_autotrade_{suffix}.md"
    report_json = REPORTS / f"paper_autotrade_{suffix}.json"
    report_md = REPORTS / f"paper_autotrade_{suffix}.md"
    for path in [json_path, report_json]:
        write_json(path, report)
    markdown = render_markdown(report)
    for path in [md_path, report_md]:
        path.write_text(markdown, encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(json_path),
                "markdown": str(md_path),
                "status": report["status"],
                "mode": report["mode"],
                "orders": len(report["simulated_orders"]),
                "real_orders": report["real_orders"],
                "broker_submit_allowed": report["broker_submit_allowed"],
                "broker_submit_scope": report.get("broker_submit_scope"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
