from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_promoted_candidate_regression import (
    Btc1dPromotedCandidateRegressionConfig,
    Btc1dPromotedCandidateRegressionService,
)
from scripts.check_btc_1d_practical_health import (
    check_practical_health,
    render_practical_health_line,
)
from scripts.check_btc_1d_contract_health import (
    check_contract_health,
    render_contract_health_line,
)
from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME,
    build_attack_challenger_remote_monitoring_deployment_handoff_path,
)
from scripts.check_btc_1d_research_stack_health import (
    check_research_stack_health,
    render_research_stack_health_line,
)
from scripts.check_btc_1d_practical_promotion_gate import main as run_practical_promotion_gate_main
import scripts.compare_btc_1d_execution_contract_screen as execution_contract_screen_script
import scripts.compare_btc_1d_execution_meta_contract_test_index as execution_meta_contract_test_index_script
import scripts.compare_btc_1d_meta_contract_screen as meta_contract_screen_script
import scripts.compare_btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review as live_shadow_locked_release_candidate_review_script
import scripts.compare_btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry as live_shadow_locked_release_entry_script
import scripts.compare_btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_check as live_shadow_locked_release_governance_check_script
import scripts.compare_btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry as live_shadow_locked_release_governance_entry_script
import scripts.compare_btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff as remote_monitoring_deployment_handoff_script
import scripts.compare_btc_1d_quick_read_contract_screen as quick_read_contract_screen_script
import scripts.compare_btc_1d_research_stack_operating_brief as research_stack_operating_brief_script
import scripts.build_btc_1d_operator_dashboard as operator_dashboard_script
from scripts.compare_btc_1d_execution_contract_screen import (
    render_execution_contract_health_line,
    render_execution_contract_read,
)
from scripts.print_btc_1d_operating_brief import (
    build_operating_brief,
    render_operating_brief,
    render_operating_brief_markdown,
)
from scripts.build_btc_1d_shadow_packet import write_shadow_packet
from scripts.run_bithumb_paper_nightly import run_nightly_paper, render_paper_nightly_health_line
from scripts.publish_btc_1d_practical_scorecard import main as run_practical_scorecard_main
from scripts.publish_btc_1d_operating_snapshot import publish_operating_snapshot
from scripts.run_btc_1d_walk_forward_low_vol_cap_candidate import parse_args as parse_walk_forward_args
from scripts.validate_btc_1d_low_vol_cap_friction import main as run_friction_main
from scripts.validate_btc_1d_low_vol_cap_candidate import parse_args as parse_validation_args
from app.domains.experiments.btc_1d_walk_forward_diagnostic import Btc1dWalkForwardDiagnosticService
from app.domains.experiments.btc_paper_validation import BtcPaperValidationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the BTC 1d shadow update: paper-validation then shadow packet export. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--survivability-periods", type=int, default=2600)
    parser.add_argument("--friction-periods", type=int, default=2200)
    parser.add_argument("--walk-forward-periods", type=int, default=2200)
    parser.add_argument("--eth-symbol", default="ETHUSDT")
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    parser.add_argument("--refresh-only", action="store_true")
    parser.add_argument("--sync-passes", type=int, default=3)
    parser.add_argument("--emit-paper-nightly", action="store_true")
    parser.add_argument("--paper-logs-dir", type=Path, default=Path("logs"))
    parser.add_argument("--paper-run-id", default=None)
    parser.add_argument("--paper-ledger-json", type=Path, default=Path("artifacts/paper_execution/bithumb_paper_ledger.json"))
    parser.add_argument("--paper-output-dir", type=Path, default=Path("artifacts/paper_execution"))
    parser.add_argument("--paper-exit-json", type=Path, default=None)
    parser.add_argument("--paper-notional-krw", type=float, default=100000.0)
    parser.add_argument("--paper-max-orders", type=int, default=1)
    parser.add_argument("--paper-track", choices=["operating", "attack"], default="operating")
    return parser


def _run_validation(
    *,
    analysis_dir: Path,
    periods: int,
    fee_bps: float,
    slippage_bps: float,
    allow_synthetic_ohlcv_fallback: bool,
) -> dict:
    validation_cfg = parse_validation_args(
        [
            "--periods",
            str(periods),
            "--fee-bps",
            str(fee_bps),
            "--slippage-bps",
            str(slippage_bps),
            *(["--allow-synthetic-ohlcv-fallback"] if allow_synthetic_ohlcv_fallback else []),
        ]
    )
    return BtcPaperValidationService(analysis_results_dir=analysis_dir).run_validation(validation_cfg)


def _run_promoted_regression(
    *,
    analysis_dir: Path,
    symbol: str,
    allow_synthetic_ohlcv_fallback: bool,
) -> dict:
    config = Btc1dPromotedCandidateRegressionConfig(
        symbol=symbol,
        allow_synthetic_ohlcv_fallback=allow_synthetic_ohlcv_fallback,
    )
    return Btc1dPromotedCandidateRegressionService(analysis_results_dir=analysis_dir).run_batch(config)


def _run_walk_forward(
    *,
    periods: int,
    allow_synthetic_ohlcv_fallback: bool,
) -> dict:
    config = parse_walk_forward_args(
        [
            "--periods",
            str(periods),
            *(["--allow-synthetic-ohlcv-fallback"] if allow_synthetic_ohlcv_fallback else []),
        ]
    )
    return Btc1dWalkForwardDiagnosticService().run_diagnostic(config)


def _paper_summary_contract_bool(summary: dict, field: str, legacy_field: str) -> bool:
    return bool(summary.get(field, summary.get(legacy_field, False)))


def _resolve_latest_json_artifact(analysis_dir: Path, stem: str) -> Path | None:
    latest_path = analysis_dir / f"{stem}_latest.json"
    if latest_path.exists():
        return latest_path
    candidates = sorted(analysis_dir.glob(f"{stem}_*.json"))
    if not candidates:
        return None
    return candidates[-1]


def _load_attack_challenger_state(*, analysis_dir: Path) -> dict[str, object]:
    remote_monitoring_deployment_handoff_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff",
    )
    if remote_monitoring_deployment_handoff_path is not None:
        payload = json.loads(
            remote_monitoring_deployment_handoff_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("remote_monitoring_deployment_handoff_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("remote_monitoring_deployment_handoff_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        handoff_ready = bool(
            verdict.get("remote_monitoring_deployment_handoff_ready", False)
        )
        governance_entry_ready = bool(
            requirements.get(
                "challenger_live_shadow_locked_release_governance_entry_ready", False
            )
        )
        if handoff_ready:
            return {
                "attack_challenger_candidate": str(
                    context.get("attack_challenger_candidate", profile.get("label", ""))
                ),
                "attack_challenger_role_assignment": "attack_challenger_candidate",
                "attack_challenger_promotion_ready": bool(
                    requirements.get("promotion_chain_still_green", False)
                ),
                "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
                "attack_challenger_paper_validation_cagr": profile.get("paper_validation_cagr"),
                "attack_challenger_paper_validation_max_drawdown": profile.get("paper_validation_max_drawdown"),
                "attack_challenger_walk_forward_sensitivity_max_drift": profile.get("walk_forward_sensitivity_max_drift"),
                "attack_challenger_friction_final_decision": str(profile.get("friction_final_decision", "")),
                "attack_challenger_bridge_entry_ready": governance_entry_ready,
                "attack_challenger_bridge_queue_lane": "attack_challenger_queue" if governance_entry_ready else "bridge_repair_hold",
                "attack_challenger_execution_contract_entry_ready": governance_entry_ready,
                "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue" if governance_entry_ready else "execution_contract_entry_repair_hold",
                "attack_challenger_operator_stack_handoff_ready": governance_entry_ready,
                "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue" if governance_entry_ready else "operator_stack_repair_hold",
                "attack_challenger_operator_runbook_candidate_entry_ready": governance_entry_ready,
                "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue" if governance_entry_ready else "operator_runbook_candidate_repair_hold",
                "attack_challenger_operator_runbook_execution_entry_ready": governance_entry_ready,
                "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue" if governance_entry_ready else "operator_runbook_execution_repair_hold",
                "attack_challenger_live_readiness_review_ready": governance_entry_ready,
                "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue" if governance_entry_ready else "challenger_live_readiness_review_repair_hold",
                "attack_challenger_live_shadow_activation_review_ready": governance_entry_ready,
                "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue" if governance_entry_ready else "challenger_live_shadow_activation_repair_hold",
                "attack_challenger_live_candidate_entry_ready": governance_entry_ready,
                "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue" if governance_entry_ready else "challenger_live_candidate_repair_hold",
                "attack_challenger_live_operator_paper_entry_ready": governance_entry_ready,
                "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue" if governance_entry_ready else "challenger_live_operator_paper_repair_hold",
                "attack_challenger_live_shadow_governance_review_ready": governance_entry_ready,
                "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue" if governance_entry_ready else "challenger_live_shadow_governance_repair_hold",
                "attack_challenger_live_governed_shadow_entry_ready": governance_entry_ready,
                "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue" if governance_entry_ready else "challenger_live_governed_shadow_repair_hold",
                "attack_challenger_live_shadow_candidate_paper_review_ready": governance_entry_ready,
                "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue" if governance_entry_ready else "challenger_live_shadow_candidate_paper_repair_hold",
                "attack_challenger_live_shadow_candidate_governance_lock_ready": governance_entry_ready,
                "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue" if governance_entry_ready else "challenger_live_shadow_candidate_governance_lock_repair_hold",
                "attack_challenger_live_shadow_locked_entry_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue" if governance_entry_ready else "",
                "attack_challenger_live_shadow_locked_candidate_review_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue" if governance_entry_ready else "",
                "attack_challenger_live_shadow_locked_candidate_release_review_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue" if governance_entry_ready else "",
                "attack_challenger_live_shadow_locked_release_entry_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue" if governance_entry_ready else "",
                "attack_challenger_live_shadow_locked_release_candidate_review_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_release_candidate_review_lane": "challenger_live_shadow_locked_release_candidate_review_queue" if governance_entry_ready else "",
                "attack_challenger_live_shadow_locked_release_governance_check_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_release_governance_check_lane": "challenger_live_shadow_locked_release_governance_check_queue" if governance_entry_ready else "",
                "attack_challenger_live_shadow_locked_release_governance_entry_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_release_governance_entry_lane": "challenger_live_shadow_locked_release_governance_entry_queue" if governance_entry_ready else "",
                "attack_challenger_remote_monitoring_deployment_handoff_ready": handoff_ready,
                "attack_challenger_remote_monitoring_deployment_handoff_lane": str(
                    verdict.get("remote_monitoring_deployment_handoff_lane", "")
                ),
                "attack_challenger_bridge_report": str(
                    remote_monitoring_deployment_handoff_path
                ),
            }

    live_shadow_locked_release_governance_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry",
    )
    if live_shadow_locked_release_governance_entry_path is not None:
        payload = json.loads(
            live_shadow_locked_release_governance_entry_path.read_text(
                encoding="utf-8-sig"
            )
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get(
                "challenger_live_shadow_locked_release_governance_entry_verdict", {}
            )
            or {}
        )
        requirements = dict(
            payload.get(
                "challenger_live_shadow_locked_release_governance_entry_requirements",
                {},
            )
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        governance_entry_ready = bool(
            verdict.get(
                "challenger_live_shadow_locked_release_governance_entry_ready", False
            )
        )
        governance_check_ready = bool(
            requirements.get(
                "challenger_live_shadow_locked_release_governance_check_ready", False
            )
        )
        if governance_entry_ready:
            return {
                "attack_challenger_candidate": str(
                    context.get("attack_challenger_candidate", profile.get("label", ""))
                ),
                "attack_challenger_role_assignment": "attack_challenger_candidate",
                "attack_challenger_promotion_ready": bool(
                    requirements.get("promotion_chain_still_green", False)
                ),
                "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
                "attack_challenger_paper_validation_cagr": profile.get("paper_validation_cagr"),
                "attack_challenger_paper_validation_max_drawdown": profile.get("paper_validation_max_drawdown"),
                "attack_challenger_walk_forward_sensitivity_max_drift": profile.get("walk_forward_sensitivity_max_drift"),
                "attack_challenger_friction_final_decision": str(profile.get("friction_final_decision", "")),
                "attack_challenger_bridge_entry_ready": governance_check_ready,
                "attack_challenger_bridge_queue_lane": "attack_challenger_queue" if governance_check_ready else "bridge_repair_hold",
                "attack_challenger_execution_contract_entry_ready": governance_check_ready,
                "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue" if governance_check_ready else "execution_contract_entry_repair_hold",
                "attack_challenger_operator_stack_handoff_ready": governance_check_ready,
                "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue" if governance_check_ready else "operator_stack_repair_hold",
                "attack_challenger_operator_runbook_candidate_entry_ready": governance_check_ready,
                "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue" if governance_check_ready else "operator_runbook_candidate_repair_hold",
                "attack_challenger_operator_runbook_execution_entry_ready": governance_check_ready,
                "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue" if governance_check_ready else "operator_runbook_execution_repair_hold",
                "attack_challenger_live_readiness_review_ready": governance_check_ready,
                "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue" if governance_check_ready else "challenger_live_readiness_review_repair_hold",
                "attack_challenger_live_shadow_activation_review_ready": governance_check_ready,
                "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue" if governance_check_ready else "challenger_live_shadow_activation_repair_hold",
                "attack_challenger_live_candidate_entry_ready": governance_check_ready,
                "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue" if governance_check_ready else "challenger_live_candidate_repair_hold",
                "attack_challenger_live_operator_paper_entry_ready": governance_check_ready,
                "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue" if governance_check_ready else "challenger_live_operator_paper_repair_hold",
                "attack_challenger_live_shadow_governance_review_ready": governance_check_ready,
                "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue" if governance_check_ready else "challenger_live_shadow_governance_repair_hold",
                "attack_challenger_live_governed_shadow_entry_ready": governance_check_ready,
                "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue" if governance_check_ready else "challenger_live_governed_shadow_repair_hold",
                "attack_challenger_live_shadow_candidate_paper_review_ready": governance_check_ready,
                "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue" if governance_check_ready else "challenger_live_shadow_candidate_paper_repair_hold",
                "attack_challenger_live_shadow_candidate_governance_lock_ready": governance_check_ready,
                "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue" if governance_check_ready else "challenger_live_shadow_candidate_governance_lock_repair_hold",
                "attack_challenger_live_shadow_locked_entry_ready": governance_check_ready,
                "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue" if governance_check_ready else "",
                "attack_challenger_live_shadow_locked_candidate_review_ready": governance_check_ready,
                "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue" if governance_check_ready else "",
                "attack_challenger_live_shadow_locked_candidate_release_review_ready": governance_check_ready,
                "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue" if governance_check_ready else "",
                "attack_challenger_live_shadow_locked_release_entry_ready": governance_check_ready,
                "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue" if governance_check_ready else "",
                "attack_challenger_live_shadow_locked_release_candidate_review_ready": governance_check_ready,
                "attack_challenger_live_shadow_locked_release_candidate_review_lane": "challenger_live_shadow_locked_release_candidate_review_queue" if governance_check_ready else "",
                "attack_challenger_live_shadow_locked_release_governance_check_ready": governance_check_ready,
                "attack_challenger_live_shadow_locked_release_governance_check_lane": "challenger_live_shadow_locked_release_governance_check_queue" if governance_check_ready else "",
                "attack_challenger_live_shadow_locked_release_governance_entry_ready": governance_entry_ready,
                "attack_challenger_live_shadow_locked_release_governance_entry_lane": str(
                    verdict.get(
                        "challenger_live_shadow_locked_release_governance_entry_lane",
                        "",
                    )
                ),
                "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
                "attack_challenger_remote_monitoring_deployment_handoff_lane": "",
                "attack_challenger_bridge_report": str(
                    live_shadow_locked_release_governance_entry_path
                ),
            }

    live_shadow_locked_release_governance_check_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_check",
    )
    if live_shadow_locked_release_governance_check_path is not None:
        payload = json.loads(
            live_shadow_locked_release_governance_check_path.read_text(
                encoding="utf-8-sig"
            )
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get(
                "challenger_live_shadow_locked_release_governance_check_verdict", {}
            )
            or {}
        )
        requirements = dict(
            payload.get(
                "challenger_live_shadow_locked_release_governance_check_requirements",
                {},
            )
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        governance_check_ready = bool(
            verdict.get(
                "challenger_live_shadow_locked_release_governance_check_ready", False
            )
        )
        release_candidate_review_ready = bool(
            requirements.get(
                "challenger_live_shadow_locked_release_candidate_review_ready", False
            )
        )
        if governance_check_ready:
            return {
                "attack_challenger_candidate": str(
                    context.get("attack_challenger_candidate", profile.get("label", ""))
                ),
                "attack_challenger_role_assignment": "attack_challenger_candidate",
                "attack_challenger_promotion_ready": bool(
                    requirements.get("promotion_chain_still_green", False)
                ),
                "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
                "attack_challenger_paper_validation_cagr": profile.get("paper_validation_cagr"),
                "attack_challenger_paper_validation_max_drawdown": profile.get("paper_validation_max_drawdown"),
                "attack_challenger_walk_forward_sensitivity_max_drift": profile.get("walk_forward_sensitivity_max_drift"),
                "attack_challenger_friction_final_decision": str(profile.get("friction_final_decision", "")),
                "attack_challenger_bridge_entry_ready": release_candidate_review_ready,
                "attack_challenger_bridge_queue_lane": "attack_challenger_queue" if release_candidate_review_ready else "bridge_repair_hold",
                "attack_challenger_execution_contract_entry_ready": release_candidate_review_ready,
                "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue" if release_candidate_review_ready else "execution_contract_entry_repair_hold",
                "attack_challenger_operator_stack_handoff_ready": release_candidate_review_ready,
                "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue" if release_candidate_review_ready else "operator_stack_repair_hold",
                "attack_challenger_operator_runbook_candidate_entry_ready": release_candidate_review_ready,
                "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue" if release_candidate_review_ready else "operator_runbook_candidate_repair_hold",
                "attack_challenger_operator_runbook_execution_entry_ready": release_candidate_review_ready,
                "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue" if release_candidate_review_ready else "operator_runbook_execution_repair_hold",
                "attack_challenger_live_readiness_review_ready": release_candidate_review_ready,
                "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue" if release_candidate_review_ready else "challenger_live_readiness_review_repair_hold",
                "attack_challenger_live_shadow_activation_review_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue" if release_candidate_review_ready else "challenger_live_shadow_activation_repair_hold",
                "attack_challenger_live_candidate_entry_ready": release_candidate_review_ready,
                "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue" if release_candidate_review_ready else "challenger_live_candidate_repair_hold",
                "attack_challenger_live_operator_paper_entry_ready": release_candidate_review_ready,
                "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue" if release_candidate_review_ready else "challenger_live_operator_paper_repair_hold",
                "attack_challenger_live_shadow_governance_review_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue" if release_candidate_review_ready else "challenger_live_shadow_governance_repair_hold",
                "attack_challenger_live_governed_shadow_entry_ready": release_candidate_review_ready,
                "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue" if release_candidate_review_ready else "challenger_live_governed_shadow_repair_hold",
                "attack_challenger_live_shadow_candidate_paper_review_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue" if release_candidate_review_ready else "challenger_live_shadow_candidate_paper_repair_hold",
                "attack_challenger_live_shadow_candidate_governance_lock_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue" if release_candidate_review_ready else "challenger_live_shadow_candidate_governance_lock_repair_hold",
                "attack_challenger_live_shadow_locked_entry_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue" if release_candidate_review_ready else "",
                "attack_challenger_live_shadow_locked_candidate_review_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue" if release_candidate_review_ready else "",
                "attack_challenger_live_shadow_locked_candidate_release_review_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue" if release_candidate_review_ready else "",
                "attack_challenger_live_shadow_locked_release_entry_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue" if release_candidate_review_ready else "",
                "attack_challenger_live_shadow_locked_release_candidate_review_ready": release_candidate_review_ready,
                "attack_challenger_live_shadow_locked_release_candidate_review_lane": "challenger_live_shadow_locked_release_candidate_review_queue" if release_candidate_review_ready else "",
                "attack_challenger_live_shadow_locked_release_governance_check_ready": governance_check_ready,
                "attack_challenger_live_shadow_locked_release_governance_check_lane": str(
                    verdict.get(
                        "challenger_live_shadow_locked_release_governance_check_lane", ""
                    )
                ),
                "attack_challenger_live_shadow_locked_release_governance_entry_ready": False,
                "attack_challenger_live_shadow_locked_release_governance_entry_lane": "",
                "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
                "attack_challenger_remote_monitoring_deployment_handoff_lane": "",
                "attack_challenger_bridge_report": str(
                    live_shadow_locked_release_governance_check_path
                ),
            }

    live_shadow_locked_release_candidate_review_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review",
    )
    if live_shadow_locked_release_candidate_review_path is not None:
        payload = json.loads(
            live_shadow_locked_release_candidate_review_path.read_text(
                encoding="utf-8-sig"
            )
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get(
                "challenger_live_shadow_locked_release_candidate_review_verdict", {}
            )
            or {}
        )
        requirements = dict(
            payload.get(
                "challenger_live_shadow_locked_release_candidate_review_requirements",
                {},
            )
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        release_candidate_review_ready = bool(
            verdict.get(
                "challenger_live_shadow_locked_release_candidate_review_ready", False
            )
        )
        locked_release_entry_ready = bool(
            requirements.get("challenger_live_shadow_locked_release_entry_ready", False)
        )
        locked_candidate_release_review_ready = bool(
            requirements.get("promotion_chain_still_green", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get("paper_validation_cagr"),
            "attack_challenger_paper_validation_max_drawdown": profile.get("paper_validation_max_drawdown"),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get("walk_forward_sensitivity_max_drift"),
            "attack_challenger_friction_final_decision": str(profile.get("friction_final_decision", "")),
            "attack_challenger_bridge_entry_ready": release_candidate_review_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue" if release_candidate_review_ready else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": release_candidate_review_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue" if release_candidate_review_ready else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": release_candidate_review_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue" if release_candidate_review_ready else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": release_candidate_review_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue" if release_candidate_review_ready else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": release_candidate_review_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue" if release_candidate_review_ready else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": release_candidate_review_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue" if release_candidate_review_ready else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": release_candidate_review_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue" if release_candidate_review_ready else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": release_candidate_review_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue" if release_candidate_review_ready else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": release_candidate_review_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue" if release_candidate_review_ready else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": release_candidate_review_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue" if release_candidate_review_ready else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": release_candidate_review_ready,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue" if release_candidate_review_ready else "challenger_live_governed_shadow_repair_hold",
            "attack_challenger_live_shadow_candidate_paper_review_ready": release_candidate_review_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue" if release_candidate_review_ready else "challenger_live_shadow_candidate_paper_repair_hold",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": release_candidate_review_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue" if release_candidate_review_ready else "challenger_live_shadow_candidate_governance_lock_repair_hold",
            "attack_challenger_live_shadow_locked_entry_ready": locked_candidate_release_review_ready,
            "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue" if locked_candidate_release_review_ready else "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": locked_candidate_release_review_ready,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue" if locked_candidate_release_review_ready else "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": locked_candidate_release_review_ready,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue" if locked_candidate_release_review_ready else "",
            "attack_challenger_live_shadow_locked_release_entry_ready": locked_release_entry_ready,
            "attack_challenger_live_shadow_locked_release_entry_lane": "challenger_live_shadow_locked_release_queue" if locked_release_entry_ready else "",
            "attack_challenger_live_shadow_locked_release_candidate_review_ready": release_candidate_review_ready,
            "attack_challenger_live_shadow_locked_release_candidate_review_lane": str(
                verdict.get("challenger_live_shadow_locked_release_candidate_review_lane", "")
            ),
            "attack_challenger_live_shadow_locked_release_governance_check_ready": False,
            "attack_challenger_live_shadow_locked_release_governance_check_lane": "",
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": "",
            "attack_challenger_bridge_report": str(
                live_shadow_locked_release_candidate_review_path
            ),
        }

    live_shadow_locked_release_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry",
    )
    if live_shadow_locked_release_entry_path is not None:
        payload = json.loads(
            live_shadow_locked_release_entry_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_live_shadow_locked_release_entry_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("challenger_live_shadow_locked_release_entry_requirements", {})
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        locked_release_entry_ready = bool(
            verdict.get("challenger_live_shadow_locked_release_entry_ready", False)
        )
        locked_candidate_release_review_ready = bool(
            requirements.get(
                "challenger_live_shadow_locked_candidate_release_review_ready", False
            )
        )
        locked_candidate_review_ready = bool(
            requirements.get("promotion_chain_still_green", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": locked_release_entry_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if locked_release_entry_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": locked_release_entry_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if locked_release_entry_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": locked_release_entry_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if locked_release_entry_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": locked_release_entry_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if locked_release_entry_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": locked_release_entry_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if locked_release_entry_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": locked_release_entry_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if locked_release_entry_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": locked_release_entry_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if locked_release_entry_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": locked_release_entry_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if locked_release_entry_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": locked_release_entry_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if locked_release_entry_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": locked_release_entry_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue"
            if locked_release_entry_ready
            else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": locked_release_entry_ready,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue"
            if locked_release_entry_ready
            else "challenger_live_governed_shadow_repair_hold",
            "attack_challenger_live_shadow_candidate_paper_review_ready": locked_release_entry_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue"
            if locked_release_entry_ready
            else "challenger_live_shadow_candidate_paper_repair_hold",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": locked_release_entry_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue"
            if locked_release_entry_ready
            else "challenger_live_shadow_candidate_governance_lock_repair_hold",
            "attack_challenger_live_shadow_locked_entry_ready": locked_candidate_review_ready,
            "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue"
            if locked_candidate_review_ready
            else "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": locked_candidate_review_ready,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue"
            if locked_candidate_review_ready
            else "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": locked_candidate_release_review_ready,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "challenger_live_shadow_locked_candidate_release_review_queue"
            if locked_candidate_release_review_ready
            else "",
            "attack_challenger_live_shadow_locked_release_entry_ready": locked_release_entry_ready,
            "attack_challenger_live_shadow_locked_release_entry_lane": str(
                verdict.get("challenger_live_shadow_locked_release_entry_lane", "")
            ),
            "attack_challenger_live_shadow_locked_release_governance_check_ready": False,
            "attack_challenger_live_shadow_locked_release_governance_check_lane": "",
            "attack_challenger_live_shadow_locked_release_governance_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_governance_entry_lane": "",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": False,
            "attack_challenger_remote_monitoring_deployment_handoff_lane": "",
            "attack_challenger_bridge_report": str(live_shadow_locked_release_entry_path),
        }

    live_shadow_locked_candidate_release_review_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_candidate_release_review",
    )
    if live_shadow_locked_candidate_release_review_path is not None:
        payload = json.loads(
            live_shadow_locked_candidate_release_review_path.read_text(
                encoding="utf-8-sig"
            )
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get(
                "challenger_live_shadow_locked_candidate_release_review_verdict", {}
            )
            or {}
        )
        requirements = dict(
            payload.get(
                "challenger_live_shadow_locked_candidate_release_review_requirements",
                {},
            )
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        release_review_ready = bool(
            verdict.get(
                "challenger_live_shadow_locked_candidate_release_review_ready", False
            )
        )
        locked_candidate_review_ready = bool(
            requirements.get("challenger_live_shadow_locked_candidate_review_ready", False)
        )
        locked_entry_ready = bool(
            requirements.get("promotion_chain_still_green", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": release_review_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if release_review_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": release_review_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if release_review_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": release_review_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if release_review_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": release_review_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if release_review_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": release_review_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if release_review_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": release_review_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if release_review_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": release_review_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if release_review_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": release_review_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if release_review_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": release_review_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if release_review_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": release_review_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue"
            if release_review_ready
            else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": release_review_ready,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue"
            if release_review_ready
            else "challenger_live_governed_shadow_repair_hold",
            "attack_challenger_live_shadow_candidate_paper_review_ready": release_review_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue"
            if release_review_ready
            else "challenger_live_shadow_candidate_paper_repair_hold",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": release_review_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue"
            if release_review_ready
            else "challenger_live_shadow_candidate_governance_lock_repair_hold",
            "attack_challenger_live_shadow_locked_entry_ready": locked_entry_ready,
            "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue"
            if locked_entry_ready
            else "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": locked_candidate_review_ready,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "challenger_live_shadow_locked_candidate_review_queue"
            if locked_candidate_review_ready
            else "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": release_review_ready,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": str(
                verdict.get(
                    "challenger_live_shadow_locked_candidate_release_review_lane", ""
                )
            ),
            "attack_challenger_live_shadow_locked_release_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_entry_lane": "",
            "attack_challenger_bridge_report": str(
                live_shadow_locked_candidate_release_review_path
            ),
        }

    live_shadow_locked_candidate_review_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_candidate_review",
    )
    if live_shadow_locked_candidate_review_path is not None:
        payload = json.loads(
            live_shadow_locked_candidate_review_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get(
                "challenger_live_shadow_locked_candidate_review_verdict", {}
            )
            or {}
        )
        requirements = dict(
            payload.get(
                "challenger_live_shadow_locked_candidate_review_requirements", {}
            )
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        review_ready = bool(
            verdict.get("challenger_live_shadow_locked_candidate_review_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": review_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if review_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": review_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if review_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": review_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if review_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": review_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if review_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": review_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if review_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": review_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if review_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": review_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if review_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": review_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if review_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": review_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if review_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": review_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue"
            if review_ready
            else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": review_ready,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue"
            if review_ready
            else "challenger_live_governed_shadow_repair_hold",
            "attack_challenger_live_shadow_candidate_paper_review_ready": review_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue"
            if review_ready
            else "challenger_live_shadow_candidate_paper_repair_hold",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": review_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue"
            if review_ready
            else "challenger_live_shadow_candidate_governance_lock_repair_hold",
            "attack_challenger_live_shadow_locked_entry_ready": bool(
                requirements.get("challenger_live_shadow_locked_entry_ready", False)
            ),
            "attack_challenger_live_shadow_locked_entry_lane": "challenger_live_shadow_locked_queue"
            if bool(requirements.get("challenger_live_shadow_locked_entry_ready", False))
            else "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": review_ready,
            "attack_challenger_live_shadow_locked_candidate_review_lane": str(
                verdict.get("challenger_live_shadow_locked_candidate_review_lane", "")
            ),
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "",
            "attack_challenger_live_shadow_locked_release_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_entry_lane": "",
            "attack_challenger_bridge_report": str(
                live_shadow_locked_candidate_review_path
            ),
        }

    live_shadow_locked_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_entry",
    )
    if live_shadow_locked_entry_path is not None:
        payload = json.loads(
            live_shadow_locked_entry_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(payload.get("challenger_live_shadow_locked_entry_verdict", {}) or {})
        requirements = dict(
            payload.get("challenger_live_shadow_locked_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        locked_entry_ready = bool(
            verdict.get("challenger_live_shadow_locked_entry_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": locked_entry_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if locked_entry_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": locked_entry_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if locked_entry_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": locked_entry_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if locked_entry_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": locked_entry_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if locked_entry_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": locked_entry_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if locked_entry_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": locked_entry_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if locked_entry_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": locked_entry_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if locked_entry_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": locked_entry_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if locked_entry_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": locked_entry_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if locked_entry_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": locked_entry_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue"
            if locked_entry_ready
            else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": locked_entry_ready,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue"
            if locked_entry_ready
            else "challenger_live_governed_shadow_repair_hold",
            "attack_challenger_live_shadow_candidate_paper_review_ready": locked_entry_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue"
            if locked_entry_ready
            else "challenger_live_shadow_candidate_paper_repair_hold",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": locked_entry_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "challenger_live_shadow_candidate_governance_lock_queue"
            if locked_entry_ready
            else "challenger_live_shadow_candidate_governance_lock_repair_hold",
            "attack_challenger_live_shadow_locked_entry_ready": locked_entry_ready,
            "attack_challenger_live_shadow_locked_entry_lane": str(
                verdict.get("challenger_live_shadow_locked_entry_lane", "")
            ),
            "attack_challenger_live_shadow_locked_candidate_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "",
            "attack_challenger_live_shadow_locked_release_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_entry_lane": "",
            "attack_challenger_bridge_report": str(live_shadow_locked_entry_path),
        }
    live_shadow_candidate_governance_lock_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_governance_lock",
    )
    if live_shadow_candidate_governance_lock_path is not None:
        payload = json.loads(
            live_shadow_candidate_governance_lock_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get(
                "challenger_live_shadow_candidate_governance_lock_verdict", {}
            )
            or {}
        )
        requirements = dict(
            payload.get(
                "challenger_live_shadow_candidate_governance_lock_requirements", {}
            )
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        governance_lock_ready = bool(
            verdict.get("challenger_live_shadow_candidate_governance_lock_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": governance_lock_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if governance_lock_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": governance_lock_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if governance_lock_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": governance_lock_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if governance_lock_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": governance_lock_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if governance_lock_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": governance_lock_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if governance_lock_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": governance_lock_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if governance_lock_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": governance_lock_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if governance_lock_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": governance_lock_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if governance_lock_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": governance_lock_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if governance_lock_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": governance_lock_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue"
            if governance_lock_ready
            else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": governance_lock_ready,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue"
            if governance_lock_ready
            else "challenger_live_governed_shadow_repair_hold",
            "attack_challenger_live_shadow_candidate_paper_review_ready": governance_lock_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "challenger_live_shadow_candidate_paper_queue"
            if governance_lock_ready
            else "challenger_live_shadow_candidate_paper_repair_hold",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": governance_lock_ready,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": str(
                verdict.get(
                    "challenger_live_shadow_candidate_governance_lock_lane", ""
                )
            ),
            "attack_challenger_live_shadow_locked_entry_ready": False,
            "attack_challenger_live_shadow_locked_entry_lane": "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "",
            "attack_challenger_live_shadow_locked_release_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_entry_lane": "",
            "attack_challenger_bridge_report": str(
                live_shadow_candidate_governance_lock_path
            ),
        }
    live_shadow_candidate_paper_review_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_paper_review",
    )
    if live_shadow_candidate_paper_review_path is not None:
        payload = json.loads(
            live_shadow_candidate_paper_review_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_live_shadow_candidate_paper_review_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("challenger_live_shadow_candidate_paper_review_requirements", {})
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        paper_review_ready = bool(
            verdict.get("challenger_live_shadow_candidate_paper_review_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": paper_review_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if paper_review_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": paper_review_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if paper_review_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": paper_review_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if paper_review_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": paper_review_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if paper_review_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": paper_review_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if paper_review_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": paper_review_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if paper_review_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": paper_review_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if paper_review_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": paper_review_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if paper_review_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": paper_review_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if paper_review_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": paper_review_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue"
            if paper_review_ready
            else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": paper_review_ready,
            "attack_challenger_live_governed_shadow_entry_lane": "challenger_live_governed_shadow_queue"
            if paper_review_ready
            else "challenger_live_governed_shadow_repair_hold",
            "attack_challenger_live_shadow_candidate_paper_review_ready": paper_review_ready,
            "attack_challenger_live_shadow_candidate_paper_review_lane": str(
                verdict.get("challenger_live_shadow_candidate_paper_review_lane", "")
            ),
            "attack_challenger_live_shadow_candidate_governance_lock_ready": False,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "",
            "attack_challenger_live_shadow_locked_entry_ready": False,
            "attack_challenger_live_shadow_locked_entry_lane": "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "",
            "attack_challenger_live_shadow_locked_release_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_entry_lane": "",
            "attack_challenger_bridge_report": str(live_shadow_candidate_paper_review_path),
        }
    live_governed_shadow_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_governed_shadow_entry",
    )
    if live_governed_shadow_entry_path is not None:
        payload = json.loads(
            live_governed_shadow_entry_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_live_governed_shadow_entry_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("challenger_live_governed_shadow_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        governed_shadow_ready = bool(
            verdict.get("challenger_live_governed_shadow_entry_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": governed_shadow_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if governed_shadow_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": governed_shadow_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if governed_shadow_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": governed_shadow_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if governed_shadow_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": governed_shadow_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if governed_shadow_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": governed_shadow_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if governed_shadow_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": governed_shadow_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if governed_shadow_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": governed_shadow_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if governed_shadow_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": governed_shadow_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if governed_shadow_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": governed_shadow_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if governed_shadow_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": governed_shadow_ready,
            "attack_challenger_live_shadow_governance_review_lane": "challenger_live_shadow_governance_queue"
            if governed_shadow_ready
            else "challenger_live_shadow_governance_repair_hold",
            "attack_challenger_live_governed_shadow_entry_ready": governed_shadow_ready,
            "attack_challenger_live_governed_shadow_entry_lane": str(
                verdict.get("challenger_live_governed_shadow_entry_lane", "")
            ),
            "attack_challenger_live_shadow_candidate_paper_review_ready": False,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": False,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "",
            "attack_challenger_live_shadow_locked_entry_ready": False,
            "attack_challenger_live_shadow_locked_entry_lane": "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "",
            "attack_challenger_live_shadow_locked_release_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_entry_lane": "",
            "attack_challenger_bridge_report": str(live_governed_shadow_entry_path),
        }
    live_shadow_governance_review_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_governance_review",
    )
    if live_shadow_governance_review_path is not None:
        payload = json.loads(
            live_shadow_governance_review_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_live_shadow_governance_review_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("challenger_live_shadow_governance_review_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        operator_paper_ready = bool(
            requirements.get("challenger_live_operator_paper_entry_ready", False)
        )
        governance_ready = bool(
            verdict.get("challenger_live_shadow_governance_review_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": operator_paper_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if operator_paper_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": operator_paper_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if operator_paper_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": operator_paper_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if operator_paper_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": operator_paper_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if operator_paper_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": operator_paper_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if operator_paper_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": operator_paper_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if operator_paper_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": operator_paper_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if operator_paper_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": operator_paper_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if operator_paper_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": operator_paper_ready,
            "attack_challenger_live_operator_paper_entry_lane": "challenger_live_operator_paper_queue"
            if operator_paper_ready
            else "challenger_live_operator_paper_repair_hold",
            "attack_challenger_live_shadow_governance_review_ready": governance_ready,
            "attack_challenger_live_shadow_governance_review_lane": str(
                verdict.get("challenger_live_shadow_governance_review_lane", "")
            ),
            "attack_challenger_live_governed_shadow_entry_ready": False,
            "attack_challenger_live_governed_shadow_entry_lane": "",
            "attack_challenger_live_shadow_candidate_paper_review_ready": False,
            "attack_challenger_live_shadow_candidate_paper_review_lane": "",
            "attack_challenger_live_shadow_candidate_governance_lock_ready": False,
            "attack_challenger_live_shadow_candidate_governance_lock_lane": "",
            "attack_challenger_live_shadow_locked_entry_ready": False,
            "attack_challenger_live_shadow_locked_entry_lane": "",
            "attack_challenger_live_shadow_locked_candidate_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_review_lane": "",
            "attack_challenger_live_shadow_locked_candidate_release_review_ready": False,
            "attack_challenger_live_shadow_locked_candidate_release_review_lane": "",
            "attack_challenger_live_shadow_locked_release_entry_ready": False,
            "attack_challenger_live_shadow_locked_release_entry_lane": "",
            "attack_challenger_bridge_report": str(live_shadow_governance_review_path),
        }
    live_operator_paper_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_operator_paper_entry",
    )
    if live_operator_paper_entry_path is not None:
        payload = json.loads(
            live_operator_paper_entry_path.read_text(encoding="utf-8-sig")
        )
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_live_operator_paper_entry_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("challenger_live_operator_paper_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        candidate_entry_ready = bool(
            requirements.get("challenger_live_candidate_entry_ready", False)
        )
        operator_paper_ready = bool(
            verdict.get("challenger_live_operator_paper_entry_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": candidate_entry_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if candidate_entry_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": candidate_entry_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if candidate_entry_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": candidate_entry_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if candidate_entry_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": candidate_entry_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if candidate_entry_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": candidate_entry_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if candidate_entry_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": candidate_entry_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if candidate_entry_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": candidate_entry_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if candidate_entry_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": candidate_entry_ready,
            "attack_challenger_live_candidate_entry_lane": "challenger_live_candidate_queue"
            if candidate_entry_ready
            else "challenger_live_candidate_repair_hold",
            "attack_challenger_live_operator_paper_entry_ready": operator_paper_ready,
            "attack_challenger_live_operator_paper_entry_lane": str(
                verdict.get("challenger_live_operator_paper_entry_lane", "")
            ),
            "attack_challenger_live_shadow_governance_review_ready": False,
            "attack_challenger_live_shadow_governance_review_lane": "",
            "attack_challenger_bridge_report": str(live_operator_paper_entry_path),
        }
    live_candidate_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_candidate_entry",
    )
    if live_candidate_entry_path is not None:
        payload = json.loads(live_candidate_entry_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(payload.get("challenger_live_candidate_entry_verdict", {}) or {})
        requirements = dict(
            payload.get("challenger_live_candidate_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        activation_ready = bool(
            requirements.get("challenger_live_shadow_activation_review_ready", False)
        )
        candidate_entry_ready = bool(
            verdict.get("challenger_live_candidate_entry_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": activation_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if activation_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": activation_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if activation_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": activation_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if activation_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": activation_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if activation_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": activation_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if activation_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": activation_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if activation_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": activation_ready,
            "attack_challenger_live_shadow_activation_review_lane": "challenger_live_shadow_activation_queue"
            if activation_ready
            else "challenger_live_shadow_activation_repair_hold",
            "attack_challenger_live_candidate_entry_ready": candidate_entry_ready,
            "attack_challenger_live_candidate_entry_lane": str(
                verdict.get("challenger_live_candidate_entry_lane", "")
            ),
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(live_candidate_entry_path),
        }
    live_shadow_activation_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_shadow_activation_review",
    )
    if live_shadow_activation_path is not None:
        payload = json.loads(live_shadow_activation_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_live_shadow_activation_review_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("challenger_live_shadow_activation_review_requirements", {})
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        live_readiness_ready = bool(
            requirements.get("challenger_candidate_live_readiness_review_ready", False)
        )
        activation_ready = bool(
            verdict.get("challenger_live_shadow_activation_review_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": live_readiness_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if live_readiness_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": live_readiness_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if live_readiness_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": live_readiness_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if live_readiness_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": live_readiness_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if live_readiness_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": live_readiness_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if live_readiness_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": live_readiness_ready,
            "attack_challenger_live_readiness_review_lane": "challenger_live_readiness_review_queue"
            if live_readiness_ready
            else "challenger_live_readiness_review_repair_hold",
            "attack_challenger_live_shadow_activation_review_ready": activation_ready,
            "attack_challenger_live_shadow_activation_review_lane": str(
                verdict.get("challenger_live_shadow_activation_review_lane", "")
            ),
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(live_shadow_activation_path),
        }
    live_readiness_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_live_readiness_review",
    )
    if live_readiness_path is not None:
        payload = json.loads(live_readiness_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_candidate_live_readiness_review_verdict", {}) or {}
        )
        requirements = dict(
            payload.get(
                "challenger_candidate_live_readiness_review_requirements", {}
            )
            or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        shadow_monitoring_ready = bool(
            requirements.get("challenger_shadow_monitoring_entry_ready", False)
        )
        live_readiness_ready = bool(
            verdict.get("challenger_candidate_live_readiness_review_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": shadow_monitoring_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if shadow_monitoring_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": shadow_monitoring_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if shadow_monitoring_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": shadow_monitoring_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if shadow_monitoring_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": shadow_monitoring_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if shadow_monitoring_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": shadow_monitoring_ready,
            "attack_challenger_operator_runbook_execution_entry_lane": "challenger_shadow_monitoring_queue"
            if shadow_monitoring_ready
            else "operator_runbook_execution_repair_hold",
            "attack_challenger_live_readiness_review_ready": live_readiness_ready,
            "attack_challenger_live_readiness_review_lane": str(
                verdict.get("challenger_candidate_live_readiness_review_lane", "")
            ),
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(live_readiness_path),
        }
    shadow_monitoring_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_shadow_monitoring_entry",
    )
    if shadow_monitoring_path is not None:
        payload = json.loads(shadow_monitoring_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("challenger_shadow_monitoring_entry_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("challenger_shadow_monitoring_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        execution_entry_ready = bool(
            requirements.get("operator_runbook_execution_entry_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": execution_entry_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if execution_entry_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": execution_entry_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if execution_entry_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": execution_entry_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if execution_entry_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": execution_entry_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if execution_entry_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": bool(
                verdict.get("challenger_shadow_monitoring_entry_ready", False)
            ),
            "attack_challenger_operator_runbook_execution_entry_lane": str(
                verdict.get("challenger_shadow_monitoring_entry_lane", "")
            ),
            "attack_challenger_live_readiness_review_ready": False,
            "attack_challenger_live_readiness_review_lane": "",
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(shadow_monitoring_path),
        }
    runbook_execution_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_operator_runbook_execution_entry",
    )
    if runbook_execution_path is not None:
        payload = json.loads(runbook_execution_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("operator_runbook_execution_entry_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("operator_runbook_execution_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        candidate_entry_ready = bool(
            requirements.get("operator_runbook_candidate_entry_ready", False)
        )
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": candidate_entry_ready,
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if candidate_entry_ready
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": candidate_entry_ready,
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if candidate_entry_ready
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": candidate_entry_ready,
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if candidate_entry_ready
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": candidate_entry_ready,
            "attack_challenger_operator_runbook_candidate_entry_lane": "operator_runbook_candidate_queue"
            if candidate_entry_ready
            else "operator_runbook_candidate_repair_hold",
            "attack_challenger_operator_runbook_execution_entry_ready": bool(
                verdict.get("operator_runbook_execution_entry_ready", False)
            ),
            "attack_challenger_operator_runbook_execution_entry_lane": str(
                verdict.get("operator_runbook_execution_entry_lane", "")
            ),
            "attack_challenger_live_readiness_review_ready": False,
            "attack_challenger_live_readiness_review_lane": "",
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(runbook_execution_path),
        }
    runbook_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_operator_runbook_candidate_entry",
    )
    if runbook_entry_path is not None:
        payload = json.loads(runbook_entry_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(
            payload.get("operator_runbook_candidate_entry_verdict", {}) or {}
        )
        requirements = dict(
            payload.get("operator_runbook_candidate_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": bool(
                requirements.get("operator_stack_handoff_ready", False)
            ),
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if bool(requirements.get("operator_stack_handoff_ready", False))
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": bool(
                requirements.get("operator_stack_handoff_ready", False)
            ),
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if bool(requirements.get("operator_stack_handoff_ready", False))
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": bool(
                requirements.get("operator_stack_handoff_ready", False)
            ),
            "attack_challenger_operator_stack_handoff_lane": "operator_stack_handoff_queue"
            if bool(requirements.get("operator_stack_handoff_ready", False))
            else "operator_stack_repair_hold",
            "attack_challenger_operator_runbook_candidate_entry_ready": bool(
                verdict.get("operator_runbook_candidate_entry_ready", False)
            ),
            "attack_challenger_operator_runbook_candidate_entry_lane": str(
                verdict.get("operator_runbook_candidate_entry_lane", "")
            ),
            "attack_challenger_operator_runbook_execution_entry_ready": False,
            "attack_challenger_operator_runbook_execution_entry_lane": "",
            "attack_challenger_live_readiness_review_ready": False,
            "attack_challenger_live_readiness_review_lane": "",
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(runbook_entry_path),
        }
    handoff_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_operator_stack_handoff",
    )
    if handoff_path is not None:
        payload = json.loads(handoff_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(payload.get("operator_stack_handoff_verdict", {}) or {})
        requirements = dict(
            payload.get("operator_stack_handoff_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_chain_still_green", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": bool(
                requirements.get("execution_contract_entry_ready", False)
            ),
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if bool(requirements.get("execution_contract_entry_ready", False))
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": bool(
                requirements.get("execution_contract_entry_ready", False)
            ),
            "attack_challenger_execution_contract_queue_lane": "challenger_execution_contract_queue"
            if bool(requirements.get("execution_contract_entry_ready", False))
            else "execution_contract_entry_repair_hold",
            "attack_challenger_operator_stack_handoff_ready": bool(
                verdict.get("operator_stack_handoff_ready", False)
            ),
            "attack_challenger_operator_stack_handoff_lane": str(
                verdict.get("operator_stack_handoff_lane", "")
            ),
            "attack_challenger_operator_runbook_candidate_entry_ready": False,
            "attack_challenger_operator_runbook_candidate_entry_lane": "",
            "attack_challenger_operator_runbook_execution_entry_ready": False,
            "attack_challenger_operator_runbook_execution_entry_lane": "",
            "attack_challenger_live_readiness_review_ready": False,
            "attack_challenger_live_readiness_review_lane": "",
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(handoff_path),
        }
    entry_check_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check",
    )
    if entry_check_path is not None:
        payload = json.loads(entry_check_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(payload.get("execution_contract_entry_verdict", {}) or {})
        requirements = dict(
            payload.get("execution_contract_entry_requirements", {}) or {}
        )
        context = dict(payload.get("stack_context", {}) or {})
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                requirements.get("promotion_ready", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get(
                "paper_validation_cagr"
            ),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": bool(
                requirements.get("bridge_entry_ready", False)
            ),
            "attack_challenger_bridge_queue_lane": "attack_challenger_queue"
            if bool(requirements.get("bridge_entry_ready", False))
            else "bridge_repair_hold",
            "attack_challenger_execution_contract_entry_ready": bool(
                verdict.get("execution_contract_entry_ready", False)
            ),
            "attack_challenger_execution_contract_queue_lane": str(
                verdict.get("execution_contract_queue_lane", "")
            ),
            "attack_challenger_operator_stack_handoff_ready": False,
            "attack_challenger_operator_stack_handoff_lane": "",
            "attack_challenger_operator_runbook_candidate_entry_ready": False,
            "attack_challenger_operator_runbook_candidate_entry_lane": "",
            "attack_challenger_operator_runbook_execution_entry_ready": False,
            "attack_challenger_operator_runbook_execution_entry_lane": "",
            "attack_challenger_live_readiness_review_ready": False,
            "attack_challenger_live_readiness_review_lane": "",
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(entry_check_path),
        }
    bridge_entry_path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_bridge_entry_screen",
    )
    if bridge_entry_path is not None:
        payload = json.loads(bridge_entry_path.read_text(encoding="utf-8-sig"))
        profile = dict(payload.get("candidate_profile", {}) or {})
        verdict = dict(payload.get("bridge_entry_verdict", {}) or {})
        context = dict(payload.get("stack_context", {}) or {})
        return {
            "attack_challenger_candidate": str(
                context.get("attack_challenger_candidate", profile.get("label", ""))
            ),
            "attack_challenger_role_assignment": "attack_challenger_candidate",
            "attack_challenger_promotion_ready": bool(
                verdict.get("bridge_entry_ready", False)
            ),
            "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
            "attack_challenger_paper_validation_cagr": profile.get("paper_validation_cagr"),
            "attack_challenger_paper_validation_max_drawdown": profile.get(
                "paper_validation_max_drawdown"
            ),
            "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
                "walk_forward_sensitivity_max_drift"
            ),
            "attack_challenger_friction_final_decision": str(
                profile.get("friction_final_decision", "")
            ),
            "attack_challenger_bridge_entry_ready": bool(
                verdict.get("bridge_entry_ready", False)
            ),
            "attack_challenger_bridge_queue_lane": str(
                verdict.get("bridge_queue_lane", "")
            ),
            "attack_challenger_execution_contract_entry_ready": False,
            "attack_challenger_execution_contract_queue_lane": "",
            "attack_challenger_operator_stack_handoff_ready": False,
            "attack_challenger_operator_stack_handoff_lane": "",
            "attack_challenger_operator_runbook_candidate_entry_ready": False,
            "attack_challenger_operator_runbook_candidate_entry_lane": "",
            "attack_challenger_operator_runbook_execution_entry_ready": False,
            "attack_challenger_operator_runbook_execution_entry_lane": "",
            "attack_challenger_live_readiness_review_ready": False,
            "attack_challenger_live_readiness_review_lane": "",
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": str(bridge_entry_path),
        }
    path = _resolve_latest_json_artifact(
        analysis_dir,
        "btc_1d_pullthrough_asymmetric_release_promotion_bridge",
    )
    if path is None:
        return {
            "attack_challenger_candidate": "",
            "attack_challenger_role_assignment": "",
            "attack_challenger_promotion_ready": False,
            "attack_challenger_next_step": "",
            "attack_challenger_paper_validation_cagr": None,
            "attack_challenger_paper_validation_max_drawdown": None,
            "attack_challenger_walk_forward_sensitivity_max_drift": None,
            "attack_challenger_friction_final_decision": "",
            "attack_challenger_bridge_entry_ready": False,
            "attack_challenger_bridge_queue_lane": "",
            "attack_challenger_execution_contract_entry_ready": False,
            "attack_challenger_execution_contract_queue_lane": "",
            "attack_challenger_operator_stack_handoff_ready": False,
            "attack_challenger_operator_stack_handoff_lane": "",
            "attack_challenger_operator_runbook_candidate_entry_ready": False,
            "attack_challenger_operator_runbook_candidate_entry_lane": "",
            "attack_challenger_operator_runbook_execution_entry_ready": False,
            "attack_challenger_operator_runbook_execution_entry_lane": "",
            "attack_challenger_live_readiness_review_ready": False,
            "attack_challenger_live_readiness_review_lane": "",
            "attack_challenger_live_shadow_activation_review_ready": False,
            "attack_challenger_live_shadow_activation_review_lane": "",
            "attack_challenger_live_candidate_entry_ready": False,
            "attack_challenger_live_candidate_entry_lane": "",
            "attack_challenger_live_operator_paper_entry_ready": False,
            "attack_challenger_live_operator_paper_entry_lane": "",
            "attack_challenger_bridge_report": "",
        }
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    profile = dict(payload.get("candidate_profile", {}) or {})
    verdict = dict(payload.get("promotion_bridge_verdict", {}) or {})
    return {
        "attack_challenger_candidate": str(profile.get("label", "")),
        "attack_challenger_role_assignment": str(verdict.get("role_assignment", "")),
        "attack_challenger_promotion_ready": bool(verdict.get("promotion_ready", False)),
        "attack_challenger_next_step": str(verdict.get("next_step_now", "")),
        "attack_challenger_paper_validation_cagr": profile.get("paper_validation_cagr"),
        "attack_challenger_paper_validation_max_drawdown": profile.get(
            "paper_validation_max_drawdown"
        ),
        "attack_challenger_walk_forward_sensitivity_max_drift": profile.get(
            "walk_forward_sensitivity_max_drift"
        ),
        "attack_challenger_friction_final_decision": str(
            profile.get("friction_final_decision", "")
        ),
        "attack_challenger_bridge_entry_ready": False,
        "attack_challenger_bridge_queue_lane": "",
        "attack_challenger_execution_contract_entry_ready": False,
        "attack_challenger_execution_contract_queue_lane": "",
        "attack_challenger_operator_stack_handoff_ready": False,
        "attack_challenger_operator_stack_handoff_lane": "",
        "attack_challenger_operator_runbook_candidate_entry_ready": False,
        "attack_challenger_operator_runbook_candidate_entry_lane": "",
        "attack_challenger_operator_runbook_execution_entry_ready": False,
        "attack_challenger_operator_runbook_execution_entry_lane": "",
        "attack_challenger_live_readiness_review_ready": False,
        "attack_challenger_live_readiness_review_lane": "",
        "attack_challenger_live_shadow_activation_review_ready": False,
        "attack_challenger_live_shadow_activation_review_lane": "",
        "attack_challenger_live_candidate_entry_ready": False,
        "attack_challenger_live_candidate_entry_lane": "",
        "attack_challenger_live_operator_paper_entry_ready": False,
        "attack_challenger_live_operator_paper_entry_lane": "",
        "attack_challenger_bridge_report": str(path),
    }


def _derive_operator_verdict(
    *,
    shadow_decision: str,
    dashboard_ready: bool,
    quick_read_contract_partitioned: bool,
    contract_health_aligned: bool,
    execution_contract_aligned: bool,
    paper_execution_contract_aligned: bool,
    paper_ledger_consistent: bool,
) -> str:
    if (
        quick_read_contract_partitioned
        and contract_health_aligned
        and execution_contract_aligned
        and paper_execution_contract_aligned
        and paper_ledger_consistent
        and shadow_decision == "shadow_ready_for_btc_only"
    ):
        return "shadow_monitoring_ready"
    if dashboard_ready and shadow_decision == "ready":
        return "ready"
    if not (
        quick_read_contract_partitioned
        and contract_health_aligned
        and execution_contract_aligned
        and paper_execution_contract_aligned
        and paper_ledger_consistent
    ):
        return "ops_repair_required"
    return "validation_in_progress"


def _build_refresh_summary(
    *,
    latest_summary: dict[str, object],
    paper_state: dict[str, object],
    contract_health: dict[str, object],
    execution_contract_state: dict[str, object],
    dashboard_payload: dict[str, object],
    dashboard_summary: dict[str, object],
    latest_aliases: dict[str, str],
) -> dict[str, object]:
    candidate = str(
        dashboard_summary.get(
            "candidate",
            latest_summary.get("candidate", ""),
        )
    )
    shadow_decision = str(
        dashboard_summary.get(
            "shadow_decision",
            latest_summary.get("shadow_decision", ""),
        )
    )
    practical_status_label = str(dashboard_summary.get("practical_status_label", ""))
    dashboard_ready = bool(dashboard_summary.get("dashboard_ready", False))
    quick_read_contract_partitioned = bool(
        dashboard_summary.get(
            "quick_read_contract_partitioned",
            contract_health.get("contracts_are_well_partitioned", False),
        )
    )
    contract_health_aligned = bool(
        dashboard_summary.get(
            "contract_health_aligned",
            contract_health.get("contract_health_aligned", False),
        )
    )
    execution_contract_aligned = bool(
        dashboard_summary.get(
            "execution_contract_aligned",
            execution_contract_state.get("execution_contract_aligned", False),
        )
    )
    paper_execution_contract_aligned = bool(
        dashboard_summary.get(
            "paper_execution_contract_aligned",
            paper_state.get("paper_execution_contract_aligned", False),
        )
    )
    paper_ledger_consistent = bool(
        dashboard_summary.get(
            "paper_ledger_consistent",
            paper_state.get("paper_ledger_consistent", False),
        )
    )
    paper_exit_duplicate_run = bool(
        dashboard_summary.get(
            "paper_exit_duplicate_run",
            paper_state.get("paper_exit_duplicate_run", False),
        )
    )
    attention_flags = list(dashboard_summary.get("attention_flags", []) or [])
    attack_challenger_candidate = str(
        dashboard_summary.get("attack_challenger_candidate", "")
    )
    attack_challenger_role_assignment = str(
        dashboard_summary.get("attack_challenger_role_assignment", "")
    )
    attack_challenger_promotion_ready = bool(
        dashboard_summary.get("attack_challenger_promotion_ready", False)
    )
    attack_challenger_execution_contract_entry_ready = bool(
        dashboard_summary.get("attack_challenger_execution_contract_entry_ready", False)
    )
    attack_challenger_operator_stack_handoff_ready = bool(
        dashboard_summary.get("attack_challenger_operator_stack_handoff_ready", False)
    )
    attack_challenger_operator_runbook_candidate_entry_ready = bool(
        dashboard_summary.get(
            "attack_challenger_operator_runbook_candidate_entry_ready", False
        )
    )
    attack_challenger_operator_runbook_execution_entry_ready = bool(
        dashboard_summary.get(
            "attack_challenger_operator_runbook_execution_entry_ready", False
        )
    )
    attack_challenger_live_readiness_review_ready = bool(
        dashboard_summary.get("attack_challenger_live_readiness_review_ready", False)
    )
    attack_challenger_live_shadow_activation_review_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_activation_review_ready", False
        )
    )
    attack_challenger_live_candidate_entry_ready = bool(
        dashboard_summary.get("attack_challenger_live_candidate_entry_ready", False)
    )
    attack_challenger_live_operator_paper_entry_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_operator_paper_entry_ready", False
        )
    )
    attack_challenger_live_shadow_governance_review_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_governance_review_ready", False
        )
    )
    attack_challenger_live_governed_shadow_entry_ready = bool(
        dashboard_summary.get("attack_challenger_live_governed_shadow_entry_ready", False)
    )
    attack_challenger_live_shadow_candidate_paper_review_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_candidate_paper_review_ready", False
        )
    )
    attack_challenger_live_shadow_candidate_governance_lock_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_candidate_governance_lock_ready", False
        )
    )
    attack_challenger_live_shadow_locked_entry_ready = bool(
        dashboard_summary.get("attack_challenger_live_shadow_locked_entry_ready", False)
    )
    attack_challenger_live_shadow_locked_candidate_review_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_locked_candidate_review_ready", False
        )
    )
    attack_challenger_live_shadow_locked_candidate_release_review_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_locked_candidate_release_review_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_entry_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_locked_release_entry_ready", False
        )
    )
    attack_challenger_live_shadow_locked_release_candidate_review_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_locked_release_candidate_review_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_governance_check_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_locked_release_governance_check_ready",
            False,
        )
    )
    attack_challenger_live_shadow_locked_release_governance_entry_ready = bool(
        dashboard_summary.get(
            "attack_challenger_live_shadow_locked_release_governance_entry_ready",
            False,
        )
    )
    attack_challenger_next_step = str(
        dashboard_summary.get("attack_challenger_next_step", "")
    )
    dashboard_artifacts = dict(dashboard_payload.get("artifacts", {}) or {})
    attack_challenger_bridge_report = str(
        dashboard_artifacts.get(
            "attack_challenger_bridge_report_json",
            latest_aliases.get(
                "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff",
                contract_health.get("attack_challenger_bridge_report", ""),
            ),
        )
    )
    attack_challenger_remote_monitoring_deployment_handoff_ready = bool(
        dashboard_summary.get(
            "attack_challenger_remote_monitoring_deployment_handoff_ready",
            False,
        )
        or attack_challenger_next_step
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
    )
    deployment_monitoring_active = bool(
        dashboard_summary.get(
            "deployment_monitoring_active",
            shadow_decision == "shadow_ready_for_btc_only"
            and dashboard_ready
            and attack_challenger_remote_monitoring_deployment_handoff_ready
            and attack_challenger_next_step
            == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
        )
    )
    development = dict(dashboard_payload.get("development", {}) or {})
    next_actions = list(development.get("next_actions", []) or [])
    project_direction = str(development.get("project_direction", ""))
    operator_verdict = _derive_operator_verdict(
        shadow_decision=shadow_decision,
        dashboard_ready=dashboard_ready,
        quick_read_contract_partitioned=quick_read_contract_partitioned,
        contract_health_aligned=contract_health_aligned,
        execution_contract_aligned=execution_contract_aligned,
        paper_execution_contract_aligned=paper_execution_contract_aligned,
        paper_ledger_consistent=paper_ledger_consistent,
    )
    refresh_read = (
        "refresh summary | "
        f"verdict={operator_verdict} | "
        f"candidate={candidate} | "
        f"shadow={shadow_decision} | "
        f"practical={practical_status_label} | "
        f"dashboard_ready={dashboard_ready} | "
        f"deployment_monitoring_active={deployment_monitoring_active} | "
        f"quick_read_partitioned={quick_read_contract_partitioned} | "
        f"contract_health={contract_health_aligned} | "
        f"execution_contract={execution_contract_aligned} | "
        f"paper_execution_contract={paper_execution_contract_aligned} | "
        f"paper_ledger={paper_ledger_consistent} | "
        f"next_actions={' | '.join(next_actions) if next_actions else 'none'}"
        + (
            f" | attack_challenger={attack_challenger_candidate}"
            f" | attack_challenger_ready={attack_challenger_promotion_ready}"
            f" | attack_challenger_contract_entry_ready={attack_challenger_execution_contract_entry_ready}"
            f" | attack_challenger_handoff_ready={attack_challenger_operator_stack_handoff_ready}"
            f" | attack_challenger_runbook_entry_ready={attack_challenger_operator_runbook_candidate_entry_ready}"
            f" | attack_challenger_runbook_execution_ready={attack_challenger_operator_runbook_execution_entry_ready}"
            f" | attack_challenger_live_readiness_ready={attack_challenger_live_readiness_review_ready}"
            f" | attack_challenger_live_shadow_activation_ready={attack_challenger_live_shadow_activation_review_ready}"
            f" | attack_challenger_live_candidate_ready={attack_challenger_live_candidate_entry_ready}"
            f" | attack_challenger_live_operator_paper_ready={attack_challenger_live_operator_paper_entry_ready}"
            f" | attack_challenger_live_shadow_governance_ready={attack_challenger_live_shadow_governance_review_ready}"
            f" | attack_challenger_live_governed_shadow_ready={attack_challenger_live_governed_shadow_entry_ready}"
            f" | attack_challenger_live_shadow_candidate_paper_ready={attack_challenger_live_shadow_candidate_paper_review_ready}"
            f" | attack_challenger_live_shadow_candidate_governance_lock_ready={attack_challenger_live_shadow_candidate_governance_lock_ready}"
            f" | attack_challenger_live_shadow_locked_entry_ready={attack_challenger_live_shadow_locked_entry_ready}"
            f" | attack_challenger_live_shadow_locked_candidate_review_ready={attack_challenger_live_shadow_locked_candidate_review_ready}"
            f" | attack_challenger_live_shadow_locked_candidate_release_review_ready={attack_challenger_live_shadow_locked_candidate_release_review_ready}"
            f" | attack_challenger_live_shadow_locked_release_entry_ready={attack_challenger_live_shadow_locked_release_entry_ready}"
            f" | attack_challenger_live_shadow_locked_release_candidate_review_ready={attack_challenger_live_shadow_locked_release_candidate_review_ready}"
            f" | attack_challenger_live_shadow_locked_release_governance_check_ready={attack_challenger_live_shadow_locked_release_governance_check_ready}"
            f" | attack_challenger_live_shadow_locked_release_governance_entry_ready={attack_challenger_live_shadow_locked_release_governance_entry_ready}"
            f" | attack_challenger_remote_monitoring_handoff_ready={attack_challenger_remote_monitoring_deployment_handoff_ready}"
            f" | attack_challenger_role={attack_challenger_role_assignment}"
            f" | attack_challenger_next={attack_challenger_next_step}"
            f" | attack_challenger_bridge_report={attack_challenger_bridge_report}"
            if attack_challenger_candidate
            else ""
        )
    )
    return {
        "candidate": candidate,
        "shadow_decision": shadow_decision,
        "practical_status_label": practical_status_label,
        "dashboard_ready": dashboard_ready,
        "deployment_monitoring_active": deployment_monitoring_active,
        "quick_read_contract_partitioned": quick_read_contract_partitioned,
        "contract_health_aligned": contract_health_aligned,
        "execution_contract_aligned": execution_contract_aligned,
        "paper_execution_contract_aligned": paper_execution_contract_aligned,
        "paper_ledger_consistent": paper_ledger_consistent,
        "paper_exit_duplicate_run": paper_exit_duplicate_run,
        "operator_verdict": operator_verdict,
        "project_direction": project_direction,
        "next_actions": next_actions,
        "attention_flags": attention_flags,
        "attack_challenger_candidate": attack_challenger_candidate,
        "attack_challenger_role_assignment": attack_challenger_role_assignment,
        "attack_challenger_promotion_ready": attack_challenger_promotion_ready,
        "attack_challenger_execution_contract_entry_ready": attack_challenger_execution_contract_entry_ready,
        "attack_challenger_operator_stack_handoff_ready": attack_challenger_operator_stack_handoff_ready,
        "attack_challenger_operator_runbook_candidate_entry_ready": attack_challenger_operator_runbook_candidate_entry_ready,
        "attack_challenger_operator_runbook_execution_entry_ready": attack_challenger_operator_runbook_execution_entry_ready,
        "attack_challenger_live_readiness_review_ready": attack_challenger_live_readiness_review_ready,
        "attack_challenger_live_shadow_activation_review_ready": attack_challenger_live_shadow_activation_review_ready,
        "attack_challenger_live_candidate_entry_ready": attack_challenger_live_candidate_entry_ready,
        "attack_challenger_live_operator_paper_entry_ready": attack_challenger_live_operator_paper_entry_ready,
        "attack_challenger_live_shadow_governance_review_ready": attack_challenger_live_shadow_governance_review_ready,
        "attack_challenger_live_governed_shadow_entry_ready": attack_challenger_live_governed_shadow_entry_ready,
        "attack_challenger_live_shadow_candidate_paper_review_ready": attack_challenger_live_shadow_candidate_paper_review_ready,
        "attack_challenger_live_shadow_candidate_governance_lock_ready": attack_challenger_live_shadow_candidate_governance_lock_ready,
        "attack_challenger_live_shadow_locked_entry_ready": attack_challenger_live_shadow_locked_entry_ready,
        "attack_challenger_live_shadow_locked_candidate_review_ready": attack_challenger_live_shadow_locked_candidate_review_ready,
        "attack_challenger_live_shadow_locked_candidate_release_review_ready": attack_challenger_live_shadow_locked_candidate_release_review_ready,
        "attack_challenger_live_shadow_locked_release_entry_ready": attack_challenger_live_shadow_locked_release_entry_ready,
        "attack_challenger_live_shadow_locked_release_candidate_review_ready": attack_challenger_live_shadow_locked_release_candidate_review_ready,
        "attack_challenger_live_shadow_locked_release_governance_check_ready": attack_challenger_live_shadow_locked_release_governance_check_ready,
        "attack_challenger_live_shadow_locked_release_governance_entry_ready": attack_challenger_live_shadow_locked_release_governance_entry_ready,
        "attack_challenger_remote_monitoring_deployment_handoff_ready": attack_challenger_remote_monitoring_deployment_handoff_ready,
        "attack_challenger_next_step": attack_challenger_next_step,
        "attack_challenger_bridge_report": attack_challenger_bridge_report,
        "refresh_read": refresh_read,
        "operator_dashboard_json": str(
            latest_aliases.get(
                "btc_1d_operator_dashboard",
                "",
            )
        ),
        "operator_dashboard_html": str(
            latest_aliases.get(
                "btc_1d_operator_dashboard_html",
                "",
            )
        ),
    }


def _latest_summary(
    *,
    shadow_packet: dict,
    walk_forward: dict,
    eth_regression: dict,
    eth_symbol: str,
) -> dict:
    walk_forward_oos = walk_forward["overfitting"]["oos_metrics"]
    return {
        "candidate": shadow_packet["candidate"],
        "scope": "BTC-only",
        "carry": {
            "periods": shadow_packet["carry_reference_period"],
            "decision": shadow_packet["paper_validation_decision"],
            "sharpe": shadow_packet["paper_validation_metrics"].get("sharpe"),
            "cagr": shadow_packet["paper_validation_metrics"].get("cagr"),
            "max_drawdown": shadow_packet["paper_validation_metrics"].get("max_drawdown"),
        },
        "survivability": {
            "periods": shadow_packet["survivability_reference_period"],
            "decision": shadow_packet["survivability_validation_decision"],
            "sharpe": shadow_packet["survivability_validation_metrics"].get("sharpe"),
            "cagr": shadow_packet["survivability_validation_metrics"].get("cagr"),
            "max_drawdown": shadow_packet["survivability_validation_metrics"].get("max_drawdown"),
        },
        "walk_forward": {
            "passed": walk_forward["overfitting"]["passed"],
            "oos_sharpe": walk_forward_oos.get("sharpe"),
            "oos_cagr": walk_forward_oos.get("cagr"),
            "oos_max_drawdown": walk_forward_oos.get("max_drawdown"),
            "sensitivity_max_drift": walk_forward["overfitting"]["sensitivity_max_drift"],
            "unstable_parameters": walk_forward["overfitting"]["unstable_parameters"],
        },
        "friction": {
            "decision": shadow_packet["friction_validation_decision"],
            "heaviest_level_bps": shadow_packet["friction_validation_heaviest_level"].get("cost_bps"),
            "heaviest_level_sharpe": shadow_packet["friction_validation_heaviest_level"].get("sharpe"),
        },
        "eth_cross_check": {
            "symbol": eth_regression.get("config", {}).get("symbol", eth_symbol),
            "pass_rate": eth_regression["summary"]["pass_rate"],
            "pass_count": eth_regression["summary"]["pass_count"],
            "total_count": eth_regression["summary"]["total_count"],
        },
        "shadow_decision": shadow_packet["shadow_decision"],
    }


def _normalize_attack_challenger_handoff_fields(
    *,
    refresh_summary: dict[str, object],
    target: dict[str, object] | None = None,
) -> dict[str, object]:
    normalized = dict(target or {})
    normalized["deployment_monitoring_active"] = bool(
        refresh_summary.get(
            "deployment_monitoring_active",
            normalized.get("deployment_monitoring_active", False),
        )
    )
    normalized["attack_challenger_remote_monitoring_deployment_handoff_ready"] = bool(
        refresh_summary.get(
            "attack_challenger_remote_monitoring_deployment_handoff_ready",
            normalized.get(
                "attack_challenger_remote_monitoring_deployment_handoff_ready",
                False,
            ),
        )
    )
    normalized["attack_challenger_next_step"] = str(
        refresh_summary.get(
            "attack_challenger_next_step",
            normalized.get("attack_challenger_next_step", ""),
        )
    )
    normalized["attack_challenger_bridge_report"] = str(
        refresh_summary.get(
            "attack_challenger_bridge_report",
            normalized.get("attack_challenger_bridge_report", ""),
        )
    )
    return normalized


def _render_latest_summary_markdown(summary: dict) -> str:
    walk_forward = summary["walk_forward"]
    carry = summary["carry"]
    survivability = summary["survivability"]
    friction = summary["friction"]
    eth_cross_check = summary["eth_cross_check"]
    unstable = ", ".join(walk_forward["unstable_parameters"] or ["none"])
    return "\n".join(
        [
            "# BTC 1d Latest Summary",
            "",
            f"- Candidate: `{summary['candidate']}`",
            f"- Scope: `{summary['scope']}`",
            f"- Shadow decision: `{summary['shadow_decision']}`",
            "",
            "## Carry",
            f"- `{carry['periods']}`: `{carry['decision']}` | Sharpe `{carry['sharpe']:.4f}` | CAGR `{carry['cagr']:.4f}` | MDD `{carry['max_drawdown']:.4f}`",
            "",
            "## Survivability",
            f"- `{survivability['periods']}`: `{survivability['decision']}` | Sharpe `{survivability['sharpe']:.4f}` | CAGR `{survivability['cagr']:.4f}` | MDD `{survivability['max_drawdown']:.4f}`",
            "",
            "## Walk-Forward",
            f"- Passed: `{walk_forward['passed']}`",
            f"- OOS Sharpe `{walk_forward['oos_sharpe']:.4f}` | OOS CAGR `{walk_forward['oos_cagr']:.4f}` | OOS MDD `{walk_forward['oos_max_drawdown']:.4f}`",
            f"- Drift `{walk_forward['sensitivity_max_drift']:.4f}` | unstable `{unstable}`",
            "",
            "## Friction",
            f"- `{friction['heaviest_level_bps']}bps`: `{friction['decision']}` | Sharpe `{friction['heaviest_level_sharpe']:.4f}`",
            "",
            "## ETH Cross-Check",
            f"- `{eth_cross_check['symbol']}` pass rate `{eth_cross_check['pass_rate']}` ({eth_cross_check['pass_count']}/{eth_cross_check['total_count']})",
            "",
        ]
    )


def _write_latest_summary(*, analysis_dir: Path, summary: dict) -> dict[str, str]:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_latest_summary_{stamp}.json"
    md_path = analysis_dir / f"btc_1d_latest_summary_{stamp}.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(_render_latest_summary_markdown(summary), encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path)}


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


def _latest_index(
    *,
    summary: dict,
    latest_aliases: dict[str, str],
    contract_health: dict | None = None,
    research_stack_health_line: str = "",
    combined_health_line: str = "",
    paper_nightly_health_line: str = "",
    execution_health_line: str = "",
    execution_contract_health_line: str = "",
    execution_contract_read: str = "",
    execution_contract_aligned: bool = False,
    execution_contract_paper_ledger_snapshot_summary_aligned: bool = False,
    execution_contract_paper_execution_contract_checked_aligned_entry_aligned: bool = False,
    execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: bool = False,
    execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: bool = False,
    execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: bool = False,
    execution_contract_paper_execution_contract_checked_aligned_summary_aligned: bool = False,
    execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: bool = False,
    execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: bool = False,
    execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: bool = False,
    paper_execution_contract_checked: bool = False,
    paper_execution_contract_aligned: bool = False,
    paper_execution_contract_checked_aligned: bool = False,
    paper_execution_contract_aligned_aligned: bool = False,
    paper_execution_contract_checked_summary_aligned: bool = False,
    paper_execution_contract_aligned_summary_aligned: bool = False,
    paper_execution_contract_checked_aligned_entry_aligned: bool = False,
    paper_execution_contract_aligned_aligned_entry_aligned: bool = False,
    paper_execution_contract_checked_summary_aligned_entry_aligned: bool = False,
    paper_execution_contract_aligned_summary_aligned_entry_aligned: bool = False,
    paper_execution_contract_checked_aligned_summary_aligned: bool = False,
    paper_execution_contract_aligned_aligned_summary_aligned: bool = False,
    paper_execution_contract_checked_summary_aligned_summary_aligned: bool = False,
    paper_execution_contract_aligned_summary_aligned_summary_aligned: bool = False,
    paper_execution_read: str = "",
    paper_exit_duplicate_run: bool = False,
    paper_ledger_consistent: bool = False,
    paper_ledger_snapshot: dict[str, object] | None = None,
    attack_challenger_candidate: str = "",
    attack_challenger_role_assignment: str = "",
    attack_challenger_promotion_ready: bool = False,
    attack_challenger_next_step: str = "",
    attack_challenger_paper_validation_cagr: float | None = None,
    attack_challenger_paper_validation_max_drawdown: float | None = None,
    attack_challenger_walk_forward_sensitivity_max_drift: float | None = None,
    attack_challenger_friction_final_decision: str = "",
    attack_challenger_bridge_entry_ready: bool = False,
    attack_challenger_bridge_queue_lane: str = "",
    attack_challenger_execution_contract_entry_ready: bool = False,
    attack_challenger_execution_contract_queue_lane: str = "",
    attack_challenger_operator_stack_handoff_ready: bool = False,
    attack_challenger_operator_stack_handoff_lane: str = "",
    attack_challenger_operator_runbook_candidate_entry_ready: bool = False,
    attack_challenger_operator_runbook_candidate_entry_lane: str = "",
    attack_challenger_operator_runbook_execution_entry_ready: bool = False,
    attack_challenger_operator_runbook_execution_entry_lane: str = "",
    attack_challenger_live_readiness_review_ready: bool = False,
    attack_challenger_live_readiness_review_lane: str = "",
    attack_challenger_live_shadow_activation_review_ready: bool = False,
    attack_challenger_live_shadow_activation_review_lane: str = "",
    attack_challenger_live_candidate_entry_ready: bool = False,
    attack_challenger_live_candidate_entry_lane: str = "",
    attack_challenger_live_operator_paper_entry_ready: bool = False,
    attack_challenger_live_operator_paper_entry_lane: str = "",
    attack_challenger_live_shadow_governance_review_ready: bool = False,
    attack_challenger_live_shadow_governance_review_lane: str = "",
    attack_challenger_live_governed_shadow_entry_ready: bool = False,
    attack_challenger_live_governed_shadow_entry_lane: str = "",
    attack_challenger_live_shadow_candidate_paper_review_ready: bool = False,
    attack_challenger_live_shadow_candidate_paper_review_lane: str = "",
    attack_challenger_live_shadow_candidate_governance_lock_ready: bool = False,
    attack_challenger_live_shadow_candidate_governance_lock_lane: str = "",
    attack_challenger_live_shadow_locked_entry_ready: bool = False,
    attack_challenger_live_shadow_locked_entry_lane: str = "",
    attack_challenger_live_shadow_locked_candidate_review_ready: bool = False,
    attack_challenger_live_shadow_locked_candidate_review_lane: str = "",
    attack_challenger_live_shadow_locked_candidate_release_review_ready: bool = False,
    attack_challenger_live_shadow_locked_candidate_release_review_lane: str = "",
    attack_challenger_live_shadow_locked_release_entry_ready: bool = False,
    attack_challenger_live_shadow_locked_release_entry_lane: str = "",
    attack_challenger_live_shadow_locked_release_candidate_review_ready: bool = False,
    attack_challenger_live_shadow_locked_release_candidate_review_lane: str = "",
    attack_challenger_live_shadow_locked_release_governance_check_ready: bool = False,
    attack_challenger_live_shadow_locked_release_governance_check_lane: str = "",
    attack_challenger_live_shadow_locked_release_governance_entry_ready: bool = False,
    attack_challenger_live_shadow_locked_release_governance_entry_lane: str = "",
    attack_challenger_remote_monitoring_deployment_handoff_ready: bool = False,
    attack_challenger_remote_monitoring_deployment_handoff_lane: str = "",
    attack_challenger_bridge_report: str = "",
) -> dict:
    standard_check_order = ["practical", "research", "contract", "brief"]
    regression_lock_test = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    practical_gate_path = latest_aliases.get("btc_1d_practical_promotion_gate")
    practical = {"decision": "unknown", "ok": False, "caveat_count": 0}
    if practical_gate_path:
        gate_path = Path(practical_gate_path)
        if gate_path.exists():
            practical_gate = json.loads(gate_path.read_text(encoding="utf-8-sig"))
            practical = {
                "decision": practical_gate.get("decision", "unknown"),
                "status_label": practical_gate.get("status_label", practical_gate.get("decision", "unknown")),
                "ok": practical_gate.get("ok", False),
                "caveat_count": len(practical_gate.get("caveats", [])),
            }
    quick_read_contract_partitioned = bool(
        (contract_health or {}).get("contracts_are_well_partitioned", False)
    )
    contract_health_aligned = bool(
        (contract_health or {}).get("contract_health_aligned", False)
    )
    operator_verdict = _derive_operator_verdict(
        shadow_decision=str(summary["shadow_decision"]),
        dashboard_ready=bool(summary["shadow_decision"] == "ready"),
        quick_read_contract_partitioned=quick_read_contract_partitioned,
        contract_health_aligned=contract_health_aligned,
        execution_contract_aligned=execution_contract_aligned,
        paper_execution_contract_aligned=paper_execution_contract_aligned,
        paper_ledger_consistent=paper_ledger_consistent,
    )
    deployment_monitoring_active = bool(
        attack_challenger_remote_monitoring_deployment_handoff_ready
        and attack_challenger_next_step
        == ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
        and operator_verdict == "shadow_monitoring_ready"
    )
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
        "practical_status_label": practical["status_label"],
        "contract_health_operating_contract_aligned": bool(
            (contract_health or {}).get("operating_contract_aligned", False)
        ),
        "contract_health_paper_execution_contract_aligned": bool(
            (contract_health or {}).get("paper_execution_contract_aligned", False)
        ),
        "contract_health_aligned": contract_health_aligned,
        "contract_health_contracts_are_well_partitioned": quick_read_contract_partitioned,
        "research_stack_status": research_stack_health_line,
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
        "paper_ledger_snapshot": paper_ledger_snapshot or {},
        "paper_ledger_snapshot_read": _render_paper_ledger_snapshot_read(paper_ledger_snapshot),
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
        "research_stack_health_line": research_stack_health_line,
        "operating_brief": latest_aliases.get("btc_1d_operating_brief"),
        "operating_brief_txt": latest_aliases.get("btc_1d_operating_brief_txt"),
        "operating_brief_md": latest_aliases.get("btc_1d_operating_brief_md"),
        "practical_scorecard": latest_aliases.get("btc_1d_practical_scorecard"),
        "practical_scorecard_md": latest_aliases.get("btc_1d_practical_scorecard_md"),
        "practical_promotion_gate": latest_aliases.get("btc_1d_practical_promotion_gate"),
        "practical_promotion_gate_md": latest_aliases.get("btc_1d_practical_promotion_gate_md"),
        "research_stack_operating_brief": latest_aliases.get("btc_1d_research_stack_operating_brief"),
        "research_stack_operating_brief_md": latest_aliases.get("btc_1d_research_stack_operating_brief_md"),
        "quick_read_contract_screen": latest_aliases.get("btc_1d_quick_read_contract_screen"),
        "quick_read_contract_screen_md": latest_aliases.get("btc_1d_quick_read_contract_screen_md"),
        "execution_contract_screen": latest_aliases.get("btc_1d_execution_contract_screen"),
        "execution_contract_screen_md": latest_aliases.get("btc_1d_execution_contract_screen_md"),
        "execution_meta_contract_test_index": latest_aliases.get("btc_1d_execution_meta_contract_test_index"),
        "execution_meta_contract_test_index_md": latest_aliases.get("btc_1d_execution_meta_contract_test_index_md"),
        "meta_contract_screen": latest_aliases.get("btc_1d_meta_contract_screen"),
        "meta_contract_screen_md": latest_aliases.get("btc_1d_meta_contract_screen_md"),
        "paper_nightly_summary": latest_aliases.get("btc_1d_paper_nightly_summary"),
        "paper_nightly_summary_md": latest_aliases.get("btc_1d_paper_nightly_summary_md"),
        "latest_summary": latest_aliases.get("btc_1d_latest_summary"),
        "latest_summary_md": latest_aliases.get("btc_1d_latest_summary_md"),
        "shadow_packet": latest_aliases.get("btc_1d_shadow_packet"),
        "shadow_packet_md": latest_aliases.get("btc_1d_shadow_packet_md"),
        "status_board": latest_aliases.get("btc_1d_candidate_status_board"),
        "status_board_md": latest_aliases.get("btc_1d_candidate_status_board_md"),
        "baseline_freeze": latest_aliases.get("btc_1d_baseline_freeze"),
        "baseline_freeze_md": latest_aliases.get("btc_1d_baseline_freeze_md"),
        "shadow_readiness": latest_aliases.get("btc_1d_shadow_readiness"),
        "shadow_readiness_md": latest_aliases.get("btc_1d_shadow_readiness_md"),
        "walk_forward": latest_aliases.get("btc_1d_walk_forward_diagnostic"),
        "walk_forward_md": latest_aliases.get("btc_1d_walk_forward_diagnostic_md"),
        "friction": latest_aliases.get("btc_1d_low_vol_cap_friction"),
        "friction_md": latest_aliases.get("btc_1d_low_vol_cap_friction_md"),
        "checks": {
            "carry": summary["carry"],
            "survivability": summary["survivability"],
            "walk_forward": summary["walk_forward"],
            "friction": summary["friction"],
            "eth_cross_check": summary["eth_cross_check"],
        },
    }


def _render_latest_index_markdown(index_payload: dict) -> str:
    checks = index_payload["checks"]
    carry = checks["carry"]
    survivability = checks["survivability"]
    walk_forward = checks["walk_forward"]
    friction = checks["friction"]
    eth_cross_check = checks["eth_cross_check"]
    practical = index_payload.get(
        "practical",
        {"decision": "unknown", "status_label": "unknown", "ok": False, "caveat_count": 0},
    )
    return "\n".join(
        [
            "# BTC 1d Operating Index",
            "",
            f"- Candidate: `{index_payload['candidate']}`",
            f"- Scope: `{index_payload['scope']}`",
            f"- Shadow decision: `{index_payload['shadow_decision']}`",
            f"- Operator verdict: `{index_payload.get('operator_verdict', 'validation_in_progress')}`",
            f"- Deployment monitoring active: `{index_payload.get('deployment_monitoring_active', False)}`",
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
                f"- Execution health: `{index_payload['execution_health_line']}`"
                if index_payload.get("execution_health_line")
                else ""
            ),
            (
                f"- Execution contract read: `{index_payload['execution_contract_read']}`"
                if index_payload.get("execution_contract_read")
                else ""
            ),
            f"- Execution contract aligned: `{index_payload.get('execution_contract_aligned', False)}`",
            (
                "- Execution contract paper ledger snapshot summary aligned: "
                f"`{index_payload.get('execution_contract_paper_ledger_snapshot_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked aligned entry aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_checked_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned aligned entry aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked summary aligned entry aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned summary aligned entry aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked aligned summary aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_checked_aligned_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned aligned summary aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked summary aligned summary aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned summary aligned summary aligned: "
                f"`{index_payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
            ),
            f"- Paper execution contract checked: `{index_payload.get('paper_execution_contract_checked', False)}`",
            f"- Paper execution contract aligned: `{index_payload.get('paper_execution_contract_aligned', False)}`",
            (
                "- Paper execution contract checked aligned: "
                f"`{index_payload.get('paper_execution_contract_checked_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned aligned: "
                f"`{index_payload.get('paper_execution_contract_aligned_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked summary aligned: "
                f"`{index_payload.get('paper_execution_contract_checked_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned summary aligned: "
                f"`{index_payload.get('paper_execution_contract_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked aligned entry aligned: "
                f"`{index_payload.get('paper_execution_contract_checked_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned aligned entry aligned: "
                f"`{index_payload.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked summary aligned entry aligned: "
                f"`{index_payload.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned summary aligned entry aligned: "
                f"`{index_payload.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked aligned summary aligned: "
                f"`{index_payload.get('paper_execution_contract_checked_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned aligned summary aligned: "
                f"`{index_payload.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked summary aligned summary aligned: "
                f"`{index_payload.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned summary aligned summary aligned: "
                f"`{index_payload.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
            ),
            (
                f"- Attack challenger: `{index_payload.get('attack_challenger_candidate', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger role: `{index_payload.get('attack_challenger_role_assignment', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger promotion ready: `{index_payload.get('attack_challenger_promotion_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger bridge entry ready: `{index_payload.get('attack_challenger_bridge_entry_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger queue lane: `{index_payload.get('attack_challenger_bridge_queue_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger execution contract entry ready: `{index_payload.get('attack_challenger_execution_contract_entry_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger execution contract queue lane: `{index_payload.get('attack_challenger_execution_contract_queue_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger operator stack handoff ready: `{index_payload.get('attack_challenger_operator_stack_handoff_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger operator stack handoff lane: `{index_payload.get('attack_challenger_operator_stack_handoff_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger operator runbook candidate entry ready: `{index_payload.get('attack_challenger_operator_runbook_candidate_entry_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger operator runbook candidate entry lane: `{index_payload.get('attack_challenger_operator_runbook_candidate_entry_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger operator runbook execution entry ready: `{index_payload.get('attack_challenger_operator_runbook_execution_entry_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger operator runbook execution entry lane: `{index_payload.get('attack_challenger_operator_runbook_execution_entry_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live readiness review ready: `{index_payload.get('attack_challenger_live_readiness_review_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live readiness review lane: `{index_payload.get('attack_challenger_live_readiness_review_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live shadow activation review ready: `{index_payload.get('attack_challenger_live_shadow_activation_review_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live shadow activation review lane: `{index_payload.get('attack_challenger_live_shadow_activation_review_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live candidate entry ready: `{index_payload.get('attack_challenger_live_candidate_entry_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live candidate entry lane: `{index_payload.get('attack_challenger_live_candidate_entry_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live operator paper entry ready: `{index_payload.get('attack_challenger_live_operator_paper_entry_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live operator paper entry lane: `{index_payload.get('attack_challenger_live_operator_paper_entry_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live shadow governance review ready: `{index_payload.get('attack_challenger_live_shadow_governance_review_ready', False)}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger live shadow governance review lane: `{index_payload.get('attack_challenger_live_shadow_governance_review_lane', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                f"- Attack challenger next step: `{index_payload.get('attack_challenger_next_step', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            (
                "- Attack challenger profile: "
                f"`cagr={index_payload.get('attack_challenger_paper_validation_cagr')} | "
                f"mdd={index_payload.get('attack_challenger_paper_validation_max_drawdown')} | "
                f"drift={index_payload.get('attack_challenger_walk_forward_sensitivity_max_drift')} | "
                f"friction={index_payload.get('attack_challenger_friction_final_decision', '')}`"
                if index_payload.get("attack_challenger_candidate")
                else ""
            ),
            f"- Practical status: `{practical['status_label']}` | ok `{practical['ok']}` | caveats `{practical['caveat_count']}`",
            (
                f"- Combined health: `{index_payload['combined_health_line']}`"
                if index_payload.get("combined_health_line")
                else ""
            ),
            (
                f"- Research stack status: `{index_payload['research_stack_health_line']}`"
                if index_payload.get("research_stack_health_line")
                else ""
            ),
            (
                f"- Paper nightly: `{index_payload['paper_nightly_health_line']}`"
                if index_payload.get("paper_nightly_health_line")
                else ""
            ),
            f"- Paper exit duplicate run: `{index_payload.get('paper_exit_duplicate_run', False)}`",
            f"- Paper ledger consistent: `{index_payload.get('paper_ledger_consistent', False)}`",
            f"- Paper ledger snapshot: `{index_payload.get('paper_ledger_snapshot_read', _render_paper_ledger_snapshot_read(index_payload.get('paper_ledger_snapshot')) )}`",
            f"- Carry `{carry['periods']}`: `{carry['decision']}` | Sharpe `{carry['sharpe']:.4f}`",
            f"- Survivability `{survivability['periods']}`: `{survivability['decision']}` | Sharpe `{survivability['sharpe']:.4f}`",
            f"- Walk-forward: `{'PASS' if walk_forward['passed'] else 'FAIL'}` | OOS Sharpe `{walk_forward['oos_sharpe']:.4f}` | Drift `{walk_forward['sensitivity_max_drift']:.4f}`",
            f"- Friction `{friction['heaviest_level_bps']}bps`: `{friction['decision']}` | Sharpe `{friction['heaviest_level_sharpe']:.4f}`",
            f"- ETH cross-check: `{eth_cross_check['symbol']}` pass rate `{eth_cross_check['pass_rate']}` ({eth_cross_check['pass_count']}/{eth_cross_check['total_count']})",
            "",
            "## Quick-Read Contract",
            f"- `{index_payload['quick_read_contract_screen_md']}`",
            f"- `{index_payload['execution_contract_screen_md']}`",
            f"- `{index_payload['execution_meta_contract_test_index_md']}`",
            f"- `{index_payload['meta_contract_screen_md']}`",
            "",
            "## Promotion Bridge",
            (
                "- Attack challenger bridge report: "
                f"`{index_payload.get('attack_challenger_bridge_report', '')}`"
                if index_payload.get("attack_challenger_bridge_report")
                else "- none"
            ),
            "",
            "## Open First",
            f"- `{index_payload['operating_brief_md']}`",
            f"- `{index_payload['operating_brief_txt']}`",
            f"- `{index_payload['operating_brief']}`",
            "",
            "## Latest Stable Pointers",
            f"- Operating brief JSON: `{index_payload['operating_brief']}`",
            f"- Operating brief TXT: `{index_payload['operating_brief_txt']}`",
            f"- Operating brief MD: `{index_payload['operating_brief_md']}`",
            f"- Practical scorecard JSON: `{index_payload['practical_scorecard']}`",
            f"- Practical scorecard MD: `{index_payload['practical_scorecard_md']}`",
            f"- Practical promotion gate JSON: `{index_payload['practical_promotion_gate']}`",
            f"- Practical promotion gate MD: `{index_payload['practical_promotion_gate_md']}`",
            f"- Research stack brief JSON: `{index_payload['research_stack_operating_brief']}`",
            f"- Research stack brief MD: `{index_payload['research_stack_operating_brief_md']}`",
            f"- Quick-read contract screen JSON: `{index_payload['quick_read_contract_screen']}`",
            f"- Quick-read contract screen MD: `{index_payload['quick_read_contract_screen_md']}`",
            f"- Execution contract screen JSON: `{index_payload['execution_contract_screen']}`",
            f"- Execution contract screen MD: `{index_payload['execution_contract_screen_md']}`",
            f"- Execution meta contract test index JSON: `{index_payload['execution_meta_contract_test_index']}`",
            f"- Execution meta contract test index MD: `{index_payload['execution_meta_contract_test_index_md']}`",
            f"- Meta contract screen JSON: `{index_payload['meta_contract_screen']}`",
            f"- Meta contract screen MD: `{index_payload['meta_contract_screen_md']}`",
            f"- Paper nightly summary JSON: `{index_payload.get('paper_nightly_summary')}`",
            f"- Paper nightly summary MD: `{index_payload.get('paper_nightly_summary_md')}`",
            (
                "- Attack challenger bridge report JSON: "
                f"`{index_payload.get('attack_challenger_bridge_report', '')}`"
                if index_payload.get("attack_challenger_bridge_report")
                else ""
            ),
            f"- Summary JSON: `{index_payload['latest_summary']}`",
            f"- Summary MD: `{index_payload['latest_summary_md']}`",
            f"- Shadow packet JSON: `{index_payload['shadow_packet']}`",
            f"- Shadow packet MD: `{index_payload['shadow_packet_md']}`",
            f"- Status board JSON: `{index_payload['status_board']}`",
            f"- Status board MD: `{index_payload['status_board_md']}`",
            f"- Baseline freeze JSON: `{index_payload['baseline_freeze']}`",
            f"- Baseline freeze MD: `{index_payload['baseline_freeze_md']}`",
            f"- Shadow readiness JSON: `{index_payload['shadow_readiness']}`",
            f"- Shadow readiness MD: `{index_payload['shadow_readiness_md']}`",
            f"- Walk-forward JSON: `{index_payload['walk_forward']}`",
            f"- Walk-forward MD: `{index_payload['walk_forward_md']}`",
            f"- Friction JSON: `{index_payload['friction']}`",
            f"- Friction MD: `{index_payload['friction_md']}`",
            "",
        ]
    )


def _write_latest_index(*, analysis_dir: Path, index_payload: dict) -> dict[str, str]:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_operating_index_{stamp}.json"
    md_path = analysis_dir / f"btc_1d_operating_index_{stamp}.md"
    json_payload = json.dumps(index_payload, indent=2)
    md_payload = _render_latest_index_markdown(index_payload)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    (analysis_dir / "btc_1d_operating_index_latest.json").write_text(json_payload, encoding="utf-8")
    (analysis_dir / "btc_1d_operating_index_md_latest.md").write_text(md_payload, encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path)}


def _write_operating_brief(*, analysis_dir: Path, brief: dict) -> dict[str, str]:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_operating_brief_{stamp}.json"
    txt_path = analysis_dir / f"btc_1d_operating_brief_{stamp}.txt"
    md_path = analysis_dir / f"btc_1d_operating_brief_{stamp}.md"
    json_payload = json.dumps(brief, indent=2)
    txt_payload = render_operating_brief(brief)
    md_payload = render_operating_brief_markdown(brief)
    json_path.write_text(json_payload, encoding="utf-8")
    txt_path.write_text(txt_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    (analysis_dir / "btc_1d_operating_brief_latest.json").write_text(json_payload, encoding="utf-8")
    (analysis_dir / "btc_1d_operating_brief_txt_latest.txt").write_text(txt_payload, encoding="utf-8")
    (analysis_dir / "btc_1d_operating_brief_md_latest.md").write_text(md_payload, encoding="utf-8")
    return {"json": str(json_path), "txt": str(txt_path), "md": str(md_path)}


def _publish_practical_outputs(*, analysis_dir: Path) -> dict[str, str]:
    scorecard_json = analysis_dir / "btc_1d_practical_scorecard_latest.json"
    scorecard_md = analysis_dir / "btc_1d_practical_scorecard_md_latest.md"
    gate_json = analysis_dir / "btc_1d_practical_promotion_gate_latest.json"
    gate_md = analysis_dir / "btc_1d_practical_promotion_gate_md_latest.md"
    try:
        with redirect_stdout(io.StringIO()):
            run_practical_scorecard_main(["--analysis-dir", str(analysis_dir)])
            run_practical_promotion_gate_main(["--analysis-dir", str(analysis_dir)])
    except FileNotFoundError as exc:
        payload = {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "status": "unavailable",
            "decision": "not_ready",
            "ok": False,
            "caveat_count": 1,
            "reason": str(exc),
            "note": "Optional practical scorecard artifacts are absent; shadow update continues for current operating-readiness outputs.",
        }
        scorecard_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        scorecard_md.write_text(
            "\n".join(
                [
                    "# BTC 1d Practical Scorecard",
                    "",
                    "- Status: `unavailable`",
                    "- Decision: `not_ready`",
                    f"- Reason: `{exc}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        gate_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        gate_md.write_text(
            "\n".join(
                [
                    "# BTC 1d Practical Promotion Gate",
                    "",
                    "- Status: `unavailable`",
                    "- Decision: `not_ready`",
                    f"- Reason: `{exc}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        with redirect_stdout(io.StringIO()):
            run_practical_promotion_gate_main(["--analysis-dir", str(analysis_dir)])
    return {
        "btc_1d_practical_scorecard": str(scorecard_json),
        "btc_1d_practical_scorecard_md": str(scorecard_md),
        "btc_1d_practical_promotion_gate": str(gate_json),
        "btc_1d_practical_promotion_gate_md": str(gate_md),
    }


def _publish_research_outputs(*, analysis_dir: Path) -> dict[str, str]:
    with redirect_stdout(io.StringIO()):
        research_stack_operating_brief_script.ANALYSIS_DIR = analysis_dir
        research_stack_operating_brief_script.main()
        quick_read_contract_screen_script.ANALYSIS_DIR = analysis_dir
        quick_read_contract_screen_script.main()
        meta_contract_screen_script.ANALYSIS_DIR = analysis_dir
        meta_contract_screen_script.main()
    return {
        "btc_1d_research_stack_operating_brief": str(
            analysis_dir / "btc_1d_research_stack_operating_brief_latest.json"
        ),
        "btc_1d_research_stack_operating_brief_md": str(
            analysis_dir / "btc_1d_research_stack_operating_brief_md_latest.md"
        ),
        "btc_1d_quick_read_contract_screen": str(
            analysis_dir / "btc_1d_quick_read_contract_screen_latest.json"
        ),
        "btc_1d_quick_read_contract_screen_md": str(
            analysis_dir / "btc_1d_quick_read_contract_screen_md_latest.md"
        ),
        "btc_1d_meta_contract_screen": str(
            analysis_dir / "btc_1d_meta_contract_screen_latest.json"
        ),
        "btc_1d_meta_contract_screen_md": str(
            analysis_dir / "btc_1d_meta_contract_screen_md_latest.md"
        ),
    }


def _publish_execution_outputs(*, analysis_dir: Path) -> dict[str, str]:
    with redirect_stdout(io.StringIO()):
        execution_meta_contract_test_index_script.ANALYSIS_DIR = analysis_dir
        execution_meta_contract_test_index_script.main()
        execution_contract_screen_script.ANALYSIS_DIR = analysis_dir
        execution_contract_screen_script.main()
    return {
        "btc_1d_execution_contract_screen": str(
            analysis_dir / "btc_1d_execution_contract_screen_latest.json"
        ),
        "btc_1d_execution_contract_screen_md": str(
            analysis_dir / "btc_1d_execution_contract_screen_md_latest.md"
        ),
        "btc_1d_execution_meta_contract_test_index": str(
            analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json"
        ),
        "btc_1d_execution_meta_contract_test_index_md": str(
            analysis_dir / "btc_1d_execution_meta_contract_test_index_md_latest.md"
        ),
    }


def _publish_attack_challenger_outputs(*, analysis_dir: Path) -> dict[str, str]:
    with redirect_stdout(io.StringIO()):
        live_shadow_locked_release_entry_script.ANALYSIS_DIR = analysis_dir
        live_shadow_locked_release_entry_script.main()
        live_shadow_locked_release_candidate_review_script.ANALYSIS_DIR = analysis_dir
        live_shadow_locked_release_candidate_review_script.main()
        live_shadow_locked_release_governance_check_script.ANALYSIS_DIR = analysis_dir
        live_shadow_locked_release_governance_check_script.main()
        live_shadow_locked_release_governance_entry_script.ANALYSIS_DIR = analysis_dir
        live_shadow_locked_release_governance_entry_script.main()
        remote_monitoring_deployment_handoff_script.ANALYSIS_DIR = analysis_dir
        remote_monitoring_deployment_handoff_script.main()
    return {
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry_latest.json"
        ),
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry_md": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_entry_md_latest.md"
        ),
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review_latest.json"
        ),
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review_md": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_candidate_review_md_latest.md"
        ),
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_check": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_check_latest.json"
        ),
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_check_md": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_check_md_latest.md"
        ),
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json"
        ),
        "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_md": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_md_latest.md"
        ),
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff": str(
            build_attack_challenger_remote_monitoring_deployment_handoff_path(analysis_dir)
        ),
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md": str(
            analysis_dir
            / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md"
        ),
    }


def _refresh_contract_artifacts_after_paper(
    *,
    analysis_dir: Path,
    latest_aliases: dict[str, str],
) -> dict[str, str]:
    refreshed_aliases = dict(latest_aliases)
    refreshed_aliases.update(
        _write_latest_aliases(
            analysis_dir=analysis_dir,
            paths=_publish_research_outputs(analysis_dir=analysis_dir),
        )
    )
    refreshed_aliases.update(
        _write_latest_aliases(
            analysis_dir=analysis_dir,
            paths=_publish_execution_outputs(analysis_dir=analysis_dir),
        )
    )
    return refreshed_aliases


def _load_execution_contract_state(
    *,
    analysis_dir: Path,
    latest_aliases: dict[str, str],
    paper_execution_read: str,
    execution_health_line: str,
) -> dict[str, object]:
    execution_contract_screen_path = Path(
        latest_aliases.get(
            "btc_1d_execution_contract_screen",
            str(analysis_dir / "btc_1d_execution_contract_screen_latest.json"),
        )
    )
    execution_contract_aligned = False
    execution_contract_read = render_execution_contract_read(
        execution_contract_aligned=False,
        paper_execution_read=paper_execution_read,
    )
    execution_contract_paper_ledger_snapshot_summary_aligned = False
    execution_contract_paper_execution_contract_checked_aligned_entry_aligned = False
    execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = False
    execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = False
    execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = False
    execution_contract_paper_execution_contract_checked_aligned_summary_aligned = False
    execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = False
    execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = False
    execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = False
    if execution_contract_screen_path.exists():
        execution_contract_payload = json.loads(
            execution_contract_screen_path.read_text(encoding="utf-8-sig")
        )
        execution_contract_summary = execution_contract_payload.get("execution_contract_summary", {})
        execution_contract_verdict = execution_contract_payload.get("execution_contract_verdict", {})
        execution_contract_aligned = bool(execution_contract_verdict.get("execution_contract_aligned", False))
        execution_contract_read = str(
            execution_contract_summary.get(
                "execution_contract_read",
                render_execution_contract_read(
                    execution_contract_aligned=execution_contract_aligned,
                    paper_execution_read=paper_execution_read,
                ),
            )
        )
        execution_contract_paper_ledger_snapshot_summary_aligned = bool(
            execution_contract_summary.get("paper_ledger_snapshot_summary_aligned", False)
        )
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_aligned_entry_aligned", False
            )
        )
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_aligned_entry_aligned", False
            )
        )
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_summary_aligned_entry_aligned", False
            )
        )
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_summary_aligned_entry_aligned", False
            )
        )
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_aligned_summary_aligned", False
            )
        )
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_aligned_summary_aligned", False
            )
        )
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_checked_summary_aligned_summary_aligned", False
            )
        )
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
            execution_contract_summary.get(
                "paper_execution_contract_aligned_summary_aligned_summary_aligned", False
            )
        )
    execution_contract_health_line = render_execution_contract_health_line(
        execution_health_line=execution_health_line,
        execution_contract_read=str(execution_contract_read),
    )
    return {
        "execution_contract_aligned": execution_contract_aligned,
        "execution_contract_read": str(execution_contract_read),
        "execution_contract_health_line": execution_contract_health_line,
        "execution_contract_paper_ledger_snapshot_summary_aligned": (
            execution_contract_paper_ledger_snapshot_summary_aligned
        ),
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
    }


def _write_operator_dashboard_artifacts(
    *,
    analysis_dir: Path,
    latest_aliases: dict[str, str],
) -> dict[str, str]:
    report = operator_dashboard_script.build_dashboard(analysis_dir)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_operator_dashboard_{stamp}.json"
    md_path = analysis_dir / f"btc_1d_operator_dashboard_{stamp}.md"
    html_path = analysis_dir / f"btc_1d_operator_dashboard_{stamp}.html"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(operator_dashboard_script.render_markdown(report), encoding="utf-8")
    html_path.write_text(operator_dashboard_script.render_html(report), encoding="utf-8")
    refreshed_aliases = dict(latest_aliases)
    refreshed_aliases.update(
        operator_dashboard_script._write_latest_aliases(json_path, md_path, html_path)
    )
    return refreshed_aliases


def _write_latest_aliases(*, analysis_dir: Path, paths: dict[str, str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for key, source in paths.items():
        if not source:
            continue
        source_path = Path(source)
        latest_path = analysis_dir / f"{key}_latest{source_path.suffix}"
        if source_path.resolve() != latest_path.resolve():
            shutil.copyfile(source_path, latest_path)
        aliases[key] = str(latest_path)
    return aliases


def _render_combined_health_line(*, practical_health: dict, research_stack_health: dict) -> str:
    practical_line = render_practical_health_line(practical_health)
    research_line = render_research_stack_health_line(research_stack_health)
    return f"{practical_line} || {research_line}"


def _render_execution_health_line(*, combined_health_line: str, paper_nightly_health_line: str = "") -> str:
    if paper_nightly_health_line:
        return f"{combined_health_line} || {paper_nightly_health_line}"
    return combined_health_line


def _load_latest_summary_payload(*, analysis_dir: Path) -> dict:
    summary_path = analysis_dir / "btc_1d_latest_summary_latest.json"
    if not summary_path.exists():
        raise FileNotFoundError(
            f"Missing latest summary artifact: {summary_path}"
        )
    return json.loads(summary_path.read_text(encoding="utf-8-sig"))


def _load_paper_nightly_state(*, analysis_dir: Path) -> dict[str, object]:
    summary_path = analysis_dir / "btc_1d_paper_nightly_summary_latest.json"
    defaults: dict[str, object] = {
        "paper_nightly": None,
        "paper_nightly_health_line": "",
        "paper_execution_contract_checked": False,
        "paper_execution_contract_aligned": False,
        "paper_execution_contract_checked_aligned": False,
        "paper_execution_contract_aligned_aligned": False,
        "paper_execution_contract_checked_summary_aligned": False,
        "paper_execution_contract_aligned_summary_aligned": False,
        "paper_execution_contract_checked_aligned_entry_aligned": False,
        "paper_execution_contract_aligned_aligned_entry_aligned": False,
        "paper_execution_contract_checked_summary_aligned_entry_aligned": False,
        "paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
        "paper_execution_contract_checked_aligned_summary_aligned": False,
        "paper_execution_contract_aligned_aligned_summary_aligned": False,
        "paper_execution_contract_checked_summary_aligned_summary_aligned": False,
        "paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
        "paper_execution_read": "",
        "paper_exit_duplicate_run": False,
        "paper_ledger_consistent": False,
        "paper_ledger_snapshot": {},
    }
    if not summary_path.exists():
        return defaults

    paper_nightly = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    return {
        "paper_nightly": paper_nightly,
        "paper_nightly_health_line": render_paper_nightly_health_line(paper_nightly),
        "paper_execution_contract_checked": bool(paper_nightly.get("execution_contract_checked", False)),
        "paper_execution_contract_aligned": bool(paper_nightly.get("execution_contract_aligned", False)),
        "paper_execution_contract_checked_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_aligned",
            "execution_contract_paper_execution_contract_checked_aligned",
        ),
        "paper_execution_contract_aligned_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned",
        ),
        "paper_execution_contract_checked_summary_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_summary_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned",
        ),
        "paper_execution_contract_aligned_summary_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned",
        ),
        "paper_execution_contract_checked_aligned_entry_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
        ),
        "paper_execution_contract_aligned_aligned_entry_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
        ),
        "paper_execution_contract_checked_summary_aligned_entry_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_summary_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
        ),
        "paper_execution_contract_aligned_summary_aligned_entry_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
        ),
        "paper_execution_contract_checked_aligned_summary_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
        ),
        "paper_execution_contract_aligned_aligned_summary_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
        ),
        "paper_execution_contract_checked_summary_aligned_summary_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_summary_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
        ),
        "paper_execution_contract_aligned_summary_aligned_summary_aligned": _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
        ),
        "paper_execution_read": str(paper_nightly.get("paper_execution_read", "")),
        "paper_exit_duplicate_run": bool(paper_nightly.get("paper_exit_duplicate_run", False)),
        "paper_ledger_consistent": bool(paper_nightly.get("paper_ledger_consistent", False)),
        "paper_ledger_snapshot": dict(paper_nightly.get("paper_ledger_snapshot", {}) or {}),
    }


def refresh_operator_stack(*, analysis_dir: Path, sync_passes: int = 3) -> dict[str, object]:
    latest_summary = _load_latest_summary_payload(analysis_dir=analysis_dir)
    paper_state = _load_paper_nightly_state(analysis_dir=analysis_dir)
    latest_aliases: dict[str, str] = {
        "btc_1d_latest_summary": str(analysis_dir / "btc_1d_latest_summary_latest.json"),
        "btc_1d_latest_summary_md": str(analysis_dir / "btc_1d_latest_summary_md_latest.md"),
        "btc_1d_operating_index": str(analysis_dir / "btc_1d_operating_index_latest.json"),
        "btc_1d_operating_index_md": str(analysis_dir / "btc_1d_operating_index_md_latest.md"),
        "btc_1d_operating_brief": str(analysis_dir / "btc_1d_operating_brief_latest.json"),
        "btc_1d_operating_brief_txt": str(analysis_dir / "btc_1d_operating_brief_txt_latest.txt"),
        "btc_1d_operating_brief_md": str(analysis_dir / "btc_1d_operating_brief_md_latest.md"),
        "btc_1d_research_stack_operating_brief": str(
            analysis_dir / "btc_1d_research_stack_operating_brief_latest.json"
        ),
        "btc_1d_research_stack_operating_brief_md": str(
            analysis_dir / "btc_1d_research_stack_operating_brief_md_latest.md"
        ),
        "btc_1d_quick_read_contract_screen": str(
            analysis_dir / "btc_1d_quick_read_contract_screen_latest.json"
        ),
        "btc_1d_quick_read_contract_screen_md": str(
            analysis_dir / "btc_1d_quick_read_contract_screen_md_latest.md"
        ),
        "btc_1d_execution_contract_screen": str(
            analysis_dir / "btc_1d_execution_contract_screen_latest.json"
        ),
        "btc_1d_execution_contract_screen_md": str(
            analysis_dir / "btc_1d_execution_contract_screen_md_latest.md"
        ),
        "btc_1d_execution_meta_contract_test_index": str(
            analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json"
        ),
        "btc_1d_execution_meta_contract_test_index_md": str(
            analysis_dir / "btc_1d_execution_meta_contract_test_index_md_latest.md"
        ),
        "btc_1d_meta_contract_screen": str(analysis_dir / "btc_1d_meta_contract_screen_latest.json"),
        "btc_1d_meta_contract_screen_md": str(
            analysis_dir / "btc_1d_meta_contract_screen_md_latest.md"
        ),
    }
    if (analysis_dir / "btc_1d_paper_nightly_summary_latest.json").exists():
        latest_aliases["btc_1d_paper_nightly_summary"] = str(
            analysis_dir / "btc_1d_paper_nightly_summary_latest.json"
        )
    if (analysis_dir / "btc_1d_paper_nightly_summary_md_latest.md").exists():
        latest_aliases["btc_1d_paper_nightly_summary_md"] = str(
            analysis_dir / "btc_1d_paper_nightly_summary_md_latest.md"
        )
    attack_challenger_state = _load_attack_challenger_state(analysis_dir=analysis_dir)

    def _write_operator_pair(
        *,
        attack_challenger_state_local: dict[str, object],
        contract_health_state: dict[str, object],
        execution_contract_state_local: dict[str, object],
    ) -> tuple[dict[str, str], dict[str, str]]:
        attack_challenger_state = attack_challenger_state_local
        latest_index = _latest_index(
            summary=latest_summary,
            latest_aliases=latest_aliases,
            contract_health=contract_health_state,
            research_stack_health_line=render_research_stack_health_line(research_stack_health),
            combined_health_line=combined_health_line,
            paper_nightly_health_line=str(paper_state["paper_nightly_health_line"]),
            execution_health_line=execution_health_line,
            execution_contract_health_line=str(
                execution_contract_state_local["execution_contract_health_line"]
            ),
            execution_contract_read=str(execution_contract_state_local["execution_contract_read"]),
            execution_contract_aligned=bool(
                execution_contract_state_local["execution_contract_aligned"]
            ),
            execution_contract_paper_ledger_snapshot_summary_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_ledger_snapshot_summary_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_checked_aligned_entry_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_checked_aligned_entry_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_aligned_aligned_entry_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_checked_aligned_summary_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_checked_aligned_summary_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_aligned_aligned_summary_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"
                ]
            ),
            execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(
                execution_contract_state_local[
                    "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"
                ]
            ),
            paper_execution_contract_checked=bool(paper_state["paper_execution_contract_checked"]),
            paper_execution_contract_aligned=bool(paper_state["paper_execution_contract_aligned"]),
            paper_execution_contract_checked_aligned=bool(
                paper_state["paper_execution_contract_checked_aligned"]
            ),
            paper_execution_contract_aligned_aligned=bool(
                paper_state["paper_execution_contract_aligned_aligned"]
            ),
            paper_execution_contract_checked_summary_aligned=bool(
                paper_state["paper_execution_contract_checked_summary_aligned"]
            ),
            paper_execution_contract_aligned_summary_aligned=bool(
                paper_state["paper_execution_contract_aligned_summary_aligned"]
            ),
            paper_execution_contract_checked_aligned_entry_aligned=bool(
                paper_state["paper_execution_contract_checked_aligned_entry_aligned"]
            ),
            paper_execution_contract_aligned_aligned_entry_aligned=bool(
                paper_state["paper_execution_contract_aligned_aligned_entry_aligned"]
            ),
            paper_execution_contract_checked_summary_aligned_entry_aligned=bool(
                paper_state["paper_execution_contract_checked_summary_aligned_entry_aligned"]
            ),
            paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(
                paper_state["paper_execution_contract_aligned_summary_aligned_entry_aligned"]
            ),
            paper_execution_contract_checked_aligned_summary_aligned=bool(
                paper_state["paper_execution_contract_checked_aligned_summary_aligned"]
            ),
            paper_execution_contract_aligned_aligned_summary_aligned=bool(
                paper_state["paper_execution_contract_aligned_aligned_summary_aligned"]
            ),
            paper_execution_contract_checked_summary_aligned_summary_aligned=bool(
                paper_state["paper_execution_contract_checked_summary_aligned_summary_aligned"]
            ),
            paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(
                paper_state["paper_execution_contract_aligned_summary_aligned_summary_aligned"]
            ),
            paper_execution_read=str(paper_state["paper_execution_read"]),
            paper_exit_duplicate_run=bool(paper_state["paper_exit_duplicate_run"]),
            paper_ledger_consistent=bool(paper_state["paper_ledger_consistent"]),
            paper_ledger_snapshot=dict(paper_state["paper_ledger_snapshot"]),
            attack_challenger_candidate=str(attack_challenger_state["attack_challenger_candidate"]),
            attack_challenger_role_assignment=str(
                attack_challenger_state["attack_challenger_role_assignment"]
            ),
            attack_challenger_promotion_ready=bool(
                attack_challenger_state["attack_challenger_promotion_ready"]
            ),
            attack_challenger_next_step=str(attack_challenger_state["attack_challenger_next_step"]),
            attack_challenger_paper_validation_cagr=attack_challenger_state[
                "attack_challenger_paper_validation_cagr"
            ],
            attack_challenger_paper_validation_max_drawdown=attack_challenger_state[
                "attack_challenger_paper_validation_max_drawdown"
            ],
            attack_challenger_walk_forward_sensitivity_max_drift=attack_challenger_state[
                "attack_challenger_walk_forward_sensitivity_max_drift"
            ],
            attack_challenger_friction_final_decision=str(
                attack_challenger_state["attack_challenger_friction_final_decision"]
            ),
            attack_challenger_bridge_entry_ready=bool(
                attack_challenger_state["attack_challenger_bridge_entry_ready"]
            ),
            attack_challenger_bridge_queue_lane=str(
                attack_challenger_state["attack_challenger_bridge_queue_lane"]
            ),
            attack_challenger_execution_contract_entry_ready=bool(
                attack_challenger_state["attack_challenger_execution_contract_entry_ready"]
            ),
            attack_challenger_execution_contract_queue_lane=str(
                attack_challenger_state["attack_challenger_execution_contract_queue_lane"]
            ),
            attack_challenger_operator_stack_handoff_ready=bool(
                attack_challenger_state["attack_challenger_operator_stack_handoff_ready"]
            ),
            attack_challenger_operator_stack_handoff_lane=str(
                attack_challenger_state["attack_challenger_operator_stack_handoff_lane"]
            ),
            attack_challenger_operator_runbook_candidate_entry_ready=bool(
                attack_challenger_state[
                    "attack_challenger_operator_runbook_candidate_entry_ready"
                ]
            ),
            attack_challenger_operator_runbook_candidate_entry_lane=str(
                attack_challenger_state[
                    "attack_challenger_operator_runbook_candidate_entry_lane"
                ]
            ),
            attack_challenger_operator_runbook_execution_entry_ready=bool(
                attack_challenger_state[
                    "attack_challenger_operator_runbook_execution_entry_ready"
                ]
            ),
            attack_challenger_operator_runbook_execution_entry_lane=str(
                attack_challenger_state[
                    "attack_challenger_operator_runbook_execution_entry_lane"
                ]
            ),
            attack_challenger_live_readiness_review_ready=bool(
                attack_challenger_state[
                    "attack_challenger_live_readiness_review_ready"
                ]
            ),
            attack_challenger_live_readiness_review_lane=str(
                attack_challenger_state[
                    "attack_challenger_live_readiness_review_lane"
                ]
            ),
            attack_challenger_live_shadow_activation_review_ready=bool(
                attack_challenger_state[
                    "attack_challenger_live_shadow_activation_review_ready"
                ]
            ),
            attack_challenger_live_shadow_activation_review_lane=str(
                attack_challenger_state[
                    "attack_challenger_live_shadow_activation_review_lane"
                ]
            ),
            attack_challenger_live_candidate_entry_ready=bool(
                attack_challenger_state[
                    "attack_challenger_live_candidate_entry_ready"
                ]
            ),
            attack_challenger_live_candidate_entry_lane=str(
                attack_challenger_state[
                    "attack_challenger_live_candidate_entry_lane"
                ]
            ),
            attack_challenger_live_operator_paper_entry_ready=bool(
                attack_challenger_state[
                    "attack_challenger_live_operator_paper_entry_ready"
                ]
            ),
            attack_challenger_live_operator_paper_entry_lane=str(
                attack_challenger_state[
                    "attack_challenger_live_operator_paper_entry_lane"
                ]
            ),
            attack_challenger_live_shadow_governance_review_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_governance_review_ready", False
                )
            ),
            attack_challenger_live_shadow_governance_review_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_governance_review_lane", ""
                )
            ),
            attack_challenger_live_governed_shadow_entry_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_governed_shadow_entry_ready", False
                )
            ),
            attack_challenger_live_governed_shadow_entry_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_governed_shadow_entry_lane", ""
                )
            ),
            attack_challenger_live_shadow_candidate_paper_review_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_candidate_paper_review_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_candidate_paper_review_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_candidate_paper_review_lane", ""
                )
            ),
            attack_challenger_live_shadow_candidate_governance_lock_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_candidate_governance_lock_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_candidate_governance_lock_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_candidate_governance_lock_lane",
                    "",
                )
            ),
            attack_challenger_live_shadow_locked_entry_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_entry_ready", False
                )
            ),
            attack_challenger_live_shadow_locked_entry_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_entry_lane", ""
                )
            ),
            attack_challenger_live_shadow_locked_candidate_review_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_candidate_review_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_locked_candidate_review_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_candidate_review_lane",
                    "",
                )
            ),
            attack_challenger_live_shadow_locked_candidate_release_review_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_candidate_release_review_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_locked_candidate_release_review_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_candidate_release_review_lane",
                    "",
                )
            ),
            attack_challenger_live_shadow_locked_release_entry_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_entry_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_locked_release_entry_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_entry_lane",
                    "",
                )
            ),
            attack_challenger_live_shadow_locked_release_candidate_review_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_candidate_review_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_locked_release_candidate_review_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_candidate_review_lane",
                    "",
                )
            ),
            attack_challenger_live_shadow_locked_release_governance_check_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_governance_check_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_locked_release_governance_check_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_governance_check_lane",
                    "",
                )
            ),
            attack_challenger_live_shadow_locked_release_governance_entry_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_governance_entry_ready",
                    False,
                )
            ),
            attack_challenger_live_shadow_locked_release_governance_entry_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_live_shadow_locked_release_governance_entry_lane",
                    "",
                )
            ),
            attack_challenger_remote_monitoring_deployment_handoff_ready=bool(
                attack_challenger_state.get(
                    "attack_challenger_remote_monitoring_deployment_handoff_ready",
                    False,
                )
            ),
            attack_challenger_remote_monitoring_deployment_handoff_lane=str(
                attack_challenger_state.get(
                    "attack_challenger_remote_monitoring_deployment_handoff_lane",
                    "",
                )
            ),
            attack_challenger_bridge_report=str(
                attack_challenger_state["attack_challenger_bridge_report"]
            ),
        )
        latest_index_paths_local = _write_latest_index(
            analysis_dir=analysis_dir,
            index_payload=latest_index,
        )
        latest_aliases.update(
            _write_latest_aliases(
                analysis_dir=analysis_dir,
                paths={
                    "btc_1d_operating_index": latest_index_paths_local["json"],
                    "btc_1d_operating_index_md": latest_index_paths_local["md"],
                },
            )
        )
        operating_brief = build_operating_brief(analysis_dir=analysis_dir)
        operating_brief_paths_local = _write_operating_brief(
            analysis_dir=analysis_dir,
            brief=operating_brief,
        )
        latest_aliases.update(
            _write_latest_aliases(
                analysis_dir=analysis_dir,
                paths={
                    "btc_1d_operating_brief": operating_brief_paths_local["json"],
                    "btc_1d_operating_brief_txt": operating_brief_paths_local["txt"],
                    "btc_1d_operating_brief_md": operating_brief_paths_local["md"],
                },
            )
        )
        return latest_index_paths_local, operating_brief_paths_local

    latest_aliases.update(_publish_practical_outputs(analysis_dir=analysis_dir))
    bootstrap_execution_health_line = str(paper_state["paper_nightly_health_line"])
    bootstrap_execution_contract_state = _load_execution_contract_state(
        analysis_dir=analysis_dir,
        latest_aliases=latest_aliases,
        paper_execution_read=str(paper_state["paper_execution_read"]),
        execution_health_line=bootstrap_execution_health_line,
    )
    bootstrap_index = _latest_index(
        summary=latest_summary,
        latest_aliases=latest_aliases,
        contract_health={},
        research_stack_health_line="",
        combined_health_line="",
        paper_nightly_health_line=str(paper_state["paper_nightly_health_line"]),
        execution_health_line=bootstrap_execution_health_line,
        execution_contract_health_line=str(
            bootstrap_execution_contract_state["execution_contract_health_line"]
        ),
        execution_contract_read=str(bootstrap_execution_contract_state["execution_contract_read"]),
        execution_contract_aligned=bool(bootstrap_execution_contract_state["execution_contract_aligned"]),
        execution_contract_paper_ledger_snapshot_summary_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_ledger_snapshot_summary_aligned"]
        ),
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"]
        ),
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"]
        ),
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"]
        ),
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"]
        ),
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"]
        ),
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"]
        ),
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"]
        ),
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(
            bootstrap_execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"]
        ),
        paper_execution_contract_checked=bool(paper_state["paper_execution_contract_checked"]),
        paper_execution_contract_aligned=bool(paper_state["paper_execution_contract_aligned"]),
        paper_execution_contract_checked_aligned=bool(
            paper_state["paper_execution_contract_checked_aligned"]
        ),
        paper_execution_contract_aligned_aligned=bool(
            paper_state["paper_execution_contract_aligned_aligned"]
        ),
        paper_execution_contract_checked_summary_aligned=bool(
            paper_state["paper_execution_contract_checked_summary_aligned"]
        ),
        paper_execution_contract_aligned_summary_aligned=bool(
            paper_state["paper_execution_contract_aligned_summary_aligned"]
        ),
        paper_execution_contract_checked_aligned_entry_aligned=bool(
            paper_state["paper_execution_contract_checked_aligned_entry_aligned"]
        ),
        paper_execution_contract_aligned_aligned_entry_aligned=bool(
            paper_state["paper_execution_contract_aligned_aligned_entry_aligned"]
        ),
        paper_execution_contract_checked_summary_aligned_entry_aligned=bool(
            paper_state["paper_execution_contract_checked_summary_aligned_entry_aligned"]
        ),
        paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(
            paper_state["paper_execution_contract_aligned_summary_aligned_entry_aligned"]
        ),
        paper_execution_contract_checked_aligned_summary_aligned=bool(
            paper_state["paper_execution_contract_checked_aligned_summary_aligned"]
        ),
        paper_execution_contract_aligned_aligned_summary_aligned=bool(
            paper_state["paper_execution_contract_aligned_aligned_summary_aligned"]
        ),
        paper_execution_contract_checked_summary_aligned_summary_aligned=bool(
            paper_state["paper_execution_contract_checked_summary_aligned_summary_aligned"]
        ),
        paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(
            paper_state["paper_execution_contract_aligned_summary_aligned_summary_aligned"]
        ),
        paper_execution_read=str(paper_state["paper_execution_read"]),
        paper_exit_duplicate_run=bool(paper_state["paper_exit_duplicate_run"]),
        paper_ledger_consistent=bool(paper_state["paper_ledger_consistent"]),
        paper_ledger_snapshot=dict(paper_state["paper_ledger_snapshot"]),
        attack_challenger_candidate=str(attack_challenger_state["attack_challenger_candidate"]),
        attack_challenger_role_assignment=str(attack_challenger_state["attack_challenger_role_assignment"]),
        attack_challenger_promotion_ready=bool(attack_challenger_state["attack_challenger_promotion_ready"]),
        attack_challenger_next_step=str(attack_challenger_state["attack_challenger_next_step"]),
        attack_challenger_paper_validation_cagr=attack_challenger_state["attack_challenger_paper_validation_cagr"],
        attack_challenger_paper_validation_max_drawdown=attack_challenger_state["attack_challenger_paper_validation_max_drawdown"],
        attack_challenger_walk_forward_sensitivity_max_drift=attack_challenger_state["attack_challenger_walk_forward_sensitivity_max_drift"],
        attack_challenger_friction_final_decision=str(attack_challenger_state["attack_challenger_friction_final_decision"]),
        attack_challenger_bridge_entry_ready=bool(attack_challenger_state["attack_challenger_bridge_entry_ready"]),
        attack_challenger_bridge_queue_lane=str(attack_challenger_state["attack_challenger_bridge_queue_lane"]),
        attack_challenger_execution_contract_entry_ready=bool(attack_challenger_state["attack_challenger_execution_contract_entry_ready"]),
        attack_challenger_execution_contract_queue_lane=str(attack_challenger_state["attack_challenger_execution_contract_queue_lane"]),
        attack_challenger_operator_stack_handoff_ready=bool(attack_challenger_state["attack_challenger_operator_stack_handoff_ready"]),
        attack_challenger_operator_stack_handoff_lane=str(attack_challenger_state["attack_challenger_operator_stack_handoff_lane"]),
        attack_challenger_operator_runbook_candidate_entry_ready=bool(attack_challenger_state["attack_challenger_operator_runbook_candidate_entry_ready"]),
        attack_challenger_operator_runbook_candidate_entry_lane=str(attack_challenger_state["attack_challenger_operator_runbook_candidate_entry_lane"]),
        attack_challenger_operator_runbook_execution_entry_ready=bool(attack_challenger_state["attack_challenger_operator_runbook_execution_entry_ready"]),
        attack_challenger_operator_runbook_execution_entry_lane=str(attack_challenger_state["attack_challenger_operator_runbook_execution_entry_lane"]),
        attack_challenger_live_readiness_review_ready=bool(attack_challenger_state["attack_challenger_live_readiness_review_ready"]),
        attack_challenger_live_readiness_review_lane=str(attack_challenger_state["attack_challenger_live_readiness_review_lane"]),
        attack_challenger_live_shadow_activation_review_ready=bool(attack_challenger_state["attack_challenger_live_shadow_activation_review_ready"]),
        attack_challenger_live_shadow_activation_review_lane=str(attack_challenger_state["attack_challenger_live_shadow_activation_review_lane"]),
        attack_challenger_live_candidate_entry_ready=bool(attack_challenger_state["attack_challenger_live_candidate_entry_ready"]),
        attack_challenger_live_candidate_entry_lane=str(attack_challenger_state["attack_challenger_live_candidate_entry_lane"]),
        attack_challenger_live_operator_paper_entry_ready=bool(attack_challenger_state["attack_challenger_live_operator_paper_entry_ready"]),
        attack_challenger_live_operator_paper_entry_lane=str(attack_challenger_state["attack_challenger_live_operator_paper_entry_lane"]),
        attack_challenger_live_shadow_governance_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_governance_review_ready", False)),
        attack_challenger_live_shadow_governance_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_governance_review_lane", "")),
        attack_challenger_live_governed_shadow_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_governed_shadow_entry_ready", False)),
        attack_challenger_live_governed_shadow_entry_lane=str(attack_challenger_state.get("attack_challenger_live_governed_shadow_entry_lane", "")),
        attack_challenger_live_shadow_candidate_paper_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_candidate_paper_review_ready", False)),
        attack_challenger_live_shadow_candidate_paper_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_candidate_paper_review_lane", "")),
        attack_challenger_live_shadow_candidate_governance_lock_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_candidate_governance_lock_ready", False)),
        attack_challenger_live_shadow_candidate_governance_lock_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_candidate_governance_lock_lane", "")),
        attack_challenger_live_shadow_locked_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_entry_ready", False)),
        attack_challenger_live_shadow_locked_entry_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_entry_lane", "")),
        attack_challenger_live_shadow_locked_candidate_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_review_ready", False)),
        attack_challenger_live_shadow_locked_candidate_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_review_lane", "")),
        attack_challenger_live_shadow_locked_candidate_release_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_release_review_ready", False)),
        attack_challenger_live_shadow_locked_candidate_release_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_release_review_lane", "")),
        attack_challenger_live_shadow_locked_release_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_entry_ready", False)),
        attack_challenger_live_shadow_locked_release_entry_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_entry_lane", "")),
        attack_challenger_live_shadow_locked_release_candidate_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_candidate_review_ready", False)),
        attack_challenger_live_shadow_locked_release_candidate_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_candidate_review_lane", "")),
        attack_challenger_live_shadow_locked_release_governance_check_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_governance_check_ready", False)),
        attack_challenger_live_shadow_locked_release_governance_check_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_governance_check_lane", "")),
        attack_challenger_live_shadow_locked_release_governance_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_governance_entry_ready", False)),
        attack_challenger_live_shadow_locked_release_governance_entry_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_governance_entry_lane", "")),
        attack_challenger_bridge_report=str(attack_challenger_state["attack_challenger_bridge_report"]),
    )
    bootstrap_index_paths = _write_latest_index(analysis_dir=analysis_dir, index_payload=bootstrap_index)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=analysis_dir,
            paths={
                "btc_1d_operating_index": bootstrap_index_paths["json"],
                "btc_1d_operating_index_md": bootstrap_index_paths["md"],
            },
        )
    )
    with redirect_stdout(io.StringIO()):
        research_stack_operating_brief_script.ANALYSIS_DIR = analysis_dir
        research_stack_operating_brief_script.main()
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=analysis_dir,
            paths={
                "btc_1d_research_stack_operating_brief": str(
                    analysis_dir / "btc_1d_research_stack_operating_brief_latest.json"
                ),
                "btc_1d_research_stack_operating_brief_md": str(
                    analysis_dir / "btc_1d_research_stack_operating_brief_md_latest.md"
                ),
            },
        )
    )
    placeholder_brief = {
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
        "standard_check_order": ["practical", "research", "contract", "brief"],
        "paper_execution_contract_checked": False,
        "paper_execution_contract_aligned": False,
        "contract_health_operating_contract_aligned": False,
        "contract_health_paper_execution_contract_aligned": False,
        "contract_health_contracts_are_well_partitioned": False,
        "contract_health_aligned": False,
    }
    (analysis_dir / "btc_1d_operating_brief_latest.json").write_text(
        json.dumps(placeholder_brief, indent=2),
        encoding="utf-8",
    )
    (analysis_dir / "btc_1d_operating_brief_txt_latest.txt").write_text(
        "bootstrap operating brief",
        encoding="utf-8",
    )
    (analysis_dir / "btc_1d_operating_brief_md_latest.md").write_text(
        "# bootstrap operating brief",
        encoding="utf-8",
    )
    placeholder_execution_contract = {
        "execution_contract_summary": {
            "execution_contract_read": render_execution_contract_read(
                execution_contract_aligned=False,
                paper_execution_read=str(paper_state["paper_execution_read"]),
            ),
            "paper_ledger_snapshot_summary_aligned": False,
            "paper_execution_contract_checked_aligned_entry_aligned": False,
            "paper_execution_contract_aligned_aligned_entry_aligned": False,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": False,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
            "paper_execution_contract_checked_aligned_summary_aligned": False,
            "paper_execution_contract_aligned_aligned_summary_aligned": False,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": False,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
            "paper_ledger_snapshot_read": _render_paper_ledger_snapshot_read(
                dict(paper_state["paper_ledger_snapshot"])
            ),
        },
        "execution_contract_verdict": {
            "execution_contract_aligned": False,
        },
    }
    (analysis_dir / "btc_1d_execution_contract_screen_latest.json").write_text(
        json.dumps(placeholder_execution_contract, indent=2),
        encoding="utf-8",
    )
    (analysis_dir / "btc_1d_execution_contract_screen_md_latest.md").write_text(
        "# bootstrap execution contract screen",
        encoding="utf-8",
    )
    (analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json").write_text(
        json.dumps({}, indent=2),
        encoding="utf-8",
    )
    (analysis_dir / "btc_1d_execution_meta_contract_test_index_md_latest.md").write_text(
        "# bootstrap execution meta contract test index",
        encoding="utf-8",
    )
    latest_aliases.update(
        {
            "btc_1d_operating_brief": str(analysis_dir / "btc_1d_operating_brief_latest.json"),
            "btc_1d_operating_brief_txt": str(analysis_dir / "btc_1d_operating_brief_txt_latest.txt"),
            "btc_1d_operating_brief_md": str(analysis_dir / "btc_1d_operating_brief_md_latest.md"),
            "btc_1d_execution_contract_screen": str(
                analysis_dir / "btc_1d_execution_contract_screen_latest.json"
            ),
            "btc_1d_execution_contract_screen_md": str(
                analysis_dir / "btc_1d_execution_contract_screen_md_latest.md"
            ),
            "btc_1d_execution_meta_contract_test_index": str(
                analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json"
            ),
            "btc_1d_execution_meta_contract_test_index_md": str(
                analysis_dir / "btc_1d_execution_meta_contract_test_index_md_latest.md"
            ),
        }
    )
    bootstrap_brief = build_operating_brief(analysis_dir=analysis_dir)
    bootstrap_brief_paths = _write_operating_brief(analysis_dir=analysis_dir, brief=bootstrap_brief)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=analysis_dir,
            paths={
                "btc_1d_operating_brief": bootstrap_brief_paths["json"],
                "btc_1d_operating_brief_txt": bootstrap_brief_paths["txt"],
                "btc_1d_operating_brief_md": bootstrap_brief_paths["md"],
            },
        )
    )

    practical_health = check_practical_health(analysis_dir=analysis_dir)
    research_stack_health = check_research_stack_health(analysis_dir=analysis_dir)
    combined_health_line = _render_combined_health_line(
        practical_health=practical_health,
        research_stack_health=research_stack_health,
    )
    execution_health_line = _render_execution_health_line(
        combined_health_line=combined_health_line,
        paper_nightly_health_line=str(paper_state["paper_nightly_health_line"]),
    )

    def _has_seeded_attack_challenger_outputs() -> bool:
        return any(
            analysis_dir.glob("btc_1d_pullthrough_asymmetric_release_*_latest.json")
        )

    latest_index_paths: dict[str, str] = {}
    operating_brief_paths: dict[str, str] = {}
    contract_health: dict[str, object] = {}
    execution_contract_state: dict[str, object] = {}

    def _sync_operator_stack_once() -> None:
        nonlocal latest_aliases
        nonlocal latest_index_paths
        nonlocal operating_brief_paths
        nonlocal contract_health
        nonlocal execution_contract_state
        nonlocal research_stack_health
        nonlocal combined_health_line
        nonlocal execution_health_line

        # Publish challenger outputs first so every downstream surface reads the
        # same latest handoff stage instead of mixing pre- and post-publish state.
        if _has_seeded_attack_challenger_outputs():
            latest_aliases.update(
                _write_latest_aliases(
                    analysis_dir=analysis_dir,
                    paths=_publish_attack_challenger_outputs(analysis_dir=analysis_dir),
                )
            )
        latest_aliases = _refresh_contract_artifacts_after_paper(
            analysis_dir=analysis_dir,
            latest_aliases=latest_aliases,
        )
        research_stack_health = check_research_stack_health(analysis_dir=analysis_dir)
        combined_health_line = _render_combined_health_line(
            practical_health=practical_health,
            research_stack_health=research_stack_health,
        )
        execution_health_line = _render_execution_health_line(
            combined_health_line=combined_health_line,
            paper_nightly_health_line=str(paper_state["paper_nightly_health_line"]),
        )
        contract_health = check_contract_health(analysis_dir=analysis_dir)
        execution_contract_state = _load_execution_contract_state(
            analysis_dir=analysis_dir,
            latest_aliases=latest_aliases,
            paper_execution_read=str(paper_state["paper_execution_read"]),
            execution_health_line=execution_health_line,
        )
        latest_index_paths, operating_brief_paths = _write_operator_pair(
            attack_challenger_state_local=_load_attack_challenger_state(
                analysis_dir=analysis_dir
            ),
            contract_health_state=contract_health,
            execution_contract_state_local=execution_contract_state,
        )
        latest_aliases = _refresh_contract_artifacts_after_paper(
            analysis_dir=analysis_dir,
            latest_aliases=latest_aliases,
        )
        contract_health = check_contract_health(analysis_dir=analysis_dir)
        execution_contract_state = _load_execution_contract_state(
            analysis_dir=analysis_dir,
            latest_aliases=latest_aliases,
            paper_execution_read=str(paper_state["paper_execution_read"]),
            execution_health_line=execution_health_line,
        )
        latest_index_paths, operating_brief_paths = _write_operator_pair(
            attack_challenger_state_local=_load_attack_challenger_state(
                analysis_dir=analysis_dir
            ),
            contract_health_state=contract_health,
            execution_contract_state_local=execution_contract_state,
        )
        latest_aliases = _write_operator_dashboard_artifacts(
            analysis_dir=analysis_dir,
            latest_aliases=latest_aliases,
        )

    def _attack_stage_signature() -> tuple[object, ...]:
        state = _load_attack_challenger_state(analysis_dir=analysis_dir)
        return (
            bool(state.get("attack_challenger_live_shadow_locked_release_entry_ready", False)),
            bool(
                state.get(
                    "attack_challenger_live_shadow_locked_release_candidate_review_ready",
                    False,
                )
            ),
            bool(
                state.get(
                    "attack_challenger_live_shadow_locked_release_governance_check_ready",
                    False,
                )
            ),
            bool(
                state.get(
                    "attack_challenger_live_shadow_locked_release_governance_entry_ready",
                    False,
                )
            ),
            bool(
                state.get(
                    "attack_challenger_remote_monitoring_deployment_handoff_ready",
                    False,
                )
            ),
            str(state.get("attack_challenger_next_step", "")),
            str(state.get("attack_challenger_bridge_report", "")),
        )

    for _ in range(max(sync_passes, 1)):
        _sync_operator_stack_once()

    # The challenger handoff chain advances one mirrored stage at a time
    # (candidate review -> governance check -> governance entry -> handoff).
    # Iterate to a local fixed point so latest artifacts do not stop one stage
    # behind the newly mirrored operator surfaces.
    for _ in range(6):
        before_signature = _attack_stage_signature()
        _sync_operator_stack_once()
        after_signature = _attack_stage_signature()
        if after_signature == before_signature:
            break
    _sync_operator_stack_once()
    contract_health = check_contract_health(analysis_dir=analysis_dir)
    dashboard_path = Path(
        latest_aliases.get(
            "btc_1d_operator_dashboard",
            str(analysis_dir / "btc_1d_operator_dashboard_latest.json"),
        )
    )
    dashboard_payload: dict[str, object] = {}
    dashboard_summary: dict[str, object] = {}
    if dashboard_path.exists():
        dashboard_payload = json.loads(dashboard_path.read_text(encoding="utf-8-sig"))
        dashboard_summary = dict(dashboard_payload.get("dashboard_summary", {}))
    refresh_summary = _build_refresh_summary(
        latest_summary=latest_summary,
        paper_state=paper_state,
        contract_health=contract_health,
        execution_contract_state=execution_contract_state,
        dashboard_payload=dashboard_payload,
        dashboard_summary=dashboard_summary,
        latest_aliases=latest_aliases,
    )
    normalized_contract_health = _normalize_attack_challenger_handoff_fields(
        refresh_summary=refresh_summary,
        target=contract_health,
    )
    normalized_execution_contract_state = _normalize_attack_challenger_handoff_fields(
        refresh_summary=refresh_summary,
        target=execution_contract_state,
    )
    normalized_top_level_handoff = _normalize_attack_challenger_handoff_fields(
        refresh_summary=refresh_summary,
    )
    return {
        "analysis_dir": str(analysis_dir),
        "sync_passes": max(sync_passes, 1),
        "refresh_summary": refresh_summary,
        "deployment_monitoring_active": bool(
            normalized_top_level_handoff["deployment_monitoring_active"]
        ),
        "attack_challenger_remote_monitoring_deployment_handoff_ready": bool(
            normalized_top_level_handoff[
                "attack_challenger_remote_monitoring_deployment_handoff_ready"
            ]
        ),
        "attack_challenger_next_step": str(
            normalized_top_level_handoff["attack_challenger_next_step"]
        ),
        "attack_challenger_bridge_report": str(
            normalized_top_level_handoff["attack_challenger_bridge_report"]
        ),
        "latest_aliases": latest_aliases,
        "combined_health_line": combined_health_line,
        "paper_nightly_health_line": str(paper_state["paper_nightly_health_line"]),
        "execution_health_line": execution_health_line,
        "contract_health": normalized_contract_health,
        "execution_contract_state": normalized_execution_contract_state,
        "dashboard_summary": dashboard_summary,
    }


def _build_shadow_update_output(
    *,
    practical_health: dict,
    practical_health_line: str,
    research_stack_health: dict,
    research_stack_health_line: str,
    contract_health: dict,
    contract_health_line: str,
    regression_lock_test: str,
    combined_health_line: str,
    paper_nightly_health_line: str,
    execution_health_line: str,
    execution_contract_health_line: str,
    execution_contract_read: str,
    execution_contract_aligned: bool,
    execution_contract_paper_ledger_snapshot_summary_aligned: bool,
    execution_contract_paper_execution_contract_checked_aligned_entry_aligned: bool,
    execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: bool,
    execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: bool,
    execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: bool,
    execution_contract_paper_execution_contract_checked_aligned_summary_aligned: bool,
    execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: bool,
    execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: bool,
    execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: bool,
    paper_execution_contract_checked: bool,
    paper_execution_contract_aligned: bool,
    paper_execution_contract_checked_aligned: bool,
    paper_execution_contract_aligned_aligned: bool,
    paper_execution_contract_checked_summary_aligned: bool,
    paper_execution_contract_aligned_summary_aligned: bool,
    paper_execution_contract_checked_aligned_entry_aligned: bool,
    paper_execution_contract_aligned_aligned_entry_aligned: bool,
    paper_execution_contract_checked_summary_aligned_entry_aligned: bool,
    paper_execution_contract_aligned_summary_aligned_entry_aligned: bool,
    paper_execution_contract_checked_aligned_summary_aligned: bool,
    paper_execution_contract_aligned_aligned_summary_aligned: bool,
    paper_execution_contract_checked_summary_aligned_summary_aligned: bool,
    paper_execution_contract_aligned_summary_aligned_summary_aligned: bool,
    paper_execution_read: str,
    paper_exit_duplicate_run: bool,
    paper_ledger_consistent: bool,
    paper_ledger_snapshot: dict[str, object],
    latest_summary: dict,
    latest_summary_paths: dict[str, str],
    latest_index_paths: dict[str, str],
    operating_brief_paths: dict[str, str],
    latest_aliases: dict[str, str],
    carry_validation: dict,
    survivability_validation: dict,
    eth_regression: dict,
    walk_forward: dict,
    shadow_packet_result: dict,
    operating_snapshot: dict,
    eth_symbol: str,
    carry_periods: int,
    survivability_periods: int,
    walk_forward_periods: int,
    paper_nightly: dict | None = None,
) -> dict:
    payload = {
        "practical_health": practical_health,
        "practical_health_line": practical_health_line,
        "research_stack_health": research_stack_health,
        "research_stack_health_line": research_stack_health_line,
        "contract_health": contract_health,
        "contract_health_line": contract_health_line,
        "contract_health_operating_contract_aligned": bool(
            contract_health.get("operating_contract_aligned", False)
        ),
        "contract_health_paper_execution_contract_aligned": bool(
            contract_health.get("paper_execution_contract_aligned", False)
        ),
        "contract_health_aligned": bool(
            contract_health.get("contract_health_aligned", False)
        ),
        "contract_health_contracts_are_well_partitioned": bool(
            contract_health.get("contracts_are_well_partitioned", False)
        ),
        "regression_lock_test": regression_lock_test,
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
        "paper_ledger_snapshot_read": _render_paper_ledger_snapshot_read(paper_ledger_snapshot),
        "latest_summary": latest_summary,
        "latest_summary_json": latest_summary_paths["json"],
        "latest_summary_md": latest_summary_paths["md"],
        "latest_index_json": latest_index_paths["json"],
        "latest_index_md": latest_index_paths["md"],
        "operating_brief_json": operating_brief_paths["json"],
        "operating_brief_txt": operating_brief_paths["txt"],
        "operating_brief_md": operating_brief_paths["md"],
        "latest_aliases": latest_aliases,
        "carry_validation": {
            "analysis_result_json": carry_validation["analysis_result_json"],
            "analysis_result_csv": carry_validation["analysis_result_csv"],
            "decision": carry_validation["decision_record"]["decision"],
            "periods": carry_periods,
        },
        "survivability_validation": {
            "analysis_result_json": survivability_validation["analysis_result_json"],
            "analysis_result_csv": survivability_validation["analysis_result_csv"],
            "decision": survivability_validation["decision_record"]["decision"],
            "periods": survivability_periods,
        },
        "eth_regression": {
            "analysis_result_json": eth_regression["analysis_result_json"],
            "summary": eth_regression["summary"],
            "symbol": eth_symbol,
        },
        "walk_forward": {
            "analysis_result_json": walk_forward["analysis_result_json"],
            "analysis_result_md": walk_forward["analysis_result_md"],
            "periods": walk_forward_periods,
            "passed": walk_forward["overfitting"]["passed"],
            "oos_sharpe": walk_forward["overfitting"]["oos_metrics"].get("sharpe"),
            "sensitivity_max_drift": walk_forward["overfitting"]["sensitivity_max_drift"],
            "unstable_parameters": walk_forward["overfitting"]["unstable_parameters"],
        },
        "shadow_packet": shadow_packet_result["packet"],
        "shadow_packet_json": shadow_packet_result["json_path"],
        "shadow_packet_md": shadow_packet_result["md_path"],
        "operating_snapshot": operating_snapshot,
    }
    if paper_nightly is not None:
        payload["paper_nightly"] = paper_nightly
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.refresh_only:
        payload = refresh_operator_stack(
            analysis_dir=args.analysis_dir,
            sync_passes=int(args.sync_passes),
        )
        refresh_summary = dict(payload.get("refresh_summary", {}))
        normalized_top_level_handoff = _normalize_attack_challenger_handoff_fields(
            refresh_summary=refresh_summary,
            target=payload,
        )
        payload["deployment_monitoring_active"] = bool(
            normalized_top_level_handoff["deployment_monitoring_active"]
        )
        payload["attack_challenger_remote_monitoring_deployment_handoff_ready"] = bool(
            normalized_top_level_handoff[
                "attack_challenger_remote_monitoring_deployment_handoff_ready"
            ]
        )
        payload["attack_challenger_next_step"] = str(
            normalized_top_level_handoff["attack_challenger_next_step"]
        )
        payload["attack_challenger_bridge_report"] = str(
            normalized_top_level_handoff["attack_challenger_bridge_report"]
        )
        print(json.dumps(payload, indent=2))
        return 0
    carry_validation = _run_validation(
        analysis_dir=args.analysis_dir,
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    survivability_validation = _run_validation(
        analysis_dir=args.analysis_dir,
        periods=args.survivability_periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    friction_result = run_friction_main(
        [
            "--analysis-dir",
            str(args.analysis_dir),
            "--periods",
            str(args.friction_periods),
            *(["--allow-synthetic-ohlcv-fallback"] if args.allow_synthetic_ohlcv_fallback else []),
        ]
    )
    friction_candidates = sorted(
        args.analysis_dir.glob("btc_1d_low_vol_cap_friction_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    friction_path = friction_candidates[0] if friction_candidates else None
    walk_forward = _run_walk_forward(
        periods=args.walk_forward_periods,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    eth_regression = _run_promoted_regression(
        analysis_dir=args.analysis_dir,
        symbol=args.eth_symbol,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    shadow_packet_result = write_shadow_packet(
        analysis_dir=args.analysis_dir,
        output_dir=args.analysis_dir,
        carry_paper_path=Path(carry_validation["analysis_result_json"]),
        survivability_paper_path=Path(survivability_validation["analysis_result_json"]),
        friction_path=friction_path,
        walk_forward_path=Path(walk_forward["analysis_result_json"]),
    )
    operating_snapshot = publish_operating_snapshot(analysis_dir=args.analysis_dir)
    latest_summary = _latest_summary(
        shadow_packet=shadow_packet_result["packet"],
        walk_forward=walk_forward,
        eth_regression=eth_regression,
        eth_symbol=args.eth_symbol,
    )
    latest_summary_paths = _write_latest_summary(analysis_dir=args.analysis_dir, summary=latest_summary)
    latest_aliases = _write_latest_aliases(
        analysis_dir=args.analysis_dir,
        paths={
            "btc_1d_latest_summary": latest_summary_paths["json"],
            "btc_1d_latest_summary_md": latest_summary_paths["md"],
            "btc_1d_shadow_packet": shadow_packet_result["json_path"],
            "btc_1d_shadow_packet_md": shadow_packet_result["md_path"],
            "btc_1d_candidate_status_board": operating_snapshot["status_json"],
            "btc_1d_candidate_status_board_md": operating_snapshot["status_md"],
            "btc_1d_baseline_freeze": operating_snapshot["freeze_json"],
            "btc_1d_baseline_freeze_md": operating_snapshot["freeze_md"],
            "btc_1d_shadow_readiness": operating_snapshot["readiness_json"],
            "btc_1d_shadow_readiness_md": operating_snapshot["readiness_md"],
            "btc_1d_walk_forward_diagnostic": walk_forward["analysis_result_json"],
            "btc_1d_walk_forward_diagnostic_md": walk_forward["analysis_result_md"],
            "btc_1d_low_vol_cap_friction": str(friction_path) if friction_path else "",
            "btc_1d_low_vol_cap_friction_md": (
                str(friction_path.with_suffix(".md")) if friction_path else ""
            ),
        },
    )
    latest_aliases.update(_publish_practical_outputs(analysis_dir=args.analysis_dir))
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths=_publish_research_outputs(analysis_dir=args.analysis_dir),
        )
    )
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths=_publish_execution_outputs(analysis_dir=args.analysis_dir),
        )
    )
    research_stack_health = check_research_stack_health(analysis_dir=args.analysis_dir)
    practical_health = check_practical_health(analysis_dir=args.analysis_dir)
    contract_health = check_contract_health(analysis_dir=args.analysis_dir)
    practical_health_line = render_practical_health_line(practical_health)
    research_stack_health_line = render_research_stack_health_line(research_stack_health)
    contract_health_line = render_contract_health_line(contract_health)
    regression_lock_test = contract_health.get(
        "regression_lock_test",
        "tests/unit/test_btc_1d_operating_cli_help_contract.py",
    )
    combined_health_line = _render_combined_health_line(
        practical_health=practical_health,
        research_stack_health=research_stack_health,
    )
    attack_challenger_state = _load_attack_challenger_state(analysis_dir=args.analysis_dir)
    paper_nightly = None
    paper_nightly_health_line = ""
    paper_execution_contract_checked = False
    paper_execution_contract_aligned = False
    paper_execution_contract_checked_aligned = False
    paper_execution_contract_aligned_aligned = False
    paper_execution_contract_checked_summary_aligned = False
    paper_execution_contract_aligned_summary_aligned = False
    paper_execution_contract_checked_aligned_entry_aligned = False
    paper_execution_contract_aligned_aligned_entry_aligned = False
    paper_execution_contract_checked_summary_aligned_entry_aligned = False
    paper_execution_contract_aligned_summary_aligned_entry_aligned = False
    paper_execution_contract_checked_aligned_summary_aligned = False
    paper_execution_contract_aligned_aligned_summary_aligned = False
    paper_execution_contract_checked_summary_aligned_summary_aligned = False
    paper_execution_contract_aligned_summary_aligned_summary_aligned = False
    paper_execution_read = ""
    paper_exit_duplicate_run = False
    paper_ledger_consistent = False
    paper_ledger_snapshot: dict[str, object] = {}
    if args.emit_paper_nightly:
        access_key = os.getenv("BITHUMB_ACCESS_KEY", "shadow-demo-access-key")
        secret_key = os.getenv("BITHUMB_SECRET_KEY", "shadow-demo-secret-key")
        paper_nightly = run_nightly_paper(
            logs_dir=args.paper_logs_dir,
            run_id=args.paper_run_id,
            ledger_json=args.paper_ledger_json,
            output_dir=args.paper_output_dir,
            exit_json=args.paper_exit_json,
            notional_krw=float(args.paper_notional_krw),
            max_orders=int(args.paper_max_orders),
            strategy_track=str(args.paper_track),
            access_key=access_key,
            secret_key=secret_key,
            client_order_prefix="shadow-nightly",
        )
        paper_nightly_health_line = render_paper_nightly_health_line(paper_nightly)
        paper_execution_contract_checked = bool(paper_nightly.get("execution_contract_checked", False))
        paper_execution_contract_aligned = bool(paper_nightly.get("execution_contract_aligned", False))
        paper_execution_contract_checked_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_aligned",
            "execution_contract_paper_execution_contract_checked_aligned",
        )
        paper_execution_contract_aligned_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned",
        )
        paper_execution_contract_checked_summary_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_summary_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned",
        )
        paper_execution_contract_aligned_summary_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned",
        )
        paper_execution_contract_checked_aligned_entry_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
        )
        paper_execution_contract_aligned_aligned_entry_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
        )
        paper_execution_contract_checked_summary_aligned_entry_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_summary_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
        )
        paper_execution_contract_aligned_summary_aligned_entry_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
        )
        paper_execution_contract_checked_aligned_summary_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
        )
        paper_execution_contract_aligned_aligned_summary_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
        )
        paper_execution_contract_checked_summary_aligned_summary_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_checked_summary_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
        )
        paper_execution_contract_aligned_summary_aligned_summary_aligned = _paper_summary_contract_bool(
            paper_nightly,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned",
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
        )
        paper_execution_read = paper_nightly.get("paper_execution_read", "")
        paper_exit_duplicate_run = bool(paper_nightly.get("paper_exit_duplicate_run", False))
        paper_ledger_consistent = bool(paper_nightly.get("paper_ledger_consistent", False))
        paper_ledger_snapshot = dict(paper_nightly.get("paper_ledger_snapshot", {}) or {})
        latest_aliases.update(
            _write_latest_aliases(
                analysis_dir=args.analysis_dir,
                paths={
                    "btc_1d_paper_nightly_summary": paper_nightly["artifacts"]["summary_json"],
                    "btc_1d_paper_nightly_summary_md": paper_nightly["artifacts"]["summary_md"],
                },
            )
        )
    execution_health_line = _render_execution_health_line(
        combined_health_line=combined_health_line,
        paper_nightly_health_line=paper_nightly_health_line,
    )
    execution_contract_read = render_execution_contract_read(
        execution_contract_aligned=True,
        paper_execution_read=paper_execution_read,
    )
    execution_contract_state = _load_execution_contract_state(
        analysis_dir=args.analysis_dir,
        latest_aliases=latest_aliases,
        paper_execution_read=paper_execution_read,
        execution_health_line=execution_health_line,
    )
    latest_index = _latest_index(
        summary=latest_summary,
        latest_aliases=latest_aliases,
        contract_health=contract_health,
        research_stack_health_line=research_stack_health_line,
        combined_health_line=combined_health_line,
        paper_nightly_health_line=paper_nightly_health_line,
        execution_health_line=execution_health_line,
        execution_contract_health_line=str(execution_contract_state["execution_contract_health_line"]),
        execution_contract_read=str(execution_contract_state["execution_contract_read"]),
        execution_contract_aligned=bool(execution_contract_state["execution_contract_aligned"]),
        execution_contract_paper_ledger_snapshot_summary_aligned=bool(execution_contract_state["execution_contract_paper_ledger_snapshot_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"]),
        paper_execution_contract_checked=paper_execution_contract_checked,
        paper_execution_contract_aligned=paper_execution_contract_aligned,
        paper_execution_contract_checked_aligned=paper_execution_contract_checked_aligned,
        paper_execution_contract_aligned_aligned=paper_execution_contract_aligned_aligned,
        paper_execution_contract_checked_summary_aligned=paper_execution_contract_checked_summary_aligned,
        paper_execution_contract_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned,
        paper_execution_contract_checked_aligned_entry_aligned=paper_execution_contract_checked_aligned_entry_aligned,
        paper_execution_contract_aligned_aligned_entry_aligned=paper_execution_contract_aligned_aligned_entry_aligned,
        paper_execution_contract_checked_summary_aligned_entry_aligned=paper_execution_contract_checked_summary_aligned_entry_aligned,
        paper_execution_contract_aligned_summary_aligned_entry_aligned=paper_execution_contract_aligned_summary_aligned_entry_aligned,
        paper_execution_contract_checked_aligned_summary_aligned=paper_execution_contract_checked_aligned_summary_aligned,
        paper_execution_contract_aligned_aligned_summary_aligned=paper_execution_contract_aligned_aligned_summary_aligned,
        paper_execution_contract_checked_summary_aligned_summary_aligned=paper_execution_contract_checked_summary_aligned_summary_aligned,
        paper_execution_contract_aligned_summary_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned_summary_aligned,
        paper_execution_read=paper_execution_read,
        paper_exit_duplicate_run=paper_exit_duplicate_run,
        paper_ledger_consistent=paper_ledger_consistent,
        paper_ledger_snapshot=paper_ledger_snapshot,
        attack_challenger_candidate=str(attack_challenger_state["attack_challenger_candidate"]),
        attack_challenger_role_assignment=str(attack_challenger_state["attack_challenger_role_assignment"]),
        attack_challenger_promotion_ready=bool(attack_challenger_state["attack_challenger_promotion_ready"]),
        attack_challenger_next_step=str(attack_challenger_state["attack_challenger_next_step"]),
        attack_challenger_paper_validation_cagr=attack_challenger_state["attack_challenger_paper_validation_cagr"],
        attack_challenger_paper_validation_max_drawdown=attack_challenger_state["attack_challenger_paper_validation_max_drawdown"],
        attack_challenger_walk_forward_sensitivity_max_drift=attack_challenger_state["attack_challenger_walk_forward_sensitivity_max_drift"],
        attack_challenger_friction_final_decision=str(attack_challenger_state["attack_challenger_friction_final_decision"]),
        attack_challenger_bridge_entry_ready=bool(attack_challenger_state["attack_challenger_bridge_entry_ready"]),
        attack_challenger_bridge_queue_lane=str(attack_challenger_state["attack_challenger_bridge_queue_lane"]),
        attack_challenger_execution_contract_entry_ready=bool(attack_challenger_state["attack_challenger_execution_contract_entry_ready"]),
        attack_challenger_execution_contract_queue_lane=str(attack_challenger_state["attack_challenger_execution_contract_queue_lane"]),
        attack_challenger_operator_stack_handoff_ready=bool(attack_challenger_state["attack_challenger_operator_stack_handoff_ready"]),
        attack_challenger_operator_stack_handoff_lane=str(attack_challenger_state["attack_challenger_operator_stack_handoff_lane"]),
        attack_challenger_operator_runbook_candidate_entry_ready=bool(attack_challenger_state["attack_challenger_operator_runbook_candidate_entry_ready"]),
        attack_challenger_operator_runbook_candidate_entry_lane=str(attack_challenger_state["attack_challenger_operator_runbook_candidate_entry_lane"]),
        attack_challenger_operator_runbook_execution_entry_ready=bool(attack_challenger_state["attack_challenger_operator_runbook_execution_entry_ready"]),
        attack_challenger_operator_runbook_execution_entry_lane=str(attack_challenger_state["attack_challenger_operator_runbook_execution_entry_lane"]),
        attack_challenger_live_readiness_review_ready=bool(attack_challenger_state["attack_challenger_live_readiness_review_ready"]),
        attack_challenger_live_readiness_review_lane=str(attack_challenger_state["attack_challenger_live_readiness_review_lane"]),
        attack_challenger_live_shadow_activation_review_ready=bool(attack_challenger_state["attack_challenger_live_shadow_activation_review_ready"]),
        attack_challenger_live_shadow_activation_review_lane=str(attack_challenger_state["attack_challenger_live_shadow_activation_review_lane"]),
        attack_challenger_live_candidate_entry_ready=bool(attack_challenger_state["attack_challenger_live_candidate_entry_ready"]),
        attack_challenger_live_candidate_entry_lane=str(attack_challenger_state["attack_challenger_live_candidate_entry_lane"]),
        attack_challenger_live_operator_paper_entry_ready=bool(attack_challenger_state["attack_challenger_live_operator_paper_entry_ready"]),
        attack_challenger_live_operator_paper_entry_lane=str(attack_challenger_state["attack_challenger_live_operator_paper_entry_lane"]),
        attack_challenger_live_shadow_governance_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_governance_review_ready", False)),
        attack_challenger_live_shadow_governance_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_governance_review_lane", "")),
        attack_challenger_live_governed_shadow_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_governed_shadow_entry_ready", False)),
        attack_challenger_live_governed_shadow_entry_lane=str(attack_challenger_state.get("attack_challenger_live_governed_shadow_entry_lane", "")),
        attack_challenger_live_shadow_candidate_paper_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_candidate_paper_review_ready", False)),
        attack_challenger_live_shadow_candidate_paper_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_candidate_paper_review_lane", "")),
        attack_challenger_live_shadow_candidate_governance_lock_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_candidate_governance_lock_ready", False)),
        attack_challenger_live_shadow_candidate_governance_lock_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_candidate_governance_lock_lane", "")),
        attack_challenger_live_shadow_locked_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_entry_ready", False)),
        attack_challenger_live_shadow_locked_entry_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_entry_lane", "")),
        attack_challenger_live_shadow_locked_candidate_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_review_ready", False)),
        attack_challenger_live_shadow_locked_candidate_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_review_lane", "")),
        attack_challenger_live_shadow_locked_candidate_release_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_release_review_ready", False)),
        attack_challenger_live_shadow_locked_candidate_release_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_release_review_lane", "")),
        attack_challenger_live_shadow_locked_release_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_entry_ready", False)),
        attack_challenger_live_shadow_locked_release_entry_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_entry_lane", "")),
        attack_challenger_live_shadow_locked_release_candidate_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_candidate_review_ready", False)),
        attack_challenger_live_shadow_locked_release_candidate_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_candidate_review_lane", "")),
        attack_challenger_bridge_report=str(attack_challenger_state["attack_challenger_bridge_report"]),
    )
    latest_index_paths = _write_latest_index(analysis_dir=args.analysis_dir, index_payload=latest_index)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths={
                "btc_1d_operating_index": latest_index_paths["json"],
                "btc_1d_operating_index_md": latest_index_paths["md"],
            },
        )
    )
    operating_brief = build_operating_brief(analysis_dir=args.analysis_dir)
    operating_brief_paths = _write_operating_brief(analysis_dir=args.analysis_dir, brief=operating_brief)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths={
                "btc_1d_operating_brief": operating_brief_paths["json"],
                "btc_1d_operating_brief_txt": operating_brief_paths["txt"],
                "btc_1d_operating_brief_md": operating_brief_paths["md"],
            },
        )
    )
    latest_aliases = _refresh_contract_artifacts_after_paper(
        analysis_dir=args.analysis_dir,
        latest_aliases=latest_aliases,
    )
    contract_health = check_contract_health(analysis_dir=args.analysis_dir)
    contract_health_line = render_contract_health_line(contract_health)
    regression_lock_test = contract_health.get(
        "regression_lock_test",
        "tests/unit/test_btc_1d_operating_cli_help_contract.py",
    )
    execution_contract_state = _load_execution_contract_state(
        analysis_dir=args.analysis_dir,
        latest_aliases=latest_aliases,
        paper_execution_read=paper_execution_read,
        execution_health_line=execution_health_line,
    )
    latest_index = _latest_index(
        summary=latest_summary,
        latest_aliases=latest_aliases,
        contract_health=contract_health,
        research_stack_health_line=research_stack_health_line,
        combined_health_line=combined_health_line,
        paper_nightly_health_line=paper_nightly_health_line,
        execution_health_line=execution_health_line,
        execution_contract_health_line=str(execution_contract_state["execution_contract_health_line"]),
        execution_contract_read=str(execution_contract_state["execution_contract_read"]),
        execution_contract_aligned=bool(execution_contract_state["execution_contract_aligned"]),
        execution_contract_paper_ledger_snapshot_summary_aligned=bool(execution_contract_state["execution_contract_paper_ledger_snapshot_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"]),
        paper_execution_contract_checked=paper_execution_contract_checked,
        paper_execution_contract_aligned=paper_execution_contract_aligned,
        paper_execution_contract_checked_aligned=paper_execution_contract_checked_aligned,
        paper_execution_contract_aligned_aligned=paper_execution_contract_aligned_aligned,
        paper_execution_contract_checked_summary_aligned=paper_execution_contract_checked_summary_aligned,
        paper_execution_contract_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned,
        paper_execution_contract_checked_aligned_entry_aligned=paper_execution_contract_checked_aligned_entry_aligned,
        paper_execution_contract_aligned_aligned_entry_aligned=paper_execution_contract_aligned_aligned_entry_aligned,
        paper_execution_contract_checked_summary_aligned_entry_aligned=paper_execution_contract_checked_summary_aligned_entry_aligned,
        paper_execution_contract_aligned_summary_aligned_entry_aligned=paper_execution_contract_aligned_summary_aligned_entry_aligned,
        paper_execution_contract_checked_aligned_summary_aligned=paper_execution_contract_checked_aligned_summary_aligned,
        paper_execution_contract_aligned_aligned_summary_aligned=paper_execution_contract_aligned_aligned_summary_aligned,
        paper_execution_contract_checked_summary_aligned_summary_aligned=paper_execution_contract_checked_summary_aligned_summary_aligned,
        paper_execution_contract_aligned_summary_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned_summary_aligned,
        paper_execution_read=paper_execution_read,
        paper_exit_duplicate_run=paper_exit_duplicate_run,
        paper_ledger_consistent=paper_ledger_consistent,
        paper_ledger_snapshot=paper_ledger_snapshot,
        attack_challenger_candidate=str(attack_challenger_state["attack_challenger_candidate"]),
        attack_challenger_role_assignment=str(attack_challenger_state["attack_challenger_role_assignment"]),
        attack_challenger_promotion_ready=bool(attack_challenger_state["attack_challenger_promotion_ready"]),
        attack_challenger_next_step=str(attack_challenger_state["attack_challenger_next_step"]),
        attack_challenger_paper_validation_cagr=attack_challenger_state["attack_challenger_paper_validation_cagr"],
        attack_challenger_paper_validation_max_drawdown=attack_challenger_state["attack_challenger_paper_validation_max_drawdown"],
        attack_challenger_walk_forward_sensitivity_max_drift=attack_challenger_state["attack_challenger_walk_forward_sensitivity_max_drift"],
        attack_challenger_friction_final_decision=str(attack_challenger_state["attack_challenger_friction_final_decision"]),
        attack_challenger_bridge_entry_ready=bool(attack_challenger_state["attack_challenger_bridge_entry_ready"]),
        attack_challenger_bridge_queue_lane=str(attack_challenger_state["attack_challenger_bridge_queue_lane"]),
        attack_challenger_execution_contract_entry_ready=bool(attack_challenger_state["attack_challenger_execution_contract_entry_ready"]),
        attack_challenger_execution_contract_queue_lane=str(attack_challenger_state["attack_challenger_execution_contract_queue_lane"]),
        attack_challenger_operator_stack_handoff_ready=bool(attack_challenger_state["attack_challenger_operator_stack_handoff_ready"]),
        attack_challenger_operator_stack_handoff_lane=str(attack_challenger_state["attack_challenger_operator_stack_handoff_lane"]),
        attack_challenger_operator_runbook_candidate_entry_ready=bool(attack_challenger_state["attack_challenger_operator_runbook_candidate_entry_ready"]),
        attack_challenger_operator_runbook_candidate_entry_lane=str(attack_challenger_state["attack_challenger_operator_runbook_candidate_entry_lane"]),
        attack_challenger_operator_runbook_execution_entry_ready=bool(attack_challenger_state["attack_challenger_operator_runbook_execution_entry_ready"]),
        attack_challenger_operator_runbook_execution_entry_lane=str(attack_challenger_state["attack_challenger_operator_runbook_execution_entry_lane"]),
        attack_challenger_live_readiness_review_ready=bool(attack_challenger_state["attack_challenger_live_readiness_review_ready"]),
        attack_challenger_live_readiness_review_lane=str(attack_challenger_state["attack_challenger_live_readiness_review_lane"]),
        attack_challenger_live_shadow_activation_review_ready=bool(attack_challenger_state["attack_challenger_live_shadow_activation_review_ready"]),
        attack_challenger_live_shadow_activation_review_lane=str(attack_challenger_state["attack_challenger_live_shadow_activation_review_lane"]),
        attack_challenger_live_candidate_entry_ready=bool(attack_challenger_state["attack_challenger_live_candidate_entry_ready"]),
        attack_challenger_live_candidate_entry_lane=str(attack_challenger_state["attack_challenger_live_candidate_entry_lane"]),
        attack_challenger_live_operator_paper_entry_ready=bool(attack_challenger_state["attack_challenger_live_operator_paper_entry_ready"]),
        attack_challenger_live_operator_paper_entry_lane=str(attack_challenger_state["attack_challenger_live_operator_paper_entry_lane"]),
        attack_challenger_live_shadow_governance_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_governance_review_ready", False)),
        attack_challenger_live_shadow_governance_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_governance_review_lane", "")),
        attack_challenger_live_governed_shadow_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_governed_shadow_entry_ready", False)),
        attack_challenger_live_governed_shadow_entry_lane=str(attack_challenger_state.get("attack_challenger_live_governed_shadow_entry_lane", "")),
        attack_challenger_live_shadow_candidate_paper_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_candidate_paper_review_ready", False)),
        attack_challenger_live_shadow_candidate_paper_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_candidate_paper_review_lane", "")),
        attack_challenger_live_shadow_candidate_governance_lock_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_candidate_governance_lock_ready", False)),
        attack_challenger_live_shadow_candidate_governance_lock_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_candidate_governance_lock_lane", "")),
        attack_challenger_live_shadow_locked_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_entry_ready", False)),
        attack_challenger_live_shadow_locked_entry_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_entry_lane", "")),
        attack_challenger_live_shadow_locked_candidate_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_review_ready", False)),
        attack_challenger_live_shadow_locked_candidate_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_review_lane", "")),
        attack_challenger_live_shadow_locked_candidate_release_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_release_review_ready", False)),
        attack_challenger_live_shadow_locked_candidate_release_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_candidate_release_review_lane", "")),
        attack_challenger_live_shadow_locked_release_entry_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_entry_ready", False)),
        attack_challenger_live_shadow_locked_release_entry_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_entry_lane", "")),
        attack_challenger_live_shadow_locked_release_candidate_review_ready=bool(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_candidate_review_ready", False)),
        attack_challenger_live_shadow_locked_release_candidate_review_lane=str(attack_challenger_state.get("attack_challenger_live_shadow_locked_release_candidate_review_lane", "")),
        attack_challenger_bridge_report=str(attack_challenger_state["attack_challenger_bridge_report"]),
    )
    latest_index_paths = _write_latest_index(analysis_dir=args.analysis_dir, index_payload=latest_index)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths={
                "btc_1d_operating_index": latest_index_paths["json"],
                "btc_1d_operating_index_md": latest_index_paths["md"],
            },
        )
    )
    operating_brief = build_operating_brief(analysis_dir=args.analysis_dir)
    operating_brief_paths = _write_operating_brief(analysis_dir=args.analysis_dir, brief=operating_brief)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths={
                "btc_1d_operating_brief": operating_brief_paths["json"],
                "btc_1d_operating_brief_txt": operating_brief_paths["txt"],
                "btc_1d_operating_brief_md": operating_brief_paths["md"],
            },
        )
    )
    latest_aliases = _refresh_contract_artifacts_after_paper(
        analysis_dir=args.analysis_dir,
        latest_aliases=latest_aliases,
    )
    contract_health = check_contract_health(analysis_dir=args.analysis_dir)
    contract_health_line = render_contract_health_line(contract_health)
    regression_lock_test = contract_health.get(
        "regression_lock_test",
        "tests/unit/test_btc_1d_operating_cli_help_contract.py",
    )
    execution_contract_state = _load_execution_contract_state(
        analysis_dir=args.analysis_dir,
        latest_aliases=latest_aliases,
        paper_execution_read=paper_execution_read,
        execution_health_line=execution_health_line,
    )
    latest_index = _latest_index(
        summary=latest_summary,
        latest_aliases=latest_aliases,
        contract_health=contract_health,
        research_stack_health_line=research_stack_health_line,
        combined_health_line=combined_health_line,
        paper_nightly_health_line=paper_nightly_health_line,
        execution_health_line=execution_health_line,
        execution_contract_health_line=str(execution_contract_state["execution_contract_health_line"]),
        execution_contract_read=str(execution_contract_state["execution_contract_read"]),
        execution_contract_aligned=bool(execution_contract_state["execution_contract_aligned"]),
        execution_contract_paper_ledger_snapshot_summary_aligned=bool(execution_contract_state["execution_contract_paper_ledger_snapshot_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"]),
        paper_execution_contract_checked=paper_execution_contract_checked,
        paper_execution_contract_aligned=paper_execution_contract_aligned,
        paper_execution_contract_checked_aligned=paper_execution_contract_checked_aligned,
        paper_execution_contract_aligned_aligned=paper_execution_contract_aligned_aligned,
        paper_execution_contract_checked_summary_aligned=paper_execution_contract_checked_summary_aligned,
        paper_execution_contract_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned,
        paper_execution_contract_checked_aligned_entry_aligned=paper_execution_contract_checked_aligned_entry_aligned,
        paper_execution_contract_aligned_aligned_entry_aligned=paper_execution_contract_aligned_aligned_entry_aligned,
        paper_execution_contract_checked_summary_aligned_entry_aligned=paper_execution_contract_checked_summary_aligned_entry_aligned,
        paper_execution_contract_aligned_summary_aligned_entry_aligned=paper_execution_contract_aligned_summary_aligned_entry_aligned,
        paper_execution_contract_checked_aligned_summary_aligned=paper_execution_contract_checked_aligned_summary_aligned,
        paper_execution_contract_aligned_aligned_summary_aligned=paper_execution_contract_aligned_aligned_summary_aligned,
        paper_execution_contract_checked_summary_aligned_summary_aligned=paper_execution_contract_checked_summary_aligned_summary_aligned,
        paper_execution_contract_aligned_summary_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned_summary_aligned,
        paper_execution_read=paper_execution_read,
        paper_exit_duplicate_run=paper_exit_duplicate_run,
        paper_ledger_consistent=paper_ledger_consistent,
        paper_ledger_snapshot=paper_ledger_snapshot,
    )
    latest_index_paths = _write_latest_index(analysis_dir=args.analysis_dir, index_payload=latest_index)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths={
                "btc_1d_operating_index": latest_index_paths["json"],
                "btc_1d_operating_index_md": latest_index_paths["md"],
            },
        )
    )
    operating_brief = build_operating_brief(analysis_dir=args.analysis_dir)
    operating_brief_paths = _write_operating_brief(analysis_dir=args.analysis_dir, brief=operating_brief)
    latest_aliases.update(
        _write_latest_aliases(
            analysis_dir=args.analysis_dir,
            paths={
                "btc_1d_operating_brief": operating_brief_paths["json"],
                "btc_1d_operating_brief_txt": operating_brief_paths["txt"],
                "btc_1d_operating_brief_md": operating_brief_paths["md"],
            },
        )
    )
    latest_aliases = _refresh_contract_artifacts_after_paper(
        analysis_dir=args.analysis_dir,
        latest_aliases=latest_aliases,
    )
    refresh_payload = refresh_operator_stack(
        analysis_dir=args.analysis_dir,
        sync_passes=max(int(args.sync_passes), 1),
    )
    latest_aliases = dict(refresh_payload["latest_aliases"])
    contract_health = dict(refresh_payload["contract_health"])
    contract_health_line = render_contract_health_line(contract_health)
    regression_lock_test = contract_health.get(
        "regression_lock_test",
        "tests/unit/test_btc_1d_operating_cli_help_contract.py",
    )
    execution_contract_state = dict(refresh_payload["execution_contract_state"])
    latest_index_paths = {
        "json": str(latest_aliases["btc_1d_operating_index"]),
        "md": str(latest_aliases["btc_1d_operating_index_md"]),
    }
    operating_brief_paths = {
        "json": str(latest_aliases["btc_1d_operating_brief"]),
        "txt": str(latest_aliases["btc_1d_operating_brief_txt"]),
        "md": str(latest_aliases["btc_1d_operating_brief_md"]),
    }
    output_payload = _build_shadow_update_output(
        practical_health=practical_health,
        practical_health_line=practical_health_line,
        research_stack_health=research_stack_health,
        research_stack_health_line=research_stack_health_line,
        contract_health=contract_health,
        contract_health_line=contract_health_line,
        regression_lock_test=regression_lock_test,
        combined_health_line=combined_health_line,
        paper_nightly_health_line=paper_nightly_health_line,
        execution_health_line=execution_health_line,
        execution_contract_health_line=str(execution_contract_state["execution_contract_health_line"]),
        execution_contract_read=str(execution_contract_state["execution_contract_read"]),
        execution_contract_aligned=bool(execution_contract_state["execution_contract_aligned"]),
        execution_contract_paper_ledger_snapshot_summary_aligned=bool(execution_contract_state["execution_contract_paper_ledger_snapshot_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"]),
        execution_contract_paper_execution_contract_checked_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"]),
        execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=bool(execution_contract_state["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"]),
        paper_execution_contract_checked=paper_execution_contract_checked,
        paper_execution_contract_aligned=paper_execution_contract_aligned,
        paper_execution_contract_checked_aligned=paper_execution_contract_checked_aligned,
        paper_execution_contract_aligned_aligned=paper_execution_contract_aligned_aligned,
        paper_execution_contract_checked_summary_aligned=paper_execution_contract_checked_summary_aligned,
        paper_execution_contract_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned,
        paper_execution_contract_checked_aligned_entry_aligned=paper_execution_contract_checked_aligned_entry_aligned,
        paper_execution_contract_aligned_aligned_entry_aligned=paper_execution_contract_aligned_aligned_entry_aligned,
        paper_execution_contract_checked_summary_aligned_entry_aligned=paper_execution_contract_checked_summary_aligned_entry_aligned,
        paper_execution_contract_aligned_summary_aligned_entry_aligned=paper_execution_contract_aligned_summary_aligned_entry_aligned,
        paper_execution_contract_checked_aligned_summary_aligned=paper_execution_contract_checked_aligned_summary_aligned,
        paper_execution_contract_aligned_aligned_summary_aligned=paper_execution_contract_aligned_aligned_summary_aligned,
        paper_execution_contract_checked_summary_aligned_summary_aligned=paper_execution_contract_checked_summary_aligned_summary_aligned,
        paper_execution_contract_aligned_summary_aligned_summary_aligned=paper_execution_contract_aligned_summary_aligned_summary_aligned,
        paper_execution_read=paper_execution_read,
        paper_exit_duplicate_run=paper_exit_duplicate_run,
        paper_ledger_consistent=paper_ledger_consistent,
        paper_ledger_snapshot=paper_ledger_snapshot,
        latest_summary=latest_summary,
        latest_summary_paths=latest_summary_paths,
        latest_index_paths=latest_index_paths,
        operating_brief_paths=operating_brief_paths,
        latest_aliases=latest_aliases,
        carry_validation=carry_validation,
        survivability_validation=survivability_validation,
        eth_regression=eth_regression,
        walk_forward=walk_forward,
        shadow_packet_result=shadow_packet_result,
        operating_snapshot=operating_snapshot,
        eth_symbol=args.eth_symbol,
        carry_periods=args.periods,
        survivability_periods=args.survivability_periods,
        walk_forward_periods=args.walk_forward_periods,
        paper_nightly=paper_nightly,
    )
    print(json.dumps(output_payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
