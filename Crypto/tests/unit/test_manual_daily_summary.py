from __future__ import annotations

import json
from pathlib import Path

from scripts.manual_daily_summary import build_manual_daily_summary, render_text_summary


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_manual_daily_summary_collects_three_sources(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"

    _write_json(
        artifacts_dir / "run-1" / "approved_strategy.json",
        {
            "winners": [
                {
                    "strategy_id": "mean_rev_approved",
                    "source_run_id": "run-1",
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "parameters": {},
                    "metrics": {"sharpe": 1.2, "max_drawdown": 0.1, "win_rate": 0.55, "trades": 120, "cagr": 0.08},
                }
            ]
        },
    )
    _write_json(
        reexport_dir / "run-1" / "publish" / "policy_bundle.json",
        {
            "bundle_id": "policy_1",
            "source_run_id": "run-1",
            "bundle_mode": "shadow",
            "strategies": [
                {
                    "strategy_id": "mean_rev_approved",
                    "policy_type": "filter_and_boost",
                    "symbol_scope": ["KRW-BTC", "KRW-ETH"],
                    "decision_rules": {"allow_if": ["close > ema_20"], "reject_if": [], "boost_score": 0.1},
                    "valid_until": "2099-01-01T00:00:00Z",
                }
            ],
        },
    )
    _write_json(
        logs_dir / "hourly_run_1h_1.json",
        {
            "run_id": "1h:1",
            "candle_close_utc": "2026-03-22T12:00:00+00:00",
            "metadata": {
                "market_filter": {
                    "symbol": "BTC",
                    "close": 100.0,
                    "ema_period": 26,
                    "ema": 105.0,
                    "below_ema": True,
                },
                "counterfactual_buys_without_market_filter": [
                    {"symbol": "ETH", "final_rank": 1, "final_ranking_score": 5.55, "policy_materiality": "entry_reversal", "policy_decision": "BOOST"}
                ],
            },
            "manual_brief": {
                "headline": "Actionable BUY candidates exist, but policy was not decisive at the cutoff.",
                "summary": {
                    "buy_count": 1,
                    "hold_count": 0,
                    "no_buy_count": 0,
                    "scheduled_due_to_policy_count": 0,
                    "near_miss_after_policy_count": 0,
                },
                "notes": ["Baseline scanner and guardrails dominated this run."],
                "watchlist": [
                    {
                        "symbol": "BTC",
                        "rank": 1,
                        "action": "BUY",
                        "final_decision": "SCHEDULED",
                        "policy_materiality": "none",
                        "action_reason": "Scheduled by the baseline scanner.",
                    }
                ],
            },
            "manual_recommendations": [],
        },
    )

    payload = build_manual_daily_summary(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
    )

    assert payload["strategy_snapshot"]["strategy_id"] == "mean_rev_approved"
    assert payload["policy_snapshot"]["bundle_id"] == "policy_1"
    assert payload["manual_brief"]["summary"]["buy_count"] == 1
    assert payload["sources"]["manual_brief_source_kind"] == "hourly_run"
    assert any("parameters are empty" in warning for warning in payload["warnings"])
    assert any("no direct policy-driven scheduling reversal" in warning for warning in payload["warnings"])
    assert any("Market filter is active" in warning for warning in payload["warnings"])
    assert any("Without the market filter" in warning for warning in payload["warnings"])


def test_render_text_summary_contains_sections() -> None:
    rendered = render_text_summary(
        {
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
                "source_run_id": "run-1",
                "bundle_mode": "shadow",
                "policy_type": "filter_and_boost",
                "symbol_scope_count": 2,
                "boost_score": 0.1,
                "valid_until": "2099-01-01T00:00:00Z",
            },
            "sources": {
                "approved_strategy_path": "artifacts/run-1/approved_strategy.json",
                "policy_bundle_path": "artifacts_reexport/run-1/publish/policy_bundle.json",
                "manual_brief_source": "logs/hourly_run_1h_1.json",
                "manual_brief_source_kind": "legacy_signals",
                "manual_brief_mtime_utc": "2026-03-22T12:00:00Z",
            },
            "snapshot_metadata": {
                "market_filter": {
                    "symbol": "BTC",
                    "close": 100.0,
                    "ema_period": 26,
                    "ema": 105.0,
                    "below_ema": True,
                },
                "counterfactual_buys_without_market_filter": [
                    {"symbol": "ETH", "final_rank": 1, "final_ranking_score": 5.55, "policy_materiality": "entry_reversal", "policy_decision": "BOOST"}
                ],
            },
            "manual_brief": {
                "headline": "Actionable BUY candidates exist, but policy was not decisive at the cutoff.",
                "summary": {
                    "buy_count": 1,
                    "hold_count": 0,
                    "no_buy_count": 0,
                    "scheduled_due_to_policy_count": 0,
                    "near_miss_after_policy_count": 0,
                },
                "watchlist": [
                    {
                        "symbol": "BTC",
                        "action": "BUY",
                        "rank": 1,
                        "final_decision": "SCHEDULED",
                        "policy_materiality": "none",
                        "action_reason": "Scheduled by the baseline scanner.",
                    }
                ],
            },
            "warnings": ["Approved strategy parameters are empty; inspect research payload fidelity."],
        }
    )

    assert "strategy:" in rendered
    assert "policy:" in rendered
    assert "sources:" in rendered
    assert "market_filter:" in rendered
    assert "counterfactual_buys_without_market_filter:" in rendered
    assert "brief_source_kind: legacy_signals" in rendered
    assert "manual_brief:" in rendered
    assert "BTC | action=BUY | rank=1 | decision=SCHEDULED | policy=none" in rendered
    assert "warnings:" in rendered


def test_build_manual_daily_summary_warns_on_bundle_mismatch(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"

    _write_json(
        artifacts_dir / "run-1" / "approved_strategy.json",
        {
            "winners": [
                {
                    "strategy_id": "mean_rev_approved",
                    "source_run_id": "run-1",
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "parameters": {"period": 20},
                    "metrics": {},
                }
            ]
        },
    )
    _write_json(
        reexport_dir / "run-2" / "publish" / "policy_bundle.json",
        {
            "bundle_id": "policy_2",
            "source_run_id": "run-2",
            "bundle_mode": "shadow",
            "strategies": [
                {
                    "strategy_id": "other_approved",
                    "policy_type": "filter_and_boost",
                    "symbol_scope": ["KRW-BTC"],
                    "decision_rules": {"allow_if": [], "reject_if": [], "boost_score": 0.1},
                    "valid_until": "2099-01-01T00:00:00Z",
                }
            ],
        },
    )
    _write_json(
        logs_dir / "hourly_run_1h_2.json",
        {
            "run_id": "1h:2",
            "candle_close_utc": "2099-01-01T00:00:00+00:00",
            "manual_brief": {
                "headline": "No actionable BUY candidates in this run under current guardrails.",
                "summary": {
                    "buy_count": 0,
                    "hold_count": 0,
                    "no_buy_count": 1,
                    "scheduled_due_to_policy_count": 0,
                    "near_miss_after_policy_count": 0,
                },
                "notes": [],
                "watchlist": [],
            },
            "manual_recommendations": [],
        },
    )

    payload = build_manual_daily_summary(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
    )

    assert any("source_run_id does not match" in warning for warning in payload["warnings"])
    assert any("strategy_id does not match" in warning for warning in payload["warnings"])


def test_build_manual_daily_summary_uses_artifact_paths_from_selected_brief(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    reexport_dir = tmp_path / "artifacts_reexport"
    logs_dir = tmp_path / "logs"

    _write_json(
        artifacts_dir / "run-1" / "approved_strategy.json",
        {
            "winners": [
                {
                    "strategy_id": "mean_rev_approved",
                    "source_run_id": "run-1",
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "parameters": {"period": 20},
                    "metrics": {"sharpe": 1.0},
                }
            ]
        },
    )
    _write_json(
        artifacts_dir / "run-2" / "approved_strategy.json",
        {
            "winners": [
                {
                    "strategy_id": "other_strategy",
                    "source_run_id": "run-2",
                    "symbol": "ETHUSDT",
                    "timeframe": "4h",
                    "parameters": {"period": 99},
                    "metrics": {"sharpe": 9.0},
                }
            ]
        },
    )
    _write_json(
        reexport_dir / "run-1" / "publish" / "policy_bundle.json",
        {
            "bundle_id": "policy_1",
            "source_run_id": "run-1",
            "bundle_mode": "shadow",
            "strategies": [
                {
                    "strategy_id": "mean_rev_approved",
                    "policy_type": "filter_and_boost",
                    "symbol_scope": ["KRW-BTC"],
                    "decision_rules": {"allow_if": [], "reject_if": [], "boost_score": 0.1},
                    "valid_until": "2099-01-01T00:00:00Z",
                }
            ],
        },
    )
    _write_json(
        reexport_dir / "run-2" / "publish" / "policy_bundle.json",
        {
            "bundle_id": "policy_2",
            "source_run_id": "run-2",
            "bundle_mode": "shadow",
            "strategies": [
                {
                    "strategy_id": "other_strategy",
                    "policy_type": "filter_and_boost",
                    "symbol_scope": ["KRW-ETH"],
                    "decision_rules": {"allow_if": [], "reject_if": [], "boost_score": 0.2},
                    "valid_until": "2099-01-01T00:00:00Z",
                }
            ],
        },
    )
    # make run-2 look newest on disk
    (artifacts_dir / "run-2" / "approved_strategy.json").touch()
    (reexport_dir / "run-2" / "publish" / "policy_bundle.json").touch()
    _write_json(
        logs_dir / "manual_snapshot_1h_1.json",
        {
            "run_id": "1h:1",
            "candle_close_utc": "2026-03-22T12:00:00+00:00",
            "metadata": {
                "approved_strategy_path": str(artifacts_dir / "run-1" / "approved_strategy.json"),
                "policy_bundle_path": str(reexport_dir / "run-1" / "publish" / "policy_bundle.json"),
            },
            "manual_brief": {
                "headline": "No actionable BUY candidates in this run under current guardrails.",
                "summary": {
                    "buy_count": 0,
                    "hold_count": 0,
                    "no_buy_count": 1,
                    "scheduled_due_to_policy_count": 0,
                    "near_miss_after_policy_count": 0,
                },
                "notes": [],
                "watchlist": [],
            },
            "manual_recommendations": [],
        },
    )

    payload = build_manual_daily_summary(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        run_id="1h:1",
    )

    assert payload["strategy_snapshot"]["strategy_id"] == "mean_rev_approved"
    assert payload["policy_snapshot"]["bundle_id"] == "policy_1"
    assert payload["sources"]["approved_strategy_path"].endswith("run-1\\approved_strategy.json")
    assert payload["sources"]["policy_bundle_path"].endswith("run-1\\publish\\policy_bundle.json")
