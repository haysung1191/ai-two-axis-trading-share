from __future__ import annotations

import shutil
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd


ROOT = REPO_ROOT
UNIVERSE_PATH = ROOT / "backtests" / "kis_operating_universe_candidates_institutional_v1.csv"
SOURCE_ROOT = ROOT / "data" / "flows_naver_8y" / "stock"
TARGET_ROOT = ROOT / "data" / "flows_operating_institutional_v1" / "stock"
REPORT_PATH = ROOT / "backtests" / "kis_operating_flow_coverage.csv"


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH)
    universe["Code"] = universe["Code"].astype(str).str.zfill(6)
    stock_codes = sorted(universe[universe["Market"].astype(str).eq("STOCK")]["Code"].unique().tolist())

    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    for stale in TARGET_ROOT.glob("*.csv.gz"):
        stale.unlink()

    rows: list[dict] = []
    copied = 0
    missing = 0
    for code in stock_codes:
        src = SOURCE_ROOT / f"{code}.csv.gz"
        dst = TARGET_ROOT / src.name
        exists = src.exists()
        rows.append(
            {
                "Code": code,
                "SourcePath": str(src),
                "TargetPath": str(dst),
                "SourceExists": int(exists),
                "Copied": int(exists),
            }
        )
        if exists:
            shutil.copy2(src, dst)
            copied += 1
        else:
            missing += 1

    report = pd.DataFrame(rows).sort_values("Code").reset_index(drop=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(REPORT_PATH, index=False, encoding="utf-8-sig")

    print(f"stocks={len(stock_codes)}")
    print(f"copied={copied}")
    print(f"missing={missing}")
    print(f"target_root={TARGET_ROOT}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
