from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import jobs.hourly_job as hj
import pytest
from src.config import AppConfig
from src.policy.models import PolicyFlags, compute_strategy_checksum, validate_bundle_payload
from src.policy.replay import replay_policy_decision


class _FakeCandidate:
    def __init__(self, score: float = 1.0, symbol: str = "BTC") -> None:
        self.symbol = symbol
        self.score = score
        self.rank = 0
        self.signal_close_ts_ms = 9 * 3600000
        self.stop_dist = 1.0
        self.tp_dist = 1.5
        self.time_exit_ts_ms = 12 * 3600000
        self.features = SimpleNamespace(
            rsi=55.0,
            macd_hist=0.2,
            ema_fast=100.0,
            ema_slow=95.0,
            volume_ratio=1.4,
            atr=3.0,
            atr_pct=0.02,
            bb_width=0.03,
            close=105.0,
        )

    def features_json(self) -> str:
        return '{"close":105.0}'


class _FakeClient:
    def close(self) -> None:
        pass

    def fetch_1h_candles(self, symbol: str):
        interval = 3600000
        close_ts = 10 * interval
        return [
            (close_ts - interval, 100.0, 110.0, 95.0, 105.0, 1000.0),
            (close_ts, 106.0, 111.0, 104.0, 107.0, 800.0),
        ]

    def diagnose_1h_semantics(self, a, b):
        return {"ok": True}

    def list_krw_tickers_by_quote_volume(self, *args, **kwargs):
        return [SimpleNamespace(symbol="BTC")]

    def pick_candle_for_start_ts(self, rows, close_ts_ms, interval_ms):
        return SimpleNamespace(o=106.0)

    def pick_closed_candle_for_close_ts(self, rows, close_ts_ms, interval_ms):
        return SimpleNamespace(o=100.0, h=110.0, l=95.0, c=105.0)


def _run_hourly(tmp_path, monkeypatch, *, flags, policy_results, policy_state, max_positions: int = 2) -> sqlite3.Connection:
    tmp_path.mkdir(parents=True, exist_ok=True)
    interval_ms = 3600000
    close_ts_ms = 10 * interval_ms
    cfg = AppConfig(
        db_path=str(tmp_path / "state.db"),
        log_level="INFO",
        config_path="(test)",
        app_env="test",
        exchange={"krw_quote_volume_24h_min": 0, "max_symbols": 5},
        strategy={
            "interval_ms": interval_ms,
            "starting_equity_krw": 10000000,
            "risk_per_trade": 0.005,
            "max_concurrent_positions": max_positions,
            "max_new_entries_per_day": 3,
            "daily_realized_loss_kill_switch": 0.02,
            "per_symbol_cooldown_ms": 21600000,
            "market_filter_symbol": "BTC",
            "market_filter_ema": 26,
            "slippage_rate": 0.0008,
            "fee_rate": 0.0004,
        },
        scanner={"top_n": 10},
        email={"enabled": False},
        smtp={},
    )

    monkeypatch.setattr(hj, "load_config", lambda: cfg)
    monkeypatch.setattr(hj, "setup_logging", lambda level: None)
    monkeypatch.setattr(hj, "BithumbPublicClient", lambda: _FakeClient())
    monkeypatch.setattr(hj, "now_utc_ms", lambda: close_ts_ms + 1234)
    monkeypatch.setattr(hj, "latest_closed_candle_close_ts_ms", lambda now_ms, interval: close_ts_ms)
    monkeypatch.setattr(hj, "maybe_fill_scheduled_orders", lambda *args, **kwargs: 0)
    monkeypatch.setattr(hj, "maybe_exit_positions", lambda *args, **kwargs: 0)
    monkeypatch.setattr(hj, "scan_symbol", lambda *args, **kwargs: _FakeCandidate())
    monkeypatch.setattr(hj, "read_policy_flags", lambda: flags)
    monkeypatch.setattr(hj, "load_policy_state", lambda _: policy_state)
    if policy_results is not None:
        monkeypatch.setattr(hj, "evaluate_policy_candidates", lambda **kwargs: policy_results)
    monkeypatch.setenv("HOURLY_LOCK_PATH", str(tmp_path / "hourly.lock"))

    rc = hj.main()
    assert rc == 0
    conn = sqlite3.connect(str(tmp_path / "state.db"))
    conn.row_factory = sqlite3.Row
    return conn


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
        "bundle_id": "bundle-1",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_run_id": "run-1",
        "bundle_mode": "shadow",
        "strategies": [strategy],
    }


def test_shadow_mode_does_not_alter_live_decisions(tmp_path, monkeypatch) -> None:
    flags = SimpleNamespace(
        trace_enabled=False,
        shadow_enabled=True,
        active_enabled=False,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    policy_result = SimpleNamespace(
        matched_strategy_id="strat-1",
        policy_decision="BOOST",
        policy_score_delta=0.1,
        reasons=("allow:close > ema_20",),
        deterministic_hash="abc",
    )
    policy_state = SimpleNamespace(status="loaded", bundle=SimpleNamespace(bundle_id="bundle-1"), error=None)
    summary_path = Path("logs") / "hourly_run_1h_36000000.json"
    if summary_path.exists():
        summary_path.unlink()
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results={"KRW-BTC": policy_result},
        policy_state=policy_state,
    )
    try:
        row = conn.execute("SELECT score FROM signals WHERE symbol='BTC'").fetchone()
        assert row["score"] == 1.0
        trace = conn.execute("SELECT policy_decision FROM selection_trace WHERE symbol='BTC'").fetchone()
        assert trace["policy_decision"] == "BOOST"
    finally:
        conn.close()


def test_active_mode_still_respects_existing_risk_guardrails(tmp_path, monkeypatch) -> None:
    flags = SimpleNamespace(
        trace_enabled=False,
        shadow_enabled=False,
        active_enabled=True,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    policy_result = SimpleNamespace(
        matched_strategy_id="strat-1",
        policy_decision="BOOST",
        policy_score_delta=0.1,
        reasons=("allow:close > ema_20",),
        deterministic_hash="abc",
    )
    policy_state = SimpleNamespace(status="loaded", bundle=SimpleNamespace(bundle_id="bundle-1"), error=None)
    summary_path = Path("logs") / "hourly_run_1h_36000000.json"
    if summary_path.exists():
        summary_path.unlink()
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results={"KRW-BTC": policy_result},
        policy_state=policy_state,
        max_positions=0,
    )
    try:
        order = conn.execute("SELECT status, blocked_reason FROM paper_orders WHERE symbol='BTC'").fetchone()
        assert order["status"] == "CANCELED"
        assert order["blocked_reason"] == "MAX_CONCURRENT"
    finally:
        conn.close()


def test_soft_reject_disabled_remains_advisory_only(tmp_path, monkeypatch) -> None:
    flags = SimpleNamespace(
        trace_enabled=False,
        shadow_enabled=False,
        active_enabled=True,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    policy_result = SimpleNamespace(
        matched_strategy_id="strat-1",
        policy_decision="SOFT_REJECT",
        policy_score_delta=0.0,
        reasons=("reject:drawdown_7d > 0.2",),
        deterministic_hash="abc",
    )
    policy_state = SimpleNamespace(status="loaded", bundle=SimpleNamespace(bundle_id="bundle-1"), error=None)
    summary_path = Path("logs") / "hourly_run_1h_36000000.json"
    if summary_path.exists():
        summary_path.unlink()
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results={"KRW-BTC": policy_result},
        policy_state=policy_state,
    )
    try:
        order = conn.execute("SELECT status, blocked_reason FROM paper_orders WHERE symbol='BTC'").fetchone()
        assert order["status"] == "SCHEDULED"
        assert order["blocked_reason"] is None
    finally:
        conn.close()


def test_attach_candidate_attribution_marks_policy_scheduled_and_near_miss() -> None:
    traced_candidates = [
        _FakeCandidate(score=5.55, symbol="BOOSTED"),
        _FakeCandidate(score=5.52, symbol="RAW_TOP"),
        _FakeCandidate(score=5.49, symbol="NEAR"),
    ]
    final_candidates = list(traced_candidates)
    raw_candidates = [
        _FakeCandidate(score=5.52, symbol="RAW_TOP"),
        _FakeCandidate(score=5.50, symbol="BOOSTED"),
        _FakeCandidate(score=5.44, symbol="NEAR"),
    ]
    trace_context = {
        "BOOSTED": {
            "final_ranking_score": 5.55,
            "policy_result": {"policy_score_delta_capped": 0.05},
        },
        "RAW_TOP": {
            "final_ranking_score": 5.52,
            "policy_result": {"policy_score_delta_capped": 0.0},
        },
        "NEAR": {
            "final_ranking_score": 5.49,
            "policy_result": {"policy_score_delta_capped": 0.05},
        },
    }
    outcomes = {
        "BOOSTED": {"blocked_reason": None},
        "RAW_TOP": {"blocked_reason": "MAX_CONCURRENT"},
        "NEAR": {"blocked_reason": "MAX_CONCURRENT"},
    }

    hj._attach_candidate_attribution(
        traced_candidates=traced_candidates,
        final_candidates=final_candidates,
        raw_candidates=raw_candidates,
        trace_context=trace_context,
        outcomes=outcomes,
    )

    boosted = trace_context["BOOSTED"]
    assert boosted["raw_rank"] == 2
    assert boosted["final_rank"] == 1
    assert boosted["entry_cutoff_rank"] == 1
    assert boosted["cutoff_score_raw"] == 5.52
    assert boosted["cutoff_score_final"] == 5.55
    assert boosted["would_have_been_scheduled_without_policy"] is False
    assert boosted["scheduled_due_to_policy"] is True
    assert boosted["near_miss_after_policy"] is False
    assert boosted["shortfall_after_policy"] == 0.0

    near = trace_context["NEAR"]
    assert near["raw_rank"] == 3
    assert near["final_rank"] == 3
    assert near["entry_cutoff_rank"] == 1
    assert near["would_have_been_scheduled_without_policy"] is False
    assert near["scheduled_due_to_policy"] is False
    assert near["near_miss_after_policy"] is False
    assert near["shortfall_after_policy"] == pytest.approx(0.06)


def test_attach_candidate_attribution_uses_full_raw_population_for_policy_promotion() -> None:
    traced_candidates = [
        _FakeCandidate(score=6.11, symbol="A"),
        _FakeCandidate(score=6.05, symbol="B"),
        _FakeCandidate(score=5.55, symbol="PROMOTED"),
    ]
    final_candidates = list(traced_candidates)
    raw_candidates = [
        _FakeCandidate(score=6.10, symbol="A"),
        _FakeCandidate(score=6.05, symbol="B"),
        _FakeCandidate(score=6.00, symbol="DISPLACED"),
        _FakeCandidate(score=5.50, symbol="PROMOTED"),
    ]
    trace_context = {
        "A": {"final_ranking_score": 6.11, "policy_result": {"policy_score_delta_capped": 0.0}},
        "B": {"final_ranking_score": 6.05, "policy_result": {"policy_score_delta_capped": 0.0}},
        "PROMOTED": {"final_ranking_score": 5.55, "policy_result": {"policy_score_delta_capped": 0.05}},
    }
    outcomes = {
        "A": {"blocked_reason": None},
        "B": {"blocked_reason": None},
        "PROMOTED": {"blocked_reason": None},
    }

    hj._attach_candidate_attribution(
        traced_candidates=traced_candidates,
        final_candidates=final_candidates,
        raw_candidates=raw_candidates,
        trace_context=trace_context,
        outcomes=outcomes,
    )

    promoted = trace_context["PROMOTED"]
    assert promoted["raw_rank"] == 4
    assert promoted["final_rank"] == 3
    assert promoted["entry_cutoff_rank"] == 3
    assert promoted["cutoff_score_raw"] == 6.0
    assert promoted["cutoff_score_final"] == 5.55
    assert promoted["would_have_been_scheduled_without_policy"] is False
    assert promoted["scheduled_due_to_policy"] is True


def test_attach_candidate_attribution_uses_actual_marginal_scheduled_rank() -> None:
    traced_candidates = [
        _FakeCandidate(score=6.0, symbol="FIRST"),
        _FakeCandidate(score=5.9, symbol="BLOCKED"),
        _FakeCandidate(score=5.8, symbol="SECOND"),
        _FakeCandidate(score=5.79, symbol="NEAR"),
    ]
    final_candidates = list(traced_candidates)
    raw_candidates = list(traced_candidates)
    trace_context = {
        "FIRST": {"final_ranking_score": 6.0, "policy_result": {"policy_score_delta_capped": 0.0}},
        "BLOCKED": {"final_ranking_score": 5.9, "policy_result": {"policy_score_delta_capped": 0.0}},
        "SECOND": {"final_ranking_score": 5.8, "policy_result": {"policy_score_delta_capped": 0.0}},
        "NEAR": {"final_ranking_score": 5.79, "policy_result": {"policy_score_delta_capped": 0.05}},
    }
    outcomes = {
        "FIRST": {"blocked_reason": None},
        "BLOCKED": {"blocked_reason": "COOLDOWN"},
        "SECOND": {"blocked_reason": None},
        "NEAR": {"blocked_reason": "MAX_CONCURRENT"},
    }

    hj._attach_candidate_attribution(
        traced_candidates=traced_candidates,
        final_candidates=final_candidates,
        raw_candidates=raw_candidates,
        trace_context=trace_context,
        outcomes=outcomes,
    )

    second = trace_context["SECOND"]
    assert second["entry_cutoff_rank"] == 3
    assert second["cutoff_score_raw"] == 5.8
    assert second["cutoff_score_final"] == 5.8
    assert second["would_have_been_scheduled_without_policy"] is True
    assert second["scheduled_due_to_policy"] is False

    near = trace_context["NEAR"]
    assert near["entry_cutoff_rank"] == 3
    assert near["final_rank"] == 4
    assert near["near_miss_after_policy"] is True
    assert near["shortfall_after_policy"] == pytest.approx(0.01)


def test_hourly_trace_and_run_summary_include_attribution_fields(tmp_path, monkeypatch) -> None:
    flags = SimpleNamespace(
        trace_enabled=True,
        shadow_enabled=False,
        active_enabled=True,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    policy_result = SimpleNamespace(
        matched_strategy_id="strat-1",
        policy_decision="BOOST",
        policy_score_delta=0.1,
        reasons=("allow:close > ema_20",),
        deterministic_hash="abc",
    )
    policy_state = SimpleNamespace(status="loaded", bundle=SimpleNamespace(bundle_id="bundle-1"), error=None)
    summary_path = Path("logs") / "hourly_run_1h_36000000.json"
    if summary_path.exists():
        summary_path.unlink()
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results={"KRW-BTC": policy_result},
        policy_state=policy_state,
    )
    try:
        row = conn.execute("SELECT trace_json FROM selection_trace WHERE symbol='BTC'").fetchone()
        payload = json.loads(row["trace_json"])
        trace_core = payload["trace_core"]
        for field in (
            "raw_rank",
            "final_rank",
            "entry_cutoff_rank",
            "cutoff_score_raw",
            "cutoff_score_final",
            "would_have_been_scheduled_without_policy",
            "scheduled_due_to_policy",
            "near_miss_after_policy",
            "shortfall_after_policy",
        ):
            assert field in trace_core

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        signal = summary["signals"][0]
        for field in (
            "raw_rank",
            "final_rank",
            "entry_cutoff_rank",
            "cutoff_score_raw",
            "cutoff_score_final",
            "would_have_been_scheduled_without_policy",
            "scheduled_due_to_policy",
            "near_miss_after_policy",
            "shortfall_after_policy",
        ):
            assert field in signal
    finally:
        conn.close()


def test_bundle_failure_does_not_break_hourly_loop(tmp_path, monkeypatch) -> None:
    flags = SimpleNamespace(
        trace_enabled=True,
        shadow_enabled=False,
        active_enabled=False,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    policy_state = SimpleNamespace(status="invalid", bundle=None, error="checksum mismatch")
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results={},
        policy_state=policy_state,
    )
    try:
        run = conn.execute("SELECT status FROM runs").fetchone()
        assert run["status"] == "COMPLETED"
    finally:
        conn.close()


def test_trace_write_exception_does_not_break_decision_loop(tmp_path, monkeypatch) -> None:
    flags = SimpleNamespace(
        trace_enabled=True,
        shadow_enabled=True,
        active_enabled=False,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    policy_result = SimpleNamespace(
        matched_strategy_id="strat-1",
        policy_decision="BOOST",
        policy_score_delta=0.1,
        reasons=("allow:close > ema_20",),
        deterministic_hash="abc",
    )
    policy_state = SimpleNamespace(status="loaded", bundle=SimpleNamespace(bundle_id="bundle-1"), error=None)
    monkeypatch.setattr(
        hj,
        "persist_selection_trace",
        lambda *args, **kwargs: (_ for _ in ()).throw(sqlite3.OperationalError("database is locked")),
    )
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results={"KRW-BTC": policy_result},
        policy_state=policy_state,
    )
    try:
        run = conn.execute("SELECT status FROM runs").fetchone()
        assert run["status"] == "COMPLETED"
    finally:
        conn.close()


def test_loader_invalid_bundle_preserves_baseline_decisions(tmp_path, monkeypatch) -> None:
    flags = SimpleNamespace(
        trace_enabled=True,
        shadow_enabled=True,
        active_enabled=False,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results={},
        policy_state=SimpleNamespace(status="invalid", bundle=None, error="bad bundle"),
    )
    try:
        row = conn.execute("SELECT score FROM signals WHERE symbol='BTC'").fetchone()
        assert row["score"] == 1.0
    finally:
        conn.close()


def test_mixed_advisory_and_enforced_soft_reject_behavior(tmp_path, monkeypatch) -> None:
    advisory_flags = SimpleNamespace(
        trace_enabled=True,
        shadow_enabled=False,
        active_enabled=True,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=False,
    )
    enforced_flags = SimpleNamespace(
        trace_enabled=True,
        shadow_enabled=False,
        active_enabled=True,
        symbol_allowlist=(),
        max_score_delta=0.15,
        soft_reject_enabled=True,
    )
    policy_result = SimpleNamespace(
        matched_strategy_id="strat-1",
        policy_decision="SOFT_REJECT",
        policy_score_delta=0.0,
        reasons=("reject:drawdown_7d > 0.2",),
        deterministic_hash="abc",
    )
    policy_state = SimpleNamespace(status="loaded", bundle=SimpleNamespace(bundle_id="bundle-1"), error=None)
    conn = _run_hourly(tmp_path / "advisory", monkeypatch, flags=advisory_flags, policy_results={"KRW-BTC": policy_result}, policy_state=policy_state)
    try:
        advisory = json.loads(conn.execute("SELECT trace_json FROM selection_trace WHERE symbol='BTC'").fetchone()["trace_json"])
        assert advisory["trace_core"]["advisory_vs_enforced"] == "advisory"
        assert advisory["trace_core"]["suppressed"] is False
    finally:
        conn.close()

    conn = _run_hourly(tmp_path / "enforced", monkeypatch, flags=enforced_flags, policy_results={"KRW-BTC": policy_result}, policy_state=policy_state)
    try:
        enforced = json.loads(conn.execute("SELECT trace_json FROM selection_trace WHERE symbol='BTC'").fetchone()["trace_json"])
        order = conn.execute("SELECT blocked_reason FROM paper_orders WHERE symbol='BTC'").fetchone()
        assert enforced["trace_core"]["advisory_vs_enforced"] == "enforced"
        assert enforced["trace_core"]["suppressed"] is True
        assert order["blocked_reason"] == "POLICY_SOFT_REJECT"
    finally:
        conn.close()


def test_replay_matches_stored_trace_payload(tmp_path, monkeypatch) -> None:
    flags = PolicyFlags(
        trace_enabled=True,
        shadow_enabled=False,
        active_enabled=True,
        symbol_allowlist=("KRW-BTC",),
        max_score_delta=0.05,
        soft_reject_enabled=False,
    )
    bundle_payload = _bundle_payload()
    bundle = validate_bundle_payload(bundle_payload)
    policy_state = SimpleNamespace(status="loaded", bundle=bundle, error=None)
    conn = _run_hourly(
        tmp_path,
        monkeypatch,
        flags=flags,
        policy_results=None,
        policy_state=policy_state,
    )
    try:
        trace_row = conn.execute("SELECT trace_json FROM selection_trace WHERE symbol='BTC'").fetchone()
        trace_payload = json.loads(trace_row["trace_json"])
        replay_result = replay_policy_decision(
            {
                "ts": 10 * 3600000,
                "symbol": "KRW-BTC",
                "scanner_score_before_policy": trace_payload["trace_core"]["scanner_score_before_policy"],
                "normalized_feature_snapshot": trace_payload["trace_core"]["normalized_feature_snapshot"],
                "bundle_load_status": trace_payload["trace_core"]["bundle_load_status"],
                "risk_guardrail_outcome_summary": trace_payload["trace_core"]["risk_guardrail_outcome_summary"],
            },
            bundle_payload,
            flags,
        )
        assert replay_result["policy_result"]["policy_decision"] == trace_payload["trace_core"]["policy_decision"]
        assert replay_result["policy_result"]["policy_score_delta_capped"] == trace_payload["trace_core"]["policy_score_delta_capped"]
        assert replay_result["combined_final_score"] == trace_payload["trace_core"]["final_ranking_score"]
    finally:
        conn.close()
