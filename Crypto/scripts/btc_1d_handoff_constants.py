from __future__ import annotations

from pathlib import Path

ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP = "deployment monitoring active"
ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_NEXT_STEP = (
    "repair_remote_monitoring_and_deployment_handoff"
)
ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE = (
    "remote_monitoring_and_deployment_handoff_queue"
)
ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_LANE = (
    "remote_monitoring_and_deployment_handoff_repair_hold"
)

ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME = (
    "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
)

ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_RELATIVE_PATH = (
    "analysis_results/"
    f"{ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME}"
)


def build_attack_challenger_remote_monitoring_deployment_handoff_path(
    analysis_dir: Path,
) -> Path:
    return analysis_dir / ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME
