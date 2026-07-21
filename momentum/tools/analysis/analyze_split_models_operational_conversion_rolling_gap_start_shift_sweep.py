from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    STRONGEST_VARIANT,
)
from tools.analysis.analyze_split_models_operational_conversion_oos_validation import _pass_metrics, _run_candidate
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_rolling_gap_start_shift_sweep"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Rolling-Gap Start-Shift Sweep",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Status",
        "",
        f"- Decision: `{summary['sweep_decision']}`",
        f"- Best variant: `{summary['best_variant']}`",
        f"- Worst shift CAGR: `{_pct(summary['best_worst_shift_cagr'])}`",
        f"- Worst shift MDD: `{_pct(summary['best_worst_shift_mdd'])}`",
        f"- Worst shift negative WF: `{summary['best_worst_shift_negative_wf']}`",
        "",
        "## Specs",
        "",
        "| Rank | Sym | Sector | Max | Gap Months | Pass | Worst CAGR | Worst MDD | Worst Neg WF |",
        "| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_specs"], start=1):
        lines.append(
            f"| {idx} | {_pct(row['min_symbol_weight'])} | {_pct(row['min_sector_weight'])} | "
            f"{int(row['max_defense_count'])} | {int(row['min_defense_gap_months'])} | "
            f"`{row['all_shifts_pass']}` | {_pct(row['worst_shift_cagr'])} | "
            f"{_pct(row['worst_shift_mdd'])} | {int(row['worst_shift_negative_wf'])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    strongest = variants[STRONGEST_VARIANT]
    baseline = variants[BASELINE_VARIANT]
    specs = [
        {
            "min_symbol_weight": 0.09,
            "min_sector_weight": 0.28,
            "max_defense_count": 8,
            "min_defense_gap_months": 3,
            "trim_fraction": 1.0,
        },
        {
            "min_symbol_weight": 0.09,
            "min_sector_weight": 0.28,
            "max_defense_count": 8,
            "min_defense_gap_months": 4,
            "trim_fraction": 1.0,
        },
    ]
    spec_rows: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []
    for spec in specs:
        shift_rows: list[dict[str, object]] = []
        for start_shift_months in [0, 1, 2]:
            row = _run_candidate(
                strongest=strongest,
                baseline=baseline,
                universe=universe,
                price_cache=price_cache,
                flow_cache=flow_cache,
                monthly_close=monthly_close,
                signal_dates=signal_dates[start_shift_months:],
                cfg=cfg,
                **spec,
            )
            row["StartShiftMonths"] = start_shift_months
            shift_rows.append(row)
            all_rows.append({**spec, **row})
        pass_flags = [bool(_pass_metrics(row)) for row in shift_rows]
        spec_rows.append(
            {
                **spec,
                "variant": str(shift_rows[0]["Variant"]),
                "all_shifts_pass": all(pass_flags),
                "passed_shift_count": int(sum(pass_flags)),
                "worst_shift_cagr": float(min(float(row["CAGR"]) for row in shift_rows)),
                "worst_shift_mdd": float(min(float(row["MDD"]) for row in shift_rows)),
                "worst_shift_negative_wf": int(max(int(row["NegativeCAGRWindows"]) for row in shift_rows)),
                "shift_rows": shift_rows,
            }
        )
    ranked = sorted(
        spec_rows,
        key=lambda row: (
            not bool(row["all_shifts_pass"]),
            -int(row["passed_shift_count"]),
            int(row["worst_shift_negative_wf"]),
            -float(row["worst_shift_mdd"]),
            -float(row["worst_shift_cagr"]),
        ),
    )
    best = ranked[0]
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sweep_decision": "PASS_ROLLING_GAP_START_SHIFT_FOUND" if best["all_shifts_pass"] else "BLOCK_ROLLING_GAP_START_SHIFT",
        "best_variant": best["variant"],
        "best_params": {
            "min_symbol_weight": best["min_symbol_weight"],
            "min_sector_weight": best["min_sector_weight"],
            "max_defense_count": best["max_defense_count"],
            "min_defense_gap_months": best["min_defense_gap_months"],
            "trim_fraction": best["trim_fraction"],
        },
        "best_worst_shift_cagr": best["worst_shift_cagr"],
        "best_worst_shift_mdd": best["worst_shift_mdd"],
        "best_worst_shift_negative_wf": best["worst_shift_negative_wf"],
        "ranked_specs": ranked,
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    pd.DataFrame(all_rows).drop(columns=["DefenseDates"], errors="ignore").to_csv(
        OUTPUT_DIR / "rolling_gap_start_shift_sweep_rows.csv", index=False, encoding="utf-8-sig"
    )
    (OUTPUT_DIR / "rolling_gap_start_shift_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "rolling_gap_start_shift_sweep.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
