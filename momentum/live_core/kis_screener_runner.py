from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

import pandas as pd


def classify_screening_quality(
    *,
    attempted_ticker_count: int,
    price_fetch_success_count: int,
    valid_momentum_count: int,
    empty_price_count: int,
    invalid_momentum_count: int,
) -> tuple[str, str]:
    attempted = int(attempted_ticker_count or 0)
    if attempted <= 0:
        return "unknown", "No screening attempts were recorded."

    fetch_coverage = price_fetch_success_count / attempted
    success_coverage = valid_momentum_count / attempted

    if fetch_coverage < 0.5 or success_coverage < 0.35:
        return "review", "Screening coverage collapsed and the latest snapshot should be treated as unstable."
    if fetch_coverage < 0.85 or success_coverage < 0.7 or empty_price_count > 0 or invalid_momentum_count > 0:
        return "caution", "Screening completed with visible data loss or filtering attrition."
    return "stable", "Screening coverage and valid momentum throughput stayed healthy."


def annotate_stock_ranking_comparison(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "offensive_score" not in df.columns or "MAD_gap_pct" not in df.columns:
        return df

    annotated = df.copy()
    annotated["offensive_rank"] = (
        annotated["offensive_score"].rank(method="first", ascending=False).astype(int)
    )
    annotated["legacy_mad_rank"] = (
        annotated["MAD_gap_pct"].rank(method="first", ascending=False).astype(int)
    )
    annotated["rank_delta_vs_legacy"] = (
        annotated["legacy_mad_rank"] - annotated["offensive_rank"]
    )
    return annotated


def resolve_screening_window(now: datetime | None = None) -> tuple[str, str]:
    today_dt = now or datetime.today()
    while today_dt.weekday() >= 5:
        today_dt -= timedelta(days=1)

    past_dt = today_dt - timedelta(days=400)
    return past_dt.strftime("%Y%m%d"), today_dt.strftime("%Y%m%d")


def build_screening_frame(
    *,
    api,
    tickers: list[tuple[str, str]],
    momentum_calculator: Callable[[list[dict]], dict | None],
    etf_mode: bool = False,
    max_items: int = 2500,
    sort_column: str | None = None,
    print_fn: Callable[[str], None] = print,
    now: datetime | None = None,
) -> pd.DataFrame:
    mode_label = "ETF" if etf_mode else "개별종목"
    print_fn(f"[{mode_label}] 스캔 대상: {len(tickers)}개")

    past_str, today_str = resolve_screening_window(now=now)
    results: list[dict] = []
    total = min(len(tickers), max_items)
    price_fetch_success = 0
    empty_price_count = 0
    invalid_momentum_count = 0
    empty_price_codes: list[str] = []
    invalid_momentum_codes: list[str] = []

    for idx, (code, name) in enumerate(tickers[:max_items], start=1):
        log_interval = 20 if etf_mode else 50
        if idx % log_interval == 0:
            print_fn(f"진행 상황: {idx}/{total} ({round(idx/total*100, 1)}%)")

        prices = api.get_historical_prices(code, past_str, today_str, "D")
        if prices:
            price_fetch_success += 1
        else:
            empty_price_count += 1
            empty_price_codes.append(str(code))
        mom_data = momentum_calculator(prices)
        if mom_data:
            row = {"Code": code, "Name": name, "Type": mode_label}
            row.update(mom_data)
            results.append(row)
        elif prices:
            invalid_momentum_count += 1
            invalid_momentum_codes.append(str(code))

    df = pd.DataFrame(results)
    if not df.empty:
        if sort_column:
            sort_col = sort_column
        elif etf_mode:
            sort_col = "avg_momentum"
        elif "offensive_score" in df.columns:
            sort_col = "offensive_score"
        else:
            sort_col = "MAD_gap_pct"
        df = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
        if not etf_mode:
            df = annotate_stock_ranking_comparison(df)

    attempted = int(total)
    valid_count = int(len(results))
    quality_status, quality_note = classify_screening_quality(
        attempted_ticker_count=attempted,
        price_fetch_success_count=price_fetch_success,
        valid_momentum_count=valid_count,
        empty_price_count=empty_price_count,
        invalid_momentum_count=invalid_momentum_count,
    )
    quality_summary = (
        "status={status}; attempted={attempted}; fetched={fetched}; valid={valid}; empty_price={empty_price}; "
        "invalid_momentum={invalid}; fetch_coverage={fetch_coverage:.2f}; success_coverage={success_coverage:.2f}"
    ).format(
        status=quality_status,
        attempted=attempted,
        fetched=price_fetch_success,
        valid=valid_count,
        empty_price=empty_price_count,
        invalid=invalid_momentum_count,
        fetch_coverage=(price_fetch_success / attempted) if attempted else 0.0,
        success_coverage=(valid_count / attempted) if attempted else 0.0,
    )
    df.attrs["screening_quality"] = {
        "quality_status": quality_status,
        "quality_note": quality_note,
        "attempted_ticker_count": attempted,
        "price_fetch_success_count": int(price_fetch_success),
        "valid_momentum_count": valid_count,
        "empty_price_count": int(empty_price_count),
        "invalid_momentum_count": int(invalid_momentum_count),
        "price_fetch_coverage": round((price_fetch_success / attempted), 4) if attempted else 0.0,
        "success_coverage": round((valid_count / attempted), 4) if attempted else 0.0,
        "empty_price_codes_sample": empty_price_codes[:5],
        "invalid_momentum_codes_sample": invalid_momentum_codes[:5],
        "quality_summary": quality_summary,
    }

    print_fn(f"[{mode_label}] 스크리닝 완료. 결과 {len(df)}개")
    return df
