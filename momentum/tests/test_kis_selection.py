from dataclasses import dataclass

import pandas as pd

from live_core.kis_selection import (
    OVERHEAT_CAUTION,
    OVERHEAT_NORMAL,
    OVERHEAT_OVERHEATED,
    add_scores,
    feature_frame_at,
    features,
    oscillation_candidates_at,
    rank_at,
    select_buffer,
)


@dataclass
class DummyStrategy:
    osc_lookback: int = 5
    osc_band_sigma: float = 1.5
    osc_band_break_sigma: float = 2.0
    osc_z_entry: float = -1.5
    mad_t2: float = 5.0


def test_add_scores_sets_overheat_buckets():
    frame = pd.DataFrame(
        {
            "r1": [10, 50, 5],
            "r3": [1, 1, 1],
            "r6": [1, 1, 1],
            "r12": [1, 1, 1],
            "avg_mom": [20, 20, 20],
            "mrat": [1.4, 2.4, 2.0],
            "mad_gap": [30, 101, 70],
        },
        index=["normal", "overheated", "caution"],
    )
    scored = add_scores(frame)
    assert scored.loc["normal", "overheat"] == OVERHEAT_NORMAL
    assert scored.loc["caution", "overheat"] == OVERHEAT_CAUTION
    assert scored.loc["overheated", "overheat"] == OVERHEAT_OVERHEATED


def test_select_buffer_keeps_prev_within_exit_rank():
    ranked = ["A", "B", "C", "D"]
    prev = ["D", "X"]
    selected = select_buffer(ranked, prev, top_n=3, use_buffer=True, entry_rank=2, exit_rank=4)
    assert selected == ["D", "A", "B"]


def test_rank_and_oscillation_candidates_filter_correctly():
    idx = pd.date_range("2024-01-01", periods=260, freq="B")
    close = pd.DataFrame(
        {
            "A": range(1, 261),
            "B": list(range(1, 256)) + [200, 180, 170, 165, 167],
        },
        index=idx,
        dtype=float,
    )
    feat = features(close, DummyStrategy())
    dt = idx[-1]

    ranked = rank_at(feat, dt)
    assert "A" in ranked.index

    frame = feature_frame_at(feat, dt)
    assert "buy_score" in frame.columns
    assert "overheat" in frame.columns

    osc_feat = {
        "r1": pd.DataFrame({"A": [5.0], "B": [-1.0]}, index=[dt]),
        "r3": pd.DataFrame({"A": [5.0], "B": [2.0]}, index=[dt]),
        "r6": pd.DataFrame({"A": [5.0], "B": [2.0]}, index=[dt]),
        "r12": pd.DataFrame({"A": [5.0], "B": [2.0]}, index=[dt]),
        "avg_mom": pd.DataFrame({"A": [5.0], "B": [1.0]}, index=[dt]),
        "mrat": pd.DataFrame({"A": [1.3], "B": [1.2]}, index=[dt]),
        "mad_gap": pd.DataFrame({"A": [10.0], "B": [1.0]}, index=[dt]),
        "ma60": pd.DataFrame({"A": [1.0], "B": [1.0]}, index=[dt]),
        "osc_mean": pd.DataFrame({"A": [1.0], "B": [1.0]}, index=[dt]),
        "osc_std": pd.DataFrame({"A": [1.0], "B": [1.0]}, index=[dt]),
        "osc_z": pd.DataFrame({"A": [-1.0], "B": [-2.0]}, index=[dt]),
        "osc_recovery": pd.DataFrame({"A": [1.0], "B": [1.0]}, index=[dt]),
        "osc_lower_band": pd.DataFrame({"A": [1.0], "B": [1.0]}, index=[dt]),
        "osc_break": pd.DataFrame({"A": [0.0], "B": [0.0]}, index=[dt]),
        "osc_break_persist": pd.DataFrame({"A": [0.0], "B": [0.0]}, index=[dt]),
    }
    eligible_mask = pd.DataFrame(True, index=close.index, columns=close.columns)
    eligible_mask.loc[dt, "A"] = False
    osc = oscillation_candidates_at(osc_feat, dt, DummyStrategy(), eligible_mask=eligible_mask)
    assert list(osc.index) == ["B"]
