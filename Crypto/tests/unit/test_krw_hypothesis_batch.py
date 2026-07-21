from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.krw_hypothesis_batch import KrwHypothesisBatchConfig, KrwHypothesisBatchService
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_krw_hypothesis_batch import parse_args
from strategies.krw_btc_regime_relative_rotation_4h import Strategy as RegimeRelativeRotationStrategy


def test_krw_hypothesis_batch_cli_defaults() -> None:
    config = parse_args([])

    assert config.interval == "4h"
    assert config.periods == 360
    assert config.max_symbols == 2


def test_krw_btc_regime_relative_rotation_generates_multi_signals() -> None:
    idx = pd.date_range("2024-01-01", periods=100, freq="4h", tz="UTC")
    btc_close = pd.Series([100.0 + (i * 0.5) for i in range(len(idx))], index=idx, dtype=float)

    def _frame(close: pd.Series) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "open": close,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1000.0,
            },
            index=idx,
        )

    eth_close = pd.Series([50.0 + (i * 0.8) for i in range(len(idx))], index=idx, dtype=float)
    xrp_close = pd.Series([30.0 + (i * 0.25) for i in range(len(idx))], index=idx, dtype=float)

    strategy = RegimeRelativeRotationStrategy()
    signal_map = strategy.generate_multi_signals(
        {
            "KRW-BTC": _frame(btc_close),
            "KRW-ETH": _frame(eth_close),
            "KRW-XRP": _frame(xrp_close),
        }
    )

    assert set(signal_map.keys()) == {"KRW-ETH", "KRW-XRP"}
    assert signal_map["KRW-ETH"].sum() > 0


def test_build_universe_prefers_core_symbols_and_filters_denylist(monkeypatch) -> None:
    service = KrwHypothesisBatchService()

    class _FakeTicker:
        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

    class _FakeClient:
        def list_krw_tickers_by_quote_volume(self, min_quote_krw_24h: float, max_symbols: int):
            _ = (min_quote_krw_24h, max_symbols)
            return [_FakeTicker("ETH"), _FakeTicker("USDT"), _FakeTicker("SOL"), _FakeTicker("DOGE"), _FakeTicker("XRP")]

        def close(self) -> None:
            return None

    monkeypatch.setattr("app.domains.experiments.krw_hypothesis_batch.BithumbPublicClient", lambda: _FakeClient())

    symbols = service.build_universe(KrwHypothesisBatchConfig(max_symbols=2, use_shadow_allowlist=False))

    assert symbols == ["KRW-BTC", "KRW-ETH", "KRW-XRP"]


def test_stage1_filter_and_artifacts(tmp_path, monkeypatch) -> None:
    artifact_store = ArtifactStore(root_dir=tmp_path / "artifacts")
    service = KrwHypothesisBatchService(
        artifact_store=artifact_store,
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )
    config = KrwHypothesisBatchConfig(max_symbols=2, use_shadow_allowlist=False)

    idx = pd.date_range("2024-01-01", periods=140, freq="4h", tz="UTC")

    def _frame(base: float, slope: float) -> pd.DataFrame:
        close = pd.Series([base + (i * slope) for i in range(len(idx))], index=idx, dtype=float)
        return pd.DataFrame(
            {
                "open": close,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1000.0,
            },
            index=idx,
        )

    monkeypatch.setattr(service, "build_universe", lambda cfg: ["KRW-BTC", "KRW-ETH", "KRW-XRP"])
    monkeypatch.setattr(
        service,
        "_load_filtered_frames",
        lambda symbols, cfg: (
            {
                "KRW-BTC": _frame(100.0, 0.35),
                "KRW-ETH": _frame(50.0, 0.6),
                "KRW-XRP": _frame(40.0, 0.2),
            },
            [],
        ),
    )

    result = service.run_batch(config, run_id="krw-stage-screen")

    assert result["run_id"] == "krw-stage-screen"
    assert len(result["results"]) == 2
    assert "stage1_survivors" in result
    assert Path(result["analysis_result_json"]).exists()
