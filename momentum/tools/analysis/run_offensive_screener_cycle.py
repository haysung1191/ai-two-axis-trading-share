from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from screener import MomentumScreener
from tools.analysis import build_offensive_screener_comparison_report as comparison_report


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "offensive_screener_cycle"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def build_cycle_payload(
    screening_csv_path: str | Path,
    report_json_path: str | Path,
    report_md_path: str | Path,
    *,
    row_count: int,
    top_n: int,
    etf_mode: bool,
    stock_sort_column: str | None,
) -> dict[str, object]:
    return {
        "screening_csv_path": str(screening_csv_path),
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
        "row_count": int(row_count),
        "top_n": int(top_n),
        "etf_mode": bool(etf_mode),
        "stock_sort_column": stock_sort_column,
    }


def render_cycle_text(payload: dict[str, object]) -> str:
    lines = [
        "Offensive Screener Cycle",
        f"row_count={payload.get('row_count', 0)}",
        f"top_n={payload.get('top_n', 0)}",
        f"etf_mode={payload.get('etf_mode', False)}",
        f"stock_sort_column={payload.get('stock_sort_column', '-')}",
        f"screening_csv_path={payload.get('screening_csv_path', '-')}",
        f"report_json_path={payload.get('report_json_path', '-')}",
        f"report_md_path={payload.get('report_md_path', '-')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=200)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--etf-mode", action="store_true")
    parser.add_argument("--stock-sort-column", default=None)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()

    screener = MomentumScreener()
    df = screener.run(
        max_items=args.max_items,
        etf_mode=args.etf_mode,
        stock_sort_column=args.stock_sort_column,
    )

    screening_csv_path = output_dir / f"offensive_screening_{stamp}.csv"
    report_json_path = output_dir / f"offensive_screening_report_{stamp}.json"
    report_md_path = output_dir / f"offensive_screening_report_{stamp}.md"
    latest_csv_path = output_dir / "offensive_screening_latest.csv"
    latest_json_path = output_dir / "offensive_screening_report_latest.json"
    latest_md_path = output_dir / "offensive_screening_report_latest.md"

    df.to_csv(screening_csv_path, index=False, encoding="utf-8-sig")
    df.to_csv(latest_csv_path, index=False, encoding="utf-8-sig")

    report_payload = comparison_report.build_comparison_payload(df, top_n=args.top_n)
    report_text = comparison_report.render_report(report_payload)
    report_json_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    report_md_path.write_text(report_text, encoding="utf-8")
    latest_json_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    latest_md_path.write_text(report_text, encoding="utf-8")

    cycle_payload = build_cycle_payload(
        screening_csv_path=screening_csv_path,
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        row_count=len(df),
        top_n=args.top_n,
        etf_mode=args.etf_mode,
        stock_sort_column=args.stock_sort_column,
    )
    if args.json:
        print(json.dumps(cycle_payload, indent=2))
        return
    print(render_cycle_text(cycle_payload), end="")


if __name__ == "__main__":
    main()
