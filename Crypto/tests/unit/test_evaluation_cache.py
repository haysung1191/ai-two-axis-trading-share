from __future__ import annotations

from pathlib import Path
from types import MethodType

import pandas as pd

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.evaluation.scorecard import EvaluationScorecard
from app.domains.governance.contracts import Spec, StrategyProposal


def _build_frame(scale: float = 1.0) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=8, freq="h")
    base = pd.Series([100.0 + (i * scale) for i in range(8)], index=idx)
    frame = pd.DataFrame(index=idx)
    frame["open"] = base
    frame["high"] = base * 1.01
    frame["low"] = base * 0.99
    frame["close"] = base
    frame["volume"] = 1000.0
    return frame


def _scorecard(name: str, run_id: str = "run-cache") -> EvaluationScorecard:
    return EvaluationScorecard.model_validate(
        {
            "run_id": run_id,
            "strategy": {
                "name": name,
                "strategy_id": f"{name}_approved",
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
                "cagr": 0.06,
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


def test_evaluation_cache_hit(tmp_path: Path) -> None:
    cache_dir = tmp_path / "evaluation_cache"
    strategy_file = tmp_path / "alpha.py"
    strategy_file.write_text("def get_strategy():\n    return None\n", encoding="utf-8")

    evaluator = CandidateEvaluator(cache_dir=cache_dir)
    calls = {"count": 0}

    def fake_evaluate_candidate(self, run_id, candidate, proposal, spec, ohlcv_by_symbol):
        _ = (proposal, spec, ohlcv_by_symbol)
        calls["count"] += 1
        return _scorecard(str(candidate["strategy_name"]), run_id=run_id)

    evaluator.evaluate_candidate = MethodType(fake_evaluate_candidate, evaluator)

    spec = Spec(run_goal="cache", context="unit", requirements=[], metadata={"symbols": ["BTCUSDT"]})
    candidate = {"strategy_name": "alpha", "file_path": str(strategy_file), "parameters": {"window": 10}}
    proposal = StrategyProposal(strategy_name="alpha", hypothesis="h", market_regime="trend", implementation_notes="i")
    frames = {"BTCUSDT": _build_frame()}

    first = evaluator.evaluate_candidates(
        run_id="run-cache-1",
        candidates=[candidate],
        proposals=[proposal],
        spec=spec,
        ohlcv_by_symbol=frames,
        max_workers=1,
    )
    second = evaluator.evaluate_candidates(
        run_id="run-cache-2",
        candidates=[candidate],
        proposals=[proposal],
        spec=spec,
        ohlcv_by_symbol=frames,
        max_workers=1,
    )

    assert calls["count"] == 1
    assert first[0].strategy.name == second[0].strategy.name
    assert len(list(cache_dir.glob("*.json"))) == 1


def test_cache_invalidation(tmp_path: Path) -> None:
    cache_dir = tmp_path / "evaluation_cache"
    strategy_file = tmp_path / "alpha.py"
    strategy_file.write_text("VALUE = 1\n", encoding="utf-8")

    evaluator = CandidateEvaluator(cache_dir=cache_dir)
    calls = {"count": 0}

    def fake_evaluate_candidate(self, run_id, candidate, proposal, spec, ohlcv_by_symbol):
        _ = (proposal, spec, ohlcv_by_symbol)
        calls["count"] += 1
        return _scorecard(str(candidate["strategy_name"]), run_id=run_id)

    evaluator.evaluate_candidate = MethodType(fake_evaluate_candidate, evaluator)

    spec = Spec(run_goal="cache", context="unit", requirements=[], metadata={"symbols": ["BTCUSDT"]})
    proposal = StrategyProposal(strategy_name="alpha", hypothesis="h", market_regime="trend", implementation_notes="i")

    candidate = {"strategy_name": "alpha", "file_path": str(strategy_file), "parameters": {"window": 10}}
    frames = {"BTCUSDT": _build_frame(scale=1.0)}

    evaluator.evaluate_candidates("run-1", [candidate], [proposal], spec, frames, max_workers=1)
    assert calls["count"] == 1

    candidate_with_new_params = {**candidate, "parameters": {"window": 11}}
    evaluator.evaluate_candidates("run-2", [candidate_with_new_params], [proposal], spec, frames, max_workers=1)
    assert calls["count"] == 2

    strategy_file.write_text("VALUE = 2\n", encoding="utf-8")
    evaluator.evaluate_candidates("run-3", [candidate], [proposal], spec, frames, max_workers=1)
    assert calls["count"] == 3

    changed_frames = {"BTCUSDT": _build_frame(scale=2.0)}
    evaluator.evaluate_candidates("run-4", [candidate], [proposal], spec, changed_frames, max_workers=1)
    assert calls["count"] == 4
