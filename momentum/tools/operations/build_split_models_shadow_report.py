from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from split_models.backtest import BacktestConfig, run_backtests


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_shadow"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
FLOAT_TOLERANCE = 1e-9


def _recent_slice(df: pd.DataFrame, date_col: str, months: int = 12) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    out = out.dropna(subset=[date_col]).sort_values(date_col)
    if out.empty:
        return out
    cutoff = out[date_col].max() - pd.DateOffset(months=months)
    return out[out[date_col] >= cutoff].copy()


def _passes_threshold(value: float, threshold: float, comparator: str) -> bool:
    if comparator == ">=":
        return value >= (threshold - FLOAT_TOLERANCE)
    if comparator == "<=":
        return value <= (threshold + FLOAT_TOLERANCE)
    return value > (threshold + FLOAT_TOLERANCE)


def _health_checks(summary: dict, turnover_monitor: pd.DataFrame) -> pd.DataFrame:
    checks = [
        {
            "Check": "Current holdings >= 4",
            "Metric": "current_holdings",
            "Value": float(summary["current_holdings"] or 0),
            "Threshold": 4.0,
            "Comparator": ">=",
        },
        {
            "Check": "Current top1 weight <= 0.25",
            "Metric": "current_top1_weight",
            "Value": float(summary["current_top1_weight"] or 0.0),
            "Threshold": 0.25,
            "Comparator": "<=",
        },
        {
            "Check": "Current top3 weight <= 0.60",
            "Metric": "current_top3_weight",
            "Value": float(summary["current_top3_weight"] or 0.0),
            "Threshold": 0.60,
            "Comparator": "<=",
        },
        {
            "Check": "Recent avg turnover <= 1.50",
            "Metric": "recent_avg_turnover",
            "Value": float(summary["recent_avg_turnover"] or 0.0),
            "Threshold": 1.50,
            "Comparator": "<=",
        },
        {
            "Check": "Recent CAGR proxy > 0",
            "Metric": "recent_cagr_proxy",
            "Value": float(summary["recent_cagr_proxy"] or 0.0),
            "Threshold": 0.0,
            "Comparator": ">",
        },
        {
            "Check": "Current max sector weight <= 0.50",
            "Metric": "current_max_sector_weight",
            "Value": float(summary["current_max_sector_weight"] or 0.0),
            "Threshold": 0.50,
            "Comparator": "<=",
        },
    ]

    if not turnover_monitor.empty and "Holdings" in turnover_monitor.columns:
        min_holdings_recent = float(pd.to_numeric(turnover_monitor["Holdings"], errors="coerce").min())
        max_top1_recent = float(pd.to_numeric(turnover_monitor.get("Top1Weight"), errors="coerce").max())
        max_top3_recent = float(pd.to_numeric(turnover_monitor.get("Top3Weight"), errors="coerce").max())
        max_sector_recent = float(pd.to_numeric(turnover_monitor.get("MaxSectorWeight"), errors="coerce").max())
        checks.extend(
            [
                {
                    "Check": "Recent min holdings >= 4",
                    "Metric": "recent_min_holdings",
                    "Value": min_holdings_recent,
                    "Threshold": 4.0,
                    "Comparator": ">=",
                },
                {
                    "Check": "Recent max top1 weight <= 0.25",
                    "Metric": "recent_max_top1_weight",
                    "Value": max_top1_recent,
                    "Threshold": 0.25,
                    "Comparator": "<=",
                },
                {
                    "Check": "Recent max top3 weight <= 0.75",
                    "Metric": "recent_max_top3_weight",
                    "Value": max_top3_recent,
                    "Threshold": 0.75,
                    "Comparator": "<=",
                },
                {
                    "Check": "Recent max sector weight <= 0.70",
                    "Metric": "recent_max_sector_weight",
                    "Value": max_sector_recent,
                    "Threshold": 0.70,
                    "Comparator": "<=",
                },
            ]
        )

    out = pd.DataFrame(checks)
    passed = []
    for row in out.itertuples(index=False):
        passed.append(int(_passes_threshold(float(row.Value), float(row.Threshold), str(row.Comparator))))
    out["Passed"] = passed
    return out


def _append_history(path: Path, row_df: pd.DataFrame, key_cols: list[str]) -> None:
    if row_df.empty:
        return
    if path.exists():
        old = pd.read_csv(path)
        merged = pd.concat([old, row_df], ignore_index=True)
    else:
        merged = row_df.copy()
    keep_cols = [col for col in key_cols if col in merged.columns]
    if keep_cols:
        merged = merged.drop_duplicates(subset=keep_cols, keep="last")
    merged.to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = run_backtests(output_dir=OUTPUT_DIR, config=BacktestConfig(baseline_variant=BASELINE_VARIANT))

    nav = results["trading_book_backtest_nav"].copy()
    positions = results["trading_book_backtest_positions"].copy()
    weights = pd.read_csv(OUTPUT_DIR / "trading_book_backtest_weights.csv")

    recent_nav = _recent_slice(nav, "SignalDate", months=12)
    recent_positions = _recent_slice(positions, "SignalDate", months=12)
    recent_weights = _recent_slice(weights, "SignalDate", months=12)

    concentration = pd.DataFrame()
    if not recent_positions.empty:
        concentration = (
            recent_positions.groupby("SignalDate")
            .agg(
                PositionCount=("Symbol", "count"),
                Top1Weight=("TargetWeight", "max"),
                Top3Weight=("TargetWeight", lambda s: float(pd.Series(s).sort_values(ascending=False).head(3).sum())),
                AvgMomentumScore=("MomentumScore", "mean"),
                AvgFlowScore=("FlowScore", "mean"),
            )
            .reset_index()
        )

    turnover_monitor = recent_nav[["SignalDate", "NextDate", "GrossReturn", "NetReturn", "Turnover", "NAV", "Holdings"]].copy()
    turnover_monitor["LossFlag"] = (pd.to_numeric(turnover_monitor["NetReturn"], errors="coerce") < 0).astype(int)
    if not concentration.empty:
        turnover_monitor = turnover_monitor.merge(concentration, on="SignalDate", how="left")

    current_book = pd.DataFrame()
    current_sector = pd.DataFrame()
    if not recent_positions.empty:
        latest_signal = recent_positions["SignalDate"].max()
        current_book = recent_positions[recent_positions["SignalDate"] == latest_signal].copy()
        current_book = current_book.sort_values(["TargetWeight", "MomentumScore"], ascending=[False, False]).reset_index(drop=True)
        current_sector = (
            current_book.groupby(["Market", "Sector"], as_index=False)
            .agg(
                PositionCount=("Symbol", "count"),
                WeightSum=("TargetWeight", "sum"),
                AvgMomentumScore=("MomentumScore", "mean"),
            )
            .sort_values(["WeightSum", "AvgMomentumScore"], ascending=[False, False])
            .reset_index(drop=True)
        )

    monthly_sector = pd.DataFrame()
    sector_leaders = pd.DataFrame()
    if not recent_positions.empty:
        monthly_sector = (
            recent_positions.groupby(["SignalDate", "Market", "Sector"], as_index=False)
            .agg(
                PositionCount=("Symbol", "count"),
                WeightSum=("TargetWeight", "sum"),
                AvgMomentumScore=("MomentumScore", "mean"),
            )
            .sort_values(["SignalDate", "WeightSum"], ascending=[True, False])
        )
        sector_leaders = (
            monthly_sector.sort_values(["SignalDate", "WeightSum", "AvgMomentumScore"], ascending=[True, False, False])
            .groupby("SignalDate", as_index=False)
            .first()
            .rename(
                columns={
                    "Market": "DominantSectorMarket",
                    "Sector": "DominantSector",
                    "PositionCount": "DominantSectorPositionCount",
                    "WeightSum": "DominantSectorWeight",
                    "AvgMomentumScore": "DominantSectorAvgMomentumScore",
                }
            )
        )
        max_sector_by_month = (
            monthly_sector.groupby("SignalDate", as_index=False)
            .agg(MaxSectorWeight=("WeightSum", "max"))
        )
        turnover_monitor = turnover_monitor.merge(max_sector_by_month, on="SignalDate", how="left")

    loss_months = pd.DataFrame()
    if not turnover_monitor.empty:
        loss_months = turnover_monitor[turnover_monitor["LossFlag"] == 1].copy()
        if not loss_months.empty and not sector_leaders.empty:
            loss_months = loss_months.merge(sector_leaders, on="SignalDate", how="left")
        if not loss_months.empty:
            loss_months["LossRank"] = (
                pd.to_numeric(loss_months["NetReturn"], errors="coerce")
                .rank(method="first", ascending=True)
                .astype(int)
            )
            loss_months = loss_months.sort_values(["NetReturn", "SignalDate"], ascending=[True, True]).reset_index(drop=True)
        expected_loss_cols = [
            "SignalDate",
            "NextDate",
            "GrossReturn",
            "NetReturn",
            "Turnover",
            "NAV",
            "Holdings",
            "LossFlag",
            "PositionCount",
            "Top1Weight",
            "Top3Weight",
            "AvgMomentumScore",
            "AvgFlowScore",
            "MaxSectorWeight",
            "DominantSectorMarket",
            "DominantSector",
            "DominantSectorPositionCount",
            "DominantSectorWeight",
            "DominantSectorAvgMomentumScore",
            "LossRank",
        ]
        loss_months = loss_months.reindex(columns=expected_loss_cols)

    recent_nav.to_csv(OUTPUT_DIR / "shadow_recent_nav.csv", index=False, encoding="utf-8-sig")
    recent_positions.to_csv(OUTPUT_DIR / "shadow_recent_positions.csv", index=False, encoding="utf-8-sig")
    recent_weights.to_csv(OUTPUT_DIR / "shadow_recent_weights.csv", index=False, encoding="utf-8-sig")
    turnover_monitor.to_csv(OUTPUT_DIR / "shadow_turnover_monitor.csv", index=False, encoding="utf-8-sig")
    concentration.to_csv(OUTPUT_DIR / "shadow_concentration_monitor.csv", index=False, encoding="utf-8-sig")
    current_book.to_csv(OUTPUT_DIR / "shadow_current_book.csv", index=False, encoding="utf-8-sig")
    current_sector.to_csv(OUTPUT_DIR / "shadow_current_sector_mix.csv", index=False, encoding="utf-8-sig")
    monthly_sector.to_csv(OUTPUT_DIR / "shadow_monthly_sector_mix.csv", index=False, encoding="utf-8-sig")
    loss_months.to_csv(OUTPUT_DIR / "shadow_loss_month_diagnostics.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": BASELINE_VARIANT,
        "recent_months": int(len(recent_nav)),
        "recent_start": "" if recent_nav.empty else str(pd.to_datetime(recent_nav["SignalDate"]).min().date()),
        "recent_end": "" if recent_nav.empty else str(pd.to_datetime(recent_nav["NextDate"]).max().date()),
        "recent_cagr_proxy": None,
        "recent_avg_turnover": float(pd.to_numeric(recent_nav["Turnover"], errors="coerce").mean()) if not recent_nav.empty else None,
        "recent_loss_months": int(turnover_monitor["LossFlag"].sum()) if not turnover_monitor.empty else 0,
        "current_holdings": int(len(current_book)),
        "current_top1_weight": float(current_book["TargetWeight"].max()) if not current_book.empty else None,
        "current_top3_weight": float(current_book["TargetWeight"].head(3).sum()) if not current_book.empty else None,
        "current_max_sector_weight": float(current_sector["WeightSum"].max()) if not current_sector.empty else None,
        "current_dominant_sector": None if current_sector.empty else str(current_sector.iloc[0]["Sector"]),
    }
    if not recent_nav.empty:
        nav_series = pd.to_numeric(recent_nav["NAV"], errors="coerce")
        if len(nav_series) >= 2:
            years = max(len(nav_series) / 12.0, 1.0 / 12.0)
            summary["recent_cagr_proxy"] = float((nav_series.iloc[-1] / nav_series.iloc[0]) ** (1.0 / years) - 1.0)

    health = _health_checks(summary, turnover_monitor)
    summary["health_pass_count"] = int(health["Passed"].sum()) if not health.empty else 0
    summary["health_total_checks"] = int(len(health))
    summary["health_verdict"] = "PASS" if not health.empty and bool(health["Passed"].all()) else "FAIL"

    (OUTPUT_DIR / "shadow_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(OUTPUT_DIR / "shadow_summary.csv", index=False, encoding="utf-8-sig")
    health.to_csv(OUTPUT_DIR / "shadow_health.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "shadow_health.json").write_text(health.to_json(orient="records", indent=2), encoding="utf-8")

    history_row = summary_df.copy()
    history_row["RunTimestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    _append_history(
        OUTPUT_DIR / "shadow_summary_history.csv",
        history_row,
        key_cols=["baseline_variant", "recent_start", "recent_end"],
    )

    if not health.empty:
        health_history = health.copy()
        health_history["BaselineVariant"] = summary["baseline_variant"]
        health_history["RecentStart"] = summary["recent_start"]
        health_history["RecentEnd"] = summary["recent_end"]
        health_history["RunTimestamp"] = history_row["RunTimestamp"].iloc[0]
        _append_history(
            OUTPUT_DIR / "shadow_health_history.csv",
            health_history,
            key_cols=["BaselineVariant", "RecentStart", "RecentEnd", "Check"],
        )

    print(f"baseline_variant={summary['baseline_variant']}")
    print(f"recent_months={summary['recent_months']}")
    print(f"recent_loss_months={summary['recent_loss_months']}")
    print(f"current_holdings={summary['current_holdings']}")
    print(f"health_verdict={summary['health_verdict']}")


if __name__ == "__main__":
    main()
