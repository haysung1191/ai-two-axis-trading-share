from __future__ import annotations

from scripts.validate_btc_1d_low_vol_cap_friction import build_parser


def test_btc_1d_low_vol_cap_friction_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.periods == 2200
    assert args.cost_levels_bps == [0.0, 8.0, 12.0, 20.0]
