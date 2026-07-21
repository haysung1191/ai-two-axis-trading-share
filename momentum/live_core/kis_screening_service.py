from __future__ import annotations

from pathlib import Path
from typing import Callable

import config
from kis_api import KISApi
from live_core.kis_screener_metrics import calculate_momentum_metrics
from live_core.kis_screener_runner import build_screening_frame
from live_core.kis_screener_universe import get_current_stock_universe, get_etf_tickers


def run_default_screening(
    *,
    etf_mode: bool = False,
    max_items: int = 2500,
    stock_sort_column: str | None = None,
    config_module=config,
    repo_root: Path | None = None,
    api_factory: Callable[[], KISApi] = KISApi,
    momentum_calculator: Callable[[list[dict]], dict | None] = calculate_momentum_metrics,
):
    repo_root = repo_root or Path(__file__).resolve().parents[1]
    api = api_factory()

    if etf_mode:
        tickers = get_etf_tickers()
    else:
        tickers = get_current_stock_universe(
            config_module=config_module,
            repo_root=repo_root,
        )

    return build_screening_frame(
        api=api,
        tickers=tickers,
        momentum_calculator=momentum_calculator,
        etf_mode=etf_mode,
        max_items=max_items,
        sort_column="avg_momentum" if etf_mode else stock_sort_column,
    )
