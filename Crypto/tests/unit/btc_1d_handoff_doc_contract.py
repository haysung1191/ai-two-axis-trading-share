from __future__ import annotations

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_RELATIVE_PATH,
)
from tests.unit.btc_1d_handoff_contract_keys import FAST_GATE_SHARED_HANDOFF_KEYS

HANDOFF_BRIDGE_REPORT_RELATIVE_PATH = (
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_RELATIVE_PATH
)
HANDOFF_BRIDGE_REPORT_ABSOLUTE_PATH = (
    r"C:\AI\Crypto\analysis_results"
    "\\"
    f"{ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME}"
)


def build_readme_handoff_confirmation_lines() -> list[str]:
    lines: list[str] = []
    for key in FAST_GATE_SHARED_HANDOFF_KEYS:
        if key == "attack_challenger_next_step":
            lines.append(
                "confirm `attack_challenger_next_step = "
                f"{ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}`"
            )
        elif key == "attack_challenger_bridge_report":
            lines.append(
                "confirm `attack_challenger_bridge_report = "
                f"{HANDOFF_BRIDGE_REPORT_RELATIVE_PATH}`"
            )
        else:
            lines.append(f"confirm `{key} = true`")
    return lines


def build_runbook_final_handoff_confirmation_lines() -> list[str]:
    lines: list[str] = []
    for key in FAST_GATE_SHARED_HANDOFF_KEYS:
        if key == "attack_challenger_next_step":
            lines.append(
                "confirm `attack_challenger_next_step = "
                f"{ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}`"
            )
        elif key == "attack_challenger_bridge_report":
            lines.append(
                "confirm `attack_challenger_bridge_report = "
                f"{HANDOFF_BRIDGE_REPORT_RELATIVE_PATH}`"
            )
        elif key == "deployment_monitoring_active":
            lines.append(
                "confirm `deployment_monitoring_active = true` "
                "on `btc_1d_operator_dashboard_latest.json`"
            )
        else:
            lines.append(f"confirm `{key} = true`")
    return lines


def build_runbook_final_handoff_verification_lines() -> list[str]:
    return [
        "- `attack_challenger_remote_monitoring_deployment_handoff_ready: True`",
        (
            "- `attack_challenger_next_step: "
            f"{ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP}`"
        ),
        "- `deployment_monitoring_active: True`",
        f"- `attack_challenger_bridge_report: {HANDOFF_BRIDGE_REPORT_ABSOLUTE_PATH}`",
    ]
