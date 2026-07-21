from __future__ import annotations

import json
from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
)
from scripts.check_btc_1d_contract_health import (
    build_parser,
    check_contract_health,
    render_contract_health_line,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_contract_health_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.analysis_dir == Path("analysis_results")
    assert args.as_json is False
    assert "health_order_aligned reports whether practical/research/contract health outputs share that same order." in build_parser().description
    assert "all_health_standard_order_aligned is a deprecated alias for health_order_aligned." in build_parser().description


def test_check_contract_health_reads_latest_contracts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "deployment_monitoring_active": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "deployment_monitoring_active": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": ["quick_read", "stack_roles", "stack", "near_miss_priority", "operating_read"],
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

    result = check_contract_health(analysis_dir=analysis_dir)

    assert result["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert result["operating_brief_version"] == "operating_v3"
    assert result["operating_index_version"] == "operating_v3"
    assert result["research_stack_version"] == "research_stack_v2"
    assert result["operating_contract_aligned"] is True
    assert result["paper_execution_contract_aligned"] is True
    assert result["contract_health_aligned"] is True
    assert result["research_contract_distinct"] is True
    assert result["contracts_are_well_partitioned"] is True
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        result["attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert (
        result["attack_challenger_bridge_report"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert result["operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        result["operating_brief_attack_challenger_next_step"]
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    assert (
        result["operating_brief_attack_challenger_bridge_report"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert result["deployment_monitoring_active"] is True
    assert result["operating_brief_deployment_monitoring_active"] is True
    assert result["attack_challenger_handoff_aligned"] is True
    assert result["shared_standard_check_order"] == ["practical", "research", "contract", "brief"]
    assert result["standard_check_order_aligned"] is True
    assert result["health_order_aligned"] is True
    assert result["all_health_standard_order_aligned"] is True
    assert (
        result["deprecated_fields"]["all_health_standard_order_aligned"]
        == "Deprecated alias for health_order_aligned. Prefer health_order_aligned."
    )


def test_check_contract_health_fails_when_paper_execution_contract_self_check_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": False,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": False,
            "contract_health_contracts_are_well_partitioned": False,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
            "attack_challenger_next_step": "challenger_live_shadow_locked_release_governance_entry",
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": False,
            "contract_health_contracts_are_well_partitioned": False,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
            "attack_challenger_next_step": "challenger_live_shadow_locked_release_governance_entry",
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json",
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": ["quick_read", "stack_roles", "stack", "near_miss_priority", "operating_read"],
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

    result = check_contract_health(analysis_dir=analysis_dir)

    assert result["operating_contract_aligned"] is True
    assert result["paper_execution_contract_aligned"] is False
    assert result["contract_health_aligned"] is True
    assert result["contracts_are_well_partitioned"] is False
    assert result["research_contract_distinct"] is True
    assert result["attack_challenger_handoff_aligned"] is True


def test_check_contract_health_exposes_attack_challenger_handoff_mismatch_between_index_and_brief(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
            "attack_challenger_next_step": "operator review pending",
            "attack_challenger_bridge_report": "analysis_results\\stale_handoff.json",
            "deployment_monitoring_active": False,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "deployment_monitoring_active": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": ["quick_read", "stack_roles", "stack", "near_miss_priority", "operating_read"],
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

    result = check_contract_health(analysis_dir=analysis_dir)

    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert result["operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready"] is False
    assert result["operating_brief_attack_challenger_next_step"] == "operator review pending"
    assert result["operating_brief_attack_challenger_bridge_report"] == "analysis_results\\stale_handoff.json"
    assert result["attack_challenger_handoff_aligned"] is False


def test_check_contract_health_exposes_deployment_monitoring_active_mismatch_between_index_and_brief(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": "deployment monitoring active",
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "deployment_monitoring_active": False,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order_version": "operating_v3",
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "deployment_monitoring_active": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": ["quick_read", "stack_roles", "stack", "near_miss_priority", "operating_read"],
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

    result = check_contract_health(analysis_dir=analysis_dir)

    assert result["deployment_monitoring_active"] is True
    assert result["operating_brief_deployment_monitoring_active"] is False
    assert result["attack_challenger_handoff_aligned"] is False


def test_render_contract_health_line_includes_core_fields() -> None:
    rendered = render_contract_health_line(
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "operating_brief_version": "operating_v3",
            "operating_index_version": "operating_v3",
            "research_stack_version": "research_stack_v2",
            "operating_contract_aligned": True,
            "paper_execution_contract_aligned": True,
            "contract_health_aligned": True,
            "research_contract_distinct": True,
            "contracts_are_well_partitioned": True,
            "preferred_operating_contract_version": "operating_v3",
            "preferred_research_contract_version": "research_stack_v2",
            "shared_standard_check_order": ["practical", "research", "contract", "brief"],
            "standard_check_order_aligned": True,
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "deployment_monitoring_active": True,
            "operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "operating_brief_attack_challenger_next_step": ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
            "operating_brief_attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "operating_brief_deployment_monitoring_active": True,
            "attack_challenger_handoff_aligned": True,
            "health_order_aligned": True,
            "all_health_standard_order_aligned": True,
            "deprecated_fields": {
                "all_health_standard_order_aligned": "Deprecated alias for health_order_aligned. Prefer health_order_aligned."
            },
        }
    )

    assert "BTC 1d contract health" in rendered
    assert "operating_brief=operating_v3" in rendered
    assert "operating_index=operating_v3" in rendered
    assert "research=research_stack_v2" in rendered
    assert "aligned=True" in rendered
    assert "paper_execution_aligned=True" in rendered
    assert "contract_health_aligned=True" in rendered
    assert "partitioned=True" in rendered
    assert "attack_challenger_handoff_ready=True" in rendered
    assert (
        f"attack_challenger_next={ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}"
        in rendered
    )
    assert (
        "attack_challenger_bridge_report="
        "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    ) in rendered
    assert "deployment_monitoring_active=True" in rendered
    assert "attack_challenger_handoff_aligned=True" in rendered
    assert "standard_order_aligned=True" in rendered
    assert "health_order_aligned=True" in rendered
    assert "standard_order=practical > research > contract > brief" in rendered
