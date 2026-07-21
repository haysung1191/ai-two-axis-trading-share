from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

import config
from kis_api import KISApi
from tools.operations.execute_split_models_shadow_live_orders import (
    KR_SYMBOL_ALIASES,
    US_OVRS_EXCHANGE_BY_SYMBOL,
    US_PRICE_EXCHANGE_BY_OVRS,
    _resolve_kr_symbol,
    _resolve_us_exchange,
)


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_book(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["TargetWeight"] = pd.to_numeric(frame["TargetWeight"], errors="coerce").fillna(0.0)
    frame = frame[frame["TargetWeight"] > 0].copy()
    return frame.reset_index(drop=True)


def _safe_int(value: float) -> int:
    return int(math.floor(value)) if value >= 0 else 0


def build_capital_readiness(
    book: pd.DataFrame,
    api: KISApi,
    overrides: dict[str, str],
    total_capital: float | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    usd_krw_rate: float | None = None
    rows: list[dict[str, object]] = []

    for _, row in book.iterrows():
        market = str(row["Market"])
        symbol = str(row["Symbol"])
        target_weight = float(row["TargetWeight"])

        item: dict[str, object] = {
            "Market": market,
            "AssetType": row.get("AssetType"),
            "Symbol": symbol,
            "ResolvedSymbol": symbol,
            "Name": row.get("Name"),
            "Sector": row.get("Sector"),
            "TargetWeight": target_weight,
            "ResolvedExchange": "",
            "ResolvedPrice": pd.NA,
            "FXRate": pd.NA,
            "OneShareCostKRW": pd.NA,
            "MinTotalCapitalForOneShareKRW": pd.NA,
            "Status": "READY",
            "Reason": "",
        }

        try:
            if target_weight <= 0:
                raise ValueError("non_positive_target_weight")

            if market == "KR":
                resolved_symbol = _resolve_kr_symbol(symbol, overrides)
                if resolved_symbol is None:
                    raise ValueError("invalid_kr_symbol")
                quote = api.get_domestic_quote(resolved_symbol)
                one_share_cost_krw = float(quote["price"])
                item["ResolvedSymbol"] = resolved_symbol
                item["ResolvedExchange"] = "KRX"
                item["ResolvedPrice"] = one_share_cost_krw
            elif market == "US":
                ovrs_exchange = _resolve_us_exchange(symbol, overrides)
                if ovrs_exchange is None:
                    raise ValueError("missing_us_exchange_mapping")
                price_exchange = US_PRICE_EXCHANGE_BY_OVRS[ovrs_exchange]
                quote = api.get_overseas_quote(price_exchange, symbol)
                if usd_krw_rate is None:
                    usd_krw_rate = float(api.get_usd_krw_rate())
                one_share_cost_krw = float(quote["price"]) * usd_krw_rate
                item["ResolvedExchange"] = ovrs_exchange
                item["ResolvedPrice"] = float(quote["price"])
                item["FXRate"] = usd_krw_rate
            else:
                raise ValueError(f"unsupported_market:{market}")

            min_total_capital = int(math.ceil(one_share_cost_krw / target_weight))
            item["OneShareCostKRW"] = one_share_cost_krw
            item["MinTotalCapitalForOneShareKRW"] = min_total_capital

            if total_capital is not None:
                target_budget = float(total_capital) * target_weight
                max_shares = _safe_int(target_budget / one_share_cost_krw)
                item["TargetBudgetKRW"] = target_budget
                item["MaxSharesAtCapital"] = max_shares
                item["FundableAtCapital"] = bool(max_shares >= 1)
        except Exception as exc:  # noqa: BLE001
            item["Status"] = "BLOCKED"
            item["Reason"] = str(exc)
            if total_capital is not None:
                item["TargetBudgetKRW"] = float(total_capital) * target_weight
                item["MaxSharesAtCapital"] = pd.NA
                item["FundableAtCapital"] = False

        rows.append(item)

    details = pd.DataFrame(rows)
    ready = details[details["Status"] == "READY"].copy()

    summary: dict[str, object] = {
        "kis_env": config.ENV,
        "holdings_considered": int(len(details)),
        "ready_count": int((details["Status"] == "READY").sum()),
        "blocked_count": int((details["Status"] == "BLOCKED").sum()),
        "usd_krw_rate": usd_krw_rate,
        "blocked_reasons": sorted({reason for reason in details["Reason"].fillna("").tolist() if reason}),
    }

    if not ready.empty:
        summary["min_capital_all_holdings_one_share_krw"] = int(ready["MinTotalCapitalForOneShareKRW"].max())
        summary["max_single_name_one_share_cost_krw"] = float(ready["OneShareCostKRW"].max())
    else:
        summary["min_capital_all_holdings_one_share_krw"] = None
        summary["max_single_name_one_share_cost_krw"] = None

    if total_capital is not None:
        summary["evaluated_total_capital"] = float(total_capital)
        if "FundableAtCapital" in details.columns:
            fundable = details["FundableAtCapital"].fillna(False)
            summary["fundable_count_at_capital"] = int(fundable.sum())
            summary["unfundable_count_at_capital"] = int((~fundable).sum())
            summary["fundable_symbols_at_capital"] = details.loc[fundable, "Symbol"].tolist()

    return details, summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book-path", default=str(SHADOW_DIR / "shadow_current_book.csv"))
    parser.add_argument("--details-path", default=str(SHADOW_DIR / "shadow_capital_readiness.csv"))
    parser.add_argument("--summary-path", default=str(SHADOW_DIR / "shadow_capital_readiness_summary.json"))
    parser.add_argument("--exchange-overrides-json", default="")
    parser.add_argument("--total-capital", type=float, default=None)
    args = parser.parse_args(argv)

    overrides = json.loads(args.exchange_overrides_json) if args.exchange_overrides_json else {}
    book = _load_book(Path(args.book_path))
    api = KISApi()
    details, summary = build_capital_readiness(book, api, overrides, total_capital=args.total_capital)

    details_path = Path(args.details_path)
    details_path.parent.mkdir(parents=True, exist_ok=True)
    details.to_csv(details_path, index=False, encoding="utf-8-sig")

    Path(args.summary_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
