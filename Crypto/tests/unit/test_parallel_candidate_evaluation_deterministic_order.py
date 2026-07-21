import time
from types import MethodType

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.evaluation.scorecard import EvaluationScorecard
from app.domains.governance.contracts import Spec, StrategyProposal


def test_parallel_candidate_evaluation_deterministic_order() -> None:
    evaluator = CandidateEvaluator(deterministic_seed=42)

    def fake_evaluate_candidate(self, run_id, candidate, proposal, spec, ohlcv_by_symbol):
        _ = (run_id, proposal, spec, ohlcv_by_symbol)
        time.sleep(float(candidate["delay_sec"]))
        return EvaluationScorecard.model_validate(
            {
                "run_id": "run-order-1",
                "strategy": {
                    "name": candidate["strategy_name"],
                    "strategy_id": f"{candidate['strategy_name']}_approved",
                    "source_type": "new",
                    "parent_strategy": None,
                    "category": "momentum",
                },
                "single_asset": {
                    "symbol": "BTCUSDT",
                    "trades": 10,
                    "sharpe": 1.0,
                    "max_drawdown": 0.1,
                    "win_rate": 0.5,
                    "cagr": 0.05,
                    "equity_curve_summary": {},
                },
                "multi_asset": {
                    "sharpe_mean": 1.0,
                    "sharpe_std": 0.1,
                    "drawdown_mean": 0.1,
                    "drawdown_worst": 0.1,
                },
                "regime": {
                    "sharpe_by_regime": {},
                    "drawdown_by_regime": {},
                    "sharpe_regime_std": 0.1,
                },
                "overfitting": {
                    "is_metrics": {},
                    "oos_metrics": {},
                    "walk_forward": [],
                    "sensitivity_drift": 0.0,
                    "unstable_parameters": [],
                    "flags": [],
                },
                "qa_passed": True,
                "applied_rules": [],
                "violations": [],
                "passed_gates": ["qa", "risk_policy"],
                "failed_gates": [],
                "candidate_pass": True,
                "metadata": {
                    "symbols_tested": ["BTCUSDT"],
                    "deterministic_seed": 42,
                },
            }
        )

    evaluator.evaluate_candidate = MethodType(fake_evaluate_candidate, evaluator)

    candidates = [
        {"strategy_name": "s1", "delay_sec": 0.04},
        {"strategy_name": "s2", "delay_sec": 0.03},
        {"strategy_name": "s3", "delay_sec": 0.02},
        {"strategy_name": "s4", "delay_sec": 0.01},
    ]
    proposals = [
        StrategyProposal(
            strategy_name=row["strategy_name"],
            hypothesis="h",
            market_regime="trend",
            implementation_notes="i",
        )
        for row in candidates
    ]
    spec = Spec(run_goal="order", context="unit", requirements=[], metadata={"symbols": ["BTCUSDT"]})

    result = evaluator.evaluate_candidates(
        run_id="run-order-1",
        candidates=candidates,
        proposals=proposals,
        spec=spec,
        max_workers=4,
    )

    assert [scorecard.strategy.name for scorecard in result] == ["s1", "s2", "s3", "s4"]
