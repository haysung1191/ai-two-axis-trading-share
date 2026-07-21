from argparse import Namespace
from dataclasses import dataclass

from live_core.kis_strategy_config import build_default_strategies, strategy_runtime_kwargs


@dataclass
class DummyStrategy:
    name: str
    rebalance: str
    top_n_stock: int
    top_n_etf: int
    fee_rate: float
    use_buffer: bool = False
    entry_rank: int = 20
    exit_rank: int = 25
    use_regime_filter: bool = False
    stop_loss_pct: float = 0.0
    trend_exit_ma: int = 0
    regime_ma_window: int = 200
    regime_slope_window: int = 20
    regime_breadth_threshold: float = 0.55
    vol_lookback: int = 20
    target_vol_annual: float = 0.20
    max_weight: float = 0.20
    min_gross_exposure: float = 0.50
    selection_mode: str = "topn"
    score_top_k: int = 50
    score_power: float = 1.5
    regime_off_exposure: float = 0.40
    allow_intraperiod_reentry: bool = True
    reentry_cooldown_days: int = 0
    use_regime_state_model: bool = False
    enable_oscillation_long: bool = False
    osc_lookback: int = 20
    osc_z_entry: float = -1.5
    osc_z_exit: float = -0.25
    osc_z_stop: float = -2.5
    osc_band_sigma: float = 1.5
    osc_band_break_sigma: float = 2.0
    osc_reentry_cooldown_days: int = 5
    range_slope_threshold: float = 0.015
    range_dist_threshold: float = 0.03
    range_breakout_persistence_threshold: float = 0.35
    range_breadth_tolerance: float = 0.15
    use_rotation_overlay: bool = False
    rotation_top_k: int = 5
    rotation_tilt_strength: float = 0.20
    rotation_min_sleeve_weight: float = 0.25
    fixed_sleeve_weights: dict | None = None
    use_etf_risk_budget: bool = False
    risk_budget_lookback: int = 120
    risk_budget_shrinkage: float = 0.35
    risk_budget_iv_blend: float = 0.50
    use_foreign_flow_model: bool = False
    flow_model_version: int = 2
    flow_hold_buffer: int = 10
    flow_trend_ma: int = 60
    flow_foreign_ratio_cap: float = 40.0
    flow_foreign_ratio_penalty: float = 0.50
    use_quality_profitability_model: bool = False
    quality_hold_buffer: int = 10
    quality_trend_ma: int = 60
    use_point_in_time_universe: bool = True
    stock_universe_min_bars: int = 750
    stock_universe_min_price: float = 1000.0
    stock_universe_min_avg_value: float = 5_000_000_000.0
    stock_universe_min_median_value: float = 2_000_000_000.0
    stock_universe_max_zero_days: int = 1
    etf_universe_min_bars: int = 180
    etf_universe_min_avg_value: float = 500_000_000.0
    etf_universe_min_median_value: float = 100_000_000.0
    etf_universe_max_zero_days: int = 1


def _args() -> Namespace:
    return Namespace(
        top_n=20,
        stop_loss_pct=0.12,
        trend_exit_ma=60,
        regime_ma_window=200,
        regime_slope_window=20,
        regime_breadth_threshold=0.55,
        vol_lookback=20,
        target_vol_annual=0.2,
        max_weight=0.2,
        min_gross_exposure=0.5,
        score_top_k=50,
        score_power=1.5,
        allow_intraperiod_reentry=1,
        reentry_cooldown_days=0,
        osc_lookback=20,
        osc_z_entry=-1.5,
        osc_z_exit=-0.25,
        osc_z_stop=-2.5,
        osc_band_sigma=1.5,
        osc_band_break_sigma=2.0,
        osc_reentry_cooldown_days=5,
        range_slope_threshold=0.015,
        range_dist_threshold=0.03,
        range_breakout_persistence_threshold=0.35,
        range_breadth_tolerance=0.15,
        rotation_top_k=5,
        rotation_tilt_strength=0.2,
        rotation_min_sleeve_weight=0.25,
        risk_budget_lookback=120,
        risk_budget_shrinkage=0.35,
        risk_budget_iv_blend=0.5,
        quality_hold_buffer=10,
        quality_trend_ma=60,
        use_point_in_time_universe=1,
        stock_universe_min_bars=750,
        stock_universe_min_price=1000.0,
        stock_universe_min_avg_value=5_000_000_000.0,
        stock_universe_min_median_value=2_000_000_000.0,
        stock_universe_max_zero_days=1,
        etf_universe_min_bars=180,
        etf_universe_min_avg_value=500_000_000.0,
        etf_universe_min_median_value=100_000_000.0,
        etf_universe_max_zero_days=1,
        regime_off_exposure=0.4,
    )


def test_strategy_runtime_kwargs_smoke():
    args = _args()
    kwargs = strategy_runtime_kwargs(args, fee_rate=0.001, use_regime_filter=True)
    assert kwargs["top_n_stock"] == 20
    assert kwargs["fee_rate"] == 0.001
    assert kwargs["use_regime_filter"] is True
    assert kwargs["allow_intraperiod_reentry"] is True
    assert kwargs["risk_budget_lookback"] == 120


def test_build_default_strategies_smoke():
    args = _args()
    strategies = build_default_strategies(args, DummyStrategy, fee_rate=0.001, use_regime_filter=True)
    assert len(strategies) == 16
    assert strategies[0].name == "Daily Top20"
    assert strategies[0].fee_rate == 0.001
    etf_risk_budget = next(s for s in strategies if s.name == "Weekly ETF RiskBudget")
    assert etf_risk_budget.use_etf_risk_budget is True
    assert etf_risk_budget.max_weight == 0.35
    foreign_flow = next(s for s in strategies if s.name == "Weekly ForeignFlow v2")
    assert foreign_flow.use_foreign_flow_model is True
    assert foreign_flow.score_top_k == 20
