from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_btc_1d_research_stack_health import (
    check_research_stack_health,
    render_research_stack_health_line,
)
from scripts.check_btc_1d_contract_health import (
    check_contract_health,
    render_contract_health_line,
)
from scripts.check_btc_1d_practical_health import render_practical_health_line
from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a short BTC 1d operating brief from the latest stable artifacts. "
            "Standard check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--as-json", action="store_true")
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _resolve_analysis_path(analysis_dir: Path, raw_path: str | Path | None) -> Path:
    if raw_path is None:
        return analysis_dir / "__missing__.json"
    path = Path(raw_path)
    if path.is_absolute():
        return path
    analysis_relative = analysis_dir.parent / path
    if analysis_relative.exists():
        return analysis_relative
    if path.exists():
        return path
    return analysis_relative


def _replace_research_segment(line: str, fresh_research_line: str) -> str:
    if not line or not fresh_research_line:
        return line
    segments = line.split(" || ")
    replaced = False
    refreshed_segments: list[str] = []
    for segment in segments:
        if segment.startswith("BTC 1d research stack |"):
            refreshed_segments.append(fresh_research_line)
            replaced = True
        else:
            refreshed_segments.append(segment)
    if replaced:
        return " || ".join(refreshed_segments)
    return line


def _render_paper_ledger_snapshot_read(snapshot: dict[str, object] | None) -> str:
    payload = snapshot or {}
    return (
        "paper ledger | "
        f"open={int(payload.get('open_position_count', 0))} | "
        f"closed={int(payload.get('closed_position_count', 0))} | "
        f"exit_fills={int(payload.get('exit_fill_count', 0))} | "
        f"orders={int(payload.get('order_count', 0))} | "
        f"fills={int(payload.get('fill_count', 0))}"
    )


def _paper_summary_contract_bool(summary: dict[str, Any], field: str, legacy_field: str) -> bool:
    if field in summary:
        return bool(summary.get(field, False))
    return bool(summary.get(legacy_field, False))


def _brief_contract_health_bool(
    brief: dict[str, Any],
    top_level_field: str,
    nested_field: str,
    fallback_field: str | None = None,
) -> bool:
    if top_level_field in brief:
        return bool(brief.get(top_level_field, False))
    contract_health = brief.get("contract_health", {})
    if nested_field in contract_health:
        return bool(contract_health.get(nested_field, False))
    if fallback_field is not None:
        return bool(brief.get(fallback_field, False))
    return False


def _derive_operator_verdict(
    *,
    shadow_decision: str,
    quick_read_contract_partitioned: bool,
    contract_health_aligned: bool,
    execution_contract_aligned: bool,
    paper_execution_contract_aligned: bool,
    paper_ledger_consistent: bool,
) -> str:
    dashboard_ready = (
        shadow_decision == "ready"
        and quick_read_contract_partitioned
        and contract_health_aligned
        and execution_contract_aligned
        and paper_execution_contract_aligned
        and paper_ledger_consistent
    )
    if dashboard_ready:
        return "ready"
    if (
        quick_read_contract_partitioned
        and contract_health_aligned
        and execution_contract_aligned
        and paper_execution_contract_aligned
        and paper_ledger_consistent
        and shadow_decision == "shadow_ready_for_btc_only"
    ):
        return "shadow_monitoring_ready"
    if not (
        quick_read_contract_partitioned
        and contract_health_aligned
        and execution_contract_aligned
        and paper_execution_contract_aligned
        and paper_ledger_consistent
    ):
        return "ops_repair_required"
    return "validation_in_progress"


def build_operating_brief(*, analysis_dir: Path) -> dict[str, Any]:
    summary = _load_json(analysis_dir / "btc_1d_latest_summary_latest.json")
    index_payload = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")
    checks = index_payload["checks"]
    carry = checks["carry"]
    survivability = checks["survivability"]
    walk_forward = checks["walk_forward"]
    friction = checks["friction"]
    eth_cross_check = checks["eth_cross_check"]
    practical_gate_path = index_payload.get("practical_promotion_gate") or str(
        analysis_dir / "btc_1d_practical_promotion_gate_latest.json"
    )
    practical_gate_file = _resolve_analysis_path(analysis_dir, practical_gate_path)
    practical_gate = _load_json(practical_gate_file) if practical_gate_file.exists() else None
    practical_status_label = (
        practical_gate.get("status_label", practical_gate["decision"]) if practical_gate else "unknown"
    )
    research_stack_health = check_research_stack_health(analysis_dir=analysis_dir)
    research_stack_status = (
        render_research_stack_health_line(research_stack_health) if research_stack_health else "unknown"
    )
    contract_health = check_contract_health(analysis_dir=analysis_dir)
    contract_health_line = render_contract_health_line(contract_health) if contract_health else "unknown"
    contract_health_operating_contract_aligned = bool(
        (contract_health or {}).get("operating_contract_aligned", False)
    )
    contract_health_paper_execution_contract_aligned = bool(
        (contract_health or {}).get("paper_execution_contract_aligned", False)
    )
    contract_health_aligned = bool(
        (contract_health or {}).get("contract_health_aligned", False)
    )
    contract_health_contracts_are_well_partitioned = bool(
        (contract_health or {}).get("contracts_are_well_partitioned", False)
    )
    paper_nightly_health_line = index_payload.get("paper_nightly_health_line", "")
    execution_health_line = _replace_research_segment(
        str(index_payload.get("execution_health_line", "")),
        research_stack_status,
    )
    execution_contract_health_line = _replace_research_segment(
        str(index_payload.get("execution_contract_health_line", "")),
        research_stack_status,
    )
    execution_contract_read = index_payload.get("execution_contract_read", "")
    paper_nightly_summary_path = _resolve_analysis_path(
        analysis_dir,
        index_payload.get("paper_nightly_summary")
        or str(analysis_dir / "btc_1d_paper_nightly_summary_latest.json"),
    )
    paper_nightly_summary = (
        _load_json(paper_nightly_summary_path) if paper_nightly_summary_path.exists() else {}
    )
    execution_contract_aligned = False
    execution_contract_paper_ledger_snapshot_summary_aligned = False
    execution_contract_paper_execution_contract_checked_aligned_entry_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
            False,
        )
    )
    execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
            False,
        )
    )
    execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
            False,
        )
    )
    execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
            False,
        )
    )
    execution_contract_paper_execution_contract_checked_aligned_summary_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
            False,
        )
    )
    execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
            False,
        )
    )
    execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
            False,
        )
    )
    execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
        index_payload.get(
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
            False,
        )
    )
    paper_execution_contract_checked = bool(
        paper_nightly_summary.get(
            "execution_contract_checked",
            index_payload.get("paper_execution_contract_checked", False),
        )
    )
    paper_execution_contract_aligned = bool(
        paper_nightly_summary.get(
            "execution_contract_aligned",
            index_payload.get("paper_execution_contract_aligned", False),
        )
    )
    paper_execution_contract_checked_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_checked_aligned",
            "execution_contract_paper_execution_contract_checked_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_checked_aligned", False))
    )
    paper_execution_contract_aligned_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_aligned_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_aligned_aligned", False))
    )
    paper_execution_contract_checked_summary_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_checked_summary_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_checked_summary_aligned", False))
    )
    paper_execution_contract_aligned_summary_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_aligned_summary_aligned", False))
    )
    paper_execution_contract_checked_aligned_entry_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_checked_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_checked_aligned_entry_aligned", False))
    )
    paper_execution_contract_aligned_aligned_entry_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_aligned_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_aligned_aligned_entry_aligned", False))
    )
    paper_execution_contract_checked_summary_aligned_entry_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_checked_summary_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False))
    )
    paper_execution_contract_aligned_summary_aligned_entry_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False))
    )
    paper_execution_contract_checked_aligned_summary_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_checked_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_checked_aligned_summary_aligned", False))
    )
    paper_execution_contract_aligned_aligned_summary_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_aligned_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_aligned_aligned_summary_aligned", False))
    )
    paper_execution_contract_checked_summary_aligned_summary_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_checked_summary_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False))
    )
    paper_execution_contract_aligned_summary_aligned_summary_aligned = (
        _paper_summary_contract_bool(
            paper_nightly_summary,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
        )
        if paper_nightly_summary
        else bool(index_payload.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False))
    )
    derived_paper_execution_contract_aligned = all(
        [
            paper_execution_contract_checked
            == bool(index_payload.get("paper_execution_contract_checked", paper_execution_contract_checked)),
            paper_execution_contract_aligned
            == bool(index_payload.get("paper_execution_contract_aligned", paper_execution_contract_aligned)),
            paper_execution_contract_checked_aligned
            == bool(index_payload.get("paper_execution_contract_checked_aligned", paper_execution_contract_checked_aligned)),
            paper_execution_contract_aligned_aligned
            == bool(index_payload.get("paper_execution_contract_aligned_aligned", paper_execution_contract_aligned_aligned)),
            paper_execution_contract_checked_summary_aligned
            == bool(index_payload.get("paper_execution_contract_checked_summary_aligned", paper_execution_contract_checked_summary_aligned)),
            paper_execution_contract_aligned_summary_aligned
            == bool(index_payload.get("paper_execution_contract_aligned_summary_aligned", paper_execution_contract_aligned_summary_aligned)),
            paper_execution_contract_checked_aligned_entry_aligned
            == bool(index_payload.get("paper_execution_contract_checked_aligned_entry_aligned", paper_execution_contract_checked_aligned_entry_aligned)),
            paper_execution_contract_aligned_aligned_entry_aligned
            == bool(index_payload.get("paper_execution_contract_aligned_aligned_entry_aligned", paper_execution_contract_aligned_aligned_entry_aligned)),
            paper_execution_contract_checked_summary_aligned_entry_aligned
            == bool(index_payload.get("paper_execution_contract_checked_summary_aligned_entry_aligned", paper_execution_contract_checked_summary_aligned_entry_aligned)),
            paper_execution_contract_aligned_summary_aligned_entry_aligned
            == bool(index_payload.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", paper_execution_contract_aligned_summary_aligned_entry_aligned)),
            paper_execution_contract_checked_aligned_summary_aligned
            == bool(index_payload.get("paper_execution_contract_checked_aligned_summary_aligned", paper_execution_contract_checked_aligned_summary_aligned)),
            paper_execution_contract_aligned_aligned_summary_aligned
            == bool(index_payload.get("paper_execution_contract_aligned_aligned_summary_aligned", paper_execution_contract_aligned_aligned_summary_aligned)),
            paper_execution_contract_checked_summary_aligned_summary_aligned
            == bool(index_payload.get("paper_execution_contract_checked_summary_aligned_summary_aligned", paper_execution_contract_checked_summary_aligned_summary_aligned)),
            paper_execution_contract_aligned_summary_aligned_summary_aligned
            == bool(index_payload.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", paper_execution_contract_aligned_summary_aligned_summary_aligned)),
        ]
    )
    if not contract_health_operating_contract_aligned:
        contract_health_operating_contract_aligned = bool(
            index_payload.get("contract_health_operating_contract_aligned", True)
        )
    if not contract_health_paper_execution_contract_aligned:
        contract_health_paper_execution_contract_aligned = bool(
            index_payload.get(
                "contract_health_paper_execution_contract_aligned",
                derived_paper_execution_contract_aligned,
            )
        )
    if not contract_health_aligned:
        contract_health_aligned = bool(
            index_payload.get(
                "contract_health_aligned",
                contract_health_operating_contract_aligned
                and contract_health_paper_execution_contract_aligned,
            )
        )
    if not contract_health_contracts_are_well_partitioned:
        contract_health_contracts_are_well_partitioned = bool(
            index_payload.get(
                "contract_health_contracts_are_well_partitioned",
                contract_health_operating_contract_aligned
                and contract_health_paper_execution_contract_aligned,
            )
        )
    execution_contract_screen_path = _resolve_analysis_path(
        analysis_dir,
        index_payload.get("execution_contract_screen")
        or str(analysis_dir / "btc_1d_execution_contract_screen_latest.json"),
    )
    if execution_contract_screen_path.exists():
        execution_contract_payload = _load_json(execution_contract_screen_path)
        execution_contract_summary = execution_contract_payload.get("execution_contract_summary", {})
        execution_contract_verdict = execution_contract_payload.get("execution_contract_verdict", {})
        execution_contract_aligned = bool(
            execution_contract_verdict.get("execution_contract_aligned", False)
        )
        execution_contract_paper_ledger_snapshot_summary_aligned = bool(
            execution_contract_summary.get("paper_ledger_snapshot_summary_aligned", False)
        )
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_aligned_entry_aligned",
                execution_contract_paper_execution_contract_checked_aligned_entry_aligned,
            )
        )
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_aligned_entry_aligned",
                execution_contract_paper_execution_contract_aligned_aligned_entry_aligned,
            )
        )
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_summary_aligned_entry_aligned",
                execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned,
            )
        )
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_summary_aligned_entry_aligned",
                execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned,
            )
        )
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_aligned_summary_aligned",
                execution_contract_paper_execution_contract_checked_aligned_summary_aligned,
            )
        )
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_aligned_summary_aligned",
                execution_contract_paper_execution_contract_aligned_aligned_summary_aligned,
            )
        )
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_summary_aligned_summary_aligned",
                execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned,
            )
        )
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_summary_aligned_summary_aligned",
                execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned,
            )
        )
    paper_execution_read = index_payload.get("paper_execution_read", "")
    paper_exit_duplicate_run = bool(index_payload.get("paper_exit_duplicate_run", False))
    paper_ledger_consistent = bool(index_payload.get("paper_ledger_consistent", False))
    paper_ledger_snapshot = dict(index_payload.get("paper_ledger_snapshot", {}) or {})
    paper_ledger_snapshot_read = index_payload.get(
        "paper_ledger_snapshot_read",
        _render_paper_ledger_snapshot_read(paper_ledger_snapshot),
    )
    attack_challenger_candidate = str(index_payload.get("attack_challenger_candidate", ""))
    attack_challenger_role_assignment = str(
        index_payload.get("attack_challenger_role_assignment", "")
    )
    attack_challenger_promotion_ready = bool(
        index_payload.get("attack_challenger_promotion_ready", False)
    )
    attack_challenger_next_step = str(index_payload.get("attack_challenger_next_step", ""))
    attack_challenger_paper_validation_cagr = index_payload.get(
        "attack_challenger_paper_validation_cagr"
    )
    attack_challenger_paper_validation_max_drawdown = index_payload.get(
        "attack_challenger_paper_validation_max_drawdown"
    )
    attack_challenger_walk_forward_sensitivity_max_drift = index_payload.get(
        "attack_challenger_walk_forward_sensitivity_max_drift"
    )
    attack_challenger_friction_final_decision = str(
        index_payload.get("attack_challenger_friction_final_decision", "")
    )
    attack_challenger_bridge_entry_ready = bool(
        index_payload.get("attack_challenger_bridge_entry_ready", False)
    )
    attack_challenger_bridge_queue_lane = str(
        index_payload.get("attack_challenger_bridge_queue_lane", "")
    )
    attack_challenger_execution_contract_entry_ready = bool(
        index_payload.get("attack_challenger_execution_contract_entry_ready", False)
    )
    attack_challenger_execution_contract_queue_lane = str(
        index_payload.get("attack_challenger_execution_contract_queue_lane", "")
    )
    attack_challenger_operator_stack_handoff_ready = bool(
        index_payload.get("attack_challenger_operator_stack_handoff_ready", False)
    )
    attack_challenger_operator_stack_handoff_lane = str(
        index_payload.get("attack_challenger_operator_stack_handoff_lane", "")
    )
    attack_challenger_operator_runbook_candidate_entry_ready = bool(
        index_payload.get("attack_challenger_operator_runbook_candidate_entry_ready", False)
    )
    attack_challenger_operator_runbook_candidate_entry_lane = str(
        index_payload.get("attack_challenger_operator_runbook_candidate_entry_lane", "")
    )
    attack_challenger_operator_runbook_execution_entry_ready = bool(
        index_payload.get("attack_challenger_operator_runbook_execution_entry_ready", False)
    )
    attack_challenger_operator_runbook_execution_entry_lane = str(
        index_payload.get("attack_challenger_operator_runbook_execution_entry_lane", "")
    )
    attack_challenger_live_readiness_review_ready = bool(
        index_payload.get("attack_challenger_live_readiness_review_ready", False)
    )
    attack_challenger_live_readiness_review_lane = str(
        index_payload.get("attack_challenger_live_readiness_review_lane", "")
    )
    attack_challenger_live_shadow_activation_review_ready = bool(
        index_payload.get("attack_challenger_live_shadow_activation_review_ready", False)
    )
    attack_challenger_live_shadow_activation_review_lane = str(
        index_payload.get("attack_challenger_live_shadow_activation_review_lane", "")
    )
    attack_challenger_live_candidate_entry_ready = bool(
        index_payload.get("attack_challenger_live_candidate_entry_ready", False)
    )
    attack_challenger_live_candidate_entry_lane = str(
        index_payload.get("attack_challenger_live_candidate_entry_lane", "")
    )
    attack_challenger_live_operator_paper_entry_ready = bool(
        index_payload.get("attack_challenger_live_operator_paper_entry_ready", False)
    )
    attack_challenger_live_operator_paper_entry_lane = str(
        index_payload.get("attack_challenger_live_operator_paper_entry_lane", "")
    )
    attack_challenger_live_shadow_governance_review_ready = bool(
        index_payload.get("attack_challenger_live_shadow_governance_review_ready", False)
    )
    attack_challenger_live_shadow_governance_review_lane = str(
        index_payload.get("attack_challenger_live_shadow_governance_review_lane", "")
    )
    attack_challenger_live_governed_shadow_entry_ready = bool(
        index_payload.get("attack_challenger_live_governed_shadow_entry_ready", False)
    )
    attack_challenger_live_governed_shadow_entry_lane = str(
        index_payload.get("attack_challenger_live_governed_shadow_entry_lane", "")
    )
    attack_challenger_live_shadow_candidate_paper_review_ready = bool(
        index_payload.get(
            "attack_challenger_live_shadow_candidate_paper_review_ready", False
        )
    )
    attack_challenger_live_shadow_candidate_paper_review_lane = str(
        index_payload.get("attack_challenger_live_shadow_candidate_paper_review_lane", "")
    )
    attack_challenger_live_shadow_candidate_governance_lock_ready = bool(
        index_payload.get(
            "attack_challenger_live_shadow_candidate_governance_lock_ready", False
        )
    )
    attack_challenger_live_shadow_candidate_governance_lock_lane = str(
        index_payload.get(
            "attack_challenger_live_shadow_candidate_governance_lock_lane", ""
        )
    )
    attack_challenger_live_shadow_locked_entry_ready = bool(
        index_payload.get("attack_challenger_live_shadow_locked_entry_ready", False)
    )
    attack_challenger_live_shadow_locked_entry_lane = str(
        index_payload.get("attack_challenger_live_shadow_locked_entry_lane", "")
    )
    attack_challenger_live_shadow_locked_candidate_review_ready = bool(
        index_payload.get(
            "attack_challenger_live_shadow_locked_candidate_review_ready", False
        )
    )
    attack_challenger_live_shadow_locked_candidate_review_lane = str(
        index_payload.get(
            "attack_challenger_live_shadow_locked_candidate_review_lane", ""
        )
    )
    attack_challenger_live_shadow_locked_candidate_release_review_ready = bool(
        index_payload.get(
            "attack_challenger_live_shadow_locked_candidate_release_review_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_candidate_release_review_lane = str(
        index_payload.get(
            "attack_challenger_live_shadow_locked_candidate_release_review_lane",
            "",
        )
    )
    attack_challenger_live_shadow_locked_release_entry_ready = bool(
        index_payload.get("attack_challenger_live_shadow_locked_release_entry_ready", False)
    )
    attack_challenger_live_shadow_locked_release_entry_lane = str(
        index_payload.get("attack_challenger_live_shadow_locked_release_entry_lane", "")
    )
    attack_challenger_live_shadow_locked_release_candidate_review_ready = bool(
        index_payload.get(
            "attack_challenger_live_shadow_locked_release_candidate_review_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_candidate_review_lane = str(
        index_payload.get(
            "attack_challenger_live_shadow_locked_release_candidate_review_lane",
            "",
        )
    )
    attack_challenger_live_shadow_locked_release_governance_check_ready = bool(
        index_payload.get(
            "attack_challenger_live_shadow_locked_release_governance_check_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_governance_check_lane = str(
        index_payload.get(
            "attack_challenger_live_shadow_locked_release_governance_check_lane",
            "",
        )
    )
    attack_challenger_live_shadow_locked_release_governance_entry_ready = bool(
        index_payload.get(
            "attack_challenger_live_shadow_locked_release_governance_entry_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_governance_entry_lane = str(
        index_payload.get(
            "attack_challenger_live_shadow_locked_release_governance_entry_lane",
            "",
        )
    )
    attack_challenger_remote_monitoring_deployment_handoff_ready = bool(
        index_payload.get(
            "attack_challenger_remote_monitoring_deployment_handoff_ready",
            False,
        )
    )
    attack_challenger_remote_monitoring_deployment_handoff_lane = str(
        index_payload.get(
            "attack_challenger_remote_monitoring_deployment_handoff_lane",
            "",
        )
    )
    deployment_monitoring_active = bool(
        index_payload.get(
            "deployment_monitoring_active",
            attack_challenger_remote_monitoring_deployment_handoff_ready
            and str(summary["shadow_decision"]) == "shadow_ready_for_btc_only"
            and attack_challenger_next_step
            == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
        )
    )
    attack_challenger_bridge_report = str(index_payload.get("attack_challenger_bridge_report", ""))
    operator_verdict = str(
        index_payload.get(
            "operator_verdict",
            _derive_operator_verdict(
                shadow_decision=str(summary["shadow_decision"]),
                quick_read_contract_partitioned=contract_health_contracts_are_well_partitioned,
                contract_health_aligned=contract_health_aligned,
                execution_contract_aligned=execution_contract_aligned,
                paper_execution_contract_aligned=paper_execution_contract_aligned,
                paper_ledger_consistent=paper_ledger_consistent,
            ),
        )
    )
    standard_check_order = ["practical", "research", "contract", "brief"]
    regression_lock_test = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    practical_carry_metrics = practical_gate.get("carry_metrics", {}) if practical_gate else {}
    practical = {
        "decision": practical_gate["decision"] if practical_gate else "unknown",
        "status_label": practical_status_label,
        "ok": practical_gate["ok"] if practical_gate else False,
        "caveats": practical_gate.get("caveats", []) if practical_gate else [],
        "caveat_count": len(practical_gate.get("caveats", [])) if practical_gate else 0,
        "candidate": practical_gate.get("candidate", summary["candidate"]) if practical_gate else summary["candidate"],
        "sharpe": practical_carry_metrics.get("sharpe", carry["sharpe"]),
        "cagr": practical_carry_metrics.get("cagr", carry["cagr"]),
        "max_drawdown": practical_carry_metrics.get("max_drawdown", carry["max_drawdown"]),
    }
    combined_health_line = f"{render_practical_health_line(practical)} || {research_stack_status}"
    return {
        "candidate": summary["candidate"],
        "scope": summary["scope"],
        "shadow_decision": summary["shadow_decision"],
        "operator_verdict": operator_verdict,
        "deployment_monitoring_active": deployment_monitoring_active,
        "standard_check_order": standard_check_order,
        "regression_lock_test": regression_lock_test,
        "quick_read_order_version": "operating_v3",
        "quick_read_order": [
            "practical_status",
            "combined_health",
            "research_stack_status",
            "carry",
            "survivability",
            "walk_forward",
            "friction",
            "eth_cross_check",
            "quick_read_contract",
            "open_first",
        ],
        "practical_status_label": practical_status_label,
        "research_stack_status": research_stack_status,
        "contract_health_line": contract_health_line,
        "contract_health_operating_contract_aligned": contract_health_operating_contract_aligned,
        "contract_health_paper_execution_contract_aligned": contract_health_paper_execution_contract_aligned,
        "contract_health_aligned": contract_health_aligned,
        "contract_health_contracts_are_well_partitioned": contract_health_contracts_are_well_partitioned,
        "combined_health_line": combined_health_line,
        "paper_nightly_health_line": paper_nightly_health_line,
        "execution_health_line": execution_health_line,
        "execution_contract_health_line": execution_contract_health_line,
        "execution_contract_read": execution_contract_read,
        "execution_contract_aligned": execution_contract_aligned,
        "execution_contract_paper_ledger_snapshot_summary_aligned": execution_contract_paper_ledger_snapshot_summary_aligned,
        "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": (
            execution_contract_paper_execution_contract_checked_aligned_entry_aligned
        ),
        "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": (
            execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
        ),
        "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": (
            execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
        ),
        "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
            execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
        ),
        "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": (
            execution_contract_paper_execution_contract_checked_aligned_summary_aligned
        ),
        "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": (
            execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
        ),
        "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": (
            execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
        ),
        "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
            execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
        ),
        "paper_execution_contract_checked": paper_execution_contract_checked,
        "paper_execution_contract_aligned": paper_execution_contract_aligned,
        "paper_execution_contract_checked_aligned": paper_execution_contract_checked_aligned,
        "paper_execution_contract_aligned_aligned": paper_execution_contract_aligned_aligned,
        "paper_execution_contract_checked_summary_aligned": paper_execution_contract_checked_summary_aligned,
        "paper_execution_contract_aligned_summary_aligned": paper_execution_contract_aligned_summary_aligned,
        "paper_execution_contract_checked_aligned_entry_aligned": (
            paper_execution_contract_checked_aligned_entry_aligned
        ),
        "paper_execution_contract_aligned_aligned_entry_aligned": (
            paper_execution_contract_aligned_aligned_entry_aligned
        ),
        "paper_execution_contract_checked_summary_aligned_entry_aligned": (
            paper_execution_contract_checked_summary_aligned_entry_aligned
        ),
        "paper_execution_contract_aligned_summary_aligned_entry_aligned": (
            paper_execution_contract_aligned_summary_aligned_entry_aligned
        ),
        "paper_execution_contract_checked_aligned_summary_aligned": (
            paper_execution_contract_checked_aligned_summary_aligned
        ),
        "paper_execution_contract_aligned_aligned_summary_aligned": (
            paper_execution_contract_aligned_aligned_summary_aligned
        ),
        "paper_execution_contract_checked_summary_aligned_summary_aligned": (
            paper_execution_contract_checked_summary_aligned_summary_aligned
        ),
        "paper_execution_contract_aligned_summary_aligned_summary_aligned": (
            paper_execution_contract_aligned_summary_aligned_summary_aligned
        ),
        "paper_execution_read": paper_execution_read,
        "paper_exit_duplicate_run": paper_exit_duplicate_run,
        "paper_ledger_consistent": paper_ledger_consistent,
        "paper_ledger_snapshot": paper_ledger_snapshot,
        "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
        "attack_challenger_candidate": attack_challenger_candidate,
        "attack_challenger_role_assignment": attack_challenger_role_assignment,
        "attack_challenger_promotion_ready": attack_challenger_promotion_ready,
        "attack_challenger_next_step": attack_challenger_next_step,
        "attack_challenger_paper_validation_cagr": attack_challenger_paper_validation_cagr,
        "attack_challenger_paper_validation_max_drawdown": attack_challenger_paper_validation_max_drawdown,
        "attack_challenger_walk_forward_sensitivity_max_drift": attack_challenger_walk_forward_sensitivity_max_drift,
        "attack_challenger_friction_final_decision": attack_challenger_friction_final_decision,
        "attack_challenger_bridge_entry_ready": attack_challenger_bridge_entry_ready,
        "attack_challenger_bridge_queue_lane": attack_challenger_bridge_queue_lane,
        "attack_challenger_execution_contract_entry_ready": attack_challenger_execution_contract_entry_ready,
        "attack_challenger_execution_contract_queue_lane": attack_challenger_execution_contract_queue_lane,
        "attack_challenger_operator_stack_handoff_ready": attack_challenger_operator_stack_handoff_ready,
        "attack_challenger_operator_stack_handoff_lane": attack_challenger_operator_stack_handoff_lane,
        "attack_challenger_operator_runbook_candidate_entry_ready": attack_challenger_operator_runbook_candidate_entry_ready,
        "attack_challenger_operator_runbook_candidate_entry_lane": attack_challenger_operator_runbook_candidate_entry_lane,
        "attack_challenger_operator_runbook_execution_entry_ready": attack_challenger_operator_runbook_execution_entry_ready,
        "attack_challenger_operator_runbook_execution_entry_lane": attack_challenger_operator_runbook_execution_entry_lane,
        "attack_challenger_live_readiness_review_ready": attack_challenger_live_readiness_review_ready,
        "attack_challenger_live_readiness_review_lane": attack_challenger_live_readiness_review_lane,
        "attack_challenger_live_shadow_activation_review_ready": attack_challenger_live_shadow_activation_review_ready,
        "attack_challenger_live_shadow_activation_review_lane": attack_challenger_live_shadow_activation_review_lane,
        "attack_challenger_live_candidate_entry_ready": attack_challenger_live_candidate_entry_ready,
        "attack_challenger_live_candidate_entry_lane": attack_challenger_live_candidate_entry_lane,
        "attack_challenger_live_operator_paper_entry_ready": attack_challenger_live_operator_paper_entry_ready,
        "attack_challenger_live_operator_paper_entry_lane": attack_challenger_live_operator_paper_entry_lane,
        "attack_challenger_live_shadow_governance_review_ready": attack_challenger_live_shadow_governance_review_ready,
        "attack_challenger_live_shadow_governance_review_lane": attack_challenger_live_shadow_governance_review_lane,
        "attack_challenger_live_governed_shadow_entry_ready": attack_challenger_live_governed_shadow_entry_ready,
        "attack_challenger_live_governed_shadow_entry_lane": attack_challenger_live_governed_shadow_entry_lane,
        "attack_challenger_live_shadow_candidate_paper_review_ready": attack_challenger_live_shadow_candidate_paper_review_ready,
        "attack_challenger_live_shadow_candidate_paper_review_lane": attack_challenger_live_shadow_candidate_paper_review_lane,
        "attack_challenger_live_shadow_candidate_governance_lock_ready": attack_challenger_live_shadow_candidate_governance_lock_ready,
        "attack_challenger_live_shadow_candidate_governance_lock_lane": attack_challenger_live_shadow_candidate_governance_lock_lane,
        "attack_challenger_live_shadow_locked_entry_ready": attack_challenger_live_shadow_locked_entry_ready,
        "attack_challenger_live_shadow_locked_entry_lane": attack_challenger_live_shadow_locked_entry_lane,
        "attack_challenger_live_shadow_locked_candidate_review_ready": attack_challenger_live_shadow_locked_candidate_review_ready,
        "attack_challenger_live_shadow_locked_candidate_review_lane": attack_challenger_live_shadow_locked_candidate_review_lane,
        "attack_challenger_live_shadow_locked_candidate_release_review_ready": attack_challenger_live_shadow_locked_candidate_release_review_ready,
        "attack_challenger_live_shadow_locked_candidate_release_review_lane": attack_challenger_live_shadow_locked_candidate_release_review_lane,
        "attack_challenger_live_shadow_locked_release_entry_ready": attack_challenger_live_shadow_locked_release_entry_ready,
        "attack_challenger_live_shadow_locked_release_entry_lane": attack_challenger_live_shadow_locked_release_entry_lane,
        "attack_challenger_live_shadow_locked_release_candidate_review_ready": attack_challenger_live_shadow_locked_release_candidate_review_ready,
        "attack_challenger_live_shadow_locked_release_candidate_review_lane": attack_challenger_live_shadow_locked_release_candidate_review_lane,
        "attack_challenger_live_shadow_locked_release_governance_check_ready": attack_challenger_live_shadow_locked_release_governance_check_ready,
        "attack_challenger_live_shadow_locked_release_governance_check_lane": attack_challenger_live_shadow_locked_release_governance_check_lane,
        "attack_challenger_live_shadow_locked_release_governance_entry_ready": attack_challenger_live_shadow_locked_release_governance_entry_ready,
        "attack_challenger_live_shadow_locked_release_governance_entry_lane": attack_challenger_live_shadow_locked_release_governance_entry_lane,
        "attack_challenger_remote_monitoring_deployment_handoff_ready": attack_challenger_remote_monitoring_deployment_handoff_ready,
        "attack_challenger_remote_monitoring_deployment_handoff_lane": attack_challenger_remote_monitoring_deployment_handoff_lane,
        "attack_challenger_bridge_report": attack_challenger_bridge_report,
        "practical": practical,
        "carry": {
            "periods": carry["periods"],
            "decision": carry["decision"],
            "sharpe": carry["sharpe"],
            "cagr": carry["cagr"],
            "max_drawdown": carry["max_drawdown"],
        },
        "survivability": {
            "periods": survivability["periods"],
            "decision": survivability["decision"],
            "sharpe": survivability["sharpe"],
            "cagr": survivability["cagr"],
            "max_drawdown": survivability["max_drawdown"],
        },
        "walk_forward": {
            "passed": walk_forward["passed"],
            "oos_sharpe": walk_forward["oos_sharpe"],
            "oos_cagr": walk_forward["oos_cagr"],
            "oos_max_drawdown": walk_forward["oos_max_drawdown"],
            "sensitivity_max_drift": walk_forward["sensitivity_max_drift"],
            "unstable_parameters": walk_forward["unstable_parameters"],
        },
        "friction": {
            "decision": friction["decision"],
            "heaviest_level_bps": friction["heaviest_level_bps"],
            "heaviest_level_sharpe": friction["heaviest_level_sharpe"],
        },
        "eth_cross_check": {
            "symbol": eth_cross_check["symbol"],
            "pass_rate": eth_cross_check["pass_rate"],
            "pass_count": eth_cross_check["pass_count"],
            "total_count": eth_cross_check["total_count"],
        },
        "research_stack_health": research_stack_health,
        "contract_health": contract_health,
        "paths": {
            "operating_index_md": index_payload["operating_index_md"] if "operating_index_md" in index_payload else str(
                analysis_dir / "btc_1d_operating_index_md_latest.md"
            ),
            "practical_promotion_gate_md": index_payload.get("practical_promotion_gate_md", str(
                analysis_dir / "btc_1d_practical_promotion_gate_md_latest.md"
            )),
            "research_stack_operating_brief_md": index_payload.get(
                "research_stack_operating_brief_md",
                str(analysis_dir / "btc_1d_research_stack_operating_brief_md_latest.md"),
            ),
            "quick_read_contract_screen_md": index_payload.get(
                "quick_read_contract_screen_md",
                str(analysis_dir / "btc_1d_quick_read_contract_screen_md_latest.md"),
            ),
            "execution_contract_screen_md": index_payload.get(
                "execution_contract_screen_md",
                str(analysis_dir / "btc_1d_execution_contract_screen_md_latest.md"),
            ),
            "execution_meta_contract_test_index_md": index_payload.get(
                "execution_meta_contract_test_index_md",
                str(analysis_dir / "btc_1d_execution_meta_contract_test_index_md_latest.md"),
            ),
            "meta_contract_screen_md": index_payload.get(
                "meta_contract_screen_md",
                str(analysis_dir / "btc_1d_meta_contract_screen_md_latest.md"),
            ),
            "paper_nightly_summary": index_payload.get(
                "paper_nightly_summary",
                str(analysis_dir / "btc_1d_paper_nightly_summary_latest.json"),
            ),
            "paper_nightly_summary_md": index_payload.get(
                "paper_nightly_summary_md",
                str(analysis_dir / "btc_1d_paper_nightly_summary_md_latest.md"),
            ),
            "summary_md": index_payload["latest_summary_md"],
            "shadow_packet_md": index_payload["shadow_packet_md"],
            "status_board_md": index_payload["status_board_md"],
            "baseline_freeze_md": index_payload["baseline_freeze_md"],
            "shadow_readiness_md": index_payload["shadow_readiness_md"],
        },
    }


def render_operating_brief(brief: dict[str, Any]) -> str:
    carry = brief["carry"]
    survivability = brief["survivability"]
    walk_forward = brief["walk_forward"]
    friction = brief["friction"]
    eth_cross_check = brief["eth_cross_check"]
    practical = brief.get("practical", {"decision": "unknown", "status_label": "unknown", "ok": False, "caveats": []})
    research_stack_health = brief.get("research_stack_health", {})
    contract_health = brief.get("contract_health", {})
    status_label = practical.get("status_label", practical.get("decision", "unknown"))
    unstable = ", ".join(walk_forward["unstable_parameters"] or ["none"])
    caveat_count = len(practical["caveats"])
    research_stack_line = render_research_stack_health_line(research_stack_health) if research_stack_health else "n/a"
    contract_line = render_contract_health_line(contract_health) if contract_health else "n/a"
    contract_health_operating_contract_aligned = _brief_contract_health_bool(
        brief,
        "contract_health_operating_contract_aligned",
        "operating_contract_aligned",
    )
    contract_health_paper_execution_contract_aligned = _brief_contract_health_bool(
        brief,
        "contract_health_paper_execution_contract_aligned",
        "paper_execution_contract_aligned",
        "paper_execution_contract_aligned",
    )
    contract_health_aligned = _brief_contract_health_bool(
        brief,
        "contract_health_aligned",
        "contract_health_aligned",
    )
    if not contract_health_aligned:
        contract_health_aligned = (
            contract_health_operating_contract_aligned
            and contract_health_paper_execution_contract_aligned
        )
    contract_health_contracts_are_well_partitioned = _brief_contract_health_bool(
        brief,
        "contract_health_contracts_are_well_partitioned",
        "contracts_are_well_partitioned",
    )
    return "\n".join(
        [
            "BTC 1d Operating Brief",
            f"candidate: {brief['candidate']}",
            f"scope: {brief['scope']}",
            f"shadow_decision: {brief['shadow_decision']}",
            f"operator_verdict: {brief.get('operator_verdict', 'validation_in_progress')}",
            f"deployment_monitoring_active: {brief.get('deployment_monitoring_active', False)}",
            f"practical_status: {status_label} | ok={practical['ok']} | caveats={caveat_count}",
            (
                f"carry_{carry['periods']}: {carry['decision']} | sharpe={carry['sharpe']:.4f} "
                f"| cagr={carry['cagr']:.4f} | mdd={carry['max_drawdown']:.4f}"
            ),
            (
                f"survivability_{survivability['periods']}: {survivability['decision']} "
                f"| sharpe={survivability['sharpe']:.4f} | cagr={survivability['cagr']:.4f} "
                f"| mdd={survivability['max_drawdown']:.4f}"
            ),
            (
                f"walk_forward: {'PASS' if walk_forward['passed'] else 'FAIL'} "
                f"| oos_sharpe={walk_forward['oos_sharpe']:.4f} "
                f"| oos_cagr={walk_forward['oos_cagr']:.4f} "
                f"| oos_mdd={walk_forward['oos_max_drawdown']:.4f} "
                f"| drift={walk_forward['sensitivity_max_drift']:.4f} "
                f"| unstable={unstable}"
            ),
            (
                f"friction_{friction['heaviest_level_bps']}bps: {friction['decision']} "
                f"| sharpe={friction['heaviest_level_sharpe']:.4f}"
            ),
            (
                f"eth_cross_check: {eth_cross_check['symbol']} pass_rate={eth_cross_check['pass_rate']} "
                f"({eth_cross_check['pass_count']}/{eth_cross_check['total_count']})"
            ),
            f"combined_health_line: {brief.get('combined_health_line', 'n/a')}",
            f"execution_health_line: {brief.get('execution_health_line', 'n/a')}",
            f"execution_contract_health_line: {brief.get('execution_contract_health_line', 'n/a')}",
            f"execution_contract_read: {brief.get('execution_contract_read', 'n/a')}",
            f"execution_contract_aligned: {brief.get('execution_contract_aligned', False)}",
            "execution_contract_paper_ledger_snapshot_summary_aligned: "
            f"{brief.get('execution_contract_paper_ledger_snapshot_summary_aligned', False)}",
            (
                f"attack_challenger_candidate: {brief.get('attack_challenger_candidate', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_candidate: n/a"
            ),
            (
                "attack_challenger_role_assignment: "
                f"{brief.get('attack_challenger_role_assignment', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_role_assignment: n/a"
            ),
            (
                "attack_challenger_promotion_ready: "
                f"{brief.get('attack_challenger_promotion_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_promotion_ready: False"
            ),
            (
                "attack_challenger_bridge_entry_ready: "
                f"{brief.get('attack_challenger_bridge_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_bridge_entry_ready: False"
            ),
            (
                "attack_challenger_bridge_queue_lane: "
                f"{brief.get('attack_challenger_bridge_queue_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_bridge_queue_lane: n/a"
            ),
            (
                "attack_challenger_execution_contract_entry_ready: "
                f"{brief.get('attack_challenger_execution_contract_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_execution_contract_entry_ready: False"
            ),
            (
                "attack_challenger_execution_contract_queue_lane: "
                f"{brief.get('attack_challenger_execution_contract_queue_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_execution_contract_queue_lane: n/a"
            ),
            (
                "attack_challenger_operator_stack_handoff_ready: "
                f"{brief.get('attack_challenger_operator_stack_handoff_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_operator_stack_handoff_ready: False"
            ),
            (
                "attack_challenger_operator_stack_handoff_lane: "
                f"{brief.get('attack_challenger_operator_stack_handoff_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_operator_stack_handoff_lane: n/a"
            ),
            (
                "attack_challenger_operator_runbook_candidate_entry_ready: "
                f"{brief.get('attack_challenger_operator_runbook_candidate_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_operator_runbook_candidate_entry_ready: False"
            ),
            (
                "attack_challenger_operator_runbook_candidate_entry_lane: "
                f"{brief.get('attack_challenger_operator_runbook_candidate_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_operator_runbook_candidate_entry_lane: n/a"
            ),
            (
                "attack_challenger_operator_runbook_execution_entry_ready: "
                f"{brief.get('attack_challenger_operator_runbook_execution_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_operator_runbook_execution_entry_ready: False"
            ),
            (
                "attack_challenger_operator_runbook_execution_entry_lane: "
                f"{brief.get('attack_challenger_operator_runbook_execution_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_operator_runbook_execution_entry_lane: n/a"
            ),
            (
                "attack_challenger_live_readiness_review_ready: "
                f"{brief.get('attack_challenger_live_readiness_review_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_readiness_review_ready: False"
            ),
            (
                "attack_challenger_live_readiness_review_lane: "
                f"{brief.get('attack_challenger_live_readiness_review_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_readiness_review_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_activation_review_ready: "
                f"{brief.get('attack_challenger_live_shadow_activation_review_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_activation_review_ready: False"
            ),
            (
                "attack_challenger_live_shadow_activation_review_lane: "
                f"{brief.get('attack_challenger_live_shadow_activation_review_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_activation_review_lane: n/a"
            ),
            (
                "attack_challenger_live_candidate_entry_ready: "
                f"{brief.get('attack_challenger_live_candidate_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_candidate_entry_ready: False"
            ),
            (
                "attack_challenger_live_candidate_entry_lane: "
                f"{brief.get('attack_challenger_live_candidate_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_candidate_entry_lane: n/a"
            ),
            (
                "attack_challenger_live_operator_paper_entry_ready: "
                f"{brief.get('attack_challenger_live_operator_paper_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_operator_paper_entry_ready: False"
            ),
            (
                "attack_challenger_live_operator_paper_entry_lane: "
                f"{brief.get('attack_challenger_live_operator_paper_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_operator_paper_entry_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_governance_review_ready: "
                f"{brief.get('attack_challenger_live_shadow_governance_review_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_governance_review_ready: False"
            ),
            (
                "attack_challenger_live_shadow_governance_review_lane: "
                f"{brief.get('attack_challenger_live_shadow_governance_review_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_governance_review_lane: n/a"
            ),
            (
                "attack_challenger_live_governed_shadow_entry_ready: "
                f"{brief.get('attack_challenger_live_governed_shadow_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_governed_shadow_entry_ready: False"
            ),
            (
                "attack_challenger_live_governed_shadow_entry_lane: "
                f"{brief.get('attack_challenger_live_governed_shadow_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_governed_shadow_entry_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_candidate_paper_review_ready: "
                f"{brief.get('attack_challenger_live_shadow_candidate_paper_review_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_candidate_paper_review_ready: False"
            ),
            (
                "attack_challenger_live_shadow_candidate_paper_review_lane: "
                f"{brief.get('attack_challenger_live_shadow_candidate_paper_review_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_candidate_paper_review_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_candidate_governance_lock_ready: "
                f"{brief.get('attack_challenger_live_shadow_candidate_governance_lock_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_candidate_governance_lock_ready: False"
            ),
            (
                "attack_challenger_live_shadow_candidate_governance_lock_lane: "
                f"{brief.get('attack_challenger_live_shadow_candidate_governance_lock_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_candidate_governance_lock_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_locked_entry_ready: "
                f"{brief.get('attack_challenger_live_shadow_locked_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_entry_ready: False"
            ),
            (
                "attack_challenger_live_shadow_locked_entry_lane: "
                f"{brief.get('attack_challenger_live_shadow_locked_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_entry_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_locked_candidate_review_ready: "
                f"{brief.get('attack_challenger_live_shadow_locked_candidate_review_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_candidate_review_ready: False"
            ),
            (
                "attack_challenger_live_shadow_locked_candidate_review_lane: "
                f"{brief.get('attack_challenger_live_shadow_locked_candidate_review_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_candidate_review_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_locked_candidate_release_review_ready: "
                f"{brief.get('attack_challenger_live_shadow_locked_candidate_release_review_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_candidate_release_review_ready: False"
            ),
            (
                "attack_challenger_live_shadow_locked_candidate_release_review_lane: "
                f"{brief.get('attack_challenger_live_shadow_locked_candidate_release_review_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_candidate_release_review_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_locked_release_entry_ready: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_entry_ready: False"
            ),
            (
                "attack_challenger_live_shadow_locked_release_entry_lane: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_entry_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_locked_release_candidate_review_ready: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_candidate_review_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_candidate_review_ready: False"
            ),
            (
                "attack_challenger_live_shadow_locked_release_candidate_review_lane: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_candidate_review_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_candidate_review_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_locked_release_governance_check_ready: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_governance_check_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_governance_check_ready: False"
            ),
            (
                "attack_challenger_live_shadow_locked_release_governance_check_lane: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_governance_check_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_governance_check_lane: n/a"
            ),
            (
                "attack_challenger_live_shadow_locked_release_governance_entry_ready: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_governance_entry_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_governance_entry_ready: False"
            ),
            (
                "attack_challenger_live_shadow_locked_release_governance_entry_lane: "
                f"{brief.get('attack_challenger_live_shadow_locked_release_governance_entry_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_live_shadow_locked_release_governance_entry_lane: n/a"
            ),
            (
                "attack_challenger_remote_monitoring_deployment_handoff_ready: "
                f"{brief.get('attack_challenger_remote_monitoring_deployment_handoff_ready', False)}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_remote_monitoring_deployment_handoff_ready: False"
            ),
            (
                "attack_challenger_remote_monitoring_deployment_handoff_lane: "
                f"{brief.get('attack_challenger_remote_monitoring_deployment_handoff_lane', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_remote_monitoring_deployment_handoff_lane: n/a"
            ),
            (
                "attack_challenger_next_step: "
                f"{brief.get('attack_challenger_next_step', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_next_step: n/a"
            ),
            (
                "attack_challenger_bridge_report: "
                f"{brief.get('attack_challenger_bridge_report', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_bridge_report: n/a"
            ),
            (
                "attack_challenger_profile: "
                f"cagr={brief.get('attack_challenger_paper_validation_cagr')} | "
                f"mdd={brief.get('attack_challenger_paper_validation_max_drawdown')} | "
                f"drift={brief.get('attack_challenger_walk_forward_sensitivity_max_drift')} | "
                f"friction={brief.get('attack_challenger_friction_final_decision', '')}"
                if brief.get("attack_challenger_candidate")
                else "attack_challenger_profile: n/a"
            ),
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_checked_aligned_entry_aligned', False)}",
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_aligned_aligned_entry_aligned', False)}",
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned', False)}",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}",
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_checked_aligned_summary_aligned', False)}",
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_aligned_aligned_summary_aligned', False)}",
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned', False)}",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"{brief.get('execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}",
            f"paper_execution_contract_checked: {brief.get('paper_execution_contract_checked', False)}",
            f"paper_execution_contract_aligned: {brief.get('paper_execution_contract_aligned', False)}",
            "paper_execution_contract_checked_aligned: "
            f"{brief.get('paper_execution_contract_checked_aligned', False)}",
            "paper_execution_contract_aligned_aligned: "
            f"{brief.get('paper_execution_contract_aligned_aligned', False)}",
            "paper_execution_contract_checked_summary_aligned: "
            f"{brief.get('paper_execution_contract_checked_summary_aligned', False)}",
            "paper_execution_contract_aligned_summary_aligned: "
            f"{brief.get('paper_execution_contract_aligned_summary_aligned', False)}",
            "paper_execution_contract_checked_aligned_entry_aligned: "
            f"{brief.get('paper_execution_contract_checked_aligned_entry_aligned', False)}",
            "paper_execution_contract_aligned_aligned_entry_aligned: "
            f"{brief.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}",
            "paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"{brief.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}",
            "paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"{brief.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}",
            "paper_execution_contract_checked_aligned_summary_aligned: "
            f"{brief.get('paper_execution_contract_checked_aligned_summary_aligned', False)}",
            "paper_execution_contract_aligned_aligned_summary_aligned: "
            f"{brief.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}",
            "paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"{brief.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}",
            "paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"{brief.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}",
            f"research_stack_status: {research_stack_line}",
            f"contract_health_line: {contract_line}",
            "contract_health_operating_contract_aligned: "
            f"{contract_health_operating_contract_aligned}",
            "contract_health_paper_execution_contract_aligned: "
            f"{contract_health_paper_execution_contract_aligned}",
            "contract_health_aligned: "
            f"{contract_health_aligned}",
            "contract_health_contracts_are_well_partitioned: "
            f"{contract_health_contracts_are_well_partitioned}",
            f"paper_nightly_health_line: {brief.get('paper_nightly_health_line', 'n/a')}",
            f"paper_execution_read: {brief.get('paper_execution_read', 'n/a')}",
            f"paper_exit_duplicate_run: {brief.get('paper_exit_duplicate_run', False)}",
            f"paper_ledger_consistent: {brief.get('paper_ledger_consistent', False)}",
            f"paper_ledger_snapshot: {brief.get('paper_ledger_snapshot_read', _render_paper_ledger_snapshot_read(brief.get('paper_ledger_snapshot')))}",
            f"practical_gate: {brief['paths'].get('practical_promotion_gate_md', 'analysis_results\\\\btc_1d_practical_promotion_gate_md_latest.md')}",
            f"research_stack: {brief['paths'].get('research_stack_operating_brief_md', 'analysis_results\\\\btc_1d_research_stack_operating_brief_md_latest.md')}",
            f"quick_read_contract: {brief['paths'].get('quick_read_contract_screen_md', 'analysis_results\\\\btc_1d_quick_read_contract_screen_md_latest.md')}",
            f"execution_contract: {brief['paths'].get('execution_contract_screen_md', 'analysis_results\\\\btc_1d_execution_contract_screen_md_latest.md')}",
            f"execution_contract_test_index: {brief['paths'].get('execution_meta_contract_test_index_md', 'analysis_results\\\\btc_1d_execution_meta_contract_test_index_md_latest.md')}",
            f"meta_contract: {brief['paths'].get('meta_contract_screen_md', 'analysis_results\\\\btc_1d_meta_contract_screen_md_latest.md')}",
            f"paper_nightly: {brief['paths'].get('paper_nightly_summary_md', 'analysis_results\\\\btc_1d_paper_nightly_summary_md_latest.md')}",
            f"open_first: {brief['paths']['operating_index_md']}",
        ]
    )


def render_operating_brief_markdown(brief: dict[str, Any]) -> str:
    carry = brief["carry"]
    survivability = brief["survivability"]
    walk_forward = brief["walk_forward"]
    friction = brief["friction"]
    eth_cross_check = brief["eth_cross_check"]
    practical = brief.get("practical", {"decision": "unknown", "status_label": "unknown", "ok": False, "caveats": []})
    research_stack_health = brief.get("research_stack_health", {})
    contract_health = brief.get("contract_health", {})
    status_label = practical.get("status_label", practical.get("decision", "unknown"))
    unstable = ", ".join(walk_forward["unstable_parameters"] or ["none"])
    research_stack_line = render_research_stack_health_line(research_stack_health) if research_stack_health else "n/a"
    contract_line = render_contract_health_line(contract_health) if contract_health else "n/a"
    contract_health_operating_contract_aligned = _brief_contract_health_bool(
        brief,
        "contract_health_operating_contract_aligned",
        "operating_contract_aligned",
    )
    contract_health_paper_execution_contract_aligned = _brief_contract_health_bool(
        brief,
        "contract_health_paper_execution_contract_aligned",
        "paper_execution_contract_aligned",
        "paper_execution_contract_aligned",
    )
    contract_health_aligned = _brief_contract_health_bool(
        brief,
        "contract_health_aligned",
        "contract_health_aligned",
    )
    if not contract_health_aligned:
        contract_health_aligned = (
            contract_health_operating_contract_aligned
            and contract_health_paper_execution_contract_aligned
        )
    contract_health_contracts_are_well_partitioned = _brief_contract_health_bool(
        brief,
        "contract_health_contracts_are_well_partitioned",
        "contracts_are_well_partitioned",
    )
    return "\n".join(
            [
                "# BTC 1d Operating Brief",
                "",
                f"- Candidate: `{brief['candidate']}`",
                f"- Scope: `{brief['scope']}`",
                f"- Shadow decision: `{brief['shadow_decision']}`",
                f"- Operator verdict: `{brief.get('operator_verdict', 'validation_in_progress')}`",
                f"- Deployment monitoring active: `{brief.get('deployment_monitoring_active', False)}`",
                (
                    f"- Attack challenger: `{brief.get('attack_challenger_candidate', '')}` | "
                    f"role `{brief.get('attack_challenger_role_assignment', '')}` | "
                    f"promotion_ready `{brief.get('attack_challenger_promotion_ready', False)}` | "
                    f"bridge_entry_ready `{brief.get('attack_challenger_bridge_entry_ready', False)}` | "
                    f"queue `{brief.get('attack_challenger_bridge_queue_lane', '')}` | "
                    f"contract_entry_ready `{brief.get('attack_challenger_execution_contract_entry_ready', False)}` | "
                    f"contract_queue `{brief.get('attack_challenger_execution_contract_queue_lane', '')}` | "
                    f"handoff_ready `{brief.get('attack_challenger_operator_stack_handoff_ready', False)}` | "
                    f"handoff_lane `{brief.get('attack_challenger_operator_stack_handoff_lane', '')}` | "
                    f"runbook_entry_ready `{brief.get('attack_challenger_operator_runbook_candidate_entry_ready', False)}` | "
                    f"runbook_lane `{brief.get('attack_challenger_operator_runbook_candidate_entry_lane', '')}` | "
                    f"runbook_execution_ready `{brief.get('attack_challenger_operator_runbook_execution_entry_ready', False)}` | "
                    f"runbook_execution_lane `{brief.get('attack_challenger_operator_runbook_execution_entry_lane', '')}` | "
                    f"live_readiness_ready `{brief.get('attack_challenger_live_readiness_review_ready', False)}` | "
                    f"live_readiness_lane `{brief.get('attack_challenger_live_readiness_review_lane', '')}` | "
                    f"live_shadow_activation_ready `{brief.get('attack_challenger_live_shadow_activation_review_ready', False)}` | "
                    f"live_shadow_activation_lane `{brief.get('attack_challenger_live_shadow_activation_review_lane', '')}` | "
                    f"live_candidate_ready `{brief.get('attack_challenger_live_candidate_entry_ready', False)}` | "
                    f"live_candidate_lane `{brief.get('attack_challenger_live_candidate_entry_lane', '')}` | "
                    f"live_operator_paper_ready `{brief.get('attack_challenger_live_operator_paper_entry_ready', False)}` | "
                    f"live_operator_paper_lane `{brief.get('attack_challenger_live_operator_paper_entry_lane', '')}` | "
                    f"live_shadow_governance_ready `{brief.get('attack_challenger_live_shadow_governance_review_ready', False)}` | "
                    f"live_shadow_governance_lane `{brief.get('attack_challenger_live_shadow_governance_review_lane', '')}` | "
                    f"live_governed_shadow_ready `{brief.get('attack_challenger_live_governed_shadow_entry_ready', False)}` | "
                    f"live_governed_shadow_lane `{brief.get('attack_challenger_live_governed_shadow_entry_lane', '')}` | "
                    f"live_shadow_candidate_paper_ready `{brief.get('attack_challenger_live_shadow_candidate_paper_review_ready', False)}` | "
                    f"live_shadow_candidate_paper_lane `{brief.get('attack_challenger_live_shadow_candidate_paper_review_lane', '')}` | "
                    f"live_shadow_candidate_governance_lock_ready `{brief.get('attack_challenger_live_shadow_candidate_governance_lock_ready', False)}` | "
                    f"live_shadow_candidate_governance_lock_lane `{brief.get('attack_challenger_live_shadow_candidate_governance_lock_lane', '')}` | "
                    f"live_shadow_locked_entry_ready `{brief.get('attack_challenger_live_shadow_locked_entry_ready', False)}` | "
                    f"live_shadow_locked_entry_lane `{brief.get('attack_challenger_live_shadow_locked_entry_lane', '')}` | "
                    f"live_shadow_locked_candidate_review_ready `{brief.get('attack_challenger_live_shadow_locked_candidate_review_ready', False)}` | "
                    f"live_shadow_locked_candidate_review_lane `{brief.get('attack_challenger_live_shadow_locked_candidate_review_lane', '')}` | "
                    f"live_shadow_locked_candidate_release_review_ready `{brief.get('attack_challenger_live_shadow_locked_candidate_release_review_ready', False)}` | "
                    f"live_shadow_locked_candidate_release_review_lane `{brief.get('attack_challenger_live_shadow_locked_candidate_release_review_lane', '')}` | "
                    f"live_shadow_locked_release_entry_ready `{brief.get('attack_challenger_live_shadow_locked_release_entry_ready', False)}` | "
                    f"live_shadow_locked_release_entry_lane `{brief.get('attack_challenger_live_shadow_locked_release_entry_lane', '')}` | "
                    f"live_shadow_locked_release_candidate_review_ready `{brief.get('attack_challenger_live_shadow_locked_release_candidate_review_ready', False)}` | "
                    f"live_shadow_locked_release_candidate_review_lane `{brief.get('attack_challenger_live_shadow_locked_release_candidate_review_lane', '')}` | "
                    f"live_shadow_locked_release_governance_check_ready `{brief.get('attack_challenger_live_shadow_locked_release_governance_check_ready', False)}` | "
                    f"live_shadow_locked_release_governance_check_lane `{brief.get('attack_challenger_live_shadow_locked_release_governance_check_lane', '')}` | "
                    f"live_shadow_locked_release_governance_entry_ready `{brief.get('attack_challenger_live_shadow_locked_release_governance_entry_ready', False)}` | "
                    f"live_shadow_locked_release_governance_entry_lane `{brief.get('attack_challenger_live_shadow_locked_release_governance_entry_lane', '')}` | "
                    f"remote_monitoring_deployment_handoff_ready `{brief.get('attack_challenger_remote_monitoring_deployment_handoff_ready', False)}` | "
                    f"remote_monitoring_deployment_handoff_lane `{brief.get('attack_challenger_remote_monitoring_deployment_handoff_lane', '')}` | "
                    f"next `{brief.get('attack_challenger_next_step', '')}`"
                    if brief.get("attack_challenger_candidate")
                    else ""
                ),
                (
                    "- Attack challenger profile: "
                    f"`cagr={brief.get('attack_challenger_paper_validation_cagr')} | "
                    f"mdd={brief.get('attack_challenger_paper_validation_max_drawdown')} | "
                    f"drift={brief.get('attack_challenger_walk_forward_sensitivity_max_drift')} | "
                    f"friction={brief.get('attack_challenger_friction_final_decision', '')}`"
                    if brief.get("attack_challenger_candidate")
                    else ""
                ),
                (
                    "- Attack challenger next step: "
                    f"`{brief.get('attack_challenger_next_step', '')}`"
                    if brief.get("attack_challenger_candidate")
                    else ""
                ),
                (
                    "- Attack challenger bridge report: "
                    f"`{brief.get('attack_challenger_bridge_report', '')}`"
                    if brief.get("attack_challenger_candidate")
                    else ""
                ),
                "",
                "## Standard Check Order",
                "1. Practical",
                "2. Research",
                "3. Contract",
                "4. Brief",
                "- Regression lock: `tests/unit/test_btc_1d_operating_cli_help_contract.py`",
                "",
                "## Quick Read",
                (
                    f"- Execution health: `{brief.get('execution_health_line')}`"
                    if brief.get("execution_health_line")
                    else ""
                ),
                (
                    f"- Execution contract health: `{brief.get('execution_contract_health_line')}`"
                    if brief.get("execution_contract_health_line")
                    else ""
                ),
                (
                    f"- Execution contract read: `{brief.get('execution_contract_read')}`"
                    if brief.get("execution_contract_read")
                    else ""
                ),
                f"- Execution contract aligned: `{brief.get('execution_contract_aligned', False)}`",
                (
                    "- Execution contract paper ledger snapshot summary aligned: "
                    f"`{brief.get('execution_contract_paper_ledger_snapshot_summary_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract checked aligned entry aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_checked_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract aligned aligned entry aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract checked summary aligned entry aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract aligned summary aligned entry aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract checked aligned summary aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_checked_aligned_summary_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract aligned aligned summary aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract checked summary aligned summary aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
                ),
                (
                    "- Execution contract paper execution contract aligned summary aligned summary aligned: "
                    f"`{brief.get('execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
                ),
                f"- Paper execution contract checked: `{brief.get('paper_execution_contract_checked', False)}`",
                f"- Paper execution contract aligned: `{brief.get('paper_execution_contract_aligned', False)}`",
                (
                    "- Paper execution contract checked aligned: "
                    f"`{brief.get('paper_execution_contract_checked_aligned', False)}`"
                ),
                (
                    "- Paper execution contract aligned aligned: "
                    f"`{brief.get('paper_execution_contract_aligned_aligned', False)}`"
                ),
                (
                    "- Paper execution contract checked summary aligned: "
                    f"`{brief.get('paper_execution_contract_checked_summary_aligned', False)}`"
                ),
                (
                    "- Paper execution contract aligned summary aligned: "
                    f"`{brief.get('paper_execution_contract_aligned_summary_aligned', False)}`"
                ),
                (
                    "- Paper execution contract checked aligned entry aligned: "
                    f"`{brief.get('paper_execution_contract_checked_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Paper execution contract aligned aligned entry aligned: "
                    f"`{brief.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Paper execution contract checked summary aligned entry aligned: "
                    f"`{brief.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Paper execution contract aligned summary aligned entry aligned: "
                    f"`{brief.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
                ),
                (
                    "- Paper execution contract checked aligned summary aligned: "
                    f"`{brief.get('paper_execution_contract_checked_aligned_summary_aligned', False)}`"
                ),
                (
                    "- Paper execution contract aligned aligned summary aligned: "
                    f"`{brief.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
                ),
                (
                    "- Paper execution contract checked summary aligned summary aligned: "
                    f"`{brief.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
                ),
                (
                    "- Paper execution contract aligned summary aligned summary aligned: "
                    f"`{brief.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
                ),
                f"- Practical status: `{status_label}` | ok `{practical['ok']}` | caveats `{len(practical['caveats'])}`",
                f"- Combined health: `{brief.get('combined_health_line', 'n/a')}`",
                f"- Research stack status: `{research_stack_line}`",
                f"- Contract health: `{contract_line}`",
                (
                    "- Contract health operating aligned: "
                    f"`{contract_health_operating_contract_aligned}`"
                ),
                (
                    "- Contract health paper execution aligned: "
                    f"`{contract_health_paper_execution_contract_aligned}`"
                ),
                (
                    "- Contract health aligned: "
                    f"`{contract_health_aligned}`"
                ),
                (
                    "- Contract health partitioned: "
                    f"`{contract_health_contracts_are_well_partitioned}`"
                ),
                (
                    f"- Paper nightly: `{brief.get('paper_nightly_health_line')}`"
                    if brief.get("paper_nightly_health_line")
                    else ""
                ),
                f"- Paper exit duplicate run: `{brief.get('paper_exit_duplicate_run', False)}`",
                f"- Paper ledger consistent: `{brief.get('paper_ledger_consistent', False)}`",
                f"- Paper ledger snapshot: `{brief.get('paper_ledger_snapshot_read', _render_paper_ledger_snapshot_read(brief.get('paper_ledger_snapshot')))}`",
            "",
            "## Quick-Read Contract",
            f"- `{brief['paths'].get('quick_read_contract_screen_md', 'analysis_results\\\\btc_1d_quick_read_contract_screen_md_latest.md')}`",
            f"- `{brief['paths'].get('execution_contract_screen_md', 'analysis_results\\\\btc_1d_execution_contract_screen_md_latest.md')}`",
            f"- `{brief['paths'].get('execution_meta_contract_test_index_md', 'analysis_results\\\\btc_1d_execution_meta_contract_test_index_md_latest.md')}`",
            f"- `{brief['paths'].get('meta_contract_screen_md', 'analysis_results\\\\btc_1d_meta_contract_screen_md_latest.md')}`",
            "",
            "## Paper Nightly",
            f"- `{brief['paths'].get('paper_nightly_summary_md', 'analysis_results\\\\btc_1d_paper_nightly_summary_md_latest.md')}`",
            "",
            "## Open First",
            f"- `{brief['paths']['operating_index_md']}`",
            "",
            "## Carry",
            (
                f"- `{carry['periods']}`: `{carry['decision']}` | Sharpe `{carry['sharpe']:.4f}` "
                f"| CAGR `{carry['cagr']:.4f}` | MDD `{carry['max_drawdown']:.4f}`"
            ),
            "",
            "## Survivability",
            (
                f"- `{survivability['periods']}`: `{survivability['decision']}` | Sharpe `{survivability['sharpe']:.4f}` "
                f"| CAGR `{survivability['cagr']:.4f}` | MDD `{survivability['max_drawdown']:.4f}`"
            ),
            "",
            "## Walk-Forward",
            (
                f"- `{'PASS' if walk_forward['passed'] else 'FAIL'}` | OOS Sharpe `{walk_forward['oos_sharpe']:.4f}` "
                f"| OOS CAGR `{walk_forward['oos_cagr']:.4f}` | OOS MDD `{walk_forward['oos_max_drawdown']:.4f}`"
            ),
            f"- Drift `{walk_forward['sensitivity_max_drift']:.4f}` | unstable `{unstable}`",
            "",
            "## Friction",
            (
                f"- `{friction['heaviest_level_bps']}bps`: `{friction['decision']}` "
                f"| Sharpe `{friction['heaviest_level_sharpe']:.4f}`"
            ),
            "",
            "## ETH Cross-Check",
            (
                f"- `{eth_cross_check['symbol']}` pass rate `{eth_cross_check['pass_rate']}` "
                f"({eth_cross_check['pass_count']}/{eth_cross_check['total_count']})"
            ),
            "",
            "## Practical Gate",
            f"- `{brief['paths'].get('practical_promotion_gate_md', 'analysis_results\\\\btc_1d_practical_promotion_gate_md_latest.md')}`",
            "",
            "## Research Stack",
            f"- `{brief['paths'].get('research_stack_operating_brief_md', 'analysis_results\\\\btc_1d_research_stack_operating_brief_md_latest.md')}`",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    brief = build_operating_brief(analysis_dir=args.analysis_dir)
    if args.as_json:
        print(json.dumps(brief, indent=2))
    else:
        print(render_operating_brief(brief))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
