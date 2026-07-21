from __future__ import annotations

from scripts.compare_btc_1d_meta_contract_screen import _render_markdown


def test_meta_contract_summary_wording_is_regression_locked() -> None:
    rendered = _render_markdown(
        {
            "entries": [
                {
                    "label": "execution_contract_screen",
                    "source": "analysis_results\\btc_1d_execution_contract_screen_latest.json",
                    "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                    "wording_regression_test": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
                    "standard_check_order": [
                        "practical",
                        "research",
                        "contract",
                        "brief",
                    ],
                }
            ],
            "meta_contract_summary": {
                "shared_regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                "regression_lock_aligned": True,
                "shared_standard_check_order": [
                    "practical",
                    "research",
                    "contract",
                    "brief",
                ],
                "standard_check_order_aligned": True,
                "standard_check_order_scope": [
                    "operating_brief",
                    "operating_index",
                    "quick_read_contract_screen",
                    "execution_contract_screen",
                ],
                "health_order_aligned": True,
                "execution_contract_entry_scope_included": True,
                "execution_contract_wording_lock_included": True,
                "execution_contract_symmetry_lock_included": True,
                "meta_contract_topline_regression_test": "tests/unit/test_btc_1d_meta_contract_wording_contract.py",
                "meta_contract_topline_reason_wording_included": True,
                "meta_contract_topline_status": "meta topline status | regression_test=tests/unit/test_btc_1d_meta_contract_wording_contract.py | reason_included=True",
                "meta_contract_topline_quick_status": "meta topline quick | lock=ok | reason=included",
                "meta_contract_topline_highlight": "topline highlight | lock=ok | reason=included",
                "meta_contract_reason_highlight_summary": "reason+highlight | summary_ready | reason=included",
                "meta_contract_reason_final_verdict": "reason final verdict | complete | reason=included",
                "meta_contract_integrated_topline_verdict": "meta contract integrated | topline=complete | reason=complete",
                "execution_contract_symmetry_regression_test": (
                    "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py"
                ),
                "execution_contract_symmetry_fields": [
                    "symmetry_regression_test",
                    "execution_contract_symmetry_lock_included",
                    "execution_contract_symmetry_regression_test",
                    "execution_meta_contract_test_index_symmetry_fields",
                ],
                "execution_contract_symmetry_field_set": [
                    "symmetry_regression_test",
                    "execution_contract_symmetry_lock_included",
                    "execution_contract_symmetry_regression_test",
                    "execution_meta_contract_test_index_symmetry_fields",
                ],
                "execution_contract_symmetry_field_map": (
                    "symmetry field map | symmetry_regression_test | "
                    "execution_contract_symmetry_lock_included | "
                    "execution_contract_symmetry_regression_test | "
                    "execution_meta_contract_test_index_symmetry_fields"
                ),
                "execution_contract_symmetry_contract_bundle": (
                    "symmetry contract bundle | symmetry_regression_test | "
                    "execution_contract_symmetry_lock_included | "
                    "execution_contract_symmetry_regression_test | "
                    "execution_meta_contract_test_index_symmetry_fields"
                ),
                "execution_contract_symmetry_ready": True,
                "execution_contract_symmetry_reason_scope": (
                    "symmetry reason scope | key | set | map | bundle | ready"
                ),
                "execution_contract_symmetry_reason_range_summary": (
                    "symmetry reason range | key | set | map | bundle | ready | stack_complete"
                ),
                "execution_contract_symmetry_reason_final_summary": (
                    "symmetry reason final | key | set | map | bundle | ready | "
                    "stack_complete | summary_ready"
                ),
                "execution_contract_symmetry_status": (
                    "symmetry contract status | ready=True | symmetry reason scope | "
                    "key | set | map | bundle | ready"
                ),
                "execution_contract_symmetry_stack_complete": True,
                "execution_contract_symmetry_summary_ready": True,
                "execution_contract_symmetry_topline_verdict": (
                    "symmetry contract topline | complete"
                ),
                "execution_meta_quick_status": "execution+meta quick | execution=complete | meta=complete",
                "execution_meta_integrated_quick_verdict": "execution+meta integrated | execution=complete | meta=complete",
                "execution_meta_topline_bundle": "execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete",
                "execution_meta_bundle_ready_verdict": "execution+meta bundle ready | complete",
                "execution_meta_topline_ready": "execution+meta topline ready | complete",
                "execution_meta_stack_complete": "execution+meta stack complete | complete",
                "execution_meta_contract_test_index_symmetry_fields": [
                    "symmetry_regression_test",
                    "execution_contract_symmetry_lock_included",
                    "execution_contract_symmetry_regression_test",
                    "execution_meta_contract_test_index_symmetry_fields",
                ],
                "contract_read_order_lock_included": True,
                "contract_read_order_regression_test": (
                    "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
                ),
                "reverse_screen_pointer_lock_included": True,
                "reverse_screen_pointer_lock_scope": ["meta_contract_screen_summary"],
                "reverse_screen_pointer_scope_regression_test": (
                    "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
                ),
                "execution_meta_contract_test_index_md": (
                    "analysis_results\\btc_1d_execution_meta_contract_test_index_md_latest.md"
                ),
                "deprecated_aliases": {
                    "all_health_standard_order_aligned": (
                        "Deprecated alias for health_order_aligned. Prefer health_order_aligned."
                    )
                },
                "health_standard_check_order_scope": [
                    "practical_health",
                    "research_stack_health",
                    "contract_health",
                ],
            },
            "meta_contract_verdict": {
                "contract_is_fully_aligned": True,
                "reason": (
                    "Latest brief/index/contract-screen JSON and practical-research-contract "
                    "health JSON should share the same regression lock test, while standard "
                    "check order should stay aligned across the outputs that publish it, "
                    "including execution contract summary and execution contract entry scope, "
                    "plus execution contract wording lock, meta_contract_topline_regression_test, "
                    "execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata, "
                    "and execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/"
                    "execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete."
                ),
            },
        }
    )

    assert (
        "Execution contract symmetry topline verdict: `symmetry contract topline | complete`"
        in rendered
    )
    assert "Execution contract symmetry ready: `True`" in rendered
    assert (
        "Execution contract symmetry summary ready: `True`" in rendered
    )
    assert "Contract fully aligned: `True`" in rendered
    assert "Execution-meta reason field-set lock: `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`" in rendered
    assert "Execution-meta reason final-sentence lock: `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`" in rendered
    assert "Execution meta stack complete: `execution+meta stack complete | complete`" in rendered
    assert "execution_meta_stack_complete." in rendered
    assert "Reason: Latest brief/index/contract-screen JSON and practical-research-contract health JSON should share the same regression lock test, while standard check order should stay aligned across the outputs that publish it, including execution contract summary and execution contract entry scope, plus execution contract wording lock, meta_contract_topline_regression_test, execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata, and execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete." in rendered
