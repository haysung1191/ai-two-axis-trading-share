from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts.validate_btc_1d_trend_dip_reversal_breakout_tsmh_candidate import (
    build_validation_configs,
    load_latest_survivors,
)


def test_load_latest_survivors_filters_keep_rows(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "btc_1d_trend_dip_reversal_breakout_exit_compression_batch_20260419T140432Z.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "strategy_name": "btc_1d_trend_dip_reversal_breakout_v3_exit_compression",
                        "variant_label": "volume_lookback_16_seeded",
                        "decision": "KEEP",
                        "parameters": {"volume_lookback": 16},
                    },
                    {
                        "strategy_name": "btc_1d_trend_dip_reversal_breakout_v2_exit_compression",
                        "variant_label": "volume_ratio_106_seeded",
                        "decision": "DROP",
                        "parameters": {"volume_lookback": 20},
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    survivors = load_latest_survivors(analysis_dir)

    assert len(survivors) == 1
    assert survivors[0]["variant_label"] == "volume_lookback_16_seeded"


def test_build_validation_configs_uses_latest_keep_survivors(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "btc_1d_trend_dip_reversal_breakout_exit_compression_batch_20260419T140432Z.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "strategy_name": "btc_1d_trend_dip_reversal_breakout_v3_exit_compression",
                        "variant_label": "volume_lookback_16_seeded",
                        "decision": "KEEP",
                        "parameters": {
                            "trend_ema_window": 96,
                            "volume_lookback": 16,
                            "min_volume_ratio": 1.08,
                        },
                    },
                    {
                        "strategy_name": "btc_1d_trend_dip_reversal_breakout_v8_exit_compression",
                        "variant_label": "structure_stack_seeded",
                        "decision": "KEEP",
                        "parameters": {
                            "trend_ema_window": 96,
                            "swing_lookback": 26,
                            "pullback_window": 5,
                            "volume_lookback": 16,
                            "min_volume_ratio": 1.08,
                        },
                    },
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    args = Namespace(
        analysis_dir=analysis_dir,
        symbol="BTCUSDT",
        interval="1d",
        periods=2200,
        fee_bps=8.0,
        slippage_bps=8.0,
        allow_synthetic_ohlcv_fallback=True,
    )

    configs = build_validation_configs(args)

    assert [config.strategy_name for config in configs] == [
        "btc_1d_trend_dip_reversal_breakout_v3_exit_compression",
        "btc_1d_trend_dip_reversal_breakout_v8_exit_compression",
    ]
    assert configs[0].artifact_label == "volume_lookback_16_seeded"
    assert configs[0].min_cagr == 0.2
    assert configs[0].max_drawdown == 0.22
    assert configs[1].extra_parameters["swing_lookback"] == 26
