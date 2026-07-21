from __future__ import annotations

from app.domains.experiments.btc_1d_post_spike_bridge_backup_dual_validation import (
    Btc1dPostSpikeBridgeBackupDualValidationService,
)


def test_bridge_backup_dual_validation_runs(tmp_path) -> None:
    class _StubDiagnosticService:
        def __init__(self, output_dir):
            self._output_dir = output_dir
            self.calls = []

        def run_diagnostic(self, config, *, run_id=None):
            self.calls.append((config.fee_bps, config.slippage_bps, config.candidate_label))
            analysis_path = self._output_dir / f"{config.candidate_label.replace(':', '_')}.json"
            analysis_path.write_text("{}", encoding="utf-8")
            return {
                "base_metrics": {
                    "cagr": 0.35 if config.fee_bps == 8.0 else 0.346,
                    "sharpe": 1.82,
                    "max_drawdown": 0.095,
                },
                "overfitting": {
                    "sensitivity_max_drift": 0.13,
                    "walk_forward": [
                        {"window": 2, "metrics": {"trades": 0, "sharpe": 0.0, "cagr": 0.0}},
                    ],
                },
                "analysis_result_json": str(analysis_path),
            }

    stub = _StubDiagnosticService(tmp_path)
    service = Btc1dPostSpikeBridgeBackupDualValidationService(
        analysis_results_dir=tmp_path,
        diagnostic_service=stub,
    )
    result = service.run_validation(run_id="btc-1d-post-spike-bridge-backup-dual-validation-test")

    assert len(stub.calls) == 2
    assert result["analysis_result_json"].endswith(".json")
    assert result["report"]["base_validation"]["base_cagr"] == 0.35
    assert result["report"]["cost20_validation"]["cost20_cagr"] == 0.346
    assert result["report"]["base_validation"]["idle_windows"] == [2]
