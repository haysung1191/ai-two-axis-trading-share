from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis.build_offensive_screener_filter_recommendation import _load_json


def _normalize_code(value: object) -> str:
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() and len(text) <= 6 else text


def _apply_thresholds(
    df: pd.DataFrame,
    thresholds: dict[str, float],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty or not thresholds:
        return df.copy(), df.iloc[0:0].copy()

    mask = pd.Series(True, index=df.index)
    for field, threshold in thresholds.items():
        if field in df.columns:
            mask &= pd.to_numeric(df[field], errors="coerce").fillna(0.0) >= float(threshold)
        else:
            mask &= False

    passed = df.loc[mask].copy().reset_index(drop=True)
    failed = df.loc[~mask].copy().reset_index(drop=True)
    return passed, failed


def build_filter_application_payload(
    screening_df: pd.DataFrame,
    recommendation_payload: dict[str, object],
) -> dict[str, object]:
    thresholds = recommendation_payload.get("recommended_thresholds", {}) or {}
    passed, failed = _apply_thresholds(screening_df, thresholds)
    return {
        "input_row_count": int(len(screening_df)),
        "passed_row_count": int(len(passed)),
        "failed_row_count": int(len(failed)),
        "recommended_thresholds": thresholds,
        "passed_codes": [_normalize_code(value) for value in passed["Code"].tolist()] if "Code" in passed.columns else [],
        "failed_codes": [_normalize_code(value) for value in failed["Code"].tolist()] if "Code" in failed.columns else [],
    }


def render_filter_application(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Screener Filter Application",
        "",
        f"- input_row_count: {payload.get('input_row_count', 0)}",
        f"- passed_row_count: {payload.get('passed_row_count', 0)}",
        f"- failed_row_count: {payload.get('failed_row_count', 0)}",
        "",
        "## Recommended Thresholds",
    ]
    thresholds = payload.get("recommended_thresholds", {}) or {}
    if thresholds:
        for field, value in thresholds.items():
            lines.append(f"- {field}: {value}")
    else:
        lines.append("- none")

    lines.extend(["", "## Passed Codes"])
    passed_codes = payload.get("passed_codes", []) or []
    if passed_codes:
        for code in passed_codes:
            lines.append(f"- {code}")
    else:
        lines.append("- none")

    lines.extend(["", "## Failed Codes"])
    failed_codes = payload.get("failed_codes", []) or []
    if failed_codes:
        for code in failed_codes:
            lines.append(f"- {code}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--screening-csv-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_screening_latest.csv"),
    )
    parser.add_argument(
        "--recommendation-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_filter_recommendation_latest.json"),
    )
    parser.add_argument("--output-passed-csv-path")
    parser.add_argument("--output-failed-csv-path")
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    screening_df = pd.read_csv(args.screening_csv_path, dtype={"Code": str})
    recommendation_payload = _load_json(args.recommendation_json_path)
    thresholds = recommendation_payload.get("recommended_thresholds", {}) or {}
    passed_df, failed_df = _apply_thresholds(screening_df, thresholds)
    payload = build_filter_application_payload(screening_df, recommendation_payload)
    report = render_filter_application(payload)

    if args.output_passed_csv_path:
        out_passed = Path(args.output_passed_csv_path)
        out_passed.parent.mkdir(parents=True, exist_ok=True)
        passed_df.to_csv(out_passed, index=False, encoding="utf-8-sig")
    if args.output_failed_csv_path:
        out_failed = Path(args.output_failed_csv_path)
        out_failed.parent.mkdir(parents=True, exist_ok=True)
        failed_df.to_csv(out_failed, index=False, encoding="utf-8-sig")
    if args.output_json_path:
        out_json = Path(args.output_json_path)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.output_md_path:
        out_md = Path(args.output_md_path)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(report, encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(report, end="")


if __name__ == "__main__":
    main()
