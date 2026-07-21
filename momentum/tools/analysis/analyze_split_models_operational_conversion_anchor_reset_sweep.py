from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _run_trading_backtest_variant
from tools.analysis.analyze_split_models_operational_conversion_redistribution_sweep import (
    _patch_tail_release_custom,
    _pct,
)
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    _build_context,
    _run_with_patch,
    _summarize_candidate,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_anchor_reset_sweep"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
CURRENT_ANCHOR_VARIANT = "tail_release_top25_mid75_pen35_floor25"
UPSTREAM_VARIANTS = [
    "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on",
    "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on",
    "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_risk_on",
    "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on",
    "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on",
    "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
]


def _bucket(row: pd.Series, baseline: pd.Series) -> str:
    if (
        row["NegativeCAGRWindows"] == 0
        and row["CAGR"] > baseline["CAGR"]
        and row["Sharpe"] > baseline["Sharpe"]
        and row["MDD"] >= -0.32
    ):
        return "tight_watch"
    if row["NegativeCAGRWindows"] == 0 and row["CAGR"] > 0.70:
        return "watch"
    return "monitor"


def _anchor_name(upstream_variant: str) -> str:
    upstream_stub = upstream_variant.replace("rule_sector_cap2_breadth_it_us5_", "")
    return f"anchor_reset_{upstream_stub}_tail25_mid75_floor25"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Anchor Reset Sweep",
        "",
        "## Purpose",
        "",
        "- test whether the current operational-conversion anchor is sitting on the best nearby upstream family",
        "- keep the same redistribution overlay and only change the upstream ranked-tail structure underneath it",
        "",
        "## Current Read",
        "",
        f"- current anchor: `{summary['current_anchor_variant']}`",
        f"- best anchor-reset point: `{summary['best_variant']}`",
        f"- best anchor-reset MDD: `{_pct(summary['best_mdd'])}`",
        f"- best anchor-reset CAGR: `{_pct(summary['best_cagr'])}`",
        "",
        "## Ranked Sweep",
        "",
        "| Rank | Variant | Upstream | Bucket | CAGR | MDD | Sharpe | Neg WF |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(summary["ranked_rows"], start=1):
        lines.append(
            f"| {idx} | `{row['Variant']}` | `{row['UpstreamVariant']}` | `{row['Bucket']}` | "
            f"{_pct(row['CAGR'])} | {_pct(row['MDD'])} | {row['Sharpe']:.4f} | {int(row['NegativeCAGRWindows'])} |"
        )
    lines.extend(["", "## Verdict", "", f"- {summary['verdict']}", ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variants = _baseline_variant_map()
    baseline = variants[BASELINE_VARIANT]

    strongest_variant = variants["rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"]
    strongest_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, strongest_variant
    )
    baseline_result = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, baseline
    )
    baseline_summary = _summarize_candidate(BASELINE_VARIANT, baseline_result, strongest_result)

    redistribution_patch = _patch_tail_release_custom(top2_share=0.25, penalty_start=0.35, penalty_floor=0.25)

    rows: list[dict[str, object]] = []
    for upstream_name in UPSTREAM_VARIANTS:
        upstream_variant = variants[upstream_name]
        anchored_variant = replace(upstream_variant, name=_anchor_name(upstream_name))
        result = _run_with_patch(
            anchored_variant,
            redistribution_patch,
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        summary = _summarize_candidate(anchored_variant.name, result, strongest_result)
        summary["UpstreamVariant"] = upstream_name
        summary["Bucket"] = _bucket(pd.Series(summary), pd.Series(baseline_summary))
        rows.append(summary)

    current_anchor_upstream = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
    current_anchor_row = next(row for row in rows if row["UpstreamVariant"] == current_anchor_upstream)
    current_anchor_row["Variant"] = CURRENT_ANCHOR_VARIANT

    compare = pd.DataFrame(rows).sort_values(
        ["NegativeCAGRWindows", "MDD", "CAGR", "Sharpe"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "anchor_reset_sweep_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    summary = {
        "current_anchor_variant": CURRENT_ANCHOR_VARIANT,
        "current_anchor_upstream_variant": current_anchor_upstream,
        "best_variant": str(best["Variant"]),
        "best_upstream_variant": str(best["UpstreamVariant"]),
        "best_cagr": float(best["CAGR"]),
        "best_mdd": float(best["MDD"]),
        "best_sharpe": float(best["Sharpe"]),
        "ranked_rows": compare.to_dict(orient="records"),
    }

    if best["UpstreamVariant"] == current_anchor_upstream:
        summary["verdict"] = (
            f"the current anchor is still the best nearby upstream reset point. "
            f"No adjacent ranked-tail family beats `{CURRENT_ANCHOR_VARIANT}` on drawdown-control ordering."
        )
    else:
        summary["verdict"] = (
            f"the anchor-reset sweep finds `{summary['best_variant']}` on `{summary['best_upstream_variant']}` as a better nearby base; "
            f"it moves MDD to {_pct(summary['best_mdd'])} with CAGR {_pct(summary['best_cagr'])}."
        )

    (OUTPUT_DIR / "anchor_reset_sweep_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "anchor_reset_sweep_review.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
