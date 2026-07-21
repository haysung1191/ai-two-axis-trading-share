import argparse
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd

from kis_quality_data import default_quality_base, fetch_quality_events, write_quality_events


def list_stock_codes(price_base: str, max_files: int = 0) -> list[str]:
    root = Path(price_base) / "stock"
    codes = sorted(p.stem.replace(".csv", "") for p in root.glob("*.csv.gz"))
    if max_files > 0:
        codes = codes[:max_files]
    return codes


def main() -> None:
    p = argparse.ArgumentParser(description="Backfill FnGuide-based quality/profitability sidecar data.")
    p.add_argument("--price-base", type=str, default="data/prices_operating_institutional_v1")
    p.add_argument("--save-base", type=str, default=default_quality_base())
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--skip-existing", type=int, default=1)
    args = p.parse_args()

    codes = list_stock_codes(args.price_base, max_files=args.max_files)
    rows: list[dict] = []
    for code in codes:
        save_path = os.path.join(args.save_base, "stock", f"{code}.csv.gz")
        if int(args.skip_existing) == 1 and os.path.exists(save_path):
            rows.append({"Code": code, "Status": "SKIP"})
            continue
        try:
            df = fetch_quality_events(code)
            write_quality_events(df, save_path)
            rows.append(
                {
                    "Code": code,
                    "Status": "OK",
                    "Rows": int(len(df)),
                    "CoverageStart": str(pd.to_datetime(df["effective_date"]).min().date()),
                    "CoverageEnd": str(pd.to_datetime(df["effective_date"]).max().date()),
                }
            )
        except Exception as e:
            rows.append({"Code": code, "Status": "ERR", "Error": str(e)})

    out = pd.DataFrame(rows)
    report_path = os.path.join(args.save_base, "quality_backfill_report.csv")
    out.to_csv(report_path, index=False, encoding="utf-8-sig")
    print(f"[OK] wrote {report_path}")


if __name__ == "__main__":
    main()
