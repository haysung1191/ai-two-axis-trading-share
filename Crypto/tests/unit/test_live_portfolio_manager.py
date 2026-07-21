from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_bithumb_live_portfolio_manager as manager_script
from src.execution.live_portfolio_manager import (
    apply_live_exit_fill,
    bootstrap_live_portfolio_state,
    decide_live_portfolio_action,
)
from src.execution.live_portfolio_profiles import resolve_live_portfolio_profile


def _summary_payload(tmp_path: Path) -> dict:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "suggested_stop_price_krw": None,
                        "suggested_take_profit_price_krw": None,
                        "time_exit_utc": None,
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "run_id": "1h:demo",
        "submitted_orders": [
            {
                "symbol": "BTC",
                "market": "KRW-BTC",
                "client_order_id": "live-btc-01",
                "response": {"order_id": "entry-1"},
                "order_status": {
                    "order": {
                        "executed_volume": "0.00088869",
                        "executed_funds": "99799.887",
                        "paid_fee": "39.91",
                        "trades": [{"price": "112300000", "volume": "0.00088869"}],
                    }
                },
            }
        ],
        "artifacts": {
            "summary_json": str(tmp_path / "summary.json"),
            "plan_json": str(plan_path),
        },
    }


def test_bootstrap_live_portfolio_state_builds_thresholds(tmp_path: Path) -> None:
    state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.015,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    assert state["status"] == "OPEN"
    assert state["profile"]["name"] == "custom"
    assert state["entry_price_krw"] == 112300000.0
    assert state["remaining_volume"] == 0.00088869
    assert state["rules"]["partial_take_profit_price_krw"] > state["entry_price_krw"]
    assert state["rules"]["full_stop_loss_price_krw"] < state["entry_price_krw"]


def test_decide_live_portfolio_action_triggers_partial_take_profit(tmp_path: Path) -> None:
    state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    decision = decide_live_portfolio_action(
        state,
        current_price_krw=114000000.0,
        min_order_volume=0.00005,
    )
    assert decision["action"] == "sell"
    assert decision["stage"] == "partial_take_profit"


def test_apply_live_exit_fill_closes_position_after_full_exit(tmp_path: Path) -> None:
    state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    updated = apply_live_exit_fill(
        state,
        stage="full_take_profit",
        reason="FULL_TAKE_PROFIT",
        volume=0.00088869,
        current_price_krw=116000000.0,
        order_id="exit-1",
        client_order_id="live-btc-fulltp",
        paid_fee_krw=20.0,
        executed_funds_krw=103000.0,
    )
    assert updated["status"] == "CLOSED"
    assert updated["remaining_volume"] == 0.0
    assert updated["flags"]["full_exit_done"] is True


def test_run_live_portfolio_manager_holds_open_position_when_threshold_not_hit(monkeypatch, tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(_summary_payload(tmp_path), ensure_ascii=False, indent=2), encoding="utf-8")
    state_path = tmp_path / "state.json"

    class FakePublicClient:
        def get_current_price_krw(self, symbol: str) -> float:
            assert symbol == "BTC"
            return 112400000.0

    class FakePrivateClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "BTC", "balance": "0.00088869"}, {"currency": "KRW", "balance": "200"}]}

    monkeypatch.setattr(manager_script, "BithumbPublicClient", FakePublicClient)
    monkeypatch.setattr(manager_script, "BithumbPrivateClient", FakePrivateClient)

    payload = manager_script.run_live_portfolio_manager(
        state_path=state_path,
        summary_path=summary_path,
        logs_dir=tmp_path,
        output_dir=tmp_path,
        execution_log=tmp_path / "exec.jsonl",
        event_log_path=tmp_path / "events.jsonl",
        latest_event_json_path=tmp_path / "event_latest.json",
        latest_event_text_path=tmp_path / "event_latest.txt",
        access_key="ak",
        secret_key="sk",
        client_order_prefix="live",
        allowed_markets=["KRW-BTC"],
        portfolio_profile="operating",
        partial_take_profit_pct=None,
        full_take_profit_pct=None,
        partial_stop_loss_pct=None,
        full_stop_loss_pct=None,
        partial_take_profit_fraction=None,
        partial_stop_loss_fraction=None,
        min_order_volume=0.00005,
        min_reentry_krw=10000.0,
        reentry_notional_krw=50000.0,
        max_total_quote_krw=100000.0,
        submit=False,
        reentry_enabled=False,
        status_poll_seconds=2.0,
        status_timeout_seconds=20.0,
        cancel_on_timeout=False,
    )

    assert payload["submitted"] is False
    assert payload["portfolio_profile"]["name"] == "operating"
    assert payload["state"]["status"] == "OPEN"
    assert payload["state"]["last_decision"]["action"] == "hold"
    event_rows = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(event_rows) == 1
    assert json.loads(event_rows[0])["event_type"] == "bootstrap_entry_state"
    latest_event = json.loads((tmp_path / "event_latest.json").read_text(encoding="utf-8"))
    assert latest_event["event_type"] == "no_new_event"
    assert latest_event["last_reason"] == "threshold_not_hit"
    assert latest_event["estimated_unrealized_pnl_krw"] == pytest.approx(88.869)
    assert latest_event["next_trigger_stage"] == "partial_stop_loss"
    assert latest_event["next_trigger_price_krw"] == pytest.approx(111177000.0)
    assert latest_event["next_trigger_distance_krw"] == pytest.approx(-1223000.0)
    assert latest_event["next_trigger_distance_pct"] == pytest.approx(-1.0880782918149465)
    assert latest_event["remaining_position_pct"] == pytest.approx(100.0)
    assert latest_event["sold_volume"] == pytest.approx(0.0)
    assert latest_event["cumulative_realized_pnl_krw"] is None
    assert latest_event["cumulative_realized_return_pct"] is None
    assert latest_event["reentry_ready"] is None
    latest_event_text = (tmp_path / "event_latest.txt").read_text(encoding="utf-8")
    assert latest_event_text == (
        "no_new_event | symbol=BTC | position_status=OPEN | last_reason=threshold_not_hit"
        " | current_price_krw=112400000 | next_trigger=partial_stop_loss"
        " | next_trigger_price_krw=111177000 | next_trigger_distance_krw=-1223000"
        " | next_trigger_distance_pct=-1.09 | remaining_volume=0.00088869"
        " | remaining_position_pct=100 | sold_volume=0"
        " | cumulative_realized_pnl_krw=- | cumulative_realized_return_pct=- | reentry_ready=-"
        " | realized_pnl_krw=- | unrealized_pnl_krw=88.87\n"
    )


def test_manager_main_appends_run_log(monkeypatch, tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(_summary_payload(tmp_path), ensure_ascii=False, indent=2), encoding="utf-8")
    state_path = tmp_path / "state.json"
    run_log_path = tmp_path / "manager_runs.jsonl"

    class FakePublicClient:
        def get_current_price_krw(self, symbol: str) -> float:
            return 112400000.0

    class FakePrivateClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "BTC", "balance": "0.00088869"}, {"currency": "KRW", "balance": "200"}]}

    monkeypatch.setattr(manager_script, "BithumbPublicClient", FakePublicClient)
    monkeypatch.setattr(manager_script, "BithumbPrivateClient", FakePrivateClient)
    monkeypatch.setattr(
        manager_script.sys,
        "argv",
        [
            "run_bithumb_live_portfolio_manager.py",
            "--state-path",
            str(state_path),
            "--summary-path",
            str(summary_path),
            "--logs-dir",
            str(tmp_path),
            "--output-dir",
            str(tmp_path),
            "--execution-log",
            str(tmp_path / "exec.jsonl"),
            "--manager-run-log",
            str(run_log_path),
            "--manager-event-log",
            str(tmp_path / "events.jsonl"),
            "--manager-latest-event-json",
            str(tmp_path / "event_latest.json"),
            "--manager-latest-event-text",
            str(tmp_path / "event_latest.txt"),
            "--access-key",
            "ak",
            "--secret-key",
            "sk",
            "--allowed-market",
            "KRW-BTC",
            "--format",
            "json",
        ],
    )

    exit_code = manager_script.main()
    assert exit_code == 0
    rows = run_log_path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    payload = json.loads(rows[0])
    assert payload["status"] == "ok"
    assert payload["symbol"] == "BTC"
    assert payload["last_action"] == "hold"
    assert payload["next_trigger_stage"] == "partial_stop_loss"
    assert payload["remaining_position_pct"] == pytest.approx(100.0)
    assert payload["cumulative_realized_pnl_krw"] is None
    assert payload["reentry_ready"] is None


def test_run_live_portfolio_manager_appends_exit_event_on_sell(monkeypatch, tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(_summary_payload(tmp_path), ensure_ascii=False, indent=2), encoding="utf-8")
    state_path = tmp_path / "state.json"
    event_log_path = tmp_path / "events.jsonl"

    class FakePublicClient:
        def get_current_price_krw(self, symbol: str) -> float:
            return 114000000.0

    class FakePrivateClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "BTC", "balance": "0.00088869"}, {"currency": "KRW", "balance": "200"}]}

        @staticmethod
        def build_market_sell_order_body(order_intent: dict[str, object], *, client_order_id: str | None = None) -> dict[str, str]:
            return {
                "market": str(order_intent["market"]),
                "side": "ask",
                "order_type": "market",
                "volume": str(order_intent["volume"]),
                "client_order_id": str(client_order_id),
            }

        @staticmethod
        def create_order(order_body: dict[str, str]) -> dict[str, str]:
            return {"order_id": "exit-1", "client_order_id": order_body["client_order_id"]}

        @staticmethod
        def get_order(*, uuid: str | None = None, client_order_id: str | None = None) -> dict[str, object]:
            return {
                "uuid": uuid,
                "client_order_id": client_order_id,
                "state": "done",
                "executed_funds": "50000",
                "paid_fee": "20",
            }

    monkeypatch.setattr(manager_script, "BithumbPublicClient", FakePublicClient)
    monkeypatch.setattr(manager_script, "BithumbPrivateClient", FakePrivateClient)

    payload = manager_script.run_live_portfolio_manager(
        state_path=state_path,
        summary_path=summary_path,
        logs_dir=tmp_path,
        output_dir=tmp_path,
        execution_log=tmp_path / "exec.jsonl",
        event_log_path=event_log_path,
        latest_event_json_path=tmp_path / "event_latest.json",
        latest_event_text_path=tmp_path / "event_latest.txt",
        access_key="ak",
        secret_key="sk",
        client_order_prefix="live",
        allowed_markets=["KRW-BTC"],
        portfolio_profile="operating",
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
        min_order_volume=0.00005,
        min_reentry_krw=10000.0,
        reentry_notional_krw=50000.0,
        max_total_quote_krw=100000.0,
        submit=True,
        reentry_enabled=False,
        status_poll_seconds=2.0,
        status_timeout_seconds=20.0,
        cancel_on_timeout=False,
    )

    assert payload["submitted"] is True
    assert payload["portfolio_profile"]["name"] == "operating"
    rows = [json.loads(line) for line in event_log_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["event_type"] == "bootstrap_entry_state"
    assert rows[-1]["event_type"] == "exit_order_submitted"
    assert rows[-1]["last_reason"] == "PARTIAL_TAKE_PROFIT"
    latest_event = json.loads((tmp_path / "event_latest.json").read_text(encoding="utf-8"))
    assert latest_event["event_type"] == "exit_order_submitted"
    assert latest_event["estimated_realized_pnl_krw"] == pytest.approx(735.3865)
    assert latest_event["next_trigger_stage"] == "full_take_profit"
    assert latest_event["next_trigger_price_krw"] == pytest.approx(115669000.0)
    assert latest_event["next_trigger_distance_krw"] == pytest.approx(1669000.0)
    assert latest_event["next_trigger_distance_pct"] == pytest.approx(1.4640350877192982)
    assert latest_event["remaining_position_pct"] == pytest.approx(50.0)
    assert latest_event["sold_volume"] == pytest.approx(0.000444345)
    assert latest_event["cumulative_realized_pnl_krw"] == pytest.approx(80.05649999999878)
    assert latest_event["cumulative_realized_return_pct"] == pytest.approx(0.16043404938925185)
    assert latest_event["reentry_ready"] is None
    latest_event_text = (tmp_path / "event_latest.txt").read_text(encoding="utf-8")
    assert latest_event_text == (
        "exit_order_submitted | symbol=BTC | position_status=OPEN | last_reason=PARTIAL_TAKE_PROFIT"
        " | current_price_krw=114000000 | next_trigger=full_take_profit"
        " | next_trigger_price_krw=115669000 | next_trigger_distance_krw=1669000"
        " | next_trigger_distance_pct=1.46 | remaining_volume=0.00044435"
        " | remaining_position_pct=50 | sold_volume=0.00044435"
        " | cumulative_realized_pnl_krw=80.06 | cumulative_realized_return_pct=0.16 | reentry_ready=-"
        " | realized_pnl_krw=735.39 | unrealized_pnl_krw=755.39\n"
    )


def test_build_latest_event_text_summary_rounds_numeric_fields() -> None:
    summary = manager_script._build_latest_event_text_summary(
        {
            "event_type": "no_new_event",
            "symbol": "BTC",
            "position_status": "OPEN",
            "last_reason": "threshold_not_hit",
            "current_price_krw": 112172000.4,
            "next_trigger_stage": "partial_stop_loss",
            "next_trigger_price_krw": 111177000,
            "next_trigger_distance_krw": -995000.4,
            "next_trigger_distance_pct": -0.8869901353418775,
            "remaining_volume": 0.00088869,
            "remaining_position_pct": 100.0,
            "sold_volume": 0.0,
            "cumulative_realized_pnl_krw": None,
            "cumulative_realized_return_pct": None,
            "reentry_ready": None,
            "estimated_realized_pnl_krw": None,
            "estimated_unrealized_pnl_krw": -113.75232,
        }
    )
    assert summary == (
        "no_new_event | symbol=BTC | position_status=OPEN | last_reason=threshold_not_hit"
        " | current_price_krw=112172000 | next_trigger=partial_stop_loss"
        " | next_trigger_price_krw=111177000 | next_trigger_distance_krw=-995000"
        " | next_trigger_distance_pct=-0.89 | remaining_volume=0.00088869"
        " | remaining_position_pct=100 | sold_volume=0"
        " | cumulative_realized_pnl_krw=- | cumulative_realized_return_pct=- | reentry_ready=-"
        " | realized_pnl_krw=- | unrealized_pnl_krw=-113.75"
    )


def test_build_next_trigger_snapshot_prefers_nearest_pending_threshold(tmp_path: Path) -> None:
    state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.015,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    snapshot = manager_script._build_next_trigger_snapshot(state=state, current_price_krw=112172000.0)
    assert snapshot == {
        "next_trigger_stage": "partial_stop_loss",
        "next_trigger_price_krw": pytest.approx(111177000.0),
        "next_trigger_distance_krw": pytest.approx(-995000.0),
        "next_trigger_distance_pct": pytest.approx(-0.8870306315301502),
    }


def test_build_position_progress_snapshot_tracks_partial_exit_state(tmp_path: Path) -> None:
    state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    updated = apply_live_exit_fill(
        state,
        stage="partial_take_profit",
        reason="PARTIAL_TAKE_PROFIT",
        volume=0.00044434,
        current_price_krw=114000000.0,
        order_id="exit-1",
        client_order_id="live-btc-ptp",
        paid_fee_krw=20.0,
        executed_funds_krw=50000.0,
    )
    snapshot = manager_script._build_position_progress_snapshot(
        state=updated,
        payload={"krw_balance": 200.0, "reentry_enabled": False, "min_reentry_krw": 10000.0},
    )
    assert snapshot == {
        "initial_volume": pytest.approx(0.00088869),
        "sold_volume": pytest.approx(0.00044434),
        "remaining_position_pct": pytest.approx(50.00056262588755),
        "cumulative_realized_pnl_krw": pytest.approx(80.61800000000221),
        "cumulative_realized_return_pct": pytest.approx(0.16156111913370433),
        "reentry_ready": None,
    }


def test_write_no_event_outputs_uses_closed_waiting_reentry_event_type(tmp_path: Path) -> None:
    state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    closed_state = apply_live_exit_fill(
        state,
        stage="full_take_profit",
        reason="FULL_TAKE_PROFIT",
        volume=0.00088869,
        current_price_krw=116000000.0,
        order_id="exit-1",
        client_order_id="live-btc-fulltp",
        paid_fee_krw=20.0,
        executed_funds_krw=103000.0,
    )
    latest_json_path = tmp_path / "event_latest.json"
    latest_text_path = tmp_path / "event_latest.txt"
    manager_script.write_no_event_outputs(
        state=closed_state,
        payload={
            "mode": "closed_waiting",
            "submitted": False,
            "current_price_krw": 116000000.0,
            "asset_balance": 0.0,
            "krw_balance": 15000.0,
            "reentry_enabled": True,
            "min_reentry_krw": 10000.0,
        },
        latest_json_path=latest_json_path,
        latest_text_path=latest_text_path,
    )
    latest_event = json.loads(latest_json_path.read_text(encoding="utf-8"))
    assert latest_event["event_type"] == "closed_waiting_reentry"
    assert latest_event["position_status"] == "CLOSED"
    assert latest_event["reentry_ready"] is True
    assert "next_trigger_stage" not in latest_event
    latest_text = latest_text_path.read_text(encoding="utf-8")
    assert latest_text == (
        "closed_waiting_reentry | symbol=BTC | position_status=CLOSED | last_reason=FULL_TAKE_PROFIT"
        " | current_price_krw=116000000 | next_trigger=- | next_trigger_price_krw=-"
        " | next_trigger_distance_krw=- | next_trigger_distance_pct=- | remaining_volume=0"
        " | remaining_position_pct=0 | sold_volume=0.00088869"
        " | cumulative_realized_pnl_krw=3180.11 | cumulative_realized_return_pct=3.19 | reentry_ready=True"
        " | realized_pnl_krw=- | unrealized_pnl_krw=0\n"
    )


def test_write_no_event_outputs_uses_closed_waiting_funds_event_type(tmp_path: Path) -> None:
    state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    closed_state = apply_live_exit_fill(
        state,
        stage="full_stop_loss",
        reason="FULL_STOP_LOSS",
        volume=0.00088869,
        current_price_krw=110000000.0,
        order_id="exit-1",
        client_order_id="live-btc-fullsl",
        paid_fee_krw=20.0,
        executed_funds_krw=97000.0,
    )
    latest_json_path = tmp_path / "event_latest.json"
    latest_text_path = tmp_path / "event_latest.txt"
    manager_script.write_no_event_outputs(
        state=closed_state,
        payload={
            "mode": "closed_waiting",
            "submitted": False,
            "current_price_krw": 110000000.0,
            "asset_balance": 0.0,
            "krw_balance": 5000.0,
            "reentry_enabled": True,
            "min_reentry_krw": 10000.0,
        },
        latest_json_path=latest_json_path,
        latest_text_path=latest_text_path,
    )
    latest_event = json.loads(latest_json_path.read_text(encoding="utf-8"))
    assert latest_event["event_type"] == "closed_waiting_funds"
    assert latest_event["position_status"] == "CLOSED"
    assert latest_event["reentry_ready"] is False


def test_resolve_latest_snapshot_event_type_handles_closed_modes() -> None:
    assert (
        manager_script._resolve_latest_snapshot_event_type(
            state={"status": "CLOSED"},
            payload={"reentry_enabled": True, "krw_balance": 15000.0, "min_reentry_krw": 10000.0},
        )
        == "closed_waiting_reentry"
    )
    assert (
        manager_script._resolve_latest_snapshot_event_type(
            state={"status": "CLOSED"},
            payload={"reentry_enabled": True, "krw_balance": 5000.0, "min_reentry_krw": 10000.0},
        )
        == "closed_waiting_funds"
    )
    assert (
        manager_script._resolve_latest_snapshot_event_type(
            state={"status": "CLOSED"},
            payload={"reentry_enabled": False, "krw_balance": 5000.0, "min_reentry_krw": 10000.0},
        )
        == "closed_idle"
    )


def test_build_manager_event_log_record_includes_prior_closed_position_context(tmp_path: Path) -> None:
    prior_state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    prior_state = apply_live_exit_fill(
        prior_state,
        stage="full_take_profit",
        reason="FULL_TAKE_PROFIT",
        volume=0.00088869,
        current_price_krw=116000000.0,
        order_id="exit-1",
        client_order_id="live-btc-fulltp",
        paid_fee_krw=20.0,
        executed_funds_krw=103000.0,
    )
    next_state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    record = manager_script.build_manager_event_log_record(
        event_type="reentry_submitted",
        state=next_state,
        payload={
            "mode": "reentry",
            "submitted": True,
            "current_price_krw": 112500000.0,
            "asset_balance": 0.00088869,
            "krw_balance": 15000.0,
            "reentry_enabled": True,
            "min_reentry_krw": 10000.0,
            "prior_state": prior_state,
        },
    )
    assert record["event_type"] == "reentry_submitted"
    assert record["prior_position_status"] == "CLOSED"
    assert record["prior_exit_reason"] == "FULL_TAKE_PROFIT"
    assert record["prior_exit_stage"] == "full_take_profit"
    assert record["prior_exit_price_krw"] == pytest.approx(116000000.0)
    assert record["prior_cumulative_realized_pnl_krw"] == pytest.approx(3180.1129999999976)
    assert record["prior_cumulative_realized_return_pct"] == pytest.approx(3.1864895798930086)
    summary = manager_script._build_latest_event_text_summary(record)
    assert summary == (
        "reentry_submitted | symbol=BTC | position_status=OPEN | last_reason=-"
        " | prior_exit_reason=FULL_TAKE_PROFIT | prior_realized_pnl_krw=3180.11"
        " | prior_realized_return_pct=3.19 | current_price_krw=112500000"
        " | next_trigger=partial_take_profit | next_trigger_price_krw=113423000"
        " | next_trigger_distance_krw=923000 | next_trigger_distance_pct=0.82"
        " | remaining_volume=0.00088869 | remaining_position_pct=100 | sold_volume=0"
        " | cumulative_realized_pnl_krw=- | cumulative_realized_return_pct=- | reentry_ready=-"
        " | realized_pnl_krw=- | unrealized_pnl_krw=177.74"
    )


def test_build_manager_run_log_record_includes_operating_summary_and_prior_context(tmp_path: Path) -> None:
    prior_state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    prior_state = apply_live_exit_fill(
        prior_state,
        stage="full_take_profit",
        reason="FULL_TAKE_PROFIT",
        volume=0.00088869,
        current_price_krw=116000000.0,
        order_id="exit-1",
        client_order_id="live-btc-fulltp",
        paid_fee_krw=20.0,
        executed_funds_krw=103000.0,
    )
    next_state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.01,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    record = manager_script.build_manager_run_log_record(
        status="ok",
        state_path=tmp_path / "state.json",
        payload={
            "mode": "reentry",
            "submitted": True,
            "current_price_krw": 112500000.0,
            "asset_balance": 0.00088869,
            "krw_balance": 15000.0,
            "reentry_enabled": True,
            "min_reentry_krw": 10000.0,
            "prior_state": prior_state,
            "state": next_state,
        },
    )
    assert record["status"] == "ok"
    assert record["mode"] == "reentry"
    assert record["next_trigger_stage"] == "partial_take_profit"
    assert record["remaining_position_pct"] == pytest.approx(100.0)
    assert record["prior_exit_reason"] == "FULL_TAKE_PROFIT"
    assert record["prior_cumulative_realized_pnl_krw"] == pytest.approx(3180.1129999999976)


def test_resolve_live_portfolio_profile_attack_defaults() -> None:
    profile = resolve_live_portfolio_profile("attack")

    assert profile.name == "attack"
    assert profile.objective == "maximize_cagr"
    assert profile.partial_take_profit_pct == pytest.approx(0.02)
    assert profile.full_take_profit_pct == pytest.approx(0.05)
    assert profile.full_stop_loss_pct > profile.partial_stop_loss_pct


def test_resolve_live_portfolio_profile_allows_overrides() -> None:
    profile = resolve_live_portfolio_profile("operating", full_take_profit_pct=0.04)

    assert profile.name == "operating"
    assert profile.objective == "minimize_mdd"
    assert profile.full_take_profit_pct == pytest.approx(0.04)


def test_run_live_portfolio_manager_reentry_uses_attack_track(monkeypatch, tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(_summary_payload(tmp_path), ensure_ascii=False, indent=2), encoding="utf-8")
    state_path = tmp_path / "state.json"

    closed_state = bootstrap_live_portfolio_state(
        _summary_payload(tmp_path),
        partial_take_profit_pct=0.015,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    )
    closed_state = apply_live_exit_fill(
        closed_state,
        stage="full_take_profit",
        reason="FULL_TAKE_PROFIT",
        volume=0.00088869,
        current_price_krw=116000000.0,
        order_id="exit-1",
        client_order_id="live-btc-fulltp",
        paid_fee_krw=20.0,
        executed_funds_krw=103000.0,
    )
    state_path.write_text(json.dumps(closed_state, ensure_ascii=False, indent=2), encoding="utf-8")

    class FakePublicClient:
        def get_current_price_krw(self, symbol: str) -> float:
            assert symbol == "BTC"
            return 116000000.0

    class FakePrivateClient:
        def __init__(self, access_key: str | None = None, secret_key: str | None = None) -> None:
            self.access_key = access_key
            self.secret_key = secret_key

        def has_credentials(self) -> bool:
            return True

        @staticmethod
        def get_accounts() -> dict[str, object]:
            return {"data": [{"currency": "BTC", "balance": "0"}, {"currency": "KRW", "balance": "15000"}]}

    captured: dict[str, object] = {}

    def _fake_run_live_autotrade(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        reentry_plan_path = tmp_path / "reentry_plan.json"
        reentry_plan_path.write_text(
            json.dumps(
                {
                    "order_intents": [
                        {
                            "symbol": "BTC",
                            "market": "KRW-BTC",
                            "reference_price_krw": 116000000.0,
                            "suggested_stop_price_krw": None,
                            "suggested_take_profit_price_krw": None,
                            "time_exit_utc": None,
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return {
            "run_id": "1h:reentry",
            "strategy_track": kwargs.get("strategy_track"),
            "submitted_count": 1,
            "submitted_orders": [
                {
                    "symbol": "BTC",
                    "market": "KRW-BTC",
                    "client_order_id": "live-btc-reentry",
                    "response": {"order_id": "entry-2"},
                    "order_status": {
                        "order": {
                            "executed_volume": "0.00043103",
                            "executed_funds": "50000",
                            "paid_fee": "20",
                            "trades": [{"price": "116000000", "volume": "0.00043103"}],
                        }
                    },
                }
            ],
            "artifacts": {
                "summary_json": str(tmp_path / "reentry_summary.json"),
                "plan_json": str(reentry_plan_path),
            },
        }

    monkeypatch.setattr(manager_script, "BithumbPublicClient", FakePublicClient)
    monkeypatch.setattr(manager_script, "BithumbPrivateClient", FakePrivateClient)
    monkeypatch.setattr(manager_script, "run_live_autotrade", _fake_run_live_autotrade)

    payload = manager_script.run_live_portfolio_manager(
        state_path=state_path,
        summary_path=summary_path,
        logs_dir=tmp_path,
        output_dir=tmp_path,
        execution_log=tmp_path / "exec.jsonl",
        event_log_path=tmp_path / "events.jsonl",
        latest_event_json_path=tmp_path / "event_latest.json",
        latest_event_text_path=tmp_path / "event_latest.txt",
        access_key="ak",
        secret_key="sk",
        client_order_prefix="live",
        allowed_markets=["KRW-BTC"],
        portfolio_profile="attack",
        partial_take_profit_pct=None,
        full_take_profit_pct=None,
        partial_stop_loss_pct=None,
        full_stop_loss_pct=None,
        partial_take_profit_fraction=None,
        partial_stop_loss_fraction=None,
        min_order_volume=0.00005,
        min_reentry_krw=10000.0,
        reentry_notional_krw=50000.0,
        max_total_quote_krw=100000.0,
        submit=False,
        reentry_enabled=True,
        status_poll_seconds=2.0,
        status_timeout_seconds=20.0,
        cancel_on_timeout=False,
    )

    assert captured["strategy_track"] == "attack"
    assert payload["mode"] == "reentry"
    assert payload["portfolio_profile"]["name"] == "attack"
    assert payload["reentry_payload"]["strategy_track"] == "attack"
    assert payload["state"]["profile"]["name"] == "attack"
