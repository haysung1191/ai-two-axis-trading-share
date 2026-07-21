from types import SimpleNamespace

from live_core.kis_settings import KISBacktestSettings, build_arg_parser, settings_from_args


def test_settings_properties_expose_fee_and_regime_bool():
    settings = KISBacktestSettings(base="data/prices", flow_base="data/flows", quality_base="data/quality", fee_bps=12.5, regime_filter=0)

    assert settings.fee_rate == 0.00125
    assert settings.use_regime_filter_bool is False


def test_settings_from_args_builds_dataclass():
    args = SimpleNamespace(
        base="data/prices",
        top_n=10,
        fee_bps=8.0,
        max_files=5,
        save_prefix="out",
        min_common_dates=180,
        regime_filter=1,
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
        regime_off_exposure=0.4,
        allow_intraperiod_reentry=1,
        reentry_cooldown_days=0,
        range_slope_threshold=0.015,
        range_dist_threshold=0.03,
        range_breakout_persistence_threshold=0.35,
        range_breadth_tolerance=0.15,
        osc_lookback=20,
        osc_z_entry=-1.5,
        osc_z_exit=-0.25,
        osc_z_stop=-2.5,
        osc_band_sigma=1.5,
        osc_band_break_sigma=2.0,
        osc_reentry_cooldown_days=5,
        rotation_top_k=5,
        rotation_tilt_strength=0.2,
        rotation_min_sleeve_weight=0.25,
        risk_budget_lookback=120,
        risk_budget_shrinkage=0.35,
        risk_budget_iv_blend=0.5,
        flow_base="data/flows",
        quality_base="data/quality",
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
    )

    settings = settings_from_args(args)

    assert settings.base == "data/prices"
    assert settings.flow_base == "data/flows"
    assert settings.quality_base == "data/quality"
    assert settings.use_regime_filter_bool is True


def test_build_arg_parser_uses_injected_defaults():
    defaults = KISBacktestSettings(
        base="custom/prices",
        flow_base="custom/flows",
        quality_base="custom/quality",
        fee_bps=9.0,
        save_prefix="custom_out",
    )

    parser = build_arg_parser(defaults)
    parsed = parser.parse_args([])

    assert parsed.base == "custom/prices"
    assert parsed.flow_base == "custom/flows"
    assert parsed.quality_base == "custom/quality"
    assert parsed.save_prefix == "custom_out"
    assert parsed.fee_bps == 9.0
