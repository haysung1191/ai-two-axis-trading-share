from __future__ import annotations

from app.domains.experiments.btc_1d_practical_benchmark_batch import (
    Btc1dPracticalBenchmarkBatchService,
    Btc1dPracticalBenchmarkConfig,
)
from scripts.run_btc_1d_practical_benchmark_batch import parse_args


def test_practical_benchmark_batch_runs_and_writes_outputs(tmp_path) -> None:
    service = Btc1dPracticalBenchmarkBatchService(
        analysis_results_dir=tmp_path,
        artifacts_root=tmp_path / "artifacts",
    )
    result = service.run_batch(
        Btc1dPracticalBenchmarkConfig(
            periods=240,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-practical-benchmark-test",
    )
    assert len(result["results"]) == 4
    labels = {row["label"] for row in result["results"]}
    assert labels == {"practical_leader", "buy_and_hold", "simple_ma_trend", "simple_breakout"}
    assert (tmp_path / "artifacts" / "btc-1d-practical-benchmark-test" / "btc_1d_practical_benchmark_batch.json").exists()
    assert list(tmp_path.glob("btc_1d_practical_benchmark_batch_*.json"))
    assert list(tmp_path.glob("btc_1d_practical_benchmark_batch_*.csv"))
    assert list(tmp_path.glob("btc_1d_practical_benchmark_batch_*.md"))


def test_run_btc_1d_practical_benchmark_batch_defaults() -> None:
    config = parse_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.fee_bps == 8.0
    assert config.slippage_bps == 8.0
