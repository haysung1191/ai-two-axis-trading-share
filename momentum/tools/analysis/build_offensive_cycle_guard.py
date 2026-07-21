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


def _classify_component_drift(component_changes: list[dict[str, object]]) -> tuple[str, str]:
    if not component_changes:
        return "benign", "No component drift detected."

    change_index = {
        str(row.get("component")): float(row.get("change", 0.0) or 0.0)
        for row in component_changes
    }
    mom1_change = change_index.get("mom1", 0.0)
    volume_change = change_index.get("volume", 0.0)
    breakout_change = change_index.get("breakout", 0.0)

    if mom1_change <= -0.25:
        return "warning", "Recent-strength component weakened materially."
    if breakout_change <= -0.15:
        return "warning", "Breakout support weakened materially."
    if mom1_change < 0 or breakout_change < 0:
        return "watch", "A core offensive component softened and should be watched."
    if volume_change >= 0 or breakout_change >= 0:
        return "benign", "Component drift is flat-to-positive."
    return "benign", "No meaningful component drift risk detected."


def _build_act_now_stability_rows(
    cycle_diff_payload: dict[str, object] | None,
    action_memo_payload: dict[str, object] | None,
    *,
    max_safe_score_change: float,
    max_safe_rank_change: int,
) -> list[dict[str, object]]:
    if not action_memo_payload:
        return []

    decisions = action_memo_payload.get("decisions", []) or []
    act_now_rows = [row for row in decisions if row.get("action_label") == "act_now"]
    if not act_now_rows:
        return []

    diff_index = {
        str(row.get("Code")): row for row in (cycle_diff_payload or {}).get("top_candidate_score_changes", []) or []
    }
    act_added = set((cycle_diff_payload or {}).get("act_now_added", []) or [])

    stability_rows: list[dict[str, object]] = []
    for row in act_now_rows:
        code = str(row.get("Code", ""))
        diff_row = diff_index.get(code)
        score_change = float(diff_row.get("score_change", 0.0) or 0.0) if diff_row else 0.0
        rank_change = int(diff_row.get("rank_change", 0) or 0) if diff_row else 0
        component_changes = list(diff_row.get("component_changes", []) or []) if diff_row else []
        component_drift_severity, component_drift_reason = _classify_component_drift(component_changes)
        component_summary = ", ".join(
            "{component}={change}".format(
                component=component_row.get("component", "-"),
                change=component_row.get("change", 0),
            )
            for component_row in component_changes[:3]
        ) if component_changes else "none"
        support_signals = list(row.get("action_reasons", []) or row.get("reason_tags", []) or [])
        support_summary = ", ".join(str(item) for item in support_signals[:3]) if support_signals else "none"
        if not cycle_diff_payload:
            status = "no_baseline"
            reason = "No previous cycle exists yet for act-now stability comparison."
        elif code in act_added:
            status = "review"
            reason = "New act-now entry. Confirm the promotion is intentional before trusting continuity."
        elif abs(score_change) <= max_safe_score_change and abs(rank_change) <= max_safe_rank_change:
            status = "stable"
            reason = "Act-now member held its slot with only small score and rank movement."
        else:
            status = "caution"
            reason = "Act-now member stayed in place, but score or rank moved enough to warrant a quick check."
        stability_rows.append(
            {
                "Code": code,
                "Name": row.get("Name"),
                "stability_status": status,
                "score_change": round(score_change, 2),
                "rank_change": rank_change,
                "reason": reason,
                "support_signals": support_signals,
                "support_summary": support_summary,
                "component_changes": component_changes,
                "component_summary": component_summary,
                "component_drift_severity": component_drift_severity,
                "component_drift_reason": component_drift_reason,
            }
        )
    return stability_rows


def build_cycle_guard_payload(
    cycle_diff_payload: dict[str, object] | None,
    action_memo_payload: dict[str, object] | None = None,
    screening_quality: dict[str, object] | None = None,
    *,
    max_safe_count_change: int = 0,
    max_safe_membership_change: int = 0,
    max_safe_score_change: float = 1.0,
    max_safe_rank_change: int = 1,
    max_caution_score_change: float = 2.0,
    max_caution_rank_change: int = 2,
) -> dict[str, object]:
    thresholds = {
        "max_safe_count_change": int(max_safe_count_change),
        "max_safe_membership_change": int(max_safe_membership_change),
        "max_safe_score_change": float(max_safe_score_change),
        "max_safe_rank_change": int(max_safe_rank_change),
        "max_caution_score_change": float(max_caution_score_change),
        "max_caution_rank_change": int(max_caution_rank_change),
    }
    screening_quality = screening_quality or {}
    quality_status = str(screening_quality.get("quality_status", "unknown") or "unknown")
    quality_summary = str(screening_quality.get("quality_summary", "none") or "none")
    quality_metrics = {
        "screening_quality_status": quality_status,
        "screening_attempted_ticker_count": int(screening_quality.get("attempted_ticker_count", 0) or 0),
        "screening_price_fetch_success_count": int(screening_quality.get("price_fetch_success_count", 0) or 0),
        "screening_valid_momentum_count": int(screening_quality.get("valid_momentum_count", 0) or 0),
        "screening_empty_price_count": int(screening_quality.get("empty_price_count", 0) or 0),
        "screening_invalid_momentum_count": int(screening_quality.get("invalid_momentum_count", 0) or 0),
        "screening_price_fetch_coverage": round(float(screening_quality.get("price_fetch_coverage", 0.0) or 0.0), 2),
        "screening_success_coverage": round(float(screening_quality.get("success_coverage", 0.0) or 0.0), 2),
    }
    quality_codes = {
        "empty_price_codes_sample": list(screening_quality.get("empty_price_codes_sample", []) or []),
        "invalid_momentum_codes_sample": list(screening_quality.get("invalid_momentum_codes_sample", []) or []),
    }
    if not cycle_diff_payload:
        return {
            "guard_status": "no_baseline",
            "guard_summary": "No previous offensive cycle exists yet, so stability cannot be judged.",
            "previous_label": None,
            "current_label": None,
            "thresholds": thresholds,
            "act_now_stability": _build_act_now_stability_rows(
                None,
                action_memo_payload,
                max_safe_score_change=max_safe_score_change,
                max_safe_rank_change=max_safe_rank_change,
            ),
            "breaches": ["missing_previous_cycle"],
            "metrics": quality_metrics,
            "screening_quality": {
                "quality_status": quality_status,
                "quality_summary": quality_summary,
                "codes": quality_codes,
            },
        }

    score_rows = cycle_diff_payload.get("top_candidate_score_changes", []) or []
    act_count_change = abs(int(cycle_diff_payload.get("act_now_count_change", 0) or 0))
    validate_count_change = abs(int(cycle_diff_payload.get("validate_now_count_change", 0) or 0))
    act_membership_change = len(cycle_diff_payload.get("act_now_added", []) or []) + len(
        cycle_diff_payload.get("act_now_removed", []) or []
    )
    validate_membership_change = len(cycle_diff_payload.get("validate_now_added", []) or []) + len(
        cycle_diff_payload.get("validate_now_removed", []) or []
    )
    largest_score_change = max((abs(float(row.get("score_change", 0.0) or 0.0)) for row in score_rows), default=0.0)
    largest_rank_change = max((abs(int(row.get("rank_change", 0) or 0)) for row in score_rows), default=0)

    metrics = {
        "act_now_count_change_abs": act_count_change,
        "validate_now_count_change_abs": validate_count_change,
        "act_now_membership_change": act_membership_change,
        "validate_now_membership_change": validate_membership_change,
        "largest_score_change": round(largest_score_change, 2),
        "largest_rank_change": int(largest_rank_change),
    }
    metrics.update(quality_metrics)

    caution_flags: list[str] = []
    review_flags: list[str] = []

    if act_count_change > max_safe_count_change:
        review_flags.append("act_now_count_change")
    if act_membership_change > max_safe_membership_change:
        review_flags.append("act_now_membership_change")

    if validate_count_change > max_safe_count_change:
        caution_flags.append("validate_now_count_change")
    if validate_membership_change > max_safe_membership_change:
        caution_flags.append("validate_now_membership_change")
    if largest_score_change > max_safe_score_change:
        caution_flags.append("top_candidate_score_change")
    if largest_rank_change > max_safe_rank_change:
        caution_flags.append("top_candidate_rank_change")
    if largest_score_change > max_caution_score_change and "top_candidate_score_change" not in review_flags:
        review_flags.append("top_candidate_score_change")
    if largest_rank_change > max_caution_rank_change and "top_candidate_rank_change" not in review_flags:
        review_flags.append("top_candidate_rank_change")
    if quality_status == "caution":
        caution_flags.append("screening_quality_caution")
    elif quality_status == "review":
        review_flags.append("screening_quality_review")

    status = "stable"
    summary = "No material offensive-cycle instability detected."
    if review_flags:
        status = "review"
        summary = "Act-now composition shifted or top-candidate movement exceeded review thresholds."
    elif caution_flags:
        status = "caution"
        summary = "Offensive cycle stayed broadly intact, but secondary bucket or score movement deserves a quick check."
    if quality_status == "caution" and status == "caution":
        summary = "Offensive cycle stayed broadly intact, but screening quality softened enough to warrant a quick check."
    elif quality_status == "review":
        summary = "Screening quality degraded enough that offensive-cycle continuity should be reviewed before trusting the latest run."

    return {
        "guard_status": status,
        "guard_summary": summary,
        "previous_label": cycle_diff_payload.get("previous_label"),
        "current_label": cycle_diff_payload.get("current_label"),
        "thresholds": thresholds,
        "act_now_stability": _build_act_now_stability_rows(
            cycle_diff_payload,
            action_memo_payload,
            max_safe_score_change=max_safe_score_change,
            max_safe_rank_change=max_safe_rank_change,
        ),
        "caution_flags": caution_flags,
        "review_flags": review_flags,
        "breaches": sorted(set(review_flags + caution_flags)),
        "metrics": metrics,
        "screening_quality": {
            "quality_status": quality_status,
            "quality_summary": quality_summary,
            "codes": quality_codes,
        },
    }


def render_cycle_guard(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Cycle Guard",
        "",
        f"- guard_status: {payload.get('guard_status', '-')}",
        f"- previous_label: {payload.get('previous_label', '-')}",
        f"- current_label: {payload.get('current_label', '-')}",
        f"- guard_summary: {payload.get('guard_summary', '-')}",
        "",
        "## Metrics",
    ]
    metrics = payload.get("metrics", {}) or {}
    if metrics:
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")

    lines.extend(["", "## Screening Quality"])
    screening_quality = payload.get("screening_quality", {}) or {}
    if screening_quality:
        lines.append(f"- quality_status: {screening_quality.get('quality_status', 'unknown')}")
        lines.append(f"- quality_summary: {screening_quality.get('quality_summary', 'none')}")
        codes = screening_quality.get("codes", {}) or {}
        lines.append(
            "- quality_codes: empty_price={empty_price}; invalid_momentum={invalid}".format(
                empty_price=",".join(codes.get("empty_price_codes_sample", []) or []) or "none",
                invalid=",".join(codes.get("invalid_momentum_codes_sample", []) or []) or "none",
            )
        )
    else:
        lines.append("- none")

    lines.extend(["", "## Breaches"])
    review_flags = payload.get("review_flags", []) or []
    caution_flags = payload.get("caution_flags", []) or []
    if review_flags:
        for flag in review_flags:
            lines.append(f"- review:{flag}")
    if caution_flags:
        for flag in caution_flags:
            lines.append(f"- caution:{flag}")
    if not review_flags and not caution_flags:
        lines.append("- none")
    lines.extend(["", "## Thresholds"])
    thresholds = payload.get("thresholds", {}) or {}
    if thresholds:
        for key, value in thresholds.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "## Act Now Stability"])
    act_now_stability = payload.get("act_now_stability", []) or []
    if act_now_stability:
        for row in act_now_stability:
            lines.append(
                "- {code} {name}: stability_status={status}, score_change={score_change}, rank_change={rank_change}, support={support}, reason={reason}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    status=row.get("stability_status", "-"),
                    score_change=row.get("score_change", 0),
                    rank_change=row.get("rank_change", 0),
                    support=row.get("support_summary", "none"),
                    reason="{reason}; components={components}; component_drift={severity} ({drift_reason})".format(
                        reason=row.get("reason", "-"),
                        components=row.get("component_summary", "none"),
                        severity=row.get("component_drift_severity", "benign"),
                        drift_reason=row.get("component_drift_reason", "-"),
                    ),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle-diff-json-path")
    parser.add_argument("--action-memo-json-path")
    parser.add_argument("--screening-quality-json-path")
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cycle_diff_payload = _load_json(args.cycle_diff_json_path) if args.cycle_diff_json_path else None
    action_memo_payload = _load_json(args.action_memo_json_path) if args.action_memo_json_path else None
    screening_quality = _load_json(args.screening_quality_json_path) if args.screening_quality_json_path else None
    payload = build_cycle_guard_payload(cycle_diff_payload, action_memo_payload, screening_quality)
    report = render_cycle_guard(payload)

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
