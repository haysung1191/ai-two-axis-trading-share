from __future__ import annotations

from pathlib import Path

from split_models.pipeline import run_pipeline


def test_split_models_pipeline_smoke(tmp_path: Path) -> None:
    outputs = run_pipeline(output_dir=tmp_path)

    assert not outputs["flow_regime_snapshot"].empty
    assert "ScopeType" in outputs["flow_regime_snapshot"].columns
    assert "CandidateState" in outputs["momentum_trade_candidates"].columns
    assert "WatchGrade" in outputs["tenbagger_watchlist"].columns
    assert "KRPriceSource" in outputs["momentum_trade_candidates"].columns
    assert not outputs["data_readiness"].empty
    assert "PriceMissingCount" in outputs["data_readiness"].columns

    expected = [
        "flow_regime_snapshot.csv",
        "momentum_trade_candidates.csv",
        "tenbagger_watchlist.csv",
        "portfolio_trading_book.csv",
        "portfolio_tenbagger_book.csv",
        "split_models_summary.csv",
        "split_models_summary.json",
        "split_models_data_readiness.csv",
        "split_models_data_readiness.json",
    ]
    for name in expected:
        assert (tmp_path / name).exists()

    summary = (tmp_path / "split_models_summary.csv").read_text(encoding="utf-8-sig")
    assert "KRPriceRoot" in summary
    assert "KRFlowRoot" in summary
    readiness = (tmp_path / "split_models_data_readiness.csv").read_text(encoding="utf-8-sig")
    assert "KR_STOCK" in readiness
