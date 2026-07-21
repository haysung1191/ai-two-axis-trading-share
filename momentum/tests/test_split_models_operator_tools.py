from __future__ import annotations

import json
import shutil
import sys
import types
from pathlib import Path

import pandas as pd

from tools.operations import archive_split_models_operator_handoff as archive_tools
from tools.operations import build_split_models_archive_compare as archive_compare
from tools.operations import build_split_models_archive_compare_packet as archive_compare_packet
from tools.operations import build_split_models_archive_delta as archive_delta
from tools.operations import build_split_models_archive_replay_packet as archive_replay_packet
from tools.operations import build_split_models_archive_status as archive_status
from tools.operations import build_split_models_archive_stability as archive_stability
from tools.operations import build_split_models_capital_readiness as capital_readiness
from tools.operations import build_split_models_initial_entry_preflight as initial_entry_preflight
from tools.operations import build_split_models_initial_entry_report as initial_entry_report
from tools.operations import build_split_models_archive_timeline as archive_timeline
from tools.operations import build_split_models_shadow_report as shadow_report
from tools.operations import execute_split_models_shadow_live_orders as live_execution
from tools.operations import build_split_models_live_packet as live_packet
from tools.operations import build_split_models_live_readiness as live_readiness
from tools.operations import build_split_models_rebalance_orders as rebalance_orders
from tools.operations import check_split_models_archive_consistency as archive_consistency
from tools.operations import build_split_models_shadow_status as shadow_status
from tools.pipelines import run_split_models_operator_handoff as handoff_runner
from tools.pipelines import run_split_models_initial_entry as initial_entry_runner


def test_split_models_operator_tools_build_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    shadow_dir = tmp_path / "shadow"
    archive_dir = tmp_path / "archive"
    shadow_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    _write_json(
        shadow_dir / "shadow_summary.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "health_verdict": "PASS",
            "recent_avg_turnover": 0.96,
            "current_holdings": 8,
            "current_top1_weight": 0.125,
            "current_top3_weight": 0.375,
            "current_dominant_sector": "Industrials",
        },
    )
    _write_json(shadow_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
    _write_json(
        shadow_dir / "shadow_live_transition_summary.json",
        {
            "baseline_variant": "rule_breadth_it_risk_off",
            "candidate_variant": "rule_breadth_it_us5_cap",
            "signal_date": "2026-01-30",
            "weight_turnover": 0.11111111111111113,
        },
    )
    _write_csv(
        shadow_dir / "shadow_live_transition_diff.csv",
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "GILD",
                "Name": "Gilead",
                "Sector": "Health Care",
                "BaselineWeight": 0.1111111111,
                "CandidateWeight": 0.0,
                "WeightDelta": -0.1111111111,
                "Action": "Sell",
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "LMT",
                "Name": "Lockheed Martin",
                "Sector": "Industrials",
                "BaselineWeight": 0.1111111111,
                "CandidateWeight": 0.125,
                "WeightDelta": 0.0138888889,
                "Action": "Add",
            },
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "069500",
                "Name": "069500",
                "Sector": "ETF",
                "BaselineWeight": 0.1111111111,
                "CandidateWeight": 0.125,
                "WeightDelta": 0.0138888889,
                "Action": "Add",
            },
        ],
    )

    monkeypatch.setattr(rebalance_orders, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(live_readiness, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(live_packet, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(shadow_status, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(shadow_status, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_tools, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(archive_tools, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_delta, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_delta, "DELTA_PATH", archive_dir / "archive_latest_delta.json")
    monkeypatch.setattr(archive_stability, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_stability, "REPORT_PATH", archive_dir / "archive_stability_report.json")
    monkeypatch.setattr(archive_timeline, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_timeline, "REPORT_PATH", archive_dir / "archive_timeline_report.json")
    monkeypatch.setattr(archive_consistency, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(archive_consistency, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_consistency, "REPORT_PATH", archive_dir / "archive_consistency_report.json")

    monkeypatch.setattr(sys, "argv", ["build_split_models_rebalance_orders.py", "--total-capital", "100000000"])
    rebalance_orders.main()

    execution_summary = _read_json(shadow_dir / "shadow_rebalance_execution_summary.json")
    assert execution_summary["sell_count"] == 1
    assert execution_summary["buy_count"] == 2
    assert execution_summary["actionable_rows"] == 3

    live_readiness.main()
    readiness = _read_json(shadow_dir / "shadow_live_readiness.json")
    assert readiness["live_readiness_verdict"] == "GO"
    assert readiness["checks_passed"] == readiness["checks_total"] == 7

    live_packet.main()
    packet = (shadow_dir / "shadow_live_transition_packet.md").read_text(encoding="utf-8")
    assert "Split Models Live Transition Packet" in packet
    assert "SELL `GILD`" in packet
    assert "BUY `LMT`" in packet
    _write_json(
        shadow_dir / "shadow_operator_runtime_status.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "live_readiness": "GO",
            "operator_gate_verdict": "PASS",
            "archive_latest_run_id": "20260414T120000",
            "archive_prior_run_id": None,
        },
    )

    class _FakeNow:
        @staticmethod
        def now() -> "_FakeTimestamp":
            return _FakeTimestamp()

    class _FakeTimestamp:
        @staticmethod
        def strftime(fmt: str) -> str:
            assert fmt == "%Y%m%dT%H%M%S"
            return "20260414T120000"

    monkeypatch.setattr(archive_tools, "datetime", _FakeNow)
    archive_tools.main()

    manifest = pd.read_csv(archive_dir / "archive_manifest.csv")
    assert manifest.iloc[0]["BaselineVariant"] == "rule_breadth_it_us5_cap"
    assert manifest.iloc[0]["LiveReadinessVerdict"] == "GO"
    assert manifest.iloc[0]["OperatorGateVerdict"] == "PASS"
    archived_packet = archive_dir / "20260414T120000" / "shadow_live_transition_packet.md"
    assert archived_packet.exists()

    _write_json(
        shadow_dir / "split_models_backtest_summary.json",
        {
            "trading_book": {
                "CAGR": 0.3343,
                "MDD": -0.2524,
                "Sharpe": 1.4482,
            }
        },
    )
    shadow_status.main([])
    output = capsys.readouterr().out
    assert "baseline_variant=rule_breadth_it_us5_cap" in output
    assert "live_readiness=GO" in output
    assert "market_US_sell_orders=1" in output
    assert "operator_gate_verdict=FAIL" in output

    shadow_status.main(["--json"])
    json_output = capsys.readouterr().out
    payload = json.loads(json_output)
    assert payload["baseline_variant"] == "rule_breadth_it_us5_cap"
    assert payload["live_readiness"] == "GO"
    assert payload["market_US_sell_orders"] == 1
    assert payload["operator_gate_verdict"] == "FAIL"
    assert payload["operator_gate_failures"] == [
        "archive_consistency_verdict=None",
        "archive_timeline_verdict=None",
    ]
    archived_runtime_status = archive_dir / "20260414T120000" / "shadow_operator_runtime_status.json"
    assert archived_runtime_status.exists()

    class _FakeNextNow:
        @staticmethod
        def now() -> "_FakeNextTimestamp":
            return _FakeNextTimestamp()

    class _FakeNextTimestamp:
        @staticmethod
        def strftime(fmt: str) -> str:
            assert fmt == "%Y%m%dT%H%M%S"
            return "20260414T120500"

    _write_json(
        shadow_dir / "shadow_summary.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "health_verdict": "PASS",
            "recent_avg_turnover": 0.97,
            "current_holdings": 9,
            "current_top1_weight": 0.125,
            "current_top3_weight": 0.375,
            "current_dominant_sector": "Health Care",
        },
    )
    _write_json(
        shadow_dir / "shadow_operator_runtime_status.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "live_readiness": "GO",
            "current_holdings": 9,
            "operator_gate_verdict": "PASS",
            "archive_latest_run_id": "20260414T120500",
            "archive_prior_run_id": "20260414T120000",
        },
    )
    _write_json(
        archive_dir / "20260414T120000" / "shadow_operator_runtime_status.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "live_readiness": "GO",
            "operator_gate_verdict": "PASS",
            "archive_latest_run_id": "20260414T120000",
            "archive_prior_run_id": None,
        },
    )
    monkeypatch.setattr(archive_tools, "datetime", _FakeNextNow)
    archive_tools.main()
    _write_json(
        archive_dir / "20260414T120500" / "shadow_operator_runtime_status.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "live_readiness": "GO",
            "current_holdings": 9,
            "operator_gate_verdict": "PASS",
            "archive_latest_run_id": "20260414T120500",
            "archive_prior_run_id": "20260414T120000",
        },
    )
    archive_delta.main()
    archive_consistency.main()
    archive_stability.main([])
    archive_timeline.main(["--window", "2"])
    delta_payload = _read_json(archive_dir / "archive_latest_delta.json")
    assert delta_payload["comparison_available"] is True
    assert delta_payload["holdings_change"] == 1
    assert delta_payload["dominant_sector_changed"] is True
    assert delta_payload["operator_gate_changed"] is False
    assert delta_payload["latest_runtime_status"]["current_holdings"] == 9
    consistency_payload = _read_json(archive_dir / "archive_consistency_report.json")
    assert consistency_payload["archive_consistency_verdict"] == "PASS"
    stability_payload = _read_json(archive_dir / "archive_stability_report.json")
    assert stability_payload["archive_stability_verdict"] == "FAIL"
    assert stability_payload["latest_run_id"] == "20260414T120500"
    timeline_payload = _read_json(archive_dir / "archive_timeline_report.json")
    assert timeline_payload["archive_timeline_verdict"] == "PASS"
    assert timeline_payload["latest_run_id"] == "20260414T120500"
    assert len(timeline_payload["timeline"]) == 2

    capsys.readouterr()
    shadow_status.main(["--json"])
    final_status = json.loads(capsys.readouterr().out)
    assert final_status["archive_comparison_available"] is True
    assert final_status["archive_holdings_change"] == 1
    assert final_status["archive_dominant_sector_changed"] is True
    assert final_status["archive_operator_gate_changed"] is False
    assert final_status["archive_consistency_verdict"] == "PASS"
    assert final_status["archive_stability_verdict"] == "FAIL"
    assert final_status["archive_timeline_verdict"] == "PASS"
    assert final_status["operator_gate_verdict"] == "PASS"
    assert final_status["operator_gate_failures"] == []

    live_packet.main()
    refreshed_packet = (shadow_dir / "shadow_live_transition_packet.md").read_text(encoding="utf-8")
    assert "archive consistency verdict" in refreshed_packet
    assert "archive stability verdict" in refreshed_packet
    assert "archive timeline verdict" in refreshed_packet
    shutil.copy2(archive_dir / "archive_consistency_report.json", archive_dir / "20260414T120500" / "archive_consistency_report.json")
    shutil.copy2(archive_dir / "archive_stability_report.json", archive_dir / "20260414T120500" / "archive_stability_report.json")
    assert (archive_dir / "20260414T120500" / "archive_consistency_report.json").exists()
    assert (archive_dir / "20260414T120500" / "archive_stability_report.json").exists()


def test_split_models_operator_handoff_runner_invokes_steps_in_order(monkeypatch) -> None:
    calls: list[list[str]] = []
    runtime_status_calls: list[bool] = []
    sync_calls: list[bool] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == handoff_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(handoff_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(handoff_runner.sys, "executable", "python")
    monkeypatch.setattr(handoff_runner, "_write_runtime_status", lambda print_json=False: runtime_status_calls.append(print_json))
    monkeypatch.setattr(handoff_runner, "_sync_files_to_latest_archive", lambda paths: sync_calls.append(True))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/run_split_models_operator_handoff.py",
            "--total-capital",
            "100000000",
            "--refresh-shadow",
            "--refresh-reference",
        ],
    )

    handoff_runner.main()

    assert calls == [
        ["python", "tools/operations/build_split_models_shadow_report.py"],
        ["python", "tools/analysis/analyze_split_models_live_transition.py", "--canonical-shadow"],
        ["python", "tools/operations/build_split_models_rebalance_orders.py", "--total-capital", "100000000.0"],
        ["python", "tools/operations/check_split_models_shadow_drift.py", "--refresh-reference"],
        ["python", "tools/operations/build_split_models_live_readiness.py"],
        ["python", "tools/operations/build_split_models_live_packet.py"],
        ["python", "tools/operations/archive_split_models_operator_handoff.py"],
        ["python", "tools/operations/build_split_models_archive_delta.py"],
        ["python", "tools/operations/build_split_models_archive_delta.py"],
        ["python", "tools/operations/check_split_models_archive_consistency.py"],
        ["python", "tools/operations/build_split_models_archive_stability.py"],
        ["python", "tools/operations/build_split_models_archive_timeline.py"],
        ["python", "tools/operations/build_split_models_archive_replay_packet.py"],
        ["python", "tools/operations/build_split_models_live_packet.py"],
        ["python", "tools/operations/build_split_models_archive_delta.py"],
    ]
    assert runtime_status_calls == [False, False, False]
    assert sync_calls == [True, True]


def test_split_models_initial_entry_runner_invokes_capital_readiness_and_adaptive_plan(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == initial_entry_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(initial_entry_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(initial_entry_runner.sys, "executable", "python")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/run_split_models_initial_entry.py",
            "--total-capital",
            "1000000",
        ],
    )

    initial_entry_runner.main()

    assert calls == [
        [
            "python",
            "tools/operations/build_split_models_capital_readiness.py",
            "--book-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_current_book.csv"),
            "--details-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_capital_readiness_1000000.csv"),
            "--summary-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_capital_readiness_summary_1000000.json"),
            "--total-capital",
            "1000000.0",
        ],
        [
            "python",
            "tools/operations/execute_split_models_shadow_live_orders.py",
            "--initial-book-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_current_book.csv"),
            "--plan-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_plan_1000000.csv"),
            "--summary-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_summary_1000000.json"),
            "--submit-results-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_submit_results_1000000.csv"),
            "--total-capital",
            "1000000.0",
            "--adaptive-initial-entry",
        ],
        [
            "python",
            "tools/operations/build_split_models_initial_entry_preflight.py",
            "--execution-summary-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_summary_1000000.json"),
            "--execution-plan-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_plan_1000000.csv"),
            "--out-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_preflight_1000000.json"),
        ],
        [
            "python",
            "tools/operations/build_split_models_initial_entry_report.py",
            "--capital-readiness-summary-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_capital_readiness_summary_1000000.json"),
            "--preflight-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_preflight_1000000.json"),
            "--plan-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_plan_1000000.csv"),
            "--out-path",
            str(initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_report_1000000.md"),
            "--capital-slug",
            "1000000",
        ],
    ]


def test_split_models_initial_entry_runner_can_disable_adaptive(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == initial_entry_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(initial_entry_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(initial_entry_runner.sys, "executable", "python")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/run_split_models_initial_entry.py",
            "--total-capital",
            "1000000",
            "--disable-adaptive",
        ],
    )

    initial_entry_runner.main()

    assert "--adaptive-initial-entry" not in calls[1]
    assert calls[2][1] == "tools/operations/build_split_models_initial_entry_preflight.py"
    assert calls[3][1] == "tools/operations/build_split_models_initial_entry_report.py"


def test_split_models_initial_entry_runner_can_submit_live(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == initial_entry_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(initial_entry_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(initial_entry_runner.sys, "executable", "python")
    monkeypatch.setattr(initial_entry_runner, "_enforce_preflight_pass", lambda path, **kwargs: {"preflight_verdict": "PASS"})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/run_split_models_initial_entry.py",
            "--total-capital",
            "1000000",
            "--submit-live",
        ],
    )

    initial_entry_runner.main()

    assert "--submit-live" not in calls[1]
    assert calls[2][1] == "tools/operations/build_split_models_initial_entry_preflight.py"
    assert calls[3][1] == "tools/operations/build_split_models_initial_entry_report.py"
    assert "--submit-existing-plan-path" in calls[4]
    assert "--submit-live" in calls[4]
    assert "--submit-results-path" in calls[4]
    submit_results_index = calls[4].index("--submit-results-path") + 1
    assert calls[4][submit_results_index] == str(
        initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_submit_results_1000000.csv"
    )
    submit_plan_index = calls[4].index("--submit-existing-plan-path") + 1
    assert calls[4][submit_plan_index] == str(
        initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_plan_1000000.csv"
    )
    assert calls[5][1] == "tools/operations/build_split_models_initial_entry_report.py"
    assert "--submit-summary-path" in calls[5]
    submit_summary_index = calls[5].index("--submit-summary-path") + 1
    assert calls[5][submit_summary_index] == str(
        initial_entry_runner.SHADOW_DIR / "shadow_live_initial_adaptive_submit_summary_1000000.json"
    )
    assert "--submit-results-path" in calls[5]


def test_split_models_initial_entry_runner_writes_latest_index(tmp_path: Path) -> None:
    latest_index_path = tmp_path / "shadow_live_initial_adaptive_latest.json"
    capital_readiness_details_path = tmp_path / "capital_readiness.csv"
    capital_readiness_summary_path = tmp_path / "capital_readiness_summary.json"
    plan_path = tmp_path / "plan.csv"
    summary_path = tmp_path / "summary.json"
    preflight_path = tmp_path / "preflight.json"
    report_path = tmp_path / "report.md"

    capital_readiness_details_path.write_text("ok", encoding="utf-8")
    capital_readiness_summary_path.write_text("{}", encoding="utf-8")
    plan_path.write_text("a,b\n1,2\n", encoding="utf-8")
    summary_path.write_text('{"x":1}', encoding="utf-8")
    preflight_path.write_text('{"x":2}', encoding="utf-8")
    report_path.write_text("# report\n", encoding="utf-8")

    initial_entry_runner._write_latest_index(
        latest_index_path,
        capital_slug="1000000",
        total_capital=1000000,
        capital_readiness_details_path=str(capital_readiness_details_path),
        capital_readiness_summary_path=str(capital_readiness_summary_path),
        plan_path=str(plan_path),
        summary_path=str(summary_path),
        preflight_path=str(preflight_path),
        report_path=str(report_path),
        submit_results_path="submit_results.csv",
        submit_summary_path="submit_summary.json",
        submit_live=False,
    )

    payload = _read_json(latest_index_path)
    assert payload["capital_slug"] == "1000000"
    assert payload["total_capital"] == 1000000.0
    assert payload["plan_path"] == str(plan_path)
    assert payload["report_path"] == str(report_path)
    assert payload["submit_live_requested"] is False
    assert payload["check_timestamp"] is None
    assert payload["check_json_path"] is None
    assert payload["plan_sha256"] == initial_entry_runner._sha256_file(plan_path)


def test_split_models_initial_entry_runner_submit_live_stops_on_failed_preflight(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == initial_entry_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(initial_entry_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(initial_entry_runner.sys, "executable", "python")
    monkeypatch.setattr(
        initial_entry_runner,
        "_enforce_preflight_pass",
        lambda path, **kwargs: (_ for _ in ()).throw(SystemExit("initial_entry_preflight_failed: skipped_count=1")),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/run_split_models_initial_entry.py",
            "--total-capital",
            "1000000",
            "--submit-live",
        ],
    )

    try:
        initial_entry_runner.main()
    except SystemExit as exc:
        assert "initial_entry_preflight_failed" in str(exc)
    else:
        raise AssertionError("Expected SystemExit when preflight fails")

    assert len(calls) == 4
    assert all("--submit-live" not in call for call in calls)


def test_split_models_initial_entry_preflight_passes_for_ready_dry_run() -> None:
    runtime_status = {
        "live_readiness": "GO",
        "operator_gate_verdict": "PASS",
        "archive_stability_verdict": "FAIL",
    }
    execution_summary = {
        "plan_mode": "initial_entry",
        "submit_mode": "dry_run",
        "planned_count": 3,
        "skipped_count": 0,
        "adaptive_selection_enabled": True,
        "adaptive_selected_symbols": ["DOW", "XOM", "COP"],
    }
    execution_plan = pd.DataFrame(
        [
            {"Market": "US", "Symbol": "DOW", "Status": "PLANNED", "Quantity": 6, "EstimatedOrderNotionalKRW": 311386.08},
            {"Market": "US", "Symbol": "XOM", "Status": "PLANNED", "Quantity": 1, "EstimatedOrderNotionalKRW": 213480.232},
            {"Market": "US", "Symbol": "COP", "Status": "PLANNED", "Quantity": 1, "EstimatedOrderNotionalKRW": 169163.112},
        ]
    )

    payload = initial_entry_preflight.build_preflight_payload(runtime_status, execution_summary, execution_plan)

    assert payload["preflight_verdict"] == "PASS"
    assert payload["preflight_failures"] == []
    assert payload["planned_symbols"] == ["DOW", "XOM", "COP"]
    assert payload["planned_quantity_total"] == 8


def test_split_models_initial_entry_preflight_fails_for_skipped_rows() -> None:
    runtime_status = {
        "live_readiness": "GO",
        "operator_gate_verdict": "PASS",
    }
    execution_summary = {
        "plan_mode": "initial_entry",
        "submit_mode": "dry_run",
        "planned_count": 1,
        "skipped_count": 2,
        "adaptive_selection_enabled": False,
    }
    execution_plan = pd.DataFrame(
        [
            {"Market": "US", "Symbol": "DOW", "Status": "PLANNED", "Quantity": 1, "EstimatedOrderNotionalKRW": 100.0},
            {"Market": "US", "Symbol": "GEV", "Status": "SKIPPED", "Quantity": 0, "EstimatedOrderNotionalKRW": 0.0},
        ]
    )

    payload = initial_entry_preflight.build_preflight_payload(runtime_status, execution_summary, execution_plan)

    assert payload["preflight_verdict"] == "FAIL"
    assert "skipped_count=2" in payload["preflight_failures"]


def test_split_models_initial_entry_report_contains_operational_summary() -> None:
    capital_readiness = {
        "fundable_count_at_capital": 2,
        "fundable_symbols_at_capital": ["DOW", "COP"],
        "min_capital_all_holdings_one_share_krw": 7309045,
        "max_single_name_one_share_cost_krw": 1461808.95,
    }
    preflight = {
        "preflight_verdict": "PASS",
        "live_readiness": "GO",
        "operator_gate_verdict": "PASS",
        "submit_mode": "dry_run",
        "planned_count": 3,
        "skipped_count": 0,
        "planned_symbols": ["DOW", "XOM", "COP"],
        "planned_quantity_total": 8,
        "estimated_order_notional_krw_total": 694029.424,
        "execution_plan_path": "plan.csv",
        "execution_plan_sha256": "abc",
        "execution_summary_path": "summary.json",
        "execution_summary_sha256": "def",
        "archive_stability_verdict": "FAIL",
    }
    plan = pd.DataFrame(
        [
            {"Symbol": "DOW", "ExecutionSide": "BUY", "Quantity": 6, "EstimatedOrderNotionalKRW": 311386.08, "ResolvedExchange": "NYSE", "Status": "PLANNED"},
            {"Symbol": "XOM", "ExecutionSide": "BUY", "Quantity": 1, "EstimatedOrderNotionalKRW": 213480.232, "ResolvedExchange": "NYSE", "Status": "PLANNED"},
        ]
    )

    submit_summary = {
        "submit_mode": "live",
        "submitted_count": 3,
        "failed_count": 0,
        "submitted_plan_path": "plan.csv",
        "submitted_plan_sha256": "ghi",
        "preflight_path": "preflight.json",
        "preflight_sha256": "jkl",
        "check_timestamp": "20260419T145433",
        "check_json_path": "check_latest.json",
        "check_md_path": "check_latest.md",
        "check_history_json_path": "check_20260419T145433.json",
        "check_history_md_path": "check_20260419T145433.md",
    }
    submit_results = pd.DataFrame(
        [
            {
                "Symbol": "DOW",
                "ExecutionSide": "BUY",
                "Quantity": 6,
                "SubmitStatus": "SUBMITTED",
                "OrderNo": "12345",
                "SubmitReason": "",
            }
        ]
    )
    text = initial_entry_report.build_report_text(
        capital_readiness,
        preflight,
        plan,
        capital_slug="1000000",
        submit_summary=submit_summary,
        submit_results=submit_results,
    )

    assert "# Split Models Initial Entry Report" in text
    assert "Preflight verdict: `PASS`" in text
    assert "Fundable symbols at capital: `DOW, COP`" in text
    assert "| DOW | BUY | 6 |" in text
    assert "## Submission" in text
    assert "Submitted count: `3`" in text
    assert "Check timestamp used at submit: `20260419T145433`" in text
    assert "Check history Markdown path: `check_20260419T145433.md`" in text
    assert "| DOW | BUY | 6 | SUBMITTED | 12345 |  |" in text


def test_split_models_initial_entry_report_main_includes_submit_section(tmp_path: Path) -> None:
    capital_readiness_path = tmp_path / "capital_readiness_summary.json"
    preflight_path = tmp_path / "preflight.json"
    plan_path = tmp_path / "plan.csv"
    submit_summary_path = tmp_path / "submit_summary.json"
    submit_results_path = tmp_path / "submit_results.csv"
    report_path = tmp_path / "report.md"

    _write_json(
        capital_readiness_path,
        {
            "evaluated_total_capital": 1000000,
            "fundable_count_at_capital": 2,
            "fundable_symbols_at_capital": ["DOW", "COP"],
            "min_capital_all_holdings_one_share_krw": 7309045,
            "max_single_name_one_share_cost_krw": 1461808.95,
        },
    )
    _write_json(
        preflight_path,
        {
            "preflight_verdict": "PASS",
            "live_readiness": "GO",
            "operator_gate_verdict": "PASS",
            "submit_mode": "dry_run",
            "planned_count": 1,
            "skipped_count": 0,
            "planned_symbols": ["DOW"],
            "planned_quantity_total": 6,
            "estimated_order_notional_krw_total": 311386.08,
            "execution_plan_path": str(plan_path),
            "execution_plan_sha256": "abc",
            "execution_summary_path": "summary.json",
            "execution_summary_sha256": "def",
            "archive_stability_verdict": "FAIL",
        },
    )
    _write_csv(
        plan_path,
        [
            {
                "Symbol": "DOW",
                "ExecutionSide": "BUY",
                "Quantity": 6,
                "EstimatedOrderNotionalKRW": 311386.08,
                "ResolvedExchange": "NYSE",
                "Status": "PLANNED",
            }
        ],
    )
    _write_json(
        submit_summary_path,
        {
            "submit_mode": "live",
            "submitted_count": 1,
            "failed_count": 0,
            "submitted_plan_path": str(plan_path),
            "submitted_plan_sha256": "ghi",
            "preflight_path": str(preflight_path),
            "preflight_sha256": "jkl",
            "check_timestamp": "20260419T145433",
            "check_json_path": "check_latest.json",
            "check_md_path": "check_latest.md",
            "check_history_json_path": "check_20260419T145433.json",
            "check_history_md_path": "check_20260419T145433.md",
        },
    )
    _write_csv(
        submit_results_path,
        [
            {
                "Symbol": "DOW",
                "ExecutionSide": "BUY",
                "Quantity": 6,
                "SubmitStatus": "SUBMITTED",
                "OrderNo": "12345",
                "SubmitReason": "",
            }
        ],
    )

    initial_entry_report.main(
        [
            "--capital-readiness-summary-path",
            str(capital_readiness_path),
            "--preflight-path",
            str(preflight_path),
            "--plan-path",
            str(plan_path),
            "--out-path",
            str(report_path),
            "--capital-slug",
            "1000000",
            "--submit-summary-path",
            str(submit_summary_path),
            "--submit-results-path",
            str(submit_results_path),
        ]
    )

    report_text = report_path.read_text(encoding="utf-8")
    assert "## Submission" in report_text
    assert "Submit mode: `live`" in report_text
    assert "Submitted count: `1`" in report_text
    assert "Check timestamp used at submit: `20260419T145433`" in report_text
    assert "| Symbol | Side | Qty | Submit Status | Order No | Reason |" in report_text
    assert "DOW" in report_text
    assert "SUBMITTED" in report_text
    assert "12345" in report_text


def test_split_models_live_execution_can_submit_existing_plan(tmp_path: Path, monkeypatch) -> None:
    plan_path = tmp_path / "existing_plan.csv"
    summary_path = tmp_path / "submit_summary.json"
    results_path = tmp_path / "submit_results.csv"
    preflight_path = tmp_path / "preflight.json"
    _write_csv(
        plan_path,
        [
            {
                "Market": "US",
                "Symbol": "DOW",
                "ResolvedSymbol": "DOW",
                "ExecutionSide": "BUY",
                "Name": "Dow",
                "DeltaNotional": 333333.33,
                "Status": "PLANNED",
                "Reason": "",
                "ResolvedExchange": "NYSE",
                "ResolvedPrice": 35.6,
                "FXRate": 1457.8,
                "Quantity": 6,
                "EstimatedOrderNotionalKRW": 311386.08,
            }
        ],
    )
    _write_json(preflight_path, {"preflight_verdict": "PASS"})

    runtime_status_path = tmp_path / "shadow_operator_runtime_status.json"
    _write_json(runtime_status_path, {"live_readiness": "GO", "operator_gate_verdict": "PASS"})

    class _FakeApi:
        def __init__(self) -> None:
            pass

        def place_overseas_order(self, symbol, side, quantity, ovrs_excg_cd, price):
            assert symbol == "DOW"
            assert side == "BUY"
            assert quantity == 6
            assert ovrs_excg_cd == "NYSE"
            assert price == 35.6
            return {"rt_cd": "0", "msg_cd": "0", "msg1": "ok", "output": {"ODNO": "12345"}}

    monkeypatch.setattr(live_execution, "KISApi", _FakeApi)
    monkeypatch.setattr(live_execution, "RUNTIME_STATUS_PATH", runtime_status_path)
    monkeypatch.setattr(live_execution.config, "ENV", "PROD")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "execute_split_models_shadow_live_orders.py",
            "--submit-existing-plan-path",
            str(plan_path),
            "--summary-path",
            str(summary_path),
            "--submit-results-path",
            str(results_path),
            "--preflight-path",
            str(preflight_path),
            "--submit-live",
        ],
    )

    live_execution.main()

    written_summary = _read_json(summary_path)
    written_results = pd.read_csv(results_path)
    assert written_summary["plan_mode"] == "existing_plan_submit"
    assert written_summary["submitted_count"] == 1
    assert written_summary["submitted_plan_path"] == str(plan_path)
    assert written_summary["preflight_path"] == str(preflight_path)
    assert "submitted_plan_sha256" in written_summary
    assert "preflight_sha256" in written_summary
    assert written_results.iloc[0]["SubmitStatus"] == "SUBMITTED"


def test_split_models_initial_entry_runner_enforce_preflight_pass_raises(tmp_path: Path) -> None:
    preflight_path = tmp_path / "preflight.json"
    preflight_path.write_text(
        json.dumps(
            {
                "preflight_verdict": "FAIL",
                "preflight_failures": ["skipped_count=1"],
            }
        ),
        encoding="utf-8",
    )

    try:
        initial_entry_runner._enforce_preflight_pass(preflight_path)
    except SystemExit as exc:
        assert "initial_entry_preflight_failed" in str(exc)
        assert "skipped_count=1" in str(exc)
    else:
        raise AssertionError("Expected SystemExit when preflight verdict is FAIL")


def test_split_models_initial_entry_runner_enforce_preflight_pass_raises_on_plan_hash_mismatch(tmp_path: Path) -> None:
    preflight_path = tmp_path / "preflight.json"
    plan_path = tmp_path / "plan.csv"
    summary_path = tmp_path / "summary.json"
    plan_path.write_text("a,b\n1,2\n", encoding="utf-8")
    summary_path.write_text('{"ok": true}', encoding="utf-8")
    preflight_path.write_text(
        json.dumps(
            {
                "preflight_verdict": "PASS",
                "preflight_failures": [],
                "execution_plan_sha256": "bad-plan-hash",
                "execution_summary_sha256": initial_entry_runner._sha256_file(summary_path),
            }
        ),
        encoding="utf-8",
    )

    try:
        initial_entry_runner._enforce_preflight_pass(preflight_path, plan_path=plan_path, summary_path=summary_path)
    except SystemExit as exc:
        assert "execution_plan_hash_mismatch" in str(exc)
    else:
        raise AssertionError("Expected SystemExit when plan hash mismatches preflight")


def test_split_models_initial_entry_runner_enforce_preflight_pass_raises_on_summary_hash_mismatch(tmp_path: Path) -> None:
    preflight_path = tmp_path / "preflight.json"
    plan_path = tmp_path / "plan.csv"
    summary_path = tmp_path / "summary.json"
    plan_path.write_text("a,b\n1,2\n", encoding="utf-8")
    summary_path.write_text('{"ok": true}', encoding="utf-8")
    preflight_path.write_text(
        json.dumps(
            {
                "preflight_verdict": "PASS",
                "preflight_failures": [],
                "execution_plan_sha256": initial_entry_runner._sha256_file(plan_path),
                "execution_summary_sha256": "bad-summary-hash",
            }
        ),
        encoding="utf-8",
    )

    try:
        initial_entry_runner._enforce_preflight_pass(preflight_path, plan_path=plan_path, summary_path=summary_path)
    except SystemExit as exc:
        assert "execution_summary_hash_mismatch" in str(exc)
    else:
        raise AssertionError("Expected SystemExit when summary hash mismatches preflight")


def test_split_models_live_execution_plan_builds_and_skips_invalid_rows(tmp_path: Path) -> None:
    orders_path = tmp_path / "shadow_rebalance_orders.csv"
    pd.DataFrame(
        [
            {
                "ExecutionSide": "BUY",
                "Action": "Add",
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "069500",
                "Name": "069500",
                "Sector": "ETF",
                "DeltaNotional": 1_400_000,
            },
            {
                "ExecutionSide": "BUY",
                "Action": "Add",
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "0000J0",
                "Name": "0000J0",
                "Sector": "ETF",
                "DeltaNotional": 1_400_000,
            },
            {
                "ExecutionSide": "SELL",
                "Action": "Sell",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "GILD",
                "Name": "Gilead",
                "Sector": "Health Care",
                "DeltaNotional": -11_111_111.11,
            },
        ]
    ).to_csv(orders_path, index=False, encoding="utf-8-sig")

    class _FakeApi:
        def get_domestic_quote(self, symbol):
            assert symbol in {"069500", "006380"}
            return {"price": 100000.0}

        def get_overseas_quote(self, exchange_code, symbol):
            assert exchange_code == "NAS"
            assert symbol == "GILD"
            return {"price": 100.0}

        def get_usd_krw_rate(self):
            return 1000.0

    plan, summary = live_execution._build_plan(
        live_execution._load_orders(orders_path),
        _FakeApi(),
        {},
    )

    assert summary["planned_count"] == 3
    assert summary["skipped_count"] == 0
    assert "invalid_kr_symbol" not in summary["blocked_reasons"]

    kr_row = plan.loc[plan["Symbol"] == "069500"].iloc[0]
    assert int(kr_row["Quantity"]) == 14

    kr_alias_row = plan.loc[plan["Symbol"] == "0000J0"].iloc[0]
    assert kr_alias_row["ResolvedSymbol"] == "006380"
    assert int(kr_alias_row["Quantity"]) == 14

    us_row = plan.loc[plan["Symbol"] == "GILD"].iloc[0]
    assert int(us_row["Quantity"]) == 111


def test_split_models_live_execution_initial_book_respects_total_capital(tmp_path: Path) -> None:
    book_path = tmp_path / "shadow_current_book.csv"
    pd.DataFrame(
        [
            {
                "SignalDate": "2026-01-30",
                "NextDate": "2026-02-27",
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "0000J0",
                "Name": "PLUS 한화그룹주",
                "Sector": "ETF",
                "TargetWeight": 0.5,
            },
            {
                "SignalDate": "2026-01-30",
                "NextDate": "2026-02-27",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "CAT",
                "Name": "Caterpillar",
                "Sector": "Industrials",
                "TargetWeight": 0.5,
            },
        ]
    ).to_csv(book_path, index=False, encoding="utf-8-sig")

    class _FakeApi:
        def get_domestic_quote(self, symbol):
            assert symbol == "006380"
            return {"price": 5000.0}

        def get_overseas_quote(self, exchange_code, symbol):
            assert exchange_code == "NYS"
            assert symbol == "CAT"
            return {"price": 100.0}

        def get_usd_krw_rate(self):
            return 1000.0

    initial_orders = live_execution._load_initial_book(book_path, 1_000_000)
    plan, summary = live_execution._build_plan(initial_orders, _FakeApi(), {})

    assert summary["planned_count"] == 2
    assert summary["skipped_count"] == 0
    kr_row = plan.loc[plan["Symbol"] == "0000J0"].iloc[0]
    assert kr_row["ResolvedSymbol"] == "006380"
    assert int(kr_row["Quantity"]) == 100
    us_row = plan.loc[plan["Symbol"] == "CAT"].iloc[0]
    assert int(us_row["Quantity"]) == 5


def test_split_models_live_execution_initial_book_uses_added_us_exchange_mappings(tmp_path: Path) -> None:
    book_path = tmp_path / "shadow_current_book.csv"
    pd.DataFrame(
        [
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "DOW",
                "Name": "Dow",
                "Sector": "Materials",
                "TargetWeight": 0.34,
            },
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "XOM",
                "Name": "Exxon Mobil Corp.",
                "Sector": "Energy",
                "TargetWeight": 0.33,
            },
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "COP",
                "Name": "ConocoPhillips",
                "Sector": "Energy",
                "TargetWeight": 0.33,
            },
        ]
    ).to_csv(book_path, index=False, encoding="utf-8-sig")

    class _FakeApi:
        def get_overseas_quote(self, exchange_code, symbol):
            assert exchange_code == "NYS"
            prices = {
                "DOW": 50.0,
                "XOM": 100.0,
                "COP": 120.0,
            }
            return {"price": prices[symbol]}

        def get_usd_krw_rate(self):
            return 1000.0

    initial_orders = live_execution._load_initial_book(book_path, 1_000_000)
    plan, summary = live_execution._build_plan(initial_orders, _FakeApi(), {})

    assert summary["planned_count"] == 3
    assert summary["skipped_count"] == 0
    assert "missing_us_exchange_mapping" not in summary["blocked_reasons"]
    assert set(plan["ResolvedExchange"]) == {"NYSE"}
    assert int(plan.loc[plan["Symbol"] == "DOW", "Quantity"].iloc[0]) == 6
    assert int(plan.loc[plan["Symbol"] == "XOM", "Quantity"].iloc[0]) == 3
    assert int(plan.loc[plan["Symbol"] == "COP", "Quantity"].iloc[0]) == 2


def test_split_models_live_execution_adaptive_initial_entry_selects_affordable_subset() -> None:
    book = pd.DataFrame(
        [
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "DOW",
                "Name": "Dow",
                "Sector": "Materials",
                "MomentumScore": 0.1583,
                "FlowScore": 0.4582,
                "MAD63": 0.0207,
                "TargetWeight": 0.2,
            },
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "GEV",
                "Name": "GE Vernova",
                "Sector": "Industrials",
                "MomentumScore": 0.1517,
                "FlowScore": 0.1785,
                "MAD63": 0.0186,
                "TargetWeight": 0.2,
            },
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "CAT",
                "Name": "Caterpillar",
                "Sector": "Industrials",
                "MomentumScore": 0.1113,
                "FlowScore": 0.1629,
                "MAD63": 0.0153,
                "TargetWeight": 0.2,
            },
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "XOM",
                "Name": "Exxon Mobil Corp.",
                "Sector": "Energy",
                "MomentumScore": 0.0989,
                "FlowScore": 0.2510,
                "MAD63": 0.0136,
                "TargetWeight": 0.2,
            },
            {
                "SignalDate": "2026-03-31",
                "NextDate": "2026-04-17",
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "COP",
                "Name": "ConocoPhillips",
                "Sector": "Energy",
                "MomentumScore": 0.0853,
                "FlowScore": 0.2441,
                "MAD63": 0.0122,
                "TargetWeight": 0.2,
            },
        ]
    )

    class _FakeApi:
        def get_overseas_quote(self, exchange_code: str, symbol: str) -> dict[str, object]:
            assert exchange_code == "NYS"
            prices = {
                "DOW": 35.6,
                "GEV": 1002.75,
                "CAT": 794.65,
                "XOM": 146.44,
                "COP": 116.04,
            }
            return {"price": prices[symbol]}

        def get_usd_krw_rate(self) -> float:
            return 1457.8

    orders, adaptive_summary = live_execution._select_adaptive_initial_book(book, _FakeApi(), {}, 1_000_000)
    plan, summary = live_execution._build_plan(orders, _FakeApi(), {})
    summary.update(adaptive_summary)

    assert summary["adaptive_selection_enabled"] is True
    assert summary["adaptive_selected_count"] == 3
    assert summary["adaptive_selected_symbols"] == ["DOW", "XOM", "COP"]
    assert summary["adaptive_unselected_symbols"] == ["GEV", "CAT"]
    assert summary["planned_count"] == 3
    assert summary["skipped_count"] == 0

    quantities = dict(zip(plan["Symbol"], plan["Quantity"].astype(int), strict=False))
    assert quantities == {"DOW": 6, "XOM": 1, "COP": 1}


def test_split_models_live_execution_main_supports_adaptive_initial_entry(tmp_path: Path, monkeypatch) -> None:
    book_path = tmp_path / "shadow_current_book.csv"
    plan_path = tmp_path / "shadow_live_adaptive_plan.csv"
    summary_path = tmp_path / "shadow_live_adaptive_summary.json"
    _write_csv(
        book_path,
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "DOW",
                "Name": "Dow",
                "Sector": "Materials",
                "MomentumScore": 0.15,
                "FlowScore": 0.45,
                "MAD63": 0.02,
                "TargetWeight": 0.5,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "GEV",
                "Name": "GE Vernova",
                "Sector": "Industrials",
                "MomentumScore": 0.14,
                "FlowScore": 0.18,
                "MAD63": 0.02,
                "TargetWeight": 0.5,
            },
        ],
    )

    class _FakeApi:
        def __init__(self) -> None:
            pass

        def get_overseas_quote(self, exchange_code: str, symbol: str) -> dict[str, object]:
            prices = {"DOW": 35.6, "GEV": 1002.75}
            return {"price": prices[symbol]}

        def get_usd_krw_rate(self) -> float:
            return 1457.8

    monkeypatch.setattr(live_execution, "KISApi", _FakeApi)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "execute_split_models_shadow_live_orders.py",
            "--initial-book-path",
            str(book_path),
            "--adaptive-initial-entry",
            "--plan-path",
            str(plan_path),
            "--summary-path",
            str(summary_path),
            "--total-capital",
            "1000000",
        ],
    )

    live_execution.main()

    written_plan = pd.read_csv(plan_path)
    written_summary = _read_json(summary_path)
    assert written_summary["adaptive_selection_enabled"] is True
    assert written_summary["adaptive_selected_symbols"] == ["DOW"]
    assert written_summary["planned_count"] == 1
    assert written_summary["skipped_count"] == 0
    assert written_plan["Symbol"].tolist() == ["DOW"]
    assert int(written_plan.iloc[0]["Quantity"]) == 19


def test_split_models_health_checks_accept_float_noise_on_threshold() -> None:
    summary = {
        "current_holdings": 5,
        "current_top1_weight": 0.2,
        "current_top3_weight": 0.6000000000000001,
        "recent_avg_turnover": 0.9,
        "recent_cagr_proxy": 0.2,
        "current_max_sector_weight": 0.4,
    }
    turnover_monitor = pd.DataFrame(
        [
            {
                "Holdings": 5,
                "Top1Weight": 0.2,
                "Top3Weight": 0.6000000000000001,
                "MaxSectorWeight": 0.4,
            }
        ]
    )

    checks = shadow_report._health_checks(summary, turnover_monitor)
    top3_check = checks.loc[checks["Metric"] == "current_top3_weight"].iloc[0]
    recent_top3_check = checks.loc[checks["Metric"] == "recent_max_top3_weight"].iloc[0]

    assert int(top3_check["Passed"]) == 1
    assert int(recent_top3_check["Passed"]) == 1


def test_split_models_live_readiness_accepts_float_noise_on_threshold(tmp_path: Path, monkeypatch) -> None:
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir(parents=True)
    _write_json(
        shadow_dir / "shadow_summary.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "health_verdict": "PASS",
            "recent_avg_turnover": 0.9493055555555556,
            "current_holdings": 5,
            "current_top1_weight": 0.2,
            "current_top3_weight": 0.6000000000000001,
            "current_dominant_sector": "Industrials",
        },
    )
    _write_json(shadow_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
    _write_json(shadow_dir / "shadow_live_transition_summary.json", {"weight_turnover": 0.11111111111111113})
    _write_json(shadow_dir / "shadow_rebalance_execution_summary.json", {"actionable_rows": 9})
    monkeypatch.setattr(live_readiness, "SHADOW_DIR", shadow_dir)

    live_readiness.main()
    readiness = _read_json(shadow_dir / "shadow_live_readiness.json")

    assert readiness["live_readiness_verdict"] == "GO"
    assert readiness["checks_passed"] == readiness["checks_total"] == 7


def test_split_models_shadow_status_writes_runtime_file_and_tolerates_empty_market_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    shadow_dir = tmp_path / "shadow"
    archive_dir = tmp_path / "archive"
    shadow_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    _write_json(
        shadow_dir / "shadow_summary.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "health_verdict": "PASS",
            "current_holdings": 5,
            "current_dominant_sector": "Industrials",
        },
    )
    _write_json(shadow_dir / "split_models_backtest_summary.json", {"trading_book": {"CAGR": 0.33, "MDD": -0.25, "Sharpe": 1.44}})
    _write_json(shadow_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
    _write_json(shadow_dir / "shadow_live_readiness.json", {"live_readiness_verdict": "GO"})
    _write_json(shadow_dir / "shadow_live_transition_summary.json", {"weight_turnover": 0.11})
    _write_json(shadow_dir / "shadow_rebalance_execution_summary.json", {"actionable_rows": 6})
    (shadow_dir / "shadow_rebalance_market_summary.csv").write_text("", encoding="utf-8")
    _write_json(archive_dir / "archive_consistency_report.json", {"archive_consistency_verdict": "PASS"})
    _write_json(archive_dir / "archive_stability_report.json", {"archive_stability_verdict": "PASS", "latest_run_id": "20260419T100014", "window": 5})
    _write_json(archive_dir / "archive_timeline_report.json", {"archive_timeline_verdict": "PASS", "latest_run_id": "20260419T100014", "window": 8})

    monkeypatch.setattr(shadow_status, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(shadow_status, "ARCHIVE_DIR", archive_dir)

    shadow_status.main(["--write-runtime-status"])
    output = capsys.readouterr().out
    assert "operator_gate_verdict=PASS" in output

    runtime_payload = _read_json(shadow_dir / "shadow_operator_runtime_status.json")
    assert runtime_payload["live_readiness"] == "GO"
    assert runtime_payload["operator_gate_verdict"] == "PASS"


def test_archive_split_models_operator_handoff_syncs_latest_archive(tmp_path: Path, monkeypatch, capsys) -> None:
    shadow_dir = tmp_path / "shadow"
    archive_dir = tmp_path / "archive"
    latest_dir = archive_dir / "20260419T111700"
    shadow_dir.mkdir(parents=True)
    latest_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "RunId": "20260419T111700",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "FAIL",
                "CurrentHoldings": 5,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.1666666666666667,
                "ArchivePath": str(latest_dir),
            }
        ]
    ).to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")
    (shadow_dir / "shadow_summary.json").write_text(
        json.dumps(
            {
                "baseline_variant": "rule_breadth_it_us5_cap",
                "health_verdict": "PASS",
                "current_holdings": 5,
                "current_dominant_sector": "Industrials",
            }
        ),
        encoding="utf-8",
    )
    (shadow_dir / "shadow_drift_report.json").write_text(json.dumps({"drift_verdict": "PASS"}), encoding="utf-8")
    (shadow_dir / "shadow_live_readiness.json").write_text(json.dumps({"live_readiness_verdict": "GO"}), encoding="utf-8")
    (shadow_dir / "shadow_live_transition_summary.json").write_text(
        json.dumps({"weight_turnover": 0.1666666666666667}),
        encoding="utf-8",
    )
    (shadow_dir / "shadow_operator_runtime_status.json").write_text('{"operator_gate_verdict":"PASS"}', encoding="utf-8")
    (shadow_dir / "shadow_live_transition_packet.md").write_text("# packet\n", encoding="utf-8")

    monkeypatch.setattr(archive_tools, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(archive_tools, "ARCHIVE_DIR", archive_dir)

    archive_tools.main(["--sync-latest-only"])
    output = capsys.readouterr().out

    assert "archive_sync_path=" in output
    assert (latest_dir / "shadow_operator_runtime_status.json").exists()
    assert (latest_dir / "shadow_live_transition_packet.md").exists()
    refreshed_manifest = pd.read_csv(archive_dir / "archive_manifest.csv")
    assert refreshed_manifest.iloc[0]["OperatorGateVerdict"] == "PASS"


def test_archive_timeline_ignores_latest_operator_gate_cycle(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    latest_dir = archive_dir / "20260419T111839"
    prior_dir = archive_dir / "20260419T111700"
    latest_dir.mkdir(parents=True)
    prior_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "RunId": "20260419T111700",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 5,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.1666666666666667,
                "ArchivePath": str(prior_dir),
            },
            {
                "RunId": "20260419T111839",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "FAIL",
                "CurrentHoldings": 5,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.1666666666666667,
                "ArchivePath": str(latest_dir),
            },
        ]
    ).to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")

    monkeypatch.setattr(archive_timeline, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_timeline, "REPORT_PATH", archive_dir / "archive_timeline_report.json")

    payload = archive_timeline.build_timeline_payload(window=8)

    assert payload["archive_timeline_verdict"] == "PASS"
    assert payload["timeline"][0]["operator_gate_verdict"] == "FAIL"


def test_split_models_live_submit_gate_uses_runtime_operator_gate_only(tmp_path: Path, monkeypatch) -> None:
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir(parents=True)
    runtime_status_path = shadow_dir / "shadow_operator_runtime_status.json"
    _write_json(
        runtime_status_path,
        {
            "live_readiness": "GO",
            "operator_gate_verdict": "PASS",
            "archive_stability_verdict": "FAIL",
        },
    )
    plan = pd.DataFrame(
        [
            {
                "Status": "PLANNED",
                "Reason": "",
            }
        ]
    )
    monkeypatch.setattr(live_execution, "RUNTIME_STATUS_PATH", runtime_status_path)
    monkeypatch.setattr(live_execution.config, "ENV", "PROD")

    live_execution._enforce_submit_gate(plan)


def test_split_models_live_execution_rebalance_handles_us_etf_sell_mapping(tmp_path: Path) -> None:
    orders_path = tmp_path / "shadow_rebalance_orders.csv"
    pd.DataFrame(
        [
            {
                "ExecutionSide": "SELL",
                "Action": "Sell",
                "Market": "US",
                "AssetType": "ETF",
                "Symbol": "XLE",
                "Name": "Energy Select Sector SPDR Fund",
                "Sector": "Energy",
                "DeltaNotional": -166_666.6666666666,
            }
        ]
    ).to_csv(orders_path, index=False, encoding="utf-8-sig")

    class _FakeApi:
        def get_overseas_quote(self, exchange_code, symbol):
            assert exchange_code == "AMS"
            assert symbol == "XLE"
            return {"price": 80.0}

        def get_usd_krw_rate(self):
            return 1000.0

    plan, summary = live_execution._build_plan(
        live_execution._load_orders(orders_path),
        _FakeApi(),
        {},
    )

    assert summary["planned_count"] == 1
    assert summary["skipped_count"] == 0
    row = plan.iloc[0]
    assert row["ResolvedExchange"] == "AMEX"
    assert int(row["Quantity"]) == 2


def test_split_models_operator_handoff_runner_status_only(monkeypatch) -> None:
    calls: list[list[str]] = []
    runtime_status_calls: list[bool] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == handoff_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(handoff_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(handoff_runner.sys, "executable", "python")
    monkeypatch.setattr(handoff_runner, "_write_runtime_status", lambda print_json=False: runtime_status_calls.append(print_json))
    monkeypatch.setattr(sys, "argv", ["tools/pipelines/run_split_models_operator_handoff.py", "--status-only"])

    handoff_runner.main()

    assert calls == []
    assert runtime_status_calls == [False]


def test_split_models_operator_handoff_runner_status_only_json(monkeypatch) -> None:
    calls: list[list[str]] = []
    runtime_status_calls: list[bool] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == handoff_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(handoff_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(handoff_runner.sys, "executable", "python")
    monkeypatch.setattr(handoff_runner, "_write_runtime_status", lambda print_json=False: runtime_status_calls.append(print_json))
    monkeypatch.setattr(sys, "argv", ["tools/pipelines/run_split_models_operator_handoff.py", "--status-only", "--json"])

    handoff_runner.main()

    assert calls == []
    assert runtime_status_calls == [True]


def test_split_models_operator_handoff_runner_status_only_fail_on_not_go(monkeypatch) -> None:
    calls: list[list[str]] = []
    runtime_status_calls: list[bool] = []
    gate_calls: list[bool] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == handoff_runner.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(handoff_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(handoff_runner.sys, "executable", "python")
    monkeypatch.setattr(handoff_runner, "_write_runtime_status", lambda print_json=False: runtime_status_calls.append(print_json))
    monkeypatch.setattr(handoff_runner, "_enforce_operational_gate", lambda: gate_calls.append(True))
    monkeypatch.setattr(sys, "argv", ["tools/pipelines/run_split_models_operator_handoff.py", "--status-only", "--fail-on-not-go"])

    handoff_runner.main()

    assert calls == []
    assert runtime_status_calls == [False]
    assert gate_calls == [True]


def test_split_models_operator_handoff_runner_enforce_operational_gate_raises(tmp_path: Path, monkeypatch) -> None:
    runtime_status_path = tmp_path / "shadow_operator_runtime_status.json"
    runtime_status_path.write_text(
        json.dumps(
            {
                "operator_gate_verdict": "FAIL",
                "operator_gate_failures": ["live_readiness=HOLD"],
                "live_readiness": "HOLD",
                "health_verdict": "PASS",
                "drift_verdict": "PASS",
                "archive_consistency_verdict": "PASS",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(handoff_runner, "RUNTIME_STATUS_PATH", runtime_status_path)

    try:
        handoff_runner._enforce_operational_gate()
    except SystemExit as exc:
        assert "operator_gate_failed" in str(exc)
        assert "live_readiness=HOLD" in str(exc)
    else:
        raise AssertionError("Expected SystemExit for non-GO runtime status")


def test_split_models_archive_backfills_missing_operator_gate(tmp_path: Path, monkeypatch) -> None:
    shadow_dir = tmp_path / "shadow"
    archive_dir = tmp_path / "archive"
    prior_dir = archive_dir / "20260414T120000"
    shadow_dir.mkdir(parents=True)
    prior_dir.mkdir(parents=True)

    _write_json(shadow_dir / "shadow_summary.json", {"baseline_variant": "rule_breadth_it_us5_cap", "health_verdict": "PASS", "current_holdings": 8, "current_dominant_sector": "Industrials"})
    _write_json(shadow_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
    _write_json(shadow_dir / "shadow_live_readiness.json", {"live_readiness_verdict": "GO"})
    _write_json(shadow_dir / "shadow_live_transition_summary.json", {"weight_turnover": 0.11111111111111113})
    _write_json(shadow_dir / "shadow_operator_runtime_status.json", {"operator_gate_verdict": "PASS"})
    _write_json(prior_dir / "shadow_operator_runtime_status.json", {"operator_gate_verdict": "PASS"})

    pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(prior_dir),
                "OperatorGateVerdict": None,
            }
        ]
    ).to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")

    class _FakeNow:
        @staticmethod
        def now() -> "_FakeTimestamp":
            return _FakeTimestamp()

    class _FakeTimestamp:
        @staticmethod
        def strftime(fmt: str) -> str:
            assert fmt == "%Y%m%dT%H%M%S"
            return "20260414T120500"

    monkeypatch.setattr(archive_tools, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(archive_tools, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_tools, "datetime", _FakeNow)
    archive_tools.main()

    manifest = pd.read_csv(archive_dir / "archive_manifest.csv")
    assert list(manifest["OperatorGateVerdict"]) == ["PASS", "PASS"]


def test_split_models_archive_stability_fails_on_operator_gate_change(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(archive_dir / "20260414T120000"),
            },
            {
                "RunId": "20260414T120500",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "FAIL",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(archive_dir / "20260414T120500"),
            },
        ]
    ).to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")
    _write_json(
        archive_dir / "archive_latest_delta.json",
        {
            "baseline_variant_changed": False,
            "live_readiness_changed": False,
            "operator_gate_changed": True,
            "health_changed": False,
            "drift_changed": False,
            "dominant_sector_changed": False,
            "transition_turnover_change": 0.0,
        },
    )
    _write_json(
        archive_dir / "archive_consistency_report.json",
        {
            "archive_consistency_verdict": "PASS",
        },
    )

    monkeypatch.setattr(archive_stability, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_stability, "REPORT_PATH", archive_dir / "archive_stability_report.json")
    archive_stability.main(["--window", "2"])

    payload = _read_json(archive_dir / "archive_stability_report.json")
    assert payload["archive_stability_verdict"] == "FAIL"


def test_split_models_archive_status_reads_latest_and_specific_run(tmp_path: Path, monkeypatch, capsys) -> None:
    archive_dir = tmp_path / "archive"
    latest_dir = archive_dir / "20260414T120500"
    prior_dir = archive_dir / "20260414T120000"
    latest_dir.mkdir(parents=True)
    prior_dir.mkdir(parents=True)

    manifest = pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(prior_dir),
            },
            {
                "RunId": "20260414T120500",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(latest_dir),
            },
        ]
    )
    manifest.to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")

    for run_dir in [prior_dir, latest_dir]:
        _write_json(
            run_dir / "shadow_summary.json",
            {
                "baseline_variant": "rule_breadth_it_us5_cap",
                "health_verdict": "PASS",
                "current_holdings": 8,
                "current_dominant_sector": "Industrials",
            },
        )
        _write_json(run_dir / "shadow_live_readiness.json", {"live_readiness_verdict": "GO"})
        _write_json(run_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
        _write_json(run_dir / "shadow_live_transition_summary.json", {"weight_turnover": 0.11111111111111113})
        _write_json(
            run_dir / "shadow_operator_runtime_status.json",
            {"operator_gate_verdict": "PASS", "operator_gate_failures": []},
        )
        _write_json(run_dir / "shadow_rebalance_execution_summary.json", {"actionable_rows": 9})
        _write_json(run_dir / "archive_consistency_report.json", {"archive_consistency_verdict": "PASS"})
        _write_json(
            run_dir / "archive_stability_report.json",
            {"archive_stability_verdict": "PASS", "window": 5},
        )
    _write_json(
        archive_dir / "archive_timeline_report.json",
        {
            "archive_timeline_verdict": "PASS",
            "window": 8,
            "latest_run_id": "20260414T120500",
            "timeline": [
                {"run_id": "20260414T120500"},
                {"run_id": "20260414T120000"},
            ],
        },
    )

    monkeypatch.setattr(archive_status, "ARCHIVE_DIR", archive_dir)

    archive_status.main(["--json"])
    latest_payload = json.loads(capsys.readouterr().out)
    assert latest_payload["archive_run_id"] == "20260414T120500"
    assert latest_payload["archive_stability_verdict"] == "PASS"
    assert latest_payload["archive_timeline_verdict"] == "PASS"
    assert latest_payload["archive_run_in_timeline"] is True
    assert latest_payload["archive_run_timeline_rank"] == 1
    assert latest_payload["archive_prior_run_id"] == "20260414T120000"
    assert latest_payload["holdings_change_vs_prior"] == 0
    assert latest_payload["dominant_sector_changed_vs_prior"] is False
    assert latest_payload["archive_next_run_id"] is None

    archive_status.main(["--run-id", "20260414T120000"])
    text_output = capsys.readouterr().out
    assert "archive_run_id=20260414T120000" in text_output
    assert "operator_gate_verdict=PASS" in text_output
    assert "archive_run_in_timeline=True" in text_output
    assert "archive_run_timeline_rank=2" in text_output
    assert "archive_next_run_id=20260414T120500" in text_output


def test_split_models_archive_replay_packet_builds_markdown(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    latest_dir = archive_dir / "20260414T120500"
    prior_dir = archive_dir / "20260414T120000"
    latest_dir.mkdir(parents=True)
    prior_dir.mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(prior_dir),
            },
            {
                "RunId": "20260414T120500",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(latest_dir),
            },
        ]
    ).to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")

    for run_dir in [prior_dir, latest_dir]:
        _write_json(run_dir / "shadow_summary.json", {"baseline_variant": "rule_breadth_it_us5_cap", "health_verdict": "PASS", "current_holdings": 8, "current_dominant_sector": "Industrials"})
        _write_json(run_dir / "shadow_live_readiness.json", {"live_readiness_verdict": "GO"})
        _write_json(run_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
        _write_json(run_dir / "shadow_live_transition_summary.json", {"weight_turnover": 0.11111111111111113})
        _write_json(run_dir / "shadow_operator_runtime_status.json", {"operator_gate_verdict": "PASS", "operator_gate_failures": []})
        _write_json(run_dir / "shadow_rebalance_execution_summary.json", {"actionable_rows": 9})
        _write_json(run_dir / "archive_consistency_report.json", {"archive_consistency_verdict": "PASS"})
        _write_json(run_dir / "archive_stability_report.json", {"archive_stability_verdict": "PASS", "window": 5})
        (run_dir / "shadow_live_transition_packet.md").write_text("# Archived Packet\n", encoding="utf-8")

    _write_json(
        archive_dir / "archive_timeline_report.json",
        {
            "archive_timeline_verdict": "PASS",
            "window": 8,
            "latest_run_id": "20260414T120500",
            "timeline": [{"run_id": "20260414T120500"}, {"run_id": "20260414T120000"}],
        },
    )

    monkeypatch.setattr(archive_status, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_replay_packet, "ARCHIVE_DIR", archive_dir)

    resolved_run_id, packet = archive_replay_packet.build_replay_packet("20260414T120500")
    assert resolved_run_id == "20260414T120500"
    assert "archive run id: `20260414T120500`" in packet
    assert "prior run id: `20260414T120000`" in packet
    assert "## Archived Operator Packet" in packet
    assert "# Archived Packet" in packet


def test_split_models_archive_compare_reports_deltas(tmp_path: Path, monkeypatch, capsys) -> None:
    archive_dir = tmp_path / "archive"
    latest_dir = archive_dir / "20260414T120500"
    prior_dir = archive_dir / "20260414T120000"
    latest_dir.mkdir(parents=True)
    prior_dir.mkdir(parents=True)

    manifest = pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(prior_dir),
            },
            {
                "RunId": "20260414T120500",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 9,
                "CurrentDominantSector": "Health Care",
                "TransitionWeightTurnover": 0.2222222222222222,
                "ArchivePath": str(latest_dir),
            },
        ]
    )
    manifest.to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")

    for run_dir, holdings, sector, turnover in [
        (prior_dir, 8, "Industrials", 0.11111111111111113),
        (latest_dir, 9, "Health Care", 0.2222222222222222),
    ]:
        _write_json(run_dir / "shadow_summary.json", {"baseline_variant": "rule_breadth_it_us5_cap", "health_verdict": "PASS", "current_holdings": holdings, "current_dominant_sector": sector})
        _write_json(run_dir / "shadow_live_readiness.json", {"live_readiness_verdict": "GO"})
        _write_json(run_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
        _write_json(run_dir / "shadow_live_transition_summary.json", {"weight_turnover": turnover})
        _write_json(run_dir / "shadow_operator_runtime_status.json", {"operator_gate_verdict": "PASS", "operator_gate_failures": []})
        _write_json(run_dir / "shadow_rebalance_execution_summary.json", {"actionable_rows": 9})
        _write_json(run_dir / "archive_consistency_report.json", {"archive_consistency_verdict": "PASS"})
        _write_json(run_dir / "archive_stability_report.json", {"archive_stability_verdict": "PASS", "window": 5})

    _write_json(
        archive_dir / "archive_timeline_report.json",
        {
            "archive_timeline_verdict": "PASS",
            "window": 8,
            "latest_run_id": "20260414T120500",
            "timeline": [{"run_id": "20260414T120500"}, {"run_id": "20260414T120000"}],
        },
    )

    monkeypatch.setattr(archive_status, "ARCHIVE_DIR", archive_dir)
    payload = archive_compare.build_archive_compare_payload("20260414T120000", "20260414T120500")
    assert payload["holdings_change"] == 1
    assert payload["dominant_sector_changed"] is True
    assert payload["transition_turnover_change"] > 0

    archive_compare.main(["--base-run-id", "20260414T120000", "--target-run-id", "20260414T120500"])
    output = capsys.readouterr().out
    assert "holdings_change=1" in output
    assert "dominant_sector_changed=True" in output


def test_split_models_archive_compare_packet_builds_markdown(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    latest_dir = archive_dir / "20260414T120500"
    prior_dir = archive_dir / "20260414T120000"
    latest_dir.mkdir(parents=True)
    prior_dir.mkdir(parents=True)

    manifest = pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(prior_dir),
            },
            {
                "RunId": "20260414T120500",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 9,
                "CurrentDominantSector": "Health Care",
                "TransitionWeightTurnover": 0.2222222222222222,
                "ArchivePath": str(latest_dir),
            },
        ]
    )
    manifest.to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")

    for run_dir, holdings, sector, turnover in [
        (prior_dir, 8, "Industrials", 0.11111111111111113),
        (latest_dir, 9, "Health Care", 0.2222222222222222),
    ]:
        _write_json(run_dir / "shadow_summary.json", {"baseline_variant": "rule_breadth_it_us5_cap", "health_verdict": "PASS", "current_holdings": holdings, "current_dominant_sector": sector})
        _write_json(run_dir / "shadow_live_readiness.json", {"live_readiness_verdict": "GO"})
        _write_json(run_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
        _write_json(run_dir / "shadow_live_transition_summary.json", {"weight_turnover": turnover})
        _write_json(run_dir / "shadow_operator_runtime_status.json", {"operator_gate_verdict": "PASS", "operator_gate_failures": []})
        _write_json(run_dir / "shadow_rebalance_execution_summary.json", {"actionable_rows": 9})
        _write_json(run_dir / "archive_consistency_report.json", {"archive_consistency_verdict": "PASS"})
        _write_json(run_dir / "archive_stability_report.json", {"archive_stability_verdict": "PASS", "window": 5})
        (run_dir / "shadow_live_transition_packet.md").write_text("# Archived Packet\n", encoding="utf-8")

    _write_json(
        archive_dir / "archive_timeline_report.json",
        {
            "archive_timeline_verdict": "PASS",
            "window": 8,
            "latest_run_id": "20260414T120500",
            "timeline": [{"run_id": "20260414T120500"}, {"run_id": "20260414T120000"}],
        },
    )

    monkeypatch.setattr(archive_status, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_compare, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_replay_packet, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_compare_packet, "ARCHIVE_DIR", archive_dir)

    packet = archive_compare_packet.build_compare_packet("20260414T120000", "20260414T120500")
    assert "# Split Models Archive Compare Packet" in packet
    assert "holdings change: `1`" in packet
    assert "dominant sector changed: `True`" in packet
    assert "## Base Replay Packet" in packet
    assert "## Target Replay Packet" in packet


def test_split_models_archive_timeline_reports_recent_runs(tmp_path: Path, monkeypatch) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "20260414T120000").mkdir(parents=True)
    (archive_dir / "20260414T120500").mkdir(parents=True)

    pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": None,
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(archive_dir / "20260414T120000"),
            },
            {
                "RunId": "20260414T120500",
                "BaselineVariant": "rule_breadth_it_us5_cap",
                "HealthVerdict": "PASS",
                "DriftVerdict": "PASS",
                "LiveReadinessVerdict": "GO",
                "OperatorGateVerdict": "PASS",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "TransitionWeightTurnover": 0.11111111111111113,
                "ArchivePath": str(archive_dir / "20260414T120500"),
            },
        ]
    ).to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")
    _write_json(
        archive_dir / "20260414T120000" / "shadow_operator_runtime_status.json",
        {"operator_gate_verdict": "PASS"},
    )
    _write_json(
        archive_dir / "20260414T120500" / "shadow_operator_runtime_status.json",
        {"operator_gate_verdict": "PASS"},
    )

    monkeypatch.setattr(archive_timeline, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_timeline, "REPORT_PATH", archive_dir / "archive_timeline_report.json")
    archive_timeline.main(["--window", "2"])

    payload = _read_json(archive_dir / "archive_timeline_report.json")
    assert payload["archive_timeline_verdict"] == "PASS"
    assert payload["latest_run_id"] == "20260414T120500"
    assert [row["run_id"] for row in payload["timeline"]] == ["20260414T120500", "20260414T120000"]


def test_split_models_operator_gate_fails_when_archive_timeline_fails(tmp_path: Path, monkeypatch) -> None:
    shadow_dir = tmp_path / "shadow"
    archive_dir = tmp_path / "archive"
    shadow_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    _write_json(
        shadow_dir / "shadow_summary.json",
        {
            "baseline_variant": "rule_breadth_it_us5_cap",
            "health_verdict": "PASS",
            "current_holdings": 8,
            "current_dominant_sector": "Industrials",
        },
    )
    _write_json(shadow_dir / "split_models_backtest_summary.json", {"trading_book": {"CAGR": 0.33, "MDD": -0.25, "Sharpe": 1.44}})
    _write_json(shadow_dir / "shadow_drift_report.json", {"drift_verdict": "PASS"})
    _write_json(shadow_dir / "shadow_live_readiness.json", {"live_readiness_verdict": "GO"})
    _write_json(shadow_dir / "shadow_live_transition_summary.json", {"weight_turnover": 0.11111111111111113})
    _write_json(shadow_dir / "shadow_rebalance_execution_summary.json", {"actionable_rows": 9})
    _write_csv(
        shadow_dir / "shadow_rebalance_market_summary.csv",
        [{"Market": "US", "ExecutionSide": "BUY", "OrderCount": 1}],
    )
    _write_json(archive_dir / "archive_consistency_report.json", {"archive_consistency_verdict": "PASS"})
    _write_json(archive_dir / "archive_stability_report.json", {"archive_stability_verdict": "PASS", "window": 5, "latest_run_id": "20260414T120500"})
    _write_json(archive_dir / "archive_timeline_report.json", {"archive_timeline_verdict": "FAIL", "window": 8, "latest_run_id": "20260414T120500"})
    _write_json(archive_dir / "archive_latest_delta.json", {"comparison_available": False})

    monkeypatch.setattr(shadow_status, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(shadow_status, "ARCHIVE_DIR", archive_dir)

    payload = shadow_status.build_status_payload()
    assert payload["operator_gate_verdict"] == "FAIL"
    assert payload["operator_gate_failures"] == ["archive_timeline_verdict=FAIL"]


def test_split_models_dashboard_archive_replay_loaders(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    run_dir = archive_dir / "20260414T120500"
    run_dir.mkdir(parents=True)
    (run_dir / "shadow_live_transition_packet.md").write_text("# Packet\n", encoding="utf-8")
    (run_dir / "shadow_archive_replay_packet.md").write_text("# Replay Packet\n", encoding="utf-8")
    (run_dir / "shadow_summary.json").write_text(json.dumps({"health_verdict": "PASS"}), encoding="utf-8")

    fake_streamlit = types.SimpleNamespace(
        set_page_config=lambda **kwargs: None,
        cache_data=lambda ttl=60: (lambda fn: fn),
    )
    original_streamlit = sys.modules.get("streamlit")
    sys.modules["streamlit"] = fake_streamlit

    import tools.dashboards.split_models_shadow_dashboard as dashboard

    try:
        assert dashboard._load_archive_run_text("20260414T120500", "shadow_live_transition_packet.md") == ""

        original_archive_dir = dashboard.ARCHIVE_DIR
        dashboard.ARCHIVE_DIR = archive_dir
        assert dashboard._load_archive_run_text("20260414T120500", "shadow_live_transition_packet.md") == "# Packet\n"
        assert dashboard._load_archive_run_text("20260414T120500", "shadow_archive_replay_packet.md") == "# Replay Packet\n"
        assert dashboard._load_archive_run_json("20260414T120500", "shadow_summary.json")["health_verdict"] == "PASS"
        assert dashboard._load_archive_run_json("20260414T120500", "missing.json") == {}
    finally:
        dashboard.ARCHIVE_DIR = original_archive_dir
        if original_streamlit is None:
            sys.modules.pop("streamlit", None)
        else:
            sys.modules["streamlit"] = original_streamlit


def test_split_models_capital_readiness_builds_min_capital_summary(monkeypatch) -> None:
    book = pd.DataFrame(
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "DOW",
                "Name": "Dow",
                "Sector": "Materials",
                "TargetWeight": 0.2,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "GEV",
                "Name": "GE Vernova",
                "Sector": "Industrials",
                "TargetWeight": 0.2,
            },
            {
                "Market": "KR",
                "AssetType": "ETF",
                "Symbol": "0000J0",
                "Name": "PLUS Hanwha",
                "Sector": "ETF",
                "TargetWeight": 0.1,
            },
        ]
    )

    class _FakeApi:
        def get_overseas_quote(self, exchange_code: str, symbol: str) -> dict[str, object]:
            prices = {"DOW": 35.6, "GEV": 1002.75}
            return {"price": prices[symbol]}

        def get_usd_krw_rate(self) -> float:
            return 1457.8

        def get_domestic_quote(self, symbol: str) -> dict[str, object]:
            assert symbol == "006380"
            return {"price": 12345.0}

    details, summary = capital_readiness.build_capital_readiness(book, _FakeApi(), overrides={}, total_capital=1_000_000)

    assert summary["holdings_considered"] == 3
    assert summary["ready_count"] == 3
    assert summary["blocked_count"] == 0
    assert summary["fundable_count_at_capital"] == 2
    assert summary["unfundable_count_at_capital"] == 1
    assert summary["fundable_symbols_at_capital"] == ["DOW", "0000J0"]
    assert summary["min_capital_all_holdings_one_share_krw"] == 7309045

    gev_row = details.loc[details["Symbol"] == "GEV"].iloc[0]
    assert gev_row["ResolvedExchange"] == "NYSE"
    assert bool(gev_row["FundableAtCapital"]) is False
    assert gev_row["MaxSharesAtCapital"] == 0
    assert gev_row["MinTotalCapitalForOneShareKRW"] == 7309045


def test_split_models_capital_readiness_main_writes_outputs(tmp_path: Path, monkeypatch) -> None:
    book_path = tmp_path / "shadow_current_book.csv"
    details_path = tmp_path / "shadow_capital_readiness.csv"
    summary_path = tmp_path / "shadow_capital_readiness_summary.json"
    _write_csv(
        book_path,
        [
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "COP",
                "Name": "ConocoPhillips",
                "Sector": "Energy",
                "TargetWeight": 0.2,
            },
            {
                "Market": "US",
                "AssetType": "STOCK",
                "Symbol": "XOM",
                "Name": "Exxon Mobil",
                "Sector": "Energy",
                "TargetWeight": 0.2,
            },
        ],
    )

    class _FakeApi:
        def __init__(self) -> None:
            pass

        def get_overseas_quote(self, exchange_code: str, symbol: str) -> dict[str, object]:
            prices = {"COP": 116.04, "XOM": 146.44}
            return {"price": prices[symbol]}

        def get_usd_krw_rate(self) -> float:
            return 1457.8

    monkeypatch.setattr(capital_readiness, "KISApi", _FakeApi)

    capital_readiness.main(
        [
            "--book-path",
            str(book_path),
            "--details-path",
            str(details_path),
            "--summary-path",
            str(summary_path),
            "--total-capital",
            "1000000",
        ]
    )

    written_details = pd.read_csv(details_path)
    written_summary = _read_json(summary_path)
    assert written_summary["fundable_count_at_capital"] == 1
    assert written_summary["fundable_symbols_at_capital"] == ["COP"]
    assert written_summary["min_capital_all_holdings_one_share_krw"] == 1067402
    assert written_details.loc[written_details["Symbol"] == "COP", "FundableAtCapital"].iloc[0]
    assert not written_details.loc[written_details["Symbol"] == "XOM", "FundableAtCapital"].iloc[0]


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
