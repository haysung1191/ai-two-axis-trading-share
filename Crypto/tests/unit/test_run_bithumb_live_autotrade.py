from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_bithumb_live_autotrade as live_runner


def _write_manual_summary(path: Path) -> None:
    payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "manual_brief": {
            "watchlist": [
                {
                    "symbol": "BTC",
                    "rank": 1,
                    "action": "BUY",
                    "reference_price_krw": 150000000.0,
                    "suggested_stop_price_krw": 145000000.0,
                    "suggested_take_profit_price_krw": 160000000.0,
                    "risk_reward_ratio": 2.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "Scheduled by the baseline scanner.",
                }
            ]
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_run_bithumb_live_autotrade_builds_plan_and_summary(monkeypatch, tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    output_dir = tmp_path / "out"
    execution_log = tmp_path / "bithumb_live_execution_log.jsonl"

    def _fake_submit_execution_plan(
        plan: dict,
        **_: object,
    ) -> dict:
        return {
            "run_id": plan.get("run_id"),
            "candle_close_utc": plan.get("candle_close_utc"),
            "strategy_track": plan.get("strategy_track"),
            "intent_count": plan.get("intent_count", 0),
            "submitted_count": 1,
            "total_quote_krw": 250000.0,
            "funding_checks": [{"market": "KRW-BTC", "available_krw": 500000.0}],
            "submitted_orders": [
                {
                    "market": "KRW-BTC",
                    "client_order_id": "live-btc-01",
                    "quote_amount_krw": 250000.0,
                    "order_status": {"order": {"state": "done"}},
                    "status_history": [],
                    "timed_out": False,
                    "cancel_response": None,
                }
            ],
            "standard_check_order_reference": plan.get("standard_check_order_reference", []),
        }

    monkeypatch.setattr(live_runner, "submit_execution_plan", _fake_submit_execution_plan)
    monkeypatch.setattr(live_runner, "assert_no_existing_asset_position", lambda **_: None)

    payload = live_runner.run_live_autotrade(
        logs_dir=logs_dir,
        run_id=None,
        output_dir=output_dir,
        execution_log=execution_log,
        notional_krw=250000.0,
        max_orders=1,
        strategy_track="operating",
        access_key="ak",
        secret_key="sk",
        client_order_prefix="live",
        allowed_markets=["KRW-BTC"],
        max_total_quote_krw=300000.0,
        status_poll_seconds=2.0,
        status_timeout_seconds=20.0,
        cancel_on_timeout=False,
        allow_duplicate_submission=False,
        skip_exchange_duplicate_check=True,
        block_existing_asset_position=True,
        min_existing_asset_balance=0.000001,
    )

    assert payload["run_id"] == "1h:test"
    assert payload["intent_count"] == 1
    assert payload["submitted_count"] == 1
    assert payload["submitted_orders"][0]["market"] == "KRW-BTC"
    assert payload["submitted_orders"][0]["client_order_id"] == "live-btc-01"
    assert Path(payload["artifacts"]["plan_json"]).exists()
    assert Path(payload["artifacts"]["summary_json"]).exists()
    logged_rows = execution_log.read_text(encoding="utf-8").splitlines()
    assert len(logged_rows) == 1
    logged_payload = json.loads(logged_rows[0])
    assert logged_payload["mode"] == "submit"
    assert logged_payload["submitted_orders"][0]["client_order_id"] == "live-btc-01"


def test_run_bithumb_live_autotrade_blocks_when_existing_asset_position_detected(
    monkeypatch,
    tmp_path: Path,
) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    output_dir = tmp_path / "out"
    execution_log = tmp_path / "bithumb_live_execution_log.jsonl"

    class FakeClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "BTC", "balance": "0.00088869"}]}

    monkeypatch.setattr(live_runner, "BithumbPrivateClient", FakeClient)
    monkeypatch.setattr(live_runner, "submit_execution_plan", lambda *args, **kwargs: {"submitted_count": 99})

    with pytest.raises(RuntimeError, match="existing asset position blocks new live entry"):
        live_runner.run_live_autotrade(
            logs_dir=logs_dir,
            run_id=None,
            output_dir=output_dir,
            execution_log=execution_log,
            notional_krw=250000.0,
            max_orders=1,
            strategy_track="operating",
            access_key="ak",
            secret_key="sk",
            client_order_prefix="live",
            allowed_markets=["KRW-BTC"],
            max_total_quote_krw=300000.0,
            status_poll_seconds=2.0,
            status_timeout_seconds=20.0,
            cancel_on_timeout=False,
            allow_duplicate_submission=False,
            skip_exchange_duplicate_check=True,
            block_existing_asset_position=True,
            min_existing_asset_balance=0.000001,
        )


def test_extract_asset_balance_reads_wrapped_accounts_payload() -> None:
    assert (
        live_runner._extract_asset_balance(
            {
                "data": [
                    {"currency": "KRW", "balance": "1000"},
                    {"currency": "BTC", "balance": "0.00088869"},
                ]
            },
            asset_symbol="BTC",
        )
        == 0.00088869
    )
