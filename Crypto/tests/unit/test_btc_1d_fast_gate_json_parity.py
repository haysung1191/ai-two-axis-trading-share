from __future__ import annotations

from pathlib import Path

from scripts.check_btc_1d_contract_health import check_contract_health
from scripts.check_btc_1d_shadow_health import build_parser, check_shadow_health
from scripts.run_btc_1d_shadow_update import refresh_operator_stack
from tests.unit.btc_1d_handoff_contract_keys import (
    FAST_GATE_SHARED_HANDOFF_KEYS,
    FAST_GATE_SHARED_HANDOFF_KEYS_WITH_BRIEF_MIRRORS,
)
from tests.unit.test_check_btc_1d_shadow_health import _write_latest_files, _write_paper_files
from tests.unit.test_refresh_btc_1d_operator_stack import _seed_refresh_ready_analysis_dir


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")


def test_shadow_and_contract_fast_gate_json_share_core_handoff_state(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _write_latest_files(analysis_dir)
    _write_paper_files(analysis_dir)
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": [
                "quick_read",
                "stack_roles",
                "stack",
                "near_miss_priority",
                "operating_read",
            ],
        },
    )
    _write_json(
        analysis_dir / "btc_1d_meta_contract_screen_latest.json",
        {
            "meta_contract_summary": {
                "all_health_standard_order_aligned": True,
            }
        },
    )

    shadow_result = check_shadow_health(
        analysis_dir=analysis_dir,
        args=build_parser().parse_args(["--analysis-dir", str(analysis_dir), "--as-json"]),
    )
    contract_result = check_contract_health(analysis_dir=analysis_dir)

    for key in FAST_GATE_SHARED_HANDOFF_KEYS_WITH_BRIEF_MIRRORS:
        assert shadow_result[key] == contract_result[key], key


def test_shadow_fast_gate_and_refresh_payload_share_core_handoff_state(
    tmp_path: Path,
) -> None:
    analysis_dir = _seed_refresh_ready_analysis_dir(tmp_path)

    refresh_result = refresh_operator_stack(analysis_dir=analysis_dir, sync_passes=2)
    shadow_result = check_shadow_health(
        analysis_dir=analysis_dir,
        args=build_parser().parse_args(["--analysis-dir", str(analysis_dir), "--as-json"]),
    )

    for key in FAST_GATE_SHARED_HANDOFF_KEYS:
        assert shadow_result[key] == refresh_result[key], key
