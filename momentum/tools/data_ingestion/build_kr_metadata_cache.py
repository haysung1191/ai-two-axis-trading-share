from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd

from split_models.pipeline import KR_METADATA_CACHE, KR_METADATA_OVERRIDES


ROOT = REPO_ROOT


def main() -> None:
    universe = pd.read_csv(ROOT / "backtests" / "kis_operating_universe_candidates_institutional_v1.csv").copy()
    universe["Code"] = universe["Code"].astype(str).str.zfill(6)

    override_df = pd.DataFrame(columns=["Symbol", "Market", "Name", "Sector", "Source"])
    if KR_METADATA_OVERRIDES.exists():
        override_df = pd.read_csv(KR_METADATA_OVERRIDES).copy()
        override_df["Symbol"] = override_df["Symbol"].astype(str).str.zfill(6)

    rows = []
    try:
        from pykrx import stock

        for row in universe.itertuples(index=False):
            code = str(row.Code).zfill(6)
            market = str(row.Market)
            try:
                name = stock.get_market_ticker_name(code) if market == "STOCK" else code
            except Exception:
                name = code
            rows.append(
                {
                    "Symbol": code,
                    "Market": market,
                    "Name": name,
                    "Sector": "Unknown" if market == "STOCK" else "ETF",
                    "Source": "pykrx_name_only" if market == "STOCK" else "manual_needed",
                }
            )
    except Exception:
        for row in universe.itertuples(index=False):
            code = str(row.Code).zfill(6)
            market = str(row.Market)
            rows.append(
                {
                    "Symbol": code,
                    "Market": market,
                    "Name": code,
                    "Sector": "Unknown" if market == "STOCK" else "ETF",
                    "Source": "fallback_code_only",
                }
            )

    cache = pd.DataFrame(rows)
    if not override_df.empty:
        cache = cache.merge(
            override_df[["Symbol", "Market", "Name", "Sector"]].rename(
                columns={"Name": "OverrideName", "Sector": "OverrideSector"}
            ),
            on=["Symbol", "Market"],
            how="left",
        )
        cache["Name"] = cache["OverrideName"].fillna(cache["Name"])
        cache["Sector"] = cache["OverrideSector"].fillna(cache["Sector"])
        cache = cache.drop(columns=["OverrideName", "OverrideSector"])

    KR_METADATA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache.to_csv(KR_METADATA_CACHE, index=False, encoding="utf-8-sig")

    if not KR_METADATA_OVERRIDES.exists():
        template = cache.copy()
        template["Sector"] = template["Sector"].replace({"Unknown": ""})
        template.to_csv(KR_METADATA_OVERRIDES, index=False, encoding="utf-8-sig")

    unresolved = cache[cache["Sector"].astype(str).isin(["Unknown", ""])]
    print(f"cache={KR_METADATA_CACHE}")
    print(f"rows={len(cache)}")
    print(f"unresolved={len(unresolved)}")


if __name__ == "__main__":
    main()
