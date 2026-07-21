from __future__ import annotations

import json
from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
)
from scripts.check_btc_1d_shadow_health import (
    build_parser,
    check_shadow_health,
    main,
    render_health_check,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_latest_files(analysis_dir: Path, *, carry_sharpe: float = 1.16) -> None:
    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "scope": "BTC-only",
            "shadow_decision": "shadow_ready_for_btc_only",
            "carry": {"periods": 2200, "decision": "PASS", "sharpe": carry_sharpe, "cagr": 0.14, "max_drawdown": 0.10},
            "survivability": {"periods": 2600, "decision": "PASS", "sharpe": 1.15, "cagr": 0.15, "max_drawdown": 0.13},
            "walk_forward": {
                "passed": True,
                "oos_sharpe": 0.82,
                "oos_cagr": 0.05,
                "oos_max_drawdown": 0.06,
                "sensitivity_max_drift": 0.09,
                "unstable_parameters": [],
            },
            "friction": {"decision": "continue", "heaviest_level_bps": 20.0, "heaviest_level_sharpe": 1.04},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.0, "pass_count": 0, "total_count": 4},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_shadow_packet_latest.json",
        {
            "status": "carryable_candidate",
            "paper_validation_decision": "PASS",
            "survivability_validation_decision": "PASS",
            "friction_validation_heaviest_level": {"decision": "PASS"},
        },
    )


def _write_paper_files(
    analysis_dir: Path,
    *,
    paper_execution_read: str = "paper execution | track=operating | applied=0 | closed=0 | open=1",
    paper_exit_duplicate_run: bool = True,
    paper_closed_count: int = 0,
    paper_ledger_consistent: bool = True,
    paper_ledger_snapshot: dict | None = None,
    index_paper_execution_read: str | None = None,
    index_paper_exit_duplicate_run: bool | None = None,
    index_paper_ledger_consistent: bool | None = None,
    index_paper_ledger_snapshot: dict | None = None,
    index_paper_execution_contract_checked: bool | None = None,
    index_paper_execution_contract_aligned: bool | None = None,
    index_paper_execution_contract_checked_aligned: bool | None = None,
    index_paper_execution_contract_aligned_aligned: bool | None = None,
    index_paper_execution_contract_checked_summary_aligned: bool | None = None,
    index_paper_execution_contract_aligned_summary_aligned: bool | None = None,
    index_paper_execution_contract_checked_aligned_entry_aligned: bool | None = None,
    index_paper_execution_contract_aligned_aligned_entry_aligned: bool | None = None,
    index_paper_execution_contract_checked_summary_aligned_entry_aligned: bool | None = None,
    index_paper_execution_contract_aligned_summary_aligned_entry_aligned: bool | None = None,
    index_paper_execution_contract_checked_aligned_summary_aligned: bool | None = None,
    index_paper_execution_contract_aligned_aligned_summary_aligned: bool | None = None,
    index_paper_execution_contract_checked_summary_aligned_summary_aligned: bool | None = None,
    index_paper_execution_contract_aligned_summary_aligned_summary_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: bool | None = None,
    index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: bool | None = None,
    brief_paper_execution_contract_checked: bool | None = None,
    brief_paper_execution_contract_aligned: bool | None = None,
    brief_paper_execution_contract_checked_aligned: bool | None = None,
    brief_paper_execution_contract_aligned_aligned: bool | None = None,
    brief_paper_execution_contract_checked_summary_aligned: bool | None = None,
    brief_paper_execution_contract_aligned_summary_aligned: bool | None = None,
    brief_paper_execution_contract_checked_aligned_entry_aligned: bool | None = None,
    brief_paper_execution_contract_aligned_aligned_entry_aligned: bool | None = None,
    brief_paper_execution_contract_checked_summary_aligned_entry_aligned: bool | None = None,
    brief_paper_execution_contract_aligned_summary_aligned_entry_aligned: bool | None = None,
    brief_paper_execution_contract_checked_aligned_summary_aligned: bool | None = None,
    brief_paper_execution_contract_aligned_aligned_summary_aligned: bool | None = None,
    brief_paper_execution_contract_checked_summary_aligned_summary_aligned: bool | None = None,
    brief_paper_execution_contract_aligned_summary_aligned_summary_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: bool | None = None,
    brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: bool | None = None,
    execution_contract_paper_execution_read: str | None = None,
    execution_contract_paper_ledger_snapshot_read: str | None = None,
    execution_contract_aligned: bool = True,
    execution_contract_snapshot_summary_aligned: bool = True,
    summary_execution_contract_checked: bool | None = None,
    summary_execution_contract_aligned: bool | None = None,
    summary_execution_contract_paper_execution_read_aligned: bool | None = None,
    summary_execution_contract_paper_ledger_snapshot_aligned: bool | None = None,
    summary_execution_contract_snapshot_summary_aligned: bool | None = None,
    summary_execution_contract_checked_aligned: bool | None = None,
    summary_execution_contract_aligned_aligned: bool | None = None,
    summary_execution_contract_checked_summary_aligned: bool | None = None,
    summary_execution_contract_aligned_summary_aligned: bool | None = None,
    summary_execution_contract_checked_aligned_entry_aligned: bool | None = None,
    summary_execution_contract_aligned_aligned_entry_aligned: bool | None = None,
    summary_execution_contract_checked_summary_aligned_entry_aligned: bool | None = None,
    summary_execution_contract_aligned_summary_aligned_entry_aligned: bool | None = None,
    summary_execution_contract_checked_aligned_summary_aligned: bool | None = None,
    summary_execution_contract_aligned_aligned_summary_aligned: bool | None = None,
    summary_execution_contract_checked_summary_aligned_summary_aligned: bool | None = None,
    summary_execution_contract_aligned_summary_aligned_summary_aligned: bool | None = None,
    execution_contract_checked_aligned: bool = True,
    execution_contract_aligned_aligned: bool = True,
    execution_contract_checked_summary_aligned: bool = True,
    execution_contract_aligned_summary_aligned: bool = True,
    execution_contract_checked_aligned_entry_aligned: bool = True,
    execution_contract_aligned_aligned_entry_aligned: bool = True,
    execution_contract_checked_summary_aligned_entry_aligned: bool = True,
    execution_contract_aligned_summary_aligned_entry_aligned: bool = True,
    execution_contract_checked_aligned_summary_aligned: bool = True,
    execution_contract_aligned_aligned_summary_aligned: bool = True,
    execution_contract_checked_summary_aligned_summary_aligned: bool = True,
    execution_contract_aligned_summary_aligned_summary_aligned: bool = True,
    quick_read_contract_operating_contract_aligned: bool = True,
    quick_read_contract_paper_execution_contract_aligned: bool = True,
    quick_read_contract_contract_health_aligned: bool = True,
    quick_read_contract_partitioned: bool = True,
    index_contract_health_operating_contract_aligned: bool | None = None,
    index_contract_health_paper_execution_contract_aligned: bool | None = None,
    index_contract_health_aligned: bool | None = None,
    index_contract_health_contracts_are_well_partitioned: bool | None = None,
    brief_contract_health_operating_contract_aligned: bool | None = None,
    brief_contract_health_paper_execution_contract_aligned: bool | None = None,
    brief_contract_health_aligned: bool | None = None,
    brief_contract_health_contracts_are_well_partitioned: bool | None = None,
    attack_challenger_remote_monitoring_deployment_handoff_ready: bool = True,
    attack_challenger_next_step: str = ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    attack_challenger_bridge_report: str = "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
    deployment_monitoring_active: bool = True,
    brief_attack_challenger_remote_monitoring_deployment_handoff_ready: bool | None = None,
    brief_attack_challenger_next_step: str | None = None,
    brief_attack_challenger_bridge_report: str | None = None,
    brief_deployment_monitoring_active: bool | None = None,
) -> None:
    summary_path = analysis_dir / "btc_1d_paper_nightly_summary_latest.json"
    ledger_path = analysis_dir / "bithumb_paper_ledger.json"
    ledger_payload = {
        "orders": [{}],
        "fills": [{}],
        "positions": [{"status": "OPEN"}],
        "closed_positions": [{}] * paper_closed_count,
        "exit_fills": [{}] * paper_closed_count,
    }
    _write_json(ledger_path, ledger_payload)
    _write_json(
        summary_path,
        {
            "paper_execution_read": paper_execution_read,
            "paper_exit_duplicate_run": paper_exit_duplicate_run,
            "paper_closed_count": paper_closed_count,
            "paper_ledger_consistent": paper_ledger_consistent,
            "paper_ledger_consistency": {"consistent": paper_ledger_consistent},
            "paper_ledger_snapshot": paper_ledger_snapshot
            if paper_ledger_snapshot is not None
            else {
                "open_position_count": 1,
                "closed_position_count": paper_closed_count,
                "exit_fill_count": paper_closed_count,
                "order_count": 1,
                "fill_count": 1,
            },
            "execution_contract_checked": (
                summary_execution_contract_checked
                if summary_execution_contract_checked is not None
                else True
            ),
            "execution_contract_aligned": (
                summary_execution_contract_aligned
                if summary_execution_contract_aligned is not None
                else execution_contract_aligned
            ),
            "execution_contract_paper_execution_read_aligned": (
                summary_execution_contract_paper_execution_read_aligned
                if summary_execution_contract_paper_execution_read_aligned is not None
                else True
            ),
            "execution_contract_paper_ledger_snapshot_aligned": (
                summary_execution_contract_paper_ledger_snapshot_aligned
                if summary_execution_contract_paper_ledger_snapshot_aligned is not None
                else True
            ),
            "execution_contract_paper_ledger_snapshot_summary_aligned": (
                summary_execution_contract_snapshot_summary_aligned
                if summary_execution_contract_snapshot_summary_aligned is not None
                else execution_contract_snapshot_summary_aligned
            ),
            "execution_contract_paper_execution_contract_checked_aligned": (
                summary_execution_contract_checked_aligned
                if summary_execution_contract_checked_aligned is not None
                else execution_contract_checked_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_aligned": (
                summary_execution_contract_aligned_aligned
                if summary_execution_contract_aligned_aligned is not None
                else execution_contract_aligned_aligned
            ),
            "execution_contract_paper_execution_contract_checked_summary_aligned": (
                summary_execution_contract_checked_summary_aligned
                if summary_execution_contract_checked_summary_aligned is not None
                else execution_contract_checked_summary_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned": (
                summary_execution_contract_aligned_summary_aligned
                if summary_execution_contract_aligned_summary_aligned is not None
                else execution_contract_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": (
                summary_execution_contract_checked_aligned_entry_aligned
                if summary_execution_contract_checked_aligned_entry_aligned is not None
                else execution_contract_checked_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": (
                summary_execution_contract_aligned_aligned_entry_aligned
                if summary_execution_contract_aligned_aligned_entry_aligned is not None
                else execution_contract_aligned_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": (
                summary_execution_contract_checked_summary_aligned_entry_aligned
                if summary_execution_contract_checked_summary_aligned_entry_aligned is not None
                else execution_contract_checked_summary_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
                summary_execution_contract_aligned_summary_aligned_entry_aligned
                if summary_execution_contract_aligned_summary_aligned_entry_aligned is not None
                else execution_contract_aligned_summary_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": (
                summary_execution_contract_checked_aligned_summary_aligned
                if summary_execution_contract_checked_aligned_summary_aligned is not None
                else execution_contract_checked_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": (
                summary_execution_contract_aligned_aligned_summary_aligned
                if summary_execution_contract_aligned_aligned_summary_aligned is not None
                else execution_contract_aligned_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": (
                summary_execution_contract_checked_summary_aligned_summary_aligned
                if summary_execution_contract_checked_summary_aligned_summary_aligned is not None
                else execution_contract_checked_summary_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
                summary_execution_contract_aligned_summary_aligned_summary_aligned
                if summary_execution_contract_aligned_summary_aligned_summary_aligned is not None
                else execution_contract_aligned_summary_aligned_summary_aligned
            ),
            "artifacts": {"ledger_json": str(ledger_path)},
        },
    )
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "paper_nightly_summary": str(summary_path),
            "paper_execution_read": index_paper_execution_read if index_paper_execution_read is not None else paper_execution_read,
            "paper_execution_contract_checked": (
                index_paper_execution_contract_checked
                if index_paper_execution_contract_checked is not None
                else summary_payload["execution_contract_checked"]
            ),
            "paper_execution_contract_aligned": (
                index_paper_execution_contract_aligned
                if index_paper_execution_contract_aligned is not None
                else summary_payload["execution_contract_aligned"]
            ),
            "paper_execution_contract_checked_aligned": (
                index_paper_execution_contract_checked_aligned
                if index_paper_execution_contract_checked_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_aligned"]
            ),
            "paper_execution_contract_aligned_aligned": (
                index_paper_execution_contract_aligned_aligned
                if index_paper_execution_contract_aligned_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_aligned"]
            ),
            "paper_execution_contract_checked_summary_aligned": (
                index_paper_execution_contract_checked_summary_aligned
                if index_paper_execution_contract_checked_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_summary_aligned"]
            ),
            "paper_execution_contract_aligned_summary_aligned": (
                index_paper_execution_contract_aligned_summary_aligned
                if index_paper_execution_contract_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_summary_aligned"]
            ),
            "paper_execution_contract_checked_aligned_entry_aligned": (
                index_paper_execution_contract_checked_aligned_entry_aligned
                if index_paper_execution_contract_checked_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"]
            ),
            "paper_execution_contract_aligned_aligned_entry_aligned": (
                index_paper_execution_contract_aligned_aligned_entry_aligned
                if index_paper_execution_contract_aligned_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"]
            ),
            "paper_execution_contract_checked_summary_aligned_entry_aligned": (
                index_paper_execution_contract_checked_summary_aligned_entry_aligned
                if index_paper_execution_contract_checked_summary_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"]
            ),
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": (
                index_paper_execution_contract_aligned_summary_aligned_entry_aligned
                if index_paper_execution_contract_aligned_summary_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"]
            ),
            "paper_execution_contract_checked_aligned_summary_aligned": (
                index_paper_execution_contract_checked_aligned_summary_aligned
                if index_paper_execution_contract_checked_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"]
            ),
            "paper_execution_contract_aligned_aligned_summary_aligned": (
                index_paper_execution_contract_aligned_aligned_summary_aligned
                if index_paper_execution_contract_aligned_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"]
            ),
            "paper_execution_contract_checked_summary_aligned_summary_aligned": (
                index_paper_execution_contract_checked_summary_aligned_summary_aligned
                if index_paper_execution_contract_checked_summary_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"]
            ),
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": (
                index_paper_execution_contract_aligned_summary_aligned_summary_aligned
                if index_paper_execution_contract_aligned_summary_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"]
            ),
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": (
                index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned
                if index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned is not None
                else execution_contract_checked_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": (
                index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
                if index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned is not None
                else execution_contract_aligned_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": (
                index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
                if index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned is not None
                else execution_contract_checked_summary_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
                index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
                if index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned is not None
                else execution_contract_aligned_summary_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": (
                index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned
                if index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned is not None
                else execution_contract_checked_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": (
                index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
                if index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned is not None
                else execution_contract_aligned_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": (
                index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
                if index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned is not None
                else execution_contract_checked_summary_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
                index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
                if index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned is not None
                else execution_contract_aligned_summary_aligned_summary_aligned
            ),
            "paper_exit_duplicate_run": (
                index_paper_exit_duplicate_run if index_paper_exit_duplicate_run is not None else paper_exit_duplicate_run
            ),
            "paper_ledger_consistent": (
                index_paper_ledger_consistent
                if index_paper_ledger_consistent is not None
                else summary_payload["paper_ledger_consistent"]
            ),
            "contract_health_operating_contract_aligned": (
                index_contract_health_operating_contract_aligned
                if index_contract_health_operating_contract_aligned is not None
                else quick_read_contract_operating_contract_aligned
            ),
            "contract_health_paper_execution_contract_aligned": (
                index_contract_health_paper_execution_contract_aligned
                if index_contract_health_paper_execution_contract_aligned is not None
                else quick_read_contract_paper_execution_contract_aligned
            ),
            "contract_health_aligned": (
                index_contract_health_aligned
                if index_contract_health_aligned is not None
                else quick_read_contract_contract_health_aligned
            ),
            "contract_health_contracts_are_well_partitioned": (
                index_contract_health_contracts_are_well_partitioned
                if index_contract_health_contracts_are_well_partitioned is not None
                else quick_read_contract_partitioned
            ),
            "paper_ledger_snapshot": (
                index_paper_ledger_snapshot
                if index_paper_ledger_snapshot is not None
                else summary_payload["paper_ledger_snapshot"]
            ),
            "attack_challenger_remote_monitoring_deployment_handoff_ready": attack_challenger_remote_monitoring_deployment_handoff_ready,
            "attack_challenger_next_step": attack_challenger_next_step,
            "attack_challenger_bridge_report": attack_challenger_bridge_report,
            "deployment_monitoring_active": deployment_monitoring_active,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "paper_execution_contract_checked": (
                brief_paper_execution_contract_checked
                if brief_paper_execution_contract_checked is not None
                else summary_payload["execution_contract_checked"]
            ),
            "paper_execution_contract_aligned": (
                brief_paper_execution_contract_aligned
                if brief_paper_execution_contract_aligned is not None
                else summary_payload["execution_contract_aligned"]
            ),
            "paper_execution_contract_checked_aligned": (
                brief_paper_execution_contract_checked_aligned
                if brief_paper_execution_contract_checked_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_aligned"]
            ),
            "paper_execution_contract_aligned_aligned": (
                brief_paper_execution_contract_aligned_aligned
                if brief_paper_execution_contract_aligned_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_aligned"]
            ),
            "paper_execution_contract_checked_summary_aligned": (
                brief_paper_execution_contract_checked_summary_aligned
                if brief_paper_execution_contract_checked_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_summary_aligned"]
            ),
            "paper_execution_contract_aligned_summary_aligned": (
                brief_paper_execution_contract_aligned_summary_aligned
                if brief_paper_execution_contract_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_summary_aligned"]
            ),
            "paper_execution_contract_checked_aligned_entry_aligned": (
                brief_paper_execution_contract_checked_aligned_entry_aligned
                if brief_paper_execution_contract_checked_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"]
            ),
            "paper_execution_contract_aligned_aligned_entry_aligned": (
                brief_paper_execution_contract_aligned_aligned_entry_aligned
                if brief_paper_execution_contract_aligned_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"]
            ),
            "paper_execution_contract_checked_summary_aligned_entry_aligned": (
                brief_paper_execution_contract_checked_summary_aligned_entry_aligned
                if brief_paper_execution_contract_checked_summary_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"]
            ),
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": (
                brief_paper_execution_contract_aligned_summary_aligned_entry_aligned
                if brief_paper_execution_contract_aligned_summary_aligned_entry_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"]
            ),
            "paper_execution_contract_checked_aligned_summary_aligned": (
                brief_paper_execution_contract_checked_aligned_summary_aligned
                if brief_paper_execution_contract_checked_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"]
            ),
            "paper_execution_contract_aligned_aligned_summary_aligned": (
                brief_paper_execution_contract_aligned_aligned_summary_aligned
                if brief_paper_execution_contract_aligned_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"]
            ),
            "paper_execution_contract_checked_summary_aligned_summary_aligned": (
                brief_paper_execution_contract_checked_summary_aligned_summary_aligned
                if brief_paper_execution_contract_checked_summary_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"]
            ),
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": (
                brief_paper_execution_contract_aligned_summary_aligned_summary_aligned
                if brief_paper_execution_contract_aligned_summary_aligned_summary_aligned is not None
                else summary_payload["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"]
            ),
            "contract_health_operating_contract_aligned": (
                brief_contract_health_operating_contract_aligned
                if brief_contract_health_operating_contract_aligned is not None
                else quick_read_contract_operating_contract_aligned
            ),
            "contract_health_paper_execution_contract_aligned": (
                brief_contract_health_paper_execution_contract_aligned
                if brief_contract_health_paper_execution_contract_aligned is not None
                else quick_read_contract_paper_execution_contract_aligned
            ),
            "contract_health_aligned": (
                brief_contract_health_aligned
                if brief_contract_health_aligned is not None
                else quick_read_contract_contract_health_aligned
            ),
            "contract_health_contracts_are_well_partitioned": (
                brief_contract_health_contracts_are_well_partitioned
                if brief_contract_health_contracts_are_well_partitioned is not None
                else quick_read_contract_partitioned
            ),
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": (
                brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned
                if brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned is not None
                else execution_contract_checked_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": (
                brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned
                if brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned is not None
                else execution_contract_aligned_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": (
                brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned
                if brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned is not None
                else execution_contract_checked_summary_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": (
                brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned
                if brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned is not None
                else execution_contract_aligned_summary_aligned_entry_aligned
            ),
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": (
                brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned
                if brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned is not None
                else execution_contract_checked_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": (
                brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned
                if brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned is not None
                else execution_contract_aligned_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": (
                brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned
                if brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned is not None
                else execution_contract_checked_summary_aligned_summary_aligned
            ),
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": (
                brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned
                if brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned is not None
                else execution_contract_aligned_summary_aligned_summary_aligned
            ),
            "attack_challenger_remote_monitoring_deployment_handoff_ready": (
                brief_attack_challenger_remote_monitoring_deployment_handoff_ready
                if brief_attack_challenger_remote_monitoring_deployment_handoff_ready is not None
                else attack_challenger_remote_monitoring_deployment_handoff_ready
            ),
            "attack_challenger_next_step": (
                brief_attack_challenger_next_step
                if brief_attack_challenger_next_step is not None
                else attack_challenger_next_step
            ),
            "attack_challenger_bridge_report": (
                brief_attack_challenger_bridge_report
                if brief_attack_challenger_bridge_report is not None
                else attack_challenger_bridge_report
            ),
            "deployment_monitoring_active": (
                brief_deployment_monitoring_active
                if brief_deployment_monitoring_active is not None
                else deployment_monitoring_active
            ),
        },
    )
    paper_snapshot_read = (
        "paper ledger | "
        f"open={int(summary_payload['paper_ledger_snapshot'].get('open_position_count', 0))} | "
        f"closed={int(summary_payload['paper_ledger_snapshot'].get('closed_position_count', 0))} | "
        f"exit_fills={int(summary_payload['paper_ledger_snapshot'].get('exit_fill_count', 0))} | "
        f"orders={int(summary_payload['paper_ledger_snapshot'].get('order_count', 0))} | "
        f"fills={int(summary_payload['paper_ledger_snapshot'].get('fill_count', 0))}"
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "paper_execution_read": (
                    execution_contract_paper_execution_read
                    if execution_contract_paper_execution_read is not None
                    else paper_execution_read
                ),
                "paper_ledger_snapshot_read": (
                    execution_contract_paper_ledger_snapshot_read
                    if execution_contract_paper_ledger_snapshot_read is not None
                    else paper_snapshot_read
                ),
                "paper_execution_contract_checked_aligned": execution_contract_checked_aligned,
                "paper_execution_contract_aligned_aligned": execution_contract_aligned_aligned,
                "paper_execution_contract_checked_summary_aligned": execution_contract_checked_summary_aligned,
                "paper_execution_contract_aligned_summary_aligned": execution_contract_aligned_summary_aligned,
                "paper_execution_contract_checked_aligned_entry_aligned": execution_contract_checked_aligned_entry_aligned,
                "paper_execution_contract_aligned_aligned_entry_aligned": execution_contract_aligned_aligned_entry_aligned,
                "paper_execution_contract_checked_summary_aligned_entry_aligned": execution_contract_checked_summary_aligned_entry_aligned,
                "paper_execution_contract_aligned_summary_aligned_entry_aligned": execution_contract_aligned_summary_aligned_entry_aligned,
                "paper_execution_contract_checked_aligned_summary_aligned": execution_contract_checked_aligned_summary_aligned,
                "paper_execution_contract_aligned_aligned_summary_aligned": execution_contract_aligned_aligned_summary_aligned,
                "paper_execution_contract_checked_summary_aligned_summary_aligned": execution_contract_checked_summary_aligned_summary_aligned,
                "paper_execution_contract_aligned_summary_aligned_summary_aligned": execution_contract_aligned_summary_aligned_summary_aligned,
                "paper_ledger_snapshot_summary_aligned": execution_contract_snapshot_summary_aligned,
            },
            "execution_contract_verdict": {
                "execution_contract_aligned": execution_contract_aligned,
            },
        },
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "operating_contract_aligned": quick_read_contract_operating_contract_aligned,
                "paper_execution_contract_aligned": quick_read_contract_paper_execution_contract_aligned,
                "contract_health_aligned": quick_read_contract_contract_health_aligned,
            },
            "contract_verdict": {
                "contracts_are_well_partitioned": quick_read_contract_partitioned,
            },
        },
    )


def test_shadow_health_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.expected_candidate == "low_vol_cap_050_025_minvol020_p2200"
    assert args.expected_shadow_decision == "shadow_ready_for_btc_only"
    assert args.min_oos_sharpe == 0.5
    assert args.as_json is False


def test_shadow_health_main_supports_as_json(tmp_path: Path, capsys) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _write_latest_files(analysis_dir)
    _write_paper_files(analysis_dir)

    exit_code = main(["--analysis-dir", str(analysis_dir), "--as-json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["deployment_monitoring_active"] is True
    assert payload["attack_challenger_next_step"] == "deployment monitoring active"


def test_check_shadow_health_passes_for_expected_latest_state(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(analysis_dir)

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is True
    assert result["failures"] == []
    assert result["paper_checked"] is True
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert result["attack_challenger_next_step"] == "deployment monitoring active"
    assert (
        result["attack_challenger_bridge_report"]
        == "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert result["paper_exit_duplicate_run"] is True
    assert result["paper_ledger_snapshot_read"] == "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1"
    assert result["paper_execution_contract_checked"] is True
    assert result["paper_execution_contract_aligned"] is True
    assert result["operating_index_paper_execution_contract_checked"] is True
    assert result["operating_index_paper_execution_contract_aligned"] is True
    assert result["operating_index_paper_execution_contract_checked_aligned"] is True
    assert result["operating_index_paper_execution_contract_aligned_aligned"] is True
    assert result["operating_index_paper_execution_contract_checked_summary_aligned"] is True
    assert result["operating_index_paper_execution_contract_aligned_summary_aligned"] is True
    assert result["operating_index_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert result["operating_index_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert result["operating_index_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert result["operating_index_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert result["operating_index_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert result["operating_index_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert result["operating_index_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert result["operating_index_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert result["operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert result["operating_brief_paper_execution_contract_checked"] is True
    assert result["operating_brief_paper_execution_contract_aligned"] is True
    assert result["operating_brief_paper_execution_contract_checked_aligned"] is True
    assert result["operating_brief_paper_execution_contract_aligned_aligned"] is True
    assert result["operating_brief_paper_execution_contract_checked_summary_aligned"] is True
    assert result["operating_brief_paper_execution_contract_aligned_summary_aligned"] is True
    assert result["operating_brief_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert result["operating_brief_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert result["operating_brief_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert result["operating_brief_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert result["operating_brief_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert result["operating_brief_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert result["operating_brief_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert result["operating_brief_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert result["operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert result["execution_contract_checked"] is True
    assert result["execution_contract_aligned"] is True
    assert result["execution_contract_paper_execution_contract_checked_aligned"] is True
    assert result["execution_contract_paper_execution_contract_aligned_aligned"] is True
    assert result["execution_contract_paper_execution_contract_checked_summary_aligned"] is True
    assert result["execution_contract_paper_execution_contract_aligned_summary_aligned"] is True
    assert result["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert result["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert result["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert result["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert result["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert result["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert result["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert result["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert (
        result["execution_contract_paper_ledger_snapshot_read"]
        == "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1"
    )


def test_check_shadow_health_fails_when_core_gate_breaks(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir, carry_sharpe=0.91)
    _write_paper_files(analysis_dir)

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("carry sharpe below floor" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_paper_execution_read_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_paper_execution_read="paper execution | track=operating | applied=1 | closed=0 | open=0",
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper execution read mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_duplicate_exit_rerun_reports_close(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        paper_exit_duplicate_run=True,
        paper_closed_count=1,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper exit duplicate run should not close positions" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_paper_ledger_is_inconsistent(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        paper_ledger_consistent=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper ledger consistency failed" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_paper_ledger_snapshot_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        paper_ledger_snapshot={
            "open_position_count": 0,
            "closed_position_count": 0,
            "exit_fill_count": 0,
            "order_count": 0,
            "fill_count": 0,
        },
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper ledger snapshot mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_index_paper_ledger_consistency_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_paper_ledger_consistent=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper ledger consistent mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_index_paper_ledger_snapshot_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_paper_ledger_snapshot={
            "open_position_count": 9,
            "closed_position_count": 0,
            "exit_fill_count": 0,
            "order_count": 1,
            "fill_count": 1,
        },
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper ledger snapshot read mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_index_paper_execution_contract_checked_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_paper_execution_contract_checked=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper execution contract checked mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_index_paper_execution_contract_aligned_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_paper_execution_contract_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper execution contract aligned mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_brief_paper_execution_contract_checked_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        brief_paper_execution_contract_checked=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper execution contract checked brief mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_brief_paper_execution_contract_aligned_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        brief_paper_execution_contract_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("paper execution contract aligned brief mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_index_paper_execution_contract_checked_summary_aligned_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_paper_execution_contract_checked_summary_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper execution contract checked summary aligned mismatch" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_brief_paper_execution_contract_aligned_summary_aligned_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        brief_paper_execution_contract_aligned_summary_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper execution contract aligned summary aligned brief mismatch" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_index_execution_contract_entry_alignment_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "operating index execution contract checked aligned entry alignment mismatch" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_brief_execution_contract_summary_alignment_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "operating brief execution contract aligned summary aligned summary alignment mismatch"
        in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_execution_contract_snapshot_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_paper_ledger_snapshot_read="paper ledger | open=9 | closed=0 | exit_fills=0 | orders=1 | fills=1",
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("execution contract paper ledger snapshot mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_quick_read_contract_paper_execution_alignment_breaks(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        quick_read_contract_paper_execution_contract_aligned=False,
        quick_read_contract_partitioned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["quick_read_contract_checked"] is True
    assert result["quick_read_contract_paper_execution_contract_aligned"] is False
    assert result["quick_read_contract_partitioned"] is False
    assert any("quick read contract paper execution alignment failed" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_index_contract_health_alignment_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_contract_health_paper_execution_contract_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["operating_index_contract_health_paper_execution_contract_aligned"] is False
    assert any("contract health paper execution aligned mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_index_contract_health_summary_drift(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_contract_health_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["quick_read_contract_contract_health_aligned"] is True
    assert result["operating_index_contract_health_aligned"] is False
    assert any("contract health aligned mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_brief_contract_health_partitioned_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        brief_contract_health_contracts_are_well_partitioned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["operating_brief_contract_health_contracts_are_well_partitioned"] is False
    assert any("contract health partitioned brief mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_brief_contract_health_summary_drift(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        brief_contract_health_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["quick_read_contract_contract_health_aligned"] is True
    assert result["operating_brief_contract_health_aligned"] is False
    assert any("contract health aligned brief mismatch" in failure for failure in result["failures"])


def test_check_shadow_health_fails_when_execution_contract_summary_alignment_breaks(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_snapshot_summary_aligned=False,
        execution_contract_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any("execution contract drift detected" in failure for failure in result["failures"])
    assert any(
        "execution contract paper ledger snapshot summary alignment failed" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_execution_contract_self_check_alignment_breaks(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(analysis_dir)
    payload = json.loads((analysis_dir / "btc_1d_execution_contract_screen_latest.json").read_text(encoding="utf-8"))
    payload["execution_contract_summary"]["paper_execution_contract_aligned_summary_aligned"] = False
    _write_json(analysis_dir / "btc_1d_execution_contract_screen_latest.json", payload)

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "execution contract paper execution contract aligned summary alignment failed" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_execution_contract_entry_alignment_breaks(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_checked_aligned_entry_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "execution contract paper execution contract checked aligned entry alignment failed" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_paper_summary_execution_contract_alignment_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_aligned=True,
        summary_execution_contract_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper summary execution contract aligned mismatch" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_paper_summary_snapshot_alignment_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_snapshot_summary_aligned=True,
        summary_execution_contract_snapshot_summary_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper summary execution contract paper ledger snapshot summary alignment mismatch" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_paper_summary_execution_contract_self_check_alignment_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_checked_aligned=True,
        summary_execution_contract_checked_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper summary execution contract paper execution contract checked alignment mismatch"
        in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_paper_summary_execution_contract_self_check_summary_alignment_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_aligned_summary_aligned=True,
        summary_execution_contract_aligned_summary_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper summary execution contract paper execution contract aligned summary alignment mismatch"
        in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_paper_summary_execution_contract_entry_alignment_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_checked_aligned_entry_aligned=True,
        summary_execution_contract_checked_aligned_entry_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper summary execution contract paper execution contract checked aligned entry alignment mismatch"
        in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_paper_summary_execution_contract_summary_summary_alignment_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        execution_contract_aligned_summary_aligned_summary_aligned=True,
        summary_execution_contract_aligned_summary_aligned_summary_aligned=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert any(
        "paper summary execution contract paper execution contract aligned summary aligned summary alignment mismatch"
        in failure
        for failure in result["failures"]
    )


def test_render_health_check_lists_failures() -> None:
    rendered = render_health_check(
        {
            "ok": False,
            "candidate": "low_vol_cap_050_025_minvol020_p2200",
            "shadow_decision": "shadow_ready_for_btc_only",
            "attack_challenger_remote_monitoring_deployment_handoff_ready": True,
            "attack_challenger_next_step": "deployment monitoring active",
            "attack_challenger_bridge_report": "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json",
            "deployment_monitoring_active": True,
            "operating_brief_deployment_monitoring_active": True,
            "carry_decision": "PASS",
            "survivability_decision": "PASS",
            "walk_forward_passed": False,
            "friction_decision": "continue",
            "eth_pass_rate": 0.0,
            "paper_checked": True,
            "paper_execution_read": "paper execution | track=operating | applied=0 | closed=0 | open=1",
            "paper_exit_duplicate_run": True,
            "paper_ledger_snapshot_read": "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1",
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": False,
            "operating_index_paper_execution_contract_checked": True,
            "operating_index_paper_execution_contract_aligned": False,
            "operating_index_paper_execution_contract_checked_aligned": True,
            "operating_index_paper_execution_contract_aligned_aligned": False,
            "operating_index_paper_execution_contract_checked_summary_aligned": True,
            "operating_index_paper_execution_contract_aligned_summary_aligned": False,
            "operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": False,
            "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
            "operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": False,
            "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
            "operating_brief_paper_execution_contract_checked": True,
            "operating_brief_paper_execution_contract_aligned": False,
            "operating_brief_paper_execution_contract_checked_aligned": True,
            "operating_brief_paper_execution_contract_aligned_aligned": False,
            "operating_brief_paper_execution_contract_checked_summary_aligned": True,
            "operating_brief_paper_execution_contract_aligned_summary_aligned": False,
            "operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": False,
            "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
            "operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": False,
            "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
            "execution_contract_checked": True,
            "execution_contract_aligned": False,
            "execution_contract_paper_execution_contract_checked_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned": False,
            "execution_contract_paper_execution_contract_checked_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned": False,
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": False,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": False,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": True,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
            "execution_contract_paper_ledger_snapshot_read": "paper ledger | open=9 | closed=0 | exit_fills=0 | orders=1 | fills=1",
            "quick_read_contract_checked": True,
            "quick_read_contract_operating_contract_aligned": True,
            "quick_read_contract_paper_execution_contract_aligned": False,
            "quick_read_contract_contract_health_aligned": False,
            "quick_read_contract_partitioned": False,
            "operating_index_contract_health_operating_contract_aligned": True,
            "operating_index_contract_health_paper_execution_contract_aligned": False,
            "operating_index_contract_health_aligned": False,
            "operating_index_contract_health_contracts_are_well_partitioned": False,
            "operating_brief_contract_health_operating_contract_aligned": True,
            "operating_brief_contract_health_paper_execution_contract_aligned": False,
            "operating_brief_contract_health_aligned": False,
            "operating_brief_contract_health_contracts_are_well_partitioned": False,
            "failures": ["walk-forward gate failed"],
        }
    )

    assert "BTC 1d Shadow Health Check" in rendered
    assert "status: FAIL" in rendered
    assert "attack_challenger_remote_monitoring_deployment_handoff_ready: True" in rendered
    assert "attack_challenger_next_step: deployment monitoring active" in rendered
    assert (
        "attack_challenger_bridge_report: "
        "analysis_results\\btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    ) in rendered
    assert "deployment_monitoring_active: True" in rendered
    assert "operating_brief_deployment_monitoring_active: True" in rendered
    assert "paper_checked: True" in rendered
    assert "paper_execution_read: paper execution | track=operating | applied=0 | closed=0 | open=1" in rendered
    assert "paper_exit_duplicate_run: True" in rendered
    assert "paper_ledger_snapshot: paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1" in rendered
    assert "paper_execution_contract_checked: True" in rendered
    assert "paper_execution_contract_aligned: False" in rendered
    assert "operating_index_paper_execution_contract_checked: True" in rendered
    assert "operating_index_paper_execution_contract_aligned: False" in rendered
    assert "operating_index_paper_execution_contract_checked_aligned: True" in rendered
    assert "operating_index_paper_execution_contract_aligned_aligned: False" in rendered
    assert "operating_index_paper_execution_contract_checked_summary_aligned: True" in rendered
    assert "operating_index_paper_execution_contract_aligned_summary_aligned: False" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_checked_aligned_entry_aligned: True" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: False" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: True" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: False" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_checked_aligned_summary_aligned: True" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: False" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: True" in rendered
    assert "operating_index_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: False" in rendered
    assert "operating_brief_paper_execution_contract_checked: True" in rendered
    assert "operating_brief_paper_execution_contract_aligned: False" in rendered
    assert "operating_brief_paper_execution_contract_checked_aligned: True" in rendered
    assert "operating_brief_paper_execution_contract_aligned_aligned: False" in rendered
    assert "operating_brief_paper_execution_contract_checked_summary_aligned: True" in rendered
    assert "operating_brief_paper_execution_contract_aligned_summary_aligned: False" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_checked_aligned_entry_aligned: True" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: False" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: True" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: False" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_checked_aligned_summary_aligned: True" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: False" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: True" in rendered
    assert "operating_brief_execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: False" in rendered
    assert "execution_contract_aligned: False" in rendered
    assert "execution_contract_paper_execution_contract_checked_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_aligned: False" in rendered
    assert "execution_contract_paper_execution_contract_checked_summary_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_summary_aligned: False" in rendered
    assert "execution_contract_paper_execution_contract_checked_aligned_entry_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: False" in rendered
    assert "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: False" in rendered
    assert "execution_contract_paper_execution_contract_checked_aligned_summary_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: False" in rendered
    assert "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: True" in rendered
    assert "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: False" in rendered
    assert "execution_contract_paper_ledger_snapshot: paper ledger | open=9 | closed=0 | exit_fills=0 | orders=1 | fills=1" in rendered
    assert "quick_read_contract_operating_contract_aligned: True" in rendered
    assert "quick_read_contract_paper_execution_contract_aligned: False" in rendered
    assert "quick_read_contract_contract_health_aligned: False" in rendered
    assert "quick_read_contract_partitioned: False" in rendered
    assert "operating_index_contract_health_operating_contract_aligned: True" in rendered
    assert "operating_index_contract_health_paper_execution_contract_aligned: False" in rendered
    assert "operating_index_contract_health_aligned: False" in rendered
    assert "operating_index_contract_health_contracts_are_well_partitioned: False" in rendered
    assert "operating_brief_contract_health_operating_contract_aligned: True" in rendered
    assert "operating_brief_contract_health_paper_execution_contract_aligned: False" in rendered
    assert "operating_brief_contract_health_aligned: False" in rendered
    assert "operating_brief_contract_health_contracts_are_well_partitioned: False" in rendered
    assert "- walk-forward gate failed" in rendered


def test_check_shadow_health_prefers_paper_summary_self_check_mirror_over_legacy_contract_origin(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        index_paper_execution_contract_checked_aligned=False,
        brief_paper_execution_contract_checked_aligned=False,
    )
    summary_path = analysis_dir / "btc_1d_paper_nightly_summary_latest.json"
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    summary_payload["paper_execution_contract_checked_aligned"] = False
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is True
    assert result["operating_index_paper_execution_contract_checked_aligned"] is False
    assert result["operating_brief_paper_execution_contract_checked_aligned"] is False


def test_check_shadow_health_fails_when_attack_challenger_handoff_ready_brief_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        attack_challenger_remote_monitoring_deployment_handoff_ready=True,
        brief_attack_challenger_remote_monitoring_deployment_handoff_ready=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["attack_challenger_remote_monitoring_deployment_handoff_ready"] is True
    assert (
        result["operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready"]
        is False
    )
    assert any(
        "attack challenger remote monitoring deployment handoff ready brief mismatch"
        in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_attack_challenger_next_step_brief_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        attack_challenger_next_step="deployment monitoring active",
        brief_attack_challenger_next_step="operator review pending",
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["attack_challenger_next_step"] == "deployment monitoring active"
    assert result["operating_brief_attack_challenger_next_step"] == "operator review pending"
    assert any(
        "attack challenger next step brief mismatch" in failure
        for failure in result["failures"]
    )


def test_check_shadow_health_fails_when_deployment_monitoring_active_brief_drifts(
    tmp_path: Path,
) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir()
    _write_latest_files(analysis_dir)
    _write_paper_files(
        analysis_dir,
        deployment_monitoring_active=True,
        brief_deployment_monitoring_active=False,
    )

    result = check_shadow_health(analysis_dir=analysis_dir, args=build_parser().parse_args([]))

    assert result["ok"] is False
    assert result["deployment_monitoring_active"] is True
    assert result["operating_brief_deployment_monitoring_active"] is False
    assert any(
        "deployment monitoring active brief mismatch" in failure
        for failure in result["failures"]
    )
