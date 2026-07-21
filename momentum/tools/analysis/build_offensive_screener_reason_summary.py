from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _collect_report_paths(directory: str | Path) -> list[Path]:
    base = Path(directory)
    return sorted(
        [
            path
            for path in base.glob("offensive_screening_report_*.json")
            if "enriched" in path.name or "latest" in path.name
        ]
    )


COMPONENT_FIELDS = [
    "offensive_component_mom12",
    "offensive_component_mom6",
    "offensive_component_mom1",
    "offensive_component_trend",
    "offensive_component_breakout",
    "offensive_component_volume",
]


def _build_component_section(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {"row_count": 0, "average_components": [], "top_component_frequency": []}

    sums = {field: 0.0 for field in COMPONENT_FIELDS}
    top_counter: Counter[str] = Counter()
    counted_rows = 0

    for row in rows:
        present = False
        top_field = None
        top_value = float("-inf")
        for field in COMPONENT_FIELDS:
            value = float(row.get(field, 0.0) or 0.0)
            sums[field] += value
            if field in row:
                present = True
            if value > top_value:
                top_value = value
                top_field = field
        if present:
            counted_rows += 1
            if top_field:
                top_counter[top_field] += 1

    if counted_rows == 0:
        return {"row_count": 0, "average_components": [], "top_component_frequency": []}

    averages = [
        {"component": field, "avg_score": round(sums[field] / counted_rows, 2)}
        for field in sorted(COMPONENT_FIELDS, key=lambda name: sums[name], reverse=True)
    ]
    top_frequency = [
        {"component": field, "count": count}
        for field, count in top_counter.most_common()
    ]
    return {
        "row_count": counted_rows,
        "average_components": averages,
        "top_component_frequency": top_frequency,
    }


def build_reason_summary_payload(report_payloads: list[dict[str, object]]) -> dict[str, object]:
    leader_counter: Counter[str] = Counter()
    promotion_counter: Counter[str] = Counter()
    report_count = 0
    all_leader_rows: list[dict[str, object]] = []
    all_promotion_rows: list[dict[str, object]] = []

    for payload in report_payloads:
        report_count += 1
        leaders = payload.get("leaders", []) or []
        promotions = payload.get("biggest_promotions", []) or []
        all_leader_rows.extend(leaders)
        all_promotion_rows.extend(promotions)
        for row in leaders:
            for tag in row.get("reason_tags", []) or []:
                leader_counter[str(tag)] += 1
        for row in promotions:
            for tag in row.get("reason_tags", []) or []:
                promotion_counter[str(tag)] += 1

    return {
        "report_count": report_count,
        "leader_reason_frequency": [
            {"reason_tag": tag, "count": count}
            for tag, count in leader_counter.most_common()
        ],
        "promotion_reason_frequency": [
            {"reason_tag": tag, "count": count}
            for tag, count in promotion_counter.most_common()
        ],
        "leader_component_profile": _build_component_section(all_leader_rows),
        "promotion_component_profile": _build_component_section(all_promotion_rows),
    }


def render_reason_summary(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Screener Reason Summary",
        "",
        f"- report_count: {payload.get('report_count', 0)}",
        "",
        "## Leader Reason Frequency",
    ]
    leader_rows = payload.get("leader_reason_frequency", []) or []
    if leader_rows:
        for row in leader_rows:
            lines.append(f"- {row.get('reason_tag', '-')}: {row.get('count', 0)}")
    else:
        lines.append("- none")

    lines.extend(["", "## Leader Component Profile"])
    lines.extend(_render_component_profile(payload.get("leader_component_profile", {}) or {}))

    lines.extend(["", "## Promotion Reason Frequency"])
    promo_rows = payload.get("promotion_reason_frequency", []) or []
    if promo_rows:
        for row in promo_rows:
            lines.append(f"- {row.get('reason_tag', '-')}: {row.get('count', 0)}")
    else:
        lines.append("- none")

    lines.extend(["", "## Promotion Component Profile"])
    lines.extend(_render_component_profile(payload.get("promotion_component_profile", {}) or {}))
    lines.append("")
    return "\n".join(lines)


def _render_component_profile(section: dict[str, object]) -> list[str]:
    lines = [f"- row_count: {section.get('row_count', 0)}", "- average_components:"]
    average_rows = section.get("average_components", []) or []
    if average_rows:
        for row in average_rows:
            lines.append(f"  {row.get('component', '-')}: {row.get('avg_score', 0)}")
    else:
        lines.append("  none")
    lines.append("- top_component_frequency:")
    top_rows = section.get("top_component_frequency", []) or []
    if top_rows:
        for row in top_rows:
            lines.append(f"  {row.get('component', '-')}: {row.get('count', 0)}")
    else:
        lines.append("  none")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-dir",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle"),
    )
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report_paths = _collect_report_paths(args.report_dir)
    report_payloads = [_load_json(path) for path in report_paths]
    payload = build_reason_summary_payload(report_payloads)
    report = render_reason_summary(payload)

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
