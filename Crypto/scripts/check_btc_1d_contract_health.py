from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.btc_1d_contract_health_constants import (
    HEALTH_ORDER_ALIAS,
    HEALTH_ORDER_CANONICAL,
    HEALTH_ORDER_DEPRECATION_MESSAGE,
)
from scripts.compare_btc_1d_quick_read_contract_screen import build_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a one-line BTC 1d quick-read contract health check. "
            "Standard operating check order: practical -> research -> contract -> brief. "
            f"{HEALTH_ORDER_CANONICAL} reports whether practical/research/contract health outputs share that same order. "
            f"{HEALTH_ORDER_ALIAS} is a deprecated alias for {HEALTH_ORDER_CANONICAL}."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--as-json", action="store_true")
    return parser


def check_contract_health(*, analysis_dir: Path) -> dict[str, Any]:
    report = build_report(analysis_dir=analysis_dir)
    summary = report.get("contract_summary", {})
    verdict = report.get("contract_verdict", {})
    operating_index_path = analysis_dir / "btc_1d_operating_index_latest.json"
    operating_index_payload: dict[str, Any] = {}
    if operating_index_path.exists():
        operating_index_payload = json.loads(
            operating_index_path.read_text(encoding="utf-8-sig")
        )
    operating_brief_path = analysis_dir / "btc_1d_operating_brief_latest.json"
    operating_brief_payload: dict[str, Any] = {}
    if operating_brief_path.exists():
        operating_brief_payload = json.loads(
            operating_brief_path.read_text(encoding="utf-8-sig")
        )
    meta_contract_summary: dict[str, Any] = {}
    meta_contract_path = analysis_dir / "btc_1d_meta_contract_screen_latest.json"
    if meta_contract_path.exists():
        meta_contract_payload = json.loads(meta_contract_path.read_text(encoding="utf-8-sig"))
        meta_contract_summary = meta_contract_payload.get("meta_contract_summary", {})
    health_order_aligned = meta_contract_summary.get(
        HEALTH_ORDER_CANONICAL,
        meta_contract_summary.get(HEALTH_ORDER_ALIAS, False),
    )
    return {
        "regression_lock_test": report.get("regression_lock_test", "unknown"),
        "operating_brief_version": summary.get("operating_brief_version", "unknown"),
        "operating_index_version": summary.get("operating_index_version", "unknown"),
        "research_stack_version": summary.get("research_stack_version", "unknown"),
        "operating_contract_aligned": summary.get("operating_contract_aligned", False),
        "paper_execution_contract_aligned": summary.get("paper_execution_contract_aligned", False),
        "contract_health_aligned": summary.get("contract_health_aligned", False),
        "research_contract_distinct": summary.get("research_contract_distinct", False),
        "contracts_are_well_partitioned": verdict.get("contracts_are_well_partitioned", False),
        "preferred_operating_contract_version": verdict.get("preferred_operating_contract_version", "unknown"),
        "preferred_research_contract_version": verdict.get("preferred_research_contract_version", "unknown"),
        "shared_standard_check_order": summary.get("shared_standard_check_order", []),
        "standard_check_order_aligned": bool(summary.get("shared_standard_check_order")),
        "attack_challenger_remote_monitoring_deployment_handoff_ready": bool(
            operating_index_payload.get(
                "attack_challenger_remote_monitoring_deployment_handoff_ready", False
            )
        ),
        "attack_challenger_next_step": str(
            operating_index_payload.get("attack_challenger_next_step", "")
        ),
        "attack_challenger_bridge_report": str(
            operating_index_payload.get("attack_challenger_bridge_report", "")
        ),
        "deployment_monitoring_active": bool(
            operating_index_payload.get("deployment_monitoring_active", False)
        ),
        "operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready": bool(
            operating_brief_payload.get(
                "attack_challenger_remote_monitoring_deployment_handoff_ready", False
            )
        ),
        "operating_brief_attack_challenger_next_step": str(
            operating_brief_payload.get("attack_challenger_next_step", "")
        ),
        "operating_brief_attack_challenger_bridge_report": str(
            operating_brief_payload.get("attack_challenger_bridge_report", "")
        ),
        "operating_brief_deployment_monitoring_active": bool(
            operating_brief_payload.get("deployment_monitoring_active", False)
        ),
        "attack_challenger_handoff_aligned": (
            bool(
                operating_brief_payload.get(
                    "attack_challenger_remote_monitoring_deployment_handoff_ready", False
                )
            )
            == bool(
                operating_index_payload.get(
                    "attack_challenger_remote_monitoring_deployment_handoff_ready", False
                )
            )
            and str(operating_brief_payload.get("attack_challenger_next_step", ""))
            == str(operating_index_payload.get("attack_challenger_next_step", ""))
            and str(operating_brief_payload.get("attack_challenger_bridge_report", ""))
            == str(operating_index_payload.get("attack_challenger_bridge_report", ""))
            and bool(operating_brief_payload.get("deployment_monitoring_active", False))
            == bool(operating_index_payload.get("deployment_monitoring_active", False))
        ),
        HEALTH_ORDER_CANONICAL: health_order_aligned,
        HEALTH_ORDER_ALIAS: health_order_aligned,
        "deprecated_fields": {
            HEALTH_ORDER_ALIAS: HEALTH_ORDER_DEPRECATION_MESSAGE,
        },
    }


def render_contract_health_line(result: dict[str, Any]) -> str:
    standard_order = result.get("shared_standard_check_order", [])
    standard_order_text = " > ".join(standard_order) if standard_order else "n/a"
    return (
        f"BTC 1d contract health | operating_brief={result['operating_brief_version']} | "
        f"operating_index={result['operating_index_version']} | "
        f"aligned={result['operating_contract_aligned']} | "
        f"paper_execution_aligned={result.get('paper_execution_contract_aligned', False)} | "
        f"contract_health_aligned={result.get('contract_health_aligned', False)} | "
        f"research={result['research_stack_version']} | "
        f"distinct={result['research_contract_distinct']} | "
        f"partitioned={result['contracts_are_well_partitioned']} | "
        "attack_challenger_handoff_ready="
        f"{result.get('attack_challenger_remote_monitoring_deployment_handoff_ready', False)} | "
        f"attack_challenger_next={result.get('attack_challenger_next_step', '')} | "
        f"attack_challenger_bridge_report={result.get('attack_challenger_bridge_report', '')} | "
        f"deployment_monitoring_active={result.get('deployment_monitoring_active', False)} | "
        f"attack_challenger_handoff_aligned={result.get('attack_challenger_handoff_aligned', False)} | "
        f"standard_order_aligned={result['standard_check_order_aligned']} | "
        f"{HEALTH_ORDER_CANONICAL}={result[HEALTH_ORDER_CANONICAL]} | "
        f"standard_order={standard_order_text}"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_contract_health(analysis_dir=args.analysis_dir)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(render_contract_health_line(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
