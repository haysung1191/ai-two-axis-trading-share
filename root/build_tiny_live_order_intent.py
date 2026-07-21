from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ops.broker_gateway import build_order_intent, evaluate_order_intent


ROOT = Path(r"C:\AI")
RUNSTATE = ROOT / "ops" / "runstate"
INTENTS = ROOT / "ops" / "orders" / "intents"
REPORTS = ROOT / "reports" / "operations"
CRYPTO_RESULTS = ROOT / "Crypto" / "analysis_results"

SIGNAL_JSON = REPORTS / "bithumb_current_actionable_nonzero_signal_scout_latest.json"
POLICY_JSON = RUNSTATE / "limited_live_policy.json"
INTENT_JSON = INTENTS / "tiny_live_order_intent_latest.json"
PLAN_JSON = CRYPTO_RESULTS / "bithumb_tiny_live_execution_plan_latest.json"
REPORT_JSON = REPORTS / "tiny_live_order_intent_pretrade_latest.json"
REPORT_MD = REPORTS / "tiny_live_order_intent_pretrade_latest.md"
GLOBAL_DISABLE = RUNSTATE / "DISABLE_ALL_TRADING"

MIN_BITHUMB_MARKET_BUY_KRW = 5000.0
DEFAULT_TINY_ORDER_KRW = 10000.0


def utc_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_live_approval(text: str) -> dict[str, float]:
    match = re.fullmatch(r"LIVE APPROVE\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)", text.strip())
    if not match:
        raise ValueError("approval must match: LIVE APPROVE <max_krw> <max_daily_loss_krw> <max_total_loss_krw>")
    max_krw, max_daily_loss_krw, max_total_loss_krw = (float(value) for value in match.groups())
    return {
        "max_krw": max_krw,
        "max_order_krw": max_krw,
        "max_daily_loss_krw": max_daily_loss_krw,
        "max_total_loss_krw": max_total_loss_krw,
    }


def approval_text(caps: dict[str, Any]) -> str:
    return (
        f"LIVE APPROVE {int(float(caps['max_krw']))} "
        f"{int(float(caps['max_daily_loss_krw']))} "
        f"{int(float(caps['max_total_loss_krw']))}"
    )


def build_policy(caps: dict[str, Any], *, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or utc_now()
    max_krw = float(caps["max_krw"])
    max_order_krw = float(caps.get("max_order_krw", max_krw))
    return {
        "generated_at_utc": generated_at_utc,
        "profile": "tiny_live_hard_cap",
        "policy_mode": "limited_live",
        "paper_enabled": False,
        "live_enabled": True,
        "broker_submit_allowed": True,
        "broker_submit_scope": "limited_live",
        "private_submit_used": False,
        "real_orders_allowed": True,
        "max_krw": max_krw,
        "crypto_cap_krw": max_krw,
        "stock_cap_krw": 0.0,
        "max_order_krw": max_order_krw,
        "max_daily_loss_krw": float(caps["max_daily_loss_krw"]),
        "max_total_loss_krw": float(caps["max_total_loss_krw"]),
        "approval_text": approval_text(
            {
                "max_krw": max_krw,
                "max_daily_loss_krw": caps["max_daily_loss_krw"],
                "max_total_loss_krw": caps["max_total_loss_krw"],
            }
        ),
        "notes": [
            "Created from exact operator LIVE APPROVE phrase.",
            "This policy is only a hard-cap firewall input; broker endpoint submission is blocked while DISABLE_ALL_TRADING exists.",
        ],
    }


def top_signal(signal_payload: dict[str, Any]) -> dict[str, Any]:
    candidate = signal_payload.get("top_triggered_candidate") or {}
    if not candidate.get("candidate_id") or not candidate.get("market"):
        raise ValueError("no top triggered Bithumb candidate is available")
    if not candidate.get("signal", {}).get("triggered"):
        raise ValueError("top Bithumb candidate does not have a current nonzero signal")
    return candidate


def tiny_notional(policy: dict[str, Any]) -> float:
    max_order = float(policy["max_order_krw"])
    max_total = float(policy["max_krw"])
    amount = min(DEFAULT_TINY_ORDER_KRW, max_order, max_total)
    if amount < MIN_BITHUMB_MARKET_BUY_KRW:
        raise ValueError("MAX_ORDER_KRW_BELOW_BITHUMB_MINIMUM")
    return amount


def build_intent(candidate: dict[str, Any], policy: dict[str, Any], *, created_at_utc: str | None = None) -> dict[str, Any]:
    created_at_utc = created_at_utc or utc_now()
    notional = tiny_notional(policy)
    market = str(candidate["market"]).upper()
    signal = candidate.get("signal", {}) or {}
    signal_id = f"{candidate['candidate_id']}:{market}:{signal.get('latest_close')}:{created_at_utc}"
    return build_order_intent(
        intent_id="",
        candidate_id=candidate["candidate_id"],
        mode="limited_live",
        asset_class="crypto",
        venue="bithumb",
        account_scope=policy["profile"],
        symbol=market,
        side="BUY",
        order_type="market",
        quantity=0,
        notional_krw=notional,
        created_at_utc=created_at_utc,
        signal_id=signal_id,
        approval_packet_id=policy["approval_text"],
        gatekeeper_permission="APPROVED_TINY_LIVE",
        broker_submit_scope="limited_live",
        producer_lane="operations",
        evidence_source="live_bithumb_public_api",
        market=market,
        quote_amount_krw=notional,
        source_signal=signal,
    )


def build_execution_plan(intent: dict[str, Any], candidate: dict[str, Any], *, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or utc_now()
    return {
        "schema_version": "1.0.0",
        "run_id": f"tiny-live-{intent['intent_id'][:12]}",
        "generated_at_utc": generated_at_utc,
        "strategy_track": "bithumb_current_actionable_orca_tiny_live",
        "candidate_id": intent["candidate_id"],
        "candle_close_utc": candidate.get("signal", {}).get("latest_timestamp"),
        "order_intents": [
            {
                "symbol": str(intent["symbol"]).replace("KRW-", ""),
                "market": intent["market"],
                "side": "BUY",
                "order_type": "market",
                "quote_amount_krw": intent["quote_amount_krw"],
                "source_intent_id": intent["intent_id"],
            }
        ],
        "standard_check_order_reference": ["practical", "research", "contract", "brief"],
    }


def build_report(approval: str, *, write: bool = False) -> dict[str, Any]:
    generated_at_utc = utc_now()
    caps = parse_live_approval(approval)
    policy = build_policy(caps, generated_at_utc=generated_at_utc)
    signal_payload = read_json(SIGNAL_JSON, {})
    candidate = top_signal(signal_payload)
    intent = build_intent(candidate, policy, created_at_utc=generated_at_utc)
    plan = build_execution_plan(intent, candidate, generated_at_utc=generated_at_utc)
    firewall = evaluate_order_intent(intent, policy, kill_switch={"live_enabled": True})
    global_disable_present = GLOBAL_DISABLE.exists()
    broker_submit_attempt_status = "BLOCKED_BY_GLOBAL_DISABLE" if global_disable_present else "READY_FOR_EXPLICIT_SUBMIT_CALL"
    report = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "approval_text": approval,
        "candidate_id": candidate["candidate_id"],
        "market": candidate["market"],
        "notional_krw": intent["notional_krw"],
        "policy_path": str(POLICY_JSON),
        "intent_path": str(INTENT_JSON),
        "execution_plan_path": str(PLAN_JSON),
        "firewall": {
            "decision": firewall.decision,
            "reason": firewall.reason,
            "broker_endpoint_allowed": firewall.broker_endpoint_allowed,
            "safety_state_hash": firewall.safety_state_hash,
            "approval_packet_id": firewall.approval_packet_id,
            "risk_caps_hash": firewall.risk_caps_hash,
        },
        "global_disable_present": global_disable_present,
        "broker_submit_attempt_status": broker_submit_attempt_status,
        "submitted_order_count": 0,
        "private_submit_used": False,
        "real_orders": 0,
        "safety": {
            "paper_enabled": False,
            "live_enabled": True,
            "broker_submit_allowed": True,
            "private_submit_used": False,
            "real_orders": 0,
            "order_intent_created": True,
            "pretrade_firewall_default_decision": firewall.decision,
        },
    }
    if write:
        write_json(POLICY_JSON, policy)
        write_json(INTENT_JSON, intent)
        write_json(PLAN_JSON, plan)
        write_json(REPORT_JSON, report)
        REPORT_MD.write_text(render_md(report), encoding="utf-8")
    return report


def render_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Tiny Live Order Intent Pretrade",
            "",
            f"- Candidate: `{report['candidate_id']}`",
            f"- Market: `{report['market']}`",
            f"- Notional KRW: `{report['notional_krw']}`",
            f"- Firewall: `{report['firewall']['decision']}` / `{report['firewall']['reason']}`",
            f"- Broker submit attempt: `{report['broker_submit_attempt_status']}`",
            f"- Global disable present: `{report['global_disable_present']}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report(args.approval, write=args.write)
    print(
        json.dumps(
            {
                "firewall_decision": report["firewall"]["decision"],
                "firewall_reason": report["firewall"]["reason"],
                "broker_submit_attempt_status": report["broker_submit_attempt_status"],
                "notional_krw": report["notional_krw"],
                "latest_json": str(REPORT_JSON),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["firewall"]["decision"] == "ALLOW_LIMITED_LIVE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
