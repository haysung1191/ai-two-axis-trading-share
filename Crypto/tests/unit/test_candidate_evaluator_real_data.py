from __future__ import annotations

from types import MethodType

import pandas as pd
import pytest

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.evaluation.scorecard import EvaluationScorecard
from app.domains.governance.contracts import Spec, StrategyProposal
from app.domains.backtesting.runner import BacktestMetrics, MultiAssetBacktestMetrics


class _FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int, int]] = []

    def get_ohlcv(self, symbol: str, interval: str, start_ts: int, end_ts: int) -> pd.DataFrame:
        self.calls.append((symbol, interval, start_ts, end_ts))
        idx = pd.date_range("2024-01-01", periods=32, freq="h", tz="UTC")
        close = pd.Series([100 + i for i in range(32)], index=idx, dtype=float)
        frame = pd.DataFrame(index=idx)
        frame["open"] = close
        frame["high"] = close + 1.0
        frame["low"] = close - 1.0
        frame["close"] = close
        frame["volume"] = 1000.0
        return frame[["open", "high", "low", "close", "volume"]]


def _scorecard(name: str, run_id: str) -> EvaluationScorecard:
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
                "cagr": 0.05,
                "equity_curve_summary": {},
                "equity_curve": [1.0, 1.1],
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
                "symbols_tested": ["BTCUSDT", "ETHUSDT"],
                "deterministic_seed": 42,
            },
        }
    )


def test_candidate_evaluator_real_data(monkeypatch) -> None:
    provider = _FakeProvider()
    evaluator = CandidateEvaluator(data_provider=provider, deterministic_seed=42)

    def fake_build_ohlcv(spec, symbol="BTCUSDT"):
        _ = (spec, symbol)
        raise AssertionError("Synthetic fallback should not be used in this test")

    def fake_evaluate_candidate(self, run_id, candidate, proposal, spec, ohlcv_by_symbol):
        _ = (proposal, spec, ohlcv_by_symbol)
        return _scorecard(str(candidate["strategy_name"]), run_id=run_id)

    monkeypatch.setattr(CandidateEvaluator, "build_ohlcv", staticmethod(fake_build_ohlcv))
    evaluator.evaluate_candidate = MethodType(fake_evaluate_candidate, evaluator)

    spec = Spec(
        run_goal="real data path",
        context="unit test",
        requirements=[],
        metadata={
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "ohlcv_interval": "1h",
            "ohlcv_start_ts": 1704067200000,
            "ohlcv_end_ts": 1704182400000,
        },
    )
    candidates = [{"strategy_name": "s1"}, {"strategy_name": "s2"}]
    proposals = [
        StrategyProposal(strategy_name="s1", hypothesis="h", market_regime="trend", implementation_notes="i"),
        StrategyProposal(strategy_name="s2", hypothesis="h", market_regime="trend", implementation_notes="i"),
    ]

    result = evaluator.evaluate_candidates(
        run_id="run-real-data-1",
        candidates=candidates,
        proposals=proposals,
        spec=spec,
        max_workers=1,
    )

    assert len(result) == 2
    assert [x.strategy.name for x in result] == ["s1", "s2"]
    assert len(provider.calls) == 2
    assert provider.calls[0][0] == "BTCUSDT"
    assert provider.calls[1][0] == "ETHUSDT"


def test_candidate_evaluator_defaults_to_krw_symbols(monkeypatch) -> None:
    provider = _FakeProvider()
    evaluator = CandidateEvaluator(data_provider=provider, deterministic_seed=42)

    def fake_build_ohlcv(spec, symbol="KRW-BTC"):
        _ = (spec, symbol)
        raise AssertionError("Synthetic fallback should not be used in this test")

    def fake_evaluate_candidate(self, run_id, candidate, proposal, spec, ohlcv_by_symbol):
        _ = (proposal, spec, ohlcv_by_symbol)
        return _scorecard(str(candidate["strategy_name"]), run_id=run_id)

    monkeypatch.setattr(CandidateEvaluator, "build_ohlcv", staticmethod(fake_build_ohlcv))
    evaluator.evaluate_candidate = MethodType(fake_evaluate_candidate, evaluator)

    spec = Spec(
        run_goal="krw defaults",
        context="unit test",
        requirements=[],
        metadata={
            "ohlcv_interval": "1h",
            "ohlcv_start_ts": 1704067200000,
            "ohlcv_end_ts": 1704182400000,
        },
    )
    candidates = [{"strategy_name": "s1"}]
    proposals = [StrategyProposal(strategy_name="s1", hypothesis="h", market_regime="trend", implementation_notes="i")]

    result = evaluator.evaluate_candidates(
        run_id="run-krw-defaults",
        candidates=candidates,
        proposals=proposals,
        spec=spec,
        max_workers=1,
    )

    assert len(result) == 1
    assert [call[0] for call in provider.calls] == ["KRW-BTC", "KRW-ETH", "KRW-SOL"]
    assert "BTCUSDT" not in [call[0] for call in provider.calls]


def test_candidate_evaluator_raises_when_real_data_fetch_fails_by_default() -> None:
    class _FailingProvider:
        def get_ohlcv(self, symbol: str, interval: str, start_ts: int, end_ts: int) -> pd.DataFrame:
            _ = (symbol, interval, start_ts, end_ts)
            raise RuntimeError("network down")

    evaluator = CandidateEvaluator(data_provider=_FailingProvider(), deterministic_seed=42)
    spec = Spec(
        run_goal="real data required",
        context="unit test",
        requirements=[],
        metadata={"symbols": ["BTCUSDT"], "ohlcv_interval": "1h"},
    )
    candidates = [{"strategy_name": "s1"}]
    proposals = [StrategyProposal(strategy_name="s1", hypothesis="h", market_regime="trend", implementation_notes="i")]

    with pytest.raises(RuntimeError, match="Failed to load real OHLCV data"):
        evaluator.evaluate_candidates(
            run_id="run-real-data-fail",
            candidates=candidates,
            proposals=proposals,
            spec=spec,
            max_workers=1,
        )


def test_candidate_evaluator_allows_explicit_synthetic_fallback(monkeypatch) -> None:
    class _FailingProvider:
        def get_ohlcv(self, symbol: str, interval: str, start_ts: int, end_ts: int) -> pd.DataFrame:
            _ = (symbol, interval, start_ts, end_ts)
            raise RuntimeError("network down")

    evaluator = CandidateEvaluator(data_provider=_FailingProvider(), deterministic_seed=42)

    def fake_evaluate_candidate(self, run_id, candidate, proposal, spec, ohlcv_by_symbol):
        _ = (proposal, spec, ohlcv_by_symbol)
        return _scorecard(str(candidate["strategy_name"]), run_id=run_id)

    evaluator.evaluate_candidate = MethodType(fake_evaluate_candidate, evaluator)

    spec = Spec(
        run_goal="synthetic fallback",
        context="unit test",
        requirements=[],
        metadata={
            "symbols": ["BTCUSDT"],
            "ohlcv_interval": "1h",
            "allow_synthetic_ohlcv_fallback": True,
        },
    )
    candidates = [{"strategy_name": "s1"}]
    proposals = [StrategyProposal(strategy_name="s1", hypothesis="h", market_regime="trend", implementation_notes="i")]

    result = evaluator.evaluate_candidates(
        run_id="run-real-data-synthetic",
        candidates=candidates,
        proposals=proposals,
        spec=spec,
        max_workers=1,
    )

    assert len(result) == 1


def test_candidate_evaluator_builds_basket_risk_report() -> None:
    multi_metrics = MultiAssetBacktestMetrics(
        symbols=["BTCUSDT", "ETHUSDT"],
        per_symbol={
            "BTCUSDT": BacktestMetrics(
                trades=12,
                sharpe=1.5,
                max_drawdown=0.10,
                win_rate=0.60,
                cagr=0.12,
                equity_curve_summary={},
                equity_curve=[1.0, 1.1, 1.2],
            ),
            "ETHUSDT": BacktestMetrics(
                trades=8,
                sharpe=0.4,
                max_drawdown=0.25,
                win_rate=0.45,
                cagr=0.02,
                equity_curve_summary={},
                equity_curve=[1.0, 1.05, 1.1],
            ),
        },
        sharpe_mean=0.95,
        sharpe_std=0.55,
        drawdown_mean=0.175,
        drawdown_worst=0.25,
    )

    report = CandidateEvaluator._build_basket_risk_report(multi_metrics)

    assert report["trades"] == 20
    assert report["sharpe"] == pytest.approx(0.95)
    assert report["max_drawdown"] == pytest.approx(0.25)
    assert report["win_rate"] == pytest.approx(0.525)
    basket_final_equity = (1.2 + 1.1) / 2.0
    expected_cagr = float((basket_final_equity ** (1 / (2 / (365.25 * 24.0)))) - 1.0)
    assert report["cagr"] == pytest.approx(expected_cagr)
    assert set(report["symbol_metrics"].keys()) == {"BTCUSDT", "ETHUSDT"}


def test_candidate_evaluator_uses_basket_report_for_risk_policy(monkeypatch, tmp_path) -> None:
    class _FakeRunner:
        def run_multi_symbol(self, strategy, symbols, ohlcv_by_symbol, params=None, **kwargs):
            _ = (strategy, symbols, ohlcv_by_symbol, params, kwargs)
            return MultiAssetBacktestMetrics(
                symbols=["BTCUSDT", "ETHUSDT"],
                per_symbol={
                    "BTCUSDT": BacktestMetrics(
                        trades=20,
                        sharpe=2.0,
                        max_drawdown=0.05,
                        win_rate=0.70,
                        cagr=0.20,
                        equity_curve_summary={},
                        equity_curve=[],
                    ),
                    "ETHUSDT": BacktestMetrics(
                        trades=20,
                        sharpe=0.8,
                        max_drawdown=0.30,
                        win_rate=0.50,
                        cagr=0.04,
                        equity_curve_summary={},
                        equity_curve=[],
                    ),
                },
                sharpe_mean=1.4,
                sharpe_std=0.6,
                drawdown_mean=0.175,
                drawdown_worst=0.30,
            )

        def evaluate_regimes(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return {
                "sharpe_by_regime": {"trend": 1.0},
                "drawdown_by_regime": {"trend": 0.1},
                "sharpe_regime_std": 0.1,
            }

    class _FakeOverfitting:
        passed = True
        is_metrics = {"sharpe": 1.2}
        oos_metrics = {"sharpe": 1.0}
        walk_forward = [{"window": 1, "metrics": {"sharpe": 1.1}}]
        sensitivity_max_drift = 0.1
        unstable_parameters: list[str] = []

        def evaluate(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return self

    captured: dict[str, object] = {}

    class _FakeRiskPolicy:
        rules = {"overfitting": {}}

        def evaluate(self, metadata, backtest_report, overfitting_report):
            captured["metadata"] = metadata
            captured["backtest_report"] = backtest_report
            captured["overfitting_report"] = overfitting_report
            return ["backtest_thresholds"], [], []

    monkeypatch.setattr("app.domains.evaluation.candidate_evaluator.load_strategy", lambda *args, **kwargs: object())

    evaluator = CandidateEvaluator(
        runner=_FakeRunner(),
        overfitting=_FakeOverfitting(),
        risk_policy=_FakeRiskPolicy(),
        cache_dir=tmp_path / "cache",
    )
    spec = Spec(
        run_goal="basket gate",
        context="unit test",
        requirements=[],
        metadata={"fee_bps": 8.0, "slippage_bps": 8.0},
    )
    proposal = StrategyProposal(
        strategy_name="mean_reversion",
        hypothesis="h",
        market_regime="range",
        implementation_notes="i",
    )
    idx = pd.date_range("2024-01-01", periods=48, freq="h", tz="UTC")
    close = pd.Series(range(48), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    scorecard = evaluator.evaluate_candidate(
        run_id="run-basket-risk",
        candidate={
            "strategy_name": "mean_reversion",
            "file_path": str(tmp_path / "mean_reversion.py"),
            "parameters": {"window": 21},
            "source_type": "new",
        },
        proposal=proposal,
        spec=spec,
        ohlcv_by_symbol={"BTCUSDT": frame, "ETHUSDT": frame},
    )

    backtest_report = captured["backtest_report"]
    assert isinstance(backtest_report, dict)
    assert backtest_report["sharpe"] == pytest.approx(1.4)
    assert backtest_report["max_drawdown"] == pytest.approx(0.30)
    assert backtest_report["win_rate"] == pytest.approx(0.60)
    assert backtest_report["cagr"] == pytest.approx(0.12)
    assert backtest_report["trades"] == 40
    assert scorecard.candidate_pass is True


def test_candidate_evaluator_supports_krw_rotation_candidate(monkeypatch, tmp_path) -> None:
    class _FakeRunner:
        def run(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return BacktestMetrics(
                trades=12,
                sharpe=1.1,
                max_drawdown=0.08,
                win_rate=0.55,
                cagr=0.09,
                equity_curve_summary={},
                equity_curve=[],
            )

        def evaluate_regimes(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return {
                "sharpe_by_regime": {"trend": 1.0},
                "drawdown_by_regime": {"trend": 0.1},
                "sharpe_regime_std": 0.1,
            }

    class _FakeOverfitting:
        passed = True
        is_metrics = {"sharpe": 1.0}
        oos_metrics = {"sharpe": 0.9}
        walk_forward = []
        sensitivity_max_drift = 0.0
        unstable_parameters: list[str] = []

        def evaluate(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return self

    class _FakeRiskPolicy:
        rules = {"overfitting": {}}

        def evaluate(self, metadata, backtest_report, overfitting_report):
            _ = (metadata, backtest_report, overfitting_report)
            return ["backtest_thresholds"], [], []

    class _RotationStrategy:
        name = "krw_relative_strength_rotation"
        default_params = {"btc_symbol": "KRW-BTC", "ema_window": 72, "lookback": 24, "atr_window": 24, "top_k": 3}

        def generate_signals(self, ohlcv, params=None):
            _ = (ohlcv, params)
            return pd.Series(dtype=float)

        def generate_multi_signals(self, ohlcv_by_symbol, params=None):
            _ = params
            index = next(iter(ohlcv_by_symbol.values())).index
            return {
                "KRW-ETH": pd.Series(1.0, index=index, dtype=float),
                "KRW-SOL": pd.Series(0.0, index=index, dtype=float),
            }

    monkeypatch.setattr("app.domains.evaluation.candidate_evaluator.load_strategy", lambda *args, **kwargs: _RotationStrategy())

    evaluator = CandidateEvaluator(
        runner=_FakeRunner(),
        overfitting=_FakeOverfitting(),
        risk_policy=_FakeRiskPolicy(),
        cache_dir=tmp_path / "cache",
    )
    proposal = StrategyProposal(
        strategy_name="krw_relative_strength_rotation",
        strategy_category="momentum",
        hypothesis="h",
        market_regime="trend",
        implementation_notes="i",
    )
    idx = pd.date_range("2024-01-01", periods=80, freq="h", tz="UTC")
    close = pd.Series(range(80), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    scorecard = evaluator.evaluate_candidate(
        run_id="run-rotation",
        candidate={
            "strategy_name": "krw_relative_strength_rotation",
            "file_path": str(tmp_path / "krw_relative_strength_rotation.py"),
            "parameters": {"btc_symbol": "KRW-BTC", "ema_window": 72, "lookback": 24, "atr_window": 24, "top_k": 3},
            "source_type": "new",
            "strategy_category": "momentum",
        },
        proposal=proposal,
        spec=Spec(run_goal="rotation", context="unit test", requirements=[], metadata={"fee_bps": 8.0, "slippage_bps": 8.0}),
        ohlcv_by_symbol={"KRW-BTC": frame, "KRW-ETH": frame, "KRW-SOL": frame},
    )

    assert scorecard.strategy.name == "krw_relative_strength_rotation"
    assert scorecard.metadata.symbols_tested == ["KRW-ETH", "KRW-SOL"]
    assert scorecard.candidate_pass is True


def test_candidate_evaluator_supports_krw_volume_breakout_candidate(monkeypatch, tmp_path) -> None:
    class _FakeRunner:
        def run(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return BacktestMetrics(
                trades=14,
                sharpe=1.25,
                max_drawdown=0.07,
                win_rate=0.58,
                cagr=0.11,
                equity_curve_summary={},
                equity_curve=[],
            )

        def evaluate_regimes(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return {
                "sharpe_by_regime": {"trend": 1.0},
                "drawdown_by_regime": {"trend": 0.1},
                "sharpe_regime_std": 0.1,
            }

    class _FakeOverfitting:
        passed = True
        is_metrics = {"sharpe": 1.0}
        oos_metrics = {"sharpe": 0.9}
        walk_forward = []
        sensitivity_max_drift = 0.0
        unstable_parameters: list[str] = []

        def evaluate(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return self

    class _FakeRiskPolicy:
        rules = {"overfitting": {}}

        def evaluate(self, metadata, backtest_report, overfitting_report):
            _ = (metadata, backtest_report, overfitting_report)
            return ["backtest_thresholds"], [], []

    class _BreakoutStrategy:
        name = "krw_volume_surge_breakout"
        default_params = {
            "btc_symbol": "KRW-BTC",
            "ema_window": 72,
            "volume_lookback": 24,
            "volume_surge_threshold": 2.5,
            "breakout_window": 20,
            "top_k": 3,
        }

        def generate_signals(self, ohlcv, params=None):
            _ = (ohlcv, params)
            return pd.Series(dtype=float)

        def generate_multi_signals(self, ohlcv_by_symbol, params=None):
            _ = params
            index = next(iter(ohlcv_by_symbol.values())).index
            return {
                "KRW-ETH": pd.Series(1.0, index=index, dtype=float),
                "KRW-SOL": pd.Series(0.0, index=index, dtype=float),
            }

    monkeypatch.setattr("app.domains.evaluation.candidate_evaluator.load_strategy", lambda *args, **kwargs: _BreakoutStrategy())

    evaluator = CandidateEvaluator(
        runner=_FakeRunner(),
        overfitting=_FakeOverfitting(),
        risk_policy=_FakeRiskPolicy(),
        cache_dir=tmp_path / "cache",
    )
    proposal = StrategyProposal(
        strategy_name="krw_volume_surge_breakout",
        strategy_category="volatility_breakout",
        hypothesis="h",
        market_regime="trend",
        implementation_notes="i",
    )
    idx = pd.date_range("2024-01-01", periods=80, freq="h", tz="UTC")
    close = pd.Series(range(80), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    scorecard = evaluator.evaluate_candidate(
        run_id="run-volume-breakout",
        candidate={
            "strategy_name": "krw_volume_surge_breakout",
            "file_path": str(tmp_path / "krw_volume_surge_breakout.py"),
            "parameters": {
                "btc_symbol": "KRW-BTC",
                "ema_window": 72,
                "volume_lookback": 24,
                "volume_surge_threshold": 2.5,
                "breakout_window": 20,
                "top_k": 3,
            },
            "source_type": "new",
            "strategy_category": "volatility_breakout",
        },
        proposal=proposal,
        spec=Spec(run_goal="volume breakout", context="unit test", requirements=[], metadata={"fee_bps": 8.0, "slippage_bps": 8.0}),
        ohlcv_by_symbol={"KRW-BTC": frame, "KRW-ETH": frame, "KRW-SOL": frame},
    )

    assert scorecard.strategy.name == "krw_volume_surge_breakout"
    assert scorecard.metadata.symbols_tested == ["KRW-ETH", "KRW-SOL"]
    assert scorecard.candidate_pass is True


def test_candidate_evaluator_supports_krw_trend_pullback_reaccel_candidate(monkeypatch, tmp_path) -> None:
    class _FakeRunner:
        def run(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return BacktestMetrics(
                trades=16,
                sharpe=1.35,
                max_drawdown=0.06,
                win_rate=0.61,
                cagr=0.14,
                equity_curve_summary={},
                equity_curve=[],
            )

        def evaluate_regimes(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return {
                "sharpe_by_regime": {"trend": 1.0},
                "drawdown_by_regime": {"trend": 0.1},
                "sharpe_regime_std": 0.1,
            }

    class _FakeOverfitting:
        passed = True
        is_metrics = {"sharpe": 1.0}
        oos_metrics = {"sharpe": 0.9}
        walk_forward = []
        sensitivity_max_drift = 0.0
        unstable_parameters: list[str] = []

        def evaluate(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return self

    class _FakeRiskPolicy:
        rules = {"overfitting": {}}

        def evaluate(self, metadata, backtest_report, overfitting_report):
            _ = (metadata, backtest_report, overfitting_report)
            return ["backtest_thresholds"], [], []

    class _TrendPullbackReaccelStrategy:
        name = "krw_trend_pullback_reaccel"
        default_params = {
            "btc_symbol": "KRW-BTC",
            "btc_ema_window": 72,
            "fast_ema_window": 20,
            "slow_ema_window": 72,
            "pullback_window": 6,
            "breakout_window": 3,
            "return_lookback": 12,
            "atr_window": 14,
            "top_k": 3,
        }

        def generate_signals(self, ohlcv, params=None):
            _ = (ohlcv, params)
            return pd.Series(dtype=float)

        def generate_multi_signals(self, ohlcv_by_symbol, params=None):
            _ = params
            index = next(iter(ohlcv_by_symbol.values())).index
            return {
                "KRW-ETH": pd.Series(1.0, index=index, dtype=float),
                "KRW-SOL": pd.Series(0.0, index=index, dtype=float),
            }

    monkeypatch.setattr("app.domains.evaluation.candidate_evaluator.load_strategy", lambda *args, **kwargs: _TrendPullbackReaccelStrategy())

    evaluator = CandidateEvaluator(
        runner=_FakeRunner(),
        overfitting=_FakeOverfitting(),
        risk_policy=_FakeRiskPolicy(),
        cache_dir=tmp_path / "cache",
    )
    proposal = StrategyProposal(
        strategy_name="krw_trend_pullback_reaccel",
        strategy_category="trend_following",
        hypothesis="h",
        market_regime="trend",
        implementation_notes="i",
    )
    idx = pd.date_range("2024-01-01", periods=90, freq="h", tz="UTC")
    close = pd.Series(range(90), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    scorecard = evaluator.evaluate_candidate(
        run_id="run-trend-pullback-reaccel",
        candidate={
            "strategy_name": "krw_trend_pullback_reaccel",
            "file_path": str(tmp_path / "krw_trend_pullback_reaccel.py"),
            "parameters": {
                "btc_symbol": "KRW-BTC",
                "btc_ema_window": 72,
                "fast_ema_window": 20,
                "slow_ema_window": 72,
                "pullback_window": 6,
                "breakout_window": 3,
                "return_lookback": 12,
                "atr_window": 14,
                "top_k": 3,
            },
            "source_type": "new",
            "strategy_category": "trend_following",
        },
        proposal=proposal,
        spec=Spec(run_goal="trend pullback reaccel", context="unit test", requirements=[], metadata={"fee_bps": 8.0, "slippage_bps": 8.0}),
        ohlcv_by_symbol={"KRW-BTC": frame, "KRW-ETH": frame, "KRW-SOL": frame},
    )

    assert scorecard.strategy.name == "krw_trend_pullback_reaccel"
    assert scorecard.metadata.symbols_tested == ["KRW-ETH", "KRW-SOL"]
    assert scorecard.candidate_pass is True


def test_candidate_evaluator_supports_krw_low_vol_breakout_candidate(monkeypatch, tmp_path) -> None:
    class _FakeRunner:
        def run(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return BacktestMetrics(
                trades=18,
                sharpe=1.4,
                max_drawdown=0.05,
                win_rate=0.62,
                cagr=0.16,
                equity_curve_summary={},
                equity_curve=[],
            )

        def evaluate_regimes(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return {
                "sharpe_by_regime": {"trend": 1.0},
                "drawdown_by_regime": {"trend": 0.1},
                "sharpe_regime_std": 0.1,
            }

    class _FakeOverfitting:
        passed = True
        is_metrics = {"sharpe": 1.0}
        oos_metrics = {"sharpe": 0.9}
        walk_forward = []
        sensitivity_max_drift = 0.0
        unstable_parameters: list[str] = []

        def evaluate(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return self

    class _FakeRiskPolicy:
        rules = {"overfitting": {}}

        def evaluate(self, metadata, backtest_report, overfitting_report):
            _ = (metadata, backtest_report, overfitting_report)
            return ["backtest_thresholds"], [], []

    class _LowVolBreakoutStrategy:
        name = "krw_low_vol_breakout"
        default_params = {
            "btc_symbol": "KRW-BTC",
            "btc_ema_window": 72,
            "atr_window": 20,
            "contraction_history_window": 60,
            "breakout_window": 20,
            "volume_window": 20,
            "top_k": 3,
        }

        def generate_signals(self, ohlcv, params=None):
            _ = (ohlcv, params)
            return pd.Series(dtype=float)

        def generate_multi_signals(self, ohlcv_by_symbol, params=None):
            _ = params
            index = next(iter(ohlcv_by_symbol.values())).index
            return {
                "KRW-ETH": pd.Series(1.0, index=index, dtype=float),
                "KRW-SOL": pd.Series(0.0, index=index, dtype=float),
            }

    monkeypatch.setattr("app.domains.evaluation.candidate_evaluator.load_strategy", lambda *args, **kwargs: _LowVolBreakoutStrategy())

    evaluator = CandidateEvaluator(
        runner=_FakeRunner(),
        overfitting=_FakeOverfitting(),
        risk_policy=_FakeRiskPolicy(),
        cache_dir=tmp_path / "cache",
    )
    proposal = StrategyProposal(
        strategy_name="krw_low_vol_breakout",
        strategy_category="volatility_breakout",
        hypothesis="h",
        market_regime="trend",
        implementation_notes="i",
    )
    idx = pd.date_range("2024-01-01", periods=120, freq="h", tz="UTC")
    close = pd.Series(range(120), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    scorecard = evaluator.evaluate_candidate(
        run_id="run-low-vol-breakout",
        candidate={
            "strategy_name": "krw_low_vol_breakout",
            "file_path": str(tmp_path / "krw_low_vol_breakout.py"),
            "parameters": {
                "btc_symbol": "KRW-BTC",
                "btc_ema_window": 72,
                "atr_window": 20,
                "contraction_history_window": 60,
                "breakout_window": 20,
                "volume_window": 20,
                "top_k": 3,
            },
            "source_type": "new",
            "strategy_category": "volatility_breakout",
        },
        proposal=proposal,
        spec=Spec(run_goal="low vol breakout", context="unit test", requirements=[], metadata={"fee_bps": 8.0, "slippage_bps": 8.0}),
        ohlcv_by_symbol={"KRW-BTC": frame, "KRW-ETH": frame, "KRW-SOL": frame},
    )

    assert scorecard.strategy.name == "krw_low_vol_breakout"
    assert scorecard.metadata.symbols_tested == ["KRW-ETH", "KRW-SOL"]
    assert scorecard.candidate_pass is True


def test_candidate_evaluator_supports_krw_btc_swing_trend_candidate(monkeypatch, tmp_path) -> None:
    class _FakeRunner:
        def run_multi_symbol(self, strategy, symbols, ohlcv_by_symbol, params=None, **kwargs):
            _ = (strategy, symbols, ohlcv_by_symbol, params, kwargs)
            return MultiAssetBacktestMetrics(
                symbols=["KRW-BTC"],
                per_symbol={
                    "KRW-BTC": BacktestMetrics(
                        trades=9,
                        sharpe=1.2,
                        max_drawdown=0.12,
                        win_rate=0.56,
                        cagr=0.14,
                        equity_curve_summary={},
                        equity_curve=[1.0, 1.02, 1.05],
                    )
                },
                sharpe_mean=1.2,
                sharpe_std=0.0,
                drawdown_mean=0.12,
                drawdown_worst=0.12,
            )

        def evaluate_regimes(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return {
                "sharpe_by_regime": {"trend": 1.0},
                "drawdown_by_regime": {"trend": 0.1},
                "sharpe_regime_std": 0.1,
            }

    class _FakeOverfitting:
        passed = True
        is_metrics = {"sharpe": 1.0}
        oos_metrics = {"sharpe": 0.9}
        walk_forward = []
        sensitivity_max_drift = 0.0
        unstable_parameters: list[str] = []

        def evaluate(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return self

    class _FakeRiskPolicy:
        rules = {"overfitting": {}}

        def evaluate(self, metadata, backtest_report, overfitting_report):
            _ = (metadata, backtest_report, overfitting_report)
            return ["backtest_thresholds"], [], []

    class _SwingTrendStrategy:
        name = "krw_btc_swing_trend"
        default_params = {"symbol": "KRW-BTC", "fast_ema_window": 20, "slow_ema_window": 72}

        def generate_signals(self, ohlcv, params=None):
            _ = (ohlcv, params)
            return pd.Series(1.0, index=ohlcv.index, dtype=float)

    monkeypatch.setattr("app.domains.evaluation.candidate_evaluator.load_strategy", lambda *args, **kwargs: _SwingTrendStrategy())

    evaluator = CandidateEvaluator(
        runner=_FakeRunner(),
        overfitting=_FakeOverfitting(),
        risk_policy=_FakeRiskPolicy(),
        cache_dir=tmp_path / "cache",
    )
    proposal = StrategyProposal(
        strategy_name="krw_btc_swing_trend",
        strategy_category="trend_following",
        hypothesis="h",
        market_regime="trend",
        implementation_notes="i",
    )
    idx = pd.date_range("2024-01-01", periods=120, freq="4h", tz="UTC")
    close = pd.Series(range(120), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    scorecard = evaluator.evaluate_candidate(
        run_id="run-krw-btc-swing-trend",
        candidate={
            "strategy_name": "krw_btc_swing_trend",
            "file_path": str(tmp_path / "krw_btc_swing_trend.py"),
            "parameters": {"symbol": "KRW-BTC", "fast_ema_window": 20, "slow_ema_window": 72},
            "source_type": "new",
            "strategy_category": "trend_following",
        },
        proposal=proposal,
        spec=Spec(
            run_goal="krw btc swing trend",
            context="unit test",
            requirements=[],
            metadata={"symbols": ["KRW-BTC"], "ohlcv_interval": "4h", "fee_bps": 8.0, "slippage_bps": 8.0},
        ),
        ohlcv_by_symbol={"KRW-BTC": frame},
    )

    assert scorecard.strategy.name == "krw_btc_swing_trend"
    assert scorecard.metadata.symbols_tested == ["KRW-BTC"]
    assert scorecard.candidate_pass is True



def test_candidate_evaluator_supports_krw_btc_mean_reversion_candidate(monkeypatch, tmp_path) -> None:
    class _FakeRunner:
        def run_multi_symbol(self, strategy, symbols, ohlcv_by_symbol, params=None, **kwargs):
            _ = (strategy, symbols, ohlcv_by_symbol, params, kwargs)
            return MultiAssetBacktestMetrics(
                symbols=["KRW-BTC"],
                per_symbol={
                    "KRW-BTC": BacktestMetrics(
                        trades=11,
                        sharpe=0.8,
                        max_drawdown=0.09,
                        win_rate=0.54,
                        cagr=0.06,
                        equity_curve_summary={},
                        equity_curve=[1.0, 1.01, 1.03],
                    )
                },
                sharpe_mean=0.8,
                sharpe_std=0.0,
                drawdown_mean=0.09,
                drawdown_worst=0.09,
            )

        def evaluate_regimes(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return {
                "sharpe_by_regime": {"range": 0.8},
                "drawdown_by_regime": {"range": 0.09},
                "sharpe_regime_std": 0.0,
            }

    class _FakeOverfitting:
        passed = True
        is_metrics = {"sharpe": 0.8}
        oos_metrics = {"sharpe": 0.7}
        walk_forward = []
        sensitivity_max_drift = 0.0
        unstable_parameters: list[str] = []

        def evaluate(self, strategy, ohlcv, params=None, **kwargs):
            _ = (strategy, ohlcv, params, kwargs)
            return self

    class _FakeRiskPolicy:
        rules = {"overfitting": {}}

        def evaluate(self, metadata, backtest_report, overfitting_report):
            _ = (metadata, backtest_report, overfitting_report)
            return ["backtest_thresholds"], [], []

    class _MeanReversionStrategy:
        name = "krw_btc_mean_reversion"
        default_params = {
            "symbol": "KRW-BTC",
            "bollinger_window": 20,
            "bollinger_std_multiplier": 2.0,
            "rsi_window": 14,
            "rsi_threshold": 30.0,
            "exit_sma_window": 20,
        }

        def generate_signals(self, ohlcv, params=None):
            _ = (ohlcv, params)
            return pd.Series(1.0, index=ohlcv.index, dtype=float)

    monkeypatch.setattr("app.domains.evaluation.candidate_evaluator.load_strategy", lambda *args, **kwargs: _MeanReversionStrategy())

    evaluator = CandidateEvaluator(
        runner=_FakeRunner(),
        overfitting=_FakeOverfitting(),
        risk_policy=_FakeRiskPolicy(),
        cache_dir=tmp_path / "cache",
    )
    proposal = StrategyProposal(
        strategy_name="krw_btc_mean_reversion",
        strategy_category="mean_reversion",
        hypothesis="h",
        market_regime="range",
        implementation_notes="i",
    )
    idx = pd.date_range("2024-01-01", periods=120, freq="h", tz="UTC")
    close = pd.Series(range(120), index=idx, dtype=float) + 100.0
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    scorecard = evaluator.evaluate_candidate(
        run_id="run-krw-btc-mean-reversion",
        candidate={
            "strategy_name": "krw_btc_mean_reversion",
            "file_path": str(tmp_path / "krw_btc_mean_reversion.py"),
            "parameters": {
                "symbol": "KRW-BTC",
                "bollinger_window": 20,
                "bollinger_std_multiplier": 2.0,
                "rsi_window": 14,
                "rsi_threshold": 30.0,
                "exit_sma_window": 20,
            },
            "source_type": "new",
            "strategy_category": "mean_reversion",
        },
        proposal=proposal,
        spec=Spec(
            run_goal="krw btc mean reversion",
            context="unit test",
            requirements=[],
            metadata={"symbols": ["KRW-BTC"], "ohlcv_interval": "1h", "fee_bps": 8.0, "slippage_bps": 8.0},
        ),
        ohlcv_by_symbol={"KRW-BTC": frame},
    )

    assert scorecard.strategy.name == "krw_btc_mean_reversion"
    assert scorecard.metadata.symbols_tested == ["KRW-BTC"]
    assert scorecard.candidate_pass is True
