from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_execution_contract_screen import (
    REGRESSION_LOCK_TEST,
    STANDARD_CHECK_ORDER_REFERENCE,
    SYMMETRY_FIELDS,
    SYMMETRY_REGRESSION_TEST,
    WORDING_REGRESSION_TEST,
    _paper_summary_contract_bool,
    _render_markdown,
    _write_latest_aliases,
    build_report,
    render_execution_contract_health_line,
    render_execution_contract_read,
    render_paper_ledger_snapshot_read,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_quick_read_contract_screen(
    analysis_dir: Path, *, contract_health_aligned: bool
) -> None:
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "contract_health_aligned": contract_health_aligned,
            }
        },
    )


def test_build_report_aligns_execution_contract_fields(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"
    paper_ledger_snapshot_read = "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1"

    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "contract_health_aligned": True,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "contract_health_aligned": True,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "execution_contract_checked": True,
            "execution_contract_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=True,
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": (
                    "meta contract integrated | topline=complete | reason=complete"
                ),
                "execution_meta_integrated_quick_verdict": (
                    "execution+meta integrated | execution=complete | meta=complete"
                ),
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {
            "tests": [
                {
                    "label": "contract_read_order_runbook_contract",
                    "locks": [
                        "quick-read contract screen read order",
                        "execution contract screen read order",
                        "meta contract screen read order",
                        "execution meta contract test index read order",
                        "execution/meta contract test map reverse screen pointers",
                    ],
                }
            ],
            "summary": {
                "meta_contract_tests": [
                    "tests/unit/test_compare_btc_1d_meta_contract_screen.py",
                    "tests/unit/test_btc_1d_meta_contract_runbook_wording_contract.py",
                    "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                ]
            }
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=True,
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["execution_contract_summary"]["execution_contract_read"] == (
        "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0"
    )
    assert report["execution_contract_summary"]["execution_contract_health_line"] == (
        "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ... || "
        "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0"
    )
    assert report["execution_contract_summary"]["regression_lock_test"] == REGRESSION_LOCK_TEST
    assert report["execution_contract_summary"]["wording_regression_test"] == WORDING_REGRESSION_TEST
    assert report["execution_contract_summary"]["symmetry_regression_test"] == SYMMETRY_REGRESSION_TEST
    assert report["execution_contract_summary"]["symmetry_fields"] == SYMMETRY_FIELDS
    assert report["execution_contract_summary"]["symmetry_field_set"] == SYMMETRY_FIELDS
    assert (
        report["execution_contract_summary"]["symmetry_field_map"]
        == "symmetry field map | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields"
    )
    assert (
        report["execution_contract_summary"]["symmetry_contract_bundle"]
        == "symmetry contract bundle | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields"
    )
    assert report["execution_contract_summary"]["symmetry_contract_ready"] is True
    assert (
        report["execution_contract_summary"]["symmetry_reason_scope"]
        == "symmetry reason scope | key | set | map | bundle | ready"
    )
    assert (
        report["execution_contract_summary"]["symmetry_reason_range_summary"]
        == "symmetry reason range | key | set | map | bundle | ready | stack_complete"
    )
    assert (
        report["execution_contract_summary"]["symmetry_reason_final_summary"]
        == "symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready"
    )
    assert (
        report["execution_contract_summary"]["symmetry_contract_status"]
        == "symmetry contract status | ready=True | symmetry reason scope | key | set | map | bundle | ready"
    )
    assert report["execution_contract_summary"]["symmetry_contract_stack_complete"] is True
    assert report["execution_contract_summary"]["symmetry_contract_summary_ready"] is True
    assert (
        report["execution_contract_summary"]["symmetry_contract_topline_verdict"]
        == "symmetry contract topline | complete"
    )
    assert (
        report["execution_contract_summary"]["meta_contract_integrated_topline_verdict"]
        == "meta contract integrated | topline=complete | reason=complete"
    )
    assert (
        report["execution_contract_summary"]["execution_meta_quick_status"]
        == "execution+meta quick | execution=complete | meta=complete"
    )
    assert (
        report["execution_contract_summary"]["execution_meta_integrated_quick_verdict"]
        == "execution+meta integrated | execution=complete | meta=complete"
    )
    assert (
        report["execution_contract_summary"]["execution_meta_topline_bundle"]
        == "execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete"
    )
    assert (
        report["execution_contract_summary"]["execution_meta_bundle_ready_verdict"]
        == "execution+meta bundle ready | complete"
    )
    assert (
        report["execution_contract_summary"]["execution_meta_topline_ready"]
        == "execution+meta topline ready | complete"
    )
    assert (
        report["execution_contract_summary"]["execution_meta_stack_complete"]
        == "execution+meta stack complete | complete"
    )
    assert (
        report["execution_contract_summary"]["execution_meta_contract_test_index_symmetry_fields"]
        == SYMMETRY_FIELDS
    )
    assert report["execution_contract_summary"]["execution_meta_contract_test_index_md"].endswith(
        "btc_1d_execution_meta_contract_test_index_md_latest.md"
    )
    assert report["execution_contract_summary"]["contract_read_order_lock_included"] is True
    assert report["execution_contract_summary"]["reverse_screen_pointer_lock_included"] is True
    assert report["execution_contract_summary"]["reverse_screen_pointer_lock_scope"] == [
        "execution_contract_screen_summary"
    ]
    assert (
        report["execution_contract_summary"]["reverse_screen_pointer_scope_regression_test"]
        == "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
    )
    assert (
        report["execution_contract_summary"]["contract_read_order_regression_test"]
        == "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
    )
    assert report["execution_contract_summary"]["standard_check_order_reference"] == STANDARD_CHECK_ORDER_REFERENCE
    assert report["entries"][0]["regression_lock_test"] == REGRESSION_LOCK_TEST
    assert report["entries"][0]["standard_check_order_reference"] == STANDARD_CHECK_ORDER_REFERENCE
    assert report["entries"][1]["regression_lock_test"] == REGRESSION_LOCK_TEST
    assert report["entries"][1]["standard_check_order_reference"] == STANDARD_CHECK_ORDER_REFERENCE
    assert report["execution_contract_summary"]["execution_health_line"] == execution_health_line
    assert report["execution_contract_summary"]["paper_nightly_health_line"] == paper_nightly_health_line
    assert report["execution_contract_summary"]["paper_execution_read"] == paper_execution_read
    assert report["execution_contract_summary"]["contract_health_aligned_read"] is True
    assert report["execution_contract_summary"]["quick_read_contract_health_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned"] is True
    assert report["execution_contract_summary"]["paper_ledger_snapshot_read"] == paper_ledger_snapshot_read
    assert report["execution_contract_summary"]["execution_health_aligned"] is True
    assert report["execution_contract_summary"]["paper_nightly_health_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_read_aligned"] is True
    assert report["execution_contract_summary"]["contract_health_entry_aligned"] is True
    assert report["execution_contract_summary"]["contract_health_summary_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_summary_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned_summary_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert report["execution_contract_summary"]["paper_ledger_snapshot_aligned"] is True
    assert report["execution_contract_summary"]["paper_ledger_snapshot_summary_aligned"] is True
    assert report["execution_contract_verdict"]["execution_contract_aligned"] is True
    assert "contract health aligned state" in report["execution_contract_verdict"]["reason"]
    assert "paper ledger snapshot read" in report["execution_contract_verdict"]["reason"]
    assert "symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata" in report["execution_contract_verdict"]["reason"]
    assert "execution_meta_stack_complete" in report["execution_contract_verdict"]["reason"]
    assert report["paper_nightly_summary"]["paper_duplicate_count"] == 0
    assert report["paper_nightly_summary"]["paper_closed_count"] == 1
    assert report["paper_nightly_summary"]["paper_ledger_snapshot_read"] == paper_ledger_snapshot_read
    assert report["paper_nightly_summary"]["paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True


def test_paper_summary_contract_bool_prefers_nightly_self_check_field() -> None:
    summary = {
        "paper_execution_contract_checked_aligned": False,
        "execution_contract_paper_execution_contract_checked_aligned": True,
    }

    assert (
        _paper_summary_contract_bool(
            summary,
            "paper_execution_contract_checked_aligned",
            "execution_contract_paper_execution_contract_checked_aligned",
        )
        is False
    )


def test_build_report_prefers_paper_summary_self_check_mirror_over_legacy_contract_origin(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"
    paper_ledger_snapshot_read = "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1"

    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "execution_contract_checked": True,
            "execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": False,
            "execution_contract_paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned": True,
            "paper_execution_contract_checked_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": True,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
                "paper_execution_contract_checked_aligned_summary_aligned": False,
                "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": True,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=True,
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": (
                    "meta contract integrated | topline=complete | reason=complete"
                ),
                "execution_meta_integrated_quick_verdict": (
                    "execution+meta integrated | execution=complete | meta=complete"
                ),
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {
            "tests": [],
            "summary": {"meta_contract_tests": []},
        },
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["paper_nightly_summary"]["paper_execution_contract_checked_aligned"] is False
    assert report["execution_contract_summary"]["paper_execution_contract_checked_aligned_read"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_aligned"] is True
    assert report["paper_nightly_summary"]["paper_execution_contract_checked_aligned_summary_aligned"] is False
    assert report["execution_contract_summary"]["paper_execution_contract_checked_aligned_summary_aligned"] is False
    assert report["execution_contract_verdict"]["execution_contract_aligned"] is False


def test_build_report_fails_alignment_when_snapshot_read_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"

    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_ledger_snapshot_read": "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1",
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "execution_contract_checked": True,
            "execution_contract_aligned": False,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=True,
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": (
                    "meta contract integrated | topline=complete | reason=complete"
                ),
                "execution_meta_integrated_quick_verdict": (
                    "execution+meta integrated | execution=complete | meta=complete"
                ),
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {"tests": [], "summary": {"meta_contract_tests": []}},
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["execution_contract_summary"]["paper_ledger_snapshot_aligned"] is False
    assert report["execution_contract_verdict"]["execution_contract_aligned"] is False
    assert report["execution_contract_summary"]["execution_contract_read"] == (
        "execution contract | drifted | paper execution | track=operating | applied=1 | closed=1 | open=0"
    )
    assert report["execution_contract_summary"]["execution_meta_quick_status"] == (
        "execution+meta quick | execution=incomplete | meta=complete"
    )


def test_build_report_fails_alignment_when_summary_snapshot_read_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"
    shared_snapshot = "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1"

    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_ledger_snapshot_read": shared_snapshot,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_ledger_snapshot_read": shared_snapshot,
            "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
            "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "execution_contract_checked": True,
            "execution_contract_aligned": False,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1",
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=True,
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": (
                    "meta contract integrated | topline=complete | reason=complete"
                ),
                "execution_meta_integrated_quick_verdict": (
                    "execution+meta integrated | execution=complete | meta=complete"
                ),
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {"tests": [], "summary": {"meta_contract_tests": []}},
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["execution_contract_summary"]["paper_ledger_snapshot_aligned"] is True
    assert report["execution_contract_summary"]["paper_ledger_snapshot_summary_aligned"] is False
    assert report["execution_contract_verdict"]["execution_contract_aligned"] is False
    assert report["execution_contract_summary"]["execution_contract_read"] == (
        "execution contract | drifted | paper execution | track=operating | applied=1 | closed=1 | open=0"
    )


def test_build_report_fails_alignment_when_summary_execution_contract_state_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"
    shared_snapshot = "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1"

    for filename in ["btc_1d_operating_brief_latest.json", "btc_1d_operating_index_latest.json"]:
        _write_json(
            analysis_dir / filename,
            {
                "regression_lock_test": REGRESSION_LOCK_TEST,
                "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
                "execution_health_line": execution_health_line,
                "paper_nightly_health_line": paper_nightly_health_line,
                "paper_execution_read": paper_execution_read,
                "paper_execution_contract_checked": True,
                "paper_execution_contract_aligned": True,
                "paper_ledger_snapshot_read": shared_snapshot,
                "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
                "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
            },
        )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "execution_contract_checked": True,
            "execution_contract_aligned": False,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": shared_snapshot,
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=True,
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": "meta contract integrated | topline=complete | reason=complete",
                "execution_meta_integrated_quick_verdict": "execution+meta integrated | execution=complete | meta=complete",
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {"tests": [], "summary": {"meta_contract_tests": []}},
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["execution_contract_summary"]["paper_execution_contract_aligned_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_aligned_summary_aligned"] is False
    assert report["execution_contract_verdict"]["execution_contract_aligned"] is False
    assert report["execution_contract_summary"]["execution_contract_read"] == (
        "execution contract | drifted | paper execution | track=operating | applied=1 | closed=1 | open=0"
    )


def test_build_report_fails_alignment_when_contract_health_summary_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"
    shared_snapshot = "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1"

    for filename in ["btc_1d_operating_brief_latest.json", "btc_1d_operating_index_latest.json"]:
        payload = {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "contract_health_aligned": True,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_ledger_snapshot_read": shared_snapshot,
        }
        if filename == "btc_1d_operating_index_latest.json":
            payload["paper_nightly_summary"] = "analysis_results\\btc_1d_paper_nightly_summary_latest.json"
            payload["paper_nightly_summary_md"] = "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md"
        _write_json(analysis_dir / filename, payload)
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "execution_contract_checked": True,
            "execution_contract_aligned": True,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": shared_snapshot,
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=False,
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": "meta contract integrated | topline=complete | reason=complete",
                "execution_meta_integrated_quick_verdict": "execution+meta integrated | execution=complete | meta=complete",
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {"tests": [], "summary": {"meta_contract_tests": []}},
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["execution_contract_summary"]["contract_health_entry_aligned"] is True
    assert report["execution_contract_summary"]["contract_health_summary_aligned"] is False
    assert report["execution_contract_verdict"]["execution_contract_aligned"] is False
    assert report["execution_contract_summary"]["execution_meta_quick_status"] == (
        "execution+meta quick | execution=incomplete | meta=complete"
    )


def test_build_report_fails_alignment_when_entry_self_check_summary_alignment_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    execution_health_line = "BTC 1d practical health ... || BTC 1d research stack ... || BTC 1d paper nightly ..."
    paper_nightly_health_line = (
        "BTC 1d paper nightly | track=operating | intents=1 | signed=1 | applied=1 | closed=1 | open=0"
    )
    paper_execution_read = "paper execution | track=operating | applied=1 | closed=1 | open=0"
    shared_snapshot = "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1"

    for filename in ["btc_1d_operating_brief_latest.json", "btc_1d_operating_index_latest.json"]:
        payload = {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "standard_check_order": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "contract_health_aligned": True,
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "paper_execution_contract_checked_aligned": True,
            "paper_execution_contract_aligned_aligned": True,
            "paper_execution_contract_checked_summary_aligned": False,
            "paper_execution_contract_aligned_summary_aligned": True,
            "paper_ledger_snapshot_read": shared_snapshot,
        }
        if filename == "btc_1d_operating_index_latest.json":
            payload["paper_nightly_summary"] = "analysis_results\\btc_1d_paper_nightly_summary_latest.json"
            payload["paper_nightly_summary_md"] = "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md"
        _write_json(analysis_dir / filename, payload)
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "paper_execution_read": paper_execution_read,
            "execution_contract_checked": True,
            "execution_contract_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": False,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
            "paper_nightly_health_line": paper_nightly_health_line,
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": shared_snapshot,
        },
    )
    _write_quick_read_contract_screen(
        analysis_dir,
        contract_health_aligned=True,
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": "meta contract integrated | topline=complete | reason=complete",
                "execution_meta_integrated_quick_verdict": "execution+meta integrated | execution=complete | meta=complete",
            }
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json",
        {"tests": [], "summary": {"meta_contract_tests": []}},
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["execution_contract_summary"]["paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert report["execution_contract_summary"]["paper_execution_contract_checked_summary_aligned_summary_aligned"] is False
    assert report["execution_contract_verdict"]["execution_contract_aligned"] is False


def test_render_markdown_and_latest_aliases(tmp_path: Path) -> None:
    rendered = _render_markdown(
        {
            "entries": [
                {
                    "label": "operating_brief",
                    "source": "analysis_results\\btc_1d_operating_brief_latest.json",
                    "regression_lock_test": REGRESSION_LOCK_TEST,
                    "standard_check_order_reference": STANDARD_CHECK_ORDER_REFERENCE,
                    "execution_health_line": "health",
                    "paper_nightly_health_line": "nightly",
                    "paper_execution_read": "paper read",
                    "contract_health_aligned": True,
                    "paper_execution_contract_checked": True,
                    "paper_execution_contract_aligned": True,
                    "paper_execution_contract_checked_aligned": True,
                    "paper_execution_contract_aligned_aligned": True,
                    "paper_execution_contract_checked_summary_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned": True,
                    "paper_execution_contract_checked_aligned_entry_aligned": True,
                    "paper_execution_contract_aligned_aligned_entry_aligned": True,
                    "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
                    "paper_execution_contract_checked_aligned_summary_aligned": True,
                    "paper_execution_contract_aligned_aligned_summary_aligned": True,
                    "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
                    "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
                },
                {
                    "label": "operating_index",
                    "source": "analysis_results\\btc_1d_operating_index_latest.json",
                    "regression_lock_test": REGRESSION_LOCK_TEST,
                    "standard_check_order_reference": STANDARD_CHECK_ORDER_REFERENCE,
                    "execution_health_line": "health",
                    "paper_nightly_health_line": "nightly",
                    "paper_execution_read": "paper read",
                    "contract_health_aligned": True,
                    "paper_execution_contract_checked": True,
                    "paper_execution_contract_aligned": True,
                    "paper_execution_contract_checked_aligned": True,
                    "paper_execution_contract_aligned_aligned": True,
                    "paper_execution_contract_checked_summary_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned": True,
                    "paper_execution_contract_checked_aligned_entry_aligned": True,
                    "paper_execution_contract_aligned_aligned_entry_aligned": True,
                    "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
                    "paper_execution_contract_checked_aligned_summary_aligned": True,
                    "paper_execution_contract_aligned_aligned_summary_aligned": True,
                    "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
                    "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
                },
            ],
            "paper_nightly_summary": {
                "source": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
                "paper_execution_read": "paper read",
                "paper_execution_contract_checked": True,
                "paper_execution_contract_aligned": True,
                "paper_execution_contract_checked_aligned": True,
                "paper_execution_contract_aligned_aligned": True,
                "paper_execution_contract_checked_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
                "paper_execution_contract_checked_aligned_entry_aligned": True,
                "paper_execution_contract_aligned_aligned_entry_aligned": True,
                "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
                "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
                "paper_execution_contract_checked_aligned_summary_aligned": True,
                "paper_execution_contract_aligned_aligned_summary_aligned": True,
                "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
                "paper_nightly_health_line": "nightly",
                "intent_count": 1,
                "signed_request_count": 1,
                "paper_applied_count": 1,
                "paper_duplicate_count": 2,
                "paper_closed_count": 1,
                "paper_open_count": 0,
                "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
            },
            "meta_contract_summary": {
                "meta_contract_integrated_topline_verdict": (
                    "meta contract integrated | topline=complete | reason=complete"
                ),
                "execution_meta_integrated_quick_verdict": (
                    "execution+meta integrated | execution=complete | meta=complete"
                ),
            },
            "execution_contract_summary": {
                "execution_contract_health_line": "health || execution contract | aligned | paper read",
                "execution_contract_read": "execution contract | aligned | paper read",
                "regression_lock_test": REGRESSION_LOCK_TEST,
                "wording_regression_test": WORDING_REGRESSION_TEST,
                "symmetry_regression_test": SYMMETRY_REGRESSION_TEST,
                "symmetry_fields": SYMMETRY_FIELDS,
                "symmetry_field_set": SYMMETRY_FIELDS,
                "symmetry_field_map": "symmetry field map | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields",
                "symmetry_contract_bundle": "symmetry contract bundle | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields",
                "symmetry_contract_ready": True,
                "symmetry_reason_scope": "symmetry reason scope | key | set | map | bundle | ready",
                "symmetry_reason_range_summary": "symmetry reason range | key | set | map | bundle | ready | stack_complete",
                "symmetry_reason_final_summary": "symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready",
                "symmetry_contract_status": "symmetry contract status | ready=True | symmetry reason scope | key | set | map | bundle | ready",
                "symmetry_contract_stack_complete": True,
                "symmetry_contract_summary_ready": True,
                "symmetry_contract_topline_verdict": "symmetry contract topline | complete",
                "meta_contract_integrated_topline_verdict": "meta contract integrated | topline=complete | reason=complete",
                "execution_meta_quick_status": "execution+meta quick | execution=complete | meta=complete",
                "execution_meta_integrated_quick_verdict": "execution+meta integrated | execution=complete | meta=complete",
                "execution_meta_topline_bundle": "execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete",
                "execution_meta_bundle_ready_verdict": "execution+meta bundle ready | complete",
                "execution_meta_topline_ready": "execution+meta topline ready | complete",
                "execution_meta_stack_complete": "execution+meta stack complete | complete",
                "execution_meta_contract_test_index_md": "analysis_results\\btc_1d_execution_meta_contract_test_index_md_latest.md",
                "execution_meta_contract_test_index_symmetry_fields": SYMMETRY_FIELDS,
                "contract_read_order_lock_included": True,
                "contract_read_order_regression_test": "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                "reverse_screen_pointer_lock_included": True,
                "reverse_screen_pointer_lock_scope": ["execution_contract_screen_summary"],
                "reverse_screen_pointer_scope_regression_test": "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                "standard_check_order_reference": STANDARD_CHECK_ORDER_REFERENCE,
                "execution_health_line": "health",
                "paper_nightly_health_line": "nightly",
                "paper_execution_read": "paper read",
                "contract_health_aligned_read": True,
                "quick_read_contract_health_aligned": True,
                "paper_execution_contract_checked": True,
                "paper_execution_contract_aligned": True,
                "paper_execution_contract_checked_aligned_read": True,
                "paper_execution_contract_aligned_aligned_read": True,
                "paper_execution_contract_checked_summary_aligned_read": True,
                "paper_execution_contract_aligned_summary_aligned_read": True,
                "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
                "execution_health_aligned": True,
                "paper_nightly_health_aligned": True,
                "paper_execution_read_aligned": True,
                "contract_health_entry_aligned": True,
                "contract_health_summary_aligned": True,
                "paper_execution_contract_checked_aligned": True,
                "paper_execution_contract_aligned_aligned": True,
                "paper_execution_contract_checked_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
                "paper_execution_contract_checked_aligned_entry_aligned": True,
                "paper_execution_contract_aligned_aligned_entry_aligned": True,
                "paper_execution_contract_checked_summary_aligned_entry_aligned": True,
                "paper_execution_contract_aligned_summary_aligned_entry_aligned": True,
                "paper_execution_contract_checked_aligned_summary_aligned": True,
                "paper_execution_contract_aligned_aligned_summary_aligned": True,
                "paper_execution_contract_checked_summary_aligned_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned_summary_aligned": True,
                "paper_ledger_snapshot_aligned": True,
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_summary_paths": {
                    "paper_nightly_summary": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
                    "paper_nightly_summary_md": "analysis_results\\btc_1d_paper_nightly_summary_md_latest.md",
                },
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": True,
                "reason": "Execution contract is aligned.",
            },
        }
    )

    assert "# BTC 1d Execution Contract Screen" in rendered
    assert "Symmetry contract topline verdict: `symmetry contract topline | complete`" in rendered
    assert "Meta contract integrated topline verdict: `meta contract integrated | topline=complete | reason=complete`" in rendered
    assert "Execution meta quick status: `execution+meta quick | execution=complete | meta=complete`" in rendered
    assert "Execution meta integrated quick verdict: `execution+meta integrated | execution=complete | meta=complete`" in rendered
    assert "Execution meta topline bundle: `execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete`" in rendered
    assert "Execution meta bundle ready verdict: `execution+meta bundle ready | complete`" in rendered
    assert "Execution meta topline ready: `execution+meta topline ready | complete`" in rendered
    assert "Execution meta stack complete: `execution+meta stack complete | complete`" in rendered
    assert "Execution contract health: `health || execution contract | aligned | paper read`" in rendered
    assert "Execution contract read: `execution contract | aligned | paper read`" in rendered
    assert f"Regression lock: `{REGRESSION_LOCK_TEST}`" in rendered
    assert f"Wording regression lock: `{WORDING_REGRESSION_TEST}`" in rendered
    assert f"Symmetry regression lock: `{SYMMETRY_REGRESSION_TEST}`" in rendered
    assert "Symmetry fields: `['symmetry_regression_test', 'execution_contract_symmetry_lock_included', 'execution_contract_symmetry_regression_test', 'execution_meta_contract_test_index_symmetry_fields']`" in rendered
    assert "Symmetry field set: `['symmetry_regression_test', 'execution_contract_symmetry_lock_included', 'execution_contract_symmetry_regression_test', 'execution_meta_contract_test_index_symmetry_fields']`" in rendered
    assert "Symmetry field map: `symmetry field map | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields`" in rendered
    assert "Symmetry contract bundle: `symmetry contract bundle | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields`" in rendered
    assert "Symmetry contract ready: `True`" in rendered
    assert "Symmetry reason scope: `symmetry reason scope | key | set | map | bundle | ready`" in rendered
    assert "Symmetry reason range summary: `symmetry reason range | key | set | map | bundle | ready | stack_complete`" in rendered
    assert "Symmetry reason final summary: `symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready`" in rendered
    assert "Symmetry contract status: `symmetry contract status | ready=True | symmetry reason scope | key | set | map | bundle | ready`" in rendered
    assert "Symmetry contract stack complete: `True`" in rendered
    assert "Symmetry contract summary ready: `True`" in rendered
    assert "Execution meta contract test index: `analysis_results\\btc_1d_execution_meta_contract_test_index_md_latest.md`" in rendered
    assert "Execution meta contract test index symmetry fields: `['symmetry_regression_test', 'execution_contract_symmetry_lock_included', 'execution_contract_symmetry_regression_test', 'execution_meta_contract_test_index_symmetry_fields']`" in rendered
    assert "Contract read-order lock included: `True`" in rendered
    assert "Contract read-order regression lock: `tests/unit/test_btc_1d_contract_read_order_runbook_contract.py`" in rendered
    assert "Reverse screen pointer lock included: `True`" in rendered
    assert "Reverse screen pointer lock scope: `['execution_contract_screen_summary']`" in rendered
    assert "Reverse screen pointer scope regression lock: `tests/unit/test_btc_1d_contract_read_order_runbook_contract.py`" in rendered
    assert "Standard check order: `practical > research > contract > brief`" in rendered
    assert "Execution contract aligned: `True`" in rendered
    assert "Paper execution read: `paper read`" in rendered
    assert "Contract health entry aligned: `True`" in rendered
    assert "Contract health summary aligned: `True`" in rendered
    assert "Contract health aligned: `True`" in rendered
    assert "Quick-read contract health aligned truth: `True`" in rendered
    assert "Paper execution contract checked aligned: `True`" in rendered
    assert "Paper execution contract aligned aligned: `True`" in rendered
    assert "Paper execution contract checked summary aligned: `True`" in rendered
    assert "Paper execution contract aligned summary aligned: `True`" in rendered
    assert "Paper execution contract checked aligned entry aligned: `True`" in rendered
    assert "Paper execution contract aligned aligned entry aligned: `True`" in rendered
    assert "Paper execution contract checked summary aligned entry aligned: `True`" in rendered
    assert "Paper execution contract aligned summary aligned entry aligned: `True`" in rendered
    assert "Paper execution contract checked aligned summary aligned: `True`" in rendered
    assert "Paper execution contract aligned aligned summary aligned: `True`" in rendered
    assert "Paper execution contract checked summary aligned summary aligned: `True`" in rendered
    assert "Paper execution contract aligned summary aligned summary aligned: `True`" in rendered
    assert "Paper execution contract checked: `True`" in rendered
    assert "Paper execution contract aligned: `True`" in rendered
    assert "Paper ledger snapshot aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked: `True`" in rendered
    assert "Paper nightly summary execution contract aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked aligned: `True`" in rendered
    assert "Paper nightly summary execution contract aligned aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked summary aligned: `True`" in rendered
    assert "Paper nightly summary execution contract aligned summary aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked aligned entry aligned: `True`" in rendered
    assert "Paper nightly summary execution contract aligned aligned entry aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked summary aligned entry aligned: `True`" in rendered
    assert "Paper nightly summary execution contract aligned summary aligned entry aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked aligned summary aligned: `True`" in rendered
    assert "Paper nightly summary execution contract aligned aligned summary aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked summary aligned summary aligned: `True`" in rendered
    assert "Paper nightly summary execution contract aligned summary aligned summary aligned: `True`" in rendered
    assert "Paper ledger snapshot summary aligned: `True`" in rendered
    assert "Paper ledger snapshot: `paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1`" in rendered
    assert "Paper nightly summary snapshot: `paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1`" in rendered
    assert "Execution-meta reason field-set lock: `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`" in rendered
    assert "Execution-meta reason final-sentence lock: `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`" in rendered
    assert "## Paper Nightly Summary" in rendered
    assert "paper_duplicate_count: `2`" in rendered
    assert "paper_ledger_snapshot: `paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1`" in rendered
    assert "## operating_index" in rendered
    assert f"regression_lock_test: `{REGRESSION_LOCK_TEST}`" in rendered
    assert "standard_check_order_reference: `practical > research > contract > brief`" in rendered
    assert "paper_execution_contract_checked: `True`" in rendered
    assert "paper_execution_contract_aligned: `True`" in rendered

    json_path = tmp_path / "btc_1d_execution_contract_screen_20260417T000000Z.json"
    md_path = tmp_path / "btc_1d_execution_contract_screen_20260417T000000Z.md"
    json_path.write_text('{"ok": true}', encoding="utf-8")
    md_path.write_text("# ok", encoding="utf-8")

    aliases = _write_latest_aliases(json_path, md_path)

    latest_json = Path(aliases["btc_1d_execution_contract_screen"])
    latest_md = Path(aliases["btc_1d_execution_contract_screen_md"])
    assert latest_json.name == "btc_1d_execution_contract_screen_latest.json"
    assert latest_json.read_text(encoding="utf-8") == '{"ok": true}'
    assert latest_md.name == "btc_1d_execution_contract_screen_md_latest.md"
    assert latest_md.read_text(encoding="utf-8") == "# ok"


def test_render_execution_contract_read_uses_alignment_label() -> None:
    assert (
        render_execution_contract_read(
            execution_contract_aligned=True,
            paper_execution_read="paper execution | track=operating | applied=1 | closed=1 | open=0",
        )
        == "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0"
    )
    assert (
        render_execution_contract_read(
            execution_contract_aligned=False,
            paper_execution_read="",
        )
        == "execution contract | drifted"
    )


def test_render_paper_ledger_snapshot_read_uses_snapshot_fields() -> None:
    assert render_paper_ledger_snapshot_read(
        {
            "open_position_count": 2,
            "closed_position_count": 1,
            "exit_fill_count": 1,
            "order_count": 3,
            "fill_count": 3,
        }
    ) == "paper ledger | open=2 | closed=1 | exit_fills=1 | orders=3 | fills=3"


def test_render_execution_contract_health_line_prefers_combined_form() -> None:
    assert (
        render_execution_contract_health_line(
            execution_health_line="execution health line",
            execution_contract_read="execution contract read",
        )
        == "execution health line || execution contract read"
    )
    assert (
        render_execution_contract_health_line(
            execution_health_line="",
            execution_contract_read="execution contract read",
        )
        == "execution contract read"
    )
