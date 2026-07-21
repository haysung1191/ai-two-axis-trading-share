from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _review_priority_score(row: dict[str, object]) -> float:
    score = float(row.get("offensive_score", 0.0) or 0.0)
    rank_delta = float(row.get("rank_delta_vs_legacy", 0.0) or 0.0)
    bonus = 0.0
    if row.get("priority_bucket") == "core":
        bonus += 12.0
    elif row.get("priority_bucket") == "candidate":
        bonus += 5.0
    if row.get("is_promotion"):
        bonus += 8.0
    if row.get("is_leader"):
        bonus += 4.0
    bonus += min(max(rank_delta, 0.0), 15.0)
    bonus += min(float(row.get("offensive_component_mom1", 0.0) or 0.0), 15.0) * 0.3
    bonus += min(float(row.get("offensive_component_volume", 0.0) or 0.0), 10.0) * 0.2
    return round(score + bonus, 2)


def _review_label(row: dict[str, object]) -> str:
    if row.get("priority_bucket") == "core" and row.get("is_promotion"):
        return "promoted_core"
    if row.get("priority_bucket") == "core":
        return "core_leader"
    if row.get("is_promotion"):
        return "promotion_probe"
    if row.get("priority_bucket") == "candidate":
        return "candidate_monitor"
    return "watch_only"


def build_review_shortlist_payload(
    candidate_packet: dict[str, object],
    *,
    top_n: int = 5,
) -> dict[str, object]:
    candidates = list(candidate_packet.get("candidates", []) or [])
    enriched = []
    for row in candidates:
        enriched_row = dict(row)
        enriched_row["review_priority_score"] = _review_priority_score(row)
        enriched_row["review_label"] = _review_label(row)
        enriched.append(enriched_row)

    shortlist = sorted(
        enriched,
        key=lambda row: (
            -float(row.get("review_priority_score", 0.0) or 0.0),
            int(row.get("offensive_rank", 9999) or 9999),
        ),
    )[:top_n]

    return {
        "candidate_count": int(len(candidates)),
        "top_n": int(top_n),
        "shortlist_count": int(len(shortlist)),
        "shortlist": shortlist,
    }


def render_review_shortlist(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Review Shortlist",
        "",
        f"- candidate_count: {payload.get('candidate_count', 0)}",
        f"- top_n: {payload.get('top_n', 0)}",
        f"- shortlist_count: {payload.get('shortlist_count', 0)}",
        "",
        "## Shortlist",
    ]
    shortlist = payload.get("shortlist", []) or []
    if shortlist:
        for row in shortlist:
            lines.append(
                "- {code} {name}: review_label={label}, review_priority_score={priority}, offensive_score={score}, offensive_rank={rank}, rank_delta_vs_legacy={delta}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    label=row.get("review_label", "-"),
                    priority=row.get("review_priority_score", "-"),
                    score=row.get("offensive_score", "-"),
                    rank=row.get("offensive_rank", "-"),
                    delta=row.get("rank_delta_vs_legacy", "-"),
                )
            )
            lines.append(
                "  reason_tags={tags}".format(
                    tags=",".join(str(tag) for tag in row.get("reason_tags", []) or ["none"])
                )
            )
        return "\n".join(lines) + "\n"
    lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate-packet-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_candidate_packet_latest.json"),
    )
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    candidate_packet = _load_json(args.candidate_packet_json_path)
    payload = build_review_shortlist_payload(candidate_packet, top_n=args.top_n)
    report = render_review_shortlist(payload)

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
