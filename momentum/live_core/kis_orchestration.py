from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import pandas as pd

from live_core.kis_io import write_csv_any
from live_core.kis_metrics import blend_component_metrics

if TYPE_CHECKING:
    from kis_backtest_from_prices import StrategyConfig


HYBRID_STRATEGY_COMPONENTS: dict[str, dict[str, float]] = {
    "Weekly Hybrid RS50 RB50": {
        "Weekly Score50 RegimeState": 0.50,
        "Weekly ETF RiskBudget": 0.50,
    },
    "Weekly Hybrid Flow50 RS50": {
        "Weekly ForeignFlow v2": 0.50,
        "Weekly Score50 RegimeState": 0.50,
    },
    "Weekly Hybrid FV350 RS50": {
        "Weekly ForeignFlow v3": 0.50,
        "Weekly Score50 RegimeState": 0.50,
    },
    "Weekly Hybrid QP50 RS50": {
        "Weekly QualityProfitability MVP": 0.50,
        "Weekly Score50 RegimeState": 0.50,
    },
}

RESEARCH_ONLY_STRATEGY_NAMES = {
    "Weekly ForeignFlow v2",
    "Weekly ForeignFlow v3",
    "Weekly Hybrid Flow50 RS50",
    "Weekly Hybrid FV350 RS50",
    "Weekly QualityProfitability MVP",
    "Weekly Hybrid QP50 RS50",
}

OPERATIONAL_CANDIDATE_STRATEGY_NAMES = {
    "Weekly Score50 RegimeState",
    "Weekly ETF RiskBudget",
    "Weekly Hybrid RS50 RB50",
}


def is_hybrid_strategy_name(strategy_name: str) -> bool:
    return strategy_name in HYBRID_STRATEGY_COMPONENTS


def is_research_only_strategy_name(strategy_name: str) -> bool:
    return str(strategy_name) in RESEARCH_ONLY_STRATEGY_NAMES


def is_operational_candidate_strategy_name(strategy_name: str) -> bool:
    return str(strategy_name) in OPERATIONAL_CANDIDATE_STRATEGY_NAMES


def blend_strategy_results(
    strategy_name: str,
    component_results: dict[str, tuple[pd.DataFrame, dict[str, float]]],
) -> tuple[pd.DataFrame, dict[str, float]]:
    spec = HYBRID_STRATEGY_COMPONENTS.get(strategy_name)
    if spec is None:
        raise ValueError(f"Unsupported hybrid strategy: {strategy_name}")
    missing = [name for name in spec.keys() if name not in component_results]
    if missing:
        raise ValueError(f"Missing hybrid components for {strategy_name}: {missing}")

    daily_frames: list[pd.Series] = []
    for component_name in spec.keys():
        out, _ = component_results[component_name]
        if out is None or out.empty or "daily_return" not in out.columns:
            raise ValueError(f"Hybrid component {component_name} has no daily_return series.")
        daily_frames.append(out["daily_return"].rename(component_name))
    merged = pd.concat(daily_frames, axis=1, join="inner").fillna(0.0)
    if merged.empty:
        raise ValueError(f"Hybrid component overlap is empty for {strategy_name}.")

    out = pd.DataFrame(index=merged.index)
    out["daily_return"] = 0.0
    for component_name, weight in spec.items():
        out["daily_return"] = out["daily_return"] + float(weight) * merged[component_name]
    out["nav"] = (1.0 + out["daily_return"]).cumprod()
    metrics = blend_component_metrics(spec, component_results, out)
    return out, metrics


def run_strategy_batch(
    strategies: list[StrategyConfig],
    run_strategy: Callable[[StrategyConfig], tuple[pd.DataFrame, dict[str, float]]],
) -> tuple[list[dict[str, Any]], pd.DataFrame | None, dict[str, tuple[pd.DataFrame, dict[str, float]]]]:
    summary: list[dict[str, Any]] = []
    nav: pd.DataFrame | None = None
    strategy_outputs: dict[str, tuple[pd.DataFrame, dict[str, float]]] = {}

    for strategy in strategies:
        print(f"running {strategy.name}...")
        out, metrics = run_strategy(strategy)
        row = {"Strategy": strategy.name}
        row.update(metrics)
        summary.append(row)
        strategy_outputs[strategy.name] = (out, metrics)
        if nav is None:
            nav = pd.DataFrame(index=out.index)
        nav[strategy.name] = out["nav"]

    return summary, nav, strategy_outputs


def append_hybrid_results(
    summary: list[dict[str, Any]],
    nav: pd.DataFrame | None,
    strategy_outputs: dict[str, tuple[pd.DataFrame, dict[str, float]]],
) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    if nav is None:
        nav = pd.DataFrame()
    for hybrid_name in HYBRID_STRATEGY_COMPONENTS.keys():
        if not all(component_name in strategy_outputs for component_name in HYBRID_STRATEGY_COMPONENTS[hybrid_name].keys()):
            continue
        print(f"running {hybrid_name}...")
        out, metrics = blend_strategy_results(hybrid_name, strategy_outputs)
        row = {"Strategy": hybrid_name}
        row.update(metrics)
        summary.append(row)
        nav[hybrid_name] = out["nav"]
    return summary, nav


def save_backtest_outputs(summary: list[dict[str, Any]], nav: pd.DataFrame, save_prefix: str) -> tuple[pd.DataFrame, str, str]:
    summary_df = pd.DataFrame(summary)
    summary_path = f"{save_prefix}_summary.csv"
    nav_path = f"{save_prefix}_nav.csv"
    write_csv_any(summary_df, summary_path, index=False)
    write_csv_any(nav, nav_path, index=True)
    return summary_df, summary_path, nav_path
