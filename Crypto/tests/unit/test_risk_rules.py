from pathlib import Path

from app.domains.governance.risk_policy import RiskPolicy


def test_risk_rules_reject_violating_strategy() -> None:
    policy = RiskPolicy(rules_path=Path("app/domains/governance/rules/risk_rules.yml"))
    metadata = {
        "strategy_name": "martingale_scalper",
        "position_size": 0.5,
        "expected_max_drawdown": 0.15,
        "min_sharpe": 1.0,
        "max_drawdown": 0.2,
        "min_win_rate": 0.5,
        "min_cagr": 0.05,
    }
    backtest = {
        "sharpe": 0.2,
        "max_drawdown": 0.4,
        "win_rate": 0.3,
        "cagr": -0.1,
    }
    overfitting = {"passed": False, "sensitivity_max_drift": 0.8}

    _, violations, failed_gates = policy.evaluate(metadata, backtest, overfitting)

    assert violations
    assert failed_gates
    assert any("blocked strategy keyword detected" in violation for violation in violations)
