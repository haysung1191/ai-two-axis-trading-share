from __future__ import annotations

import json

import scripts.run_btc_1d_attack_primary_queue_step as mod
from scripts.run_btc_1d_attack_primary_queue_step import build_primary_step_report


def _anchor_report() -> dict:
    return {
        "current_candidate": {
            "label": "tighter_stop_mid_hold",
            "strategy_name": "btc_1d_trend_dip_reversal_breakout_v4",
            "cagr": 0.39088346,
            "max_drawdown": 0.24839003,
            "sharpe": 1.3211,
        }
    }


def test_primary_queue_step_stays_in_mutation_loop_when_compression_is_not_better() -> None:
    batch_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "analysis_result_csv": "analysis_results/demo.csv",
        "results": [
            {
                "variant_label": "tighter_stop_shorter_hold",
                "strategy_name": "btc_1d_trend_dip_reversal_breakout_exit_v4",
                "cagr": 0.38738927,
                "max_drawdown": 0.26438192,
                "sharpe": 1.33880175,
                "completed_trades": 33,
                "failed_gates": ["backtest_max_drawdown"],
            }
        ],
    }

    report = build_primary_step_report(
        step="exit_compression_batch",
        batch_result=batch_result,
        anchor_report=_anchor_report(),
    )

    assert report["comparison"]["improves_drawdown"] is False
    assert report["step_verdict"]["status"] == "stay_in_primary_mutation_loop"
    assert report["step_verdict"]["next_step"] == "exit_symmetry_batch"


def test_primary_queue_step_advances_when_drawdown_improves_and_profile_holds() -> None:
    batch_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "analysis_result_csv": "analysis_results/demo.csv",
        "results": [
            {
                "variant_label": "improved_exit_shape",
                "strategy_name": "btc_1d_trend_dip_reversal_breakout_exit_v5",
                "cagr": 0.3790,
                "max_drawdown": 0.2360,
                "sharpe": 1.29,
                "completed_trades": 34,
                "failed_gates": [],
            }
        ],
    }

    report = build_primary_step_report(
        step="exit_compression_batch",
        batch_result=batch_result,
        anchor_report=_anchor_report(),
    )

    assert report["comparison"]["improves_drawdown"] is True
    assert report["comparison"]["keeps_attack_profile"] is True
    assert report["step_verdict"]["status"] == "advance_to_candidate_validation"
    assert report["step_verdict"]["next_step"] == "candidate_validation"


def test_primary_queue_step_holds_anchor_after_symmetry_fail() -> None:
    batch_result = {
        "run_id": "demo-run",
        "analysis_result_json": "analysis_results/demo.json",
        "analysis_result_csv": "analysis_results/demo.csv",
        "results": [
            {
                "variant_label": "tighter_stop_mid_hold",
                "strategy_name": "btc_1d_trend_dip_reversal_breakout_symmetry_v4",
                "cagr": 0.39088346,
                "max_drawdown": 0.24839003,
                "sharpe": 1.32107053,
                "completed_trades": 32,
                "failed_gates": ["backtest_max_drawdown"],
            }
        ],
    }

    report = build_primary_step_report(
        step="exit_symmetry_batch",
        batch_result=batch_result,
        anchor_report=_anchor_report(),
    )

    assert report["comparison"]["improves_drawdown"] is False
    assert report["comparison"]["keeps_attack_profile"] is True
    assert report["step_verdict"]["status"] == "stay_in_primary_mutation_loop"
    assert report["step_verdict"]["next_step"] == "hold_primary_anchor"


def test_run_exit_compression_step_applies_attack_seed(tmp_path, monkeypatch) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "btc_1d_attack_common_rules_latest.json").write_text(
        json.dumps(
            {
                "recommended_attack_rule_seed": {
                    "trend_ema_window": 88,
                    "min_volume_ratio": 1.09,
                    "stop_ema_window": 18,
                    "max_hold_bars": 30,
                }
            }
        ),
        encoding="utf-8",
    )

    class _StubService:
        captured_variants = None

        def __init__(self, analysis_results_dir):
            self.analysis_results_dir = analysis_results_dir

        def run_batch(self, config, variants=None):
            _StubService.captured_variants = variants
            return {
                "run_id": "demo-run",
                "analysis_result_json": "analysis_results/demo.json",
                "analysis_result_csv": "analysis_results/demo.csv",
                "results": [
                    {
                        "variant_label": "current_reference_seeded",
                        "strategy_name": "btc_1d_trend_dip_reversal_breakout_v1_exit_compression",
                        "cagr": 0.38738927,
                        "max_drawdown": 0.26438192,
                        "sharpe": 1.33880175,
                        "completed_trades": 33,
                        "failed_gates": ["backtest_max_drawdown"],
                    }
                ],
            }

    monkeypatch.setattr(mod, "Btc1dTrendDipReversalBreakoutExitCompressionBatchService", _StubService)
    monkeypatch.setattr(
        mod,
        "build_trend_dip_reopen_screen",
        lambda: _anchor_report(),
    )

    args = mod.build_parser().parse_args(
        [
            "--analysis-dir",
            str(analysis_dir),
            "--apply-attack-seed",
        ]
    )
    report = mod.run_exit_compression_step(args)

    assert report["seed_application"]["attack_seed_applied"] is True
    assert report["seed_application"]["attack_seed_parameters"]["trend_ema_window"] == 88
    assert _StubService.captured_variants[0]["label"] == "current_reference_seeded"
    assert _StubService.captured_variants[0]["parameters"]["trend_ema_window"] == 88
    assert _StubService.captured_variants[0]["parameters"]["min_volume_ratio"] == 1.09
    assert _StubService.captured_variants[0]["parameters"]["max_hold_bars"] == 32
