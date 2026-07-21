import argparse
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


sns.set_theme(style="whitegrid", context="talk")


def read_nav(path: Path, label: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df["Strategy"] = label
    return df


def add_drawdown(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Drawdown"] = out["nav"] / out["nav"].cummax() - 1.0
    return out


def style_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_nav(fig_dir: Path, data_dir: Path) -> None:
    frames = [
        read_nav(data_dir / "us_etf_riskbudget_nav.csv", "ETF RiskBudget"),
        read_nav(data_dir / "us_same_universe_ew_nav.csv", "Same-Universe EW"),
        read_nav(data_dir / "us_stock_mom12_1_nav.csv", "Stock Mom12_1"),
    ]
    plot_df = pd.concat(frames, ignore_index=True)
    fig, ax = plt.subplots(figsize=(14, 8))
    palette = {
        "ETF RiskBudget": "#355C7D",
        "Same-Universe EW": "#6C9A8B",
        "Stock Mom12_1": "#C06C84",
    }
    for strategy, grp in plot_df.groupby("Strategy"):
        ax.plot(grp["date"], grp["nav"], label=strategy, linewidth=2.5, color=palette[strategy])
    ax.set_title("Cumulative NAV")
    ax.set_ylabel("NAV")
    ax.set_xlabel("")
    style_axis(ax)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(fig_dir / "figure_1_cumulative_nav.png", dpi=220)
    plt.close(fig)


def plot_drawdown(fig_dir: Path, data_dir: Path) -> None:
    frames = [
        add_drawdown(read_nav(data_dir / "us_etf_riskbudget_nav.csv", "ETF RiskBudget")),
        add_drawdown(read_nav(data_dir / "us_same_universe_ew_nav.csv", "Same-Universe EW")),
        add_drawdown(read_nav(data_dir / "us_stock_mom12_1_nav.csv", "Stock Mom12_1")),
    ]
    plot_df = pd.concat(frames, ignore_index=True)
    fig, ax = plt.subplots(figsize=(14, 8))
    palette = {
        "ETF RiskBudget": "#355C7D",
        "Same-Universe EW": "#6C9A8B",
        "Stock Mom12_1": "#C06C84",
    }
    for strategy, grp in plot_df.groupby("Strategy"):
        ax.plot(grp["date"], grp["Drawdown"], label=strategy, linewidth=2.3, color=palette[strategy])
    ax.set_title("Drawdown")
    ax.set_ylabel("Drawdown")
    ax.set_xlabel("")
    style_axis(ax)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(fig_dir / "figure_2_drawdown.png", dpi=220)
    plt.close(fig)


def plot_cost_curve(fig_dir: Path, data_dir: Path) -> None:
    cost = pd.read_csv(data_dir / "us_stock_mom12_1_cost.csv")
    break_even = pd.read_csv(data_dir / "us_stock_mom12_1_break_even_cost.csv")
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.plot(cost["OneWayCostBps"], cost["CAGR"] * 100.0, marker="o", linewidth=2.5, color="#C06C84")
    be = float(break_even["BreakEvenOneWayBps_CAGRMatchBenchmark"].iloc[0])
    ax.axvline(be, color="#355C7D", linestyle="--", linewidth=2, label=f"Break-even vs benchmark: {be:.1f} bps")
    ax.set_title("CAGR vs One-Way Transaction Cost")
    ax.set_xlabel("One-Way Cost (bps)")
    ax.set_ylabel("CAGR (%)")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(fig_dir / "figure_3_cost_curve.png", dpi=220)
    plt.close(fig)


def plot_capacity(fig_dir: Path, data_dir: Path) -> None:
    cap = pd.read_csv(data_dir / "us_stock_mom12_1_capacity_summary.csv")
    cap = cap.sort_values("ParticipationThreshold").copy()
    cap["ParticipationPct"] = cap["ParticipationThreshold"] * 100.0
    cap["CapacityAUM_M"] = cap["CapacityAUMUSD"] / 1_000_000.0
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.plot(cap["ParticipationPct"], cap["CapacityAUM_M"], marker="o", linewidth=2.5, color="#6C9A8B")
    for _, row in cap.iterrows():
        ax.text(row["ParticipationPct"], row["CapacityAUM_M"], f"{row['CapacityAUM_M']:.1f}", fontsize=10, ha="left", va="bottom")
    ax.set_title("Capacity vs Participation Threshold")
    ax.set_xlabel("Participation Threshold (% of 60-day median dollar volume)")
    ax.set_ylabel("Capacity (USD millions)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(fig_dir / "figure_4_capacity_curve.png", dpi=220)
    plt.close(fig)


def plot_walkforward(fig_dir: Path, data_dir: Path) -> None:
    wf = pd.read_csv(data_dir / "us_walkforward_results.csv", parse_dates=["TestStart", "TestEnd"])
    keep = ["US Same-Universe EW Benchmark", "US Stock Mom12_1", "US ETF RiskBudget"]
    wf = wf[wf["Strategy"].isin(keep)].copy()
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(data=wf, x="TestStart", y="CAGR", hue="Strategy", ax=ax, palette=["#355C7D", "#6C9A8B", "#C06C84"])
    ax.set_title("Walk-Forward CAGR by Window")
    ax.set_xlabel("Test Window Start")
    ax.set_ylabel("CAGR")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(frameon=False, title="")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(fig_dir / "figure_5_walkforward_cagr.png", dpi=220)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate paper figures for U.S. momentum manuscript.")
    p.add_argument("--data-dir", type=str, default="backtests/us_momentum_eval_pitwiki_20260329")
    p.add_argument("--fig-dir", type=str, default="docs/figures_us_momentum_20260329")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    fig_dir = Path(args.fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    plot_nav(fig_dir, data_dir)
    plot_drawdown(fig_dir, data_dir)
    plot_cost_curve(fig_dir, data_dir)
    plot_capacity(fig_dir, data_dir)
    plot_walkforward(fig_dir, data_dir)
    print(f"saved figures to {fig_dir}")


if __name__ == "__main__":
    main()
