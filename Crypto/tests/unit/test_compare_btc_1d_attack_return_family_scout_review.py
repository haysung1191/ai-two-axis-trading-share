from __future__ import annotations

import json
from pathlib import Path

import scripts.compare_btc_1d_attack_return_family_scout_review as mod


def _write_batch(path: Path, family: str, base_gap: float, cost20_gap: float, replacement_open: bool) -> None:
    row = {
        "family": family,
        "variant_label": "leader",
        "base_cagr_gap_to_main": base_gap,
        "cost20_cagr_gap_to_main": cost20_gap,
        "max_sensitivity_drift": 0.12,
        "base_sharpe": 1.9,
        "mdd_improvement_vs_main": 0.07,
        "negative_window_clean": replacement_open,
        "replacement_open_passed": replacement_open,
    }
    path.write_text(json.dumps({"results": [row]}), encoding="utf-8")


def _write_common_rules(path: Path, families: list[str]) -> None:
    payload = {"leaders": [{"family": family} for family in families]}
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_return_family_scout_review_collects_latest_family_rows(tmp_path, monkeypatch) -> None:
    _write_batch(tmp_path / "btc_1d_attack_return_family_scout_batch_20260515T000001Z.json", "family_a", 0.10, 0.09, False)
    _write_batch(tmp_path / "btc_1d_attack_return_family_scout_batch_20260515T000002Z.json", "family_b", 0.03, 0.04, True)
    _write_common_rules(tmp_path / "btc_1d_attack_common_rules_latest.json", ["family_a", "family_b"])
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(mod, "COMMON_RULES_LATEST", tmp_path / "btc_1d_attack_common_rules_latest.json")

    report = mod.build_report()

    assert report["return_family_scout_reference"]["completed_family_count"] == 2
    assert report["return_family_scout_reference"]["replacement_open_count"] == 1
    assert report["return_family_scout_verdict"]["main_gap_recovery_found"] is True
    assert report["return_family_scout_verdict"]["next_step_now"] == "open_attack_main_replacement_review"


def test_return_family_scout_review_reports_expand_when_none_pass(tmp_path, monkeypatch) -> None:
    _write_batch(tmp_path / "btc_1d_attack_return_family_scout_batch_20260515T000001Z.json", "family_a", 0.10, 0.09, False)
    _write_common_rules(tmp_path / "btc_1d_attack_common_rules_latest.json", ["family_a", "family_b"])
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(mod, "COMMON_RULES_LATEST", tmp_path / "btc_1d_attack_common_rules_latest.json")

    report = mod.build_report()

    assert report["return_family_scout_reference"]["completed_family_count"] == 1
    assert report["return_family_scout_verdict"]["main_gap_recovery_found"] is False
    assert report["return_family_scout_verdict"]["next_step_now"] == "expand_return_family_scout_with_unchecked_leaders"


def test_return_family_scout_review_closes_when_all_common_rule_leaders_checked(tmp_path, monkeypatch) -> None:
    _write_batch(tmp_path / "btc_1d_attack_return_family_scout_batch_20260515T000001Z.json", "family_a", 0.10, 0.09, False)
    _write_batch(tmp_path / "btc_1d_attack_return_family_scout_batch_20260515T000002Z.json", "family_b", 0.12, 0.10, False)
    _write_common_rules(tmp_path / "btc_1d_attack_common_rules_latest.json", ["family_a", "family_b"])
    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)
    monkeypatch.setattr(mod, "COMMON_RULES_LATEST", tmp_path / "btc_1d_attack_common_rules_latest.json")

    report = mod.build_report()

    assert report["return_family_scout_reference"]["unchecked_common_rule_leader_count"] == 0
    assert report["return_family_scout_verdict"]["main_gap_recovery_found"] is False
    assert (
        report["return_family_scout_verdict"]["next_step_now"]
        == "close_common_rule_return_family_scout_and_open_new_return_family_axis"
    )
