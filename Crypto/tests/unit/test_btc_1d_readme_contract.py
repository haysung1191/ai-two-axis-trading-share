from __future__ import annotations

from pathlib import Path

from tests.unit.btc_1d_handoff_doc_contract import (
    build_readme_handoff_confirmation_lines,
)
from tests.unit.btc_1d_handoff_contract_keys import FAST_GATE_SHARED_HANDOFF_KEYS


def test_readme_locks_fast_operating_check_handoff_wording() -> None:
    text = Path(r"C:\AI\Crypto\README.md").read_text(encoding="utf-8")

    expected_lines = [
        "## Fast Operating Check",
        "the standard operating check order is:",
        "1. Practical",
        "2. Research",
        "3. Contract",
        "4. Brief",
        "Fast terminal entry points:",
        r"`C:\AI\Crypto\scripts\check_btc_1d_practical_health.py`",
        r"`C:\AI\Crypto\scripts\check_btc_1d_research_stack_health.py`",
        r"`C:\AI\Crypto\scripts\check_btc_1d_contract_health.py`",
        r"`C:\AI\Crypto\scripts\check_btc_1d_shadow_health.py`",
        r"`C:\AI\Crypto\scripts\check_btc_1d_shadow_health.py --as-json`",
        "Final attack challenger handoff check:",
        "Open these when the handoff is fully advanced:",
        r"[C:\AI\Crypto\analysis_results\btc_1d_operating_index_md_latest.md](C:\AI\Crypto\analysis_results\btc_1d_operating_index_md_latest.md)",
        r"[C:\AI\Crypto\analysis_results\btc_1d_operating_brief_md_latest.md](C:\AI\Crypto\analysis_results\btc_1d_operating_brief_md_latest.md)",
        r"[C:\AI\Crypto\analysis_results\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md](C:\AI\Crypto\analysis_results\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md)",
    ]

    for expected in expected_lines:
        assert expected in text

    for expected in build_readme_handoff_confirmation_lines():
        assert expected in text

    ordered_handoff_lines = [
        build_readme_handoff_confirmation_lines()[
            FAST_GATE_SHARED_HANDOFF_KEYS.index(key)
        ]
        for key in FAST_GATE_SHARED_HANDOFF_KEYS
    ]
    positions = [text.index(expected) for expected in ordered_handoff_lines]
    assert positions == sorted(positions)
