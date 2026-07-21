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


def _code_index(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("Code")): row for row in rows}


def _action_index(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = []
    rows.extend(payload.get("act_now", []) or [])
    rows.extend(payload.get("validate_now", []) or [])
    return _code_index(rows)


def _component_changes(prev_row: dict[str, object], curr_row: dict[str, object]) -> list[dict[str, object]]:
    fields = [
        ("offensive_component_mom1", "mom1"),
        ("offensive_component_volume", "volume"),
        ("offensive_component_breakout", "breakout"),
    ]
    rows: list[dict[str, object]] = []
    for field, label in fields:
        if field not in prev_row and field not in curr_row:
            continue
        prev_value = float(prev_row.get(field, 0.0) or 0.0)
        curr_value = float(curr_row.get(field, 0.0) or 0.0)
        rows.append(
            {
                "component": label,
                "previous_value": round(prev_value, 2),
                "current_value": round(curr_value, 2),
                "change": round(curr_value - prev_value, 2),
            }
        )
    rows.sort(key=lambda row: -abs(float(row["change"])))
    return rows


def _signal_diff(previous_signals: list[str], current_signals: list[str]) -> tuple[list[str], list[str]]:
    prev_set = set(previous_signals)
    curr_set = set(current_signals)
    return sorted(curr_set - prev_set), sorted(prev_set - curr_set)


def _action_transition_rows(
    previous_payload: dict[str, object],
    current_payload: dict[str, object],
) -> list[dict[str, object]]:
    previous_actions = _action_index(previous_payload)
    current_actions = _action_index(current_payload)
    codes = sorted(set(previous_actions) | set(current_actions))
    rows: list[dict[str, object]] = []
    for code in codes:
        previous_row = previous_actions.get(code, {})
        current_row = current_actions.get(code, {})
        previous_label = str(previous_row.get("action_label") or "outside_watchlist")
        current_label = str(current_row.get("action_label") or "outside_watchlist")
        previous_count = int(previous_row.get("confirmation_count", 0) or 0)
        current_count = int(current_row.get("confirmation_count", 0) or 0)
        previous_signals = [str(item) for item in (previous_row.get("confirmation_signals", []) or [])]
        current_signals = [str(item) for item in (current_row.get("confirmation_signals", []) or [])]
        signals_added, signals_removed = _signal_diff(previous_signals, current_signals)
        if (
            previous_label == current_label
            and previous_count == current_count
            and not signals_added
            and not signals_removed
            and str(previous_row.get("rule_trigger_summary", "")) == str(current_row.get("rule_trigger_summary", ""))
        ):
            continue
        source_row = current_row or previous_row
        rows.append(
            {
                "Code": code,
                "Name": source_row.get("Name", "-"),
                "previous_action_label": previous_label,
                "current_action_label": current_label,
                "confirmation_count_change": current_count - previous_count,
                "previous_confirmation_count": previous_count,
                "current_confirmation_count": current_count,
                "signals_added": signals_added,
                "signals_removed": signals_removed,
                "previous_rule_trigger_summary": previous_row.get("rule_trigger_summary", "-"),
                "current_rule_trigger_summary": current_row.get("rule_trigger_summary", "-"),
            }
        )
    rows.sort(
        key=lambda row: (
            0 if row["previous_action_label"] != row["current_action_label"] else 1,
            -abs(int(row["confirmation_count_change"])),
            str(row["Code"]),
        )
    )
    return rows


def _validate_priority_rows(
    previous_payload: dict[str, object],
    current_payload: dict[str, object],
) -> list[dict[str, object]]:
    previous_actions = _action_index(previous_payload)
    current_actions = _action_index(current_payload)
    codes = sorted(
        code
        for code in (set(previous_actions) | set(current_actions))
        if str(previous_actions.get(code, {}).get("action_label") or "") == "validate_now"
        or str(current_actions.get(code, {}).get("action_label") or "") == "validate_now"
    )
    rows: list[dict[str, object]] = []
    for code in codes:
        previous_row = previous_actions.get(code, {})
        current_row = current_actions.get(code, {})
        previous_label = str(previous_row.get("action_label") or "outside_watchlist")
        current_label = str(current_row.get("action_label") or "outside_watchlist")
        previous_rank = int(previous_row.get("validate_priority_rank", 999) or 999)
        current_rank = int(current_row.get("validate_priority_rank", 999) or 999)
        previous_readiness = float(previous_row.get("promotion_readiness_score", 0.0) or 0.0)
        current_readiness = float(current_row.get("promotion_readiness_score", 0.0) or 0.0)
        previous_gap_count = int(previous_row.get("missing_signal_count", 0) or 0)
        current_gap_count = int(current_row.get("missing_signal_count", 0) or 0)
        previous_primary_gap = str(previous_row.get("primary_gap_signal", "none") or "none")
        current_primary_gap = str(current_row.get("primary_gap_signal", "none") or "none")
        if (
            previous_label == current_label
            and previous_rank == current_rank
            and round(previous_readiness, 2) == round(current_readiness, 2)
            and previous_gap_count == current_gap_count
            and previous_primary_gap == current_primary_gap
        ):
            continue
        source_row = current_row or previous_row
        rows.append(
            {
                "Code": code,
                "Name": source_row.get("Name", "-"),
                "previous_action_label": previous_label,
                "current_action_label": current_label,
                "previous_validate_priority_rank": None if previous_rank == 999 else previous_rank,
                "current_validate_priority_rank": None if current_rank == 999 else current_rank,
                "validate_priority_rank_change": None
                if previous_rank == 999 or current_rank == 999
                else current_rank - previous_rank,
                "previous_readiness_score": round(previous_readiness, 2),
                "current_readiness_score": round(current_readiness, 2),
                "readiness_score_change": round(current_readiness - previous_readiness, 2),
                "previous_gap_count": previous_gap_count,
                "current_gap_count": current_gap_count,
                "gap_count_change": current_gap_count - previous_gap_count,
                "previous_primary_gap_signal": previous_primary_gap,
                "current_primary_gap_signal": current_primary_gap,
            }
        )
    rows.sort(
        key=lambda row: (
            0 if row["previous_action_label"] != row["current_action_label"] else 1,
            -abs(float(row["readiness_score_change"])),
            str(row["Code"]),
        )
    )
    return rows


def _act_now_risk_rows(
    previous_payload: dict[str, object],
    current_payload: dict[str, object],
) -> list[dict[str, object]]:
    previous_actions = _action_index(previous_payload)
    current_actions = _action_index(current_payload)
    codes = sorted(
        code
        for code in (set(previous_actions) | set(current_actions))
        if str(previous_actions.get(code, {}).get("action_label") or "") == "act_now"
        or str(current_actions.get(code, {}).get("action_label") or "") == "act_now"
    )
    rows: list[dict[str, object]] = []
    for code in codes:
        previous_row = previous_actions.get(code, {})
        current_row = current_actions.get(code, {})
        previous_label = str(previous_row.get("action_label") or "outside_watchlist")
        current_label = str(current_row.get("action_label") or "outside_watchlist")
        previous_status = str(previous_row.get("act_now_risk_status", "off") or "off")
        current_status = str(current_row.get("act_now_risk_status", "off") or "off")
        previous_summary = str(previous_row.get("act_now_risk_summary", "none") or "none")
        current_summary = str(current_row.get("act_now_risk_summary", "none") or "none")
        previous_signal = str(previous_row.get("weakest_met_signal", "none") or "none")
        current_signal = str(current_row.get("weakest_met_signal", "none") or "none")
        if (
            previous_label == current_label
            and previous_status == current_status
            and previous_summary == current_summary
            and previous_signal == current_signal
        ):
            continue
        source_row = current_row or previous_row
        rows.append(
            {
                "Code": code,
                "Name": source_row.get("Name", "-"),
                "previous_action_label": previous_label,
                "current_action_label": current_label,
                "previous_act_now_risk_status": previous_status,
                "current_act_now_risk_status": current_status,
                "previous_act_now_risk_summary": previous_summary,
                "current_act_now_risk_summary": current_summary,
                "previous_weakest_met_signal": previous_signal,
                "current_weakest_met_signal": current_signal,
            }
        )
    severity_order = {"hot": 0, "warm": 1, "off": 2}
    rows.sort(
        key=lambda row: (
            0 if row["previous_act_now_risk_status"] != row["current_act_now_risk_status"] else 1,
            severity_order.get(row["current_act_now_risk_status"], 9),
            str(row["Code"]),
        )
    )
    return rows


def build_cycle_diff_payload(
    previous_payload: dict[str, object],
    current_payload: dict[str, object],
    *,
    previous_label: str,
    current_label: str,
) -> dict[str, object]:
    prev_act = _code_index(previous_payload.get("act_now", []) or [])
    curr_act = _code_index(current_payload.get("act_now", []) or [])
    prev_validate = _code_index(previous_payload.get("validate_now", []) or [])
    curr_validate = _code_index(current_payload.get("validate_now", []) or [])
    prev_top = _code_index(previous_payload.get("top_candidates", []) or [])
    curr_top = _code_index(current_payload.get("top_candidates", []) or [])

    act_added = sorted(code for code in curr_act if code not in prev_act)
    act_removed = sorted(code for code in prev_act if code not in curr_act)
    validate_added = sorted(code for code in curr_validate if code not in prev_validate)
    validate_removed = sorted(code for code in prev_validate if code not in curr_validate)

    shared_top = sorted(set(prev_top) & set(curr_top))
    score_changes = []
    for code in shared_top:
        prev_row = prev_top[code]
        curr_row = curr_top[code]
        prev_score = float(prev_row.get("offensive_score", 0.0) or 0.0)
        curr_score = float(curr_row.get("offensive_score", 0.0) or 0.0)
        prev_rank = int(prev_row.get("offensive_rank", 0) or 0)
        curr_rank = int(curr_row.get("offensive_rank", 0) or 0)
        score_changes.append(
            {
                "Code": code,
                "Name": curr_row.get("Name") or prev_row.get("Name"),
                "score_change": round(curr_score - prev_score, 2),
                "rank_change": curr_rank - prev_rank,
                "previous_score": round(prev_score, 2),
                "current_score": round(curr_score, 2),
                "previous_rank": prev_rank,
                "current_rank": curr_rank,
                "component_changes": _component_changes(prev_row, curr_row),
            }
        )
    score_changes.sort(key=lambda row: (-abs(float(row["score_change"])), row["current_rank"]))

    return {
        "previous_label": previous_label,
        "current_label": current_label,
        "act_now_count_change": int(current_payload.get("act_now_count", 0)) - int(previous_payload.get("act_now_count", 0)),
        "validate_now_count_change": int(current_payload.get("validate_now_count", 0)) - int(previous_payload.get("validate_now_count", 0)),
        "act_now_added": act_added,
        "act_now_removed": act_removed,
        "validate_now_added": validate_added,
        "validate_now_removed": validate_removed,
        "action_state_changes": _action_transition_rows(previous_payload, current_payload),
        "validate_priority_changes": _validate_priority_rows(previous_payload, current_payload),
        "act_now_risk_changes": _act_now_risk_rows(previous_payload, current_payload),
        "top_candidate_score_changes": score_changes,
    }


def render_cycle_diff(payload: dict[str, object]) -> str:
    lines = [
        "# Offensive Cycle Diff",
        "",
        f"- previous_label: {payload.get('previous_label', '-')}",
        f"- current_label: {payload.get('current_label', '-')}",
        f"- act_now_count_change: {payload.get('act_now_count_change', 0)}",
        f"- validate_now_count_change: {payload.get('validate_now_count_change', 0)}",
        "",
        "## Act Now Added",
    ]
    for section, key in [
        ("## Act Now Added", "act_now_added"),
        ("## Act Now Removed", "act_now_removed"),
        ("## Validate Now Added", "validate_now_added"),
        ("## Validate Now Removed", "validate_now_removed"),
    ]:
        if lines[-1] != section:
            lines.extend(["", section])
        rows = payload.get(key, []) or []
        if rows:
            for code in rows:
                lines.append(f"- {code}")
        else:
            lines.append("- none")

    lines.extend(["", "## Action State Changes"])
    action_state_changes = payload.get("action_state_changes", []) or []
    if action_state_changes:
        for row in action_state_changes:
            lines.append(
                "- {code} {name}: action_label={previous}->{current}, confirmation_count_change={delta}, signals_added={added}, signals_removed={removed}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    previous=row.get("previous_action_label", "-"),
                    current=row.get("current_action_label", "-"),
                    delta=row.get("confirmation_count_change", 0),
                    added=",".join(str(item) for item in row.get("signals_added", []) or ["none"]),
                    removed=",".join(str(item) for item in row.get("signals_removed", []) or ["none"]),
                )
            )
            lines.append(
                "  previous_rule_trigger={previous}; current_rule_trigger={current}".format(
                    previous=row.get("previous_rule_trigger_summary", "-"),
                    current=row.get("current_rule_trigger_summary", "-"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Validate Priority Changes"])
    validate_priority_changes = payload.get("validate_priority_changes", []) or []
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

    lines.extend(["", "## Act Now Risk Changes"])
    act_now_risk_changes = payload.get("act_now_risk_changes", []) or []
    if act_now_risk_changes:
        for row in act_now_risk_changes:
            lines.append(
                "- {code} {name}: action_label={previous}->{current}, risk_status={previous_status}->{current_status}, weakest_signal={previous_signal}->{current_signal}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    previous=row.get("previous_action_label", "-"),
                    current=row.get("current_action_label", "-"),
                    previous_status=row.get("previous_act_now_risk_status", "off"),
                    current_status=row.get("current_act_now_risk_status", "off"),
                    previous_signal=row.get("previous_weakest_met_signal", "none"),
                    current_signal=row.get("current_weakest_met_signal", "none"),
                )
            )
            lines.append(
                "  previous_risk={previous}; current_risk={current}".format(
                    previous=row.get("previous_act_now_risk_summary", "none"),
                    current=row.get("current_act_now_risk_summary", "none"),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Top Candidate Score Changes"])
    rows = payload.get("top_candidate_score_changes", []) or []
    if rows:
        for row in rows:
            lines.append(
                "- {code} {name}: score_change={score_change}, rank_change={rank_change}, previous_score={previous_score}, current_score={current_score}".format(
                    code=row.get("Code", "-"),
                    name=row.get("Name", "-"),
                    score_change=row.get("score_change", 0),
                    rank_change=row.get("rank_change", 0),
                    previous_score=row.get("previous_score", 0),
                    current_score=row.get("current_score", 0),
                )
            )
            component_changes = row.get("component_changes", []) or []
            if component_changes:
                summary = ", ".join(
                    "{component}={change}".format(
                        component=component_row.get("component", "-"),
                        change=component_row.get("change", 0),
                    )
                    for component_row in component_changes[:3]
                )
                lines.append(f"  component_changes={summary}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous-json-path", required=True)
    parser.add_argument("--current-json-path", required=True)
    parser.add_argument("--previous-label")
    parser.add_argument("--current-label")
    parser.add_argument("--output-json-path")
    parser.add_argument("--output-md-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    previous_payload = _load_json(args.previous_json_path)
    current_payload = _load_json(args.current_json_path)
    previous_label = args.previous_label or Path(args.previous_json_path).stem
    current_label = args.current_label or Path(args.current_json_path).stem
    payload = build_cycle_diff_payload(
        previous_payload,
        current_payload,
        previous_label=previous_label,
        current_label=current_label,
    )
    report = render_cycle_diff(payload)

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
