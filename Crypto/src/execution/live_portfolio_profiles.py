from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LivePortfolioProfile:
    name: str
    objective: str
    description: str
    partial_take_profit_pct: float
    full_take_profit_pct: float
    partial_stop_loss_pct: float
    full_stop_loss_pct: float
    partial_take_profit_fraction: float
    partial_stop_loss_fraction: float

    def to_state_payload(self) -> dict[str, Any]:
        return asdict(self)


LIVE_PORTFOLIO_PROFILES: dict[str, LivePortfolioProfile] = {
    "operating": LivePortfolioProfile(
        name="operating",
        objective="minimize_mdd",
        description="Capital-preservation profile with earlier profit capture and tighter stop discipline.",
        partial_take_profit_pct=0.015,
        full_take_profit_pct=0.03,
        partial_stop_loss_pct=0.01,
        full_stop_loss_pct=0.02,
        partial_take_profit_fraction=0.5,
        partial_stop_loss_fraction=0.5,
    ),
    "attack": LivePortfolioProfile(
        name="attack",
        objective="maximize_cagr",
        description="CAGR-first profile with wider upside target and slightly looser downside tolerance.",
        partial_take_profit_pct=0.02,
        full_take_profit_pct=0.05,
        partial_stop_loss_pct=0.012,
        full_stop_loss_pct=0.028,
        partial_take_profit_fraction=0.35,
        partial_stop_loss_fraction=0.5,
    ),
}


def resolve_live_portfolio_profile(
    profile_name: str,
    *,
    partial_take_profit_pct: float | None = None,
    full_take_profit_pct: float | None = None,
    partial_stop_loss_pct: float | None = None,
    full_stop_loss_pct: float | None = None,
    partial_take_profit_fraction: float | None = None,
    partial_stop_loss_fraction: float | None = None,
) -> LivePortfolioProfile:
    normalized_name = str(profile_name or "operating").strip().lower() or "operating"
    if normalized_name not in LIVE_PORTFOLIO_PROFILES:
        raise ValueError(f"unsupported live portfolio profile: {profile_name}")

    base = LIVE_PORTFOLIO_PROFILES[normalized_name]
    payload = base.to_state_payload()
    overrides = {
        "partial_take_profit_pct": partial_take_profit_pct,
        "full_take_profit_pct": full_take_profit_pct,
        "partial_stop_loss_pct": partial_stop_loss_pct,
        "full_stop_loss_pct": full_stop_loss_pct,
        "partial_take_profit_fraction": partial_take_profit_fraction,
        "partial_stop_loss_fraction": partial_stop_loss_fraction,
    }
    for key, value in overrides.items():
        if value is not None:
            payload[key] = float(value)
    return LivePortfolioProfile(**payload)
