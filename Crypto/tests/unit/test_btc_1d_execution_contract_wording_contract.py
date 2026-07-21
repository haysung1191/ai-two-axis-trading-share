from __future__ import annotations

from scripts.compare_btc_1d_execution_contract_screen import _render_markdown


def test_execution_contract_summary_wording_is_regression_locked() -> None:
    rendered = _render_markdown(
        {
            "entries": [
                {
                    "label": "operating_brief",
                    "source": "analysis_results\\btc_1d_operating_brief_latest.json",
                    "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                    "standard_check_order_reference": [
                        "practical",
                        "research",
                        "contract",
                        "brief",
                    ],
                    "execution_health_line": "execution health",
                    "paper_nightly_health_line": "paper nightly",
                    "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
                    "contract_health_aligned": True,
                    "paper_execution_contract_checked": True,
                    "paper_execution_contract_aligned": True,
                    "paper_execution_contract_checked_aligned": True,
                    "paper_execution_contract_aligned_aligned": True,
                    "paper_execution_contract_checked_summary_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned": True,
                    "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
                },
                {
                    "label": "operating_index",
                    "source": "analysis_results\\btc_1d_operating_index_latest.json",
                    "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                    "standard_check_order_reference": [
                        "practical",
                        "research",
                        "contract",
                        "brief",
                    ],
                    "execution_health_line": "execution health",
                    "paper_nightly_health_line": "paper nightly",
                    "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
                    "contract_health_aligned": True,
                    "paper_execution_contract_checked": True,
                    "paper_execution_contract_aligned": True,
                    "paper_execution_contract_checked_aligned": True,
                    "paper_execution_contract_aligned_aligned": True,
                    "paper_execution_contract_checked_summary_aligned": True,
                    "paper_execution_contract_aligned_summary_aligned": True,
                    "paper_ledger_snapshot_read": "paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1",
                },
            ],
            "paper_nightly_summary": {
                "source": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
                "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
                "paper_execution_contract_checked": True,
                "paper_execution_contract_aligned": True,
                "paper_execution_contract_checked_aligned": True,
                "paper_execution_contract_aligned_aligned": True,
                "paper_execution_contract_checked_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
                "paper_nightly_health_line": "paper nightly",
                "intent_count": 1,
                "signed_request_count": 1,
                "paper_applied_count": 1,
                "paper_duplicate_count": 0,
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
                "symmetry_contract_topline_verdict": "symmetry contract topline | complete",
                "meta_contract_integrated_topline_verdict": "meta contract integrated | topline=complete | reason=complete",
                "execution_meta_quick_status": "execution+meta quick | execution=complete | meta=complete",
                "execution_meta_integrated_quick_verdict": "execution+meta integrated | execution=complete | meta=complete",
                "execution_meta_topline_bundle": "execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete",
                "execution_meta_bundle_ready_verdict": "execution+meta bundle ready | complete",
                "execution_meta_topline_ready": "execution+meta topline ready | complete",
                "execution_meta_stack_complete": "execution+meta stack complete | complete",
                "execution_contract_health_line": (
                    "execution health || execution contract | aligned | paper execution | "
                    "track=operating | applied=1 | closed=1 | open=0"
                ),
                "execution_contract_read": (
                    "execution contract | aligned | paper execution | "
                    "track=operating | applied=1 | closed=1 | open=0"
                ),
                "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                "wording_regression_test": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
                "symmetry_regression_test": "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py",
                "symmetry_fields": [
                    "symmetry_regression_test",
                    "execution_contract_symmetry_lock_included",
                    "execution_contract_symmetry_regression_test",
                    "execution_meta_contract_test_index_symmetry_fields",
                ],
                "symmetry_field_set": [
                    "symmetry_regression_test",
                    "execution_contract_symmetry_lock_included",
                    "execution_contract_symmetry_regression_test",
                    "execution_meta_contract_test_index_symmetry_fields",
                ],
                "symmetry_field_map": (
                    "symmetry field map | symmetry_regression_test | "
                    "execution_contract_symmetry_lock_included | "
                    "execution_contract_symmetry_regression_test | "
                    "execution_meta_contract_test_index_symmetry_fields"
                ),
                "symmetry_contract_bundle": (
                    "symmetry contract bundle | symmetry_regression_test | "
                    "execution_contract_symmetry_lock_included | "
                    "execution_contract_symmetry_regression_test | "
                    "execution_meta_contract_test_index_symmetry_fields"
                ),
                "symmetry_contract_ready": True,
                "symmetry_reason_scope": "symmetry reason scope | key | set | map | bundle | ready",
                "symmetry_reason_range_summary": (
                    "symmetry reason range | key | set | map | bundle | ready | stack_complete"
                ),
                "symmetry_reason_final_summary": (
                    "symmetry reason final | key | set | map | bundle | ready | "
                    "stack_complete | summary_ready"
                ),
                "symmetry_contract_status": (
                    "symmetry contract status | ready=True | symmetry reason scope | "
                    "key | set | map | bundle | ready"
                ),
                "symmetry_contract_stack_complete": True,
                "symmetry_contract_summary_ready": True,
                "execution_meta_contract_test_index_md": "analysis_results\\btc_1d_execution_meta_contract_test_index_md_latest.md",
                "execution_meta_contract_test_index_symmetry_fields": [
                    "symmetry_regression_test",
                    "execution_contract_symmetry_lock_included",
                    "execution_contract_symmetry_regression_test",
                    "execution_meta_contract_test_index_symmetry_fields",
                ],
                "contract_read_order_lock_included": True,
                "contract_read_order_regression_test": "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                "reverse_screen_pointer_lock_included": True,
                "reverse_screen_pointer_lock_scope": ["execution_contract_screen_summary"],
                "reverse_screen_pointer_scope_regression_test": "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                "standard_check_order_reference": [
                    "practical",
                    "research",
                    "contract",
                    "brief",
                ],
                "execution_health_line": "execution health",
                "paper_nightly_health_line": "paper nightly",
                "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
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
                "reason": (
                    "Operating brief and operating index should publish the same execution health line, "
                    "paper nightly health line, paper execution read, contract health aligned state, and paper ledger snapshot read from the latest paper nightly summary/quick-read contract truth, "
                    "while symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata and "
                    "execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/"
                    "execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete "
                    "should stay aligned across the execution contract summary."
                ),
            },
        }
    )

    assert "Symmetry contract topline verdict: `symmetry contract topline | complete`" in rendered
    assert "Meta contract integrated topline verdict: `meta contract integrated | topline=complete | reason=complete`" in rendered
    assert "Execution meta quick status: `execution+meta quick | execution=complete | meta=complete`" in rendered
    assert "Execution meta integrated quick verdict: `execution+meta integrated | execution=complete | meta=complete`" in rendered
    assert "Execution contract health: `execution health || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`" in rendered
    assert "Execution contract read: `execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0`" in rendered
    assert "Reverse screen pointer lock included: `True`" in rendered
    assert "Reverse screen pointer lock scope: `['execution_contract_screen_summary']`" in rendered
    assert "Reverse screen pointer scope regression lock: `tests/unit/test_btc_1d_contract_read_order_runbook_contract.py`" in rendered
    assert "Execution meta contract test index: `analysis_results\\btc_1d_execution_meta_contract_test_index_md_latest.md`" in rendered
    assert "Execution contract aligned: `True`" in rendered
    assert "Contract health entry aligned: `True`" in rendered
    assert "Contract health summary aligned: `True`" in rendered
    assert "Contract health aligned: `True`" in rendered
    assert "Quick-read contract health aligned truth: `True`" in rendered
    assert "paper_duplicate_count: `0`" in rendered
    assert "Paper execution contract checked aligned: `True`" in rendered
    assert "Paper execution contract aligned aligned: `True`" in rendered
    assert "Paper execution contract checked summary aligned: `True`" in rendered
    assert "Paper execution contract aligned summary aligned: `True`" in rendered
    assert "Paper execution contract checked: `True`" in rendered
    assert "Paper execution contract aligned: `True`" in rendered
    assert "Paper ledger snapshot aligned: `True`" in rendered
    assert "Paper nightly summary execution contract checked: `True`" in rendered
    assert "Paper nightly summary execution contract aligned: `True`" in rendered
    assert "Paper ledger snapshot summary aligned: `True`" in rendered
    assert "Paper ledger snapshot: `paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1`" in rendered
    assert "Paper nightly summary snapshot: `paper ledger | open=0 | closed=1 | exit_fills=1 | orders=1 | fills=1`" in rendered
    assert "Execution-meta reason field-set lock: `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`" in rendered
    assert "Execution-meta reason final-sentence lock: `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`" in rendered
    assert "execution_meta_stack_complete should stay aligned across the execution contract summary." in rendered
    assert "Reason: Operating brief and operating index should publish the same execution health line, paper nightly health line, paper execution read, contract health aligned state, and paper ledger snapshot read from the latest paper nightly summary/quick-read contract truth, while symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata and execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete should stay aligned across the execution contract summary." in rendered
