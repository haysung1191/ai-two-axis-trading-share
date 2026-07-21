from __future__ import annotations

from pathlib import Path

from scripts.compare_btc_1d_execution_contract_screen import _render_markdown


def test_execution_and_meta_summary_wording_share_reverse_pointer_contract() -> None:
    rendered = _render_markdown(
        {
            "entries": [
                {
                    "label": "operating_brief",
                    "source": "analysis_results\\btc_1d_operating_brief_latest.json",
                    "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                    "standard_check_order_reference": ["practical", "research", "contract", "brief"],
                    "execution_health_line": "execution health",
                    "paper_nightly_health_line": "paper nightly",
                    "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
                },
                {
                    "label": "operating_index",
                    "source": "analysis_results\\btc_1d_operating_index_latest.json",
                    "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                    "standard_check_order_reference": ["practical", "research", "contract", "brief"],
                    "execution_health_line": "execution health",
                    "paper_nightly_health_line": "paper nightly",
                    "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
                },
            ],
            "paper_nightly_summary": {
                "source": "analysis_results\\btc_1d_paper_nightly_summary_latest.json",
                "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
                "paper_nightly_health_line": "paper nightly",
                "intent_count": 1,
                "signed_request_count": 1,
                "paper_applied_count": 1,
                "paper_closed_count": 1,
                "paper_open_count": 0,
            },
            "execution_contract_summary": {
                "execution_contract_health_line": "execution health || execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
                "execution_contract_read": "execution contract | aligned | paper execution | track=operating | applied=1 | closed=1 | open=0",
                "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
                "wording_regression_test": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
                "execution_meta_contract_test_index_md": "analysis_results\\btc_1d_execution_meta_contract_test_index_md_latest.md",
                "contract_read_order_lock_included": True,
                "contract_read_order_regression_test": "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                "reverse_screen_pointer_lock_included": True,
                "reverse_screen_pointer_lock_scope": ["execution_contract_screen_summary"],
                "reverse_screen_pointer_scope_regression_test": "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                "standard_check_order_reference": ["practical", "research", "contract", "brief"],
                "execution_health_line": "execution health",
                "paper_nightly_health_line": "paper nightly",
                "paper_execution_read": "paper execution | track=operating | applied=1 | closed=1 | open=0",
                "execution_health_aligned": True,
                "paper_nightly_health_aligned": True,
                "paper_execution_read_aligned": True,
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

    rendered_phrases = [
        "Reverse screen pointer lock included",
        "Reverse screen pointer lock scope",
        "Reverse screen pointer scope regression lock",
        "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
    ]
    runbook_phrases = [
        "`reverse_screen_pointer_lock_included`",
        "`reverse_screen_pointer_lock_scope=['execution_contract_screen_summary']`",
        "`reverse_screen_pointer_lock_scope=['meta_contract_screen_summary']`",
        "`reverse_screen_pointer_scope_regression_test`",
        "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
    ]

    runbooks = [
        Path(r"C:\AI\Crypto\docs\operator_runbook.md"),
        Path(r"C:\AI\Crypto\docs\btc_1d_shadow_update_runbook.md"),
    ]

    for phrase in rendered_phrases:
        assert phrase in rendered
    for phrase in runbook_phrases:
        for runbook in runbooks:
            assert phrase in runbook.read_text(encoding="utf-8"), f"{phrase} missing from {runbook}"
