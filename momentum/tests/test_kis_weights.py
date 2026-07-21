from types import SimpleNamespace

import pandas as pd

from live_core.kis_weights import (
    cap_weights_to_target,
    inverse_vol_weights,
    risk_budget_weights,
    score_weights_from_rank,
)


def _strategy(**overrides):
    kwargs = {
        "risk_budget_shrinkage": 0.35,
        "risk_budget_iv_blend": 0.25,
        "score_top_k": 3,
        "score_power": 1.5,
        "mad_t1": 2.0,
        "mad_t2": 5.0,
        "mad_t3": 10.0,
        "mad_w1": 1.2,
        "mad_w2": 1.0,
        "mad_w3": 0.7,
        "mad_w4": 0.4,
    }
    kwargs.update(overrides)
    return SimpleNamespace(**kwargs)


def test_inverse_vol_weights_normalizes_and_prefers_lower_vol():
    ret_window = pd.DataFrame(
        {
            "AAA": [0.01, -0.01, 0.01, -0.01],
            "BBB": [0.04, -0.04, 0.04, -0.04],
        }
    )

    weights = inverse_vol_weights(ret_window, ["AAA", "BBB"])

    assert round(sum(weights.values()), 10) == 1.0
    assert weights["AAA"] > weights["BBB"]


def test_cap_weights_to_target_enforces_cap_and_target():
    weights = {"AAA": 0.8, "BBB": 0.2}

    capped = cap_weights_to_target(weights, max_weight=0.5, target_gross=1.0)

    assert round(sum(capped.values()), 10) == 1.0
    assert capped["AAA"] == 0.5
    assert capped["BBB"] == 0.5


def test_risk_budget_weights_returns_positive_normalized_weights():
    ret_window = pd.DataFrame(
        {
            "AAA": [0.01, 0.00, 0.02, -0.01, 0.01, 0.00, 0.01, -0.01, 0.02, 0.00],
            "BBB": [0.02, -0.01, 0.01, 0.00, 0.01, -0.02, 0.01, 0.00, 0.01, -0.01],
            "CCC": [0.03, -0.02, 0.02, 0.01, 0.00, -0.01, 0.02, 0.01, 0.00, -0.01],
        }
    )

    weights = risk_budget_weights(ret_window, ["AAA", "BBB", "CCC"], _strategy())

    assert set(weights) == {"AAA", "BBB", "CCC"}
    assert round(sum(weights.values()), 10) == 1.0
    assert all(v > 0 for v in weights.values())


def test_score_weights_from_rank_uses_buy_score_and_mad_gap():
    df_rank = pd.DataFrame(
        {
            "buy_score": [5.0, 4.0, 2.0],
            "mad_gap": [1.0, 6.0, 12.0],
        },
        index=["AAA", "BBB", "CCC"],
    )

    weights = score_weights_from_rank(df_rank, _strategy())

    assert round(sum(weights.values()), 10) == 1.0
    assert weights["AAA"] > weights["BBB"] > weights["CCC"]
