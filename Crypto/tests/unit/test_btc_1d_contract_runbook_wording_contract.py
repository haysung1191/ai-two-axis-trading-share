from __future__ import annotations

from pathlib import Path

from scripts.btc_1d_contract_health_constants import (
    HEALTH_ORDER_ALIAS,
    HEALTH_ORDER_DEPRECATION_MESSAGE,
)
from tests.unit.btc_1d_handoff_doc_contract import (
    build_runbook_final_handoff_confirmation_lines,
    build_runbook_final_handoff_verification_lines,
)
from tests.unit.btc_1d_handoff_contract_keys import FAST_GATE_SHARED_HANDOFF_KEYS


def test_contract_runbooks_share_deprecated_alias_wording() -> None:
    operator_runbook = Path(r"C:\AI\Crypto\docs\operator_runbook.md").read_text(encoding="utf-8")
    shadow_update_runbook = Path(r"C:\AI\Crypto\docs\btc_1d_shadow_update_runbook.md").read_text(
        encoding="utf-8"
    )

    expected_line = f"`{HEALTH_ORDER_ALIAS}` = `{HEALTH_ORDER_DEPRECATION_MESSAGE}`"

    assert expected_line in operator_runbook
    assert expected_line in shadow_update_runbook


def test_contract_runbooks_lock_refresh_handoff_machine_read_wording() -> None:
    expected_lines = [
        "Fast refresh-only JSON read:",
        "Dedicated refresh JSON read:",
        "For both refresh commands",
        "top-level payload fields for machine",
        "check_btc_1d_shadow_health.py --as-json",
    ]
    expected_command_fragments = [
        "run_btc_1d_shadow_update.py --refresh-only --sync-passes 2",
        "refresh_btc_1d_operator_stack.py --sync-passes 2",
    ]
    paths = [
        Path(r"C:\AI\Crypto\docs\operator_runbook.md"),
        Path(r"C:\AI\Crypto\docs\btc_1d_shadow_update_runbook.md"),
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for expected in expected_lines:
            assert expected in text, f"{expected} missing from {path}"
        for expected in expected_command_fragments:
            assert expected in text, f"{expected} missing from {path}"
        ordered_key_lines = [f"`{key}`" for key in FAST_GATE_SHARED_HANDOFF_KEYS]
        positions = [text.index(expected) for expected in ordered_key_lines]
        assert positions == sorted(positions), f"handoff key order drifted in {path}"


def test_contract_runbooks_lock_deployment_monitoring_active_handoff_wording() -> None:
    expected_lines = [
        "Final attack challenger handoff check:",
        "Open these when the handoff is fully advanced:",
        "- `analysis_results/btc_1d_operating_index_md_latest.md`",
        "- `analysis_results/btc_1d_operating_brief_md_latest.md`",
        "- `analysis_results/btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md`",
        "For the final attack challenger stage, verify:",
    ]
    paths = [
        Path(r"C:\AI\Crypto\docs\operator_runbook.md"),
        Path(r"C:\AI\Crypto\docs\btc_1d_shadow_update_runbook.md"),
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for expected in expected_lines:
            assert expected in text, f"{expected} missing from {path}"
        for expected in build_runbook_final_handoff_confirmation_lines():
            assert expected in text, f"{expected} missing from {path}"
        for expected in build_runbook_final_handoff_verification_lines():
            assert expected in text, f"{expected} missing from {path}"
