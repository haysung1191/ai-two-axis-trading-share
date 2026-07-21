from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.pipelines import run_split_models_initial_entry as initial_entry_runner
from tools.pipelines import submit_split_models_initial_entry_from_latest as submit_latest_runner


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_submit_split_models_initial_entry_from_latest_check_only_skips_submit(monkeypatch, tmp_path: Path) -> None:
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    latest_index_path = tmp_path / "latest.json"
    capital_readiness_details_path = tmp_path / "capital_readiness.csv"
    capital_readiness_summary_path = tmp_path / "capital_readiness_summary.json"
    plan_path = tmp_path / "plan.csv"
    summary_path = tmp_path / "summary.json"
    preflight_path = tmp_path / "preflight.json"
    report_path = tmp_path / "report.md"
    submit_results_path = tmp_path / "submit_results.csv"
    submit_summary_path = tmp_path / "submit_summary.json"

    capital_readiness_details_path.write_text("ok", encoding="utf-8")
    capital_readiness_summary_path.write_text("{}", encoding="utf-8")
    plan_path.write_text("a,b\n1,2\n", encoding="utf-8")
    summary_path.write_text('{"ok": true}', encoding="utf-8")
    preflight_path.write_text(
        json.dumps(
            {
                "preflight_verdict": "PASS",
                "preflight_failures": [],
                "execution_plan_sha256": initial_entry_runner._sha256_file(plan_path),
                "execution_summary_sha256": initial_entry_runner._sha256_file(summary_path),
            }
        ),
        encoding="utf-8",
    )
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
        submit_results_path=str(submit_results_path),
        submit_summary_path=str(submit_summary_path),
        submit_live=False,
    )

    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        calls.append(args)

    monkeypatch.setattr(submit_latest_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(submit_latest_runner, "_timestamp_slug", lambda: "20260419T120000")
    monkeypatch.setattr(submit_latest_runner, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/submit_split_models_initial_entry_from_latest.py",
            "--latest-index-path",
            str(latest_index_path),
        ],
    )

    submit_latest_runner.main()

    assert calls == []
    latest_payload = _read_json(latest_index_path)
    assert latest_payload["submit_live_requested"] is False
    assert latest_payload["check_timestamp"] == "20260419T120000"
    assert latest_payload["check_json_path"].endswith("shadow_live_initial_adaptive_check_latest.json")
    assert latest_payload["check_md_path"].endswith("shadow_live_initial_adaptive_check_latest.md")
    assert latest_payload["check_history_json_path"].endswith("shadow_live_initial_adaptive_check_20260419T120000.json")
    assert latest_payload["check_history_md_path"].endswith("shadow_live_initial_adaptive_check_20260419T120000.md")
    check_payload = _read_json(shadow_dir / "shadow_live_initial_adaptive_check_latest.json")
    check_markdown = (shadow_dir / "shadow_live_initial_adaptive_check_latest.md").read_text(
        encoding="utf-8"
    )
    history_payload = _read_json(shadow_dir / "shadow_live_initial_adaptive_check_20260419T120000.json")
    history_markdown = (shadow_dir / "shadow_live_initial_adaptive_check_20260419T120000.md").read_text(
        encoding="utf-8"
    )
    assert check_payload["check_verdict"] == "PASS"
    assert check_payload["check_timestamp"] == "20260419T120000"
    assert check_payload["submit_mode"] == "check_only"
    assert check_payload["planned_symbols"] == []
    assert history_payload["check_timestamp"] == "20260419T120000"
    assert "## Integrity" in check_markdown
    assert "## Integrity" in history_markdown


def test_submit_split_models_initial_entry_from_latest_invokes_submit_and_refresh(monkeypatch, tmp_path: Path) -> None:
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir()
    latest_index_path = tmp_path / "latest.json"
    capital_readiness_details_path = tmp_path / "capital_readiness.csv"
    capital_readiness_summary_path = tmp_path / "capital_readiness_summary.json"
    plan_path = tmp_path / "plan.csv"
    summary_path = tmp_path / "summary.json"
    preflight_path = tmp_path / "preflight.json"
    report_path = tmp_path / "report.md"
    submit_results_path = tmp_path / "submit_results.csv"
    submit_summary_path = tmp_path / "submit_summary.json"

    capital_readiness_details_path.write_text("ok", encoding="utf-8")
    capital_readiness_summary_path.write_text("{}", encoding="utf-8")
    plan_path.write_text("a,b\n1,2\n", encoding="utf-8")
    summary_path.write_text('{"ok": true}', encoding="utf-8")
    preflight_path.write_text(
        json.dumps(
            {
                "preflight_verdict": "PASS",
                "preflight_failures": [],
                "execution_plan_sha256": initial_entry_runner._sha256_file(plan_path),
                "execution_summary_sha256": initial_entry_runner._sha256_file(summary_path),
            }
        ),
        encoding="utf-8",
    )
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
        submit_results_path=str(submit_results_path),
        submit_summary_path=str(submit_summary_path),
        submit_live=False,
    )

    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool) -> None:
        assert cwd == submit_latest_runner.ROOT
        assert check is True
        calls.append(args)
        if args[1] == "tools/operations/execute_split_models_shadow_live_orders.py":
            submit_summary_path.write_text(
                json.dumps(
                    {
                        "submit_mode": "live",
                        "submitted_count": 1,
                        "failed_count": 0,
                        "submitted_plan_path": str(plan_path),
                        "submitted_plan_sha256": initial_entry_runner._sha256_file(plan_path),
                        "preflight_path": str(preflight_path),
                        "preflight_sha256": initial_entry_runner._sha256_file(preflight_path),
                    }
                ),
                encoding="utf-8",
            )
            submit_results_path.write_text("ok", encoding="utf-8")
        if args[1] == "tools/operations/build_split_models_initial_entry_report.py":
            report_path.write_text("# refreshed\n", encoding="utf-8")

    monkeypatch.setattr(submit_latest_runner.subprocess, "run", _fake_run)
    monkeypatch.setattr(submit_latest_runner.sys, "executable", "python")
    monkeypatch.setattr(submit_latest_runner, "_timestamp_slug", lambda: "20260419T120100")
    monkeypatch.setattr(submit_latest_runner, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/submit_split_models_initial_entry_from_latest.py",
            "--latest-index-path",
            str(latest_index_path),
            "--submit-live",
        ],
    )

    submit_latest_runner.main()

    assert calls == [
        [
            "python",
            "tools/operations/execute_split_models_shadow_live_orders.py",
            "--submit-existing-plan-path",
            str(plan_path),
            "--summary-path",
            str(submit_summary_path),
            "--submit-results-path",
            str(submit_results_path),
            "--preflight-path",
            str(preflight_path),
            "--submit-live",
        ],
        [
            "python",
            "tools/operations/build_split_models_initial_entry_report.py",
            "--capital-readiness-summary-path",
            str(capital_readiness_summary_path),
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
        ],
    ]
    latest_payload = _read_json(latest_index_path)
    assert latest_payload["submit_live_requested"] is True
    assert latest_payload["submit_summary_path"] == str(submit_summary_path)
    assert latest_payload["submit_results_path"] == str(submit_results_path)
    assert latest_payload["report_sha256"] == initial_entry_runner._sha256_file(report_path)
    assert latest_payload["check_timestamp"] == "20260419T120100"
    assert latest_payload["check_json_path"].endswith("shadow_live_initial_adaptive_check_latest.json")
    assert latest_payload["check_md_path"].endswith("shadow_live_initial_adaptive_check_latest.md")
    assert latest_payload["check_history_json_path"].endswith("shadow_live_initial_adaptive_check_20260419T120100.json")
    assert latest_payload["check_history_md_path"].endswith("shadow_live_initial_adaptive_check_20260419T120100.md")
    submit_summary_payload = _read_json(submit_summary_path)
    assert submit_summary_payload["check_timestamp"] == "20260419T120100"
    assert submit_summary_payload["check_json_path"].endswith("shadow_live_initial_adaptive_check_latest.json")
    assert submit_summary_payload["check_md_path"].endswith("shadow_live_initial_adaptive_check_latest.md")
    assert submit_summary_payload["check_history_json_path"].endswith("shadow_live_initial_adaptive_check_20260419T120100.json")
    assert submit_summary_payload["check_history_md_path"].endswith("shadow_live_initial_adaptive_check_20260419T120100.md")
    history_payload = _read_json(shadow_dir / "shadow_live_initial_adaptive_check_20260419T120100.json")
    assert history_payload["check_timestamp"] == "20260419T120100"


def test_submit_split_models_initial_entry_from_latest_builds_check_payload(tmp_path: Path) -> None:
    latest_index_path = tmp_path / "latest.json"
    capital_readiness_summary_path = tmp_path / "capital_readiness_summary.json"
    preflight_path = tmp_path / "preflight.json"
    capital_readiness_summary_path.write_text(
        json.dumps(
            {
                "fundable_count_at_capital": 2,
                "fundable_symbols_at_capital": ["DOW", "COP"],
                "min_capital_all_holdings_one_share_krw": 7309045,
            }
        ),
        encoding="utf-8",
    )
    preflight_path.write_text(
        json.dumps(
            {
                "preflight_verdict": "PASS",
                "live_readiness": "GO",
                "operator_gate_verdict": "PASS",
                "archive_stability_verdict": "FAIL",
                "planned_count": 3,
                "skipped_count": 0,
                "planned_symbols": ["DOW", "XOM", "COP"],
                "planned_quantity_total": 8,
                "estimated_order_notional_krw_total": 694029.424,
            }
        ),
        encoding="utf-8",
    )
    latest_payload = {
        "capital_slug": "1000000",
        "total_capital": 1000000.0,
        "plan_sha256": "abc",
        "summary_sha256": "def",
        "preflight_sha256": "ghi",
        "report_sha256": "jkl",
    }
    paths = {
        "capital_readiness_summary_path": str(capital_readiness_summary_path),
        "plan_path": "plan.csv",
        "summary_path": "summary.json",
        "preflight_path": str(preflight_path),
        "report_path": "report.md",
    }

    payload = submit_latest_runner._build_check_payload(latest_index_path, latest_payload, paths)
    markdown = submit_latest_runner._build_check_markdown(payload)

    assert payload["check_verdict"] == "PASS"
    assert payload["planned_symbols"] == ["DOW", "XOM", "COP"]
    assert payload["fundable_symbols_at_capital"] == ["DOW", "COP"]
    assert "Split Models Initial Entry Check" in markdown
    assert "DOW, XOM, COP" in markdown


def test_submit_split_models_initial_entry_from_latest_raises_on_index_hash_mismatch(monkeypatch, tmp_path: Path) -> None:
    latest_index_path = tmp_path / "latest.json"
    capital_readiness_summary_path = tmp_path / "capital_readiness_summary.json"
    plan_path = tmp_path / "plan.csv"
    summary_path = tmp_path / "summary.json"
    preflight_path = tmp_path / "preflight.json"
    report_path = tmp_path / "report.md"

    capital_readiness_summary_path.write_text("{}", encoding="utf-8")
    plan_path.write_text("a,b\n1,2\n", encoding="utf-8")
    summary_path.write_text('{"ok": true}', encoding="utf-8")
    preflight_path.write_text("{}", encoding="utf-8")
    report_path.write_text("# report\n", encoding="utf-8")

    latest_index_path.write_text(
        json.dumps(
            {
                "capital_slug": "1000000",
                "total_capital": 1000000.0,
                "capital_readiness_summary_path": str(capital_readiness_summary_path),
                "plan_path": str(plan_path),
                "summary_path": str(summary_path),
                "preflight_path": str(preflight_path),
                "report_path": str(report_path),
                "plan_sha256": "bad-hash",
                "summary_sha256": initial_entry_runner._sha256_file(summary_path),
                "preflight_sha256": initial_entry_runner._sha256_file(preflight_path),
                "report_sha256": initial_entry_runner._sha256_file(report_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/pipelines/submit_split_models_initial_entry_from_latest.py",
            "--latest-index-path",
            str(latest_index_path),
        ],
    )

    try:
        submit_latest_runner.main()
    except SystemExit as exc:
        assert "plan_sha256_mismatch" in str(exc)
    else:
        raise AssertionError("Expected SystemExit on latest index hash mismatch")
