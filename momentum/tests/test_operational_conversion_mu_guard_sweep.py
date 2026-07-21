from __future__ import annotations

import pandas as pd

from tools.analysis.analyze_split_models_operational_conversion_mu_guard_sweep import (
    _apply_mu_guard_to_book,
    _compose_variant_name,
)


def test_mu_guard_variant_name_encodes_parameters() -> None:
    variant_name = _compose_variant_name(0.11, 0.15)
    assert "muguard" in variant_name
    assert "mw11" in variant_name
    assert "trim15" in variant_name


def test_mu_guard_trims_mu_and_reallocates_to_kr_etf() -> None:
    book = pd.DataFrame(
        [
            {"Symbol": "MU", "Market": "US", "Sector": "Information Technology", "TargetWeight": 0.14, "MomentumScore": 9.0, "FlowScore": 8.0},
            {"Symbol": "AMD", "Market": "US", "Sector": "Information Technology", "TargetWeight": 0.28, "MomentumScore": 10.0, "FlowScore": 9.0},
            {"Symbol": "XLE", "Market": "US", "Sector": "Energy", "TargetWeight": 0.29, "MomentumScore": 8.0, "FlowScore": 7.0},
            {"Symbol": "069500", "Market": "KR", "Sector": "ETF", "TargetWeight": 0.16, "MomentumScore": 5.0, "FlowScore": 5.0},
            {"Symbol": "360750", "Market": "KR", "Sector": "ETF", "TargetWeight": 0.13, "MomentumScore": 4.0, "FlowScore": 4.0},
        ]
    )

    patched = _apply_mu_guard_to_book(book, 0.10, 0.10)
    mu_weight = float(patched.loc[patched["Symbol"] == "MU", "TargetWeight"].iloc[0])
    kr_etf_total = float(patched.loc[patched["Market"] == "KR", "TargetWeight"].sum())

    assert round(mu_weight, 6) == round(0.126, 6)
    assert round(kr_etf_total, 6) == round(0.304, 6)
    assert abs(float(patched["TargetWeight"].sum()) - 1.0) < 1e-9


def test_mu_guard_skips_when_mu_below_trigger() -> None:
    book = pd.DataFrame(
        [
            {"Symbol": "MU", "Market": "US", "Sector": "Information Technology", "TargetWeight": 0.14, "MomentumScore": 9.0, "FlowScore": 8.0},
            {"Symbol": "AMD", "Market": "US", "Sector": "Information Technology", "TargetWeight": 0.28, "MomentumScore": 10.0, "FlowScore": 9.0},
            {"Symbol": "XLE", "Market": "US", "Sector": "Energy", "TargetWeight": 0.29, "MomentumScore": 8.0, "FlowScore": 7.0},
            {"Symbol": "069500", "Market": "KR", "Sector": "ETF", "TargetWeight": 0.16, "MomentumScore": 5.0, "FlowScore": 5.0},
            {"Symbol": "360750", "Market": "KR", "Sector": "ETF", "TargetWeight": 0.13, "MomentumScore": 4.0, "FlowScore": 4.0},
        ]
    )

    patched = _apply_mu_guard_to_book(book, 0.20, 0.10)
    mu_weight = float(patched.loc[patched["Symbol"] == "MU", "TargetWeight"].iloc[0])
    assert round(mu_weight, 6) == round(0.14, 6)
