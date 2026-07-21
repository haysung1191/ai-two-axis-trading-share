from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models import run_pipeline


def main() -> None:
    outputs = run_pipeline()
    flow_date = outputs["flow_regime_snapshot"]["AsOfDate"].iloc[0]
    summary = outputs["momentum_trade_candidates"]
    kr_source = ""
    if "KRPriceSource" in summary.columns:
        kr_rows = summary[summary["Market"].eq("KR")]
        if not kr_rows.empty:
            kr_source = str(kr_rows["KRPriceSource"].dropna().iloc[0])
    print(f"flow_regime_snapshot={flow_date}")
    if kr_source:
        print(f"kr_price_source={kr_source}")
    readiness = outputs.get("data_readiness")
    if readiness is not None and not readiness.empty:
        kr_stock = readiness[readiness["Scope"].eq("KR_STOCK")]
        if not kr_stock.empty:
            row = kr_stock.iloc[0]
            print(
                "kr_stock_readiness="
                f"price_missing:{int(row['PriceMissingCount'])},"
                f"flow_missing:{int(row['FlowMissingCount'])},"
                f"price_latest:{row['PriceLatestMaxDate']},"
                f"flow_latest:{row['FlowLatestMaxDate']}"
            )
    print(f"momentum_trade_candidates={len(outputs['momentum_trade_candidates'])}")
    print(f"tenbagger_watchlist={len(outputs['tenbagger_watchlist'])}")
    print(f"portfolio_trading_book={len(outputs['portfolio_trading_book'])}")
    print(f"portfolio_tenbagger_book={len(outputs['portfolio_tenbagger_book'])}")


if __name__ == "__main__":
    main()
