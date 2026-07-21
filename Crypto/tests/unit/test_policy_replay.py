from datetime import UTC, datetime, timedelta

from src.policy.models import PolicyFlags, compute_strategy_checksum
from src.policy.replay import replay_policy_decision


def _bundle_payload() -> dict:
    strategy = {
        "strategy_id": "strat-1",
        "status": "APPROVED",
        "symbol_scope": ["KRW-BTC"],
        "timeframe": "1h",
        "policy_type": "filter_and_boost",
        "parameters": {"category": "momentum"},
        "decision_rules": {
            "allow_if": ["close > ema_20", "ema_20 > ema_50"],
            "boost_score": 0.1,
            "reject_if": ["drawdown_7d > 0.2000"],
        },
        "valid_until": (datetime.now(UTC) + timedelta(days=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    strategy["checksum"] = compute_strategy_checksum(strategy)
    return {
        "schema_version": "v2",
        "bundle_id": "policy_replay",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_run_id": "run-1",
        "bundle_mode": "shadow",
        "strategies": [strategy],
    }


def _candidate_snapshot() -> dict:
    return {
        "ts": 1772888400000,
        "symbol": "KRW-BTC",
        "scanner_score_before_policy": 1.2,
        "normalized_feature_snapshot": {
            "close": 105.0,
            "ema_20": 100.0,
            "ema_50": 95.0,
            "volume_zscore": 0.4,
            "drawdown_7d": 0.1,
        },
    }


def test_same_inputs_produce_identical_outputs() -> None:
    bundle = _bundle_payload()
    candidate = _candidate_snapshot()
    flags = PolicyFlags(active_enabled=True, max_score_delta=0.15)
    assert replay_policy_decision(candidate, bundle, flags) == replay_policy_decision(candidate, bundle, flags)


def test_replay_returns_trace_hash_and_capped_delta() -> None:
    result = replay_policy_decision(_candidate_snapshot(), _bundle_payload(), PolicyFlags(active_enabled=True, max_score_delta=0.05))
    assert result["policy_result"]["policy_score_delta_raw"] == 0.1
    assert result["policy_result"]["policy_score_delta_capped"] == 0.05
    assert result["combined_final_score"] == 1.25
    assert isinstance(result["final_decision_trace_hash"], str)
    assert len(result["final_decision_trace_hash"]) == 64
    assert result["suppression"]["suppressed"] is False
