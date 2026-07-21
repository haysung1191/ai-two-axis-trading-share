from __future__ import annotations

import json

import two_axis_cap_ratchet as ratchet


def test_realized_profit_ratchet_reinvests_positive_realized_profit_only() -> None:
    result = ratchet.realized_profit_ratchet_cap(
        axis="BITHUMB_KRW",
        base_cap_krw=100000,
        realized_profit_krw=10000,
        profit_reinvest_rate=0.5,
        daily_growth_limit=0.10,
        hard_ceiling_krw=1000000,
    )

    assert result["effective_cap_krw"] == 105000
    assert result["cap_increase_krw"] == 5000


def test_realized_profit_ratchet_does_not_raise_cap_on_loss() -> None:
    result = ratchet.realized_profit_ratchet_cap(
        axis="KIS_COMBINED_KRW",
        base_cap_krw=100000,
        realized_profit_krw=-5000,
    )

    assert result["effective_cap_krw"] == 100000
    assert result["cap_increase_krw"] == 0


def test_realized_profit_ratchet_respects_daily_growth_limit() -> None:
    result = ratchet.realized_profit_ratchet_cap(
        axis="BITHUMB_KRW",
        base_cap_krw=100000,
        realized_profit_krw=100000,
        previous_effective_cap_krw=100000,
        profit_reinvest_rate=1.0,
        daily_growth_limit=0.10,
        hard_ceiling_krw=1000000,
    )

    assert result["raw_profit_adjusted_cap_krw"] == 200000
    assert result["effective_cap_krw"] == 110000


def test_bithumb_realized_profit_from_events_sums_latest_market_events(tmp_path) -> None:
    (tmp_path / "orca_event_latest.json").write_text(
        json.dumps({"market": "KRW-ORCA", "cumulative_realized_pnl_krw": 300}),
        encoding="utf-8",
    )
    (tmp_path / "btc_event_latest.json").write_text(
        json.dumps({"market": "KRW-BTC", "cumulative_realized_pnl_krw": -100}),
        encoding="utf-8",
    )

    assert ratchet.bithumb_realized_profit_from_events(tmp_path) == 200


def test_kis_realized_profit_from_ledger_ignores_buy_only_rows(tmp_path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(
        "\n".join(
            [
                json.dumps({"status": "SUBMITTED", "estimated_notional_krw": 10000}),
                json.dumps({"status": "SUBMITTED", "realized_pnl_krw": 1200}),
            ]
        ),
        encoding="utf-8",
    )

    assert ratchet.kis_realized_profit_from_ledger(ledger) == 1200
