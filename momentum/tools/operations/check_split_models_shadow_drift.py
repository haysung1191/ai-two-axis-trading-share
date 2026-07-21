from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd


ROOT = REPO_ROOT
CURRENT_DIR = ROOT / "output" / "split_models_shadow"
REFERENCE_DIR = ROOT / "output" / "split_models_shadow_reference"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_book(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["Symbol", "TargetWeight", "Sector", "Market"])
    df = pd.read_csv(path)
    for col in ["Symbol", "Sector", "Market"]:
        if col not in df.columns:
            df[col] = ""
    if "TargetWeight" not in df.columns:
        df["TargetWeight"] = 0.0
    return df


def _refresh_reference(current_dir: Path, reference_dir: Path) -> None:
    reference_dir.mkdir(parents=True, exist_ok=True)
    files = [
        "shadow_summary.json",
        "shadow_current_book.csv",
        "shadow_current_sector_mix.csv",
        "shadow_health.csv",
    ]
    for name in files:
        shutil.copy2(current_dir / name, reference_dir / name)


def _weight_map(book: pd.DataFrame) -> dict[str, float]:
    keyed = {}
    for row in book.itertuples(index=False):
        key = f"{getattr(row, 'Market', '')}:{getattr(row, 'Sector', '')}:{getattr(row, 'Symbol', '')}"
        keyed[key] = float(getattr(row, "TargetWeight", 0.0))
    return keyed


def _sector_map(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if df.empty:
        return {}
    return {
        f"{row.Market}:{row.Sector}": float(row.WeightSum)
        for row in df.itertuples(index=False)
    }


def _build_report(current_dir: Path, reference_dir: Path) -> dict:
    current_summary = _load_json(current_dir / "shadow_summary.json")
    reference_summary = _load_json(reference_dir / "shadow_summary.json")
    current_book = _load_book(current_dir / "shadow_current_book.csv")
    reference_book = _load_book(reference_dir / "shadow_current_book.csv")
    current_weights = _weight_map(current_book)
    reference_weights = _weight_map(reference_book)
    current_keys = set(current_weights)
    reference_keys = set(reference_weights)
    union_keys = sorted(current_keys | reference_keys)
    weight_turnover = 0.5 * sum(abs(current_weights.get(k, 0.0) - reference_weights.get(k, 0.0)) for k in union_keys)

    current_sector = _sector_map(current_dir / "shadow_current_sector_mix.csv")
    reference_sector = _sector_map(reference_dir / "shadow_current_sector_mix.csv")
    sector_union = sorted(set(current_sector) | set(reference_sector))
    sector_shift = 0.5 * sum(abs(current_sector.get(k, 0.0) - reference_sector.get(k, 0.0)) for k in sector_union)

    report = {
        "baseline_variant_same": current_summary.get("baseline_variant") == reference_summary.get("baseline_variant"),
        "health_verdict_same": current_summary.get("health_verdict") == reference_summary.get("health_verdict"),
        "current_health_verdict": current_summary.get("health_verdict"),
        "reference_health_verdict": reference_summary.get("health_verdict"),
        "holding_count_change": int(current_summary.get("current_holdings", 0)) - int(reference_summary.get("current_holdings", 0)),
        "added_symbols": sorted(current_keys - reference_keys),
        "removed_symbols": sorted(reference_keys - current_keys),
        "book_weight_turnover": float(weight_turnover),
        "sector_weight_shift": float(sector_shift),
        "current_dominant_sector": current_summary.get("current_dominant_sector"),
        "reference_dominant_sector": reference_summary.get("current_dominant_sector"),
    }
    report["drift_verdict"] = "PASS" if report["baseline_variant_same"] and current_summary.get("health_verdict") == "PASS" else "FAIL"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-reference", action="store_true")
    args = parser.parse_args()

    if args.refresh_reference:
        _refresh_reference(CURRENT_DIR, REFERENCE_DIR)

    report = _build_report(CURRENT_DIR, REFERENCE_DIR)
    (CURRENT_DIR / "shadow_drift_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"drift_verdict={report['drift_verdict']}")
    print(f"book_weight_turnover={report['book_weight_turnover']:.6f}")
    print(f"sector_weight_shift={report['sector_weight_shift']:.6f}")
    print(f"added_symbols={len(report['added_symbols'])}")
    print(f"removed_symbols={len(report['removed_symbols'])}")


if __name__ == "__main__":
    main()
