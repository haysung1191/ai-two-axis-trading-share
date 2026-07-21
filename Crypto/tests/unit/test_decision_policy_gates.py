from app.domains.evaluation.decision_policy import DecisionPolicy
from app.domains.evaluation.scorecard import EvaluationScorecard
from app.domains.governance.contracts import Spec


def _scorecard(
    name: str,
    sharpe_mean: float,
    sharpe_std: float,
    sharpe_regime_std: float,
    walk_forward: list[dict],
    flags: list[str],
) -> EvaluationScorecard:
    return EvaluationScorecard.model_validate(
        {
            "run_id": "run-policy-1",
            "strategy": {
                "name": name,
                "strategy_id": f"{name}_approved",
                "source_type": "new",
                "parent_strategy": None,
                "category": "trend_following",
            },
            "single_asset": {
                "symbol": "BTCUSDT",
                "trades": 20,
                "sharpe": sharpe_mean,
                "max_drawdown": 0.12,
                "win_rate": 0.55,
                "cagr": 0.09,
                "equity_curve_summary": {},
            },
            "multi_asset": {
                "sharpe_mean": sharpe_mean,
                "sharpe_std": sharpe_std,
                "drawdown_mean": 0.13,
                "drawdown_worst": 0.16,
            },
            "regime": {
                "sharpe_by_regime": {},
                "drawdown_by_regime": {},
                "sharpe_regime_std": sharpe_regime_std,
            },
            "overfitting": {
                "is_metrics": {"sharpe": sharpe_mean},
                "oos_metrics": {"sharpe": sharpe_mean - 0.1},
                "walk_forward": walk_forward,
                "sensitivity_drift": 0.1,
                "unstable_parameters": [],
                "flags": flags,
            },
            "qa_passed": True,
            "applied_rules": [],
            "violations": [],
            "passed_gates": ["qa", "risk_policy"],
            "failed_gates": [],
            "candidate_pass": True,
            "metadata": {
                "symbols_tested": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                "deterministic_seed": 42,
                "strategy_parameters": {"window": 21, "z_threshold": 1.5},
            },
        }
    )


def test_decision_policy_gates() -> None:
    policy = DecisionPolicy()
    spec = Spec(run_goal="policy", context="unit", requirements=[], metadata={"top_k": 1})

    bad = _scorecard(
        name="bad",
        sharpe_mean=2.5,
        sharpe_std=1.3,
        sharpe_regime_std=1.5,
        walk_forward=[{"window": 1, "metrics": {"sharpe": 2.0}}, {"window": 2, "metrics": {"sharpe": -2.0}}],
        flags=["unstable_parameters"],
    )
    good = _scorecard(
        name="good",
        sharpe_mean=1.1,
        sharpe_std=0.2,
        sharpe_regime_std=0.3,
        walk_forward=[{"window": 1, "metrics": {"sharpe": 1.1}}, {"window": 2, "metrics": {"sharpe": 1.0}}],
        flags=[],
    )

    result = policy.decide(
        run_id="run-policy-1",
        spec=spec,
        scorecards=[bad, good],
        reject_count=0,
        iteration=1,
    )

    assert result["decision_record"]["decision"] == "PASS"
    assert result["approved_strategy"] is not None
    assert result["approved_strategy"]["winners"][0]["strategy_id"] == "good_approved"
    assert result["approved_strategy"]["winners"][0]["parameters"] == {"window": 21, "z_threshold": 1.5}
    assert "overfitting_flags" in result["decision_record"]["failed_gates"]
    assert "stability_score" in result["decision_record"]["failed_gates"]
    assert "cross_asset_instability" in result["decision_record"]["failed_gates"]
    assert "regime_instability" in result["decision_record"]["failed_gates"]
