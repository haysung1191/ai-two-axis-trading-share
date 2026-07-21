from __future__ import annotations

import json
import logging
import os
import sqlite3
from typing import Any

from src.policy.loader import PolicyBundleLoader
from src.policy.models import PolicyCandidateInput, PolicyEvaluationResult, PolicyFlags, PolicyRuntimeState
from src.policy.sidecar import SidecarPolicyEvaluator

log = logging.getLogger(__name__)


def read_policy_flags() -> PolicyFlags:
    allowlist = tuple(sorted({item.strip().upper() for item in os.getenv("POLICY_SYMBOL_ALLOWLIST", "").split(",") if item.strip()}))
    return PolicyFlags(
        trace_enabled=_env_enabled("TRACE_ENABLED", False),
        shadow_enabled=_env_enabled("POLICY_SHADOW_ENABLED", False),
        active_enabled=_env_enabled("POLICY_ACTIVE", False),
        symbol_allowlist=allowlist,
        max_score_delta=_parse_max_score_delta(os.getenv("POLICY_MAX_SCORE_DELTA", "0.15")),
        soft_reject_enabled=_env_enabled("POLICY_SOFT_REJECT_ENABLED", False),
    )


def _env_enabled(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    log.warning("invalid boolean env %s='%s'; falling back to %s", name, value, int(default))
    return default


def _parse_max_score_delta(value: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        log.warning("invalid POLICY_MAX_SCORE_DELTA '%s'; falling back to 0.15", value)
        return 0.15
    if parsed < 0:
        log.warning("negative POLICY_MAX_SCORE_DELTA '%s'; falling back to 0.15", value)
        return 0.15
    return min(parsed, 1.0)


def load_policy_state(flags: PolicyFlags) -> PolicyRuntimeState:
    bundle_path = os.getenv("POLICY_BUNDLE_PATH", "policy/current/policy_bundle.json")
    manifest_path = os.getenv("POLICY_MANIFEST_PATH", "policy/current/manifest.json")
    return PolicyBundleLoader(bundle_path=bundle_path, manifest_path=manifest_path).load(flags)


def log_policy_runtime_state(flags: PolicyFlags, runtime_state: PolicyRuntimeState) -> None:
    mode = "active" if flags.active_enabled else ("shadow" if flags.shadow_enabled else "disabled")
    if runtime_state.status == "loaded":
        log.info(
            "policy bundle loaded bundle_id=%s mode=%s trace_enabled=%s soft_reject_enabled=%s",
            runtime_state.bundle.bundle_id if runtime_state.bundle else "-",
            mode,
            int(flags.trace_enabled),
            int(flags.soft_reject_enabled),
        )
        return
    if runtime_state.status == "missing":
        log.info("policy bundle missing; baseline scanner path active mode=%s", mode)
        return
    if runtime_state.status == "expired":
        log.warning("policy bundle expired; baseline scanner path active err=%s", runtime_state.error)
        return
    if runtime_state.status == "invalid":
        log.warning("policy bundle invalid; baseline scanner path active err=%s", runtime_state.error)
        return
    log.info(
        "policy integration disabled mode=%s trace_enabled=%s soft_reject_enabled=%s",
        mode,
        int(flags.trace_enabled),
        int(flags.soft_reject_enabled),
    )


def evaluate_policy_candidates(
    *,
    ts_ms: int,
    candidates: list[PolicyCandidateInput],
    flags: PolicyFlags,
    runtime_state: PolicyRuntimeState,
) -> dict[str, PolicyEvaluationResult]:
    if runtime_state.bundle is None:
        return {}

    selected = [
        candidate
        for candidate in candidates
        if not flags.symbol_allowlist or candidate.symbol in flags.symbol_allowlist
    ]
    results = SidecarPolicyEvaluator().evaluate(current_ts=ts_ms, bundle=runtime_state.bundle, candidates=selected)
    return {result.symbol: result for result in results}


def persist_selection_trace(
    conn: sqlite3.Connection,
    *,
    ts: str,
    symbol: str,
    scanner_score: float,
    policy_bundle_id: str | None,
    policy_decision: str,
    policy_score_delta: float,
    risk_pass: bool,
    final_decision: str,
    trace_payload: dict[str, Any],
) -> None:
    try:
        conn.execute(
            """
            INSERT INTO selection_trace(
              ts, symbol, scanner_score, policy_bundle_id, policy_decision,
              policy_score_delta, risk_pass, final_decision, trace_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                symbol,
                scanner_score,
                policy_bundle_id,
                policy_decision,
                policy_score_delta,
                1 if risk_pass else 0,
                final_decision,
                json.dumps(trace_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
            ),
        )
    except Exception as exc:
        log.warning("selection trace write failed for %s: %s", symbol, exc)
