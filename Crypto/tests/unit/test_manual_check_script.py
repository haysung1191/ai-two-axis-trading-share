from __future__ import annotations

import json
from pathlib import Path

from scripts.manual_check import build_manual_check_payload, prepare_manual_policy_env, render_text_manual_check


def test_prepare_manual_policy_env_uses_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("TRACE_ENABLED", raising=False)
    monkeypatch.delenv("POLICY_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("POLICY_ACTIVE", raising=False)
    monkeypatch.delenv("POLICY_SOFT_REJECT_ENABLED", raising=False)
    monkeypatch.delenv("POLICY_MAX_SCORE_DELTA", raising=False)

    applied = prepare_manual_policy_env()

    assert applied["TRACE_ENABLED"] == "1"
    assert applied["POLICY_SHADOW_ENABLED"] == "1"
    assert applied["POLICY_ACTIVE"] == "1"
    assert applied["POLICY_SOFT_REJECT_ENABLED"] == "0"
    assert applied["POLICY_MAX_SCORE_DELTA"] == "0.05"


def test_prepare_manual_policy_env_keeps_explicit_overrides(monkeypatch) -> None:
    monkeypatch.setenv("POLICY_ACTIVE", "0")

    applied = prepare_manual_policy_env()

    assert applied["POLICY_ACTIVE"] == "0"


def test_build_manual_check_payload_generates_snapshot_and_brief(monkeypatch, tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = logs_dir / "manual_snapshot_1h_123.json"
    snapshot_path.write_text(json.dumps({"run_id": "1h:123"}, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(
        "scripts.manual_check.generate_manual_snapshot",
        lambda **kwargs: snapshot_path,
    )
    monkeypatch.setattr(
        "scripts.manual_check.build_manual_today_briefing",
        lambda **kwargs: {
            "generated_at": "2026-03-29T00:00:00Z",
            "run_id": kwargs["run_id"],
            "daily_summary": {"generated_at": "2026-03-29T00:00:00Z"},
            "operator_watchlist": {},
            "watchlist": {},
            "pretrade_checklist": {},
        },
    )

    payload = build_manual_check_payload(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
    )

    assert payload["snapshot_path"].endswith("manual_snapshot_1h_123.json")
    assert payload["run_id"] == "1h:123"
    assert payload["briefing"]["run_id"] == "1h:123"


def test_render_text_manual_check_includes_snapshot_and_env() -> None:
    rendered = render_text_manual_check(
        {
            "snapshot_path": "logs/manual_snapshot_1h_123.json",
            "run_id": "1h:123",
            "effective_policy_env": {
                "TRACE_ENABLED": "1",
                "POLICY_ACTIVE": "1",
            },
            "briefing": {
                "daily_summary": {
                    "generated_at": "2026-03-22T12:00:00Z",
                    "strategy_snapshot": {
                        "strategy_id": "mean_rev_approved",
                        "source_run_id": "run-1",
                        "symbol": "BTCUSDT",
                        "timeframe": "1h",
                        "metrics": {"sharpe": 1.2, "max_drawdown": 0.1, "win_rate": 0.55, "trades": 120, "cagr": 0.08},
                    },
                    "policy_snapshot": {
                        "bundle_id": "policy_1",
                        "bundle_mode": "shadow",
                        "policy_type": "filter_and_boost",
                        "symbol_scope_count": 2,
                        "boost_score": 0.1,
                        "valid_until": "2099-01-01T00:00:00Z",
                    },
                    "manual_brief": {"headline": "x", "summary": {}, "watchlist": []},
                    "warnings": [],
                },
                "operator_watchlist": {"generated_at": "2026-03-22T12:00:00Z", "headline": "x", "market_filter_active": False, "baseline_priority": [], "policy_assisted": [], "recheck_on_filter_release": [], "warnings": []},
                "watchlist": {"generated_at": "2026-03-22T12:00:00Z", "strategy_id": "x", "bundle_id": "y", "headline": "x", "buy_candidates": [], "monitor_candidates": [], "warnings": []},
                "pretrade_checklist": {"generated_at": "2026-03-22T12:00:00Z", "strategy_id": "x", "bundle_id": "y", "headline": "x", "general_checks": [], "candidate_checklists": [], "warnings": []},
            },
        }
    )

    assert "snapshot_path: logs/manual_snapshot_1h_123.json" in rendered
    assert "- TRACE_ENABLED=1" in rendered
    assert "=== Daily Summary ===" in rendered
