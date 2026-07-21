from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.policy.models import PolicyCandidateInput, PolicyFlags, compute_trace_hash, validate_bundle_payload
from src.policy.normalization import normalize_candidate_features
from src.policy.sidecar import SidecarPolicyEvaluator


def replay_policy_decision(
    candidate_snapshot: dict[str, Any],
    bundle_payload: dict[str, Any],
    flags: PolicyFlags,
) -> dict[str, Any]:
    bundle = validate_bundle_payload(bundle_payload)
    evaluator = SidecarPolicyEvaluator()
    normalized_features = _resolve_normalized_features(candidate_snapshot)
    candidate = PolicyCandidateInput(
        symbol=str(candidate_snapshot["symbol"]).upper(),
        scanner_score=float(candidate_snapshot["scanner_score_before_policy"]),
        features=normalized_features,
    )
    result = evaluator.evaluate(
        current_ts=int(candidate_snapshot["ts"]),
        bundle=bundle,
        candidates=[candidate],
    )[0]
    raw_delta = float(result.policy_score_delta)
    capped_delta = min(raw_delta, float(flags.max_score_delta)) if flags.active_enabled else 0.0
    final_score = candidate.scanner_score + capped_delta
    suppression_mode = "advisory"
    suppressed = False
    if result.policy_decision == "SOFT_REJECT" and flags.active_enabled and flags.soft_reject_enabled:
        suppression_mode = "enforced"
        suppressed = True
    risk_summary = dict(candidate_snapshot.get("risk_guardrail_outcome_summary", {}))
    if not risk_summary:
        risk_summary = {
            "blocked_reason": None,
            "kill_switch": False,
            "market_downtrend": False,
            "risk_pass": not suppressed,
        }

    trace_core = {
        "ts": int(candidate_snapshot["ts"]),
        "symbol": candidate.symbol,
        "scanner_score_before_policy": candidate.scanner_score,
        "policy_score_delta_raw": raw_delta,
        "policy_score_delta_capped": capped_delta,
        "policy_active": flags.active_enabled,
        "policy_shadow_enabled": flags.shadow_enabled,
        "policy_soft_reject_enabled": flags.soft_reject_enabled,
        "bundle_load_status": str(candidate_snapshot.get("bundle_load_status", "loaded")),
        "bundle_id": bundle.bundle_id,
        "matched_strategy_id": result.matched_strategy_id,
        "normalized_feature_snapshot": normalized_features,
        "evaluator_reasons": list(result.reasons),
        "advisory_vs_enforced": suppression_mode,
        "suppressed": suppressed,
        "final_ranking_score": final_score,
        "risk_guardrail_outcome_summary": risk_summary,
        "policy_decision": result.policy_decision,
    }
    trace_hash = compute_trace_hash(trace_core)
    return {
        "normalized_feature_snapshot": normalized_features,
        "policy_result": {
            "matched_strategy_id": result.matched_strategy_id,
            "policy_decision": result.policy_decision,
            "policy_score_delta_raw": raw_delta,
            "policy_score_delta_capped": capped_delta,
            "reasons": list(result.reasons),
        },
        "combined_final_score": final_score,
        "suppression": {
            "mode": suppression_mode,
            "suppressed": suppressed,
        },
        "final_decision_trace_hash": trace_hash,
        "trace_core": trace_core,
    }


def replay_policy_decision_from_files(candidate_path: str, bundle_path: str, flags: PolicyFlags) -> dict[str, Any]:
    candidate_payload = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    bundle_payload = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
    return replay_policy_decision(candidate_payload, bundle_payload, flags)


def _resolve_normalized_features(candidate_snapshot: dict[str, Any]) -> dict[str, float]:
    if "normalized_feature_snapshot" in candidate_snapshot:
        return {key: float(value) for key, value in dict(candidate_snapshot["normalized_feature_snapshot"]).items()}

    raw_candidate = candidate_snapshot.get("raw_candidate")
    if raw_candidate is not None:
        return normalize_candidate_features(raw_candidate)

    raw_features = candidate_snapshot.get("features")
    if raw_features is None:
        raise ValueError("candidate snapshot must include normalized_feature_snapshot or features")
    return {key: float(value) for key, value in dict(raw_features).items()}
