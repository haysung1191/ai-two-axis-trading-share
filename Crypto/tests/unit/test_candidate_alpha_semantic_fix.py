from __future__ import annotations

import pandas as pd

from scripts.candidate_alpha_semantic_fix import build_candidate_alpha_semantic_memo


def test_candidate_alpha_semantic_memo_detects_inverted_relationship() -> None:
    n = 96
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    tradable = [(i % 3) != 0 for i in range(n)]
    forward_return_1h = [0.002 if not value else -0.001 for value in tradable]
    forward_return_4h = [0.004 if not value else -0.002 for value in tradable]
    forward_vol_1h = [0.004 if not value else 0.003 for value in tradable]
    forward_vol_4h = [0.005 if not value else 0.004 for value in tradable]
    frame = pd.DataFrame(
        {
            "tradable_regime": tradable,
            "avoidance_regime": [not value for value in tradable],
            "dislocation_std_72": [1.0] * n,
            "delta_dislocation_std_72": [1.0] * n,
            "krw_usdt_abs_return_mean_72": [1.0] * n,
            "forward_return_1h": forward_return_1h,
            "forward_return_4h": forward_return_4h,
            "forward_vol_1h": forward_vol_1h,
            "forward_vol_4h": forward_vol_4h,
        },
        index=idx,
    )

    memo = build_candidate_alpha_semantic_memo(frame, chunks=3)

    assert memo["interpretation"]["likely_real_signal"] is True
    assert memo["interpretation"]["invert_label_semantics"] is True
    assert memo["final_decision"] == "continue but redefine as avoidance-regime detection"
