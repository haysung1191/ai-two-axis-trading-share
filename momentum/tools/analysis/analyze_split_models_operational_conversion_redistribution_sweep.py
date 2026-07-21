from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _run_with_patch,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_redistribution_sweep"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
CURRENT_REDISTRIBUTION_VARIANT = "tail_release_top50_mid50"


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _patch_tail_release_custom(
    *,
    top2_share: float,
    penalty_start: float,
    penalty_floor: float,
    bottom_count: int = 6,
    penalty_power: float = 0.50,
) -> callable:
    def patch(book: pd.DataFrame) -> pd.DataFrame:
        if book.empty or len(book) < 5:
            return book
        out = book.copy()
        ranked = out.sort_values(["MomentumScore", "FlowScore", "Symbol"], ascending=[False, False, True])
        top_index = ranked.head(2).index
        candidate_bottom = ranked.loc[~ranked.index.isin(top_index)]
        if candidate_bottom.empty:
            return out

        local_bottom_count = min(bottom_count, len(candidate_bottom))
        bottom_index = candidate_bottom.tail(local_bottom_count).index
        bottom_before = pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).copy()

        if len(bottom_index) > 1:
            penalty_steps = pd.Series(np.linspace(0.0, 1.0, len(bottom_index)) ** penalty_power, index=bottom_index)
            penalty_series = pd.Series(
                penalty_start + (penalty_floor - penalty_start) * penalty_steps,
                index=bottom_index,
            )
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * penalty_series
            )
        else:
            out.loc[bottom_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0) * penalty_start
            )

        released = float(
            bottom_before.sum() - pd.to_numeric(out.loc[bottom_index, "TargetWeight"], errors="coerce").fillna(0.0).sum()
        )
        if released > 0:
            top2_part = released * top2_share
            mid_part = released - top2_part
            out.loc[top_index, "TargetWeight"] = (
                pd.to_numeric(out.loc[top_index, "TargetWeight"], errors="coerce").fillna(0.0)
                + top2_part / float(len(top_index))
            )
            mid_index = ranked.loc[~ranked.index.isin(bottom_index.union(top_index))].index
            if len(mid_index) > 0 and mid_part > 0:
                mid_weights = pd.to_numeric(out.loc[mid_index, "TargetWeight"], errors="coerce").fillna(0.0)
                total = float(mid_weights.sum())
                if total > 0:
                    out.loc[mid_index, "TargetWeight"] = mid_weights + mid_part * (mid_weights / total)
                else:
                    out.loc[mid_index, "TargetWeight"] = mid_weights + mid_part / float(len(mid_index))

        total_after = float(pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if total_after > 0:
            out["TargetWeight"] = pd.to_numeric(out["TargetWeight"], errors="coerce").fillna(0.0) / total_after
        return out

    return patch


def _make_variant_name(top2_share: float, penalty_start: float, penalty_floor: float) -> str:
    top2_pct = int(round(top2_share * 100))
    mid_pct = 100 - top2_pct
    start_pct = int(round(penalty_start * 100))
    floor_pct = int(round(penalty_floor * 100))
    return f"tail_release_top{top2_pct:02d}_mid{mid_pct:02d}_pen{start_pct}_floor{floor_pct}"


def _conversion_bucket(row: pd.Series, baseline: pd.Series) -> str:
    if (
        row["CAGR"] > baseline["CAGR"]
        and row["Sharpe"] > baseline["Sharpe"]
        and row["NegativeCAGRWindows"] == 0
        and row["Cost75BpsCAGRDelta"] > 0
        and row["MDD"] >= -0.32
    ):
        return "tight_watch"
    if row["NegativeCAGRWindows"] == 0 and row["CAGR"] > 0.70:
        return "watch"
    return "monitor"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Redistribution Sweep",
        "",
        "## Purpose",
        "",
        "- test narrow redistribution variants around `tail_release_top50_mid50`",
        "- check whether softer tail release can claw back drawdown without breaking the family headline edge",
        "",
        "## Current Read",
        "",
        f"- operating baseline: `{summary['baseline_variant']}`",
        f"- aggressive strongest: `{summary['strongest_variant']}`",
        f"- current redistribution truth: `{summary['current_redistribution_variant']}`",
        f"- best drawdown-control point in this sweep: `{summary['best_drawdown_control_variant']}`",
        f"- best drawdown-control MDD: `{_pct(summary['best_drawdown_control_mdd'])}`",
        f"- best drawdown-control CAGR: `{_pct(summary['best_drawdown_control_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Bucket | CAGR | MDD | Sharpe | Neg WF | 75 bps CAGR delta | Top3 Share |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['ConversionBucket']}` | {_pct(row['CAGR'])} | {_pct(row['MDD'])} | "
            f"{row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} | {_pct(row['Cost75BpsCAGRDelta'])} | {_pct(row['Top3PositiveSymbolShare'])} |"
        )

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- {summary['verdict']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    baseline = variants[BASELINE_VARIANT]
    strongest = variants[STRONGEST_VARIANT]

    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest
    )
    baseline_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, baseline
    )

    baseline_summary = _summarize_candidate(BASELINE_VARIANT, baseline_result, strongest_result)

    grid = [
        (0.25, 0.35, 0.20),
        (0.35, 0.35, 0.20),
        (0.45, 0.35, 0.20),
        (0.50, 0.35, 0.20),
        (0.25, 0.35, 0.25),
        (0.35, 0.35, 0.25),
        (0.45, 0.35, 0.25),
        (0.35, 0.35, 0.30),
    ]

    rows: list[dict[str, object]] = []
    for top2_share, penalty_start, penalty_floor in grid:
        variant_name = _make_variant_name(top2_share, penalty_start, penalty_floor)
        variant = replace(strongest, name=variant_name)
        result = _run_with_patch(
            variant,
            _patch_tail_release_custom(
                top2_share=top2_share,
                penalty_start=penalty_start,
                penalty_floor=penalty_floor,
            ),
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(variant_name, result, strongest_result)
        summary["Top2Share"] = top2_share
        summary["PenaltyStart"] = penalty_start
        summary["PenaltyFloor"] = penalty_floor
        summary["CurrentRedistributionGap"] = summary["MDD"] - (-0.3464441125219072)
        summary["ConversionBucket"] = _conversion_bucket(pd.Series(summary), pd.Series(baseline_summary))
        rows.append(summary)

    compare = pd.DataFrame(rows)
    compare = compare.sort_values(
        ["NegativeCAGRWindows", "MDD", "Sharpe", "CAGR"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "redistribution_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best_drawdown = compare.sort_values(
        ["NegativeCAGRWindows", "MDD", "CAGR", "Sharpe"],
        ascending=[True, False, False, False],
    ).iloc[0]
    current_row = compare.loc[compare["Variant"] == _make_variant_name(0.50, 0.35, 0.20)].iloc[0]

    summary = {
        "baseline_variant": BASELINE_VARIANT,
        "strongest_variant": STRONGEST_VARIANT,
        "current_redistribution_variant": CURRENT_REDISTRIBUTION_VARIANT,
        "best_drawdown_control_variant": str(best_drawdown["Variant"]),
        "best_drawdown_control_cagr": float(best_drawdown["CAGR"]),
        "best_drawdown_control_mdd": float(best_drawdown["MDD"]),
        "best_drawdown_control_sharpe": float(best_drawdown["Sharpe"]),
        "best_drawdown_control_top2_share": float(best_drawdown["Top2Share"]),
        "best_drawdown_control_penalty_floor": float(best_drawdown["PenaltyFloor"]),
        "current_like_variant": str(current_row["Variant"]),
        "current_like_cagr": float(current_row["CAGR"]),
        "current_like_mdd": float(current_row["MDD"]),
        "current_like_sharpe": float(current_row["Sharpe"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }
    summary["verdict"] = (
        f"the narrow redistribution sweep found `{summary['best_drawdown_control_variant']}` as the cleanest drawdown-control point; "
        f"it improves redistribution MDD from {_pct(summary['current_like_mdd'])} to {_pct(summary['best_drawdown_control_mdd'])} "
        f"while keeping CAGR at {_pct(summary['best_drawdown_control_cagr'])}, but it still remains worse than the operating baseline drawdown bar."
    )

    (OUTPUT_DIR / "redistribution_sweep_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "redistribution_sweep_review.md").write_text(
        _build_markdown(summary), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
