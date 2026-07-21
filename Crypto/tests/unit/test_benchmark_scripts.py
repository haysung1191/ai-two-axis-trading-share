from pathlib import Path

from scripts.run_clean_benchmark import build_group_metadata, build_spec
from scripts.summarize_clean_benchmark import build_summary_rows


def test_build_group_metadata_applies_ablation_toggles() -> None:
    assert build_group_metadata("no_mutation", 1)["mutation_enabled"] is False
    assert build_group_metadata("no_regime_validation", 1)["regime_validation_enabled"] is False
    assert build_group_metadata("no_multi_asset_gate", 1)["multi_asset_gate_enabled"] is False
    assert build_group_metadata("no_overfitting_gate", 1)["overfitting_gate_enabled"] is False
    assert build_group_metadata("search_budget_stress", 1)["proposal_count"] == 20
    assert build_group_metadata("cost_friction_stress", 1)["fee_bps"] == 20.0


def test_build_spec_embeds_group_metadata() -> None:
    spec = build_spec("full_system", 2)
    assert spec.metadata["benchmark_group"] == "full_system"
    assert spec.metadata["benchmark_repetition"] == 2
    assert "benchmark-batch" in spec.requirements


def test_build_summary_rows_groups_benchmark_runs(tmp_path: Path) -> None:
    run_a = tmp_path / "run-a"
    run_b = tmp_path / "run-b"
    run_a.mkdir()
    run_b.mkdir()

    (run_a / "spec.json").write_text(
        '{"metadata":{"benchmark_group":"full_system"}}',
        encoding="utf-8",
    )
    (run_a / "decision_record.json").write_text(
        '{"decision":"PASS"}',
        encoding="utf-8",
    )
    (run_a / "run_leaderboard.json").write_text(
        '{"entries":[{"sharpe":1.2,"max_drawdown":0.2,"sharpe_std":0.1,"sharpe_regime_std":0.2,"trades":12}]}',
        encoding="utf-8",
    )

    (run_b / "spec.json").write_text(
        '{"metadata":{"benchmark_group":"full_system"}}',
        encoding="utf-8",
    )
    (run_b / "decision_record.json").write_text(
        '{"decision":"FAIL"}',
        encoding="utf-8",
    )
    (run_b / "run_leaderboard.json").write_text(
        '{"entries":[{"sharpe":0.8,"max_drawdown":0.3,"sharpe_std":0.4,"sharpe_regime_std":0.5,"trades":8}]}',
        encoding="utf-8",
    )

    rows = build_summary_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["group"] == "full_system"
    assert rows[0]["runs"] == 2
    assert rows[0]["pass_count"] == 1
