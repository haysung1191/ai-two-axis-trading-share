from __future__ import annotations

from pathlib import Path


EXPECTED_ORDER = [
    "btc_1d_quick_read_contract_screen_md_latest.md",
    "btc_1d_execution_contract_screen_md_latest.md",
    "btc_1d_meta_contract_screen_md_latest.md",
    "btc_1d_execution_meta_contract_test_index_md_latest.md",
]


def _assert_in_order(text: str, expected: list[str]) -> None:
    positions = [text.index(item) for item in expected]
    assert positions == sorted(positions), f"Expected order {expected}, got positions {positions}"


def _extract_quick_read_contract_block(text: str) -> str:
    header = "Quick-read contract check:"
    start = text.index(header)
    tail = text[start:]
    next_header_idx = tail.find("\n\nShadow update")
    if next_header_idx == -1:
        next_header_idx = tail.find("\n\nWhat to look")
    if next_header_idx == -1:
        next_header_idx = len(tail)
    return tail[:next_header_idx]


def test_contract_read_order_is_regression_locked_in_runbooks() -> None:
    paths = [
        Path(r"C:\AI\Crypto\docs\operator_runbook.md"),
        Path(r"C:\AI\Crypto\docs\btc_1d_shadow_update_runbook.md"),
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        block = _extract_quick_read_contract_block(text)
        _assert_in_order(block, EXPECTED_ORDER)
        assert "the execution/meta contract test map also points back to:" in block
        assert "analysis_results/btc_1d_quick_read_contract_screen_md_latest.md" in block
        assert "analysis_results/btc_1d_execution_contract_screen_md_latest.md" in block
        assert "analysis_results/btc_1d_meta_contract_screen_md_latest.md" in block
