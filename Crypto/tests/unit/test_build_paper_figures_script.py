from pathlib import Path

from scripts.build_paper_figures import build_paper_figures


def test_build_paper_figures_writes_expected_outputs(tmp_path: Path) -> None:
    paper_results = tmp_path / "paper_results"
    paper_results.mkdir(parents=True, exist_ok=True)

    (paper_results / "candidate_metrics.csv").write_text(
        "\n".join(
            [
                "run_id,strategy_name,source_type,category,sharpe_mean,sharpe_std,sharpe_regime_std,candidate_pass",
                "run-1,alpha,new,momentum,1.2,0.3,0.4,True",
                "run-1,beta,mutation,mean_reversion,0.8,0.6,1.1,False",
            ]
        ),
        encoding="utf-8",
    )
    (paper_results / "rejection_reasons.csv").write_text(
        "\n".join(
            [
                "failed_gate,candidate_count,run_count",
                "execution_model,10,3",
                "overfitting_flags,4,2",
            ]
        ),
        encoding="utf-8",
    )
    (paper_results / "source_type_stats.csv").write_text(
        "\n".join(
            [
                "source_type,candidate_count,pass_count,pass_rate,mean_sharpe",
                "new,1,1,1.0,1.2",
                "mutation,1,0,0.0,0.8",
            ]
        ),
        encoding="utf-8",
    )
    (paper_results / "category_stats.csv").write_text(
        "\n".join(
            [
                "category,candidate_count,pass_count,pass_rate,mean_sharpe",
                "momentum,1,1,1.0,1.2",
                "mean_reversion,1,0,0.0,0.8",
            ]
        ),
        encoding="utf-8",
    )
    (paper_results / "terminal_state_stats.csv").write_text(
        "\n".join(
            [
                "decision,run_count,run_rate",
                "PASS,1,0.5",
                "PAUSE,1,0.5",
            ]
        ),
        encoding="utf-8",
    )
    (paper_results / "candidate_funnel.csv").write_text(
        "\n".join(
            [
                "stage,count",
                "runs,1",
                "candidates_evaluated,2",
                "candidates_passed,1",
                "approved_runs,1",
                "approved_strategies_in_registry,1",
            ]
        ),
        encoding="utf-8",
    )
    (paper_results / "lineage_edges.csv").write_text(
        "\n".join(
            [
                "parent_strategy,strategy_id,source_type",
                "alpha_v1_approved,beta_approved,mutation",
            ]
        ),
        encoding="utf-8",
    )

    outputs = build_paper_figures(paper_results_dir=paper_results, output_dir=tmp_path / "paper_figures")

    assert outputs["system_overview"].exists()
    assert outputs["candidate_funnel"].exists()
    assert outputs["rejection_reasons"].exists()
    assert outputs["source_type_comparison"].exists()
    assert outputs["cross_asset_stability"].exists()
    assert outputs["regime_stability"].exists()
    assert outputs["category_outcomes"].exists()
    assert outputs["terminal_states"].exists()
    assert outputs["lineage_graph"].exists()
    assert outputs["manifest"].exists()
