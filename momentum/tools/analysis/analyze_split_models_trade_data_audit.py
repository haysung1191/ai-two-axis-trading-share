from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys
from typing import Callable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, TradingVariant, _price_path, _read_daily_frame
from tools.analysis.analyze_split_models_tradeoff_frontier import (
    BASE_VARIANT_NAME,
    _baseline_variant_map,
    _build_context,
    _patch_bonus_recipients,
    _patch_hybrid_top2_plus_third,
    _patch_multi_step_confirm_top1_flowtop2,
    _patch_regime_weight_defensive_if_top2flowsoft,
    _patch_skip_entry_flowweakest_new_bottom4_top25_mid75,
    _patch_tail_release_top50_mid50,
    _run_with_patch,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_trade_data_audit"


def _variant_specs(strongest: TradingVariant) -> list[tuple[str, TradingVariant, Callable[[pd.DataFrame], pd.DataFrame] | None]]:
    return [
        ("strongest", strongest, None),
        ("broader", replace(strongest, name="hybrid_top2_plus_third00125"), _patch_hybrid_top2_plus_third(0.00125)),
        ("quality", replace(strongest, name="bonus_recipient_top1_third_85_15"), _patch_bonus_recipients(0.85, 0.15)),
        (
            "headline",
            replace(strongest, name="tail_skip_entry_flowweakest_new_bottom4_top25_mid75"),
            _patch_skip_entry_flowweakest_new_bottom4_top25_mid75(),
        ),
        (
            "defensive_weighting",
            replace(strongest, name="regime_weight_defensive_if_top2flowsoft"),
            _patch_regime_weight_defensive_if_top2flowsoft(),
        ),
        (
            "stronger_but_more_fragile",
            replace(strongest, name="multi_step_confirm_top1_flowtop2"),
            _patch_multi_step_confirm_top1_flowtop2(),
        ),
        (
            "redistribution",
            replace(strongest, name="tail_release_top50_mid50"),
            _patch_tail_release_top50_mid50(),
        ),
    ]


def _latest_book(positions: pd.DataFrame) -> pd.DataFrame:
    if positions.empty:
        return pd.DataFrame()
    out = positions.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    latest = out["SignalDate"].max()
    return out[out["SignalDate"].eq(latest)].sort_values("TargetWeight", ascending=False).reset_index(drop=True)


def _previous_book(positions: pd.DataFrame) -> pd.DataFrame:
    if positions.empty:
        return pd.DataFrame()
    out = positions.copy()
    out["SignalDate"] = pd.to_datetime(out["SignalDate"])
    unique_dates = sorted(out["SignalDate"].dropna().unique())
    if len(unique_dates) < 2:
        return pd.DataFrame()
    prev_date = unique_dates[-2]
    return out[out["SignalDate"].eq(prev_date)].sort_values("TargetWeight", ascending=False).reset_index(drop=True)


def _transition_summary(positions: pd.DataFrame) -> dict[str, object]:
    latest = _latest_book(positions)
    previous = _previous_book(positions)
    if latest.empty:
        return {
            "latest_signal_date": None,
            "latest_next_date": None,
            "holdings": [],
            "entered_symbols": [],
            "exited_symbols": [],
        }
    latest_symbols = set(latest["Symbol"].astype(str))
    prev_symbols = set(previous["Symbol"].astype(str)) if not previous.empty else set()
    entered = sorted(latest_symbols - prev_symbols)
    exited = sorted(prev_symbols - latest_symbols)
    holdings = [
        {
            "market": str(row.Market),
            "symbol": str(row.Symbol),
            "name": str(row.Name),
            "sector": str(row.Sector),
            "target_weight": round(float(row.TargetWeight), 6),
            "momentum_score": round(float(row.MomentumScore), 6),
            "flow_score": round(float(row.FlowScore), 6) if pd.notna(row.FlowScore) else None,
        }
        for row in latest.itertuples(index=False)
    ]
    return {
        "latest_signal_date": str(pd.to_datetime(latest.iloc[0]["SignalDate"]).date()),
        "latest_next_date": str(pd.to_datetime(latest.iloc[0]["NextDate"]).date()),
        "holdings": holdings,
        "entered_symbols": entered,
        "exited_symbols": exited,
    }


def _price_audit_sample(book: pd.DataFrame) -> list[dict[str, object]]:
    if book.empty:
        return []
    rows: list[dict[str, object]] = []
    sample = book.head(min(5, len(book))).copy()
    for row in sample.itertuples(index=False):
        path = _price_path(pd.Series(row._asdict()))
        df = _read_daily_frame(path)
        rows.append(
            {
                "market": str(row.Market),
                "asset_type": str(row.AssetType),
                "symbol": str(row.Symbol),
                "name": str(row.Name),
                "price_path": str(path),
                "file_exists": bool(path.exists()),
                "rows": 0 if df is None else int(len(df)),
                "start_date": None if df is None or df.empty else str(pd.to_datetime(df["date"].min()).date()),
                "end_date": None if df is None or df.empty else str(pd.to_datetime(df["date"].max()).date()),
                "nonpositive_close_rows": 0 if df is None else int((pd.to_numeric(df["close"], errors="coerce") <= 0).sum()),
                "duplicate_date_rows": 0 if df is None else int(df.duplicated(subset=["date"]).sum()),
            }
        )
    return rows


def _today_work_summary() -> list[str]:
    return [
        "tradeoff frontier refresh",
        "quality-vs-headline refresh",
        "nightly safe summary",
        "overnight guardrail",
        "quality recipient family review",
        "promotion defense refresh",
        "dead family ledger refresh",
        "redistribution family saturation review",
        "tail-rescue saturation fix",
        "many inline genuinely-different family validations",
    ]


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Trade And Data Audit",
        "",
        "## Today Work",
        "",
    ]
    for item in summary["today_work"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Price Data Source",
            "",
            "- US stocks: `data/prices_us_stock_sp100_pitwiki/stock/*.csv.gz`",
            "- US ETFs: `data/prices_us_etf_core/etf/*.csv.gz`",
            "- KR stocks and ETFs: `data/prices_operating_institutional_v1/{stock,etf}/*.csv.gz`",
            "- KR stock flows: `data/flows_operating_institutional_v1/stock/*.csv.gz`",
            "",
            "## Model Trade Snapshot",
            "",
        ]
    )

    for model in summary["models"]:
        lines.extend(
            [
                f"- {model['label']}: `{model['variant']}`",
                f"  - latest signal date: `{model['latest_signal_date']}`",
                f"  - latest next date: `{model['latest_next_date']}`",
                f"  - entered: `{', '.join(model['entered_symbols']) if model['entered_symbols'] else 'none'}`",
                f"  - exited: `{', '.join(model['exited_symbols']) if model['exited_symbols'] else 'none'}`",
            ]
        )
        for holding in model["holdings"][:5]:
            lines.append(
                "  - holding: "
                f"`{holding['market']}:{holding['symbol']}` "
                f"`{holding['name']}` "
                f"weight `{holding['target_weight']:.4f}` "
                f"mom `{holding['momentum_score']:.4f}` "
                f"flow `{holding['flow_score'] if holding['flow_score'] is not None else 'na'}`"
            )

    lines.extend(["", "## Price File Audit", ""])
    for row in summary["price_audit"]:
        lines.extend(
            [
                f"- `{row['market']}:{row['symbol']}` `{row['name']}`",
                f"  - path: `{row['price_path']}`",
                f"  - exists: `{row['file_exists']}`",
                f"  - rows: `{row['rows']}`",
                f"  - range: `{row['start_date']} -> {row['end_date']}`",
                f"  - nonpositive close rows: `{row['nonpositive_close_rows']}`",
                f"  - duplicate date rows: `{row['duplicate_date_rows']}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            "- future review should include both current holdings and entered/exited symbols, not just performance deltas",
            "- backtest price data is local cached csv.gz data, so trust should be based on file-level auditability rather than assumption",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    strongest = _baseline_variant_map()[BASE_VARIANT_NAME]

    model_rows: list[dict[str, object]] = []
    strongest_book_for_audit = pd.DataFrame()

    for label, variant, patch_fn in _variant_specs(strongest):
        result = _run_with_patch(
            variant,
            patch_fn,
            universe,
            price_cache,
            flow_cache,
            monthly_close,
            signal_dates,
            cfg,
        )
        transition = _transition_summary(result["positions"])
        model_rows.append(
            {
                "label": label,
                "variant": variant.name,
                **transition,
            }
        )
        if label == "strongest":
            strongest_book_for_audit = _latest_book(result["positions"])

    summary = {
        "as_of_date": "2026-04-17",
        "repo": "momentum",
        "asset_class": "stocks_etfs",
        "today_work": _today_work_summary(),
        "models": model_rows,
        "price_audit": _price_audit_sample(strongest_book_for_audit),
    }

    (OUTPUT_DIR / "trade_data_audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "trade_data_audit.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
