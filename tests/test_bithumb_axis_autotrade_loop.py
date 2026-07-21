from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import run_bithumb_axis_autotrade_loop as loop


def test_select_best_candidate_per_market_keeps_highest_rank() -> None:
    rows = [
        {
            "candidate_id": "weak",
            "market": "KRW-AAA",
            "source_conversion": {"estimated_cagr": 0.2, "estimated_mdd": -0.1},
            "aggregate": {"pass_fold_count": 2},
        },
        {
            "candidate_id": "strong",
            "market": "KRW-AAA",
            "source_conversion": {"estimated_cagr": 0.8, "estimated_mdd": -0.2},
            "aggregate": {"pass_fold_count": 2},
        },
        {
            "candidate_id": "other",
            "market": "KRW-BBB",
            "source_conversion": {"estimated_cagr": 0.4, "estimated_mdd": -0.2},
            "aggregate": {"pass_fold_count": 2},
        },
    ]

    selected = loop.select_best_candidate_per_market(rows)

    assert [row["candidate_id"] for row in selected] == ["strong", "other"]


def test_load_oos_pass_candidates_includes_direct_validated_candidates(monkeypatch, tmp_path: Path) -> None:
    oos_path = tmp_path / "oos.json"
    non_orca_path = tmp_path / "non_orca.json"
    direct_path = tmp_path / "direct.json"
    oos_path.write_text(json.dumps({"evaluations": []}), encoding="utf-8")
    non_orca_path.write_text(json.dumps({"trial_results": []}), encoding="utf-8")
    direct_path.write_text(
        json.dumps(
            {
                "crypto": {
                    "top_candidates": [
                        {
                            "candidate_id": "direct_eth",
                            "market": "KRW-ETH",
                            "timeframe": "1d",
                            "status": "DIRECT_VALIDATED_PASS",
                            "parameters": {"lookback_bars": 3},
                            "metrics": {"cagr": 1.0, "mdd": -0.2, "profit_factor": 2.0},
                            "walkforward": {"pass_fold_count": 3, "positive_fold_count": 3, "total_trade_count": 30},
                            "holdout_validation": {
                                "passed": True,
                                "holdout": {"cagr": 0.4, "mdd": -0.1, "total_return": 0.2},
                            },
                        },
                        {
                            "candidate_id": "direct_weak",
                            "market": "KRW-X",
                            "status": "DIRECT_OOS_PASS_HOLDOUT_ITERATE",
                        },
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(loop, "OOS_JSON", oos_path)
    monkeypatch.setattr(loop, "NON_ORCA_OOS_JSON", non_orca_path)
    monkeypatch.setattr(loop, "DIRECT_DEVELOPMENT_JSON", direct_path)

    candidates = loop.load_oos_pass_candidates()

    assert [row["candidate_id"] for row in candidates] == ["direct_eth"]
    assert candidates[0]["source_conversion"]["estimated_cagr"] == 0.4
    assert candidates[0]["robustness_status"] == "DIRECT_HOLDOUT_HIGH_COST_PASS"


def test_run_once_scans_universe_filters_oos_and_selects_only_triggered_new_entry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(loop, "STATUS_JSON", tmp_path / "status.json")
    monkeypatch.setattr(loop, "STATUS_MD", tmp_path / "status.md")
    monkeypatch.setattr(loop, "EVENT_DIR", tmp_path / "events")
    monkeypatch.setattr(loop, "GLOBAL_DISABLE", tmp_path / "DISABLE_ALL_TRADING")
    monkeypatch.setattr(
        loop,
        "load_policy",
        lambda: {
            "max_krw": 30000.0,
            "max_order_krw": 10000.0,
            "max_daily_loss_krw": 20000.0,
            "max_total_loss_krw": 100000.0,
        },
    )
    monkeypatch.setattr(loop, "list_bithumb_universe", lambda: ["KRW-AAA", "KRW-BBB", "KRW-CCC"])
    monkeypatch.setattr(
        loop,
        "load_oos_pass_candidates",
        lambda: [
            {
                "candidate_id": "aaa_oos",
                "market": "KRW-AAA",
                "status": "OOS_CANDIDATE_PASS",
                "parameters": {},
                "source_conversion": {"estimated_cagr": 1.0, "estimated_mdd": -0.2},
                "aggregate": {"pass_fold_count": 2},
            },
            {
                "candidate_id": "bbb_oos",
                "market": "KRW-BBB",
                "status": "OOS_CANDIDATE_PASS",
                "parameters": {},
                "source_conversion": {"estimated_cagr": 0.5, "estimated_mdd": -0.2},
                "aggregate": {"pass_fold_count": 2},
            },
        ],
    )
    monkeypatch.setattr(
        loop,
        "load_open_positions",
        lambda state_dir: {
            "KRW-BBB": {
                "market": "KRW-BBB",
                "state_path": str(tmp_path / "bbb_state.json"),
                "entry_summary_path": str(tmp_path / "bbb_summary.json"),
                "estimated_exposure_krw": 10000.0,
            }
        },
    )
    monkeypatch.setattr(loop, "manage_open_positions", lambda *args, **kwargs: [{"market": "KRW-BBB"}])

    def fake_signal(candidate):
        return ({"triggered": candidate["market"] in {"KRW-AAA", "KRW-BBB"}, "latest_close": 100.0}, {"status": "LIVE_FETCH_OK"})

    monkeypatch.setattr(loop, "evaluate_candidate_signal", fake_signal)

    args = Namespace(
        submit=False,
        state_dir=str(tmp_path / "states"),
        output_dir=str(tmp_path / "out"),
        default_order_krw=10000.0,
        max_new_orders=3,
    )

    payload = loop.run_once(args)

    assert payload["universe_scanned_count"] == 3
    assert payload["oos_candidate_count"] == 2
    assert payload["skipped_non_oos_market_count"] == 1
    assert payload["triggered_candidate_count"] == 2
    assert payload["selected_new_entries"] == [
        {"market": "KRW-AAA", "candidate_id": "aaa_oos", "notional_krw": 10000.0}
    ]
    assert payload["new_submitted_order_count"] == 0
    assert payload["safety"]["effective_cap_krw"] == 30000.0
    assert json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))["status"] == payload["status"]


def test_run_once_uses_realized_profit_effective_cap(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loop, "STATUS_JSON", tmp_path / "status.json")
    monkeypatch.setattr(loop, "STATUS_MD", tmp_path / "status.md")
    monkeypatch.setattr(loop, "EVENT_DIR", tmp_path / "events")
    monkeypatch.setattr(loop, "GLOBAL_DISABLE", tmp_path / "DISABLE_ALL_TRADING")
    (tmp_path / "events").mkdir()
    (tmp_path / "events" / "aaa_event_latest.json").write_text(
        json.dumps({"market": "KRW-AAA", "cumulative_realized_pnl_krw": 10000}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        loop,
        "load_policy",
        lambda: {
            "max_krw": 100000.0,
            "crypto_cap_krw": 100000.0,
            "max_order_krw": 10000.0,
            "max_daily_loss_krw": 20000.0,
            "max_total_loss_krw": 100000.0,
        },
    )
    monkeypatch.setattr(loop, "list_bithumb_universe", lambda: [])
    monkeypatch.setattr(loop, "load_oos_pass_candidates", lambda: [])
    monkeypatch.setattr(loop, "load_open_positions", lambda state_dir: {})
    monkeypatch.setattr(loop, "manage_open_positions", lambda *args, **kwargs: [])

    args = Namespace(
        submit=False,
        state_dir=str(tmp_path / "states"),
        output_dir=str(tmp_path / "out"),
        default_order_krw=10000.0,
        max_new_orders=3,
    )

    payload = loop.run_once(args)

    assert payload["safety"]["base_cap_krw"] == 100000.0
    assert payload["safety"]["effective_cap_krw"] == 105000.0
    assert payload["safety"]["cap_ratchet"]["realized_profit_krw"] == 10000.0


def test_run_once_submit_calls_order_path_for_selected_candidate(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loop, "STATUS_JSON", tmp_path / "status.json")
    monkeypatch.setattr(loop, "STATUS_MD", tmp_path / "status.md")
    monkeypatch.setattr(loop, "GLOBAL_DISABLE", tmp_path / "DISABLE_ALL_TRADING")
    monkeypatch.setattr(
        loop,
        "load_policy",
        lambda: {
            "max_krw": 30000.0,
            "max_order_krw": 10000.0,
            "max_daily_loss_krw": 20000.0,
            "max_total_loss_krw": 100000.0,
        },
    )
    monkeypatch.setattr(loop, "list_bithumb_universe", lambda: ["KRW-AAA"])
    monkeypatch.setattr(
        loop,
        "load_oos_pass_candidates",
        lambda: [
            {
                "candidate_id": "aaa_oos",
                "market": "KRW-AAA",
                "status": "OOS_CANDIDATE_PASS",
                "parameters": {},
                "source_conversion": {"estimated_cagr": 1.0, "estimated_mdd": -0.2},
                "aggregate": {"pass_fold_count": 2},
            }
        ],
    )
    monkeypatch.setattr(loop, "load_open_positions", lambda state_dir: {})
    monkeypatch.setattr(loop, "manage_open_positions", lambda *args, **kwargs: [])
    monkeypatch.setattr(loop, "evaluate_candidate_signal", lambda candidate: ({"triggered": True, "latest_close": 100.0}, {"status": "LIVE_FETCH_OK"}))

    submitted: list[str] = []

    def fake_submit(candidate, signal, *, policy, notional_krw, output_dir):
        submitted.append(candidate["candidate_id"])
        return {
            "market": candidate["market"],
            "candidate_id": candidate["candidate_id"],
            "notional_krw": notional_krw,
            "submitted_count": 1,
        }

    monkeypatch.setattr(loop, "submit_new_entry", fake_submit)

    args = Namespace(
        submit=True,
        state_dir=str(tmp_path / "states"),
        output_dir=str(tmp_path / "out"),
        default_order_krw=10000.0,
        max_new_orders=3,
    )

    payload = loop.run_once(args)

    assert submitted == ["aaa_oos"]
    assert payload["new_submitted_order_count"] == 1
    assert payload["status"] == "BITHUMB_AXIS_AUTOTRADE_SUBMITTED"
