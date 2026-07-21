from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check the latest BTC 1d shadow health against the expected operating gates. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--as-json", action="store_true")
    parser.add_argument("--expected-candidate", default="low_vol_cap_050_025_minvol020_p2200")
    parser.add_argument("--expected-scope", default="BTC-only")
    parser.add_argument("--expected-shadow-decision", default="shadow_ready_for_btc_only")
    parser.add_argument("--expected-carry-decision", default="PASS")
    parser.add_argument("--expected-survivability-decision", default="PASS")
    parser.add_argument("--expected-friction-decision", default="continue")
    parser.add_argument("--expected-eth-pass-rate", type=float, default=0.0)
    parser.add_argument("--max-walk-forward-drift", type=float, default=0.15)
    parser.add_argument("--min-carry-sharpe", type=float, default=1.0)
    parser.add_argument("--min-survivability-sharpe", type=float, default=1.0)
    parser.add_argument("--min-friction-sharpe", type=float, default=1.0)
    parser.add_argument("--min-oos-sharpe", type=float, default=0.5)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _render_paper_ledger_snapshot_read(snapshot: dict[str, Any] | None) -> str:
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
    return bool(summary.get(field, summary.get(legacy_field, False)))


def check_shadow_health(*, analysis_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    summary = _load_json(analysis_dir / "btc_1d_latest_summary_latest.json")
    shadow_packet = _load_json(analysis_dir / "btc_1d_shadow_packet_latest.json")
    operating_index_path = analysis_dir / "btc_1d_operating_index_latest.json"
    operating_brief_path = analysis_dir / "btc_1d_operating_brief_latest.json"
    operating_index = _load_json(operating_index_path) if operating_index_path.exists() else None
    operating_brief = _load_json(operating_brief_path) if operating_brief_path.exists() else None
    failures: list[str] = []
    attack_challenger_remote_monitoring_deployment_handoff_ready = (
        bool(
            operating_index.get("attack_challenger_remote_monitoring_deployment_handoff_ready", False)
        )
        if operating_index is not None
        else False
    )
    attack_challenger_next_step = (
        str(operating_index.get("attack_challenger_next_step", ""))
        if operating_index is not None
        else ""
    )
    attack_challenger_bridge_report = (
        str(operating_index.get("attack_challenger_bridge_report", ""))
        if operating_index is not None
        else ""
    )
    deployment_monitoring_active = (
        bool(operating_index.get("deployment_monitoring_active", False))
        if operating_index is not None
        else False
    )
    operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready = (
        bool(
            operating_brief.get(
                "attack_challenger_remote_monitoring_deployment_handoff_ready",
                False,
            )
        )
        if operating_brief is not None
        else None
    )
    operating_brief_attack_challenger_next_step = (
        str(operating_brief.get("attack_challenger_next_step", ""))
        if operating_brief is not None
        else None
    )
    operating_brief_attack_challenger_bridge_report = (
        str(operating_brief.get("attack_challenger_bridge_report", ""))
        if operating_brief is not None
        else None
    )
    operating_brief_deployment_monitoring_active = (
        bool(operating_brief.get("deployment_monitoring_active", False))
        if operating_brief is not None
        else None
    )

    if operating_brief is not None:
        if (
            operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready
            != attack_challenger_remote_monitoring_deployment_handoff_ready
        ):
            failures.append(
                "attack challenger remote monitoring deployment handoff ready brief mismatch: "
                f"brief={operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready} "
                f"index={attack_challenger_remote_monitoring_deployment_handoff_ready}"
            )
        if operating_brief_attack_challenger_next_step != attack_challenger_next_step:
            failures.append(
                "attack challenger next step brief mismatch: "
                f"brief={operating_brief_attack_challenger_next_step} "
                f"index={attack_challenger_next_step}"
            )
        if operating_brief_attack_challenger_bridge_report != attack_challenger_bridge_report:
            failures.append(
                "attack challenger bridge report brief mismatch: "
                f"brief={operating_brief_attack_challenger_bridge_report} "
                f"index={attack_challenger_bridge_report}"
            )
        if operating_brief_deployment_monitoring_active != deployment_monitoring_active:
            failures.append(
                "deployment monitoring active brief mismatch: "
                f"brief={operating_brief_deployment_monitoring_active} "
                f"index={deployment_monitoring_active}"
            )

    if summary["candidate"] != args.expected_candidate:
        failures.append(
            f"candidate mismatch: expected {args.expected_candidate}, got {summary['candidate']}"
        )
    if summary["scope"] != args.expected_scope:
        failures.append(f"scope mismatch: expected {args.expected_scope}, got {summary['scope']}")
    if summary["shadow_decision"] != args.expected_shadow_decision:
        failures.append(
            f"shadow decision mismatch: expected {args.expected_shadow_decision}, got {summary['shadow_decision']}"
        )
    if summary["carry"]["decision"] != args.expected_carry_decision:
        failures.append(
            f"carry decision mismatch: expected {args.expected_carry_decision}, got {summary['carry']['decision']}"
        )
    if summary["survivability"]["decision"] != args.expected_survivability_decision:
        failures.append(
            "survivability decision mismatch: "
            f"expected {args.expected_survivability_decision}, got {summary['survivability']['decision']}"
        )
    if not summary["walk_forward"]["passed"]:
        failures.append("walk-forward gate failed")
    if summary["friction"]["decision"] != args.expected_friction_decision:
        failures.append(
            f"friction decision mismatch: expected {args.expected_friction_decision}, got {summary['friction']['decision']}"
        )
    if float(summary["eth_cross_check"]["pass_rate"]) != args.expected_eth_pass_rate:
        failures.append(
            "eth pass rate mismatch: "
            f"expected {args.expected_eth_pass_rate}, got {summary['eth_cross_check']['pass_rate']}"
        )

    if float(summary["carry"]["sharpe"]) < args.min_carry_sharpe:
        failures.append(
            f"carry sharpe below floor: {summary['carry']['sharpe']:.4f} < {args.min_carry_sharpe:.4f}"
        )
    if float(summary["survivability"]["sharpe"]) < args.min_survivability_sharpe:
        failures.append(
            "survivability sharpe below floor: "
            f"{summary['survivability']['sharpe']:.4f} < {args.min_survivability_sharpe:.4f}"
        )
    if float(summary["friction"]["heaviest_level_sharpe"]) < args.min_friction_sharpe:
        failures.append(
            "friction sharpe below floor: "
            f"{summary['friction']['heaviest_level_sharpe']:.4f} < {args.min_friction_sharpe:.4f}"
        )
    if float(summary["walk_forward"]["oos_sharpe"]) < args.min_oos_sharpe:
        failures.append(
            f"walk-forward oos sharpe below floor: {summary['walk_forward']['oos_sharpe']:.4f} < {args.min_oos_sharpe:.4f}"
        )
    if float(summary["walk_forward"]["sensitivity_max_drift"]) > args.max_walk_forward_drift:
        failures.append(
            "walk-forward drift above ceiling: "
            f"{summary['walk_forward']['sensitivity_max_drift']:.4f} > {args.max_walk_forward_drift:.4f}"
        )
    if summary["walk_forward"]["unstable_parameters"]:
        failures.append(
            f"unstable walk-forward parameters present: {summary['walk_forward']['unstable_parameters']}"
        )

    if shadow_packet["status"] != "carryable_candidate":
        failures.append(f"shadow packet status mismatch: expected carryable_candidate, got {shadow_packet['status']}")
    if shadow_packet["paper_validation_decision"] != args.expected_carry_decision:
        failures.append(
            "shadow packet carry decision mismatch: "
            f"expected {args.expected_carry_decision}, got {shadow_packet['paper_validation_decision']}"
        )
    if shadow_packet["survivability_validation_decision"] != args.expected_survivability_decision:
        failures.append(
            "shadow packet survivability decision mismatch: "
            f"expected {args.expected_survivability_decision}, got {shadow_packet['survivability_validation_decision']}"
        )
    if shadow_packet["friction_validation_heaviest_level"]["decision"] != "PASS":
        failures.append(
            "shadow packet heaviest friction decision mismatch: "
            f"expected PASS, got {shadow_packet['friction_validation_heaviest_level']['decision']}"
        )

    paper_checked = False
    paper_execution_read = None
    paper_exit_duplicate_run = None
    paper_ledger_snapshot_read = None
    paper_execution_contract_checked = None
    paper_execution_contract_aligned = None
    operating_index_paper_execution_contract_checked = None
    operating_index_paper_execution_contract_aligned = None
    operating_index_paper_execution_contract_checked_aligned = None
    operating_index_paper_execution_contract_aligned_aligned = None
    operating_index_paper_execution_contract_checked_summary_aligned = None
    operating_index_paper_execution_contract_aligned_summary_aligned = None
    operating_index_paper_execution_contract_checked_aligned_entry_aligned = None
    operating_index_paper_execution_contract_aligned_aligned_entry_aligned = None
    operating_index_paper_execution_contract_checked_summary_aligned_entry_aligned = None
    operating_index_paper_execution_contract_aligned_summary_aligned_entry_aligned = None
    operating_index_paper_execution_contract_checked_aligned_summary_aligned = None
    operating_index_paper_execution_contract_aligned_aligned_summary_aligned = None
    operating_index_paper_execution_contract_checked_summary_aligned_summary_aligned = None
    operating_index_paper_execution_contract_aligned_summary_aligned_summary_aligned = None
    operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned = None
    operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = None
    operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = None
    operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = None
    operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned = None
    operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = None
    operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = None
    operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = None
    operating_brief_paper_execution_contract_checked = None
    operating_brief_paper_execution_contract_aligned = None
    operating_brief_paper_execution_contract_checked_aligned = None
    operating_brief_paper_execution_contract_aligned_aligned = None
    operating_brief_paper_execution_contract_checked_summary_aligned = None
    operating_brief_paper_execution_contract_aligned_summary_aligned = None
    operating_brief_paper_execution_contract_checked_aligned_entry_aligned = None
    operating_brief_paper_execution_contract_aligned_aligned_entry_aligned = None
    operating_brief_paper_execution_contract_checked_summary_aligned_entry_aligned = None
    operating_brief_paper_execution_contract_aligned_summary_aligned_entry_aligned = None
    operating_brief_paper_execution_contract_checked_aligned_summary_aligned = None
    operating_brief_paper_execution_contract_aligned_aligned_summary_aligned = None
    operating_brief_paper_execution_contract_checked_summary_aligned_summary_aligned = None
    operating_brief_paper_execution_contract_aligned_summary_aligned_summary_aligned = None
    operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned = None
    operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = None
    operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = None
    operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = None
    operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned = None
    operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = None
    operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = None
    operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = None
    execution_contract_checked = False
    execution_contract_aligned = None
    execution_contract_paper_execution_contract_checked_aligned = None
    execution_contract_paper_execution_contract_aligned_aligned = None
    execution_contract_paper_execution_contract_checked_summary_aligned = None
    execution_contract_paper_execution_contract_aligned_summary_aligned = None
    execution_contract_paper_execution_contract_checked_aligned_entry_aligned = None
    execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = None
    execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = None
    execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = None
    execution_contract_paper_execution_contract_checked_aligned_summary_aligned = None
    execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = None
    execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = None
    execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = None
    execution_contract_paper_ledger_snapshot_read = None
    quick_read_contract_checked = False
    quick_read_contract_operating_contract_aligned = None
    quick_read_contract_paper_execution_contract_aligned = None
    quick_read_contract_contract_health_aligned = None
    quick_read_contract_partitioned = None
    operating_index_contract_health_operating_contract_aligned = None
    operating_index_contract_health_paper_execution_contract_aligned = None
    operating_index_contract_health_aligned = None
    operating_index_contract_health_contracts_are_well_partitioned = None
    operating_brief_contract_health_operating_contract_aligned = None
    operating_brief_contract_health_paper_execution_contract_aligned = None
    operating_brief_contract_health_aligned = None
    operating_brief_contract_health_contracts_are_well_partitioned = None
    if operating_index:
        quick_read_contract_path = analysis_dir / "btc_1d_quick_read_contract_screen_latest.json"
        if quick_read_contract_path.exists():
            quick_read_contract_payload = _load_json(quick_read_contract_path)
            quick_read_contract_summary = quick_read_contract_payload.get("contract_summary", {})
            quick_read_contract_verdict = quick_read_contract_payload.get("contract_verdict", {})
            quick_read_contract_checked = True
            quick_read_contract_operating_contract_aligned = bool(
                quick_read_contract_summary.get("operating_contract_aligned", False)
            )
            quick_read_contract_paper_execution_contract_aligned = bool(
                quick_read_contract_summary.get("paper_execution_contract_aligned", False)
            )
            quick_read_contract_contract_health_aligned = bool(
                quick_read_contract_summary.get("contract_health_aligned", False)
            )
            quick_read_contract_partitioned = bool(
                quick_read_contract_verdict.get("contracts_are_well_partitioned", False)
            )
            if not quick_read_contract_operating_contract_aligned:
                failures.append("quick read contract operating alignment failed")
            if not quick_read_contract_paper_execution_contract_aligned:
                failures.append("quick read contract paper execution alignment failed")
            if not quick_read_contract_contract_health_aligned:
                failures.append("quick read contract health alignment failed")
            if not quick_read_contract_partitioned:
                failures.append("quick read contract partitioning failed")
            operating_index_contract_health_operating_contract_aligned = bool(
                operating_index.get("contract_health_operating_contract_aligned", False)
            )
            if (
                operating_index_contract_health_operating_contract_aligned
                != quick_read_contract_operating_contract_aligned
            ):
                failures.append(
                    "contract health operating aligned mismatch: "
                    f"index={operating_index_contract_health_operating_contract_aligned} "
                    f"quick_read={quick_read_contract_operating_contract_aligned}"
                )
            operating_index_contract_health_paper_execution_contract_aligned = bool(
                operating_index.get("contract_health_paper_execution_contract_aligned", False)
            )
            if (
                operating_index_contract_health_paper_execution_contract_aligned
                != quick_read_contract_paper_execution_contract_aligned
            ):
                failures.append(
                    "contract health paper execution aligned mismatch: "
                    f"index={operating_index_contract_health_paper_execution_contract_aligned} "
                    f"quick_read={quick_read_contract_paper_execution_contract_aligned}"
                )
            operating_index_contract_health_aligned = bool(
                operating_index.get("contract_health_aligned", False)
            )
            if (
                operating_index_contract_health_aligned
                != quick_read_contract_contract_health_aligned
            ):
                failures.append(
                    "contract health aligned mismatch: "
                    f"index={operating_index_contract_health_aligned} "
                    f"quick_read={quick_read_contract_contract_health_aligned}"
                )
            operating_index_contract_health_contracts_are_well_partitioned = bool(
                operating_index.get("contract_health_contracts_are_well_partitioned", False)
            )
            if (
                operating_index_contract_health_contracts_are_well_partitioned
                != quick_read_contract_partitioned
            ):
                failures.append(
                    "contract health partitioned mismatch: "
                    f"index={operating_index_contract_health_contracts_are_well_partitioned} "
                    f"quick_read={quick_read_contract_partitioned}"
                )
            if operating_brief is not None:
                operating_brief_contract_health_operating_contract_aligned = bool(
                    operating_brief.get("contract_health_operating_contract_aligned", False)
                )
                if (
                    operating_brief_contract_health_operating_contract_aligned
                    != quick_read_contract_operating_contract_aligned
                ):
                    failures.append(
                        "contract health operating aligned brief mismatch: "
                        f"brief={operating_brief_contract_health_operating_contract_aligned} "
                        f"quick_read={quick_read_contract_operating_contract_aligned}"
                    )
                operating_brief_contract_health_paper_execution_contract_aligned = bool(
                    operating_brief.get("contract_health_paper_execution_contract_aligned", False)
                )
                if (
                    operating_brief_contract_health_paper_execution_contract_aligned
                    != quick_read_contract_paper_execution_contract_aligned
                ):
                    failures.append(
                        "contract health paper execution aligned brief mismatch: "
                        f"brief={operating_brief_contract_health_paper_execution_contract_aligned} "
                        f"quick_read={quick_read_contract_paper_execution_contract_aligned}"
                    )
                operating_brief_contract_health_aligned = bool(
                    operating_brief.get("contract_health_aligned", False)
                )
                if (
                    operating_brief_contract_health_aligned
                    != quick_read_contract_contract_health_aligned
                ):
                    failures.append(
                        "contract health aligned brief mismatch: "
                        f"brief={operating_brief_contract_health_aligned} "
                        f"quick_read={quick_read_contract_contract_health_aligned}"
                    )
                operating_brief_contract_health_contracts_are_well_partitioned = bool(
                    operating_brief.get("contract_health_contracts_are_well_partitioned", False)
                )
                if (
                    operating_brief_contract_health_contracts_are_well_partitioned
                    != quick_read_contract_partitioned
                ):
                    failures.append(
                        "contract health partitioned brief mismatch: "
                        f"brief={operating_brief_contract_health_contracts_are_well_partitioned} "
                        f"quick_read={quick_read_contract_partitioned}"
                    )
        paper_summary_path_raw = operating_index.get("paper_nightly_summary")
        if paper_summary_path_raw:
            paper_summary_path = Path(paper_summary_path_raw)
            if not paper_summary_path.is_absolute():
                paper_summary_path = analysis_dir.parent / paper_summary_path
            if paper_summary_path.exists():
                paper_summary = _load_json(paper_summary_path)
                paper_checked = True
                paper_execution_read = paper_summary.get("paper_execution_read")
                paper_exit_duplicate_run = bool(paper_summary.get("paper_exit_duplicate_run", False))
                paper_ledger_snapshot_read = _render_paper_ledger_snapshot_read(
                    paper_summary.get("paper_ledger_snapshot")
                )
                paper_execution_contract_checked = bool(
                    paper_summary.get("execution_contract_checked", False)
                )
                paper_execution_contract_aligned = bool(
                    paper_summary.get("execution_contract_aligned", False)
                )
                paper_execution_contract_checked_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_checked_aligned",
                    "execution_contract_paper_execution_contract_checked_aligned",
                )
                paper_execution_contract_aligned_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_aligned_aligned",
                    "execution_contract_paper_execution_contract_aligned_aligned",
                )
                paper_execution_contract_checked_summary_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_checked_summary_aligned",
                    "execution_contract_paper_execution_contract_checked_summary_aligned",
                )
                paper_execution_contract_aligned_summary_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_aligned_summary_aligned",
                    "execution_contract_paper_execution_contract_aligned_summary_aligned",
                )
                paper_execution_contract_checked_aligned_entry_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_checked_aligned_entry_aligned",
                    "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
                )
                paper_execution_contract_aligned_aligned_entry_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_aligned_aligned_entry_aligned",
                    "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
                )
                paper_execution_contract_checked_summary_aligned_entry_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_checked_summary_aligned_entry_aligned",
                    "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
                )
                paper_execution_contract_aligned_summary_aligned_entry_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_aligned_summary_aligned_entry_aligned",
                    "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
                )
                paper_execution_contract_checked_aligned_summary_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_checked_aligned_summary_aligned",
                    "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
                )
                paper_execution_contract_aligned_aligned_summary_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_aligned_aligned_summary_aligned",
                    "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
                )
                paper_execution_contract_checked_summary_aligned_summary_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_checked_summary_aligned_summary_aligned",
                    "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
                )
                paper_execution_contract_aligned_summary_aligned_summary_aligned_summary = _paper_summary_contract_bool(
                    paper_summary,
                    "paper_execution_contract_aligned_summary_aligned_summary_aligned",
                    "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
                )
                if not bool(paper_summary.get("paper_ledger_consistent", False)):
                    failures.append(
                        "paper ledger consistency failed: "
                        f"{paper_summary.get('paper_ledger_consistency', {})}"
                    )
                if operating_index.get("paper_execution_read", "") != paper_execution_read:
                    failures.append(
                        "paper execution read mismatch: "
                        f"index={operating_index.get('paper_execution_read', '')} "
                        f"summary={paper_execution_read}"
                    )
                if bool(operating_index.get("paper_exit_duplicate_run", False)) != paper_exit_duplicate_run:
                    failures.append(
                        "paper exit duplicate run mismatch: "
                        f"index={bool(operating_index.get('paper_exit_duplicate_run', False))} "
                        f"summary={paper_exit_duplicate_run}"
                    )
                if bool(operating_index.get("paper_ledger_consistent", False)) != bool(
                    paper_summary.get("paper_ledger_consistent", False)
                ):
                    failures.append(
                        "paper ledger consistent mismatch: "
                        f"index={bool(operating_index.get('paper_ledger_consistent', False))} "
                        f"summary={bool(paper_summary.get('paper_ledger_consistent', False))}"
                    )
                if bool(operating_index.get("paper_execution_contract_checked", False)) != paper_execution_contract_checked:
                    failures.append(
                        "paper execution contract checked mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_checked', False))} "
                        f"summary={paper_execution_contract_checked}"
                    )
                operating_index_paper_execution_contract_checked = bool(
                    operating_index.get("paper_execution_contract_checked", False)
                )
                if bool(operating_index.get("paper_execution_contract_aligned", False)) != paper_execution_contract_aligned:
                    failures.append(
                        "paper execution contract aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_aligned', False))} "
                        f"summary={paper_execution_contract_aligned}"
                    )
                operating_index_paper_execution_contract_aligned = bool(
                    operating_index.get("paper_execution_contract_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_checked_aligned", False)
                ) != paper_execution_contract_checked_aligned_summary:
                    failures.append(
                        "paper execution contract checked aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_checked_aligned', False))} "
                        f"summary={paper_execution_contract_checked_aligned_summary}"
                    )
                operating_index_paper_execution_contract_checked_aligned = bool(
                    operating_index.get("paper_execution_contract_checked_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_aligned_aligned", False)
                ) != paper_execution_contract_aligned_aligned_summary:
                    failures.append(
                        "paper execution contract aligned aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_aligned_aligned', False))} "
                        f"summary={paper_execution_contract_aligned_aligned_summary}"
                    )
                operating_index_paper_execution_contract_aligned_aligned = bool(
                    operating_index.get("paper_execution_contract_aligned_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_checked_summary_aligned", False)
                ) != paper_execution_contract_checked_summary_aligned_summary:
                    failures.append(
                        "paper execution contract checked summary aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_checked_summary_aligned', False))} "
                        f"summary={paper_execution_contract_checked_summary_aligned_summary}"
                    )
                operating_index_paper_execution_contract_checked_summary_aligned = bool(
                    operating_index.get("paper_execution_contract_checked_summary_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_aligned_summary_aligned", False)
                ) != paper_execution_contract_aligned_summary_aligned_summary:
                    failures.append(
                        "paper execution contract aligned summary aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_aligned_summary_aligned', False))} "
                        f"summary={paper_execution_contract_aligned_summary_aligned_summary}"
                    )
                operating_index_paper_execution_contract_aligned_summary_aligned = bool(
                    operating_index.get("paper_execution_contract_aligned_summary_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_checked_aligned_entry_aligned", False)
                ) != paper_execution_contract_checked_aligned_entry_aligned_summary:
                    failures.append(
                        "paper execution contract checked aligned entry aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_checked_aligned_entry_aligned', False))} "
                        f"summary={paper_execution_contract_checked_aligned_entry_aligned_summary}"
                    )
                operating_index_paper_execution_contract_checked_aligned_entry_aligned = bool(
                    operating_index.get("paper_execution_contract_checked_aligned_entry_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
                ) != paper_execution_contract_aligned_aligned_entry_aligned_summary:
                    failures.append(
                        "paper execution contract aligned aligned entry aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_aligned_aligned_entry_aligned', False))} "
                        f"summary={paper_execution_contract_aligned_aligned_entry_aligned_summary}"
                    )
                operating_index_paper_execution_contract_aligned_aligned_entry_aligned = bool(
                    operating_index.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
                ) != paper_execution_contract_checked_summary_aligned_entry_aligned_summary:
                    failures.append(
                        "paper execution contract checked summary aligned entry aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False))} "
                        f"summary={paper_execution_contract_checked_summary_aligned_entry_aligned_summary}"
                    )
                operating_index_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
                    operating_index.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
                ) != paper_execution_contract_aligned_summary_aligned_entry_aligned_summary:
                    failures.append(
                        "paper execution contract aligned summary aligned entry aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False))} "
                        f"summary={paper_execution_contract_aligned_summary_aligned_entry_aligned_summary}"
                    )
                operating_index_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
                    operating_index.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_checked_aligned_summary_aligned", False)
                ) != paper_execution_contract_checked_aligned_summary_aligned_summary:
                    failures.append(
                        "paper execution contract checked aligned summary aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_checked_aligned_summary_aligned', False))} "
                        f"summary={paper_execution_contract_checked_aligned_summary_aligned_summary}"
                    )
                operating_index_paper_execution_contract_checked_aligned_summary_aligned = bool(
                    operating_index.get("paper_execution_contract_checked_aligned_summary_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
                ) != paper_execution_contract_aligned_aligned_summary_aligned_summary:
                    failures.append(
                        "paper execution contract aligned aligned summary aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_aligned_aligned_summary_aligned', False))} "
                        f"summary={paper_execution_contract_aligned_aligned_summary_aligned_summary}"
                    )
                operating_index_paper_execution_contract_aligned_aligned_summary_aligned = bool(
                    operating_index.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
                ) != paper_execution_contract_checked_summary_aligned_summary_aligned_summary:
                    failures.append(
                        "paper execution contract checked summary aligned summary aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False))} "
                        f"summary={paper_execution_contract_checked_summary_aligned_summary_aligned_summary}"
                    )
                operating_index_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
                    operating_index.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
                )
                if bool(
                    operating_index.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
                ) != paper_execution_contract_aligned_summary_aligned_summary_aligned_summary:
                    failures.append(
                        "paper execution contract aligned summary aligned summary aligned mismatch: "
                        f"index={bool(operating_index.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False))} "
                        f"summary={paper_execution_contract_aligned_summary_aligned_summary_aligned_summary}"
                    )
                operating_index_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
                    operating_index.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
                )
                operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
                        False,
                    )
                )
                operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
                        False,
                    )
                )
                operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
                        False,
                    )
                )
                operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
                        False,
                    )
                )
                operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
                        False,
                    )
                )
                operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
                        False,
                    )
                )
                operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
                        False,
                    )
                )
                operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
                    operating_index.get(
                        "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
                        False,
                    )
                )
                if operating_brief is not None:
                    if bool(operating_brief.get("paper_execution_contract_checked", False)) != paper_execution_contract_checked:
                        failures.append(
                            "paper execution contract checked brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_checked', False))} "
                            f"summary={paper_execution_contract_checked}"
                        )
                    operating_brief_paper_execution_contract_checked = bool(
                        operating_brief.get("paper_execution_contract_checked", False)
                    )
                    if bool(operating_brief.get("paper_execution_contract_aligned", False)) != paper_execution_contract_aligned:
                        failures.append(
                            "paper execution contract aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_aligned', False))} "
                            f"summary={paper_execution_contract_aligned}"
                        )
                    operating_brief_paper_execution_contract_aligned = bool(
                        operating_brief.get("paper_execution_contract_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_checked_aligned", False)
                    ) != paper_execution_contract_checked_aligned_summary:
                        failures.append(
                            "paper execution contract checked aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_checked_aligned', False))} "
                            f"summary={paper_execution_contract_checked_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_checked_aligned = bool(
                        operating_brief.get("paper_execution_contract_checked_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_aligned_aligned", False)
                    ) != paper_execution_contract_aligned_aligned_summary:
                        failures.append(
                            "paper execution contract aligned aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_aligned_aligned', False))} "
                            f"summary={paper_execution_contract_aligned_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_aligned_aligned = bool(
                        operating_brief.get("paper_execution_contract_aligned_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_checked_summary_aligned", False)
                    ) != paper_execution_contract_checked_summary_aligned_summary:
                        failures.append(
                            "paper execution contract checked summary aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_checked_summary_aligned', False))} "
                            f"summary={paper_execution_contract_checked_summary_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_checked_summary_aligned = bool(
                        operating_brief.get("paper_execution_contract_checked_summary_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_aligned_summary_aligned", False)
                    ) != paper_execution_contract_aligned_summary_aligned_summary:
                        failures.append(
                            "paper execution contract aligned summary aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_aligned_summary_aligned', False))} "
                            f"summary={paper_execution_contract_aligned_summary_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_aligned_summary_aligned = bool(
                        operating_brief.get("paper_execution_contract_aligned_summary_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_checked_aligned_entry_aligned", False)
                    ) != paper_execution_contract_checked_aligned_entry_aligned_summary:
                        failures.append(
                            "paper execution contract checked aligned entry aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_checked_aligned_entry_aligned', False))} "
                            f"summary={paper_execution_contract_checked_aligned_entry_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_checked_aligned_entry_aligned = bool(
                        operating_brief.get("paper_execution_contract_checked_aligned_entry_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
                    ) != paper_execution_contract_aligned_aligned_entry_aligned_summary:
                        failures.append(
                            "paper execution contract aligned aligned entry aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_aligned_aligned_entry_aligned', False))} "
                            f"summary={paper_execution_contract_aligned_aligned_entry_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_aligned_aligned_entry_aligned = bool(
                        operating_brief.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
                    ) != paper_execution_contract_checked_summary_aligned_entry_aligned_summary:
                        failures.append(
                            "paper execution contract checked summary aligned entry aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False))} "
                            f"summary={paper_execution_contract_checked_summary_aligned_entry_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
                        operating_brief.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
                    ) != paper_execution_contract_aligned_summary_aligned_entry_aligned_summary:
                        failures.append(
                            "paper execution contract aligned summary aligned entry aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False))} "
                            f"summary={paper_execution_contract_aligned_summary_aligned_entry_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
                        operating_brief.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_checked_aligned_summary_aligned", False)
                    ) != paper_execution_contract_checked_aligned_summary_aligned_summary:
                        failures.append(
                            "paper execution contract checked aligned summary aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_checked_aligned_summary_aligned', False))} "
                            f"summary={paper_execution_contract_checked_aligned_summary_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_checked_aligned_summary_aligned = bool(
                        operating_brief.get("paper_execution_contract_checked_aligned_summary_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
                    ) != paper_execution_contract_aligned_aligned_summary_aligned_summary:
                        failures.append(
                            "paper execution contract aligned aligned summary aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_aligned_aligned_summary_aligned', False))} "
                            f"summary={paper_execution_contract_aligned_aligned_summary_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_aligned_aligned_summary_aligned = bool(
                        operating_brief.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
                    ) != paper_execution_contract_checked_summary_aligned_summary_aligned_summary:
                        failures.append(
                            "paper execution contract checked summary aligned summary aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False))} "
                            f"summary={paper_execution_contract_checked_summary_aligned_summary_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
                        operating_brief.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
                    )
                    if bool(
                        operating_brief.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
                    ) != paper_execution_contract_aligned_summary_aligned_summary_aligned_summary:
                        failures.append(
                            "paper execution contract aligned summary aligned summary aligned brief mismatch: "
                            f"brief={bool(operating_brief.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False))} "
                            f"summary={paper_execution_contract_aligned_summary_aligned_summary_aligned_summary}"
                        )
                    operating_brief_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
                        operating_brief.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
                    )
                    operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
                            False,
                        )
                    )
                    operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
                            False,
                        )
                    )
                    operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
                            False,
                        )
                    )
                    operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
                            False,
                        )
                    )
                    operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
                            False,
                        )
                    )
                    operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
                            False,
                        )
                    )
                    operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
                            False,
                        )
                    )
                    operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
                        operating_brief.get(
                            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
                            False,
                        )
                    )
                if operating_index.get("paper_ledger_snapshot", {}) != paper_summary.get("paper_ledger_snapshot", {}):
                    failures.append(
                        "paper ledger snapshot read mismatch: "
                        f"index={operating_index.get('paper_ledger_snapshot', {})} "
                        f"summary={paper_summary.get('paper_ledger_snapshot', {})}"
                    )
                if paper_exit_duplicate_run and int(paper_summary.get("paper_closed_count", 0)) != 0:
                    failures.append(
                        "paper exit duplicate run should not close positions: "
                        f"paper_closed_count={paper_summary.get('paper_closed_count', 0)}"
                    )
                execution_contract_path = analysis_dir / "btc_1d_execution_contract_screen_latest.json"
                if execution_contract_path.exists():
                    execution_contract = _load_json(execution_contract_path)
                    execution_summary = execution_contract.get("execution_contract_summary", {})
                    execution_verdict = execution_contract.get("execution_contract_verdict", {})
                    execution_contract_checked = True
                    execution_contract_aligned = bool(
                        execution_verdict.get("execution_contract_aligned", False)
                    )
                    execution_contract_paper_execution_contract_checked_aligned = bool(
                        execution_summary.get("paper_execution_contract_checked_aligned", False)
                    )
                    execution_contract_paper_execution_contract_aligned_aligned = bool(
                        execution_summary.get("paper_execution_contract_aligned_aligned", False)
                    )
                    execution_contract_paper_execution_contract_checked_summary_aligned = bool(
                        execution_summary.get("paper_execution_contract_checked_summary_aligned", False)
                    )
                    execution_contract_paper_execution_contract_aligned_summary_aligned = bool(
                        execution_summary.get("paper_execution_contract_aligned_summary_aligned", False)
                    )
                    execution_contract_paper_execution_contract_checked_aligned_entry_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_checked_aligned_entry_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_execution_contract_aligned_aligned_entry_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_aligned_aligned_entry_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_checked_summary_aligned_entry_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_aligned_summary_aligned_entry_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_execution_contract_checked_aligned_summary_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_checked_aligned_summary_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_execution_contract_aligned_aligned_summary_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_aligned_aligned_summary_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_checked_summary_aligned_summary_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned = bool(
                        execution_summary.get(
                            "paper_execution_contract_aligned_summary_aligned_summary_aligned",
                            False,
                        )
                    )
                    execution_contract_paper_ledger_snapshot_read = execution_summary.get(
                        "paper_ledger_snapshot_read", ""
                    )
                    if paper_execution_contract_checked is not True:
                        failures.append(
                            "paper summary execution contract checked mismatch: "
                            f"summary={paper_execution_contract_checked} contract=True"
                        )
                    if paper_execution_contract_aligned != execution_contract_aligned:
                        failures.append(
                            "paper summary execution contract aligned mismatch: "
                            f"summary={paper_execution_contract_aligned} "
                            f"contract={execution_contract_aligned}"
                        )
                    if not bool(execution_verdict.get("execution_contract_aligned", False)):
                        failures.append(
                            "execution contract drift detected: "
                            f"verdict={execution_verdict.get('execution_contract_aligned')}"
                        )
                    if execution_summary.get("paper_execution_read", "") != paper_execution_read:
                        failures.append(
                            "execution contract paper execution read mismatch: "
                            f"contract={execution_summary.get('paper_execution_read', '')} "
                            f"summary={paper_execution_read}"
                        )
                    if execution_summary.get("paper_ledger_snapshot_read", "") != paper_ledger_snapshot_read:
                        failures.append(
                            "execution contract paper ledger snapshot mismatch: "
                            f"contract={execution_summary.get('paper_ledger_snapshot_read', '')} "
                            f"summary={paper_ledger_snapshot_read}"
                        )
                    if not execution_contract_paper_execution_contract_checked_aligned:
                        failures.append(
                            "execution contract paper execution contract checked alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_aligned_aligned:
                        failures.append(
                            "execution contract paper execution contract aligned alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_checked_summary_aligned:
                        failures.append(
                            "execution contract paper execution contract checked summary alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_aligned_summary_aligned:
                        failures.append(
                            "execution contract paper execution contract aligned summary alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_checked_aligned_entry_aligned:
                        failures.append(
                            "execution contract paper execution contract checked aligned entry alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_aligned_aligned_entry_aligned:
                        failures.append(
                            "execution contract paper execution contract aligned aligned entry alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned:
                        failures.append(
                            "execution contract paper execution contract checked summary aligned entry alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned:
                        failures.append(
                            "execution contract paper execution contract aligned summary aligned entry alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_checked_aligned_summary_aligned:
                        failures.append(
                            "execution contract paper execution contract checked aligned summary alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_aligned_aligned_summary_aligned:
                        failures.append(
                            "execution contract paper execution contract aligned aligned summary alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned:
                        failures.append(
                            "execution contract paper execution contract checked summary aligned summary alignment failed"
                        )
                    if not execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned:
                        failures.append(
                            "execution contract paper execution contract aligned summary aligned summary alignment failed"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned
                        != execution_contract_paper_execution_contract_checked_aligned_entry_aligned
                    ):
                        failures.append(
                            "operating index execution contract checked aligned entry alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned} "
                            f"contract={execution_contract_paper_execution_contract_checked_aligned_entry_aligned}"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
                        != execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
                    ):
                        failures.append(
                            "operating index execution contract aligned aligned entry alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned} "
                            f"contract={execution_contract_paper_execution_contract_aligned_aligned_entry_aligned}"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
                        != execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
                    ):
                        failures.append(
                            "operating index execution contract checked summary aligned entry alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned} "
                            f"contract={execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned}"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
                        != execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
                    ):
                        failures.append(
                            "operating index execution contract aligned summary aligned entry alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned} "
                            f"contract={execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned}"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned
                        != execution_contract_paper_execution_contract_checked_aligned_summary_aligned
                    ):
                        failures.append(
                            "operating index execution contract checked aligned summary alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned} "
                            f"contract={execution_contract_paper_execution_contract_checked_aligned_summary_aligned}"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
                        != execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
                    ):
                        failures.append(
                            "operating index execution contract aligned aligned summary alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned} "
                            f"contract={execution_contract_paper_execution_contract_aligned_aligned_summary_aligned}"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
                        != execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
                    ):
                        failures.append(
                            "operating index execution contract checked summary aligned summary alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned} "
                            f"contract={execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned}"
                        )
                    if (
                        operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
                        != execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
                    ):
                        failures.append(
                            "operating index execution contract aligned summary aligned summary alignment mismatch: "
                            f"index={operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned} "
                            f"contract={execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned}"
                        )
                    if operating_brief is not None:
                        if (
                            operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned
                            != execution_contract_paper_execution_contract_checked_aligned_entry_aligned
                        ):
                            failures.append(
                                "operating brief execution contract checked aligned entry alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned} "
                                f"contract={execution_contract_paper_execution_contract_checked_aligned_entry_aligned}"
                            )
                        if (
                            operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
                            != execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
                        ):
                            failures.append(
                                "operating brief execution contract aligned aligned entry alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned} "
                                f"contract={execution_contract_paper_execution_contract_aligned_aligned_entry_aligned}"
                            )
                        if (
                            operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
                            != execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
                        ):
                            failures.append(
                                "operating brief execution contract checked summary aligned entry alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned} "
                                f"contract={execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned}"
                            )
                        if (
                            operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
                            != execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
                        ):
                            failures.append(
                                "operating brief execution contract aligned summary aligned entry alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned} "
                                f"contract={execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned}"
                            )
                        if (
                            operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned
                            != execution_contract_paper_execution_contract_checked_aligned_summary_aligned
                        ):
                            failures.append(
                                "operating brief execution contract checked aligned summary alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned} "
                                f"contract={execution_contract_paper_execution_contract_checked_aligned_summary_aligned}"
                            )
                        if (
                            operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
                            != execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
                        ):
                            failures.append(
                                "operating brief execution contract aligned aligned summary alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned} "
                                f"contract={execution_contract_paper_execution_contract_aligned_aligned_summary_aligned}"
                            )
                        if (
                            operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
                            != execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
                        ):
                            failures.append(
                                "operating brief execution contract checked summary aligned summary alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned} "
                                f"contract={execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned}"
                            )
                        if (
                            operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
                            != execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
                        ):
                            failures.append(
                                "operating brief execution contract aligned summary aligned summary alignment mismatch: "
                                f"brief={operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned} "
                                f"contract={execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned}"
                            )
                    if not bool(execution_summary.get("paper_ledger_snapshot_summary_aligned", False)):
                        failures.append("execution contract paper ledger snapshot summary alignment failed")
                    if (
                        bool(paper_summary.get("execution_contract_paper_execution_read_aligned", False))
                        != (
                            execution_summary.get("paper_execution_read", "") == paper_execution_read
                        )
                    ):
                        failures.append(
                            "paper summary execution contract paper execution read alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_read_aligned', False))} "
                            f"contract={execution_summary.get('paper_execution_read', '') == paper_execution_read}"
                        )
                    if (
                        bool(paper_summary.get("execution_contract_paper_ledger_snapshot_aligned", False))
                        != (
                            execution_summary.get("paper_ledger_snapshot_read", "") == paper_ledger_snapshot_read
                        )
                    ):
                        failures.append(
                            "paper summary execution contract paper ledger snapshot alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_ledger_snapshot_aligned', False))} "
                            f"contract={execution_summary.get('paper_ledger_snapshot_read', '') == paper_ledger_snapshot_read}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_ledger_snapshot_summary_aligned",
                                False,
                            )
                        )
                        != bool(execution_summary.get("paper_ledger_snapshot_summary_aligned", False))
                    ):
                        failures.append(
                            "paper summary execution contract paper ledger snapshot summary alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_ledger_snapshot_summary_aligned', False))} "
                            f"contract={bool(execution_summary.get('paper_ledger_snapshot_summary_aligned', False))}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_checked_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_checked_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract checked alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_checked_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_checked_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_aligned_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_aligned_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract aligned alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_aligned_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_aligned_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_checked_summary_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_checked_summary_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract checked summary alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_checked_summary_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_checked_summary_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_aligned_summary_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_aligned_summary_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract aligned summary alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_aligned_summary_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_aligned_summary_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_checked_aligned_entry_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract checked aligned entry alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_checked_aligned_entry_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_checked_aligned_entry_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract aligned aligned entry alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_aligned_aligned_entry_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_aligned_aligned_entry_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract checked summary aligned entry alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract aligned summary aligned entry alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_checked_aligned_summary_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract checked aligned summary alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_checked_aligned_summary_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_checked_aligned_summary_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract aligned aligned summary alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_aligned_aligned_summary_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_aligned_aligned_summary_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract checked summary aligned summary alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned}"
                        )
                    if (
                        bool(
                            paper_summary.get(
                                "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
                                False,
                            )
                        )
                        != execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
                    ):
                        failures.append(
                            "paper summary execution contract paper execution contract aligned summary aligned summary alignment mismatch: "
                            f"summary={bool(paper_summary.get('execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned', False))} "
                            f"contract={execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned}"
                        )
                ledger_path_raw = paper_summary.get("artifacts", {}).get("ledger_json")
                if ledger_path_raw:
                    ledger_path = Path(ledger_path_raw)
                    if not ledger_path.is_absolute():
                        ledger_path = analysis_dir.parent / ledger_path
                    if ledger_path.exists():
                        ledger_payload = _load_json(ledger_path)
                        ledger_snapshot = {
                            "open_position_count": len(
                                [row for row in ledger_payload.get("positions", []) if row.get("status") == "OPEN"]
                            ),
                            "closed_position_count": len(ledger_payload.get("closed_positions", [])),
                            "exit_fill_count": len(ledger_payload.get("exit_fills", [])),
                            "order_count": len(ledger_payload.get("orders", [])),
                            "fill_count": len(ledger_payload.get("fills", [])),
                        }
                        if paper_summary.get("paper_ledger_snapshot") != ledger_snapshot:
                            failures.append(
                                "paper ledger snapshot mismatch: "
                                f"summary={paper_summary.get('paper_ledger_snapshot')} "
                                f"ledger={ledger_snapshot}"
                            )

    return {
        "ok": not failures,
        "candidate": summary["candidate"],
        "shadow_decision": summary["shadow_decision"],
        "carry_decision": summary["carry"]["decision"],
        "survivability_decision": summary["survivability"]["decision"],
        "walk_forward_passed": summary["walk_forward"]["passed"],
        "friction_decision": summary["friction"]["decision"],
        "eth_pass_rate": summary["eth_cross_check"]["pass_rate"],
        "paper_checked": paper_checked,
        "paper_execution_read": paper_execution_read,
        "paper_exit_duplicate_run": paper_exit_duplicate_run,
        "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
        "paper_execution_contract_checked": paper_execution_contract_checked,
        "paper_execution_contract_aligned": paper_execution_contract_aligned,
        "operating_index_paper_execution_contract_checked": (
            operating_index_paper_execution_contract_checked
        ),
        "operating_index_paper_execution_contract_aligned": (
            operating_index_paper_execution_contract_aligned
        ),
        "operating_index_paper_execution_contract_checked_aligned": (
            operating_index_paper_execution_contract_checked_aligned
        ),
        "operating_index_paper_execution_contract_aligned_aligned": (
            operating_index_paper_execution_contract_aligned_aligned
        ),
        "operating_index_paper_execution_contract_checked_summary_aligned": (
            operating_index_paper_execution_contract_checked_summary_aligned
        ),
        "operating_index_paper_execution_contract_aligned_summary_aligned": (
            operating_index_paper_execution_contract_aligned_summary_aligned
        ),
        "operating_index_paper_execution_contract_checked_aligned_entry_aligned": (
            operating_index_paper_execution_contract_checked_aligned_entry_aligned
        ),
        "operating_index_paper_execution_contract_aligned_aligned_entry_aligned": (
            operating_index_paper_execution_contract_aligned_aligned_entry_aligned
        ),
        "operating_index_paper_execution_contract_checked_summary_aligned_entry_aligned": (
            operating_index_paper_execution_contract_checked_summary_aligned_entry_aligned
        ),
        "operating_index_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
            operating_index_paper_execution_contract_aligned_summary_aligned_entry_aligned
        ),
        "operating_index_paper_execution_contract_checked_aligned_summary_aligned": (
            operating_index_paper_execution_contract_checked_aligned_summary_aligned
        ),
        "operating_index_paper_execution_contract_aligned_aligned_summary_aligned": (
            operating_index_paper_execution_contract_aligned_aligned_summary_aligned
        ),
        "operating_index_paper_execution_contract_checked_summary_aligned_summary_aligned": (
            operating_index_paper_execution_contract_checked_summary_aligned_summary_aligned
        ),
        "operating_index_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
            operating_index_paper_execution_contract_aligned_summary_aligned_summary_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned": (
            operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": (
            operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": (
            operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
            operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned": (
            operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": (
            operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": (
            operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
        ),
        "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
            operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
        ),
        "operating_brief_paper_execution_contract_checked": (
            operating_brief_paper_execution_contract_checked
        ),
        "operating_brief_paper_execution_contract_aligned": (
            operating_brief_paper_execution_contract_aligned
        ),
        "operating_brief_paper_execution_contract_checked_aligned": (
            operating_brief_paper_execution_contract_checked_aligned
        ),
        "operating_brief_paper_execution_contract_aligned_aligned": (
            operating_brief_paper_execution_contract_aligned_aligned
        ),
        "operating_brief_paper_execution_contract_checked_summary_aligned": (
            operating_brief_paper_execution_contract_checked_summary_aligned
        ),
        "operating_brief_paper_execution_contract_aligned_summary_aligned": (
            operating_brief_paper_execution_contract_aligned_summary_aligned
        ),
        "operating_brief_paper_execution_contract_checked_aligned_entry_aligned": (
            operating_brief_paper_execution_contract_checked_aligned_entry_aligned
        ),
        "operating_brief_paper_execution_contract_aligned_aligned_entry_aligned": (
            operating_brief_paper_execution_contract_aligned_aligned_entry_aligned
        ),
        "operating_brief_paper_execution_contract_checked_summary_aligned_entry_aligned": (
            operating_brief_paper_execution_contract_checked_summary_aligned_entry_aligned
        ),
        "operating_brief_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
            operating_brief_paper_execution_contract_aligned_summary_aligned_entry_aligned
        ),
        "operating_brief_paper_execution_contract_checked_aligned_summary_aligned": (
            operating_brief_paper_execution_contract_checked_aligned_summary_aligned
        ),
        "operating_brief_paper_execution_contract_aligned_aligned_summary_aligned": (
            operating_brief_paper_execution_contract_aligned_aligned_summary_aligned
        ),
        "operating_brief_paper_execution_contract_checked_summary_aligned_summary_aligned": (
            operating_brief_paper_execution_contract_checked_summary_aligned_summary_aligned
        ),
        "operating_brief_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
            operating_brief_paper_execution_contract_aligned_summary_aligned_summary_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned": (
            operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": (
            operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": (
            operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
            operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned": (
            operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": (
            operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": (
            operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
        ),
        "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
            operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
        ),
        "execution_contract_checked": execution_contract_checked,
        "execution_contract_aligned": execution_contract_aligned,
        "execution_contract_paper_execution_contract_checked_aligned": (
            execution_contract_paper_execution_contract_checked_aligned
        ),
        "execution_contract_paper_execution_contract_aligned_aligned": (
            execution_contract_paper_execution_contract_aligned_aligned
        ),
        "execution_contract_paper_execution_contract_checked_summary_aligned": (
            execution_contract_paper_execution_contract_checked_summary_aligned
        ),
        "execution_contract_paper_execution_contract_aligned_summary_aligned": (
            execution_contract_paper_execution_contract_aligned_summary_aligned
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
        "execution_contract_paper_ledger_snapshot_read": execution_contract_paper_ledger_snapshot_read,
        "quick_read_contract_checked": quick_read_contract_checked,
        "quick_read_contract_operating_contract_aligned": quick_read_contract_operating_contract_aligned,
        "quick_read_contract_paper_execution_contract_aligned": quick_read_contract_paper_execution_contract_aligned,
        "quick_read_contract_contract_health_aligned": quick_read_contract_contract_health_aligned,
        "quick_read_contract_partitioned": quick_read_contract_partitioned,
        "operating_index_contract_health_operating_contract_aligned": (
            operating_index_contract_health_operating_contract_aligned
        ),
        "operating_index_contract_health_paper_execution_contract_aligned": (
            operating_index_contract_health_paper_execution_contract_aligned
        ),
        "operating_index_contract_health_aligned": operating_index_contract_health_aligned,
        "operating_index_contract_health_contracts_are_well_partitioned": (
            operating_index_contract_health_contracts_are_well_partitioned
        ),
        "operating_brief_contract_health_operating_contract_aligned": (
            operating_brief_contract_health_operating_contract_aligned
        ),
        "operating_brief_contract_health_paper_execution_contract_aligned": (
            operating_brief_contract_health_paper_execution_contract_aligned
        ),
        "operating_brief_contract_health_aligned": operating_brief_contract_health_aligned,
        "operating_brief_contract_health_contracts_are_well_partitioned": (
            operating_brief_contract_health_contracts_are_well_partitioned
        ),
        "attack_challenger_remote_monitoring_deployment_handoff_ready": (
            attack_challenger_remote_monitoring_deployment_handoff_ready
        ),
        "attack_challenger_next_step": attack_challenger_next_step,
        "attack_challenger_bridge_report": attack_challenger_bridge_report,
        "deployment_monitoring_active": deployment_monitoring_active,
        "operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready": (
            operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready
        ),
        "operating_brief_attack_challenger_next_step": (
            operating_brief_attack_challenger_next_step
        ),
        "operating_brief_attack_challenger_bridge_report": (
            operating_brief_attack_challenger_bridge_report
        ),
        "operating_brief_deployment_monitoring_active": (
            operating_brief_deployment_monitoring_active
        ),
        "failures": failures,
    }


def render_health_check(result: dict[str, Any]) -> str:
    status = "PASS" if result["ok"] else "FAIL"
    lines = [
        "BTC 1d Shadow Health Check",
        f"status: {status}",
        f"candidate: {result['candidate']}",
        f"shadow_decision: {result['shadow_decision']}",
        (
            "attack_challenger_remote_monitoring_deployment_handoff_ready: "
            f"{result.get('attack_challenger_remote_monitoring_deployment_handoff_ready', False)}"
        ),
        f"attack_challenger_next_step: {result.get('attack_challenger_next_step', '')}",
        f"attack_challenger_bridge_report: {result.get('attack_challenger_bridge_report', '')}",
        f"deployment_monitoring_active: {result.get('deployment_monitoring_active', False)}",
        (
            "operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready: "
            f"{result.get('operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready')}"
        ),
        (
            "operating_brief_attack_challenger_next_step: "
            f"{result.get('operating_brief_attack_challenger_next_step', '')}"
        ),
        (
            "operating_brief_attack_challenger_bridge_report: "
            f"{result.get('operating_brief_attack_challenger_bridge_report', '')}"
        ),
        (
            "operating_brief_deployment_monitoring_active: "
            f"{result.get('operating_brief_deployment_monitoring_active')}"
        ),
        f"carry: {result['carry_decision']}",
        f"survivability: {result['survivability_decision']}",
        f"walk_forward: {'PASS' if result['walk_forward_passed'] else 'FAIL'}",
        f"friction: {result['friction_decision']}",
        f"eth_pass_rate: {result['eth_pass_rate']}",
        f"paper_checked: {result.get('paper_checked', False)}",
    ]
    if result.get("paper_checked"):
        lines.append(f"paper_execution_read: {result.get('paper_execution_read')}")
        lines.append(f"paper_exit_duplicate_run: {result.get('paper_exit_duplicate_run')}")
        lines.append(f"paper_ledger_snapshot: {result.get('paper_ledger_snapshot_read')}")
        lines.append(
            "paper_execution_contract_checked: "
            f"{result.get('paper_execution_contract_checked')}"
        )
        lines.append(
            "paper_execution_contract_aligned: "
            f"{result.get('paper_execution_contract_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_checked: "
            f"{result.get('operating_index_paper_execution_contract_checked')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_aligned: "
            f"{result.get('operating_index_paper_execution_contract_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_checked_aligned: "
            f"{result.get('operating_index_paper_execution_contract_checked_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_aligned_aligned: "
            f"{result.get('operating_index_paper_execution_contract_aligned_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_checked_summary_aligned: "
            f"{result.get('operating_index_paper_execution_contract_checked_summary_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_aligned_summary_aligned: "
            f"{result.get('operating_index_paper_execution_contract_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_checked_aligned_entry_aligned: "
            f"{result.get('operating_index_paper_execution_contract_checked_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_aligned_aligned_entry_aligned: "
            f"{result.get('operating_index_paper_execution_contract_aligned_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"{result.get('operating_index_paper_execution_contract_checked_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"{result.get('operating_index_paper_execution_contract_aligned_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_checked_aligned_summary_aligned: "
            f"{result.get('operating_index_paper_execution_contract_checked_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_aligned_aligned_summary_aligned: "
            f"{result.get('operating_index_paper_execution_contract_aligned_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"{result.get('operating_index_paper_execution_contract_checked_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"{result.get('operating_index_paper_execution_contract_aligned_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"{result.get('operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_checked: "
            f"{result.get('operating_brief_paper_execution_contract_checked')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_checked_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_checked_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_aligned_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_aligned_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_checked_summary_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_checked_summary_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_aligned_summary_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_checked_aligned_entry_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_checked_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_aligned_aligned_entry_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_aligned_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_checked_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_aligned_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_checked_aligned_summary_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_checked_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_aligned_aligned_summary_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_aligned_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_checked_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"{result.get('operating_brief_paper_execution_contract_aligned_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"{result.get('operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned')}"
        )
    if result.get("execution_contract_checked"):
        lines.append(f"execution_contract_aligned: {result.get('execution_contract_aligned')}")
        lines.append(
            "execution_contract_paper_execution_contract_checked_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_checked_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_aligned_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_aligned_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_checked_summary_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_checked_summary_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_aligned_summary_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_aligned_summary_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_checked_aligned_entry_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_aligned_aligned_entry_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_checked_aligned_summary_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_aligned_aligned_summary_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"{result.get('execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned')}"
        )
        lines.append(
            "execution_contract_paper_ledger_snapshot: "
            f"{result.get('execution_contract_paper_ledger_snapshot_read')}"
        )
    if result.get("quick_read_contract_checked"):
        lines.append(
            "quick_read_contract_operating_contract_aligned: "
            f"{result.get('quick_read_contract_operating_contract_aligned')}"
        )
        lines.append(
            "quick_read_contract_paper_execution_contract_aligned: "
            f"{result.get('quick_read_contract_paper_execution_contract_aligned')}"
        )
        lines.append(
            "quick_read_contract_contract_health_aligned: "
            f"{result.get('quick_read_contract_contract_health_aligned')}"
        )
        lines.append(
            "quick_read_contract_partitioned: "
            f"{result.get('quick_read_contract_partitioned')}"
        )
        lines.append(
            "operating_index_contract_health_operating_contract_aligned: "
            f"{result.get('operating_index_contract_health_operating_contract_aligned')}"
        )
        lines.append(
            "operating_index_contract_health_paper_execution_contract_aligned: "
            f"{result.get('operating_index_contract_health_paper_execution_contract_aligned')}"
        )
        lines.append(
            "operating_index_contract_health_aligned: "
            f"{result.get('operating_index_contract_health_aligned')}"
        )
        lines.append(
            "operating_index_contract_health_contracts_are_well_partitioned: "
            f"{result.get('operating_index_contract_health_contracts_are_well_partitioned')}"
        )
        lines.append(
            "operating_brief_contract_health_operating_contract_aligned: "
            f"{result.get('operating_brief_contract_health_operating_contract_aligned')}"
        )
        lines.append(
            "operating_brief_contract_health_paper_execution_contract_aligned: "
            f"{result.get('operating_brief_contract_health_paper_execution_contract_aligned')}"
        )
        lines.append(
            "operating_brief_contract_health_aligned: "
            f"{result.get('operating_brief_contract_health_aligned')}"
        )
        lines.append(
            "operating_brief_contract_health_contracts_are_well_partitioned: "
            f"{result.get('operating_brief_contract_health_contracts_are_well_partitioned')}"
        )
    if result["failures"]:
        lines.append("failures:")
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_shadow_health(analysis_dir=args.analysis_dir, args=args)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(render_health_check(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
