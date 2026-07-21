from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from live_core.kis_screener_runner import annotate_stock_ranking_comparison


def _load_frame(csv_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def _build_reason_tags(row: pd.Series) -> list[str]:
    tags: list[str] = []
    if float(row.get("momentum_12m", 0.0) or 0.0) >= 200:
        tags.append("long_term_momentum")
    if float(row.get("momentum_6m", 0.0) or 0.0) >= 120:
        tags.append("mid_term_momentum")
    if float(row.get("momentum_1m", 0.0) or 0.0) >= 20:
        tags.append("recent_strength")
    if float(row.get("MAD_gap_pct", 0.0) or 0.0) >= 50:
        tags.append("trend_expansion")
    if float(row.get("volume_ratio_5d_20d", 0.0) or 0.0) >= 1.1:
        tags.append("volume_confirmation")
    if float(row.get("breakout_distance_pct", -100.0) or -100.0) >= -5:
        tags.append("near_breakout")
    if float(row.get("momentum_acceleration", 0.0) or 0.0) > 0:
        tags.append("momentum_acceleration")
    return tags or ["mixed_profile"]


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    cols = [
        "Code",
        "Name",
        "offensive_score",
        "MAD_gap_pct",
        "offensive_rank",
        "legacy_mad_rank",
        "rank_delta_vs_legacy",
        "momentum_1m",
        "momentum_6m",
        "momentum_12m",
        "volume_ratio_5d_20d",
        "breakout_distance_pct",
        "momentum_acceleration",
        "offensive_component_mom12",
        "offensive_component_mom6",
        "offensive_component_mom1",
        "offensive_component_trend",
        "offensive_component_breakout",
        "offensive_component_volume",
    ]
    existing = [c for c in cols if c in frame.columns]
    for _, row in frame.iterrows():
        item = {col: row[col] for col in existing}
        item["reason_tags"] = _build_reason_tags(row)
        records.append(item)
    return records


def build_comparison_payload(df: pd.DataFrame, *, top_n: int = 10) -> dict[str, object]:
    annotated = annotate_stock_ranking_comparison(df)
    if annotated.empty:
        return {"row_count": 0, "top_n": top_n, "leaders": [], "biggest_promotions": []}

    leaders = annotated.sort_values(
        by=["offensive_rank", "offensive_score"], ascending=[True, False]
    ).head(top_n)
    promotions = annotated.sort_values(
        by=["rank_delta_vs_legacy", "offensive_score"], ascending=[False, False]
    ).head(top_n)
    return {
        "row_count": int(len(annotated)),
        "top_n": int(top_n),
        "leaders": _records(leaders),
        "biggest_promotions": _records(promotions),
    }


def render_report(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Screener Comparison",
        "",
        f"- row_count: {payload.get('row_count', 0)}",
        f"- top_n: {payload.get('top_n', 0)}",
        "",
        "## Offensive Leaders",
    ]
    leaders = payload.get("leaders", []) or []
    if leaders:
        for row in leaders:
            lines.append(
                "- {code} {name}: offensive_score={score}, offensive_rank={off_rank}, legacy_mad_rank={legacy_rank}, rank_delta_vs_legacy={delta}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    score=row.get("offensive_score", "-"),
                    off_rank=row.get("offensive_rank", "-"),
                    legacy_rank=row.get("legacy_mad_rank", "-"),
                    delta=row.get("rank_delta_vs_legacy", "-"),
                )
            )
            lines.append(
                "  reason_tags={tags}".format(
                    tags=",".join(str(tag) for tag in row.get("reason_tags", []) or ["mixed_profile"])
                )
            )
            component_summary = _render_component_summary(row)
            if component_summary:
                lines.append(f"  score_components={component_summary}")
    else:
        lines.append("- none")

    lines.extend(["", "## Biggest Promotions"])
    promotions = payload.get("biggest_promotions", []) or []
    if promotions:
        for row in promotions:
            lines.append(
                "- {code} {name}: rank_delta_vs_legacy={delta}, offensive_score={score}, offensive_rank={off_rank}, legacy_mad_rank={legacy_rank}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    delta=row.get("rank_delta_vs_legacy", "-"),
                    score=row.get("offensive_score", "-"),
                    off_rank=row.get("offensive_rank", "-"),
                    legacy_rank=row.get("legacy_mad_rank", "-"),
                )
            )
            lines.append(
                "  reason_tags={tags}".format(
                    tags=",".join(str(tag) for tag in row.get("reason_tags", []) or ["mixed_profile"])
                )
            )
            component_summary = _render_component_summary(row)
            if component_summary:
                lines.append(f"  score_components={component_summary}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _render_component_summary(row: dict[str, object]) -> str:
    fields = [
        ("mom12", "offensive_component_mom12"),
        ("mom6", "offensive_component_mom6"),
        ("mom1", "offensive_component_mom1"),
        ("trend", "offensive_component_trend"),
        ("breakout", "offensive_component_breakout"),
        ("volume", "offensive_component_volume"),
    ]
    parts: list[str] = []
    for label, key in fields:
        if key in row and row.get(key) is not None:
            parts.append(f"{label}={row[key]}")
    return ", ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--screening-csv", required=True)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    df = _load_frame(args.screening_csv)
    payload = build_comparison_payload(df, top_n=args.top_n)
    report = render_report(payload)

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
