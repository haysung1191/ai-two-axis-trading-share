from __future__ import annotations

import json

import scripts.compare_btc_1d_trend_dip_candidate_validation_review as mod


def test_trend_dip_candidate_validation_review_routes_to_exit_symmetry_when_all_fail(tmp_path, monkeypatch) -> None:
    (tmp_path / "btc_1d_trend_dip_reversal_breakout_exit_compression_batch_20260421T000000Z.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "strategy_name": "btc_1d_trend_dip_reversal_breakout_v3_exit_compression",
                        "variant_label": "volume_lookback_16_seeded",
                        "decision": "KEEP",
                    },
                    {
                        "strategy_name": "btc_1d_trend_dip_reversal_breakout_v6_exit_compression",
                        "variant_label": "pullback_window_7_seeded",
                        "decision": "KEEP",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    for label in ("volume_lookback_16_seeded", "pullback_window_7_seeded"):
        (tmp_path / f"btc_1d_trend_dip_reversal_breakout_vX_{label}_paper_validation_20260421T000000Z.json").write_text(
            json.dumps(
                {
                    "decision_record": {
                        "decision": "FAIL",
                        "failed_gates": ["backtest_max_drawdown"],
                        "key_metrics": {
                            "cagr": 0.42,
                            "max_drawdown": 0.24,
                            "sharpe": 1.34,
                        },
                    }
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(mod, "ANALYSIS_DIR", tmp_path)

    report = mod.build_report()

    assert report["validation_reference"]["survivor_count"] == 2
    assert report["validation_review_verdict"]["has_passing_candidate"] is False
    assert report["validation_review_verdict"]["all_reviewed_candidates_failed"] is True
    assert report["validation_review_verdict"]["next_step_now"] == "run_exit_symmetry_batch"

