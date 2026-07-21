from __future__ import annotations

from pathlib import Path

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_LANE,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_RELATIVE_PATH,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
    build_attack_challenger_remote_monitoring_deployment_handoff_path,
)


def test_handoff_constants_lock_next_step_and_paths() -> None:
    assert ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP == "deployment monitoring active"
    assert (
        ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_NEXT_STEP
        == "repair_remote_monitoring_and_deployment_handoff"
    )
    assert (
        ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE
        == "remote_monitoring_and_deployment_handoff_queue"
    )
    assert (
        ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_LANE
        == "remote_monitoring_and_deployment_handoff_repair_hold"
    )
    assert (
        ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_BASENAME
        == "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    assert (
        ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_RELATIVE_PATH
        == "analysis_results/"
        "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )


def test_build_attack_challenger_remote_monitoring_deployment_handoff_path() -> None:
    analysis_dir = Path(r"C:\AI\Crypto\analysis_results")

    assert build_attack_challenger_remote_monitoring_deployment_handoff_path(
        analysis_dir
    ) == (
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
