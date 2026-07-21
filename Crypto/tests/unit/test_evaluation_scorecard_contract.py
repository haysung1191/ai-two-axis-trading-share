from app.domains.evaluation.scorecard import EvaluationScorecard


def test_evaluation_scorecard_contract() -> None:
    payload = {
        "run_id": "run-1",
        "strategy": {
            "name": "alpha",
            "strategy_id": "alpha_approved",
            "source_type": "new",
            "parent_strategy": None,
            "category": "momentum",
        },
        "single_asset": {
            "symbol": "BTCUSDT",
            "trades": 22,
            "sharpe": 1.2,
            "max_drawdown": 0.15,
            "win_rate": 0.58,
            "cagr": 0.11,
            "equity_curve_summary": {"start": 1.0, "end": 1.2},
        },
        "multi_asset": {
            "sharpe_mean": 1.1,
            "sharpe_std": 0.2,
            "drawdown_mean": 0.14,
            "drawdown_worst": 0.18,
        },
        "regime": {
            "sharpe_by_regime": {"trend": 1.4, "range": 0.9},
            "drawdown_by_regime": {"trend": 0.1, "range": 0.2},
            "sharpe_regime_std": 0.25,
        },
        "overfitting": {
            "is_metrics": {"sharpe": 1.4},
            "oos_metrics": {"sharpe": 1.1},
            "walk_forward": [{"window": 1, "metrics": {"sharpe": 1.2}}],
            "sensitivity_drift": 0.1,
            "unstable_parameters": [],
            "flags": [],
        },
        "qa_passed": True,
        "applied_rules": ["backtest_thresholds"],
        "violations": [],
        "passed_gates": ["qa", "risk_policy"],
        "failed_gates": [],
        "candidate_pass": True,
        "metadata": {
            "symbols_tested": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "deterministic_seed": 42,
        },
    }

    scorecard = EvaluationScorecard.model_validate(payload)

    assert scorecard.strategy.name == "alpha"
    assert scorecard.multi_asset.sharpe_std == 0.2
    assert scorecard.metadata.deterministic_seed == 42
