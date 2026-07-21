from __future__ import annotations

from run_stage7_local_sim_from_shadow import read_shadow_records, simulate


def shadow_record(record_id: str = "r1") -> dict:
    return {
        "record_id": record_id,
        "recorded_at": "2026-05-14T20:00:00+09:00",
        "candidate_id": "CAND-001",
        "broker_submit_allowed": False,
        "real_orders": 0,
        "order_intent_created": False,
        "signal_ok": True,
        "readiness_ok": True,
        "safety_snapshot": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "private_submit_used": False,
            "real_orders": 0,
            "order_intent_created": False,
        },
        "signals": [
            {
                "code": "069500",
                "current_price": 10000.0,
                "target_weight": 0.5,
            },
            {
                "code": "360750",
                "current_price": 25000.0,
                "target_weight": 0.25,
            },
        ],
    }


def test_stage7_local_sim_converts_shadow_targets_to_no_submit_trades() -> None:
    summary, trades = simulate([shadow_record()], starting_cash=1_000_000.0, fee_rate=0.0)

    assert summary["decision"] == "LOCAL_SIM_EVIDENCE_RECORDED"
    assert summary["cycles_processed"] == 1
    assert summary["trades_recorded"] == 2
    assert summary["safety"]["broker_submit_allowed"] is False
    assert summary["safety"]["real_orders"] == 0
    assert {trade["submit_mode"] for trade in trades} == {"local_sim_no_submit"}
    assert {trade["code"]: trade["quantity"] for trade in trades} == {
        "069500": 50,
        "360750": 10,
    }


def test_stage7_local_sim_blocks_dirty_shadow_safety_snapshot() -> None:
    dirty = shadow_record()
    dirty["safety_snapshot"]["broker_submit_allowed"] = True

    summary, trades = simulate([dirty], starting_cash=1_000_000.0, fee_rate=0.0)

    assert summary["cycles_processed"] == 0
    assert summary["trades_recorded"] == 0
    assert trades == []
    assert summary["blocked_cycles"][0]["reason"] == "shadow_record_safety_snapshot_not_clean"


def test_stage7_local_sim_supports_notional_allocation_without_prices() -> None:
    record = shadow_record()
    for signal in record["signals"]:
        signal["current_price"] = None
        signal["target_weight"] = 0.25

    summary, trades = simulate([record], starting_cash=1_000_000.0, fee_rate=0.0)

    assert summary["decision"] == "LOCAL_SIM_EVIDENCE_RECORDED"
    assert summary["simulation_mode"] == "notional_allocation_no_price"
    assert summary["cycles_processed"] == 1
    assert summary["trades_recorded"] == 2
    assert sum(row["market_value_krw"] for row in summary["positions"]) == 500000.0
    assert {trade["side"] for trade in trades} == {"BUY_NOTIONAL"}
    assert {trade["submit_mode"] for trade in trades} == {"local_sim_no_submit"}


def test_read_shadow_records_filters_candidate_id(tmp_path) -> None:
    path = tmp_path / "shadow.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"candidate_id":"CAND-001","record_id":"keep"}',
                '{"candidate_id":"CAND-002","record_id":"skip"}',
            ]
        ),
        encoding="utf-8",
    )

    records = read_shadow_records(path, "CAND-001")

    assert [record["record_id"] for record in records] == ["keep"]


def test_read_shadow_records_filters_min_recorded_at(tmp_path) -> None:
    path = tmp_path / "shadow.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"candidate_id":"CAND-001","record_id":"old","recorded_at":"2026-05-14T21:24:41+09:00"}',
                '{"candidate_id":"CAND-001","record_id":"new","recorded_at":"2026-05-14T21:26:08+09:00"}',
            ]
        ),
        encoding="utf-8",
    )

    records = read_shadow_records(path, "CAND-001", "2026-05-14T21:26:00+09:00")

    assert [record["record_id"] for record in records] == ["new"]
