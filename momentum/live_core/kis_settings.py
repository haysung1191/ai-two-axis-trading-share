from __future__ import annotations

import argparse
from dataclasses import dataclass

import config


def default_price_base() -> str:
    return f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"


def default_flow_base() -> str:
    return f"gs://{config.GCS_BUCKET_NAME}/flows_naver_8y" if config.GCS_BUCKET_NAME else "data/flows_naver_8y"


def default_quality_base() -> str:
    return "data/quality_fnguide"


@dataclass
class KISBacktestSettings:
    base: str
    top_n: int = 20
    fee_bps: float = 8.0
    max_files: int = 0
    save_prefix: str = "kis_backtest"
    min_common_dates: int = 180
    regime_filter: int = 1
    stop_loss_pct: float = 0.12
    trend_exit_ma: int = 60
    regime_ma_window: int = 200
    regime_slope_window: int = 20
    regime_breadth_threshold: float = 0.55
    vol_lookback: int = 20
    target_vol_annual: float = 0.20
    max_weight: float = 0.20
    min_gross_exposure: float = 0.50
    score_top_k: int = 50
    score_power: float = 1.5
    regime_off_exposure: float = 0.40
    allow_intraperiod_reentry: int = 1
    reentry_cooldown_days: int = 0
    range_slope_threshold: float = 0.015
    range_dist_threshold: float = 0.03
    range_breakout_persistence_threshold: float = 0.35
    range_breadth_tolerance: float = 0.15
    osc_lookback: int = 20
    osc_z_entry: float = -1.5
    osc_z_exit: float = -0.25
    osc_z_stop: float = -2.5
    osc_band_sigma: float = 1.5
    osc_band_break_sigma: float = 2.0
    osc_reentry_cooldown_days: int = 5
    rotation_top_k: int = 5
    rotation_tilt_strength: float = 0.20
    rotation_min_sleeve_weight: float = 0.25
    risk_budget_lookback: int = 120
    risk_budget_shrinkage: float = 0.35
    risk_budget_iv_blend: float = 0.50
    flow_base: str = "data/flows_naver_8y"
    quality_base: str = "data/quality_fnguide"
    quality_hold_buffer: int = 10
    quality_trend_ma: int = 60
    use_point_in_time_universe: int = 1
    stock_universe_min_bars: int = 750
    stock_universe_min_price: float = 1000.0
    stock_universe_min_avg_value: float = 5_000_000_000.0
    stock_universe_min_median_value: float = 2_000_000_000.0
    stock_universe_max_zero_days: int = 1
    etf_universe_min_bars: int = 180
    etf_universe_min_avg_value: float = 500_000_000.0
    etf_universe_min_median_value: float = 100_000_000.0
    etf_universe_max_zero_days: int = 1

    @property
    def fee_rate(self) -> float:
        return self.fee_bps / 10000.0

    @property
    def use_regime_filter_bool(self) -> bool:
        return bool(self.regime_filter)


def build_arg_parser(defaults: KISBacktestSettings | None = None) -> argparse.ArgumentParser:
    defaults = defaults or KISBacktestSettings(
        base=default_price_base(),
        flow_base=default_flow_base(),
        quality_base=default_quality_base(),
    )
    p = argparse.ArgumentParser(description="Run momentum backtests from KIS daily OHLCV close-price csv.gz data.")
    p.add_argument("--base", type=str, default=defaults.base)
    p.add_argument("--top-n", type=int, default=defaults.top_n)
    p.add_argument("--fee-bps", type=float, default=defaults.fee_bps)
    p.add_argument("--max-files", type=int, default=defaults.max_files, help="0 means all")
    p.add_argument("--save-prefix", type=str, default=defaults.save_prefix)
    p.add_argument("--min-common-dates", type=int, default=defaults.min_common_dates)
    p.add_argument("--regime-filter", type=int, default=defaults.regime_filter, help="1 enables market MA200 risk-on filter")
    p.add_argument("--stop-loss-pct", type=float, default=defaults.stop_loss_pct, help="Per-position stop loss, e.g. 0.10")
    p.add_argument("--trend-exit-ma", type=int, default=defaults.trend_exit_ma, help="Exit when price falls below MA window; 0 disables")
    p.add_argument("--regime-ma-window", type=int, default=defaults.regime_ma_window)
    p.add_argument("--regime-slope-window", type=int, default=defaults.regime_slope_window)
    p.add_argument("--regime-breadth-threshold", type=float, default=defaults.regime_breadth_threshold, help="Risk-on breadth threshold in [0,1]")
    p.add_argument("--vol-lookback", type=int, default=defaults.vol_lookback)
    p.add_argument("--target-vol-annual", type=float, default=defaults.target_vol_annual, help="Annualized target volatility; <=0 disables")
    p.add_argument("--max-weight", type=float, default=defaults.max_weight, help="Per-name cap; <=0 disables")
    p.add_argument("--min-gross-exposure", type=float, default=defaults.min_gross_exposure, help="Minimum invested exposure in risk-on, [0,1]")
    p.add_argument("--score-top-k", type=int, default=defaults.score_top_k, help="Top-K universe size for score-weight mode")
    p.add_argument("--score-power", type=float, default=defaults.score_power, help="Power transform for score-weight mode")
    p.add_argument("--regime-off-exposure", type=float, default=defaults.regime_off_exposure, help="Target gross exposure in risk-off regime")
    p.add_argument("--allow-intraperiod-reentry", type=int, default=defaults.allow_intraperiod_reentry, help="1 allows same-day re-entry after stop/trend exits")
    p.add_argument("--reentry-cooldown-days", type=int, default=defaults.reentry_cooldown_days, help="Trading-day cooldown after stop/trend exits")
    p.add_argument("--range-slope-threshold", type=float, default=defaults.range_slope_threshold)
    p.add_argument("--range-dist-threshold", type=float, default=defaults.range_dist_threshold)
    p.add_argument("--range-breakout-persistence-threshold", type=float, default=defaults.range_breakout_persistence_threshold)
    p.add_argument("--range-breadth-tolerance", type=float, default=defaults.range_breadth_tolerance)
    p.add_argument("--osc-lookback", type=int, default=defaults.osc_lookback)
    p.add_argument("--osc-z-entry", type=float, default=defaults.osc_z_entry)
    p.add_argument("--osc-z-exit", type=float, default=defaults.osc_z_exit)
    p.add_argument("--osc-z-stop", type=float, default=defaults.osc_z_stop)
    p.add_argument("--osc-band-sigma", type=float, default=defaults.osc_band_sigma)
    p.add_argument("--osc-band-break-sigma", type=float, default=defaults.osc_band_break_sigma)
    p.add_argument("--osc-reentry-cooldown-days", type=int, default=defaults.osc_reentry_cooldown_days)
    p.add_argument("--rotation-top-k", type=int, default=defaults.rotation_top_k)
    p.add_argument("--rotation-tilt-strength", type=float, default=defaults.rotation_tilt_strength)
    p.add_argument("--rotation-min-sleeve-weight", type=float, default=defaults.rotation_min_sleeve_weight)
    p.add_argument("--risk-budget-lookback", type=int, default=defaults.risk_budget_lookback)
    p.add_argument("--risk-budget-shrinkage", type=float, default=defaults.risk_budget_shrinkage)
    p.add_argument("--risk-budget-iv-blend", type=float, default=defaults.risk_budget_iv_blend)
    p.add_argument("--flow-base", type=str, default=defaults.flow_base)
    p.add_argument("--quality-base", type=str, default=defaults.quality_base)
    p.add_argument("--quality-hold-buffer", type=int, default=defaults.quality_hold_buffer)
    p.add_argument("--quality-trend-ma", type=int, default=defaults.quality_trend_ma)
    p.add_argument("--use-point-in-time-universe", type=int, default=defaults.use_point_in_time_universe)
    p.add_argument("--stock-universe-min-bars", type=int, default=defaults.stock_universe_min_bars)
    p.add_argument("--stock-universe-min-price", type=float, default=defaults.stock_universe_min_price)
    p.add_argument("--stock-universe-min-avg-value", type=float, default=defaults.stock_universe_min_avg_value)
    p.add_argument("--stock-universe-min-median-value", type=float, default=defaults.stock_universe_min_median_value)
    p.add_argument("--stock-universe-max-zero-days", type=int, default=defaults.stock_universe_max_zero_days)
    p.add_argument("--etf-universe-min-bars", type=int, default=defaults.etf_universe_min_bars)
    p.add_argument("--etf-universe-min-avg-value", type=float, default=defaults.etf_universe_min_avg_value)
    p.add_argument("--etf-universe-min-median-value", type=float, default=defaults.etf_universe_min_median_value)
    p.add_argument("--etf-universe-max-zero-days", type=int, default=defaults.etf_universe_max_zero_days)
    return p


def settings_from_args(args: argparse.Namespace) -> KISBacktestSettings:
    return KISBacktestSettings(**vars(args))
