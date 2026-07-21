from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis.build_offensive_screener_comparison_report import _build_reason_tags


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalize_code(value: object) -> str:
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() and len(text) <= 6 else text


def _build_report_index(report_payload: dict[str, object]) -> dict[str, dict[str, object]]:
    index: dict[str, dict[str, object]] = {}
    leader_codes = {_normalize_code(row.get("Code")) for row in report_payload.get("leaders", []) or []}
    promotion_codes = {_normalize_code(row.get("Code")) for row in report_payload.get("biggest_promotions", []) or []}

    for section in ("leaders", "biggest_promotions"):
        for row in report_payload.get(section, []) or []:
            code = _normalize_code(row.get("Code"))
            existing = index.setdefault(code, {})
            existing.update(row)
            existing["is_leader"] = code in leader_codes
            existing["is_promotion"] = code in promotion_codes
    return index


def _priority_bucket(score: float) -> str:
    if score >= 85:
        return "core"
    if score >= 70:
        return "candidate"
    return "watch"


def build_candidate_packet_payload(
    filtered_df: pd.DataFrame,
    report_payload: dict[str, object],
    *,
    top_n: int = 10,
) -> dict[str, object]:
    report_index = _build_report_index(report_payload)
    frame = filtered_df.copy()
    if "Code" in frame.columns:
        frame["Code"] = frame["Code"].map(_normalize_code)
    if "offensive_score" in frame.columns:
        frame = frame.sort_values(by=["offensive_score", "offensive_rank"], ascending=[False, True]).reset_index(drop=True)

    candidates: list[dict[str, object]] = []
    for _, row in frame.head(top_n).iterrows():
        code = _normalize_code(row.get("Code"))
        report_row = report_index.get(code, {})
        score = float(row.get("offensive_score", 0.0) or 0.0)
        reason_tags = report_row.get("reason_tags") or _build_reason_tags(row)
        candidates.append(
            {
                "Code": code,
                "Name": row.get("Name"),
                "offensive_score": round(score, 2),
                "offensive_rank": int(row.get("offensive_rank", 0) or 0),
                "rank_delta_vs_legacy": int(row.get("rank_delta_vs_legacy", 0) or 0),
                "priority_bucket": _priority_bucket(score),
                "is_leader": bool(report_row.get("is_leader", False)),
                "is_promotion": bool(report_row.get("is_promotion", False)),
                "reason_tags": reason_tags,
                "momentum_1m": round(float(row.get("momentum_1m", 0.0) or 0.0), 2),
                "momentum_6m": round(float(row.get("momentum_6m", 0.0) or 0.0), 2),
                "momentum_12m": round(float(row.get("momentum_12m", 0.0) or 0.0), 2),
                "offensive_component_mom1": round(float(row.get("offensive_component_mom1", 0.0) or 0.0), 2),
                "offensive_component_volume": round(float(row.get("offensive_component_volume", 0.0) or 0.0), 2),
                "offensive_component_breakout": round(float(row.get("offensive_component_breakout", 0.0) or 0.0), 2),
            }
        )

    return {
        "candidate_count": int(len(frame)),
        "top_n": int(top_n),
        "core_count": sum(1 for row in candidates if row["priority_bucket"] == "core"),
        "promotion_count": sum(1 for row in candidates if row["is_promotion"]),
        "leader_count": sum(1 for row in candidates if row["is_leader"]),
        "candidates": candidates,
    }


def render_candidate_packet(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Candidate Packet",
        "",
        f"- candidate_count: {payload.get('candidate_count', 0)}",
        f"- top_n: {payload.get('top_n', 0)}",
        f"- core_count: {payload.get('core_count', 0)}",
        f"- leader_count: {payload.get('leader_count', 0)}",
        f"- promotion_count: {payload.get('promotion_count', 0)}",
        "",
        "## Candidates",
    ]
    candidates = payload.get("candidates", []) or []
    if candidates:
        for row in candidates:
            lines.append(
                "- {code} {name}: bucket={bucket}, offensive_score={score}, offensive_rank={rank}, rank_delta_vs_legacy={delta}, leader={leader}, promotion={promotion}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    bucket=row.get("priority_bucket", "-"),
                    score=row.get("offensive_score", "-"),
                    rank=row.get("offensive_rank", "-"),
                    delta=row.get("rank_delta_vs_legacy", "-"),
                    leader=row.get("is_leader", False),
                    promotion=row.get("is_promotion", False),
                )
            )
            lines.append(
                "  reason_tags={tags}".format(
                    tags=",".join(str(tag) for tag in row.get("reason_tags", []) or ["none"])
                )
            )
            lines.append(
                "  components=mom1={mom1}, volume={volume}, breakout={breakout}".format(
                    mom1=row.get("offensive_component_mom1", "-"),
                    volume=row.get("offensive_component_volume", "-"),
                    breakout=row.get("offensive_component_breakout", "-"),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filtered-csv-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_screening_filtered_latest.csv"),
    )
    parser.add_argument(
        "--report-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_screening_report_latest.json"),
    )
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    filtered_df = pd.read_csv(args.filtered_csv_path, dtype={"Code": str})
    report_payload = _load_json(args.report_json_path)
    payload = build_candidate_packet_payload(filtered_df, report_payload, top_n=args.top_n)
    report = render_candidate_packet(payload)

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
