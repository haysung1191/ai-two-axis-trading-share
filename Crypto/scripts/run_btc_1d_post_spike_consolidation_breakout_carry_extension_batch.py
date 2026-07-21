from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_walk_forward_diagnostic import (
    Btc1dWalkForwardDiagnosticConfig,
    Btc1dWalkForwardDiagnosticService,
)


REFERENCE_CAGR = 0.34639312
REFERENCE_MDD = 0.09526207
REFERENCE_SHARPE = 1.81320199

BASE_PARAMETERS: dict[str, float] = {
    "trend_ema_window": 92.0,
    "spike_lookback": 28.0,
    "min_spike_pct": 0.1045,
    "consolidation_window": 8.0,
    "max_consolidation_depth_pct": 0.058,
    "breakout_buffer_pct": 0.0025,
    "volume_lookback": 22.0,
    "min_volume_ratio": 1.05,
    "stop_ema_window": 20.0,
    "max_hold_bars": 36.0,
}


DEFAULT_VARIANTS: list[dict[str, Any]] = [
    {"label": "anchor_hold36_stop20", "updates": {}},
    {"label": "hold34_stop20", "updates": {"max_hold_bars": 34.0}},
    {"label": "hold32_stop20", "updates": {"max_hold_bars": 32.0}},
    {"label": "hold34_stop18", "updates": {"max_hold_bars": 34.0, "stop_ema_window": 18.0}},
    {"label": "hold34_stop22", "updates": {"max_hold_bars": 34.0, "stop_ema_window": 22.0}},
    {"label": "hold38_stop20", "updates": {"max_hold_bars": 38.0}},
    {"label": "hold40_stop20", "updates": {"max_hold_bars": 40.0}},
    {"label": "hold42_stop20", "updates": {"max_hold_bars": 42.0}},
    {"label": "hold38_stop18", "updates": {"max_hold_bars": 38.0, "stop_ema_window": 18.0}},
    {"label": "hold40_stop18", "updates": {"max_hold_bars": 40.0, "stop_ema_window": 18.0}},
    {"label": "hold38_stop22", "updates": {"max_hold_bars": 38.0, "stop_ema_window": 22.0}},
    {"label": "hold40_exitconfirm2", "updates": {"max_hold_bars": 40.0, "exit_confirmation_bars": 2.0}},
    {
        "label": "hold40_stop18_exitconfirm2",
        "updates": {"max_hold_bars": 40.0, "stop_ema_window": 18.0, "exit_confirmation_bars": 2.0},
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTC 1d post-spike consolidation breakout carry-extension model batch."
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    parser.add_argument("--variant-label", action="append", default=[])
    return parser


def _selected_variants(labels: list[str]) -> list[dict[str, Any]]:
    if not labels:
        return DEFAULT_VARIANTS
    selected = [row for row in DEFAULT_VARIANTS if str(row["label"]) in set(labels)]
    if not selected:
        raise SystemExit(f"No variants matched: {labels}")
    return selected


def _negative_windows(walk_forward: list[dict[str, Any]]) -> list[int]:
    return [
        int(window.get("window", 0))
        for window in walk_forward
        if float((window.get("metrics", {}) or {}).get("sharpe", 0.0)) < 0.0
        or float((window.get("metrics", {}) or {}).get("cagr", 0.0)) < 0.0
    ]


def _idle_windows(walk_forward: list[dict[str, Any]]) -> list[int]:
    return [
        int(window.get("window", 0))
        for window in walk_forward
        if int((window.get("metrics", {}) or {}).get("trades", 0)) == 0
    ]


def run_batch(*, analysis_dir: Path, periods: int, allow_synthetic_ohlcv_fallback: bool, labels: list[str]) -> dict[str, Any]:
    service = Btc1dWalkForwardDiagnosticService(analysis_results_dir=analysis_dir)
    run_id = (
        "btc-1d-post-spike-consolidation-breakout-carry-extension-"
        f"{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    rows: list[dict[str, Any]] = []

    for variant in _selected_variants(labels):
        params = dict(BASE_PARAMETERS)
        params.update(dict(variant["updates"]))
        label = str(variant["label"])
        report = service.run_diagnostic(
            Btc1dWalkForwardDiagnosticConfig(
                symbol="BTCUSDT",
                interval="1d",
                periods=int(periods),
                strategy_name="btc_1d_post_spike_consolidation_breakout_v4",
                fee_bps=20.0,
                slippage_bps=20.0,
                walk_forward_windows=5,
                sensitivity_limit=0.35,
                allow_synthetic_ohlcv_fallback=bool(allow_synthetic_ohlcv_fallback),
                candidate_label=f"post_spike_carry_extension::{label}",
                extra_parameters=params,
            ),
            run_id=f"{run_id}-{label}",
        )
        base_metrics = dict(report["base_metrics"])
        overfitting = dict(report["overfitting"])
        walk_forward = list(overfitting.get("walk_forward", []) or [])
        negative = _negative_windows(walk_forward)
        idle = _idle_windows(walk_forward)
        trades = int(base_metrics.get("trades", 0))
        cagr = float(base_metrics.get("cagr", 0.0))
        mdd = float(base_metrics.get("max_drawdown", 0.0))
        sharpe = float(base_metrics.get("sharpe", 0.0))
        drift = float(overfitting.get("sensitivity_max_drift", 0.0))
        viable = trades >= 8 and len(negative) == 0 and len(idle) <= 1
        rows.append(
            {
                "variant_label": label,
                "viable": viable,
                "trades": trades,
                "base_cagr": cagr,
                "base_max_drawdown": mdd,
                "base_sharpe": sharpe,
                "sensitivity_max_drift": drift,
                "negative_windows": negative,
                "idle_windows": idle,
                "cagr_delta_vs_reference": cagr - REFERENCE_CAGR,
                "mdd_delta_vs_reference": mdd - REFERENCE_MDD,
                "sharpe_delta_vs_reference": sharpe - REFERENCE_SHARPE,
                "analysis_result_json": str(report["analysis_result_json"]),
                "parameters": params,
            }
        )

    rows.sort(
        key=lambda row: (
            not bool(row["viable"]),
            int(row["negative_windows"] != []),
            int(row["idle_windows"] == []),
            float(row["mdd_delta_vs_reference"]) > 0.03,
            -float(row["base_cagr"]),
            -float(row["base_sharpe"]),
        )
    )
    payload = {
        "run_id": run_id,
        "reference": {
            "label": "anchor_hold36_stop20",
            "cagr": REFERENCE_CAGR,
            "max_drawdown": REFERENCE_MDD,
            "sharpe": REFERENCE_SHARPE,
        },
        "best_variant": rows[0] if rows else {},
        "results": rows,
    }

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    output_json = analysis_dir / f"btc_1d_post_spike_consolidation_breakout_carry_extension_batch_{stamp}.json"
    output_csv = analysis_dir / f"btc_1d_post_spike_consolidation_breakout_carry_extension_batch_{stamp}.csv"
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with output_csv.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "variant_label",
                "viable",
                "trades",
                "base_cagr",
                "base_max_drawdown",
                "base_sharpe",
                "sensitivity_max_drift",
                "negative_windows",
                "idle_windows",
                "cagr_delta_vs_reference",
                "mdd_delta_vs_reference",
                "sharpe_delta_vs_reference",
                "analysis_result_json",
                "parameters",
            ],
        )
        writer.writeheader()
        for row in rows:
            writable = dict(row)
            writable["negative_windows"] = json.dumps(writable["negative_windows"])
            writable["idle_windows"] = json.dumps(writable["idle_windows"])
            writable["parameters"] = json.dumps(writable["parameters"], sort_keys=True)
            writer.writerow(writable)

    return {
        "run_id": run_id,
        "analysis_result_json": str(output_json),
        "analysis_result_csv": str(output_csv),
        "best_variant": payload["best_variant"],
        "results": rows,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_batch(
        analysis_dir=args.analysis_dir,
        periods=args.periods,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        labels=list(args.variant_label),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
