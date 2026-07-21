from app.domains.strategy.loader import _safe_strategy_module_name, load_strategy


def test_strategy_loader_loads_example_strategy() -> None:
    strategy = load_strategy("mean_reversion")
    assert strategy.name == "mean_reversion"
    assert "window" in strategy.default_params
    assert "z_threshold" in strategy.default_params


def test_safe_strategy_module_name_avoids_windows_reserved_names() -> None:
    assert _safe_strategy_module_name("CON") == "strategy_CON"
    assert _safe_strategy_module_name("nul.py") == "strategy_nul.py"
