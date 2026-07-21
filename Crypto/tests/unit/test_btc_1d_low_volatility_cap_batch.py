from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_low_volatility_cap_batch import (
    Btc1dLowVolatilityCapBatchService,
    Btc1dLowVolatilityCapConfig,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_low_volatility_cap_batch import parse_args
from strategies.btc_1d_ema_trend_atr_exit import Strategy as Btc1dStrategy


def test_btc_1d_low_volatility_cap_cli_defaults() -> None:
    config = parse_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.lookback_periods == (1400, 1800, 2200, 2600)


def test_btc_1d_low_volatility_cap_reduces_position_on_quiet_series() -> None:
    idx = pd.date_range("2024-01-01", periods=220, freq="1d", tz="UTC")
    close = pd.Series([100.0 + i * 0.08 + ((i % 5) * 0.005) for i in range(len(idx))], index=idx, dtype=float)
    frame = pd.DataFrame({"open": close, "high": close + 0.1, "low": close - 0.1, "close": close, "volume": 1000.0}, index=idx)
    signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "volatility_target": 0.2,
            "min_position_size": 0.35,
            "low_volatility_cap_threshold": 0.4,
            "low_volatility_position_cap": 0.5,
        },
    )
    assert ((signal > 0.0) & (signal <= 0.5)).any()


def test_btc_1d_entry_extension_filter_blocks_overextended_entry() -> None:
    idx = pd.date_range("2024-01-01", periods=120, freq="1d", tz="UTC")
    close_values = [100.0 for _ in range(119)] + [140.0]
    close = pd.Series(close_values, index=idx, dtype=float)
    frame = pd.DataFrame(
        {"open": close, "high": close + 0.2, "low": close - 0.2, "close": close, "volume": 1000.0},
        index=idx,
    )

    unfiltered_signal = Btc1dStrategy().generate_signals(frame, {})
    filtered_signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "max_entry_extension_from_ema_fast": 0.03,
        },
    )

    assert float(unfiltered_signal.iloc[-1]) > 0.0
    assert float(filtered_signal.iloc[-1]) == 0.0


def test_btc_1d_low_vol_cap_can_block_new_entries() -> None:
    idx = pd.date_range("2024-01-01", periods=220, freq="1d", tz="UTC")
    close = pd.Series([100.0 + i * 0.08 + ((i % 5) * 0.005) for i in range(len(idx))], index=idx, dtype=float)
    frame = pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close, "volume": 1000.0},
        index=idx,
    )

    capped_signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "volatility_target": 0.2,
            "min_position_size": 0.35,
            "low_volatility_cap_threshold": 0.4,
            "low_volatility_position_cap": 0.35,
        },
    )
    blocked_signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "volatility_target": 0.2,
            "min_position_size": 0.35,
            "low_volatility_cap_threshold": 0.4,
            "low_volatility_position_cap": 0.35,
            "block_new_entries_when_low_vol_cap": 1.0,
        },
    )

    assert ((capped_signal > 0.0) & (capped_signal <= 0.35)).any()
    assert float(blocked_signal.max()) == 0.0


def test_btc_1d_return_10d_gate_blocks_chased_entry() -> None:
    idx = pd.date_range("2024-01-01", periods=125, freq="1d", tz="UTC")
    close_values = [100.0 + (i * 0.08) for i in range(80)] + [106.0 - (i * 0.4) for i in range(15)] + [103.0 + (i * 0.8) for i in range(30)]
    close = pd.Series(close_values, index=idx, dtype=float)
    frame = pd.DataFrame(
        {"open": close, "high": close + 0.2, "low": close - 0.2, "close": close, "volume": 1000.0},
        index=idx,
    )

    unfiltered_signal = Btc1dStrategy().generate_signals(frame, {})
    filtered_signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "max_entry_return_10d": 0.04,
        },
    )

    unfiltered_entry = (unfiltered_signal > 0.0) & (unfiltered_signal.shift(1).fillna(0.0) == 0.0)
    filtered_entry = (filtered_signal > 0.0) & (filtered_signal.shift(1).fillna(0.0) == 0.0)

    assert unfiltered_entry.any()
    assert bool((unfiltered_entry & ~filtered_entry).any())


def test_btc_1d_low_volatility_cap_batch_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dLowVolatilityCapBatchService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )
    result = service.run_batch(
        Btc1dLowVolatilityCapConfig(
            lookback_periods=(240, 320),
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-low-vol-cap-test",
    )
    run_dir = tmp_path / "artifacts" / "btc-1d-low-vol-cap-test"
    assert (run_dir / "btc_1d_low_volatility_cap_batch.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert len(result["results"]) == 3
