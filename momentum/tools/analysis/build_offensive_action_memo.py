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


def _fmt_metric(value: object) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _confirmation_signals(row: dict[str, object]) -> list[str]:
    signals: list[str] = []
    if float(row.get("rank_delta_vs_legacy", 0.0) or 0.0) >= 7:
        signals.append("large_rank_upgrade")
    if float(row.get("offensive_component_volume", 0.0) or 0.0) >= 5.0:
        signals.append("volume_support")
    if float(row.get("offensive_component_breakout", 0.0) or 0.0) >= 9.5:
        signals.append("breakout_ready")
    return signals


def _missing_signal_gaps(row: dict[str, object]) -> list[dict[str, object]]:
    rank_delta = float(row.get("rank_delta_vs_legacy", 0.0) or 0.0)
    volume_component = float(row.get("offensive_component_volume", 0.0) or 0.0)
    breakout_component = float(row.get("offensive_component_breakout", 0.0) or 0.0)
    gaps = []
    if rank_delta < 7:
        gaps.append(
            {
                "signal": "large_rank_upgrade",
                "current_value": round(rank_delta, 2),
                "threshold": 7.0,
                "gap": round(7.0 - rank_delta, 2),
            }
        )
    if volume_component < 5.0:
        gaps.append(
            {
                "signal": "volume_support",
                "current_value": round(volume_component, 2),
                "threshold": 5.0,
                "gap": round(5.0 - volume_component, 2),
            }
        )
    if breakout_component < 9.5:
        gaps.append(
            {
                "signal": "breakout_ready",
                "current_value": round(breakout_component, 2),
                "threshold": 9.5,
                "gap": round(9.5 - breakout_component, 2),
            }
        )
    return gaps


def _missing_signal_gap_summary(row: dict[str, object]) -> str:
    gaps = _missing_signal_gaps(row)
    if not gaps:
        return "none"
    return ", ".join(
        "{signal}: current={current_value}, threshold={threshold}, gap={gap}".format(
            signal=gap_row["signal"],
            current_value=_fmt_metric(gap_row["current_value"]),
            threshold=_fmt_metric(gap_row["threshold"]),
            gap=_fmt_metric(gap_row["gap"]),
        )
        for gap_row in gaps
    )


def _promotion_readiness_score(row: dict[str, object], action_label: str) -> float:
    if action_label != "validate_now":
        return 0.0
    gaps = _missing_signal_gaps(row)
    if not gaps:
        return 100.0
    total_gap = sum(float(gap_row.get("gap", 0.0) or 0.0) for gap_row in gaps)
    confirmation_count = len(_confirmation_signals(row))
    score = 100.0
    score -= total_gap * 10.0
    score += confirmation_count * 15.0
    score += float(row.get("offensive_score", 0.0) or 0.0) * 0.1
    return round(score, 2)


def _primary_gap_signal(row: dict[str, object]) -> str:
    gaps = _missing_signal_gaps(row)
    if not gaps:
        return "none"
    return str(sorted(gaps, key=lambda gap_row: (float(gap_row["gap"]), str(gap_row["signal"])))[0]["signal"])


def _signal_gap_map(row: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(gap_row.get("signal")): gap_row for gap_row in _missing_signal_gaps(row)}


def _promotion_watch_status(row: dict[str, object], action_label: str) -> str:
    if action_label != "validate_now":
        return "off"
    readiness_score = _promotion_readiness_score(row, action_label)
    gaps = _missing_signal_gaps(row)
    min_gap = min((float(gap_row.get("gap", 0.0) or 0.0) for gap_row in gaps), default=999.0)
    if readiness_score >= 90 or min_gap <= 0.75:
        return "hot"
    if readiness_score >= 70 or min_gap <= 1.5:
        return "warm"
    return "off"


def _promotion_watch_summary(row: dict[str, object], action_label: str) -> str:
    status = _promotion_watch_status(row, action_label)
    if status == "off":
        return "none"
    gaps = _missing_signal_gaps(row)
    min_gap = min((float(gap_row.get("gap", 0.0) or 0.0) for gap_row in gaps), default=0.0)
    return "{status}: nearest_gap={gap}, primary_gap={primary_gap}".format(
        status=status,
        gap=_fmt_metric(round(min_gap, 2)),
        primary_gap=_primary_gap_signal(row),
    )


def _nearest_signal_gap(row: dict[str, object]) -> float:
    gaps = _missing_signal_gaps(row)
    return round(min((float(gap_row.get("gap", 999.0) or 999.0) for gap_row in gaps), default=0.0), 2)


def _total_signal_gap(row: dict[str, object]) -> float:
    gaps = _missing_signal_gaps(row)
    return round(sum(float(gap_row.get("gap", 0.0) or 0.0) for gap_row in gaps), 2)


def _met_signal_margins(row: dict[str, object]) -> list[dict[str, object]]:
    rank_delta = float(row.get("rank_delta_vs_legacy", 0.0) or 0.0)
    volume_component = float(row.get("offensive_component_volume", 0.0) or 0.0)
    breakout_component = float(row.get("offensive_component_breakout", 0.0) or 0.0)
    margins = []
    if rank_delta >= 7:
        margins.append(
            {
                "signal": "large_rank_upgrade",
                "current_value": round(rank_delta, 2),
                "threshold": 7.0,
                "margin": round(rank_delta - 7.0, 2),
            }
        )
    if volume_component >= 5.0:
        margins.append(
            {
                "signal": "volume_support",
                "current_value": round(volume_component, 2),
                "threshold": 5.0,
                "margin": round(volume_component - 5.0, 2),
            }
        )
    if breakout_component >= 9.5:
        margins.append(
            {
                "signal": "breakout_ready",
                "current_value": round(breakout_component, 2),
                "threshold": 9.5,
                "margin": round(breakout_component - 9.5, 2),
            }
        )
    return margins


def _weakest_met_signal(row: dict[str, object]) -> str:
    margins = _met_signal_margins(row)
    if not margins:
        return "none"
    return str(sorted(margins, key=lambda margin_row: (float(margin_row["margin"]), str(margin_row["signal"])))[0]["signal"])


def _act_now_risk_status(row: dict[str, object], action_label: str) -> str:
    if action_label != "act_now":
        return "off"
    margins = _met_signal_margins(row)
    if not margins:
        return "off"
    weakest_margin = min(float(margin_row.get("margin", 0.0) or 0.0) for margin_row in margins)
    if weakest_margin <= 0.15:
        return "hot"
    if weakest_margin <= 0.75:
        return "warm"
    return "off"


def _act_now_risk_summary(row: dict[str, object], action_label: str) -> str:
    status = _act_now_risk_status(row, action_label)
    if status == "off":
        return "none"
    margins = _met_signal_margins(row)
    weakest_margin = min((float(margin_row.get("margin", 0.0) or 0.0) for margin_row in margins), default=0.0)
    return "{status}: weakest_margin={margin}, weakest_signal={signal}".format(
        status=status,
        margin=round(weakest_margin, 2),
        signal=_weakest_met_signal(row),
    )


def _promotion_path_summary(row: dict[str, object], action_label: str) -> str:
    if action_label != "validate_now":
        return "none"

    confirmation_signals = _confirmation_signals(row)
    confirmation_count = len(confirmation_signals)
    needed = max(0, 2 - confirmation_count)
    if needed == 0:
        return "already_cleared"

    gaps = _missing_signal_gaps(row)
    if not gaps:
        return "manual_review"

    ranked_gaps = sorted(
        gaps,
        key=lambda gap_row: (float(gap_row.get("gap", 999.0) or 999.0), str(gap_row.get("signal", ""))),
    )
    primary = ranked_gaps[0]
    primary_signal = str(primary.get("signal", "signal"))
    primary_gap = float(primary.get("gap", 0.0) or 0.0)
    if needed == 1:
        alternates = ",".join(str(gap_row.get("signal", "-")) for gap_row in ranked_gaps[1:]) or "none"
        return (
            "one_signal_to_act_now: primary={primary} gap={gap}; alternates={alternates}".format(
                primary=primary_signal,
                gap=_fmt_metric(round(primary_gap, 2)),
                alternates=alternates,
            )
        )

    required = ",".join(str(gap_row.get("signal", "-")) for gap_row in ranked_gaps[:needed])
    return "needs_{needed}_signals: next_targets={required}".format(
        needed=needed,
        required=required,
    )


def _validate_priority_summary(row: dict[str, object], action_label: str) -> str:
    if action_label != "validate_now":
        return "none"
    return (
        "closest_path={primary} gap={nearest}; total_gap={total}; confirmations={confirmed}/2"
    ).format(
        primary=_primary_gap_signal(row),
        nearest=_fmt_metric(_nearest_signal_gap(row)),
        total=_fmt_metric(_total_signal_gap(row)),
        confirmed=len(_confirmation_signals(row)),
    )


def _promotion_trigger_signal(row: dict[str, object], action_label: str) -> str:
    if action_label != "validate_now":
        return "none"
    needed = max(0, 2 - len(_confirmation_signals(row)))
    if needed != 1:
        return "none"
    return _primary_gap_signal(row)


def _demotion_edge_summary(row: dict[str, object], action_label: str) -> str:
    if action_label != "act_now":
        return "none"
    weakest_signal = _weakest_met_signal(row)
    if weakest_signal == "none":
        return "none"

    margin_index = {str(margin_row.get("signal")): margin_row for margin_row in _met_signal_margins(row)}
    weakest_row = margin_index.get(weakest_signal, {})
    weakest_margin = round(float(weakest_row.get("margin", 0.0) or 0.0), 2)
    return "breaks_first_on={signal} margin={margin}".format(
        signal=weakest_signal,
        margin=_fmt_metric(weakest_margin),
    )


def _action_label(row: dict[str, object]) -> str:
    review_label = str(row.get("review_label", ""))
    priority_score = float(row.get("review_priority_score", 0.0) or 0.0)
    confirmation_count = len(_confirmation_signals(row))

    if review_label == "promoted_core" and confirmation_count >= 2:
        return "act_now"
    if review_label == "core_leader" and priority_score >= 115 and confirmation_count >= 2:
        return "act_now"
    if review_label in {"promotion_probe", "candidate_monitor"}:
        return "validate_now"
    if review_label == "promoted_core":
        return "validate_now"
    return "monitor_only"


def _action_reasons(row: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if row.get("is_promotion"):
        reasons.append("promotion_signal")
    if row.get("is_leader"):
        reasons.append("top_rank_leader")
    confirmation_signals = _confirmation_signals(row)
    if "large_rank_upgrade" in confirmation_signals:
        reasons.append("large_rank_upgrade")
    if float(row.get("offensive_component_mom1", 0.0) or 0.0) >= 10:
        reasons.append("recent_strength_confirmed")
    if "volume_support" in confirmation_signals:
        reasons.append("volume_support")
    if "breakout_ready" in confirmation_signals:
        reasons.append("breakout_ready")
    return reasons or ["needs_manual_review"]


def _rule_trigger_summary(row: dict[str, object], action_label: str) -> str:
    review_label = str(row.get("review_label", ""))
    priority_score = float(row.get("review_priority_score", 0.0) or 0.0)
    confirmation_signals = _confirmation_signals(row)
    confirmation_count = len(confirmation_signals)
    met_summary = ",".join(confirmation_signals) if confirmation_signals else "none"
    missing_signals = [
        signal
        for signal in ("large_rank_upgrade", "volume_support", "breakout_ready")
        if signal not in confirmation_signals
    ]
    missing_summary = ",".join(missing_signals) if missing_signals else "none"

    if action_label == "act_now":
        if review_label == "core_leader":
            return (
                "core_leader gate passed with review_priority_score={priority} and "
                "confirmation_count={count}/2; met={met}".format(
                    priority=priority_score,
                    count=confirmation_count,
                    met=met_summary,
                )
            )
        return "promoted_core gate passed with confirmation_count={count}/2; met={met}".format(
            count=confirmation_count,
            met=met_summary,
        )

    if action_label == "validate_now":
        if review_label in {"promotion_probe", "candidate_monitor"}:
            return "{label} remains in validation bucket by review_label gate.".format(label=review_label)
        if review_label == "promoted_core":
            return (
                "promoted_core kept but act-now confirmation_count={count}/2; "
                "met={met}; missing={missing}".format(
                    count=confirmation_count,
                    met=met_summary,
                    missing=missing_summary,
                )
            )
        return "{label} does not clear the act-now gate and stays in validation.".format(
            label=review_label or "unclassified"
        )

    return "{label} falls outside both act-now and validate-now gates.".format(
        label=review_label or "unclassified"
    )


def _next_gate_summary(row: dict[str, object], action_label: str) -> str:
    review_label = str(row.get("review_label", ""))
    confirmation_signals = _confirmation_signals(row)
    confirmation_count = len(confirmation_signals)
    gap_summary = _missing_signal_gap_summary(row)

    if action_label == "act_now":
        return "already_cleared"
    if action_label == "validate_now" and review_label == "promoted_core":
        return (
            "needs {needed} more confirmation signal for act-now; gaps={gaps}".format(
                needed=max(0, 2 - confirmation_count),
                gaps=gap_summary,
            )
        )
    if action_label == "validate_now" and review_label in {"promotion_probe", "candidate_monitor"}:
        return "review_label gate blocks promotion before confirmation thresholds matter."
    return "manual_review"


def build_action_memo_payload(shortlist_payload: dict[str, object]) -> dict[str, object]:
    shortlist = shortlist_payload.get("shortlist", []) or []
    decisions: list[dict[str, object]] = []
    for row in shortlist:
        action_label = _action_label(row)
        confirmation_signals = _confirmation_signals(row)
        decisions.append(
            {
                "Code": row.get("Code"),
                "Name": row.get("Name"),
                "action_label": action_label,
                "review_label": row.get("review_label"),
                "review_priority_score": row.get("review_priority_score"),
                "offensive_score": row.get("offensive_score"),
                "offensive_rank": row.get("offensive_rank"),
                "rank_delta_vs_legacy": row.get("rank_delta_vs_legacy"),
                "reason_tags": row.get("reason_tags", []),
                "confirmation_signals": confirmation_signals,
                "confirmation_count": len(confirmation_signals),
                "missing_signal_gaps": _missing_signal_gaps(row),
                "missing_signal_gap_summary": _missing_signal_gap_summary(row),
                "missing_signal_count": len(_missing_signal_gaps(row)),
                "primary_gap_signal": _primary_gap_signal(row),
                "nearest_signal_gap": _nearest_signal_gap(row),
                "total_signal_gap": _total_signal_gap(row),
                "promotion_trigger_signal": _promotion_trigger_signal(row, action_label),
                "promotion_path_summary": _promotion_path_summary(row, action_label),
                "validate_priority_summary": _validate_priority_summary(row, action_label),
                "action_reasons": _action_reasons(row),
                "rule_trigger_summary": _rule_trigger_summary(row, action_label),
                "next_gate_summary": _next_gate_summary(row, action_label),
                "promotion_readiness_score": _promotion_readiness_score(row, action_label),
                "promotion_watch_status": _promotion_watch_status(row, action_label),
                "promotion_watch_summary": _promotion_watch_summary(row, action_label),
                "act_now_risk_status": _act_now_risk_status(row, action_label),
                "act_now_risk_summary": _act_now_risk_summary(row, action_label),
                "weakest_met_signal": _weakest_met_signal(row),
                "demotion_edge_summary": _demotion_edge_summary(row, action_label),
            }
        )

    validate_now_rows = [row for row in decisions if row["action_label"] == "validate_now"]
    validate_now_rows.sort(
        key=lambda row: (
            int(row.get("missing_signal_count", 0)),
            float(row.get("nearest_signal_gap", 999.0) or 999.0),
            float(row.get("total_signal_gap", 999.0) or 999.0),
            -float(row.get("promotion_readiness_score", 0.0) or 0.0),
            -float(row.get("offensive_score", 0.0) or 0.0),
            str(row.get("Code", "")),
        )
    )
    for index, row in enumerate(validate_now_rows, start=1):
        row["validate_priority_rank"] = index

    return {
        "shortlist_count": int(len(shortlist)),
        "act_now_count": sum(1 for row in decisions if row["action_label"] == "act_now"),
        "validate_now_count": sum(1 for row in decisions if row["action_label"] == "validate_now"),
        "monitor_only_count": sum(1 for row in decisions if row["action_label"] == "monitor_only"),
        "decisions": decisions,
    }


def render_action_memo(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Action Memo",
        "",
        f"- shortlist_count: {payload.get('shortlist_count', 0)}",
        f"- act_now_count: {payload.get('act_now_count', 0)}",
        f"- validate_now_count: {payload.get('validate_now_count', 0)}",
        f"- monitor_only_count: {payload.get('monitor_only_count', 0)}",
        "",
        "## Decisions",
    ]
    decisions = payload.get("decisions", []) or []
    if decisions:
        for row in decisions:
            lines.append(
                "- {code} {name}: action_label={action}, review_label={review}, review_priority_score={priority}, offensive_score={score}, offensive_rank={rank}, rank_delta_vs_legacy={delta}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    action=row.get("action_label", "-"),
                    review=row.get("review_label", "-"),
                    priority=row.get("review_priority_score", "-"),
                    score=row.get("offensive_score", "-"),
                    rank=row.get("offensive_rank", "-"),
                    delta=row.get("rank_delta_vs_legacy", "-"),
                )
            )
            lines.append(
                "  action_reasons={reasons}".format(
                    reasons=",".join(str(item) for item in row.get("action_reasons", []) or ["none"])
                )
            )
            lines.append(
                "  next_gate={summary}".format(
                    summary=row.get("next_gate_summary", "none")
                )
            )
        return "\n".join(lines) + "\n"
    lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--review-shortlist-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_review_shortlist_latest.json"),
    )
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    shortlist_payload = _load_json(args.review_shortlist_json_path)
    payload = build_action_memo_payload(shortlist_payload)
    report = render_action_memo(payload)

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
