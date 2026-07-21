from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_attack_challenger_rotation_application_readiness as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_attack_challenger_rotation_application_readiness_blocks_when_stage_review_is_not_aligned(
    tmp_path: Path,
) -> None:
    _write_json(
        tmp_path / "btc_1d_attack_challenger_promotion_review_latest.json",
        {
            "promotion_review": {
                "promote_attack_challenger_now": True,
                "approved_attack_challenger": "depth055_volume100_hold36",
            },
            "approved_candidate_snapshot": {
                "parameters": {
                    "trend_ema_window": 96,
                    "max_consolidation_depth_pct": 0.055,
                    "min_volume_ratio": 1.0,
                    "max_hold_bars": 36,
                }
            },
        },
    )
    _write_json(
        tmp_path / "btc_1d_post_spike_consolidation_breakout_candidate_stage_review_latest.json",
        {
            "candidate_profile": {
                "label": "post_spike_consolidation_breakout_trend864_depth055_volume100_hold32",
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_walk_forward_diagnostic_20260421T000000Z.json",
        {
            "config": {
                "candidate_label": "post_spike_consolidation_breakout_btcusdt_1d_2200_trend960_depth055_volume100_hold36",
            }
        },
    )
    _write_json(
        tmp_path
        / "btc_1d_post_spike_consolidation_breakout_v4_btcusdt_1d_2200_trend960_depth055_volume100_hold36_paper_validation_20260421T000000Z.json",
        {"decision_record": {"decision": "PASS"}},
    )

    report = mod.build_report(analysis_dir=tmp_path)

    readiness = report["application_readiness"]
    assert readiness["ready_to_apply_rotation"] is False
    assert readiness["rotation_already_applied"] is True
    assert "candidate_stage_review_is_aligned" in readiness["failed_checks"]
    assert readiness["next_step_now"] == "monitor_active_post_spike_challenger_against_attack_stack"


def test_attack_challenger_rotation_application_readiness_main_writes_latest_aliases(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "build_report",
        lambda analysis_dir=tmp_path: {
            "approved_candidate_mapping": {
                "approved_attack_challenger": "depth055_volume100_hold36",
                "candidate_label": "post_spike_consolidation_breakout_btcusdt_1d_2200_trend960_depth055_volume100_hold36",
                "challenger_label": "post_spike_trend960_depth055_volume100_hold36",
                "artifact_prefix": "btcusdt_1d_2200_trend960_depth055_volume100_hold36",
            },
            "application_readiness": {
                "ready_to_apply_rotation": False,
                "failed_checks": ["candidate_stage_review_is_aligned"],
                "next_step_now": "publish_canonical_hold36_candidate_artifacts_before_rotation",
                "reason": "ok",
            },
            "artifact_evidence": {},
            "readiness_checks": [],
            "decision_summary": [],
        },
    )

    exit_code = mod.main()

    assert exit_code == 0
    latest_json = tmp_path / "btc_1d_attack_challenger_rotation_application_readiness_latest.json"
    latest_md = tmp_path / "btc_1d_attack_challenger_rotation_application_readiness_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
