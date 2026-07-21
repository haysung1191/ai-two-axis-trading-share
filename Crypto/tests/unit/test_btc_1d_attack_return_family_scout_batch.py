from __future__ import annotations

import json
from pathlib import Path

import app.domains.experiments.btc_1d_attack_return_family_scout_batch as mod
from app.domains.experiments.btc_1d_attack_return_family_scout_batch import (
    Btc1dAttackReturnFamilyScoutBatchService,
    Btc1dAttackReturnFamilyScoutConfig,
)


def _write_common_rules(path: Path) -> None:
    payload = {
        "leaders": [
            {
                "family": "volatility_spike_reversal_continuation",
                "strategy_name": "btc_1d_volatility_spike_reversal_continuation_v4",
                "variant_label": "slower_trend",
                "parameters": {"trend_ema_window": 96, "max_hold_bars": 34},
            },
            {
                "family": "post_spike_consolidation_breakout",
                "strategy_name": "btc_1d_post_spike_consolidation_breakout_v4",
                "variant_label": "slower_trend",
                "parameters": {"trend_ema_window": 96, "max_hold_bars": 36},
            },
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_attack_return_family_scout_runs_selected_family(tmp_path, monkeypatch) -> None:
    common_rules = tmp_path / "common_rules.json"
    _write_common_rules(common_rules)
    monkeypatch.setattr(mod, "COMMON_RULES_LATEST", common_rules)

    class _StubDiagnosticService:
        def run_diagnostic(self, config, run_id=None):
            is_cost20 = config.fee_bps == 20.0
            return {
                "analysis_result_json": f"{config.candidate_label}.json",
                "base_metrics": {
                    "cagr": 0.38 if not is_cost20 else 0.35,
                    "sharpe": 1.9 if not is_cost20 else 1.8,
                    "max_drawdown": 0.09,
                },
                "overfitting": {
                    "sensitivity_max_drift": 0.12,
                    "walk_forward": [
                        {"window": 1, "metrics": {"cagr": 0.05, "sharpe": 0.8, "trades": 3}},
                        {"window": 2, "metrics": {"cagr": 0.04, "sharpe": 0.7, "trades": 0}},
                    ],
                },
            }

    service = Btc1dAttackReturnFamilyScoutBatchService(
        diagnostic_service=_StubDiagnosticService(),
        analysis_results_dir=tmp_path,
    )
    result = service.run_batch(
        Btc1dAttackReturnFamilyScoutConfig(periods=1200),
        run_id="return-family-scout-test",
        families=["volatility_spike_reversal_continuation"],
    )

    assert len(result["results"]) == 1
    assert result["best_variant"]["family"] == "volatility_spike_reversal_continuation"
    assert result["analysis_result_json"].endswith(".json")
    assert "base_cagr_gap_to_main" in result["best_variant"]
    assert result["return_family_scout_verdict"]["completed_family_count"] == 1
