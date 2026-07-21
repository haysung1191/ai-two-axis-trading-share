from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from app.domains.governance.contracts import ApprovedStrategy, ApprovedStrategyBundle
from scripts.generate_manual_snapshot import _market_downtrend, _read_snapshot_policy_flags, generate_manual_snapshot
from src.policy.models import PolicyBundle, PolicyFlags, PolicyRuntimeState
from src.scanner.scanner import Candidate
from src.scanner.scoring import FeatureSnapshot


def _candidate(symbol: str, score: float, close: float, *, ema_fast: float, ema_slow: float) -> Candidate:
    features = FeatureSnapshot(
        rsi=60.0,
        macd_hist=0.1,
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        volume_ratio=1.2,
        atr=5.0,
        atr_pct=0.01,
        bb_width=0.05,
        close=close,
    )
    return Candidate(
        symbol=symbol,
        score=score,
        rank=0,
        signal_close_ts_ms=1_800_000_000_000,
        features=features,
        stop_dist=10.0,
        tp_dist=20.0,
        time_exit_ts_ms=1_800_003_600_000,
    )


def test_generate_manual_snapshot_writes_fresh_run(monkeypatch, tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"

    approved_bundle = ApprovedStrategyBundle(
        winners=[
            ApprovedStrategy(
                strategy_id="mean_rev_approved",
                approved_at=datetime.now(tz=UTC),
                source_run_id="run-1",
                symbol="BTCUSDT",
                timeframe="1h",
                parameters={"period": 20},
                metrics={},
                risk_limits={},
            )
        ]
    )
    approved_path = artifacts_dir / "run-1" / "approved_strategy.json"
    approved_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.write_text(approved_bundle.model_dump_json(indent=2), encoding="utf-8")

    bundle_path = reexport_dir / "run-1" / "publish" / "policy_bundle.json"
    manifest_path = reexport_dir / "run-1" / "publish" / "manifest.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_payload = {
        "schema_version": "v2",
        "bundle_id": "policy_test",
        "generated_at": "2099-01-01T00:00:00Z",
        "source_run_id": "run-1",
        "bundle_mode": "shadow",
        "strategies": [
            {
                "strategy_id": "mean_rev_approved",
                "status": "APPROVED",
                "symbol_scope": ["KRW-BTC", "KRW-ETH"],
                "timeframe": "1h",
                "policy_type": "filter_and_boost",
                "parameters": {},
                "decision_rules": {
                    "allow_if": ["close > ema_20"],
                    "boost_score": 0.1,
                    "reject_if": [],
                },
                "valid_until": "2099-01-10T00:00:00Z",
                "checksum": "sha256:7fce33eacfc8a27e05f0ab83eb656fa64a1d17aa0821b0f8ed9eb23003d81366",
            }
        ],
    }
    manifest_payload = {
        "schema_version": "v1",
        "bundle_id": "policy_test",
        "source_run_id": "run-1",
        "created_at": "2099-01-01T00:00:00Z",
        "files": [{"name": "policy_bundle.json", "sha256": "92eaafec0f9d7195acdbfa44c950c9a0e9f3a8b3fd9c8edca4d6f8dc91d8763b"}],
        "compatibility": {"scanner_min_version": "1.0.0", "policy_contract_version": "v2"},
    }
    bundle_path.write_text(json.dumps(bundle_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    flags = PolicyFlags(trace_enabled=True, shadow_enabled=True, active_enabled=True, max_score_delta=0.05)
    bundle = PolicyBundle.model_validate(bundle_payload)
    state = PolicyRuntimeState(status="loaded", bundle=bundle, manifest=None)

    monkeypatch.setattr(
        "scripts.generate_manual_snapshot.load_config",
        lambda: SimpleNamespace(
            strategy={"interval_ms": 3600000, "market_filter_symbol": "BTC", "market_filter_ema": 26},
            exchange={"krw_quote_volume_24h_min": 1, "max_symbols": 10},
            scanner={"top_n": 1},
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.now_utc_ms", lambda: 1_800_000_100_000)
    monkeypatch.setattr("scripts.generate_manual_snapshot.latest_closed_candle_close_ts_ms", lambda now, interval: 1_800_000_000_000)
    monkeypatch.setattr("scripts.generate_manual_snapshot._load_latest_policy_state", lambda reexport_dir: (flags, state, bundle_path, manifest_path))
    monkeypatch.setattr("scripts.generate_manual_snapshot._load_latest_approved_bundle", lambda artifacts_dir: (approved_bundle, approved_path))
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._fetch_candidates",
        lambda cfg, close_ts_ms, client: (
            [
                _candidate("BTC", 1.0, 100.0, ema_fast=101.0, ema_slow=99.0),
                _candidate("ETH", 0.99, 110.0, ema_fast=109.0, ema_slow=108.0),
            ],
            {"BTC": [], "ETH": []},
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot._market_downtrend", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._market_filter_diagnostics",
        lambda *args, **kwargs: {"symbol": "BTC", "available": True, "ema_period": 26, "below_ema": False},
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.BithumbPublicClient", lambda: SimpleNamespace(close=lambda: None))

    out_path = generate_manual_snapshot(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        trace_count=2,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["snapshot_mode"] == "read_only_manual_snapshot"
    assert out_path.name.startswith("manual_snapshot_")
    assert payload["manual_brief"]["summary"]["buy_count"] == 1
    assert payload["manual_brief"]["summary"]["near_miss_after_policy_count"] == 0
    assert payload["metadata"]["market_filter"]["below_ema"] is False
    buy = payload["manual_recommendations"][0]
    hold = payload["manual_recommendations"][1]
    assert buy["symbol"] == "ETH"
    assert buy["scheduled_due_to_policy"] is True
    assert buy["reference_price_krw"] == 110.0
    assert hold["symbol"] == "BTC"
    assert hold["final_decision"] == "CANCELED:BELOW_ENTRY_CUTOFF"


def test_generate_manual_snapshot_policy_fallback_is_explicit(monkeypatch, tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"

    approved_bundle = ApprovedStrategyBundle(
        winners=[
            ApprovedStrategy(
                strategy_id="mean_rev_approved",
                approved_at=datetime.now(tz=UTC),
                source_run_id="run-1",
                symbol="BTCUSDT",
                timeframe="1h",
                parameters={"period": 20},
                metrics={},
                risk_limits={},
            )
        ]
    )
    approved_path = artifacts_dir / "run-1" / "approved_strategy.json"
    bundle_path = reexport_dir / "run-1" / "publish" / "policy_bundle.json"
    manifest_path = reexport_dir / "run-1" / "publish" / "manifest.json"

    monkeypatch.setattr(
        "scripts.generate_manual_snapshot.load_config",
        lambda: SimpleNamespace(
            strategy={"interval_ms": 3600000, "market_filter_symbol": "BTC", "market_filter_ema": 26},
            exchange={"krw_quote_volume_24h_min": 1, "max_symbols": 10},
            scanner={"top_n": 1},
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.now_utc_ms", lambda: 1_800_000_100_000)
    monkeypatch.setattr("scripts.generate_manual_snapshot.latest_closed_candle_close_ts_ms", lambda now, interval: 1_800_000_000_000)
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._load_latest_policy_state",
        lambda reexport_dir: (
            PolicyFlags(trace_enabled=True),
            PolicyRuntimeState(status="expired", bundle=None, manifest=None, error="expired test bundle"),
            bundle_path,
            manifest_path,
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot._load_latest_approved_bundle", lambda artifacts_dir: (approved_bundle, approved_path))
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._fetch_candidates",
        lambda cfg, close_ts_ms, client: (
            [_candidate("BTC", 1.0, 100.0, ema_fast=101.0, ema_slow=99.0)],
            {"BTC": []},
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot._market_downtrend", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._market_filter_diagnostics",
        lambda *args, **kwargs: {"symbol": "BTC", "available": True, "ema_period": 26, "below_ema": False},
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.BithumbPublicClient", lambda: SimpleNamespace(close=lambda: None))

    out_path = generate_manual_snapshot(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        trace_count=1,
        allow_policy_fallback=True,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["policy_bundle_id"] is None
    assert payload["metadata"]["policy_flags"]["trace_enabled"] is False


def test_generate_manual_snapshot_records_market_filter_counterfactual(monkeypatch, tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"

    approved_bundle = ApprovedStrategyBundle(
        winners=[
            ApprovedStrategy(
                strategy_id="mean_rev_approved",
                approved_at=datetime.now(tz=UTC),
                source_run_id="run-1",
                symbol="BTCUSDT",
                timeframe="1h",
                parameters={"period": 20},
                metrics={},
                risk_limits={},
            )
        ]
    )
    approved_path = artifacts_dir / "run-1" / "approved_strategy.json"
    approved_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.write_text(approved_bundle.model_dump_json(indent=2), encoding="utf-8")

    bundle_path = reexport_dir / "run-1" / "publish" / "policy_bundle.json"
    manifest_path = reexport_dir / "run-1" / "publish" / "manifest.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_payload = {
        "schema_version": "v2",
        "bundle_id": "policy_test",
        "generated_at": "2099-01-01T00:00:00Z",
        "source_run_id": "run-1",
        "bundle_mode": "shadow",
        "strategies": [
            {
                "strategy_id": "mean_rev_approved",
                "status": "APPROVED",
                "symbol_scope": ["KRW-BTC", "KRW-ETH"],
                "timeframe": "1h",
                "policy_type": "filter_and_boost",
                "parameters": {},
                "decision_rules": {
                    "allow_if": ["close > ema_20"],
                    "boost_score": 0.1,
                    "reject_if": [],
                },
                "valid_until": "2099-01-10T00:00:00Z",
                "checksum": "sha256:7fce33eacfc8a27e05f0ab83eb656fa64a1d17aa0821b0f8ed9eb23003d81366",
            }
        ],
    }
    manifest_payload = {
        "schema_version": "v1",
        "bundle_id": "policy_test",
        "source_run_id": "run-1",
        "created_at": "2099-01-01T00:00:00Z",
        "files": [{"name": "policy_bundle.json", "sha256": "92eaafec0f9d7195acdbfa44c950c9a0e9f3a8b3fd9c8edca4d6f8dc91d8763b"}],
        "compatibility": {"scanner_min_version": "1.0.0", "policy_contract_version": "v2"},
    }
    bundle_path.write_text(json.dumps(bundle_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    flags = PolicyFlags(trace_enabled=True, shadow_enabled=True, active_enabled=True, max_score_delta=0.05)
    bundle = PolicyBundle.model_validate(bundle_payload)
    state = PolicyRuntimeState(status="loaded", bundle=bundle, manifest=None)

    monkeypatch.setattr(
        "scripts.generate_manual_snapshot.load_config",
        lambda: SimpleNamespace(
            strategy={"interval_ms": 3600000, "market_filter_symbol": "BTC", "market_filter_ema": 26},
            exchange={"krw_quote_volume_24h_min": 1, "max_symbols": 10},
            scanner={"top_n": 1},
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.now_utc_ms", lambda: 1_800_000_100_000)
    monkeypatch.setattr("scripts.generate_manual_snapshot.latest_closed_candle_close_ts_ms", lambda now, interval: 1_800_000_000_000)
    monkeypatch.setattr("scripts.generate_manual_snapshot._load_latest_policy_state", lambda reexport_dir: (flags, state, bundle_path, manifest_path))
    monkeypatch.setattr("scripts.generate_manual_snapshot._load_latest_approved_bundle", lambda artifacts_dir: (approved_bundle, approved_path))
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._fetch_candidates",
        lambda cfg, close_ts_ms, client: (
            [
                _candidate("BTC", 1.0, 100.0, ema_fast=101.0, ema_slow=99.0),
                _candidate("ETH", 0.99, 110.0, ema_fast=109.0, ema_slow=108.0),
            ],
            {"BTC": [], "ETH": []},
        ),
    )
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._market_downtrend",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._market_filter_diagnostics",
        lambda *args, **kwargs: {"symbol": "BTC", "close": 100.0, "ema_period": 26, "ema": 105.0, "below_ema": True},
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.BithumbPublicClient", lambda: SimpleNamespace(close=lambda: None))

    out_path = generate_manual_snapshot(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        trace_count=2,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["market_filter"]["below_ema"] is True
    assert len(payload["metadata"]["counterfactual_buys_without_market_filter"]) == 1
    assert payload["metadata"]["counterfactual_buys_without_market_filter"][0]["symbol"] == "ETH"


def test_read_snapshot_policy_flags_uses_runtime_env(monkeypatch) -> None:
    monkeypatch.setenv("TRACE_ENABLED", "1")
    monkeypatch.setenv("POLICY_SHADOW_ENABLED", "0")
    monkeypatch.setenv("POLICY_ACTIVE", "0")
    monkeypatch.setenv("POLICY_SOFT_REJECT_ENABLED", "1")
    monkeypatch.setenv("POLICY_MAX_SCORE_DELTA", "0.03")

    flags = _read_snapshot_policy_flags()

    assert flags.trace_enabled is True
    assert flags.shadow_enabled is False
    assert flags.active_enabled is False
    assert flags.soft_reject_enabled is True
    assert flags.max_score_delta == 0.03


def test_market_downtrend_fails_closed_when_market_filter_data_missing() -> None:
    market_downtrend = _market_downtrend(
        {},
        close_ts_ms=1_800_000_000_000,
        interval_ms=3_600_000,
        cfg=SimpleNamespace(strategy={"market_filter_symbol": "BTC", "market_filter_ema": 26}),
    )

    assert market_downtrend is True


def test_generate_manual_snapshot_expands_trace_to_cover_top_n(monkeypatch, tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"

    approved_bundle = ApprovedStrategyBundle(
        winners=[
            ApprovedStrategy(
                strategy_id="mean_rev_approved",
                approved_at=datetime.now(tz=UTC),
                source_run_id="run-1",
                symbol="BTCUSDT",
                timeframe="1h",
                parameters={"period": 20},
                metrics={},
                risk_limits={},
            )
        ]
    )
    approved_path = artifacts_dir / "run-1" / "approved_strategy.json"
    approved_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.write_text(approved_bundle.model_dump_json(indent=2), encoding="utf-8")

    bundle_path = reexport_dir / "run-1" / "publish" / "policy_bundle.json"
    manifest_path = reexport_dir / "run-1" / "publish" / "manifest.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(
        json.dumps(
                {
                    "schema_version": "v2",
                    "bundle_id": "policy_test",
                    "generated_at": "2099-01-01T00:00:00Z",
                    "source_run_id": "run-1",
                    "bundle_mode": "shadow",
                    "strategies": [
                        {
                            "strategy_id": "mean_rev_approved",
                            "status": "APPROVED",
                            "symbol_scope": ["KRW-BTC"],
                            "timeframe": "1h",
                            "policy_type": "filter_and_boost",
                            "parameters": {},
                            "decision_rules": {
                                "allow_if": [],
                                "boost_score": 0.1,
                                "reject_if": [],
                            },
                            "valid_until": "2099-01-10T00:00:00Z",
                            "checksum": "sha256:7fce33eacfc8a27e05f0ab83eb656fa64a1d17aa0821b0f8ed9eb23003d81366",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps({"bundle_id": "policy_test"}, ensure_ascii=False, indent=2), encoding="utf-8")

    flags = PolicyFlags(trace_enabled=True, shadow_enabled=True, active_enabled=True, max_score_delta=0.05)
    bundle = PolicyBundle.model_validate(json.loads(bundle_path.read_text(encoding="utf-8")))
    state = PolicyRuntimeState(status="loaded", bundle=bundle, manifest=None)

    monkeypatch.setattr(
        "scripts.generate_manual_snapshot.load_config",
        lambda: SimpleNamespace(
            strategy={"interval_ms": 3600000, "market_filter_symbol": "BTC", "market_filter_ema": 26},
            exchange={"krw_quote_volume_24h_min": 1, "max_symbols": 10},
            scanner={"top_n": 3},
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.now_utc_ms", lambda: 1_800_000_100_000)
    monkeypatch.setattr("scripts.generate_manual_snapshot.latest_closed_candle_close_ts_ms", lambda now, interval: 1_800_000_000_000)
    monkeypatch.setattr("scripts.generate_manual_snapshot._load_latest_policy_state", lambda reexport_dir: (flags, state, bundle_path, manifest_path))
    monkeypatch.setattr("scripts.generate_manual_snapshot._load_latest_approved_bundle", lambda artifacts_dir: (approved_bundle, approved_path))
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._fetch_candidates",
        lambda cfg, close_ts_ms, client: (
            [
                _candidate("BTC", 1.2, 100.0, ema_fast=101.0, ema_slow=99.0),
                _candidate("ETH", 1.1, 101.0, ema_fast=102.0, ema_slow=100.0),
                _candidate("XRP", 1.0, 102.0, ema_fast=103.0, ema_slow=101.0),
                _candidate("ADA", 0.9, 103.0, ema_fast=104.0, ema_slow=102.0),
            ],
            {"BTC": [(0, 0, 0, 0, 0, 0)]},
        ),
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot._market_downtrend", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "scripts.generate_manual_snapshot._market_filter_diagnostics",
        lambda *args, **kwargs: {"symbol": "BTC", "close": 100.0, "ema_period": 26, "ema": 105.0, "below_ema": True, "available": True},
    )
    monkeypatch.setattr("scripts.generate_manual_snapshot.BithumbPublicClient", lambda: SimpleNamespace(close=lambda: None))

    payload = json.loads(
        generate_manual_snapshot(
            artifacts_dir=artifacts_dir,
            reexport_dir=reexport_dir,
            logs_dir=logs_dir,
            trace_count=1,
        ).read_text(encoding="utf-8")
    )

    assert payload["metadata"]["traced_candidate_count"] == 3
    assert len(payload["manual_recommendations"]) == 3
    assert len(payload["metadata"]["counterfactual_buys_without_market_filter"]) == 3
