from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_paper_validation import BtcPaperValidationConfig, BtcPaperValidationService
from app.domains.governance.artifact_store import ArtifactStore
from scripts.validate_btc_4h_strategy import parse_args
from scripts.validate_btc_1d_core_strategy import parse_args as parse_btc_1d_args
from scripts.validate_btc_1d_vol_scaled_candidate import parse_args as parse_btc_1d_vol_scaled_args


def test_btc_paper_validation_cli_uses_btcusdt_4h_defaults() -> None:
    config = parse_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "4h"
    assert config.periods == 4000
    assert config.ema_fast_window == 20
    assert config.ema_slow_window == 72
    assert config.fast_break_confirmation_bars == 2


def test_btc_paper_validation_service_writes_expected_artifacts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "btc_4h_trend_regime_persistence_strength_filter_mvp_eval_20260411T065301Z.json").write_text(
        json.dumps(
            {
                "final_decision": "carry_forward",
                "aggregate_metrics": {"subset_event_window_sharpe": 0.18},
            }
        ),
        encoding="utf-8",
    )

    service = BtcPaperValidationService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=analysis_dir,
    )

    result = service.run_validation(
        BtcPaperValidationConfig(allow_synthetic_ohlcv_fallback=True, periods=120),
        run_id="btc-paper-test",
        generated_at=datetime(2026, 4, 11, 7, 0, tzinfo=UTC),
    )

    run_dir = tmp_path / "artifacts" / "btc-paper-test"
    assert (run_dir / "backtest_report.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert (run_dir / "decision_record.json").exists()
    assert (run_dir / "decision_summary.md").exists()
    assert (run_dir / "backtest_reports.json").exists()
    assert (run_dir / "btc_paper_validation.json").exists()
    assert result["completed_trades"] >= 0
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_csv"]).exists()


def test_btc_1d_core_validation_cli_defaults() -> None:
    config = parse_btc_1d_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_ema_trend_atr_exit"
    assert config.atr_window == 14
    assert config.time_stop_bars == 90


def test_btc_1d_vol_scaled_validation_cli_defaults() -> None:
    config = parse_btc_1d_vol_scaled_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.strategy_name == "btc_1d_ema_trend_atr_exit"
    assert config.min_sharpe == 1.0
    assert config.max_drawdown == 0.2
    assert config.extra_parameters["volatility_target"] == 0.2
    assert config.extra_parameters["min_position_size"] == 0.35
