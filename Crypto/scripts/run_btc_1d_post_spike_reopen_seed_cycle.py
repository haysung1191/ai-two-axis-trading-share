from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_walk_forward_diagnostic import (
    Btc1dWalkForwardDiagnosticConfig,
    Btc1dWalkForwardDiagnosticService,
)
from app.domains.experiments.btc_paper_validation import (
    BtcPaperValidationConfig,
    BtcPaperValidationService,
)
from scripts.post_spike_reopen_seeds import (
    BACKUP_REOPEN_SEED,
    PREFERRED_REOPEN_SEED,
    SEED_DEFINITIONS,
)


ANALYSIS_DIR = Path("analysis_results")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTC 1d post-spike reopen seed validation cycle.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def _safe_token(value: str) -> str:
    return (
        value.replace("::", "__")
        .replace(":", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )


def _run_seed(
    *,
    seed_label: str,
    periods: int,
    allow_synthetic_ohlcv_fallback: bool,
    analysis_dir: Path,
) -> dict:
    seed = SEED_DEFINITIONS[seed_label]
    safe_seed_label = _safe_token(seed_label)
    validation_service = BtcPaperValidationService(analysis_results_dir=analysis_dir)
    walk_service = Btc1dWalkForwardDiagnosticService(analysis_results_dir=analysis_dir)

    validation = validation_service.run_validation(
        BtcPaperValidationConfig(
            symbol="BTCUSDT",
            interval="1d",
            periods=periods,
            strategy_name=str(seed["strategy_name"]),
            strategy_category="trend_following",
            hypothesis=str(seed["hypothesis"]),
            expected_max_drawdown=0.20,
            min_sharpe=1.0,
            max_drawdown=0.20,
            min_win_rate=0.45,
            min_cagr=0.20,
            fee_bps=8.0,
            slippage_bps=8.0,
            allow_synthetic_ohlcv_fallback=allow_synthetic_ohlcv_fallback,
            artifact_label=str(seed["artifact_label"]),
            extra_parameters=dict(seed["parameters"]),
        ),
        run_id=f"btc-1d-post-spike-reopen-seed-validation-{safe_seed_label}-{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )
    walk = walk_service.run_diagnostic(
        Btc1dWalkForwardDiagnosticConfig(
            symbol="BTCUSDT",
            interval="1d",
            periods=periods,
            strategy_name=str(seed["strategy_name"]),
            walk_forward_windows=5,
            allow_synthetic_ohlcv_fallback=allow_synthetic_ohlcv_fallback,
            candidate_label=str(seed["candidate_label"]),
            extra_parameters=dict(seed["parameters"]),
        ),
        run_id=f"btc-1d-post-spike-reopen-seed-walk-{safe_seed_label}-{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )

    validation_metrics = dict(validation["decision_record"]["key_metrics"])
    overfitting = dict(walk["overfitting"])
    windows = list(overfitting.get("walk_forward", []) or [])
    negative_windows = [
        int(window.get("window", 0))
        for window in windows
        if float((window.get("metrics", {}) or {}).get("sharpe", 0.0)) < 0.0
        or float((window.get("metrics", {}) or {}).get("cagr", 0.0)) < 0.0
    ]

    return {
        "seed_label": seed_label,
        "candidate_label": str(seed["candidate_label"]),
        "strategy_name": str(seed["strategy_name"]),
        "paper_validation_passed": str(validation["decision_record"]["decision"]) == "PASS",
        "base_cagr": float(validation_metrics.get("cagr", 0.0)),
        "base_sharpe": float(validation_metrics.get("sharpe", 0.0)),
        "base_max_drawdown": float(validation_metrics.get("max_drawdown", 0.0)),
        "completed_trades": int(validation.get("completed_trades", 0)),
        "walk_forward_passed": bool(overfitting.get("passed", False)),
        "sensitivity_max_drift": float(overfitting.get("sensitivity_max_drift", 0.0)),
        "negative_window_count": len(negative_windows),
        "negative_windows": negative_windows,
        "validation_json": str(validation["analysis_result_json"]),
        "walk_forward_json": str(walk["analysis_result_json"]),
    }


def build_report(*, periods: int, allow_synthetic_ohlcv_fallback: bool, analysis_dir: Path) -> dict:
    preferred = _run_seed(
        seed_label=PREFERRED_REOPEN_SEED,
        periods=periods,
        allow_synthetic_ohlcv_fallback=allow_synthetic_ohlcv_fallback,
        analysis_dir=analysis_dir,
    )
    backup = _run_seed(
        seed_label=BACKUP_REOPEN_SEED,
        periods=periods,
        allow_synthetic_ohlcv_fallback=allow_synthetic_ohlcv_fallback,
        analysis_dir=analysis_dir,
    )

    seeds = sorted(
        [preferred, backup],
        key=lambda item: (
            not item["paper_validation_passed"],
            not item["walk_forward_passed"],
            int(item["negative_window_count"]),
            -float(item["base_cagr"]),
            -float(item["base_sharpe"]),
            float(item["sensitivity_max_drift"]),
        ),
    )

    preferred_now = seeds[0]
    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "cycle_reference": {
            "requested_preferred_seed": PREFERRED_REOPEN_SEED,
            "requested_backup_seed": BACKUP_REOPEN_SEED,
        },
        "reopen_seed_cycle": {
            "preferred_seed_now": str(preferred_now["seed_label"]),
            "next_step_now": "promote_revalidated_seed_into_attack_comparison"
            if preferred_now["paper_validation_passed"] and preferred_now["walk_forward_passed"]
            else "hold_reopen_seed_in_repair",
            "comparison_ready": all(item["paper_validation_passed"] for item in seeds),
        },
        "seed_results": seeds,
        "decision_summary": [
            f"Preferred seed on the current revalidation cycle is `{preferred_now['seed_label']}`.",
            f"Current preferred seed validation pass=`{preferred_now['paper_validation_passed']}` walk_forward_pass=`{preferred_now['walk_forward_passed']}`.",
            "Use this cycle result as the immediate seed-selection gate before reopening attack comparison.",
        ],
    }
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(
        periods=args.periods,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        analysis_dir=args.analysis_dir,
    )
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_post_spike_reopen_seed_cycle_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
