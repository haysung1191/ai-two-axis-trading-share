import argparse
import math
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd


CANONICAL_UNIVERSE = [
    "SPY",
    "QQQ",
    "IWM",
    "EFA",
    "EEM",
    "VNQ",
    "GLD",
    "PDBC",
    "HYG",
    "IEF",
    "TLT",
    "BIL",
]


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def build_template(path: Path) -> pd.DataFrame:
    cash_col = [0.0] + [""] * (len(CANONICAL_UNIVERSE) - 1)
    template = pd.DataFrame(
        {
            "Ticker": CANONICAL_UNIVERSE,
            "CurrentShares": [0.0] * len(CANONICAL_UNIVERSE),
            "CurrentCash": cash_col,
            "Notes": [""] * len(CANONICAL_UNIVERSE),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(path, index=False, encoding="utf-8-sig")
    return template


def load_latest_prices(price_base: Path) -> tuple[dict[str, float], list[str]]:
    prices: dict[str, float] = {}
    issues: list[str] = []
    for ticker in CANONICAL_UNIVERSE:
        path = price_base / "etf" / f"{ticker}.csv.gz"
        if not path.exists():
            issues.append(f"missing price file: {ticker}")
            continue
        df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        if df.empty:
            issues.append(f"empty price file: {ticker}")
            continue
        price = pd.to_numeric(df["close"], errors="coerce").iloc[-1]
        if pd.isna(price) or float(price) <= 0:
            issues.append(f"invalid latest price: {ticker}")
            continue
        prices[ticker] = float(price)
    return prices, issues


def validate_batch2(target: pd.DataFrame, decision: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    if decision.empty:
        issues.append("missing decision summary")
        return issues
    if target.empty and str(decision.iloc[0].get("Decision", "")) != "STOP":
        issues.append("missing target portfolio")
    if str(decision.iloc[0].get("Decision", "")) != "GO":
        issues.append("batch2 decision is not GO")
    if not target.empty:
        bad = sorted(set(target["Ticker"].astype(str)) - set(CANONICAL_UNIVERSE))
        if bad:
            issues.append(f"target contains non-canonical tickers: {','.join(bad)}")
        weight_sum = float(pd.to_numeric(target["TargetWeight"], errors="coerce").fillna(0.0).sum())
        if abs(weight_sum - 1.0) > 1e-9:
            issues.append("target weights do not sum to 1")
    return issues


def prepare_account_state(current: pd.DataFrame) -> tuple[pd.DataFrame, float, list[str]]:
    issues: list[str] = []
    if current.empty:
        issues.append("current holdings template is empty")
        return current, 0.0, issues
    required_cols = {"Ticker", "CurrentShares", "CurrentCash", "Notes"}
    if not required_cols.issubset(set(current.columns)):
        issues.append("account-state input missing required columns")
        return current, 0.0, issues
    current = current.copy()
    current["Ticker"] = current["Ticker"].astype(str)
    bad = sorted(set(current["Ticker"]) - set(CANONICAL_UNIVERSE))
    if bad:
        issues.append(f"current holdings contains non-canonical tickers: {','.join(bad)}")
    current = current.drop_duplicates(subset=["Ticker"], keep="last").reset_index(drop=True)
    missing = sorted(set(CANONICAL_UNIVERSE) - set(current["Ticker"]))
    if missing:
        current = pd.concat(
            [
                current,
                pd.DataFrame(
                    {
                        "Ticker": missing,
                        "CurrentShares": [0.0] * len(missing),
                        "CurrentCash": [""] * len(missing),
                        "Notes": [""] * len(missing),
                    }
                ),
            ],
            ignore_index=True,
        )
    current["CurrentShares"] = pd.to_numeric(current["CurrentShares"], errors="coerce").fillna(0.0)
    current["Notes"] = current["Notes"].fillna("").astype(str)

    cash_series = pd.to_numeric(current["CurrentCash"], errors="coerce")
    cash_values = sorted({round(float(v), 10) for v in cash_series.dropna().tolist()})
    if len(cash_values) == 0:
        issues.append("account-state input missing current cash value")
        account_cash = 0.0
    elif len(cash_values) > 1:
        issues.append("account-state input contains inconsistent current cash values")
        account_cash = float(cash_values[0])
    else:
        account_cash = float(cash_values[0])
    current["CurrentCash"] = account_cash
    if account_cash < 0:
        issues.append("current cash cannot be negative")
    return current.sort_values("Ticker").reset_index(drop=True), account_cash, issues


def build_order_sheet(
    current: pd.DataFrame, target: pd.DataFrame, prices: dict[str, float], signal_date: str, account_cash: float
) -> tuple[pd.DataFrame, list[str]]:
    issues: list[str] = []
    target_map = {
        str(row["Ticker"]): float(row["TargetWeight"])
        for _, row in target.iterrows()
    }
    rows = []
    current = current.copy()
    current["LatestPrice"] = current["Ticker"].map(prices)
    current["CurrentMarketValue"] = current["CurrentShares"] * current["LatestPrice"]
    holdings_notional = float(current["CurrentMarketValue"].fillna(0.0).sum())
    total_capital = holdings_notional + float(account_cash)
    if total_capital > 0:
        current["CurrentWeight"] = current["CurrentMarketValue"] / total_capital
    else:
        issues.append("total account capital must be positive for practical sizing")
        current["CurrentWeight"] = 0.0

    for _, row in current.sort_values("Ticker").iterrows():
        ticker = str(row["Ticker"])
        current_shares = int(round(float(row["CurrentShares"])))
        latest_price = float(row["LatestPrice"])
        current_market_value = float(row["CurrentMarketValue"])
        current_weight = float(row["CurrentWeight"])
        target_weight = float(target_map.get(ticker, 0.0))
        target_notional = total_capital * target_weight if total_capital > 0 else 0.0
        target_shares = int(math.floor((target_notional / latest_price) + 1e-12)) if latest_price > 0 else 0
        share_delta = target_shares - current_shares
        if current_shares <= 0 and target_shares > 0:
            action = "ENTER"
        elif current_shares > 0 and target_shares <= 0:
            action = "EXIT"
        elif share_delta > 0:
            action = "BUY"
        elif share_delta < 0:
            action = "SELL"
        else:
            action = "KEEP"
        notes = str(row.get("Notes", "")).strip()
        notes = "; ".join(filter(None, [notes, "sized_from_account_total_capital"]))
        rows.append(
            {
                "SignalDate": signal_date,
                "Ticker": ticker,
                "CurrentShares": current_shares,
                "LatestPrice": latest_price,
                "CurrentMarketValue": current_market_value,
                "CurrentWeight": current_weight,
                "TargetWeight": target_weight,
                "TargetNotional": target_notional,
                "ShareDelta": share_delta,
                "Action": action,
                "Notes": notes,
            }
        )
    return pd.DataFrame(rows), issues


def build_stop_outputs(reason: str, signal_date: str | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    safe_date = signal_date or ""
    order_sheet = pd.DataFrame(
        columns=[
            "SignalDate",
            "Ticker",
            "CurrentShares",
            "LatestPrice",
            "CurrentMarketValue",
            "CurrentWeight",
            "TargetWeight",
            "TargetNotional",
            "ShareDelta",
            "Action",
            "Notes",
        ]
    )
    review = pd.DataFrame(
        [
            {
                "Decision": "STOP",
                "SignalDate": safe_date,
                "OrderSheetStatus": "STOP",
                "CanonicalUniverseCheck": 0,
                "TargetMatchCheck": 0,
                "BlockingReason": reason,
            }
        ]
    )
    return order_sheet, review


def build_review(order_sheet: pd.DataFrame, target: pd.DataFrame, signal_date: str) -> tuple[pd.DataFrame, list[str]]:
    issues: list[str] = []
    if order_sheet.empty:
        issues.append("empty order sheet")
    canonical_ok = int(set(order_sheet["Ticker"].astype(str)) == set(CANONICAL_UNIVERSE)) if not order_sheet.empty else 0
    target_map = {ticker: 0.0 for ticker in CANONICAL_UNIVERSE}
    order_map = {ticker: 0.0 for ticker in CANONICAL_UNIVERSE}
    if not target.empty:
        for _, row in target.iterrows():
            target_map[str(row["Ticker"])] = float(row["TargetWeight"])
    if not order_sheet.empty:
        for _, row in order_sheet.iterrows():
            order_map[str(row["Ticker"])] = float(row["TargetWeight"])
    target_match = int(
        all(abs(float(target_map[ticker]) - float(order_map[ticker])) <= 1e-9 for ticker in CANONICAL_UNIVERSE)
    )
    if canonical_ok != 1:
        issues.append("order sheet contains non-canonical tickers")
    if target_match != 1:
        issues.append("order sheet does not match target portfolio")
    if not order_sheet.empty:
        total_market_value = float(pd.to_numeric(order_sheet["CurrentMarketValue"], errors="coerce").fillna(0.0).sum())
        total_target_notional = float(pd.to_numeric(order_sheet["TargetNotional"], errors="coerce").fillna(0.0).sum())
        inferred_total_capital = 0.0
        positive_targets = order_sheet[pd.to_numeric(order_sheet["TargetWeight"], errors="coerce").fillna(0.0) > 0]
        if not positive_targets.empty:
            inferred_total_capital = float(
                positive_targets.iloc[0]["TargetNotional"] / positive_targets.iloc[0]["TargetWeight"]
            )
        if inferred_total_capital <= 0:
            issues.append("total account capital must be positive")
        if inferred_total_capital > 0 and not (
            0 <= inferred_total_capital - total_target_notional < float(order_sheet["LatestPrice"].max()) + 1e-9
        ):
            issues.append("target notionals do not map cleanly from total account capital")
        for _, row in order_sheet.iterrows():
            delta = float(row["ShareDelta"])
            action = str(row["Action"])
            if delta > 0 and action not in {"BUY", "ENTER"}:
                issues.append(f"share delta/action mismatch: {row['Ticker']}")
                break
            if delta < 0 and action not in {"SELL", "EXIT"}:
                issues.append(f"share delta/action mismatch: {row['Ticker']}")
                break
            if abs(delta) <= 1e-9 and action != "KEEP":
                issues.append(f"share delta/action mismatch: {row['Ticker']}")
                break
    review = pd.DataFrame(
        [
            {
                "Decision": "GO" if not issues else "STOP",
                "SignalDate": signal_date,
                "OrderSheetStatus": "READY" if not issues else "STOP",
                "CanonicalUniverseCheck": canonical_ok,
                "TargetMatchCheck": target_match,
                "BlockingReason": "; ".join(issues),
            }
        ]
    )
    return review, issues


def write_outputs(output_dir: Path, template: pd.DataFrame, order_sheet: pd.DataFrame, review: pd.DataFrame) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    template.to_csv(output_dir / "account_state_template.csv", index=False, encoding="utf-8-sig")
    order_sheet.to_csv(output_dir / "order_sheet.csv", index=False, encoding="utf-8-sig")
    review.to_csv(output_dir / "manual_execution_review.csv", index=False, encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch 3 manual trading layer for US ETF dual momentum MVP v1.")
    p.add_argument("--batch2-dir", type=str, default="backtests/us_etf_dual_momentum_mvp_v1_batch2")
    p.add_argument("--price-base", type=str, default="data/prices_us_etf_dm_v1")
    p.add_argument("--output-dir", type=str, default="backtests/us_etf_dual_momentum_mvp_v1_batch3")
    p.add_argument("--current-holdings-path", type=str, default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    batch2_dir = Path(args.batch2_dir)
    output_dir = Path(args.output_dir)
    current_holdings_path = Path(args.current_holdings_path) if args.current_holdings_path else output_dir / "account_state_template.csv"

    target = load_csv(batch2_dir / "target_portfolio.csv")
    decision = load_csv(batch2_dir / "decision_summary.csv")
    signal_date = str(decision.iloc[0]["SignalDate"]) if not decision.empty and "SignalDate" in decision.columns else ""

    issues = validate_batch2(target, decision)
    if current_holdings_path.exists():
        template = load_csv(current_holdings_path)
    else:
        template = build_template(current_holdings_path)

    template, account_cash, holdings_issues = prepare_account_state(template)
    issues.extend(holdings_issues)

    prices, price_issues = load_latest_prices(Path(args.price_base))
    issues.extend(price_issues)

    if issues:
        order_sheet, review = build_stop_outputs("; ".join(issues), signal_date)
    else:
        order_sheet, sizing_issues = build_order_sheet(template, target, prices, signal_date, account_cash)
        if sizing_issues:
            order_sheet, review = build_stop_outputs("; ".join(sizing_issues), signal_date)
            write_outputs(output_dir, template, order_sheet, review)
            print(review.to_string(index=False))
            return
        review, review_issues = build_review(order_sheet, target, signal_date)
        if review_issues:
            order_sheet, review = build_stop_outputs("; ".join(review_issues), signal_date)

    write_outputs(output_dir, template, order_sheet, review)
    print(review.to_string(index=False))
    if not order_sheet.empty:
        print()
        print(order_sheet.to_string(index=False))


if __name__ == "__main__":
    main()
