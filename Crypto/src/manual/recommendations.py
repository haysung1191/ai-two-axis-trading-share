from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _iso_utc(ts_ms: int | None) -> str | None:
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


def build_manual_trade_recommendation(
    *,
    symbol: str,
    blocked_reason: str | None,
    trace_ctx: dict[str, Any],
) -> dict[str, Any]:
    feature_snapshot = trace_ctx.get("normalized_feature_snapshot", {})
    reference_price = _safe_float(feature_snapshot.get("close"))
    stop_dist = _safe_float(trace_ctx.get("suggested_stop_dist"))
    tp_dist = _safe_float(trace_ctx.get("suggested_tp_dist"))
    time_exit_ts_ms = _safe_int(trace_ctx.get("suggested_time_exit_ts_ms"))
    policy_result = trace_ctx.get("policy_result", {})
    policy_decision = str(policy_result.get("policy_decision", "NEUTRAL"))
    policy_delta = _safe_float(policy_result.get("policy_score_delta_capped")) or 0.0
    scheduled_due_to_policy = bool(trace_ctx.get("scheduled_due_to_policy"))
    near_miss_after_policy = bool(trace_ctx.get("near_miss_after_policy"))
    boosted_but_not_decisive = policy_decision == "BOOST" and policy_delta > 0.0 and not scheduled_due_to_policy

    stop_price = None
    take_profit_price = None
    if reference_price is not None and stop_dist is not None:
        stop_price = max(0.0, reference_price - stop_dist)
    if reference_price is not None and tp_dist is not None:
        take_profit_price = reference_price + tp_dist

    risk_reward_ratio = None
    if stop_dist and tp_dist and stop_dist > 0:
        risk_reward_ratio = tp_dist / stop_dist

    if policy_decision == "SOFT_REJECT":
        action = "NO_BUY"
        if blocked_reason == "POLICY_SOFT_REJECT":
            action_reason = "Policy soft reject marked this setup as unsafe."
        else:
            action_reason = "Policy soft reject was advisory in runtime, but manual entry is still not recommended."
        policy_materiality = "policy_reject"
    elif blocked_reason is None:
        action = "BUY"
        if scheduled_due_to_policy:
            action_reason = "Policy uplift moved this candidate inside the active entry cutoff."
            policy_materiality = "entry_reversal"
        elif boosted_but_not_decisive:
            action_reason = "Scheduled normally and reinforced by a positive policy boost."
            policy_materiality = "boosted_but_not_decisive"
        else:
            action_reason = "Scheduled by the baseline scanner without needing policy uplift."
            policy_materiality = "none"
    elif blocked_reason in {"MAX_CONCURRENT", "MAX_NEW_PER_DAY", "COOLDOWN"}:
        action = "HOLD"
        if near_miss_after_policy:
            action_reason = "Boosted candidate remained a near miss after policy but capacity timing blocked entry."
            policy_materiality = "near_miss"
        elif boosted_but_not_decisive:
            action_reason = "Boosted candidate remained valid, but capacity or cooldown guardrails blocked entry."
            policy_materiality = "boosted_but_not_decisive"
        else:
            action_reason = "Operational capacity or cooldown guardrail blocked entry despite a valid scan."
            policy_materiality = "none"
    elif blocked_reason == "BELOW_ENTRY_CUTOFF":
        if near_miss_after_policy:
            action = "HOLD"
            action_reason = "Boosted candidate remained just below the active entry cutoff after policy."
            policy_materiality = "near_miss"
        elif boosted_but_not_decisive:
            action = "HOLD"
            action_reason = "Boosted candidate improved but still finished below the active entry cutoff."
            policy_materiality = "boosted_but_not_decisive"
        else:
            action = "NO_BUY"
            action_reason = "Candidate ranked below the active entry cutoff."
            policy_materiality = "none"
    elif blocked_reason == "MARKET_DOWNTREND":
        action = "NO_BUY"
        action_reason = "Market regime filter blocked new long exposure."
        policy_materiality = "boosted_but_not_decisive" if boosted_but_not_decisive else "none"
    elif blocked_reason == "KILL_SWITCH":
        action = "NO_BUY"
        action_reason = "Daily kill switch blocked all new entries."
        policy_materiality = "boosted_but_not_decisive" if boosted_but_not_decisive else "none"
    elif blocked_reason == "BAD_STOP":
        action = "NO_BUY"
        action_reason = "Risk model could not form a valid stop distance."
        policy_materiality = "boosted_but_not_decisive" if boosted_but_not_decisive else "none"
    else:
        action = "NO_BUY"
        action_reason = "Guardrail blocked the trade."
        policy_materiality = "boosted_but_not_decisive" if boosted_but_not_decisive else "none"

    return {
        "symbol": symbol,
        "action": action,
        "action_reason": action_reason,
        "policy_materiality": policy_materiality,
        "reference_price_krw": reference_price,
        "suggested_stop_price_krw": stop_price,
        "suggested_take_profit_price_krw": take_profit_price,
        "risk_reward_ratio": risk_reward_ratio,
        "time_exit_utc": _iso_utc(time_exit_ts_ms),
        "policy_decision": policy_decision,
        "policy_score_delta": policy_delta,
    }
