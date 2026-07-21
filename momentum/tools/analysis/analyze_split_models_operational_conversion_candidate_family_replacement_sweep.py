from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_baseline_switch_sweep import (
    BASELINE_VARIANT,
    STRONGEST_VARIANT,
)
from tools.analysis.analyze_split_models_operational_conversion_oos_validation import _pass_metrics
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import _pct
from tools.analysis.analyze_split_models_operational_conversion_state_condition_defense_sweep import (
    _run_state_condition_defense,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context, _summarize_candidate


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_candidate_family_replacement_sweep"


def _short_family_name(name: str) -> str:
    return (
        name.replace("rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_", "")
        .replace("_risk_on", "")
        .replace("count", "c")
        .replace("bonus", "b")
        .replace("floor", "f")
        .replace("pen", "p")
    )


def _candidate_name(base_variant_name: str, params: dict[str, object]) -> str:
    return (
        f"family_replace_{_short_family_name(base_variant_name)}"
        f"_sym{int(round(float(params['min_symbol_weight']) * 100)):02d}"
        f"_sector{int(round(float(params['min_sector_weight']) * 100)):02d}"
        f"_trim{int(round(float(params['trim_fraction']) * 100)):02d}"
        f"_max{int(params['max_defense_count']):02d}"
    )


def _run_family_candidate(
    *,
    base_variant_name: str,
    base_result: dict[str, pd.DataFrame],
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
    cfg: BacktestConfig,
    params: dict[str, object],
) -> dict[str, object]:
    variants = _baseline_variant_map()
    candidate_base = variants[base_variant_name]
    baseline = variants[BASELINE_VARIANT]
    variant_name = _candidate_name(base_variant_name, params)
    result, diagnostics = _run_state_condition_defense(
        variant=replace(candidate_base, name=variant_name),
        fallback_variant=baseline,
        min_symbol_weight=float(params["min_symbol_weight"]),
        min_sector_weight=float(params["min_sector_weight"]),
        require_weak_flow=False,
        require_drag_flow_weak=False,
        max_defense_count=int(params["max_defense_count"]),
        trim_fraction=float(params["trim_fraction"]),
        universe=universe,
        price_cache=price_cache,
        flow_cache=flow_cache,
        monthly_close=monthly_close,
        signal_dates=signal_dates,
        cfg=cfg,
    )
    row = _summarize_candidate(variant_name, result, base_result)
    row["BaseVariant"] = base_variant_name
    row["MinSymbolWeight"] = float(params["min_symbol_weight"])
    row["MinSectorWeight"] = float(params["min_sector_weight"])
    row["MaxDefenseCount"] = int(params["max_defense_count"])
    row["TrimFraction"] = float(params["trim_fraction"])
    row["DefenseCount"] = int(diagnostics["defense_count"])
    row["FirstDefenseDate"] = diagnostics["first_defense_date"]
    row["LastDefenseDate"] = diagnostics["last_defense_date"]
    row["DefenseDates"] = diagnostics["defense_dates"]
    row["PassMetrics"] = _pass_metrics(row)
    return row


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Candidate-Family Replacement Sweep",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Status",
        "",
        f"- Decision: `{summary['replacement_decision']}`",
        f"- Best variant: `{summary['best_variant']}`",
        f"- Best base family: `{summary['best_base_variant']}`",
        f"- Best worst-shift CAGR: `{_pct(summary['best_worst_shift_cagr'])}`",
        f"- Best worst-shift MDD: `{_pct(summary['best_worst_shift_mdd'])}`",
        f"- Best worst-shift negative WF: `{summary['best_worst_shift_negative_wf']}`",
        "",
        "## Ranked Families",
        "",
        "| Rank | Base Family | Pass | Passed Shifts | Worst CAGR | Worst MDD | Worst Neg WF |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_families"], start=1):
        lines.append(
            f"| {idx} | `{row['base_variant']}` | `{row['all_shifts_pass']}` | "
            f"{int(row['passed_shift_count'])} | {_pct(row['worst_shift_cagr'])} | "
            f"{_pct(row['worst_shift_mdd'])} | {int(row['worst_shift_negative_wf'])} |"
        )
    lines.extend(["", "## Safety", "", json.dumps(summary["safety"], indent=2), ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    strongest = variants[STRONGEST_VARIANT]

    params = {
        "min_symbol_weight": 0.09,
        "min_sector_weight": 0.28,
        "max_defense_count": 8,
        "trim_fraction": 1.0,
    }
    family_specs = [
        STRONGEST_VARIANT,
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on",
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on",
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on",
    ]

    family_rows: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []
    for base_variant_name in family_specs:
        shift_rows: list[dict[str, object]] = []
        for start_shift_months in [0, 1, 2]:
            shifted_dates = signal_dates[start_shift_months:]
            base_result = _run_trading_backtest_variant(
                universe, price_cache, flow_cache, monthly_close, shifted_dates, cfg, strongest
            )
            row = _run_family_candidate(
                base_variant_name=base_variant_name,
                base_result=base_result,
                universe=universe,
                price_cache=price_cache,
                flow_cache=flow_cache,
                monthly_close=monthly_close,
                signal_dates=shifted_dates,
                cfg=cfg,
                params=params,
            )
            row["StartShiftMonths"] = start_shift_months
            shift_rows.append(row)
            all_rows.append(row)
        pass_flags = [bool(row["PassMetrics"]) for row in shift_rows]
        family_rows.append(
            {
                "base_variant": base_variant_name,
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
        family_rows,
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
        "replacement_decision": (
            "PASS_CANDIDATE_FAMILY_REPLACEMENT_FOUND"
            if best["all_shifts_pass"]
            else "BLOCK_NO_CANDIDATE_FAMILY_REPLACEMENT"
        ),
        "best_variant": best["variant"],
        "best_base_variant": best["base_variant"],
        "best_worst_shift_cagr": best["worst_shift_cagr"],
        "best_worst_shift_mdd": best["worst_shift_mdd"],
        "best_worst_shift_negative_wf": best["worst_shift_negative_wf"],
        "ranked_families": ranked,
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    pd.DataFrame(all_rows).drop(columns=["DefenseDates"], errors="ignore").to_csv(
        OUTPUT_DIR / "candidate_family_replacement_sweep_rows.csv", index=False, encoding="utf-8-sig"
    )
    (OUTPUT_DIR / "candidate_family_replacement_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "candidate_family_replacement_sweep.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
