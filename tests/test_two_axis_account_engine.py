from __future__ import annotations

import pytest

from two_axis_account_engine import (
    AxisExecutionLease,
    build_account_target_diff,
    build_reconciliation,
    normalize_bithumb_account_snapshot,
    normalize_kis_account_snapshot,
    target_from_order_rows,
    write_axis_artifacts,
)


def test_kis_account_diff_buys_only_missing_quantity() -> None:
    account = normalize_kis_account_snapshot(
        balance_rows=[{"pdno": "005930", "hldg_qty": "1", "evlu_amt": "10000"}]
    )
    target = target_from_order_rows(
        "KIS_COMBINED_KRW",
        [
            {
                "Symbol": "005930",
                "Market": "KR",
                "AssetType": "STOCK",
                "TargetNotionalKRW": "25000",
                "CurrentPrice": "10000",
                "SubmitAllowed": "True",
            }
        ],
    )

    diff = build_account_target_diff(
        axis="KIS_COMBINED_KRW",
        account_snapshot=account,
        target_portfolio=target,
        min_notional_krw=1,
    )

    assert diff["actionable_count"] == 1
    assert diff["decisions"][0]["action"] == "BUY"
    assert diff["decisions"][0]["delta_quantity"] == 1


def test_kis_account_diff_holds_when_target_already_held() -> None:
    account = normalize_kis_account_snapshot(
        balance_rows=[{"pdno": "005930", "hldg_qty": "2", "evlu_amt": "20000"}]
    )
    target = target_from_order_rows(
        "KIS_COMBINED_KRW",
        [{"Symbol": "005930", "Market": "KR", "TargetNotionalKRW": "25000", "CurrentPrice": "10000"}],
    )

    diff = build_account_target_diff(
        axis="KIS_COMBINED_KRW",
        account_snapshot=account,
        target_portfolio=target,
        min_notional_krw=1,
    )

    assert diff["actionable_count"] == 0
    assert diff["decisions"][0]["action"] == "HOLD"


def test_kis_account_diff_sells_managed_position_missing_from_target() -> None:
    account = normalize_kis_account_snapshot(
        balance_rows=[{"pdno": "005930", "hldg_qty": "3", "evlu_amt": "30000"}]
    )
    target = target_from_order_rows("KIS_COMBINED_KRW", [])

    diff = build_account_target_diff(
        axis="KIS_COMBINED_KRW",
        account_snapshot=account,
        target_portfolio=target,
        managed_symbols={"005930"},
        min_notional_krw=1,
    )

    assert diff["decisions"][0]["action"] == "SELL"
    assert diff["decisions"][0]["reason"] == "NO_LONGER_IN_TARGET"


def test_bithumb_snapshot_normalizes_cash_and_positions() -> None:
    snapshot = normalize_bithumb_account_snapshot(
        account_rows=[
            {"currency": "KRW", "balance": "100000"},
            {"currency": "ORCA", "balance": "4.5", "locked": "0", "avg_buy_price": "2200"},
        ]
    )

    assert snapshot["cash_krw"] == 100000
    assert snapshot["positions"][0]["market"] == "KRW-ORCA"
    assert snapshot["positions"][0]["evaluation_amount_krw"] == 9900


def test_reconciliation_flags_unresolved_broker_orders() -> None:
    payload = build_reconciliation(
        axis="KIS_COMBINED_KRW",
        submitted_events=[{"status": "SUBMITTED", "symbol": "005930"}],
        broker_orders=[{"order_id": "1", "state": "wait"}, {"order_id": "2", "state": "done"}],
    )

    assert payload["submitted_event_count"] == 1
    assert payload["unresolved_order_count"] == 1


def test_axis_execution_lease_blocks_concurrent_holder(tmp_path) -> None:
    lock_path = tmp_path / "axis.lock"

    with AxisExecutionLease(lock_path, owner="first"):
        with pytest.raises(RuntimeError):
            with AxisExecutionLease(lock_path, owner="second"):
                pass

    assert not lock_path.exists()


def test_write_axis_artifacts_writes_required_files(tmp_path) -> None:
    account = normalize_kis_account_snapshot(balance_rows=[])
    target = target_from_order_rows("KIS_COMBINED_KRW", [])
    diff = build_account_target_diff(axis="KIS_COMBINED_KRW", account_snapshot=account, target_portfolio=target)
    reconciliation = build_reconciliation(axis="KIS_COMBINED_KRW")

    paths = write_axis_artifacts(
        root=tmp_path,
        axis_slug="kis_combined_krw",
        account_snapshot=account,
        target_portfolio=target,
        diff=diff,
        reconciliation=reconciliation,
    )

    assert set(paths) == {"account_snapshot", "target_portfolio", "diff", "reconciliation", "manifest"}
    for path in paths.values():
        assert path.startswith(str(tmp_path))

