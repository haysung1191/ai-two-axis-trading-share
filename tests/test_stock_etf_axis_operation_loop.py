from __future__ import annotations

import run_stock_etf_axis_operation_loop as loop
import build_stock_etf_operating_candidate_bridge as bridge


def test_stock_submit_blockers_blocks_when_bridge_and_policy_block() -> None:
    blockers = loop.stock_submit_blockers(
        limited_live_policy={"stock_cap_krw": 0.0},
        broker_policy={
            "broker_submit_allowed": False,
            "live_enabled": False,
            "real_orders_allowed": False,
        },
        bridge_status={"blockers": ["TARGET_BOOK_DAILY_CLOSE_MISSING"]},
    )

    assert blockers == [
        "TARGET_BOOK_DAILY_CLOSE_MISSING",
        "STOCK_CAP_KRW_ZERO",
        "BROKER_POLICY_SUBMIT_BLOCKED",
        "BROKER_POLICY_LIVE_DISABLED",
        "BROKER_POLICY_REAL_ORDERS_BLOCKED",
    ]


def test_stock_submit_blockers_clears_when_all_hard_gates_are_ready() -> None:
    blockers = loop.stock_submit_blockers(
        limited_live_policy={"stock_cap_krw": 100000.0},
        broker_policy={
            "broker_submit_allowed": True,
            "live_enabled": True,
            "real_orders_allowed": True,
        },
        bridge_status={"blockers": [], "execution_warnings": ["KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE"]},
    )

    assert blockers == []


def test_plan_status_does_not_report_live_submit_blocked_when_submit_not_requested() -> None:
    assert (
        loop.kis_operation_status(submit_requested=False, submit_allowed=False, blockers=[])
        == "KIS_STOCK_ETF_DAILY_PLAN_READY"
    )


def test_buy_submit_status_reports_submit_blocked_only_when_submit_requested() -> None:
    assert (
        loop.kis_operation_status(
            submit_requested=True,
            submit_allowed=False,
            blockers=["KR_MARKET_CLOSED"],
        )
        == "KIS_STOCK_ETF_LIVE_SUBMIT_BLOCKED"
    )


def test_stock_bridge_connects_only_current_trim_candidates() -> None:
    assert bridge.CANDIDATE_TRIM[
        "stock_aggressive__tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim21_gap02_top2"
    ] == 0.21
    assert "stock_aggressive__tail_release_top25_mid75_pen35_floor25_switchcarry_gap02_top2" not in bridge.CANDIDATE_TRIM
