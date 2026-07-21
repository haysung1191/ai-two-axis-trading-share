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


def _split_gate_status(status: object) -> tuple[str, str]:
    text = str(status or "").strip()
    if not text:
        return "none", "none"
    marker = "; gaps="
    if marker not in text:
        return text, "none"
    gate_text, gap_text = text.split(marker, 1)
    return gate_text.strip() or "none", gap_text.strip() or "none"


def _priority_gate_blocker(focus_row: dict[str, object]) -> str:
    focus_type = str(focus_row.get("focus_type", "none") or "none")
    review_label = str(focus_row.get("review_label", "none") or "none")
    gate_text, _ = _split_gate_status(focus_row.get("next_gate_summary", "none"))
    if focus_type == "promotion_watch":
        if review_label in {"promotion_probe", "candidate_monitor"}:
            return "review_label={label}".format(label=review_label)
        return gate_text
    if focus_type == "act_now_risk":
        return "cleared"
    if focus_type == "act_now_dormant":
        return "dormant"
    if focus_type == "data_quality_guard":
        return str(focus_row.get("summary", "none") or "none")
    return gate_text


def _priority_reason(focus_row: dict[str, object]) -> str:
    reason = str(focus_row.get("priority_reason", "none") or "none")
    if reason != "none":
        return reason
    return str(focus_row.get("summary", "none") or "none")


def _render_guard_delta_summary(cycle_guard_payload: dict[str, object] | None) -> str:
    if not cycle_guard_payload:
        return "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none"

    metrics = cycle_guard_payload.get("metrics", {}) or {}
    return (
        "previous={previous}; current={current}; act_now_delta={act_now_delta}; "
        "validate_now_delta={validate_now_delta}; membership=act_now:{act_membership},validate_now:{validate_membership}; "
        "top_move=score:{score_delta},rank:{rank_delta}"
    ).format(
        previous=cycle_guard_payload.get("previous_label") or "none",
        current=cycle_guard_payload.get("current_label") or "none",
        act_now_delta=metrics.get("act_now_count_change_abs", "none"),
        validate_now_delta=metrics.get("validate_now_count_change_abs", "none"),
        act_membership=metrics.get("act_now_membership_change", "none"),
        validate_membership=metrics.get("validate_now_membership_change", "none"),
        score_delta=_fmt_metric(metrics.get("largest_score_change", "none")),
        rank_delta=_fmt_metric(metrics.get("largest_rank_change", "none")),
    )


def _build_act_now_demotion_rows(
    action_memo_payload: dict[str, object],
    cycle_diff_payload: dict[str, object] | None,
) -> list[dict[str, object]]:
    if not cycle_diff_payload:
        return []

    removed_codes = cycle_diff_payload.get("act_now_removed", []) or []
    if not removed_codes:
        return []

    decisions = action_memo_payload.get("decisions", []) or []
    decision_index = {str(row.get("Code")): row for row in decisions}
    score_change_index = {
        str(row.get("Code")): row for row in (cycle_diff_payload.get("top_candidate_score_changes", []) or [])
    }

    demotions: list[dict[str, object]] = []
    for code in removed_codes:
        row = decision_index.get(str(code), {})
        score_row = score_change_index.get(str(code), {})
        new_label = row.get("action_label", "monitor_only")
        component_changes = score_row.get("component_changes", []) or []
        component_summary = ", ".join(
            "{component}={change}".format(
                component=component_row.get("component", "-"),
                change=component_row.get("change", 0),
            )
            for component_row in component_changes[:3]
        ) if component_changes else "none"
        if new_label == "validate_now":
            reason = "Dropped out of act-now and now requires validation before re-entry."
        else:
            reason = "Dropped out of act-now and no longer meets immediate action status."
        demotions.append(
            {
                "Code": str(code),
                "Name": row.get("Name", "-"),
                "new_action_label": new_label,
                "score_change": score_row.get("score_change", 0),
                "rank_change": score_row.get("rank_change", 0),
                "component_summary": component_summary,
                "reason": reason,
                "rule_trigger_summary": row.get("rule_trigger_summary", "-"),
            }
        )
    return demotions


def _build_act_now_promotion_rows(
    action_memo_payload: dict[str, object],
    cycle_diff_payload: dict[str, object] | None,
) -> list[dict[str, object]]:
    if not cycle_diff_payload:
        return []

    added_codes = cycle_diff_payload.get("act_now_added", []) or []
    if not added_codes:
        return []

    decisions = action_memo_payload.get("decisions", []) or []
    decision_index = {str(row.get("Code")): row for row in decisions}
    score_change_index = {
        str(row.get("Code")): row for row in (cycle_diff_payload.get("top_candidate_score_changes", []) or [])
    }
    removed_from_validate = set(cycle_diff_payload.get("validate_now_removed", []) or [])

    promotions: list[dict[str, object]] = []
    for code in added_codes:
        row = decision_index.get(str(code), {})
        score_row = score_change_index.get(str(code), {})
        previous_label = "validate_now" if str(code) in removed_from_validate else "outside_act_now"
        component_changes = score_row.get("component_changes", []) or []
        component_summary = ", ".join(
            "{component}={change}".format(
                component=component_row.get("component", "-"),
                change=component_row.get("change", 0),
            )
            for component_row in component_changes[:3]
        ) if component_changes else "none"
        if previous_label == "validate_now":
            reason = "Recovered from validation status and re-entered act-now."
        else:
            reason = "Newly entered the act-now bucket from outside the immediate-action set."
        promotions.append(
            {
                "Code": str(code),
                "Name": row.get("Name", "-"),
                "previous_action_label": previous_label,
                "score_change": score_row.get("score_change", 0),
                "rank_change": score_row.get("rank_change", 0),
                "component_summary": component_summary,
                "reason": reason,
                "rule_trigger_summary": row.get("rule_trigger_summary", "-"),
            }
        )
    return promotions


def _build_validate_priority_rows(action_memo_payload: dict[str, object]) -> list[dict[str, object]]:
    rows = [row for row in (action_memo_payload.get("decisions", []) or []) if row.get("action_label") == "validate_now"]
    rows.sort(
        key=lambda row: (
            int(row.get("validate_priority_rank", 999) or 999),
            -float(row.get("promotion_readiness_score", 0.0) or 0.0),
            str(row.get("Code", "")),
        )
    )
    return rows


def _build_act_now_rows(action_memo_payload: dict[str, object]) -> list[dict[str, object]]:
    rows = [row for row in (action_memo_payload.get("decisions", []) or []) if row.get("action_label") == "act_now"]
    rows.sort(
        key=lambda row: (
            float(row.get("offensive_rank", 999.0) or 999.0),
            -float(row.get("offensive_score", 0.0) or 0.0),
            str(row.get("Code", "")),
        )
    )
    return rows


def _build_validate_now_rows(action_memo_payload: dict[str, object]) -> list[dict[str, object]]:
    rows = [row for row in (action_memo_payload.get("decisions", []) or []) if row.get("action_label") == "validate_now"]
    rows.sort(
        key=lambda row: (
            int(row.get("validate_priority_rank", 999) or 999),
            float(row.get("nearest_signal_gap", 999.0) or 999.0),
            float(row.get("total_signal_gap", 999.0) or 999.0),
            -float(row.get("promotion_readiness_score", 0.0) or 0.0),
            str(row.get("Code", "")),
        )
    )
    return rows


def _build_promotion_watch_rows(action_memo_payload: dict[str, object]) -> list[dict[str, object]]:
    rows = [
        row
        for row in (action_memo_payload.get("decisions", []) or [])
        if row.get("action_label") == "validate_now" and row.get("promotion_watch_status") in {"hot", "warm"}
    ]
    rows.sort(
        key=lambda row: (
            0 if row.get("promotion_watch_status") == "hot" else 1,
            int(row.get("validate_priority_rank", 999) or 999),
            -float(row.get("promotion_readiness_score", 0.0) or 0.0),
        )
    )
    return rows


def _build_act_now_risk_rows(action_memo_payload: dict[str, object]) -> list[dict[str, object]]:
    rows = [
        row
        for row in (action_memo_payload.get("decisions", []) or [])
        if row.get("action_label") == "act_now" and row.get("act_now_risk_status") in {"hot", "warm"}
    ]
    rows.sort(
        key=lambda row: (
            0 if row.get("act_now_risk_status") == "hot" else 1,
            float(row.get("offensive_rank", 999) or 999),
            -float(row.get("offensive_score", 0.0) or 0.0),
        )
    )
    return rows


def _build_act_now_defense_ladder(action_memo_payload: dict[str, object]) -> list[dict[str, object]]:
    rows = _build_act_now_risk_rows(action_memo_payload)
    ladder: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        weakest_signal = row.get("weakest_met_signal")
        if not weakest_signal or weakest_signal == "none":
            risk_summary = str(row.get("act_now_risk_summary", ""))
            marker = "weakest_signal="
            if marker in risk_summary:
                weakest_signal = risk_summary.split(marker, 1)[1].split(",", 1)[0].strip()
        ladder.append(
            {
                "defense_rank": index,
                "Code": row.get("Code", "-"),
                "Name": row.get("Name", "-"),
                "risk_status": row.get("act_now_risk_status", "off"),
                "weakest_margin": _extract_summary_metric(row.get("act_now_risk_summary"), "weakest_margin", default=999.0),
                "weakest_signal": weakest_signal or "none",
                "offensive_rank": row.get("offensive_rank", "-"),
                "offensive_score": row.get("offensive_score", "-"),
                "demotion_edge_summary": row.get("demotion_edge_summary", "none"),
            }
        )
    return ladder


def _signal_action_label(signal: object) -> str:
    mapping = {
        "volume_support": "volume confirmation",
        "large_rank_upgrade": "rank follow-through",
        "breakout_ready": "breakout hold",
    }
    return mapping.get(str(signal), str(signal) if signal else "signal state")


def _resolve_promotion_signal(row: dict[str, object]) -> object:
    signal = row.get("promotion_trigger_signal")
    if signal not in {None, "", "none"}:
        return signal
    primary_gap = row.get("primary_gap_signal")
    if primary_gap not in {None, "", "none"}:
        return primary_gap
    return signal


def _validate_operator_guidance(row: dict[str, object]) -> tuple[str, str]:
    code = str(row.get("Code", "-"))
    review_label = str(row.get("review_label", ""))
    primary_gap = row.get("primary_gap_signal", "signal")
    gap_label = _signal_action_label(primary_gap)
    next_gate = str(row.get("next_gate_summary", "none"))
    if review_label in {"promotion_probe", "candidate_monitor"}:
        action = "review {label} gate".format(label=review_label.replace("_", "-"))
        note = (
            "Validate-now candidate {code} is near promotion on {gap_label}, but "
            "review_label={review_label} still blocks promotion. Priority view: {priority}. "
            "Promotion path: {path}. Gate status: {next_gate}. Current gaps: {gaps}"
        ).format(
            code=code,
            gap_label=gap_label,
            review_label=review_label,
            priority=row.get("validate_priority_summary", "none"),
            path=row.get("promotion_path_summary", "none"),
            next_gate=next_gate,
            gaps=row.get("missing_signal_gap_summary", "none"),
        )
        return action, note

    action = f"check {gap_label}"
    note = (
        "Validate-now candidate {code} is closest to promotion on {gap_label}; "
        "if that clears, act-now promotion can trigger. Priority view: {priority}. Promotion path: {path}. Current gaps: {gaps}"
    ).format(
        code=code,
        gap_label=gap_label,
        priority=row.get("validate_priority_summary", "none"),
        path=row.get("promotion_path_summary", "none"),
        gaps=row.get("missing_signal_gap_summary", "none"),
    )
    return action, note


def _resolve_dormant_gap_signal(row: dict[str, object]) -> str:
    primary_gap = row.get("primary_gap_signal")
    if primary_gap not in {None, "", "none"}:
        return str(primary_gap)
    gap_summary = str(row.get("missing_signal_gap_summary", "") or "")
    if ":" in gap_summary:
        return gap_summary.split(":", 1)[0].strip() or "signal"
    return "signal"


def _build_focus_operator_guidance(row: dict[str, object]) -> tuple[str, str]:
    action_label = str(row.get("action_label", ""))
    if action_label == "validate_now":
        return _validate_operator_guidance(row)

    code = str(row.get("Code", "-"))
    risk_status = str(row.get("act_now_risk_status", "off"))
    if risk_status not in {"hot", "warm"}:
        primary_gap = _resolve_dormant_gap_signal(row)
        gap_label = _signal_action_label(primary_gap)
        action = f"recover {gap_label}"
        note = (
            "Act-now candidate {code} is currently dormant, and the closest re-activation trigger is {gap_label}. "
            "Current gaps: {gaps}. Rule state: {rule_state}"
        ).format(
            code=code,
            gap_label=gap_label,
            gaps=row.get("missing_signal_gap_summary", "none"),
            rule_state=row.get("rule_trigger_summary", "none"),
        )
        return action, note

    weakest_signal = row.get("weakest_met_signal")
    if not weakest_signal:
        risk_summary = str(row.get("act_now_risk_summary", ""))
        marker = "weakest_signal="
        if marker in risk_summary:
            weakest_signal = risk_summary.split(marker, 1)[1].split(",", 1)[0].strip()
    weakest_signal = weakest_signal or "signal"
    weakest_label = _signal_action_label(weakest_signal)
    action = f"verify {weakest_label}"
    note = (
        "Act-now candidate {code} is still live, but its thinnest support is {weakest_label}; "
        "if that weakens, demotion risk increases. Demotion edge: {edge}. Current buffer view: {risk}"
    ).format(
        code=code,
        weakest_label=weakest_label,
        edge=row.get("demotion_edge_summary", "none"),
        risk=row.get("act_now_risk_summary", "none"),
    )
    return action, note


def _build_data_quality_focus(
    cycle_guard_payload: dict[str, object] | None,
    screening_quality: dict[str, object] | None,
) -> dict[str, object]:
    guard_quality = (cycle_guard_payload or {}).get("screening_quality", {}) or {}
    quality_status = str(
        guard_quality.get(
            "quality_status",
            (screening_quality or {}).get("quality_status", "unknown"),
        ) or "unknown"
    )
    if quality_status not in {"caution", "review"}:
        return {}

    guard_summary = str((cycle_guard_payload or {}).get("guard_summary", "none") or "none")
    breaches = list((cycle_guard_payload or {}).get("breaches", []) or [])
    quality_summary = str(
        guard_quality.get(
            "quality_summary",
            (screening_quality or {}).get("quality_summary", "none"),
        ) or "none"
    )
    quality_codes = guard_quality.get("codes", {}) or {}
    return {
        "focus_type": "data_quality_guard",
        "priority_bucket": -1,
        "severity": quality_status,
        "Code": "screening_quality",
        "Name": "Screening Quality",
        "rank_reference": 0,
        "summary": quality_summary,
        "next_gate_summary": guard_summary,
        "operator_action": "review screening quality",
        "operator_note": (
            "Screening quality is in {status} state, so operator decisions should be gated on data integrity first. "
            "Guard summary: {guard_summary}. Breaches: {breaches}. Quality codes: empty_price={empty_price}; invalid_momentum={invalid}."
        ).format(
            status=quality_status,
            guard_summary=guard_summary,
            breaches=",".join(breaches) if breaches else "none",
            empty_price=",".join(quality_codes.get("empty_price_codes_sample", []) or []) or "none",
            invalid=",".join(quality_codes.get("invalid_momentum_codes_sample", []) or []) or "none",
        ),
    }


def _build_focus_queue(
    action_memo_payload: dict[str, object],
    cycle_guard_payload: dict[str, object] | None = None,
    screening_quality: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    def _rank_key(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 999.0

    decisions = action_memo_payload.get("decisions", []) or []
    rows: list[dict[str, object]] = []
    data_quality_focus = _build_data_quality_focus(cycle_guard_payload, screening_quality)
    if data_quality_focus:
        rows.append(data_quality_focus)
    for row in decisions:
        action_label = str(row.get("action_label", ""))
        if action_label == "validate_now" and row.get("promotion_watch_status") in {"hot", "warm"}:
            watch_status = str(row.get("promotion_watch_status", "off"))
            operator_action, operator_note = _build_focus_operator_guidance(row)
            rows.append(
                {
                    "focus_type": "promotion_watch",
                    "priority_bucket": 0 if watch_status == "hot" else 2,
                    "severity": watch_status,
                    "Code": row.get("Code", "-"),
                    "Name": row.get("Name", "-"),
                    "review_label": row.get("review_label", "none"),
                    "rank_reference": row.get("validate_priority_rank", "-"),
                    "summary": row.get("promotion_watch_summary", "none"),
                    "priority_reason": (
                        "review_label={label} still blocks promotion".format(label=row.get("review_label"))
                        if row.get("review_label") in {"promotion_probe", "candidate_monitor"}
                        else row.get("validate_priority_summary", "none")
                    ),
                    "next_gate_summary": row.get("next_gate_summary", "-"),
                    "operator_action": operator_action,
                    "operator_note": operator_note,
                }
            )
        if action_label == "act_now" and row.get("act_now_risk_status") in {"hot", "warm"}:
            risk_status = str(row.get("act_now_risk_status", "off"))
            operator_action, operator_note = _build_focus_operator_guidance(row)
            rows.append(
                {
                    "focus_type": "act_now_risk",
                    "priority_bucket": 1 if risk_status == "hot" else 3,
                    "severity": risk_status,
                    "Code": row.get("Code", "-"),
                    "Name": row.get("Name", "-"),
                    "rank_reference": row.get("offensive_rank", "-"),
                    "summary": row.get("act_now_risk_summary", "none"),
                    "priority_reason": "weakest_margin={margin}, demotion_edge={edge}".format(
                        margin=_extract_summary_metric(row.get("act_now_risk_summary"), "weakest_margin", default="none"),
                        edge=row.get("demotion_edge_summary", "none"),
                    ),
                    "next_gate_summary": row.get("rule_trigger_summary", "-"),
                    "operator_action": operator_action,
                    "operator_note": operator_note,
                }
            )
        if action_label == "act_now" and row.get("act_now_risk_status") not in {"hot", "warm"}:
            operator_action, operator_note = _build_focus_operator_guidance(row)
            rows.append(
                {
                    "focus_type": "act_now_dormant",
                    "priority_bucket": 4,
                    "severity": "dormant",
                    "Code": row.get("Code", "-"),
                    "Name": row.get("Name", "-"),
                    "rank_reference": row.get("offensive_rank", "-"),
                    "summary": "dormant: primary_gap={primary_gap}, nearest_gap={nearest_gap}".format(
                        primary_gap=_resolve_dormant_gap_signal(row),
                        nearest_gap=_fmt_metric(row.get("nearest_signal_gap", "none")),
                    ),
                    "priority_reason": row.get("missing_signal_gap_summary", "none"),
                    "next_gate_summary": row.get("missing_signal_gap_summary", "-"),
                    "operator_action": operator_action,
                    "operator_note": operator_note,
                }
            )
    rows.sort(
        key=lambda row: (
            int(row.get("priority_bucket", 9)),
            _rank_key(row.get("rank_reference", 999)),
            str(row.get("Code", "")),
        )
    )
    for index, row in enumerate(rows[:5], start=1):
        row["focus_rank"] = index
    return rows[:5]


def _build_operator_board(
    act_now_rows: list[dict[str, object]],
    validate_now_rows: list[dict[str, object]],
    focus_queue: list[dict[str, object]],
    operator_runbook: list[dict[str, object]],
    cycle_guard_payload: dict[str, object] | None,
    screening_quality: dict[str, object] | None = None,
    validate_competition: dict[str, object] | None = None,
    act_now_competition: dict[str, object] | None = None,
    latest_update: dict[str, object] | None = None,
) -> dict[str, object]:
    data_quality_focus_count = sum(1 for row in focus_queue if row.get("focus_type") == "data_quality_guard")
    hot_watch_count = sum(1 for row in focus_queue if row.get("focus_type") == "promotion_watch" and row.get("severity") == "hot")
    warm_watch_count = sum(1 for row in focus_queue if row.get("focus_type") == "promotion_watch" and row.get("severity") == "warm")
    hot_risk_count = sum(1 for row in focus_queue if row.get("focus_type") == "act_now_risk" and row.get("severity") == "hot")
    warm_risk_count = sum(1 for row in focus_queue if row.get("focus_type") == "act_now_risk" and row.get("severity") == "warm")
    live_act_now_count = hot_risk_count + warm_risk_count
    dormant_act_now_rows = [row for row in act_now_rows if row.get("act_now_risk_status") not in {"hot", "warm"}]
    dormant_act_now_count = len(dormant_act_now_rows)
    dormant_summary = " | ".join(
        "{code} {name}".format(
            code=row.get("Code", "-"),
            name=row.get("Name", "-"),
        )
        for row in dormant_act_now_rows
    ) if dormant_act_now_rows else "none"
    top_focus = focus_queue[0] if focus_queue else {}
    top_focus_code = top_focus.get("Code", "-")
    top_focus_name = top_focus.get("Name", "-")
    top_focus_action = top_focus.get("operator_action", "none")
    top_focus_reason = _priority_reason(top_focus)
    top_focus_gate = _priority_gate_blocker(top_focus)
    top_focus_type = top_focus.get("focus_type", "none")
    guard_status = (cycle_guard_payload or {}).get("guard_status", "unknown")
    guard_summary = str((cycle_guard_payload or {}).get("guard_summary", "none") or "none")
    guard_breaches = list((cycle_guard_payload or {}).get("breaches", []) or [])
    guard_delta_summary = _render_guard_delta_summary(cycle_guard_payload)
    cycle_diff_labels = "previous={previous}; current={current}".format(
        previous=(cycle_guard_payload or {}).get("previous_label", "none") or "none",
        current=(cycle_guard_payload or {}).get("current_label", "none") or "none",
    )
    cycle_guard_context = "status={status}; previous={previous}; current={current}".format(
        status=(cycle_guard_payload or {}).get("guard_status", "none") or "none",
        previous=(cycle_guard_payload or {}).get("previous_label", "none") or "none",
        current=(cycle_guard_payload or {}).get("current_label", "none") or "none",
    )
    guard_quality = (cycle_guard_payload or {}).get("screening_quality", {}) or {}
    screening_quality = screening_quality or {}
    quality_summary = str(screening_quality.get("quality_summary", "none") or "none")
    latest_update = latest_update or {}

    if top_focus:
        headline = (
            "act_now={act_now_count}, validate_now={validate_now_count}, "
            "watch_hot={watch_hot}, risk_hot={risk_hot}, data_quality={data_quality}, top_focus={focus_type}:{code} {name}"
        ).format(
            act_now_count=len(act_now_rows),
            validate_now_count=len(validate_now_rows),
            watch_hot=hot_watch_count,
            risk_hot=hot_risk_count,
            data_quality=data_quality_focus_count,
            focus_type=top_focus_type,
            code=top_focus_code,
            name=top_focus_name,
        )
        primary_call = "{action} on {code} {name}".format(
            action=top_focus_action,
            code=top_focus_code,
            name=top_focus_name,
        )
    else:
        headline = (
            "act_now={act_now_count}, validate_now={validate_now_count}, "
            "watch_hot=0, risk_hot=0, data_quality={data_quality}, top_focus=none"
        ).format(
            act_now_count=len(act_now_rows),
            validate_now_count=len(validate_now_rows),
            data_quality=data_quality_focus_count,
        )
        primary_call = "no immediate operator focus"

    return {
        "headline": headline,
        "primary_call": primary_call,
        "priority_scan": "top_focus={focus_type}:{code}; gate_blocker={gate}; action={action}; reason={reason}".format(
            focus_type=top_focus_type,
            code=top_focus_code,
            gate=top_focus_gate,
            action=top_focus_action,
            reason=top_focus_reason,
        ) if top_focus else "top_focus=none; gate_blocker=none; action=none; reason=none",
        "watch_summary": "promotion_watch: hot={hot}, warm={warm}".format(
            hot=hot_watch_count,
            warm=warm_watch_count,
        ),
        "data_quality_focus_summary": "data_quality_guard: count={count}, status={status}".format(
            count=data_quality_focus_count,
            status=guard_quality.get("quality_status", "unknown"),
        ),
        "compare_summary": (validate_competition or {}).get("summary", "none"),
        "compare_summary_contract": (validate_competition or {}).get("summary_contract", "none"),
        "risk_compare_summary": (act_now_competition or {}).get("summary", "none"),
        "risk_compare_summary_contract": (act_now_competition or {}).get("summary_contract", "none"),
        "risk_summary": "act_now_risk: hot={hot}, warm={warm}".format(
            hot=hot_risk_count,
            warm=warm_risk_count,
        ),
        "live_summary": "act_now_live: live={live}, dormant={dormant}".format(
            live=live_act_now_count,
            dormant=dormant_act_now_count,
        ),
        "dormant_summary": "act_now_dormant: {summary}".format(summary=dormant_summary),
        "data_quality_summary": quality_summary,
        "guard_summary": "cycle_guard={status}; breaches={breaches}".format(
            status=guard_status,
            breaches=",".join(guard_breaches) if guard_breaches else "none",
        ),
        "cycle_diff_labels": cycle_diff_labels,
        "cycle_guard_context": cycle_guard_context,
        "guard_delta_summary": guard_delta_summary,
        "guard_note": guard_summary,
        "guard_breach_summary": ",".join(guard_breaches) if guard_breaches else "none",
        "guard_quality_status": guard_quality.get("quality_status", "unknown"),
        "guard_quality_summary": guard_quality.get("quality_summary", "none"),
        "latest_update_summary": "status={status}; reason={reason}".format(
            status=latest_update.get("status", "none"),
            reason=latest_update.get("reason", "none"),
        ),
    }


def _build_operator_runbook(
    validate_rows: list[dict[str, object]],
    act_now_defense_ladder: list[dict[str, object]],
    dormant_rows: list[dict[str, object]],
    cycle_guard_payload: dict[str, object] | None = None,
    screening_quality: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    data_quality_focus = _build_data_quality_focus(cycle_guard_payload, screening_quality)

    if data_quality_focus:
        steps.append(
            {
                "step_rank": 1,
                "step_type": "data_quality_check",
                "Code": data_quality_focus.get("Code", "-"),
                "Name": data_quality_focus.get("Name", "-"),
                "action": data_quality_focus.get("operator_action", "review screening quality"),
                "reason": data_quality_focus.get("summary", "none"),
            }
        )

    if validate_rows:
        primary = validate_rows[0]
        primary_action, _ = _validate_operator_guidance(primary)
        steps.append(
            {
                "step_rank": len(steps) + 1,
                "step_type": "promotion_check",
                "Code": primary.get("Code", "-"),
                "Name": primary.get("Name", "-"),
                "action": primary_action,
                "reason": primary.get("validate_priority_summary", "none"),
            }
        )
    if len(validate_rows) > 1:
        secondary = validate_rows[1]
        secondary_action, _ = _validate_operator_guidance(secondary)
        steps.append(
            {
                "step_rank": len(steps) + 1,
                "step_type": "promotion_backup",
                "Code": secondary.get("Code", "-"),
                "Name": secondary.get("Name", "-"),
                "action": secondary_action if secondary_action.startswith("review ") else "keep warm watch on {signal}".format(
                    signal=_signal_action_label(_resolve_promotion_signal(secondary))
                ),
                "reason": secondary.get("validate_priority_summary", "none"),
            }
        )
    if act_now_defense_ladder:
        primary_defense = act_now_defense_ladder[0]
        steps.append(
            {
                "step_rank": len(steps) + 1,
                "step_type": "defense_watch",
                "Code": primary_defense.get("Code", "-"),
                "Name": primary_defense.get("Name", "-"),
                "action": "verify {signal}".format(
                    signal=_signal_action_label(primary_defense.get("weakest_signal"))
                ),
                "reason": "weakest_margin={margin}, demotion_edge={edge}".format(
                    margin=primary_defense.get("weakest_margin", "-"),
                    edge=primary_defense.get("demotion_edge_summary", "none"),
                ),
            }
        )
    if dormant_rows:
        primary_dormant = dormant_rows[0]
        dormant_action, _ = _build_focus_operator_guidance(primary_dormant)
        steps.append(
            {
                "step_rank": len(steps) + 1,
                "step_type": "dormant_watch",
                "Code": primary_dormant.get("Code", "-"),
                "Name": primary_dormant.get("Name", "-"),
                "action": dormant_action,
                "reason": primary_dormant.get("missing_signal_gap_summary", "none"),
            }
        )
    return steps


def _build_validate_competition(validate_rows: list[dict[str, object]]) -> dict[str, object]:
    if len(validate_rows) < 2:
        if not validate_rows:
            return {
                "summary": "none",
                "summary_contract": "none",
                "rationale_contract": "none",
            }
        leader = validate_rows[0]
        leader_next_gate, leader_gap_summary = _split_gate_status(leader.get("next_gate_summary", "none"))
        return {
            "leader_code": leader.get("Code", "-"),
            "leader_name": leader.get("Name", "-"),
            "leader_primary_gap": leader.get("primary_gap_signal", "none"),
            "leader_nearest_gap": leader.get("nearest_signal_gap", "none"),
            "leader_total_gap": leader.get("total_signal_gap", "none"),
            "leader_next_gate": leader_next_gate,
            "leader_gap_summary": leader_gap_summary,
            "challenger_code": "none",
            "challenger_name": "none",
            "challenger_primary_gap": "none",
            "challenger_nearest_gap": "none",
            "challenger_total_gap": "none",
            "challenger_next_gate": "none",
            "challenger_gap_summary": "none",
            "nearest_gap_edge": "none",
            "total_gap_edge": "none",
            "readiness_edge": "none",
            "summary": "single validate-now candidate remains: {code} {name}".format(
                code=leader.get("Code", "-"),
                name=leader.get("Name", "-"),
            ),
            "rationale": (
                "{leader_code} is the only validate-now candidate, and its closest unfinished trigger is {leader_primary} at {leader_nearest}; "
                "total unfinished gap is {leader_total}. Current gate: {leader_gate}."
            ).format(
                leader_code=leader.get("Code", "-"),
                leader_primary=leader.get("primary_gap_signal", "none"),
                leader_nearest=_fmt_metric(leader.get("nearest_signal_gap", 0)),
                leader_total=_fmt_metric(leader.get("total_signal_gap", 0)),
                leader_gate=leader.get("next_gate_summary", "none"),
            ),
            "summary_contract": "mode=single; leader={leader}; challenger=none".format(
                leader=leader.get("Code", "-"),
            ),
            "rationale_contract": (
                "mode=single; leader={leader}; challenger=none; ordering_basis=only_validate_now_candidate; "
                "primary_gap={primary_gap}; nearest_gap={nearest_gap}; total_gap={total_gap}; next_gate={next_gate}"
            ).format(
                leader=leader.get("Code", "-"),
                primary_gap=leader.get("primary_gap_signal", "none"),
                nearest_gap=_fmt_metric(leader.get("nearest_signal_gap", "none")),
                total_gap=_fmt_metric(leader.get("total_signal_gap", "none")),
                next_gate=leader_next_gate,
            ),
        }

    ordered = sorted(
        validate_rows,
        key=lambda row: (
            int(row.get("validate_priority_rank", 999) or 999),
            float(row.get("nearest_signal_gap", 999.0) or 999.0),
            float(row.get("total_signal_gap", 999.0) or 999.0),
            -float(row.get("promotion_readiness_score", 0.0) or 0.0),
        ),
    )
    leader = ordered[0]
    challenger = ordered[1]
    leader_next_gate, leader_gap_summary = _split_gate_status(leader.get("next_gate_summary", "none"))
    challenger_next_gate, challenger_gap_summary = _split_gate_status(challenger.get("next_gate_summary", "none"))
    nearest_gap_edge = round(
        float(challenger.get("nearest_signal_gap", 0.0) or 0.0) - float(leader.get("nearest_signal_gap", 0.0) or 0.0),
        2,
    )
    total_gap_edge = round(
        float(challenger.get("total_signal_gap", 0.0) or 0.0) - float(leader.get("total_signal_gap", 0.0) or 0.0),
        2,
    )
    readiness_edge = round(
        float(leader.get("promotion_readiness_score", 0.0) or 0.0) - float(challenger.get("promotion_readiness_score", 0.0) or 0.0),
        2,
    )
    summary = (
        "{leader_code} {leader_name} leads {challenger_code} {challenger_name}: "
        "nearest_gap_edge={nearest_gap_edge}, total_gap_edge={total_gap_edge}, readiness_edge={readiness_edge}"
    ).format(
        leader_code=leader.get("Code", "-"),
        leader_name=leader.get("Name", "-"),
        challenger_code=challenger.get("Code", "-"),
        challenger_name=challenger.get("Name", "-"),
        nearest_gap_edge=nearest_gap_edge,
        total_gap_edge=total_gap_edge,
        readiness_edge=readiness_edge,
    )
    rationale = (
        "{leader_code} stays ahead because its closest missing trigger is {leader_primary} at {leader_nearest}, "
        "versus {challenger_code} at {challenger_nearest}; total unfinished gap is {leader_total} versus {challenger_total}."
    ).format(
        leader_code=leader.get("Code", "-"),
        leader_primary=leader.get("primary_gap_signal", "none"),
        leader_nearest=_fmt_metric(leader.get("nearest_signal_gap", 0)),
        challenger_code=challenger.get("Code", "-"),
        challenger_nearest=_fmt_metric(challenger.get("nearest_signal_gap", 0)),
        leader_total=_fmt_metric(leader.get("total_signal_gap", 0)),
        challenger_total=_fmt_metric(challenger.get("total_signal_gap", 0)),
    )
    return {
        "leader_code": leader.get("Code", "-"),
        "leader_name": leader.get("Name", "-"),
        "leader_primary_gap": leader.get("primary_gap_signal", "none"),
        "leader_nearest_gap": leader.get("nearest_signal_gap", "none"),
        "leader_total_gap": leader.get("total_signal_gap", "none"),
        "leader_next_gate": leader_next_gate,
        "leader_gap_summary": leader_gap_summary,
        "challenger_code": challenger.get("Code", "-"),
        "challenger_name": challenger.get("Name", "-"),
        "challenger_primary_gap": challenger.get("primary_gap_signal", "none"),
        "challenger_nearest_gap": challenger.get("nearest_signal_gap", "none"),
        "challenger_total_gap": challenger.get("total_signal_gap", "none"),
        "challenger_next_gate": challenger_next_gate,
        "challenger_gap_summary": challenger_gap_summary,
        "nearest_gap_edge": nearest_gap_edge,
        "total_gap_edge": total_gap_edge,
        "readiness_edge": readiness_edge,
        "summary": summary,
        "rationale": rationale,
        "summary_contract": (
            "mode=ordered; leader={leader}; challenger={challenger}; nearest_gap_edge={nearest_gap_edge}; "
            "total_gap_edge={total_gap_edge}; readiness_edge={readiness_edge}"
        ).format(
            leader=leader.get("Code", "-"),
            challenger=challenger.get("Code", "-"),
            nearest_gap_edge=_fmt_metric(nearest_gap_edge),
            total_gap_edge=_fmt_metric(total_gap_edge),
            readiness_edge=_fmt_metric(readiness_edge),
        ),
        "rationale_contract": (
            "mode=ordered; leader={leader}; challenger={challenger}; ordering_basis=nearest_gap_then_total_gap_then_readiness; "
            "leader_primary_gap={leader_primary_gap}; leader_nearest_gap={leader_nearest_gap}; leader_total_gap={leader_total_gap}; "
            "challenger_primary_gap={challenger_primary_gap}; challenger_nearest_gap={challenger_nearest_gap}; "
            "challenger_total_gap={challenger_total_gap}; nearest_gap_edge={nearest_gap_edge}; total_gap_edge={total_gap_edge}; "
            "readiness_edge={readiness_edge}"
        ).format(
            leader=leader.get("Code", "-"),
            challenger=challenger.get("Code", "-"),
            leader_primary_gap=leader.get("primary_gap_signal", "none"),
            leader_nearest_gap=_fmt_metric(leader.get("nearest_signal_gap", "none")),
            leader_total_gap=_fmt_metric(leader.get("total_signal_gap", "none")),
            challenger_primary_gap=challenger.get("primary_gap_signal", "none"),
            challenger_nearest_gap=_fmt_metric(challenger.get("nearest_signal_gap", "none")),
            challenger_total_gap=_fmt_metric(challenger.get("total_signal_gap", "none")),
            nearest_gap_edge=_fmt_metric(nearest_gap_edge),
            total_gap_edge=_fmt_metric(total_gap_edge),
            readiness_edge=_fmt_metric(readiness_edge),
        ),
    }


def _build_act_now_competition(act_now_rows: list[dict[str, object]]) -> dict[str, object]:
    if len(act_now_rows) < 2:
        if not act_now_rows:
            return {
                "summary": "none",
                "summary_contract": "none",
                "rationale_contract": "none",
            }
        leader = act_now_rows[0]
        leader_signal = str(leader.get("weakest_met_signal", "none"))
        if leader_signal in {"", "none"}:
            leader_signal = str(_build_act_now_defense_ladder({"decisions": [leader]})[0].get("weakest_signal", "none"))
        leader_margin = _extract_summary_metric(leader.get("act_now_risk_summary"), "weakest_margin", default=999.0)
        return {
            "leader_code": leader.get("Code", "-"),
            "leader_name": leader.get("Name", "-"),
            "leader_risk_status": leader.get("act_now_risk_status", "off"),
            "leader_weakest_signal": leader_signal,
            "leader_weakest_margin": leader_margin,
            "challenger_code": "none",
            "challenger_name": "none",
            "challenger_risk_status": "off",
            "challenger_weakest_signal": "none",
            "challenger_weakest_margin": "none",
            "margin_edge": "none",
            "score_edge": "none",
            "summary": "single act-now name remains: {code} {name}".format(
                code=leader.get("Code", "-"),
                name=leader.get("Name", "-"),
            ),
            "summary_contract": "mode=single; leader={leader}; challenger=none".format(
                leader=leader.get("Code", "-"),
            ),
            "rationale_contract": (
                "mode=single; leader={leader}; challenger=none; ordering_basis=only_act_now_candidate; "
                "leader_risk_status={leader_risk_status}; leader_weakest_signal={leader_weakest_signal}; leader_weakest_margin={leader_weakest_margin}"
            ).format(
                leader=leader.get("Code", "-"),
                leader_risk_status=leader.get("act_now_risk_status", "off"),
                leader_weakest_signal=leader_signal,
                leader_weakest_margin=_fmt_metric(leader_margin),
            ),
        }

    ordered = sorted(
        act_now_rows,
        key=lambda row: (
            0 if row.get("act_now_risk_status") == "hot" else 1,
            float(row.get("offensive_rank", 999.0) or 999.0),
            -float(row.get("offensive_score", 0.0) or 0.0),
            str(row.get("Code", "")),
        ),
    )
    leader = ordered[0]
    challenger = ordered[1]
    leader_status = str(leader.get("act_now_risk_status", "off"))
    challenger_status = str(challenger.get("act_now_risk_status", "off"))
    leader_signal = str(leader.get("weakest_met_signal", "none"))
    challenger_signal = str(challenger.get("weakest_met_signal", "none"))
    if leader_signal in {"", "none"}:
        leader_signal = str(_build_act_now_defense_ladder({"decisions": [leader]})[0].get("weakest_signal", "none"))
    if challenger_signal in {"", "none"}:
        challenger_signal = str(_build_act_now_defense_ladder({"decisions": [challenger]})[0].get("weakest_signal", "none"))
    leader_margin = _extract_summary_metric(leader.get("act_now_risk_summary"), "weakest_margin", default=999.0)
    challenger_margin = _extract_summary_metric(challenger.get("act_now_risk_summary"), "weakest_margin", default=999.0)
    margin_edge = round(challenger_margin - leader_margin, 2)
    score_edge = round(
        float(leader.get("offensive_score", 0.0) or 0.0) - float(challenger.get("offensive_score", 0.0) or 0.0),
        2,
    )
    ladder_summary = " -> ".join(
        "{code} {name} ({signal}, margin={margin}, rank={rank})".format(
            code=row.get("Code", "-"),
            name=row.get("Name", "-"),
            signal=(
                row.get("weakest_met_signal")
                or _build_act_now_defense_ladder({"decisions": [row]})[0].get("weakest_signal", "none")
            ),
            margin=_extract_summary_metric(row.get("act_now_risk_summary"), "weakest_margin", default=999.0),
            rank=row.get("offensive_rank", "-"),
        )
        for row in ordered
    )
    summary = "act-now defense order: {ladder}".format(ladder=ladder_summary)
    if leader_status != challenger_status:
        rationale = (
            "{leader_code} comes first because its risk status is {leader_status} versus {challenger_status}; "
            "weakest supports are {leader_signal} margin {leader_margin} and {challenger_signal} margin {challenger_margin}."
        ).format(
            leader_code=leader.get("Code", "-"),
            leader_status=leader_status,
            challenger_status=challenger_status,
            leader_signal=leader_signal,
            leader_margin=_fmt_metric(leader_margin),
            challenger_signal=challenger_signal,
            challenger_margin=_fmt_metric(challenger_margin),
        )
    elif leader_signal == challenger_signal:
        rationale = (
            "{leader_code} comes first because both names share weakest signal {leader_signal}, "
            "and the tie breaks on offensive rank {leader_rank} versus {challenger_rank}; weakest margins are {leader_margin} and {challenger_margin}."
        ).format(
            leader_code=leader.get("Code", "-"),
            leader_signal=leader_signal,
            leader_rank=leader.get("offensive_rank", "-"),
            challenger_rank=challenger.get("offensive_rank", "-"),
            leader_margin=_fmt_metric(leader_margin),
            challenger_margin=_fmt_metric(challenger_margin),
        )
    else:
        rationale = (
            "{leader_code} comes first because both names sit in the same {leader_status} risk band, "
            "and the defense queue breaks the tie on offensive rank {leader_rank} versus {challenger_rank}; "
            "weakest supports are {leader_signal} margin {leader_margin} and {challenger_signal} margin {challenger_margin}."
        ).format(
            leader_code=leader.get("Code", "-"),
            leader_status=leader_status,
            leader_rank=leader.get("offensive_rank", "-"),
            challenger_rank=challenger.get("offensive_rank", "-"),
            leader_signal=leader_signal,
            leader_margin=_fmt_metric(leader_margin),
            challenger_signal=challenger_signal,
            challenger_margin=_fmt_metric(challenger_margin),
        )
    if leader_status != challenger_status:
        ordering_basis = "risk_status_then_rank"
    elif leader_signal == challenger_signal:
        ordering_basis = "shared_weakest_signal_then_rank"
    else:
        ordering_basis = "same_risk_band_then_rank"
    return {
        "leader_code": leader.get("Code", "-"),
        "leader_name": leader.get("Name", "-"),
        "leader_risk_status": leader_status,
        "leader_weakest_signal": leader_signal,
        "leader_weakest_margin": leader_margin,
        "challenger_code": challenger.get("Code", "-"),
        "challenger_name": challenger.get("Name", "-"),
        "challenger_risk_status": challenger_status,
        "challenger_weakest_signal": challenger_signal,
        "challenger_weakest_margin": challenger_margin,
        "margin_edge": margin_edge,
        "score_edge": score_edge,
        "ladder_summary": ladder_summary,
        "summary": summary,
        "rationale": rationale,
        "summary_contract": (
            "mode=ordered; leader={leader}; challenger={challenger}; margin_edge={margin_edge}; score_edge={score_edge}"
        ).format(
            leader=leader.get("Code", "-"),
            challenger=challenger.get("Code", "-"),
            margin_edge=_fmt_metric(margin_edge),
            score_edge=_fmt_metric(score_edge),
        ),
        "rationale_contract": (
            "mode=ordered; leader={leader}; challenger={challenger}; ordering_basis={ordering_basis}; "
            "leader_risk_status={leader_risk_status}; challenger_risk_status={challenger_risk_status}; "
            "leader_weakest_signal={leader_weakest_signal}; challenger_weakest_signal={challenger_weakest_signal}; "
            "leader_weakest_margin={leader_weakest_margin}; challenger_weakest_margin={challenger_weakest_margin}; "
            "margin_edge={margin_edge}; score_edge={score_edge}"
        ).format(
            leader=leader.get("Code", "-"),
            challenger=challenger.get("Code", "-"),
            ordering_basis=ordering_basis,
            leader_risk_status=leader_status,
            challenger_risk_status=challenger_status,
            leader_weakest_signal=leader_signal,
            challenger_weakest_signal=challenger_signal,
            leader_weakest_margin=_fmt_metric(leader_margin),
            challenger_weakest_margin=_fmt_metric(challenger_margin),
            margin_edge=_fmt_metric(margin_edge),
            score_edge=_fmt_metric(score_edge),
        ),
    }


def _extract_summary_metric(summary: object, key: str, default: float = 0.0) -> float:
    text = str(summary or "")
    marker = key + "="
    if marker not in text:
        return default
    value_text = text.split(marker, 1)[1].split(",", 1)[0].strip()
    try:
        return float(value_text)
    except ValueError:
        return default


def _augment_cycle_guard_payload(
    cycle_guard_payload: dict[str, object] | None,
    cycle_diff_payload: dict[str, object] | None,
) -> dict[str, object] | None:
    if not cycle_guard_payload:
        return None
    if not cycle_diff_payload:
        return dict(cycle_guard_payload)

    guard_payload = dict(cycle_guard_payload)
    top_changes = cycle_diff_payload.get("top_candidate_score_changes", []) or []
    largest_score_change = "none"
    largest_rank_change = "none"
    if top_changes:
        largest_score_change = max(
            (abs(float(row.get("score_change", 0.0) or 0.0)) for row in top_changes),
            default=0.0,
        )
        largest_rank_change = max(
            (abs(float(row.get("rank_change", 0.0) or 0.0)) for row in top_changes),
            default=0.0,
        )

    guard_payload["previous_label"] = cycle_diff_payload.get("previous_label", guard_payload.get("previous_label", "none"))
    guard_payload["current_label"] = cycle_diff_payload.get("current_label", guard_payload.get("current_label", "none"))
    guard_payload["metrics"] = {
        **(guard_payload.get("metrics", {}) or {}),
        "act_now_count_change_abs": abs(int(cycle_diff_payload.get("act_now_count_change", 0) or 0)),
        "validate_now_count_change_abs": abs(int(cycle_diff_payload.get("validate_now_count_change", 0) or 0)),
        "act_now_membership_change": len(cycle_diff_payload.get("act_now_added", []) or []) + len(cycle_diff_payload.get("act_now_removed", []) or []),
        "validate_now_membership_change": len(cycle_diff_payload.get("validate_now_added", []) or []) + len(cycle_diff_payload.get("validate_now_removed", []) or []),
        "largest_score_change": largest_score_change,
        "largest_rank_change": largest_rank_change,
    }
    return guard_payload


def build_handoff_summary_payload(
    model_cycle_payload: dict[str, object],
    action_memo_payload: dict[str, object],
    candidate_packet_payload: dict[str, object],
    cycle_diff_payload: dict[str, object] | None = None,
    cycle_guard_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    cycle_guard_payload = _augment_cycle_guard_payload(cycle_guard_payload, cycle_diff_payload)
    act_now = _build_act_now_rows(action_memo_payload)
    act_now_risk = _build_act_now_risk_rows(action_memo_payload)
    validate_now = _build_validate_now_rows(action_memo_payload)
    top_candidates = (candidate_packet_payload.get("candidates", []) or [])[:5]
    focus_queue = _build_focus_queue(
        action_memo_payload,
        cycle_guard_payload,
        model_cycle_payload.get("screening_quality", {}) or {},
    )
    validate_competition = _build_validate_competition(validate_now)
    act_now_competition = _build_act_now_competition(act_now_risk)
    act_now_defense_ladder = _build_act_now_defense_ladder({"decisions": act_now_risk})
    act_now_dormant = [row for row in act_now if row.get("act_now_risk_status") not in {"hot", "warm"}]
    operator_runbook = _build_operator_runbook(
        validate_now,
        act_now_defense_ladder,
        act_now_dormant,
        cycle_guard_payload,
        model_cycle_payload.get("screening_quality", {}) or {},
    )

    payload = {
        "screening_row_count": int(model_cycle_payload.get("screening_row_count", 0)),
        "filtered_row_count": int(model_cycle_payload.get("filtered_row_count", 0)),
        "shortlist_count": int(model_cycle_payload.get("shortlist_count", 0)),
        "screening_quality": model_cycle_payload.get("screening_quality", {}) or {},
        "latest_update": model_cycle_payload.get("latest_update", {}) or {},
        "act_now_count": int(action_memo_payload.get("act_now_count", 0)),
        "validate_now_count": int(action_memo_payload.get("validate_now_count", 0)),
        "act_now_live_count": len(act_now_defense_ladder),
        "act_now_dormant_count": max(int(action_memo_payload.get("act_now_count", 0)) - len(act_now_defense_ladder), 0),
        "act_now_dormant": act_now_dormant,
        "act_now": act_now,
        "validate_now": validate_now,
        "act_now_demotions": _build_act_now_demotion_rows(action_memo_payload, cycle_diff_payload),
        "act_now_promotions": _build_act_now_promotion_rows(action_memo_payload, cycle_diff_payload),
        "validate_priority": _build_validate_priority_rows(action_memo_payload),
        "promotion_watch": _build_promotion_watch_rows(action_memo_payload),
        "act_now_risk": act_now_risk,
        "validate_competition": validate_competition,
        "act_now_competition": act_now_competition,
        "act_now_defense_ladder": act_now_defense_ladder,
        "operator_runbook": operator_runbook,
        "focus_queue": focus_queue,
        "operator_board": _build_operator_board(
            act_now,
            validate_now,
            focus_queue,
            operator_runbook,
            cycle_guard_payload,
            model_cycle_payload.get("screening_quality", {}) or {},
            validate_competition,
            act_now_competition,
            model_cycle_payload.get("latest_update", {}) or {},
        ),
        "top_candidates": top_candidates,
    }
    if cycle_diff_payload:
        payload["cycle_diff"] = {
            "previous_label": cycle_diff_payload.get("previous_label"),
            "current_label": cycle_diff_payload.get("current_label"),
            "act_now_count_change": cycle_diff_payload.get("act_now_count_change", 0),
            "validate_now_count_change": cycle_diff_payload.get("validate_now_count_change", 0),
            "action_state_changes": (cycle_diff_payload.get("action_state_changes", []) or [])[:5],
            "validate_priority_changes": (cycle_diff_payload.get("validate_priority_changes", []) or [])[:5],
            "act_now_risk_changes": (cycle_diff_payload.get("act_now_risk_changes", []) or [])[:5],
            "top_candidate_score_changes": (cycle_diff_payload.get("top_candidate_score_changes", []) or [])[:3],
        }
    if cycle_guard_payload:
        payload["cycle_guard"] = {
            "previous_label": cycle_guard_payload.get("previous_label"),
            "current_label": cycle_guard_payload.get("current_label"),
            "metrics": cycle_guard_payload.get("metrics", {}) or {},
            "guard_status": cycle_guard_payload.get("guard_status"),
            "guard_summary": cycle_guard_payload.get("guard_summary"),
            "act_now_stability": cycle_guard_payload.get("act_now_stability", []) or [],
            "caution_flags": cycle_guard_payload.get("caution_flags", []) or [],
            "review_flags": cycle_guard_payload.get("review_flags", []) or [],
            "breaches": cycle_guard_payload.get("breaches", []) or [],
            "screening_quality": cycle_guard_payload.get("screening_quality", {}) or {},
        }
    return payload


def render_handoff_summary(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Handoff Summary",
        "",
        f"- screening_row_count: {payload.get('screening_row_count', 0)}",
        f"- filtered_row_count: {payload.get('filtered_row_count', 0)}",
        f"- shortlist_count: {payload.get('shortlist_count', 0)}",
        f"- act_now_count: {payload.get('act_now_count', 0)}",
        f"- validate_now_count: {payload.get('validate_now_count', 0)}",
        f"- act_now_live_count: {payload.get('act_now_live_count', 0)}",
        f"- act_now_dormant_count: {payload.get('act_now_dormant_count', 0)}",
    ]
    screening_quality = payload.get("screening_quality", {}) or {}
    if screening_quality:
        lines.extend(
            [
                "- screening_quality: {summary}".format(
                    summary=screening_quality.get("quality_summary", "none"),
                ),
                "- screening_quality_codes: empty_price={empty_price}, invalid_momentum={invalid}".format(
                    empty_price=",".join(screening_quality.get("empty_price_codes_sample", []) or []) or "none",
                    invalid=",".join(screening_quality.get("invalid_momentum_codes_sample", []) or []) or "none",
                ),
            ]
        )
    cycle_diff = payload.get("cycle_diff")
    if cycle_diff:
        lines.extend(
            [
                f"- previous_label: {cycle_diff.get('previous_label', '-')}",
                f"- current_label: {cycle_diff.get('current_label', '-')}",
                f"- act_now_count_change: {cycle_diff.get('act_now_count_change', 0)}",
                f"- validate_now_count_change: {cycle_diff.get('validate_now_count_change', 0)}",
            ]
        )
    cycle_guard = payload.get("cycle_guard")
    if cycle_guard:
        lines.extend(
            [
                f"- guard_status: {cycle_guard.get('guard_status', '-')}",
                f"- guard_summary: {cycle_guard.get('guard_summary', '-')}",
            ]
        )

    lines.extend(["", "## Operator Board"])
    operator_board = payload.get("operator_board", {}) or {}
    lines.extend(
        [
            "- headline: {headline}".format(headline=operator_board.get("headline", "-")),
            "- primary_call: {primary_call}".format(primary_call=operator_board.get("primary_call", "-")),
            "- priority_scan: {priority_scan}".format(priority_scan=operator_board.get("priority_scan", "-")),
            "- watch_summary: {watch_summary}".format(watch_summary=operator_board.get("watch_summary", "-")),
            "- data_quality_focus_summary: {data_quality_focus_summary}".format(data_quality_focus_summary=operator_board.get("data_quality_focus_summary", "-")),
            "- compare_summary: {compare_summary}".format(compare_summary=operator_board.get("compare_summary", "-")),
            "- compare_summary_contract: {compare_summary_contract}".format(compare_summary_contract=operator_board.get("compare_summary_contract", "-")),
            "- risk_compare_summary: {risk_compare_summary}".format(risk_compare_summary=operator_board.get("risk_compare_summary", "-")),
            "- risk_compare_summary_contract: {risk_compare_summary_contract}".format(risk_compare_summary_contract=operator_board.get("risk_compare_summary_contract", "-")),
            "- risk_summary: {risk_summary}".format(risk_summary=operator_board.get("risk_summary", "-")),
            "- live_summary: {live_summary}".format(live_summary=operator_board.get("live_summary", "-")),
            "- dormant_summary: {dormant_summary}".format(dormant_summary=operator_board.get("dormant_summary", "-")),
            "- data_quality_summary: {data_quality_summary}".format(data_quality_summary=operator_board.get("data_quality_summary", "-")),
            "- guard_summary: {guard_summary}".format(guard_summary=operator_board.get("guard_summary", "-")),
            "- cycle_diff_labels: {cycle_diff_labels}".format(cycle_diff_labels=operator_board.get("cycle_diff_labels", "-")),
            "- cycle_guard_context: {cycle_guard_context}".format(cycle_guard_context=operator_board.get("cycle_guard_context", "-")),
            "- guard_delta_summary: {guard_delta_summary}".format(guard_delta_summary=operator_board.get("guard_delta_summary", "-")),
            "- guard_note: {guard_note}".format(guard_note=operator_board.get("guard_note", "-")),
            "- guard_breach_summary: {guard_breach_summary}".format(guard_breach_summary=operator_board.get("guard_breach_summary", "-")),
            "- guard_quality_status: {guard_quality_status}".format(guard_quality_status=operator_board.get("guard_quality_status", "-")),
            "- guard_quality_summary: {guard_quality_summary}".format(guard_quality_summary=operator_board.get("guard_quality_summary", "-")),
            "- latest_update_summary: {latest_update_summary}".format(latest_update_summary=operator_board.get("latest_update_summary", "-")),
        ]
    )

    lines.extend(["", "## Validate Competition"])
    validate_competition = payload.get("validate_competition", {}) or {}
    if validate_competition and validate_competition.get("summary") not in {None, "none"}:
        lines.append("- summary: {summary}".format(summary=validate_competition.get("summary", "-")))
        if validate_competition.get("summary_contract"):
            lines.append("- summary_contract: {summary_contract}".format(summary_contract=validate_competition.get("summary_contract", "-")))
        if validate_competition.get("rationale"):
            lines.append("- rationale: {rationale}".format(rationale=validate_competition.get("rationale", "-")))
        if validate_competition.get("rationale_contract"):
            lines.append("- rationale_contract: {rationale_contract}".format(rationale_contract=validate_competition.get("rationale_contract", "-")))
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now Competition"])
    act_now_competition = payload.get("act_now_competition", {}) or {}
    if act_now_competition and act_now_competition.get("summary") not in {None, "none"}:
        lines.append("- summary: {summary}".format(summary=act_now_competition.get("summary", "-")))
        if act_now_competition.get("summary_contract"):
            lines.append("- summary_contract: {summary_contract}".format(summary_contract=act_now_competition.get("summary_contract", "-")))
        if act_now_competition.get("rationale"):
            lines.append("- rationale: {rationale}".format(rationale=act_now_competition.get("rationale", "-")))
        if act_now_competition.get("rationale_contract"):
            lines.append("- rationale_contract: {rationale_contract}".format(rationale_contract=act_now_competition.get("rationale_contract", "-")))
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now Defense Ladder"])
    act_now_defense_ladder = payload.get("act_now_defense_ladder", []) or []
    if act_now_defense_ladder:
        for row in act_now_defense_ladder:
            lines.append(
                "- rank={rank} {code} {name}: risk_status={status}, weakest_margin={margin}, weakest_signal={signal}, offensive_rank={offensive_rank}, offensive_score={offensive_score}, demotion_edge={edge}".format(
                    rank=row.get("defense_rank", "-"),
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    status=row.get("risk_status", "off"),
                    margin=row.get("weakest_margin", "-"),
                    signal=row.get("weakest_signal", "none"),
                    offensive_rank=row.get("offensive_rank", "-"),
                    offensive_score=row.get("offensive_score", "-"),
                    edge=row.get("demotion_edge_summary", "none"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Operator Runbook"])
    operator_runbook = payload.get("operator_runbook", []) or []
    if operator_runbook:
        for row in operator_runbook:
            lines.append(
                "- step={step} type={step_type} {code} {name}: action={action}, reason={reason}".format(
                    step=row.get("step_rank", "-"),
                    step_type=row.get("step_type", "-"),
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    action=row.get("action", "-"),
                    reason=row.get("reason", "none"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Focus Queue"])
    focus_queue = payload.get("focus_queue", []) or []
    if focus_queue:
        for row in focus_queue:
            lines.append(
                "- rank={focus_rank} type={focus_type} severity={severity} {code} {name}: reference_rank={reference_rank}, summary={summary}, action={action}, note={note}, next_step={next_step}".format(
                    focus_rank=row.get("focus_rank", "-"),
                    focus_type=row.get("focus_type", "-"),
                    severity=row.get("severity", "-"),
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    reference_rank=row.get("rank_reference", "-"),
                    summary=row.get("summary", "none"),
                    action=row.get("operator_action", "-"),
                    note=row.get("operator_note", "-"),
                    next_step=row.get("next_gate_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Recent Changes"])
    if cycle_diff:
        changes = cycle_diff.get("top_candidate_score_changes", []) or []
        if changes:
            for row in changes:
                lines.append(
                    "- {code} {name}: score_change={score_change}, rank_change={rank_change}".format(
                        code=row.get("Code", "-"),
                        name=row.get("Name", "-"),
                        score_change=row.get("score_change", 0),
                        rank_change=row.get("rank_change", 0),
                    )
                )
        else:
            lines.append("- none")
    else:
        lines.append("- none")

    lines.extend(["", "## Rule State Changes"])
    if cycle_diff:
        action_state_changes = cycle_diff.get("action_state_changes", []) or []
        if action_state_changes:
            for row in action_state_changes:
                lines.append(
                    "- {code} {name}: action_label={previous}->{current}, confirmation_count_change={delta}, signals_added={added}, signals_removed={removed}, current_rule_trigger={trigger}".format(
                        code=row.get("Code", "-"),
                        name=row.get("Name", "-"),
                        previous=row.get("previous_action_label", "-"),
                        current=row.get("current_action_label", "-"),
                        delta=row.get("confirmation_count_change", 0),
                        added=",".join(str(item) for item in row.get("signals_added", []) or ["none"]),
                        removed=",".join(str(item) for item in row.get("signals_removed", []) or ["none"]),
                        trigger=row.get("current_rule_trigger_summary", "-"),
                    )
                )
        else:
            lines.append("- none")
    else:
        lines.append("- none")

    lines.extend(["", "## Validate Priority Trend"])
    if cycle_diff:
        validate_priority_changes = cycle_diff.get("validate_priority_changes", []) or []
        if validate_priority_changes:
            for row in validate_priority_changes:
                lines.append(
                    "- {code} {name}: action_label={previous}->{current}, priority_rank={previous_rank}->{current_rank}, readiness_score_change={readiness_change}, gap_count_change={gap_change}, primary_gap={previous_gap}->{current_gap}".format(
                        code=row.get("Code", "-"),
                        name=row.get("Name", "-"),
                        previous=row.get("previous_action_label", "-"),
                        current=row.get("current_action_label", "-"),
                        previous_rank=row.get("previous_validate_priority_rank", "-"),
                        current_rank=row.get("current_validate_priority_rank", "-"),
                        readiness_change=row.get("readiness_score_change", 0),
                        gap_change=row.get("gap_count_change", 0),
                        previous_gap=row.get("previous_primary_gap_signal", "none"),
                        current_gap=row.get("current_primary_gap_signal", "none"),
                    )
                )
        else:
            lines.append("- none")
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now Risk Trend"])
    if cycle_diff:
        act_now_risk_changes = cycle_diff.get("act_now_risk_changes", []) or []
        if act_now_risk_changes:
            for row in act_now_risk_changes:
                lines.append(
                    "- {code} {name}: action_label={previous}->{current}, risk_status={previous_status}->{current_status}, weakest_signal={previous_signal}->{current_signal}, current_risk={current_risk}".format(
                        code=row.get("Code", "-"),
                        name=row.get("Name", "-"),
                        previous=row.get("previous_action_label", "-"),
                        current=row.get("current_action_label", "-"),
                        previous_status=row.get("previous_act_now_risk_status", "off"),
                        current_status=row.get("current_act_now_risk_status", "off"),
                        previous_signal=row.get("previous_weakest_met_signal", "none"),
                        current_signal=row.get("current_weakest_met_signal", "none"),
                        current_risk=row.get("current_act_now_risk_summary", "none"),
                    )
                )
        else:
            lines.append("- none")
    else:
        lines.append("- none")

    lines.extend(["", "## Cycle Guard"])
    if cycle_guard:
        lines.append("- previous_label: {previous}".format(previous=cycle_guard.get("previous_label") or "none"))
        lines.append("- current_label: {current}".format(current=cycle_guard.get("current_label") or "none"))
        lines.append("- delta_summary: {delta_summary}".format(delta_summary=_render_guard_delta_summary(cycle_guard)))
        lines.append("- summary: {summary}".format(summary=cycle_guard.get("guard_summary", "-")))
        lines.append("- breaches: {breaches}".format(
            breaches=",".join(cycle_guard.get("breaches", []) or []) or "none"
        ))
        guard_quality = cycle_guard.get("screening_quality", {}) or {}
        if guard_quality:
            lines.append("- quality_status: {status}".format(status=guard_quality.get("quality_status", "unknown")))
            lines.append("- quality_summary: {summary}".format(summary=guard_quality.get("quality_summary", "none")))
            quality_codes = guard_quality.get("codes", {}) or {}
            lines.append(
                "- quality_codes: empty_price={empty_price}, invalid_momentum={invalid}".format(
                    empty_price=",".join(quality_codes.get("empty_price_codes_sample", []) or []) or "none",
                    invalid=",".join(quality_codes.get("invalid_momentum_codes_sample", []) or []) or "none",
                )
            )
        review_flags = cycle_guard.get("review_flags", []) or []
        caution_flags = cycle_guard.get("caution_flags", []) or []
        if review_flags:
            for flag in review_flags:
                lines.append(f"- review={flag}")
        if caution_flags:
            for flag in caution_flags:
                lines.append(f"- caution={flag}")
        if not review_flags and not caution_flags:
            lines.append("- flags: none")
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now Stability"])
    if cycle_guard:
        act_now_stability = cycle_guard.get("act_now_stability", []) or []
        if act_now_stability:
            for row in act_now_stability:
                lines.append(
                    "- {code} {name}: stability_status={status}, score_change={score_change}, rank_change={rank_change}, support={support}, reason={reason}; components={components}; component_drift={severity} ({drift_reason})".format(
                        code=row.get("Code", "-"),
                        name=row.get("Name", "-"),
                        status=row.get("stability_status", "-"),
                        score_change=row.get("score_change", 0),
                        rank_change=row.get("rank_change", 0),
                        support=row.get("support_summary", "none"),
                        reason=row.get("reason", "-"),
                        components=row.get("component_summary", "none"),
                        severity=row.get("component_drift_severity", "benign"),
                        drift_reason=row.get("component_drift_reason", "-"),
                    )
                )
        else:
            lines.append("- none")
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now Demotions"])
    demotions = payload.get("act_now_demotions", []) or []
    if demotions:
        for row in demotions:
            lines.append(
                "- {code} {name}: new_action_label={label}, score_change={score_change}, rank_change={rank_change}, components={components}, reason={reason}, rule_trigger={trigger}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    label=row.get("new_action_label", "-"),
                    score_change=row.get("score_change", 0),
                    rank_change=row.get("rank_change", 0),
                    components=row.get("component_summary", "none"),
                    reason=row.get("reason", "-"),
                    trigger=row.get("rule_trigger_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now Promotions"])
    promotions = payload.get("act_now_promotions", []) or []
    if promotions:
        for row in promotions:
            lines.append(
                "- {code} {name}: previous_action_label={label}, score_change={score_change}, rank_change={rank_change}, components={components}, reason={reason}, rule_trigger={trigger}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    label=row.get("previous_action_label", "-"),
                    score_change=row.get("score_change", 0),
                    rank_change=row.get("rank_change", 0),
                    components=row.get("component_summary", "none"),
                    reason=row.get("reason", "-"),
                    trigger=row.get("rule_trigger_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now"])
    act_now = payload.get("act_now", []) or []
    if act_now:
        for row in act_now:
            lines.append(
                "- {code} {name}: offensive_score={score}, offensive_rank={rank}, rank_delta_vs_legacy={delta}, reasons={reasons}, rule_trigger={trigger}, next_gate={next_gate}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    score=row.get("offensive_score", "-"),
                    rank=row.get("offensive_rank", "-"),
                    delta=row.get("rank_delta_vs_legacy", "-"),
                    reasons=",".join(str(item) for item in row.get("action_reasons", []) or ["none"]),
                    trigger=row.get("rule_trigger_summary", "-"),
                    next_gate=row.get("next_gate_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Promotion Watch"])
    promotion_watch = payload.get("promotion_watch", []) or []
    if promotion_watch:
        for row in promotion_watch:
            lines.append(
                "- status={status} rank={priority_rank} {code} {name}: readiness_score={readiness}, watch={watch}, promotion_path={path}, next_gate={next_gate}".format(
                    status=row.get("promotion_watch_status", "off"),
                    priority_rank=row.get("validate_priority_rank", "-"),
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    readiness=row.get("promotion_readiness_score", 0),
                    watch=row.get("promotion_watch_summary", "none"),
                    path=row.get("promotion_path_summary", "none"),
                    next_gate=row.get("next_gate_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Act Now Risk"])
    act_now_risk = payload.get("act_now_risk", []) or []
    if act_now_risk:
        for row in act_now_risk:
            lines.append(
                "- status={status} {code} {name}: offensive_rank={rank}, offensive_score={score}, risk={risk}, demotion_edge={edge}, rule_trigger={trigger}".format(
                    status=row.get("act_now_risk_status", "off"),
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    rank=row.get("offensive_rank", "-"),
                    score=row.get("offensive_score", "-"),
                    risk=row.get("act_now_risk_summary", "none"),
                    edge=row.get("demotion_edge_summary", "none"),
                    trigger=row.get("rule_trigger_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Validate Priority"])
    validate_priority = payload.get("validate_priority", []) or []
    if validate_priority:
        for row in validate_priority:
            lines.append(
                "- rank={priority_rank} {code} {name}: readiness_score={readiness}, primary_gap={primary_gap}, nearest_gap={nearest}, total_gap={total}, priority_view={summary}, promotion_trigger={trigger}, promotion_path={path}, gap_count={gap_count}, next_gate={next_gate}".format(
                    priority_rank=row.get("validate_priority_rank", "-"),
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    readiness=row.get("promotion_readiness_score", 0),
                    primary_gap=row.get("primary_gap_signal", "none"),
                    nearest=row.get("nearest_signal_gap", 0),
                    total=row.get("total_signal_gap", 0),
                    summary=row.get("validate_priority_summary", "none"),
                    trigger=row.get("promotion_trigger_signal", "none"),
                    path=row.get("promotion_path_summary", "none"),
                    gap_count=row.get("missing_signal_count", 0),
                    next_gate=row.get("next_gate_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Validate Now"])
    validate_now = payload.get("validate_now", []) or []
    if validate_now:
        for row in validate_now:
            lines.append(
                "- {code} {name}: offensive_score={score}, offensive_rank={rank}, rank_delta_vs_legacy={delta}, reasons={reasons}, promotion_path={path}, rule_trigger={trigger}, next_gate={next_gate}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    score=row.get("offensive_score", "-"),
                    rank=row.get("offensive_rank", "-"),
                    delta=row.get("rank_delta_vs_legacy", "-"),
                    reasons=",".join(str(item) for item in row.get("action_reasons", []) or ["none"]),
                    path=row.get("promotion_path_summary", "none"),
                    trigger=row.get("rule_trigger_summary", "-"),
                    next_gate=row.get("next_gate_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Top Candidates"])
    top_candidates = payload.get("top_candidates", []) or []
    if top_candidates:
        for row in top_candidates:
            lines.append(
                "- {code} {name}: bucket={bucket}, offensive_score={score}, offensive_rank={rank}, reason_tags={tags}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    bucket=row.get("priority_bucket", "-"),
                    score=row.get("offensive_score", "-"),
                    rank=row.get("offensive_rank", "-"),
                    tags=",".join(str(tag) for tag in row.get("reason_tags", []) or ["none"]),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-cycle-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_model_cycle_latest.json"),
    )
    parser.add_argument(
        "--action-memo-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_action_memo_latest.json"),
    )
    parser.add_argument(
        "--candidate-packet-json-path",
        default=str(REPO_ROOT / "output" / "offensive_screener_cycle" / "offensive_candidate_packet_latest.json"),
    )
    parser.add_argument("--cycle-diff-json-path")
    parser.add_argument("--cycle-guard-json-path")
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    model_cycle_payload = _load_json(args.model_cycle_json_path)
    action_memo_payload = _load_json(args.action_memo_json_path)
    candidate_packet_payload = _load_json(args.candidate_packet_json_path)
    cycle_diff_payload = _load_json(args.cycle_diff_json_path) if args.cycle_diff_json_path else None
    cycle_guard_payload = _load_json(args.cycle_guard_json_path) if args.cycle_guard_json_path else None
    payload = build_handoff_summary_payload(
        model_cycle_payload,
        action_memo_payload,
        candidate_packet_payload,
        cycle_diff_payload,
        cycle_guard_payload,
    )
    report = render_handoff_summary(payload)

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
