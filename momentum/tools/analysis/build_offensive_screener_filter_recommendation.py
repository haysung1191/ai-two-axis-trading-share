from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


METRIC_FIELDS = [
    "offensive_component_mom1",
    "offensive_component_volume",
    "offensive_component_breakout",
]


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _minimum_thresholds(rows: list[dict[str, object]], fields: list[str]) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    for field in fields:
        values = [float(row.get(field, 0.0) or 0.0) for row in rows if field in row]
        if values:
            thresholds[field] = round(min(values), 2)
    return thresholds


def _evaluate_row_against_thresholds(
    row: dict[str, object], thresholds: dict[str, float]
) -> tuple[bool, list[dict[str, object]]]:
    failures: list[dict[str, object]] = []
    for field, threshold in thresholds.items():
        value = float(row.get(field, 0.0) or 0.0)
        if value < threshold:
            failures.append(
                {
                    "metric": field,
                    "value": round(value, 2),
                    "threshold": threshold,
                    "gap": round(value - threshold, 2),
                }
            )
    return len(failures) == 0, failures


def build_filter_recommendation_payload(report_payload: dict[str, object]) -> dict[str, object]:
    leaders = report_payload.get("leaders", []) or []
    promotions = report_payload.get("biggest_promotions", []) or []
    thresholds = _minimum_thresholds(leaders, METRIC_FIELDS)

    promotion_assessments: list[dict[str, object]] = []
    pass_count = 0
    fail_count = 0
    for row in promotions:
        passes, failures = _evaluate_row_against_thresholds(row, thresholds)
        if passes:
            pass_count += 1
        else:
            fail_count += 1
        promotion_assessments.append(
            {
                "Code": row.get("Code"),
                "Name": row.get("Name"),
                "offensive_score": row.get("offensive_score"),
                "passes_filter": passes,
                "failed_metrics": failures,
            }
        )

    return {
        "leader_count": len(leaders),
        "promotion_count": len(promotions),
        "recommended_thresholds": thresholds,
        "promotion_pass_count": pass_count,
        "promotion_fail_count": fail_count,
        "promotion_assessments": promotion_assessments,
    }


def render_filter_recommendation(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Screener Filter Recommendation",
        "",
        f"- leader_count: {payload.get('leader_count', 0)}",
        f"- promotion_count: {payload.get('promotion_count', 0)}",
        f"- promotion_pass_count: {payload.get('promotion_pass_count', 0)}",
        f"- promotion_fail_count: {payload.get('promotion_fail_count', 0)}",
        "",
        "## Recommended Thresholds",
    ]
    thresholds = payload.get("recommended_thresholds", {}) or {}
    if thresholds:
        for field, value in thresholds.items():
            lines.append(f"- {field}: {value}")
    else:
        lines.append("- none")

    lines.extend(["", "## Promotion Assessments"])
    assessments = payload.get("promotion_assessments", []) or []
    if assessments:
        for row in assessments:
            lines.append(
                "- {code} {name}: passes_filter={passes}, offensive_score={score}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    passes=row.get("passes_filter", False),
                    score=row.get("offensive_score", "-"),
                )
            )
            failures = row.get("failed_metrics", []) or []
            if failures:
                detail = ", ".join(
                    f"{item.get('metric')}={item.get('value')}<{item.get('threshold')}"
                    for item in failures
                )
                lines.append(f"  failed_metrics={detail}")
            else:
                lines.append("  failed_metrics=none")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_screening_report_latest.json"),
    )
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report_payload = _load_json(args.report_json_path)
    payload = build_filter_recommendation_payload(report_payload)
    report = render_filter_recommendation(payload)

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
