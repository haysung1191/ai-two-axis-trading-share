from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis import apply_offensive_screener_filter as filter_apply
from tools.analysis import build_offensive_action_memo as action_memo
from tools.analysis import build_offensive_candidate_packet as candidate_packet
from tools.analysis import build_offensive_cycle_diff as cycle_diff
from tools.analysis import build_offensive_cycle_guard as cycle_guard
from tools.analysis import build_offensive_handoff_summary as handoff_summary
from tools.analysis import build_offensive_review_shortlist as review_shortlist
from tools.analysis import build_offensive_screener_comparison_report as comparison_report
from tools.analysis import build_offensive_screener_filter_recommendation as filter_recommendation
from tools.analysis import build_offensive_screener_reason_summary as reason_summary
from tools.analysis.run_offensive_screener_cycle import OUTPUT_DIR, _timestamp
from screener import MomentumScreener


def _write_json_pair(output_dir: Path, stem: str, stamp: str, payload: dict[str, object]) -> None:
    stamped_path = output_dir / f"{stem}_{stamp}.json"
    latest_path = output_dir / f"{stem}_latest.json"
    text = json.dumps(payload, indent=2)
    stamped_path.write_text(text, encoding="utf-8")
    latest_path.write_text(text, encoding="utf-8")


def _write_md_pair(output_dir: Path, stem: str, stamp: str, text: str) -> None:
    stamped_path = output_dir / f"{stem}_{stamp}.md"
    latest_path = output_dir / f"{stem}_latest.md"
    stamped_path.write_text(text, encoding="utf-8")
    latest_path.write_text(text, encoding="utf-8")


def _write_csv_pair(output_dir: Path, stem: str, stamp: str, frame: pd.DataFrame) -> None:
    stamped_path = output_dir / f"{stem}_{stamp}.csv"
    latest_path = output_dir / f"{stem}_latest.csv"
    frame.to_csv(stamped_path, index=False, encoding="utf-8-sig")
    frame.to_csv(latest_path, index=False, encoding="utf-8-sig")


def _manifest_entry(output_dir: Path, stem: str, stamp: str, suffix: str) -> dict[str, str]:
    return {
        "stem": stem,
        "stamped_path": str(output_dir / f"{stem}_{stamp}.{suffix}"),
        "latest_path": str(output_dir / f"{stem}_latest.{suffix}"),
    }


def _find_previous_stamped_json(output_dir: Path, stem: str, current_stamp: str) -> Path | None:
    candidates = sorted(
        path for path in output_dir.glob(f"{stem}_*.json") if path.stem != f"{stem}_latest" and current_stamp not in path.stem
    )
    if not candidates:
        return None
    return candidates[-1]


def _latest_protection_decision(
    current_cycle_payload: dict[str, object],
    previous_handoff_payload: dict[str, object] | None,
    guard_payload: dict[str, object] | None,
) -> dict[str, object]:
    if not previous_handoff_payload:
        return {"should_promote_latest": True, "status": "no_previous", "reason": "none"}

    current_screening = int(current_cycle_payload.get("screening_row_count", 0) or 0)
    previous_screening = int(previous_handoff_payload.get("screening_row_count", 0) or 0)
    current_filtered = int(current_cycle_payload.get("filtered_row_count", 0) or 0)
    previous_filtered = int(previous_handoff_payload.get("filtered_row_count", 0) or 0)
    current_act_now = int(current_cycle_payload.get("act_now_count", 0) or 0)
    previous_act_now = int(previous_handoff_payload.get("act_now_count", 0) or 0)
    current_validate = int(current_cycle_payload.get("validate_now_count", 0) or 0)
    previous_validate = int(previous_handoff_payload.get("validate_now_count", 0) or 0)
    screening_quality = current_cycle_payload.get("screening_quality", {}) or {}
    attempted = int(screening_quality.get("attempted_ticker_count", current_screening) or current_screening or 0)
    empty_price_count = int(screening_quality.get("empty_price_count", 0) or 0)
    invalid_momentum_count = int(screening_quality.get("invalid_momentum_count", 0) or 0)
    fetch_coverage = float(screening_quality.get("price_fetch_coverage", 1.0) or 0.0)
    success_coverage = float(screening_quality.get("success_coverage", 1.0) or 0.0)
    guard_status = str((guard_payload or {}).get("guard_status", "none") or "none")

    severe_screening_collapse = previous_screening >= 8 and current_screening <= max(1, int(previous_screening * 0.35))
    severe_filtered_collapse = previous_filtered >= 5 and current_filtered <= max(1, int(previous_filtered * 0.35))
    act_now_wipeout = previous_act_now >= 2 and current_act_now == 0
    validate_collapse = previous_validate >= 2 and current_validate <= max(1, previous_validate // 2)
    severe_data_quality_drop = attempted >= 10 and (fetch_coverage < 0.5 or success_coverage < 0.35)

    should_preserve_previous = (
        guard_status == "review"
        and severe_screening_collapse
        and severe_filtered_collapse
        and severe_data_quality_drop
        and (act_now_wipeout or validate_collapse)
    )
    if not should_preserve_previous:
        return {"should_promote_latest": True, "status": "advance_latest", "reason": "none"}

    reason = (
        "preserved_previous_latest due_to=screening_collapse; previous_screening={previous_screening}; "
        "current_screening={current_screening}; previous_filtered={previous_filtered}; "
        "current_filtered={current_filtered}; previous_act_now={previous_act_now}; current_act_now={current_act_now}; "
        "previous_validate={previous_validate}; current_validate={current_validate}; attempted={attempted}; "
        "empty_price={empty_price}; invalid_momentum={invalid_momentum}; fetch_coverage={fetch_coverage:.2f}; "
        "success_coverage={success_coverage:.2f}; guard_status={guard_status}"
    ).format(
        previous_screening=previous_screening,
        current_screening=current_screening,
        previous_filtered=previous_filtered,
        current_filtered=current_filtered,
        previous_act_now=previous_act_now,
        current_act_now=current_act_now,
        previous_validate=previous_validate,
        current_validate=current_validate,
        attempted=attempted,
        empty_price=empty_price_count,
        invalid_momentum=invalid_momentum_count,
        fetch_coverage=fetch_coverage,
        success_coverage=success_coverage,
        guard_status=guard_status,
    )
    return {
        "should_promote_latest": False,
        "status": "preserved_previous_latest",
        "reason": reason,
    }


def _restore_latest_artifacts_from_previous(
    artifact_manifest: list[dict[str, str]],
    previous_stamp: str,
) -> None:
    restored_pairs: set[tuple[str, str]] = set()
    for entry in artifact_manifest:
        stem = str(entry.get("stem", "") or "")
        latest_path = Path(str(entry.get("latest_path", "") or ""))
        if not stem or not latest_path:
            continue
        key = (stem, latest_path.suffix)
        if key in restored_pairs:
            continue
        previous_path = latest_path.with_name(f"{stem}_{previous_stamp}{latest_path.suffix}")
        if previous_path.exists():
            shutil.copyfile(previous_path, latest_path)
            restored_pairs.add(key)


def _fmt_metric(value: object) -> str:
    if value in {None, "", "none"}:
        return "none"
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


def _render_validate_competition_summary(competition: dict[str, object]) -> str:
    if not competition:
        return "none"
    leader = competition.get("leader_code", "none")
    challenger = competition.get("challenger_code", "none")
    if challenger in {None, "", "none"}:
        return "mode=single; leader={leader}; challenger=none".format(leader=leader)
    return (
        "mode=ordered; leader={leader}; challenger={challenger}; nearest_gap_edge={nearest_gap_edge}; "
        "total_gap_edge={total_gap_edge}; readiness_edge={readiness_edge}"
    ).format(
        leader=leader,
        challenger=challenger,
        nearest_gap_edge=_fmt_metric(competition.get("nearest_gap_edge", "none")),
        total_gap_edge=_fmt_metric(competition.get("total_gap_edge", "none")),
        readiness_edge=_fmt_metric(competition.get("readiness_edge", "none")),
    )


def _render_act_now_competition_summary(competition: dict[str, object]) -> str:
    if not competition:
        return "none"
    leader = competition.get("leader_code", "none")
    challenger = competition.get("challenger_code", "none")
    if challenger in {None, "", "none"}:
        return "mode=single; leader={leader}; challenger=none".format(leader=leader)
    return (
        "mode=ordered; leader={leader}; challenger={challenger}; margin_edge={margin_edge}; score_edge={score_edge}"
    ).format(
        leader=leader,
        challenger=challenger,
        margin_edge=_fmt_metric(competition.get("margin_edge", "none")),
        score_edge=_fmt_metric(competition.get("score_edge", "none")),
    )


def _render_validate_competition_rationale(
    competition: dict[str, object],
    basis: dict[str, object],
) -> str:
    if not competition and not basis:
        return "none"
    leader = basis.get("leader_code") or competition.get("leader_code", "none")
    challenger = basis.get("challenger_code") or competition.get("challenger_code", "none")
    if challenger in {None, "", "none"}:
        return (
            "mode=single; leader={leader}; challenger=none; ordering_basis=only_validate_now_candidate; "
            "primary_gap={primary_gap}; nearest_gap={nearest_gap}; total_gap={total_gap}; next_gate={next_gate}"
        ).format(
            leader=leader,
            primary_gap=basis.get("leader_primary_gap", "none"),
            nearest_gap=_fmt_metric(basis.get("leader_nearest_gap", "none")),
            total_gap=_fmt_metric(basis.get("leader_total_gap", "none")),
            next_gate=basis.get("leader_next_gate", "none"),
        )
    return (
        "mode=ordered; leader={leader}; challenger={challenger}; ordering_basis=nearest_gap_then_total_gap_then_readiness; "
        "leader_primary_gap={leader_primary_gap}; leader_nearest_gap={leader_nearest_gap}; leader_total_gap={leader_total_gap}; "
        "challenger_primary_gap={challenger_primary_gap}; challenger_nearest_gap={challenger_nearest_gap}; "
        "challenger_total_gap={challenger_total_gap}; nearest_gap_edge={nearest_gap_edge}; total_gap_edge={total_gap_edge}; "
        "readiness_edge={readiness_edge}"
    ).format(
        leader=leader,
        challenger=challenger,
        leader_primary_gap=basis.get("leader_primary_gap", "none"),
        leader_nearest_gap=_fmt_metric(basis.get("leader_nearest_gap", "none")),
        leader_total_gap=_fmt_metric(basis.get("leader_total_gap", "none")),
        challenger_primary_gap=basis.get("challenger_primary_gap", "none"),
        challenger_nearest_gap=_fmt_metric(basis.get("challenger_nearest_gap", "none")),
        challenger_total_gap=_fmt_metric(basis.get("challenger_total_gap", "none")),
        nearest_gap_edge=_fmt_metric(competition.get("nearest_gap_edge", "none")),
        total_gap_edge=_fmt_metric(competition.get("total_gap_edge", "none")),
        readiness_edge=_fmt_metric(competition.get("readiness_edge", "none")),
    )


def _render_act_now_competition_rationale(
    competition: dict[str, object],
    basis: dict[str, object],
) -> str:
    if not competition and not basis:
        return "none"
    leader = basis.get("leader_code") or competition.get("leader_code", "none")
    challenger = basis.get("challenger_code") or competition.get("challenger_code", "none")
    leader_status = str(basis.get("leader_risk_status", "off"))
    challenger_status = str(basis.get("challenger_risk_status", "off"))
    leader_signal = basis.get("leader_weakest_signal", "none")
    challenger_signal = basis.get("challenger_weakest_signal", "none")
    if challenger in {None, "", "none"}:
        return (
            "mode=single; leader={leader}; challenger=none; ordering_basis=only_act_now_candidate; "
            "leader_risk_status={leader_risk_status}; leader_weakest_signal={leader_weakest_signal}; leader_weakest_margin={leader_weakest_margin}"
        ).format(
            leader=leader,
            leader_risk_status=leader_status,
            leader_weakest_signal=leader_signal,
            leader_weakest_margin=_fmt_metric(basis.get("leader_weakest_margin", "none")),
        )
    if leader_status != challenger_status:
        ordering_basis = "risk_status_then_rank"
    elif leader_signal == challenger_signal:
        ordering_basis = "shared_weakest_signal_then_rank"
    else:
        ordering_basis = "same_risk_band_then_rank"
    return (
        "mode=ordered; leader={leader}; challenger={challenger}; ordering_basis={ordering_basis}; "
        "leader_risk_status={leader_risk_status}; challenger_risk_status={challenger_risk_status}; "
        "leader_weakest_signal={leader_weakest_signal}; challenger_weakest_signal={challenger_weakest_signal}; "
        "leader_weakest_margin={leader_weakest_margin}; challenger_weakest_margin={challenger_weakest_margin}; "
        "margin_edge={margin_edge}; score_edge={score_edge}"
    ).format(
        leader=leader,
        challenger=challenger,
        ordering_basis=ordering_basis,
        leader_risk_status=leader_status,
        challenger_risk_status=challenger_status,
        leader_weakest_signal=leader_signal,
        challenger_weakest_signal=challenger_signal,
        leader_weakest_margin=_fmt_metric(basis.get("leader_weakest_margin", "none")),
        challenger_weakest_margin=_fmt_metric(basis.get("challenger_weakest_margin", "none")),
        margin_edge=_fmt_metric(competition.get("margin_edge", "none")),
        score_edge=_fmt_metric(competition.get("score_edge", "none")),
    )


def _render_guard_delta_scan(guard_payload: dict[str, object] | None) -> str:
    if not guard_payload:
        return "previous=none; current=none; act_now_delta=none; validate_now_delta=none; membership=none; top_move=none"

    metrics = guard_payload.get("metrics", {}) or {}
    return (
        "previous={previous}; current={current}; act_now_delta={act_now_delta}; "
        "validate_now_delta={validate_now_delta}; membership=act_now:{act_membership},validate_now:{validate_membership}; "
        "top_move=score:{score_delta},rank:{rank_delta}"
    ).format(
        previous=guard_payload.get("previous_label", "none"),
        current=guard_payload.get("current_label", "none"),
        act_now_delta=metrics.get("act_now_count_change_abs", "none"),
        validate_now_delta=metrics.get("validate_now_count_change_abs", "none"),
        act_membership=metrics.get("act_now_membership_change", "none"),
        validate_membership=metrics.get("validate_now_membership_change", "none"),
        score_delta=_fmt_metric(metrics.get("largest_score_change", "none")),
        rank_delta=_fmt_metric(metrics.get("largest_rank_change", "none")),
    )


def _sync_readme_thread_handoff_text(
    text: str,
    *,
    refreshed_at: str,
    cycle_payload: dict[str, object],
) -> tuple[str, dict[str, bool]]:
    operator_snapshot = cycle_payload.get("operator_snapshot", {}) or {}
    screening_quality = cycle_payload.get("screening_quality", {}) or {}
    latest_update = cycle_payload.get("latest_update", {}) or {}
    cycle_diff_payload = cycle_payload.get("cycle_diff", {}) or {}
    cycle_guard_payload = cycle_payload.get("cycle_guard", {}) or {}
    act_now_rows = operator_snapshot.get("act_now_members", []) or []
    act_now_dormant_rows = operator_snapshot.get("act_now_dormant_members", []) or []
    if not act_now_dormant_rows:
        act_now_dormant_rows = [row for row in act_now_rows if row.get("act_now_risk_status") not in {"hot", "warm"}]
    act_now_live_count = operator_snapshot.get("act_now_live_count")
    if act_now_live_count in {None, ""}:
        act_now_live_count = sum(1 for row in act_now_rows if row.get("act_now_risk_status") in {"hot", "warm"})
    act_now_dormant_count = operator_snapshot.get("act_now_dormant_count")
    if act_now_dormant_count in {None, ""}:
        if act_now_dormant_rows:
            act_now_dormant_count = len(act_now_dormant_rows)
        else:
            act_now_dormant_count = max(int(cycle_payload.get("act_now_count", 0)) - int(act_now_live_count), 0)
    dormant_act_now_codes = ", ".join(str(row.get("Code", "none")) for row in act_now_dormant_rows) or "none"
    dormant_focus = next(
        (row for row in (operator_snapshot.get("operator_focuses", []) or []) if row.get("focus_type") == "act_now_dormant"),
        {},
    )
    dormant_act_now_action = str(dormant_focus.get("action", "none") or "none")
    dormant_act_now_gap = str(dormant_focus.get("reason", dormant_focus.get("gap_summary", "none")) or "none")
    operator_steps = operator_snapshot.get("operator_steps", []) or []
    runbook_next_actions = " | ".join(
        "{step_type}:{code}:{action}".format(
            step_type=row.get("step_type", "none"),
            code=row.get("Code", "none"),
            action=row.get("action", "none"),
        )
        for row in operator_steps[:3]
    ) or "none"
    hot_risk_codes = ", ".join(str(row.get("Code", "none")) for row in act_now_rows if row.get("act_now_risk_status") == "hot") or "none"
    warm_risk_codes = ", ".join(str(row.get("Code", "none")) for row in act_now_rows if row.get("act_now_risk_status") == "warm") or "none"
    hot_promotion_watch = str(operator_snapshot.get("hot_promotion_watch_code", "none") or "none")
    warm_promotion_watch = str(operator_snapshot.get("warm_promotion_watch_code", "none") or "none")
    guard_breach_summary = str(operator_snapshot.get("guard_breach_summary", "none") or "none")
    guard_quality_status = str(operator_snapshot.get("guard_quality_status", "unknown") or "unknown")
    guard_quality_summary = str(operator_snapshot.get("guard_quality_summary", "none") or "none")
    operator_headline = str(operator_snapshot.get("operator_headline", "none") or "none")
    primary_call = str(operator_snapshot.get("primary_call", "none") or "none")
    primary_call_reason = str(operator_snapshot.get("primary_call_reason", "none") or "none")
    compare_scan = str((operator_snapshot.get("operator_scan", {}) or {}).get("compare_scan", "none") or "none")
    risk_compare_scan = str((operator_snapshot.get("operator_scan", {}) or {}).get("risk_compare_scan", "none") or "none")
    live_scan = str((operator_snapshot.get("operator_scan", {}) or {}).get("live_scan", "none") or "none")
    guard_scan = str((operator_snapshot.get("operator_scan", {}) or {}).get("guard_scan", "none") or "none")
    guard_delta_scan = str((operator_snapshot.get("operator_scan", {}) or {}).get("guard_delta_scan", "none") or "none")
    priority_scan = str((operator_snapshot.get("operator_scan", {}) or {}).get("priority_scan", "none") or "none")
    screening_quality_status = str(screening_quality.get("quality_status", "unknown") or "unknown")
    screening_quality_summary = str(screening_quality.get("quality_summary", "none") or "none")
    screening_empty_codes = ",".join(screening_quality.get("empty_price_codes_sample", []) or []) or "none"
    screening_invalid_codes = ",".join(screening_quality.get("invalid_momentum_codes_sample", []) or []) or "none"
    latest_update_status = str(latest_update.get("status", "none") or "none")
    latest_update_reason = str(latest_update.get("reason", "none") or "none")
    cycle_diff_labels = "previous={previous}; current={current}".format(
        previous=cycle_diff_payload.get("previous_label", "none") or "none",
        current=cycle_diff_payload.get("current_label", "none") or "none",
    )
    cycle_guard_context = "status={status}; previous={previous}; current={current}".format(
        status=cycle_guard_payload.get("guard_status", "none") or "none",
        previous=cycle_guard_payload.get("previous_label", "none") or "none",
        current=cycle_guard_payload.get("current_label", "none") or "none",
    )
    starter_prompt_state_block = (
        "理쒓렐 offensive ?곹깭:\n"
        f"- act_now={int(cycle_payload.get('act_now_count', 0))}\n"
        f"- validate_now={int(cycle_payload.get('validate_now_count', 0))}\n"
        f"- act_now_live={int(act_now_live_count)}\n"
        f"- act_now_dormant={int(act_now_dormant_count)}\n"
        f"- hot promotion watch={hot_promotion_watch}\n"
        f"- warm promotion watch={warm_promotion_watch}\n"
        f"- hot act-now risk={hot_risk_codes}\n"
        f"- warm act-now risk={warm_risk_codes}\n"
        f"- dormant act-now={dormant_act_now_codes}\n"
        f"- dormant act-now action={dormant_act_now_action}\n"
        f"- dormant act-now gap={dormant_act_now_gap}\n"
        f"- screening quality={screening_quality_summary}\n"
        f"- screening quality status={screening_quality_status}\n"
        f"- guard breach summary={guard_breach_summary}\n"
        f"- guard quality status={guard_quality_status}\n"
        f"- operator headline={operator_headline}\n"
        f"- compare scan={compare_scan}\n"
        f"- risk compare scan={risk_compare_scan}\n"
        f"- live scan={live_scan}\n"
        f"- guard scan={guard_scan}\n"
        f"- cycle diff labels={cycle_diff_labels}\n"
        f"- cycle guard context={cycle_guard_context}\n"
        f"- guard delta scan={guard_delta_scan}\n"
        f"- priority scan={priority_scan}\n"
        f"- primary call={primary_call}\n"
        f"- primary call reason={primary_call_reason}\n"
        f"- latest update status={latest_update_status}\n"
        f"- latest update reason={latest_update_reason}\n"
        f"- next actions={runbook_next_actions}\n"
        "- operator board? focus queue媛 ?대? 遺숈뼱 ?덉쓬\n"
        "- validate/act-now competition summary? rationale? root cycle怨?handoff summary ?묒そ 紐⑤몢 key-value contract濡??뺣젹???덉쓬\n"
    )
    latest_verified_headline_block = (
        "Latest verified headline state:\n\n"
        f"- `screening_row_count = {int(cycle_payload.get('screening_row_count', 0))}`\n"
        f"- `filtered_row_count = {int(cycle_payload.get('filtered_row_count', 0))}`\n"
        f"- `shortlist_count = {int(cycle_payload.get('shortlist_count', 0))}`\n"
        f"- `act_now_count = {int(cycle_payload.get('act_now_count', 0))}`\n"
        f"- `validate_now_count = {int(cycle_payload.get('validate_now_count', 0))}`\n"
        f"- `act_now_live_count = {int(act_now_live_count)}`\n"
        f"- `act_now_dormant_count = {int(act_now_dormant_count)}`\n"
        f"- `screening_quality = {screening_quality_summary}`\n"
        f"- `screening_quality_status = {screening_quality_status}`\n"
        f"- `latest_update_status = {latest_update_status}`\n"
        f"- `latest_update_reason = {latest_update_reason}`\n"
        f"- `guard_status = {operator_snapshot.get('guard_status', 'unknown')}`\n"
        f"- `operator_headline = {operator_headline}`\n"
        f"- `compare_scan = {compare_scan}`\n"
        f"- `risk_compare_scan = {risk_compare_scan}`\n"
        f"- `live_scan = {live_scan}`\n"
        f"- `guard_scan = {guard_scan}`\n"
        f"- `cycle_diff_labels = {cycle_diff_labels}`\n"
        f"- `cycle_guard_context = {cycle_guard_context}`\n"
        f"- `guard_delta_scan = {guard_delta_scan}`\n"
        f"- `priority_scan = {priority_scan}`\n"
        f"- `guard_breach_summary = {guard_breach_summary}`\n"
        f"- `guard_quality_status = {guard_quality_status}`\n"
    )
    latest_verified_top_focus_block = (
        "Latest verified top focus:\n\n"
        f"- warm promotion watch: `{warm_promotion_watch}`\n"
        f"- hot promotion watch: `{hot_promotion_watch}`\n"
        f"- hot act-now risk names: `{hot_risk_codes}`\n"
        f"- warm act-now risk names: `{warm_risk_codes}`\n"
        f"- dormant act-now names: `{dormant_act_now_codes}`\n"
        f"- dormant act-now action: `{dormant_act_now_action}`\n"
        f"- dormant act-now gap: `{dormant_act_now_gap}`\n"
        f"- screening quality codes: `empty_price={screening_empty_codes}; invalid_momentum={screening_invalid_codes}`\n"
        f"- guard breach summary: `{guard_breach_summary}`\n"
        f"- guard quality status: `{guard_quality_status}`\n"
        f"- guard quality summary: `{guard_quality_summary}`\n"
        f"- primary call: `{primary_call}`\n"
        f"- primary call reason: `{primary_call_reason}`\n"
        f"- runbook next actions: `{runbook_next_actions}`\n"
    )

    def _replace_block_between_markers(
        source: str,
        *,
        start_marker: str,
        end_markers: tuple[str, ...],
        replacement_block: str,
    ) -> tuple[str, bool]:
        start_index = source.find(start_marker)
        if start_index == -1:
            return source, False
        end_index = -1
        for end_marker in end_markers:
            candidate = source.find(end_marker, start_index + len(start_marker))
            if candidate != -1 and (end_index == -1 or candidate < end_index):
                end_index = candidate
        if end_index == -1:
            return source, False
        return source[:start_index] + replacement_block + source[end_index:], True

    def _replace_block_between_marker_options(
        source: str,
        *,
        start_markers: tuple[str, ...],
        end_markers: tuple[str, ...],
        replacement_block: str,
    ) -> tuple[str, bool]:
        for start_marker in start_markers:
            updated_source, replaced = _replace_block_between_markers(
                source,
                start_marker=start_marker,
                end_markers=end_markers,
                replacement_block=replacement_block,
            )
            if replaced:
                return updated_source, True
        return source, False

    replacements = [
        (
            "artifact_timestamp",
            r"Latest offensive cycle artifacts were regenerated on `[^`]+`:",
            f"Latest offensive cycle artifacts were regenerated on `{refreshed_at}`:",
        ),
    ]

    updated = text
    replaced_sections: dict[str, bool] = {}
    for section_name, pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, updated, count=1)
        replaced_sections[section_name] = updated != text if section_name == "artifact_timestamp" else True
    updated, replaced_sections["headline_state"] = _replace_block_between_markers(
        updated,
        start_marker="Latest verified headline state:\n\n",
        end_markers=("\nLatest verified top focus:",),
        replacement_block=latest_verified_headline_block + "\n",
    )
    updated, replaced_sections["top_focus"] = _replace_block_between_markers(
        updated,
        start_marker="Latest verified top focus:\n\n",
        end_markers=("\n### What Was Just Added", "\n### New Thread Starter Prompt"),
        replacement_block=latest_verified_top_focus_block + "\n",
    )
    updated, replaced_sections["starter_prompt_state"] = _replace_block_between_markers(
        updated,
        start_marker="理쒓렐 offensive ?곹깭:\n",
        end_markers=("\n吏湲덉? broad planning 留먭퀬, 媛??媛移??믪? ?ㅼ쓬 ??嫄몄쓬??諛붾줈 ?ㅽ뻾??", "\n```"),
        replacement_block=starter_prompt_state_block + "\n",
    )
    if not replaced_sections["starter_prompt_state"]:
        updated, replaced_sections["starter_prompt_state"] = _replace_block_between_marker_options(
            updated,
            start_markers=("최근 offensive 상태:\n",),
            end_markers=(
                "\n지금은 broad planning 말고, 가장 가치 높은 다음 한 걸음을 바로 실행해.",
                "\n```",
            ),
            replacement_block=starter_prompt_state_block + "\n",
        )
    return updated, replaced_sections


def _sync_readme_thread_handoff(readme_path: Path, *, cycle_payload: dict[str, object]) -> None:
    if not readme_path.exists():
        return
    stamp = str(cycle_payload.get("stamp", "") or "")
    stamp_match = re.fullmatch(r"(\d{8})T(\d{6})", stamp)
    if stamp_match:
        date_part, time_part = stamp_match.groups()
        refreshed_at = "{year}-{month}-{day} {hour}:{minute}".format(
            year=date_part[0:4],
            month=date_part[4:6],
            day=date_part[6:8],
            hour=time_part[0:2],
            minute=time_part[2:4],
        )
    else:
        refreshed_at = "unknown"
    original = readme_path.read_text(encoding="utf-8")
    updated, replaced_sections = _sync_readme_thread_handoff_text(
        original,
        refreshed_at=refreshed_at,
        cycle_payload=cycle_payload,
    )
    missing_sections = [name for name, replaced in replaced_sections.items() if not replaced]
    if missing_sections:
        raise RuntimeError(
            "README Thread Handoff sync failed to replace sections: {sections}".format(
                sections=", ".join(missing_sections),
            )
        )
    if updated != original:
        readme_path.write_text(updated, encoding="utf-8")


def _operator_snapshot_from_handoff(
    handoff_payload: dict[str, object],
    guard_payload: dict[str, object] | None,
) -> dict[str, object]:
    operator_board = handoff_payload.get("operator_board", {}) or {}
    operator_runbook = handoff_payload.get("operator_runbook", []) or []
    focus_queue = handoff_payload.get("focus_queue", []) or []
    screening_quality = handoff_payload.get("screening_quality", {}) or {}
    latest_update = handoff_payload.get("latest_update", {}) or {}

    def _step_row(step_type: str) -> dict[str, object]:
        row = next((row for row in operator_runbook if row.get("step_type") == step_type), None)
        if not row:
            return {}
        return row

    def _focus_row(code: object) -> dict[str, object]:
        if not code:
            return {}
        row = next((row for row in focus_queue if str(row.get("Code")) == str(code)), None)
        if not row:
            return {}
        return row

    def _decision_row(code: object) -> dict[str, object]:
        if not code:
            return {}
        rows = (handoff_payload.get("validate_now", []) or []) + (handoff_payload.get("act_now", []) or [])
        row = next((row for row in rows if str(row.get("Code")) == str(code)), None)
        if not row:
            return {}
        return row

    def _step_label(row: dict[str, object]) -> str:
        if not row:
            return "none"
        return "{code} {name}".format(code=row.get("Code", "-"), name=row.get("Name", "-"))

    def _gate_blocker_from_status(status: object) -> str:
        status_text = str(status or "")
        if "review_label gate blocks" in status_text:
            return "review_label"
        if "needs " in status_text:
            return "confirmation"
        if status_text == "already_cleared":
            return "cleared"
        return "active"

    def _rationale_or_fallback(section: str, fallback: str) -> str:
        value = (handoff_payload.get(section, {}) or {}).get("rationale")
        if value not in {None, "", "none"}:
            return str(value)
        return fallback

    def _watch_focus(severity: str) -> dict[str, object]:
        return next(
            (
                row for row in focus_queue
                if row.get("focus_type") == "promotion_watch" and row.get("severity") == severity
            ),
            {},
        )

    def _focus_label(focus_row: dict[str, object]) -> str:
        code = focus_row.get("Code", "none")
        name = focus_row.get("Name", "none")
        if not code or code == "none":
            return "none"
        return "{code} {name}".format(code=code, name=name)

    def _headline_label(focus_row: dict[str, object]) -> str:
        if not focus_row:
            return "none"
        return "focus_type={focus_type}; code={code}; name={name}".format(
            focus_type=focus_row.get("focus_type", "none"),
            code=focus_row.get("Code", "none"),
            name=focus_row.get("Name", "none"),
        )

    promotion_check = _step_row("promotion_check")
    promotion_backup = _step_row("promotion_backup")
    defense_watch = _step_row("defense_watch")
    hot_watch_focus = _watch_focus("hot")
    warm_watch_focus = _watch_focus("warm")
    top_focus = focus_queue[0] if focus_queue else {}
    primary_focus = top_focus if top_focus else _focus_row(promotion_check.get("Code"))
    validate_now_rows = handoff_payload.get("validate_now", []) or []
    act_now_rows = handoff_payload.get("act_now", []) or []
    validate_competition = (handoff_payload.get("validate_competition", {}) or {})
    if not validate_competition:
        validate_competition = handoff_summary._build_validate_competition(validate_now_rows)
    act_now_competition = (handoff_payload.get("act_now_competition", {}) or {})
    if not act_now_competition:
        act_now_competition = handoff_summary._build_act_now_competition(act_now_rows)

    def _validate_competition_basis(rows: list[dict[str, object]]) -> dict[str, object]:
        if not rows:
            return {}
        ordered = sorted(
            rows,
            key=lambda row: (
                int(row.get("validate_priority_rank", 999) or 999),
                float(row.get("nearest_signal_gap", 999.0) or 999.0),
                float(row.get("total_signal_gap", 999.0) or 999.0),
                -float(row.get("promotion_readiness_score", 0.0) or 0.0),
                str(row.get("Code", "")),
            ),
        )
        leader = ordered[0]
        challenger = ordered[1] if len(ordered) > 1 else {}
        leader_next_gate, leader_gap_summary = _split_gate_status(leader.get("next_gate_summary", "none"))
        basis = {
            "leader_code": leader.get("Code", "none"),
            "leader_primary_gap": leader.get("primary_gap_signal", "none"),
            "leader_nearest_gap": leader.get("nearest_signal_gap", "none"),
            "leader_total_gap": leader.get("total_signal_gap", "none"),
            "leader_next_gate": leader_next_gate,
            "leader_gap_summary": leader_gap_summary,
            "challenger_code": challenger.get("Code", "none"),
        }
        if challenger:
            challenger_next_gate, challenger_gap_summary = _split_gate_status(challenger.get("next_gate_summary", "none"))
            basis.update(
                {
                    "challenger_primary_gap": challenger.get("primary_gap_signal", "none"),
                    "challenger_nearest_gap": challenger.get("nearest_signal_gap", "none"),
                    "challenger_total_gap": challenger.get("total_signal_gap", "none"),
                    "challenger_next_gate": challenger_next_gate,
                    "challenger_gap_summary": challenger_gap_summary,
                }
            )
        return basis

    def _act_now_competition_basis(rows: list[dict[str, object]]) -> dict[str, object]:
        if not rows:
            return {}
        ordered = sorted(
            rows,
            key=lambda row: (
                0 if row.get("act_now_risk_status") == "hot" else 1,
                float(row.get("offensive_rank", 999.0) or 999.0),
                -float(row.get("offensive_score", 0.0) or 0.0),
                str(row.get("Code", "")),
            ),
        )
        leader = ordered[0]
        challenger = ordered[1] if len(ordered) > 1 else {}
        basis = {
            "leader_code": leader.get("Code", "none"),
            "leader_risk_status": leader.get("act_now_risk_status", "off"),
            "leader_weakest_signal": leader.get("weakest_met_signal", "none"),
            "leader_weakest_margin": handoff_summary._extract_summary_metric(
                leader.get("act_now_risk_summary"),
                "weakest_margin",
                default="none",
            ),
            "challenger_code": challenger.get("Code", "none"),
        }
        if challenger:
            basis.update(
                {
                    "challenger_risk_status": challenger.get("act_now_risk_status", "off"),
                    "challenger_weakest_signal": challenger.get("weakest_met_signal", "none"),
                    "challenger_weakest_margin": handoff_summary._extract_summary_metric(
                        challenger.get("act_now_risk_summary"),
                        "weakest_margin",
                        default="none",
                    ),
                }
            )
        return basis

    validate_basis = _validate_competition_basis(validate_now_rows)
    act_now_basis = _act_now_competition_basis(act_now_rows)

    def _focus_order_map(focus_type: str) -> dict[str, int]:
        return {
            str(row.get("Code")): index
            for index, row in enumerate(
                [row for row in focus_queue if row.get("focus_type") == focus_type],
                start=1,
            )
        }

    def _sort_by_focus_order(
        rows: list[dict[str, object]],
        focus_order: dict[str, int],
        *,
        fallback_rank_key: str,
    ) -> list[dict[str, object]]:
        return sorted(
            rows,
            key=lambda row: (
                int(focus_order.get(str(row.get("Code")), 999)),
                float(row.get(fallback_rank_key, 999) or 999),
                str(row.get("Code", "")),
            ),
        )

    validate_focus_order = _focus_order_map("promotion_watch")
    act_now_focus_order = _focus_order_map("act_now_risk")
    validate_now_rows = _sort_by_focus_order(
        validate_now_rows,
        validate_focus_order,
        fallback_rank_key="validate_priority_rank",
    )
    act_now_rows = _sort_by_focus_order(
        act_now_rows,
        act_now_focus_order,
        fallback_rank_key="offensive_rank",
    )

    validate_gate_details = {
        str(row.get("Code", "none")): _split_gate_status(row.get("next_gate_summary", "none"))
        for row in validate_now_rows
    }
    act_now_gate_details = {
        str(row.get("Code", "none")): _split_gate_status(row.get("next_gate_summary", "none"))
        for row in act_now_rows
    }

    validate_gate_counts = {"review_label": 0, "confirmation": 0, "cleared": 0, "active": 0}
    for row in validate_now_rows:
        validate_gate_counts[_gate_blocker_from_status(row.get("next_gate_summary"))] += 1
    validate_gate_summary = "validate_now_gate_mix: review_label={review_label}, confirmation={confirmation}, cleared={cleared}, other={active}".format(
        review_label=validate_gate_counts["review_label"],
        confirmation=validate_gate_counts["confirmation"],
        cleared=validate_gate_counts["cleared"],
        active=validate_gate_counts["active"],
    )
    validate_gate_summary = "review_label={review_label}; confirmation={confirmation}; cleared={cleared}; other={active}".format(
        review_label=validate_gate_counts["review_label"],
        confirmation=validate_gate_counts["confirmation"],
        cleared=validate_gate_counts["cleared"],
        active=validate_gate_counts["active"],
    )
    validate_gate_lineup = " | ".join(
        "code={code}; review_label={review_label}; gate_blocker={gate_blocker}".format(
            code=row.get("Code", "none"),
            review_label=row.get("review_label", "none"),
            gate_blocker=_gate_blocker_from_status(row.get("next_gate_summary")),
        )
        for row in validate_now_rows
    ) if validate_now_rows else "none"
    act_now_gate_counts = {"review_label": 0, "confirmation": 0, "cleared": 0, "active": 0}
    for row in act_now_rows:
        act_now_gate_counts[_gate_blocker_from_status(row.get("next_gate_summary"))] += 1
    act_now_gate_summary = "act_now_gate_mix: review_label={review_label}, confirmation={confirmation}, cleared={cleared}, other={active}".format(
        review_label=act_now_gate_counts["review_label"],
        confirmation=act_now_gate_counts["confirmation"],
        cleared=act_now_gate_counts["cleared"],
        active=act_now_gate_counts["active"],
    )
    act_now_gate_summary = "review_label={review_label}; confirmation={confirmation}; cleared={cleared}; other={active}".format(
        review_label=act_now_gate_counts["review_label"],
        confirmation=act_now_gate_counts["confirmation"],
        cleared=act_now_gate_counts["cleared"],
        active=act_now_gate_counts["active"],
    )
    act_now_live_rows = [row for row in act_now_rows if row.get("act_now_risk_status") in {"hot", "warm"}]
    act_now_dormant_rows = [row for row in act_now_rows if row.get("act_now_risk_status") not in {"hot", "warm"}]
    act_now_live_gate_counts = {"review_label": 0, "confirmation": 0, "cleared": 0, "active": 0}
    for row in act_now_live_rows:
        act_now_live_gate_counts[_gate_blocker_from_status(row.get("next_gate_summary"))] += 1
    act_now_live_gate_summary = "review_label={review_label}; confirmation={confirmation}; cleared={cleared}; other={active}".format(
        review_label=act_now_live_gate_counts["review_label"],
        confirmation=act_now_live_gate_counts["confirmation"],
        cleared=act_now_live_gate_counts["cleared"],
        active=act_now_live_gate_counts["active"],
    )
    act_now_gate_lineup = " | ".join(
        "code={code}; review_label={review_label}; gate_blocker={gate_blocker}; risk_status={risk_status}".format(
            code=row.get("Code", "none"),
            review_label=row.get("review_label", "none"),
            gate_blocker=_gate_blocker_from_status(row.get("next_gate_summary")),
            risk_status=row.get("act_now_risk_status", "off"),
        )
        for row in act_now_rows
    ) if act_now_rows else "none"
    act_now_live_gate_lineup = " | ".join(
        "code={code}; review_label={review_label}; gate_blocker={gate_blocker}; risk_status={risk_status}".format(
            code=row.get("Code", "none"),
            review_label=row.get("review_label", "none"),
            gate_blocker=_gate_blocker_from_status(row.get("next_gate_summary")),
            risk_status=row.get("act_now_risk_status", "off"),
        )
        for row in act_now_live_rows
    ) if act_now_live_rows else "none"
    act_now_dormant_brief = " | ".join(
        "code={code}; name={name}; gate_blocker={gate_blocker}".format(
            code=row.get("Code", "none"),
            name=row.get("Name", "none"),
            gate_blocker=_gate_blocker_from_status(row.get("next_gate_summary")),
        )
        for row in act_now_dormant_rows
    ) if act_now_dormant_rows else "none"
    validate_now_members = [
        {
            "Code": row.get("Code", "none"),
            "Name": row.get("Name", "none"),
            "review_label": row.get("review_label", "none"),
            "gate_blocker": _gate_blocker_from_status(row.get("next_gate_summary")),
            "gate_status": validate_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[0],
            "gap_summary": validate_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[1],
            "promotion_watch_status": row.get("promotion_watch_status", "off"),
            "promotion_watch_summary": row.get("promotion_watch_summary", "none"),
            "promotion_readiness_score": row.get("promotion_readiness_score", 0),
            "validate_priority_rank": row.get("validate_priority_rank", 999),
            "next_gate_summary": row.get("next_gate_summary", "none"),
        }
        for row in validate_now_rows
    ]
    act_now_members = [
        {
            "Code": row.get("Code", "none"),
            "Name": row.get("Name", "none"),
            "review_label": row.get("review_label", "none"),
            "gate_blocker": _gate_blocker_from_status(row.get("next_gate_summary")),
            "gate_status": act_now_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[0],
            "gap_summary": act_now_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[1],
            "act_now_risk_status": row.get("act_now_risk_status", "off"),
            "act_now_risk_summary": row.get("act_now_risk_summary", "none"),
            "offensive_rank": row.get("offensive_rank", 999),
            "next_gate_summary": row.get("next_gate_summary", "none"),
        }
        for row in act_now_rows
    ]
    act_now_live_members = [
        {
            "Code": row.get("Code", "none"),
            "Name": row.get("Name", "none"),
            "review_label": row.get("review_label", "none"),
            "gate_blocker": _gate_blocker_from_status(row.get("next_gate_summary")),
            "gate_status": act_now_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[0],
            "gap_summary": act_now_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[1],
            "act_now_risk_status": row.get("act_now_risk_status", "off"),
            "act_now_risk_summary": row.get("act_now_risk_summary", "none"),
            "offensive_rank": row.get("offensive_rank", 999),
            "next_gate_summary": row.get("next_gate_summary", "none"),
        }
        for row in act_now_live_rows
    ]
    act_now_dormant_members = [
        {
            "Code": row.get("Code", "none"),
            "Name": row.get("Name", "none"),
            "review_label": row.get("review_label", "none"),
            "gate_blocker": _gate_blocker_from_status(row.get("next_gate_summary")),
            "gate_status": act_now_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[0],
            "gap_summary": act_now_gate_details.get(str(row.get("Code", "none")), ("none", "none"))[1],
            "act_now_risk_status": row.get("act_now_risk_status", "off"),
            "act_now_risk_summary": row.get("act_now_risk_summary", "none"),
            "offensive_rank": row.get("offensive_rank", 999),
            "next_gate_summary": row.get("next_gate_summary", "none"),
        }
        for row in act_now_dormant_rows
    ]
    runbook_rows = [row for row in operator_runbook if row]
    operator_focuses = [
        {
            "focus_rank": row.get("focus_rank", index),
            "focus_type": row.get("focus_type", "none"),
            "Code": row.get("Code", "none"),
            "Name": row.get("Name", "none"),
            "severity": row.get("severity", "none"),
            "summary": row.get("summary", "none"),
            "review_label": _decision_row(row.get("Code")).get("review_label", "none"),
            "gate_status": _decision_row(row.get("Code")).get("next_gate_summary", "none"),
            "gate_blocker": _gate_blocker_from_status(_decision_row(row.get("Code")).get("next_gate_summary")),
            "gate_status_short": _split_gate_status(_decision_row(row.get("Code")).get("next_gate_summary", "none"))[0],
            "gap_summary": _split_gate_status(_decision_row(row.get("Code")).get("next_gate_summary", "none"))[1],
            "action": row.get("operator_action", "none"),
            "reason": next(
                (
                    step_row.get("reason", "none")
                    for step_row in operator_runbook
                    if str(step_row.get("Code")) == str(row.get("Code"))
                ),
                row.get("operator_note", "none"),
            ),
            "next_gate": row.get("next_gate_summary", "none"),
        }
        for index, row in enumerate(focus_queue, start=1)
    ]
    operator_steps = [
        {
            "step_rank": index,
            "step_type": row.get("step_type", "none"),
            "Code": row.get("Code", "none"),
            "Name": row.get("Name", "none"),
            "gate_blocker": _gate_blocker_from_status(_decision_row(row.get("Code")).get("next_gate_summary")),
            "action": row.get("action", "none"),
        }
        for index, row in enumerate(runbook_rows, start=1)
    ]
    primary_call_code = primary_focus.get("Code", promotion_check.get("Code", "none"))
    primary_call_name = primary_focus.get("Name", promotion_check.get("Name", "none"))
    primary_call_type = primary_focus.get("focus_type", promotion_check.get("step_type", "none"))
    primary_call_action = primary_focus.get("operator_action", promotion_check.get("action", "none"))
    primary_call_note = primary_focus.get("operator_note", "none")
    primary_call_decision = _decision_row(primary_call_code)
    primary_call_gate_status = primary_call_decision.get("next_gate_summary", "none")
    primary_call_gate_blocker = _gate_blocker_from_status(primary_call_gate_status)
    primary_call_gate_status_short, primary_call_gap_summary = _split_gate_status(primary_call_gate_status)
    primary_call_review_label = primary_call_decision.get("review_label", "none")
    primary_call_reason = next(
        (
            row.get("reason", "none")
            for row in operator_runbook
            if str(row.get("Code")) == str(primary_call_code)
        ),
        primary_focus.get("summary", "none"),
    )
    hot_watch_code = hot_watch_focus.get("Code", "none")
    hot_watch_name = hot_watch_focus.get("Name", "none")
    hot_watch_decision = _decision_row(hot_watch_code)
    hot_watch_gate_blocker = _gate_blocker_from_status(hot_watch_decision.get("next_gate_summary"))
    hot_watch_gate_status_short, hot_watch_gap_summary = _split_gate_status(hot_watch_decision.get("next_gate_summary", "none"))
    warm_watch_code = warm_watch_focus.get("Code", "none")
    warm_watch_name = warm_watch_focus.get("Name", "none")
    warm_watch_decision = _decision_row(warm_watch_code)
    warm_watch_gate_blocker = _gate_blocker_from_status(warm_watch_decision.get("next_gate_summary"))
    warm_watch_gate_status_short, warm_watch_gap_summary = _split_gate_status(warm_watch_decision.get("next_gate_summary", "none"))
    defense_code = defense_watch.get("Code", "none")
    dormant_focus = next((row for row in focus_queue if row.get("focus_type") == "act_now_dormant"), {})
    defense_name = defense_watch.get("Name", "none")
    defense_decision = _decision_row(defense_watch.get("Code"))
    defense_risk_status = defense_decision.get("act_now_risk_status", "off")
    defense_weakest_signal = defense_decision.get("weakest_met_signal", "none")
    quality_status = screening_quality.get("quality_status", "unknown")
    quality_scan = "status={status}; attempted={attempted}; fetched={fetched}; valid={valid}; empty_price={empty_price}; invalid_momentum={invalid}; fetch_coverage={fetch_coverage}; success_coverage={success_coverage}".format(
        status=screening_quality.get("quality_status", "unknown"),
        attempted=screening_quality.get("attempted_ticker_count", 0),
        fetched=screening_quality.get("price_fetch_success_count", 0),
        valid=screening_quality.get("valid_momentum_count", 0),
        empty_price=screening_quality.get("empty_price_count", 0),
        invalid=screening_quality.get("invalid_momentum_count", 0),
        fetch_coverage=_fmt_metric(screening_quality.get("price_fetch_coverage", 0)),
        success_coverage=_fmt_metric(screening_quality.get("success_coverage", 0)),
    )
    data_quality_focus_summary = operator_board.get(
        "data_quality_focus_summary",
        "data_quality_guard: count=0, status={status}".format(status=quality_status),
    )
    latest_update_scan = "status={status}; reason={reason}".format(
        status=latest_update.get("status", "none"),
        reason=latest_update.get("reason", "none"),
    )
    cycle_diff_labels = "previous={previous}; current={current}".format(
        previous=(guard_payload or {}).get("previous_label", "none") or "none",
        current=(guard_payload or {}).get("current_label", "none") or "none",
    )
    cycle_guard_context = "status={status}; previous={previous}; current={current}".format(
        status=(guard_payload or {}).get("guard_status", "none") or "none",
        previous=(guard_payload or {}).get("previous_label", "none") or "none",
        current=(guard_payload or {}).get("current_label", "none") or "none",
    )
    guard_scan = "status={status}; breaches={breaches}; quality={quality}; note={note}".format(
        status=(guard_payload or {}).get("guard_status", "unknown"),
        breaches=operator_board.get("guard_breach_summary", "none"),
        quality=operator_board.get("guard_quality_status", "unknown"),
        note=operator_board.get("guard_note", "none"),
    )
    guard_delta_scan = _render_guard_delta_scan(guard_payload)
    operator_scan = {
        "state_scan": "act_now={act_now}; validate_now={validate_now}; hot_watch={hot_code}; live_risk={risk_code}; guard={guard}; dormant={dormant}".format(
            act_now=len(act_now_rows),
            validate_now=len(validate_now_rows),
            hot_code=hot_watch_code,
            risk_code=defense_code,
            guard=(guard_payload or {}).get("guard_status", "unknown"),
            dormant=dormant_focus.get("Code", "none"),
        ),
        "promotion_scan": "hot_code={hot_code}; hot_name={hot_name}; hot_gate={hot_gate}; hot_action={hot_action} | warm_code={warm_code}; warm_name={warm_name}; warm_gate={warm_gate}; warm_action={warm_action}".format(
            hot_code=hot_watch_code,
            hot_name=hot_watch_name,
            hot_gate=hot_watch_gate_blocker,
            hot_action=hot_watch_focus.get("operator_action", "none"),
            warm_code=warm_watch_code,
            warm_name=warm_watch_name,
            warm_gate=warm_watch_gate_blocker,
            warm_action=warm_watch_focus.get("operator_action", "none"),
        ),
        "defense_scan": "code={code}; name={name}; risk_status={risk_status}; weakest_signal={weakest_signal}; action={action}".format(
            code=defense_code,
            name=defense_name,
            risk_status=defense_risk_status,
            weakest_signal=defense_weakest_signal,
            action=defense_watch.get("action", "none"),
        ),
        "primary_call_scan": "focus_type={focus_type}; code={code}; gate_blocker={gate_blocker}; action={action}".format(
            focus_type=primary_call_type,
            code=primary_call_code,
            gate_blocker=primary_call_gate_blocker,
            action=primary_call_action,
        ),
        "priority_scan": "top_focus={focus_type}:{code}; gate_blocker={gate_blocker}; action={action}; reason={reason}".format(
            focus_type=primary_call_type,
            code=primary_call_code,
            gate_blocker=primary_call_gate_blocker,
            action=primary_call_action,
            reason=primary_call_reason,
        ),
        "runbook_scan": " | ".join(
            "rank={rank}; step_type={step_type}; code={code}; gate_blocker={gate_blocker}; action={action}".format(
                rank=row.get("step_rank", "-"),
                step_type=row.get("step_type", "none"),
                code=row.get("Code", "none"),
                gate_blocker=row.get("gate_blocker", "none"),
                action=row.get("action", "none"),
            )
            for row in operator_steps
        ) if operator_steps else "none",
        "compare_scan": operator_board.get("compare_summary_contract", operator_board.get("compare_summary", "none")),
        "risk_compare_scan": operator_board.get("risk_compare_summary_contract", operator_board.get("risk_compare_summary", "none")),
        "live_scan": "{live} | {dormant}".format(
            live=operator_board.get("live_summary", "none"),
            dormant=operator_board.get("dormant_summary", "none"),
        ),
        "guard_scan": guard_scan,
        "cycle_diff_labels": cycle_diff_labels,
        "cycle_guard_context": cycle_guard_context,
        "guard_delta_scan": guard_delta_scan,
        "quality_scan": quality_scan,
        "data_quality_focus_scan": data_quality_focus_summary,
        "latest_update_scan": latest_update_scan,
    }

    data_quality_focus_count = sum(1 for row in focus_queue if row.get("focus_type") == "data_quality_guard")

    return {
        "guard_status": (guard_payload or {}).get("guard_status", "unknown"),
        "operator_headline": "act_now={act_now}; validate_now={validate_now}; watch_hot={watch_hot}; risk_hot={risk_hot}; data_quality={data_quality}; top_focus={top_focus}".format(
            act_now=len(act_now_rows),
            validate_now=len(validate_now_rows),
            watch_hot=sum(1 for row in focus_queue if row.get("focus_type") == "promotion_watch" and row.get("severity") == "hot"),
            risk_hot=sum(1 for row in focus_queue if row.get("focus_type") == "act_now_risk" and row.get("severity") == "hot"),
            data_quality=data_quality_focus_count,
            top_focus=_headline_label(primary_focus),
        ),
        "cycle_diff_labels": cycle_diff_labels,
        "cycle_guard_context": cycle_guard_context,
        "operator_scan": operator_scan,
        "operator_steps": operator_steps,
        "primary_call": operator_board.get("primary_call", "none"),
        "primary_call_review_label": primary_call_review_label,
        "primary_call_gate_status": primary_call_gate_status,
        "primary_call_gate_status_short": primary_call_gate_status_short,
        "primary_call_gap_summary": primary_call_gap_summary,
        "primary_call_gate_blocker": primary_call_gate_blocker,
        "watch_summary": "hot={hot}; warm={warm}".format(
            hot=sum(1 for row in focus_queue if row.get("focus_type") == "promotion_watch" and row.get("severity") == "hot"),
            warm=sum(1 for row in focus_queue if row.get("focus_type") == "promotion_watch" and row.get("severity") == "warm"),
        ),
        "compare_summary": operator_board.get("compare_summary", "none"),
        "compare_summary_contract": operator_board.get("compare_summary_contract", "none"),
        "risk_compare_summary": operator_board.get("risk_compare_summary", "none"),
        "risk_compare_summary_contract": operator_board.get("risk_compare_summary_contract", "none"),
        "live_summary": operator_board.get("live_summary", "none"),
        "dormant_summary": operator_board.get("dormant_summary", "none"),
        "data_quality_focus_summary": data_quality_focus_summary,
        "data_quality_summary": operator_board.get("data_quality_summary", quality_scan),
        "validate_gate_summary": validate_gate_summary,
        "validate_gate_lineup": validate_gate_lineup,
        "act_now_gate_summary": act_now_gate_summary,
        "act_now_gate_lineup": act_now_gate_lineup,
        "act_now_live_count": len(act_now_live_rows),
        "act_now_dormant_count": len(act_now_dormant_rows),
        "act_now_live_gate_summary": act_now_live_gate_summary,
        "act_now_live_gate_lineup": act_now_live_gate_lineup,
        "validate_now_members": validate_now_members,
        "act_now_members": act_now_members,
        "act_now_live_members": act_now_live_members,
        "act_now_dormant_members": act_now_dormant_members,
        "act_now_dormant_brief": act_now_dormant_brief,
        "validate_competition_summary": _render_validate_competition_summary(validate_competition),
        "validate_competition_rationale": _render_validate_competition_rationale(
            validate_competition,
            validate_basis,
        ),
        "validate_competition_leader_code": validate_competition.get("leader_code", "none"),
        "validate_competition_challenger_code": validate_competition.get("challenger_code", "none"),
        "validate_competition_nearest_gap_edge": validate_competition.get("nearest_gap_edge", "none"),
        "validate_competition_total_gap_edge": validate_competition.get("total_gap_edge", "none"),
        "validate_competition_readiness_edge": validate_competition.get("readiness_edge", "none"),
        "validate_competition_leader_primary_gap": validate_basis.get("leader_primary_gap", "none"),
        "validate_competition_leader_nearest_gap": validate_basis.get("leader_nearest_gap", "none"),
        "validate_competition_leader_total_gap": validate_basis.get("leader_total_gap", "none"),
        "validate_competition_leader_next_gate": validate_basis.get("leader_next_gate", "none"),
        "validate_competition_leader_gap_summary": validate_basis.get("leader_gap_summary", "none"),
        "validate_competition_challenger_primary_gap": validate_basis.get("challenger_primary_gap", "none"),
        "validate_competition_challenger_nearest_gap": validate_basis.get("challenger_nearest_gap", "none"),
        "validate_competition_challenger_total_gap": validate_basis.get("challenger_total_gap", "none"),
        "validate_competition_challenger_next_gate": validate_basis.get("challenger_next_gate", "none"),
        "validate_competition_challenger_gap_summary": validate_basis.get("challenger_gap_summary", "none"),
        "act_now_competition_summary": _render_act_now_competition_summary(act_now_competition),
        "act_now_competition_rationale": _render_act_now_competition_rationale(
            act_now_competition,
            act_now_basis,
        ),
        "act_now_competition_leader_code": act_now_competition.get("leader_code", "none"),
        "act_now_competition_challenger_code": act_now_competition.get("challenger_code", "none"),
        "act_now_competition_margin_edge": act_now_competition.get("margin_edge", "none"),
        "act_now_competition_score_edge": act_now_competition.get("score_edge", "none"),
        "act_now_competition_leader_risk_status": act_now_basis.get("leader_risk_status", "off"),
        "act_now_competition_leader_weakest_signal": act_now_basis.get("leader_weakest_signal", "none"),
        "act_now_competition_leader_weakest_margin": act_now_basis.get("leader_weakest_margin", "none"),
        "act_now_competition_challenger_risk_status": act_now_basis.get("challenger_risk_status", "off"),
        "act_now_competition_challenger_weakest_signal": act_now_basis.get("challenger_weakest_signal", "none"),
        "act_now_competition_challenger_weakest_margin": act_now_basis.get("challenger_weakest_margin", "none"),
        "risk_summary": "hot={hot}; warm={warm}".format(
            hot=sum(1 for row in focus_queue if row.get("focus_type") == "act_now_risk" and row.get("severity") == "hot"),
            warm=sum(1 for row in focus_queue if row.get("focus_type") == "act_now_risk" and row.get("severity") == "warm"),
        ),
        "guard_scan": guard_scan,
        "guard_delta_summary": guard_delta_scan,
        "guard_summary": operator_board.get("guard_summary", "status={status}".format(status=(guard_payload or {}).get("guard_status", "unknown"))),
        "guard_note": operator_board.get("guard_note", "none"),
        "guard_breach_summary": operator_board.get("guard_breach_summary", "none"),
        "guard_quality_status": operator_board.get("guard_quality_status", "unknown"),
        "guard_quality_summary": operator_board.get("guard_quality_summary", "none"),
        "primary_call_note": primary_call_note,
        "hot_promotion_watch": _focus_label(hot_watch_focus),
        "hot_promotion_watch_code": promotion_check.get("Code", "none"),
        "hot_promotion_watch_code": hot_watch_code,
        "hot_promotion_watch_name": hot_watch_name,
        "hot_promotion_watch_review_label": hot_watch_decision.get("review_label", "none"),
        "hot_promotion_watch_gate_status": hot_watch_decision.get("next_gate_summary", "none"),
        "hot_promotion_watch_gate_status_short": hot_watch_gate_status_short,
        "hot_promotion_watch_gap_summary": hot_watch_gap_summary,
        "hot_promotion_watch_gate_blocker": hot_watch_gate_blocker,
        "hot_promotion_watch_action": hot_watch_focus.get("operator_action", "none"),
        "hot_promotion_watch_reason": next(
            (row.get("reason", "none") for row in operator_runbook if str(row.get("Code")) == str(hot_watch_code)),
            "none",
        ),
        "warm_promotion_watch": _focus_label(warm_watch_focus),
        "warm_promotion_watch_code": warm_watch_code,
        "warm_promotion_watch_name": warm_watch_name,
        "warm_promotion_watch_review_label": warm_watch_decision.get("review_label", "none"),
        "warm_promotion_watch_gate_status": warm_watch_decision.get("next_gate_summary", "none"),
        "warm_promotion_watch_gate_status_short": warm_watch_gate_status_short,
        "warm_promotion_watch_gap_summary": warm_watch_gap_summary,
        "warm_promotion_watch_gate_blocker": warm_watch_gate_blocker,
        "warm_promotion_watch_action": warm_watch_focus.get("operator_action", "none"),
        "warm_promotion_watch_reason": next(
            (row.get("reason", "none") for row in operator_runbook if str(row.get("Code")) == str(warm_watch_code)),
            "none",
        ),
        "primary_defense_watch": _step_label(defense_watch),
        "primary_defense_watch_code": defense_watch.get("Code", "none"),
        "primary_defense_watch_name": defense_watch.get("Name", "none"),
        "primary_defense_watch_review_label": _decision_row(defense_watch.get("Code")).get("review_label", "none"),
        "primary_defense_watch_gate_status": _decision_row(defense_watch.get("Code")).get("next_gate_summary", "none"),
        "primary_defense_watch_gate_blocker": _gate_blocker_from_status(_decision_row(defense_watch.get("Code")).get("next_gate_summary")),
        "primary_defense_watch_action": defense_watch.get("action", "none"),
        "primary_defense_watch_reason": defense_watch.get("reason", "none"),
        "primary_call_type": primary_call_type,
        "primary_call_code": primary_call_code,
        "primary_call_name": primary_call_name,
        "primary_call_action": primary_call_action,
        "primary_call_reason": primary_call_reason,
        "operator_focuses": operator_focuses,
    }


def build_model_cycle_payload(
    *,
    stamp: str = "",
    screening_row_count: int,
    filtered_row_count: int,
    shortlist_count: int,
    act_now_count: int,
    validate_now_count: int,
    output_dir: str | Path,
    operator_snapshot: dict[str, object] | None = None,
    artifact_manifest: list[dict[str, str]] | None = None,
    screening_quality: dict[str, object] | None = None,
    latest_update: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "stamp": stamp,
        "screening_row_count": int(screening_row_count),
        "filtered_row_count": int(filtered_row_count),
        "shortlist_count": int(shortlist_count),
        "act_now_count": int(act_now_count),
        "validate_now_count": int(validate_now_count),
        "output_dir": str(output_dir),
        "operator_snapshot": operator_snapshot or {},
        "artifact_manifest": artifact_manifest or [],
        "screening_quality": screening_quality or {},
        "latest_update": latest_update or {},
    }


def render_model_cycle(payload: dict[str, object]) -> str:
    operator_snapshot = payload.get("operator_snapshot", {}) or {}
    screening_quality = payload.get("screening_quality", {}) or {}
    latest_update = payload.get("latest_update", {}) or {}
    cycle_diff_payload = payload.get("cycle_diff", {}) or {}
    cycle_guard_payload = payload.get("cycle_guard", {}) or {}
    operator_focuses = (operator_snapshot.get("operator_focuses", []) or [])
    validate_now_rows = operator_snapshot.get("validate_now_members", []) or []
    act_now_rows = operator_snapshot.get("act_now_members", []) or []
    act_now_live_rows = operator_snapshot.get("act_now_live_members", []) or []
    act_now_dormant_rows = operator_snapshot.get("act_now_dormant_members", []) or []
    operator_scan = operator_snapshot.get("operator_scan", {}) or {}
    validate_now_brief = " | ".join(
        "code={code}; name={name}; watch_status={watch_status}; gate_blocker={gate_blocker}".format(
            code=row.get("Code", "none"),
            name=row.get("Name", "none"),
            watch_status=row.get("promotion_watch_status", "off"),
            gate_blocker=row.get("gate_blocker", "none"),
        )
        for row in validate_now_rows
    ) if validate_now_rows else "none"
    act_now_brief = " | ".join(
        "code={code}; name={name}; risk_status={risk_status}; gate_blocker={gate_blocker}".format(
            code=row.get("Code", "none"),
            name=row.get("Name", "none"),
            risk_status=row.get("act_now_risk_status", "off"),
            gate_blocker=row.get("gate_blocker", "none"),
        )
        for row in act_now_rows
    ) if act_now_rows else "none"
    act_now_live_brief = " | ".join(
        "code={code}; name={name}; risk_status={risk_status}; gate_blocker={gate_blocker}".format(
            code=row.get("Code", "none"),
            name=row.get("Name", "none"),
            risk_status=row.get("act_now_risk_status", "off"),
            gate_blocker=row.get("gate_blocker", "none"),
        )
        for row in act_now_live_rows
    ) if act_now_live_rows else "none"
    act_now_dormant_brief = " | ".join(
        "code={code}; name={name}; gate_blocker={gate_blocker}".format(
            code=row.get("Code", "none"),
            name=row.get("Name", "none"),
            gate_blocker=row.get("gate_blocker", "none"),
        )
        for row in act_now_dormant_rows
    ) if act_now_dormant_rows else "none"
    lines = [
        "Offensive Model Cycle",
        f"screening_row_count={payload.get('screening_row_count', 0)}",
        f"filtered_row_count={payload.get('filtered_row_count', 0)}",
        f"shortlist_count={payload.get('shortlist_count', 0)}",
        f"act_now_count={payload.get('act_now_count', 0)}",
        f"validate_now_count={payload.get('validate_now_count', 0)}",
        f"guard_status={operator_snapshot.get('guard_status', 'unknown')}",
        "cycle_diff_labels=previous:{previous}; current:{current}".format(
            previous=cycle_diff_payload.get("previous_label", "none") or "none",
            current=cycle_diff_payload.get("current_label", "none") or "none",
        ),
        "cycle_guard_context=status:{status}; previous:{previous}; current:{current}".format(
            status=cycle_guard_payload.get("guard_status", "none") or "none",
            previous=cycle_guard_payload.get("previous_label", "none") or "none",
            current=cycle_guard_payload.get("current_label", "none") or "none",
        ),
        f"operator_headline={operator_snapshot.get('operator_headline', 'none')}",
        f"state_scan={operator_scan.get('state_scan', 'none')}",
        f"promotion_scan={operator_scan.get('promotion_scan', 'none')}",
        f"defense_scan={operator_scan.get('defense_scan', 'none')}",
        f"primary_call_scan={operator_scan.get('primary_call_scan', 'none')}",
        f"priority_scan={operator_scan.get('priority_scan', 'none')}",
        f"runbook_scan={operator_scan.get('runbook_scan', 'none')}",
        f"compare_scan={operator_scan.get('compare_scan', 'none')}",
        f"risk_compare_scan={operator_scan.get('risk_compare_scan', 'none')}",
        f"live_scan={operator_scan.get('live_scan', 'none')}",
        f"guard_scan={operator_scan.get('guard_scan', 'none')}",
        f"guard_delta_scan={operator_scan.get('guard_delta_scan', 'none')}",
        f"quality_scan={operator_scan.get('quality_scan', 'none')}",
        f"data_quality_focus_scan={operator_scan.get('data_quality_focus_scan', 'none')}",
        f"latest_update_scan={operator_scan.get('latest_update_scan', 'none')}",
        f"validate_now_brief={validate_now_brief}",
        f"act_now_brief={act_now_brief}",
        "act_now_live_summary=live={live}; dormant={dormant}".format(
            live=operator_snapshot.get("act_now_live_count", 0),
            dormant=operator_snapshot.get("act_now_dormant_count", 0),
        ),
        f"act_now_live_brief={act_now_live_brief}",
        f"act_now_dormant_brief={act_now_dormant_brief}",
        f"watch_summary={operator_snapshot.get('watch_summary', 'none')}",
        f"compare_summary={operator_snapshot.get('compare_summary', 'none')}",
        f"compare_summary_contract={operator_snapshot.get('compare_summary_contract', 'none')}",
        f"risk_compare_summary={operator_snapshot.get('risk_compare_summary', 'none')}",
        f"risk_compare_summary_contract={operator_snapshot.get('risk_compare_summary_contract', 'none')}",
        f"live_summary={operator_snapshot.get('live_summary', 'none')}",
        f"dormant_summary={operator_snapshot.get('dormant_summary', 'none')}",
        f"data_quality_focus_summary={operator_snapshot.get('data_quality_focus_summary', 'none')}",
        f"data_quality_summary={operator_snapshot.get('data_quality_summary', 'none')}",
        f"validate_gate_summary={operator_snapshot.get('validate_gate_summary', 'none')}",
        f"validate_gate_lineup={operator_snapshot.get('validate_gate_lineup', 'none')}",
        f"act_now_gate_summary={operator_snapshot.get('act_now_gate_summary', 'none')}",
        f"act_now_gate_lineup={operator_snapshot.get('act_now_gate_lineup', 'none')}",
        f"act_now_live_gate_summary={operator_snapshot.get('act_now_live_gate_summary', 'none')}",
        f"act_now_live_gate_lineup={operator_snapshot.get('act_now_live_gate_lineup', 'none')}",
        f"validate_competition={operator_snapshot.get('validate_competition_summary', 'none')}",
        f"validate_competition_rationale={operator_snapshot.get('validate_competition_rationale', 'none')}",
        "validate_competition_basis=leader={leader}; leader_primary_gap={leader_primary_gap}; leader_nearest_gap={leader_nearest_gap}; leader_total_gap={leader_total_gap}; leader_next_gate={leader_next_gate}; leader_gap_summary={leader_gap_summary}; challenger={challenger}; challenger_primary_gap={challenger_primary_gap}; challenger_nearest_gap={challenger_nearest_gap}; challenger_total_gap={challenger_total_gap}; challenger_next_gate={challenger_next_gate}; challenger_gap_summary={challenger_gap_summary}; nearest_gap_edge={nearest_gap_edge}; total_gap_edge={total_gap_edge}; readiness_edge={readiness_edge}".format(
            leader=operator_snapshot.get("validate_competition_leader_code", "none"),
            leader_primary_gap=operator_snapshot.get("validate_competition_leader_primary_gap", "none"),
            leader_nearest_gap=_fmt_metric(operator_snapshot.get("validate_competition_leader_nearest_gap", "none")),
            leader_total_gap=_fmt_metric(operator_snapshot.get("validate_competition_leader_total_gap", "none")),
            leader_next_gate=operator_snapshot.get("validate_competition_leader_next_gate", "none"),
            leader_gap_summary=operator_snapshot.get("validate_competition_leader_gap_summary", "none"),
            challenger=operator_snapshot.get("validate_competition_challenger_code", "none"),
            challenger_primary_gap=operator_snapshot.get("validate_competition_challenger_primary_gap", "none"),
            challenger_nearest_gap=_fmt_metric(operator_snapshot.get("validate_competition_challenger_nearest_gap", "none")),
            challenger_total_gap=_fmt_metric(operator_snapshot.get("validate_competition_challenger_total_gap", "none")),
            challenger_next_gate=operator_snapshot.get("validate_competition_challenger_next_gate", "none"),
            challenger_gap_summary=operator_snapshot.get("validate_competition_challenger_gap_summary", "none"),
            nearest_gap_edge=_fmt_metric(operator_snapshot.get("validate_competition_nearest_gap_edge", "none")),
            total_gap_edge=_fmt_metric(operator_snapshot.get("validate_competition_total_gap_edge", "none")),
            readiness_edge=_fmt_metric(operator_snapshot.get("validate_competition_readiness_edge", "none")),
        ),
        f"act_now_competition={operator_snapshot.get('act_now_competition_summary', 'none')}",
        f"act_now_competition_rationale={operator_snapshot.get('act_now_competition_rationale', 'none')}",
        "act_now_competition_basis=leader={leader}; leader_risk_status={leader_risk_status}; leader_weakest_signal={leader_weakest_signal}; leader_weakest_margin={leader_weakest_margin}; challenger={challenger}; challenger_risk_status={challenger_risk_status}; challenger_weakest_signal={challenger_weakest_signal}; challenger_weakest_margin={challenger_weakest_margin}; margin_edge={margin_edge}; score_edge={score_edge}".format(
            leader=operator_snapshot.get("act_now_competition_leader_code", "none"),
            leader_risk_status=operator_snapshot.get("act_now_competition_leader_risk_status", "off"),
            leader_weakest_signal=operator_snapshot.get("act_now_competition_leader_weakest_signal", "none"),
            leader_weakest_margin=_fmt_metric(operator_snapshot.get("act_now_competition_leader_weakest_margin", "none")),
            challenger=operator_snapshot.get("act_now_competition_challenger_code", "none"),
            challenger_risk_status=operator_snapshot.get("act_now_competition_challenger_risk_status", "off"),
            challenger_weakest_signal=operator_snapshot.get("act_now_competition_challenger_weakest_signal", "none"),
            challenger_weakest_margin=_fmt_metric(operator_snapshot.get("act_now_competition_challenger_weakest_margin", "none")),
            margin_edge=_fmt_metric(operator_snapshot.get("act_now_competition_margin_edge", "none")),
            score_edge=_fmt_metric(operator_snapshot.get("act_now_competition_score_edge", "none")),
        ),
        f"risk_summary={operator_snapshot.get('risk_summary', 'none')}",
        f"guard_summary={operator_snapshot.get('guard_summary', 'none')}",
        f"guard_delta_summary={operator_snapshot.get('guard_delta_summary', 'none')}",
        f"guard_breach_summary={operator_snapshot.get('guard_breach_summary', 'none')}",
        f"guard_quality_status={operator_snapshot.get('guard_quality_status', 'unknown')}",
        f"guard_quality_summary={operator_snapshot.get('guard_quality_summary', 'none')}",
        f"hot_promotion_watch={operator_snapshot.get('hot_promotion_watch', 'none')}",
        f"hot_promotion_review_label={operator_snapshot.get('hot_promotion_watch_review_label', 'none')}",
        f"hot_promotion_gate_blocker={operator_snapshot.get('hot_promotion_watch_gate_blocker', 'none')}",
        f"hot_promotion_gate_status={operator_snapshot.get('hot_promotion_watch_gate_status_short', 'none')}",
        f"hot_promotion_gap_summary={operator_snapshot.get('hot_promotion_watch_gap_summary', 'none')}",
        f"hot_promotion_action={operator_snapshot.get('hot_promotion_watch_action', 'none')}",
        f"hot_promotion_reason={operator_snapshot.get('hot_promotion_watch_reason', 'none')}",
        f"warm_promotion_watch={operator_snapshot.get('warm_promotion_watch', 'none')}",
        f"warm_promotion_review_label={operator_snapshot.get('warm_promotion_watch_review_label', 'none')}",
        f"warm_promotion_gate_blocker={operator_snapshot.get('warm_promotion_watch_gate_blocker', 'none')}",
        f"warm_promotion_gate_status={operator_snapshot.get('warm_promotion_watch_gate_status_short', 'none')}",
        f"warm_promotion_gap_summary={operator_snapshot.get('warm_promotion_watch_gap_summary', 'none')}",
        f"warm_promotion_action={operator_snapshot.get('warm_promotion_watch_action', 'none')}",
        f"warm_promotion_reason={operator_snapshot.get('warm_promotion_watch_reason', 'none')}",
        f"primary_defense_watch={operator_snapshot.get('primary_defense_watch', 'none')}",
        f"primary_defense_review_label={operator_snapshot.get('primary_defense_watch_review_label', 'none')}",
        f"primary_defense_gate_blocker={operator_snapshot.get('primary_defense_watch_gate_blocker', 'none')}",
        f"primary_defense_gate_status={operator_snapshot.get('primary_defense_watch_gate_status', 'none')}",
        f"primary_defense_action={operator_snapshot.get('primary_defense_watch_action', 'none')}",
        f"primary_defense_reason={operator_snapshot.get('primary_defense_watch_reason', 'none')}",
        f"primary_call={operator_snapshot.get('primary_call', 'none')}",
        f"primary_call_review_label={operator_snapshot.get('primary_call_review_label', 'none')}",
        f"primary_call_gate_blocker={operator_snapshot.get('primary_call_gate_blocker', 'none')}",
        f"primary_call_gate_status={operator_snapshot.get('primary_call_gate_status_short', 'none')}",
        f"primary_call_gap_summary={operator_snapshot.get('primary_call_gap_summary', 'none')}",
        f"primary_call_note={operator_snapshot.get('primary_call_note', 'none')}",
        "operator_focuses=" + " | ".join(
            "rank={rank}; type={focus_type}; code={code}; severity={severity}; review_label={review_label}; gate_blocker={gate_blocker}; action={action}; summary={summary}; next_gate={next_gate}; gap_summary={gap_summary}".format(
                rank=row.get("focus_rank", "-"),
                focus_type=row.get("focus_type", "none"),
                code=row.get("Code", "none"),
                severity=row.get("severity", "none"),
                review_label=row.get("review_label", "none"),
                gate_blocker=row.get("gate_blocker", "none"),
                action=row.get("action", "none"),
                summary=row.get("summary", "none"),
                next_gate=row.get("gate_status_short", "none"),
                gap_summary=row.get("gap_summary", "none"),
            )
            for row in operator_focuses
        ) if operator_focuses else "operator_focuses=none",
        *[
            "operator_focus_{rank}=type={focus_type}; code={code}; severity={severity}; review_label={review_label}; gate_blocker={gate_blocker}; action={action}; summary={summary}; next_gate={next_gate}; gap_summary={gap_summary}".format(
                rank=row.get("focus_rank", index),
                focus_type=row.get("focus_type", "none"),
                code=row.get("Code", "none"),
                severity=row.get("severity", "none"),
                review_label=row.get("review_label", "none"),
                gate_blocker=row.get("gate_blocker", "none"),
                action=row.get("action", "none"),
                summary=row.get("summary", "none"),
                next_gate=row.get("gate_status_short", "none"),
                gap_summary=row.get("gap_summary", "none"),
            )
            for index, row in enumerate(operator_focuses, start=1)
        ],
        *[
            "operator_step_{rank}=type={step_type}; code={code}; name={name}; gate_blocker={gate_blocker}; action={action}".format(
                rank=row.get("step_rank", index),
                step_type=row.get("step_type", "none"),
                code=row.get("Code", "none"),
                name=row.get("Name", "none"),
                gate_blocker=row.get("gate_blocker", "none"),
                action=row.get("action", "none"),
            )
            for index, row in enumerate(operator_snapshot.get("operator_steps", []) or [], start=1)
        ],
        *[
            "validate_now_member_{rank}=code={code}; name={name}; review_label={review_label}; gate_blocker={gate_blocker}; watch_status={watch_status}; readiness={readiness}; summary={summary}; next_gate={next_gate}; gap_summary={gap_summary}".format(
                rank=index,
                code=row.get("Code", "none"),
                name=row.get("Name", "none"),
                review_label=row.get("review_label", "none"),
                gate_blocker=row.get("gate_blocker", "none"),
                watch_status=row.get("promotion_watch_status", "off"),
                readiness=row.get("promotion_readiness_score", 0),
                summary=row.get("promotion_watch_summary", "none"),
                next_gate=row.get("gate_status", "none"),
                gap_summary=row.get("gap_summary", "none"),
            )
            for index, row in enumerate(validate_now_rows, start=1)
        ],
        *[
            "act_now_member_{rank}=code={code}; name={name}; review_label={review_label}; gate_blocker={gate_blocker}; risk_status={risk_status}; risk_summary={risk_summary}; next_gate={next_gate}".format(
                rank=index,
                code=row.get("Code", "none"),
                name=row.get("Name", "none"),
                review_label=row.get("review_label", "none"),
                gate_blocker=row.get("gate_blocker", "none"),
                risk_status=row.get("act_now_risk_status", "off"),
                risk_summary=row.get("act_now_risk_summary", "none"),
                next_gate=row.get("next_gate_summary", "none"),
            )
            for index, row in enumerate(act_now_rows, start=1)
        ],
        *[
            "act_now_live_member_{rank}=code={code}; name={name}; review_label={review_label}; gate_blocker={gate_blocker}; risk_status={risk_status}; risk_summary={risk_summary}; next_gate={next_gate}".format(
                rank=index,
                code=row.get("Code", "none"),
                name=row.get("Name", "none"),
                review_label=row.get("review_label", "none"),
                gate_blocker=row.get("gate_blocker", "none"),
                risk_status=row.get("act_now_risk_status", "off"),
                risk_summary=row.get("act_now_risk_summary", "none"),
                next_gate=row.get("next_gate_summary", "none"),
            )
            for index, row in enumerate(act_now_live_rows, start=1)
        ],
        "screening_quality=status={status}; attempted={attempted}; fetched={fetched}; valid={valid}; empty_price={empty_price}; invalid_momentum={invalid}; fetch_coverage={fetch_coverage}; success_coverage={success_coverage}".format(
            status=screening_quality.get("quality_status", "unknown"),
            attempted=screening_quality.get("attempted_ticker_count", 0),
            fetched=screening_quality.get("price_fetch_success_count", 0),
            valid=screening_quality.get("valid_momentum_count", 0),
            empty_price=screening_quality.get("empty_price_count", 0),
            invalid=screening_quality.get("invalid_momentum_count", 0),
            fetch_coverage=_fmt_metric(screening_quality.get("price_fetch_coverage", 0)),
            success_coverage=_fmt_metric(screening_quality.get("success_coverage", 0)),
        ),
        "screening_quality_codes=empty_price={empty_price}; invalid_momentum={invalid}".format(
            empty_price=",".join(screening_quality.get("empty_price_codes_sample", []) or []) or "none",
            invalid=",".join(screening_quality.get("invalid_momentum_codes_sample", []) or []) or "none",
        ),
        f"latest_update_status={latest_update.get('status', 'none')}",
        f"latest_update_reason={latest_update.get('reason', 'none')}",
        f"output_dir={payload.get('output_dir', '-')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=200)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--shortlist-top-n", type=int, default=5)
    parser.add_argument("--stock-sort-column", default="offensive_score")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()

    screener = MomentumScreener()
    screening_df = screener.run(
        max_items=args.max_items,
        etf_mode=False,
        stock_sort_column=args.stock_sort_column,
    )

    screening_csv_path = output_dir / f"offensive_screening_{stamp}.csv"
    screening_report_json_path = output_dir / f"offensive_screening_report_{stamp}.json"
    screening_report_md_path = output_dir / f"offensive_screening_report_{stamp}.md"
    latest_screening_csv_path = output_dir / "offensive_screening_latest.csv"
    latest_screening_report_json_path = output_dir / "offensive_screening_report_latest.json"
    latest_screening_report_md_path = output_dir / "offensive_screening_report_latest.md"

    screening_df.to_csv(screening_csv_path, index=False, encoding="utf-8-sig")
    screening_df.to_csv(latest_screening_csv_path, index=False, encoding="utf-8-sig")
    artifact_manifest: list[dict[str, str]] = [
        _manifest_entry(output_dir, "offensive_screening", stamp, "csv"),
    ]

    screening_report_payload = comparison_report.build_comparison_payload(screening_df, top_n=args.top_n)
    screening_report_text = comparison_report.render_report(screening_report_payload)
    screening_report_json_path.write_text(json.dumps(screening_report_payload, indent=2), encoding="utf-8")
    screening_report_md_path.write_text(screening_report_text, encoding="utf-8")
    latest_screening_report_json_path.write_text(json.dumps(screening_report_payload, indent=2), encoding="utf-8")
    latest_screening_report_md_path.write_text(screening_report_text, encoding="utf-8")
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_screening_report", stamp, "json"),
            _manifest_entry(output_dir, "offensive_screening_report", stamp, "md"),
        ]
    )

    summary_payload = reason_summary.build_reason_summary_payload([screening_report_payload])
    summary_text = reason_summary.render_reason_summary(summary_payload)
    _write_json_pair(output_dir, "offensive_reason_summary", stamp, summary_payload)
    _write_md_pair(output_dir, "offensive_reason_summary", stamp, summary_text)
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_reason_summary", stamp, "json"),
            _manifest_entry(output_dir, "offensive_reason_summary", stamp, "md"),
        ]
    )

    filter_rec_payload = filter_recommendation.build_filter_recommendation_payload(screening_report_payload)
    filter_rec_text = filter_recommendation.render_filter_recommendation(filter_rec_payload)
    _write_json_pair(output_dir, "offensive_filter_recommendation", stamp, filter_rec_payload)
    _write_md_pair(output_dir, "offensive_filter_recommendation", stamp, filter_rec_text)
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_filter_recommendation", stamp, "json"),
            _manifest_entry(output_dir, "offensive_filter_recommendation", stamp, "md"),
        ]
    )

    filtered_df, rejected_df = filter_apply._apply_thresholds(
        screening_df,
        filter_rec_payload.get("recommended_thresholds", {}) or {},
    )
    filter_apply_payload = filter_apply.build_filter_application_payload(screening_df, filter_rec_payload)
    filter_apply_text = filter_apply.render_filter_application(filter_apply_payload)
    _write_csv_pair(output_dir, "offensive_screening_filtered", stamp, filtered_df)
    _write_csv_pair(output_dir, "offensive_screening_rejected", stamp, rejected_df)
    _write_json_pair(output_dir, "offensive_filter_application", stamp, filter_apply_payload)
    _write_md_pair(output_dir, "offensive_filter_application", stamp, filter_apply_text)
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_screening_filtered", stamp, "csv"),
            _manifest_entry(output_dir, "offensive_screening_rejected", stamp, "csv"),
            _manifest_entry(output_dir, "offensive_filter_application", stamp, "json"),
            _manifest_entry(output_dir, "offensive_filter_application", stamp, "md"),
        ]
    )

    candidate_payload = candidate_packet.build_candidate_packet_payload(
        filtered_df,
        screening_report_payload,
        top_n=args.top_n,
    )
    candidate_text = candidate_packet.render_candidate_packet(candidate_payload)
    _write_json_pair(output_dir, "offensive_candidate_packet", stamp, candidate_payload)
    _write_md_pair(output_dir, "offensive_candidate_packet", stamp, candidate_text)
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_candidate_packet", stamp, "json"),
            _manifest_entry(output_dir, "offensive_candidate_packet", stamp, "md"),
        ]
    )

    shortlist_payload = review_shortlist.build_review_shortlist_payload(candidate_payload, top_n=args.shortlist_top_n)
    shortlist_text = review_shortlist.render_review_shortlist(shortlist_payload)
    _write_json_pair(output_dir, "offensive_review_shortlist", stamp, shortlist_payload)
    _write_md_pair(output_dir, "offensive_review_shortlist", stamp, shortlist_text)
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_review_shortlist", stamp, "json"),
            _manifest_entry(output_dir, "offensive_review_shortlist", stamp, "md"),
        ]
    )

    action_payload = action_memo.build_action_memo_payload(shortlist_payload)
    action_text = action_memo.render_action_memo(action_payload)
    _write_json_pair(output_dir, "offensive_action_memo", stamp, action_payload)
    _write_md_pair(output_dir, "offensive_action_memo", stamp, action_text)
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_action_memo", stamp, "json"),
            _manifest_entry(output_dir, "offensive_action_memo", stamp, "md"),
        ]
    )

    cycle_payload = build_model_cycle_payload(
        stamp=stamp,
        screening_row_count=len(screening_df),
        filtered_row_count=len(filtered_df),
        shortlist_count=shortlist_payload.get("shortlist_count", 0),
        act_now_count=action_payload.get("act_now_count", 0),
        validate_now_count=action_payload.get("validate_now_count", 0),
        output_dir=output_dir,
        artifact_manifest=artifact_manifest,
        screening_quality=screening_df.attrs.get("screening_quality", {}) or {},
    )

    previous_handoff_path = _find_previous_stamped_json(output_dir, "offensive_handoff_summary", stamp)
    previous_handoff_payload = None
    diff_payload = None
    guard_payload = None
    if previous_handoff_path is not None:
        previous_handoff_payload = json.loads(previous_handoff_path.read_text(encoding="utf-8"))
        diff_payload = cycle_diff.build_cycle_diff_payload(
            previous_handoff_payload,
            handoff_summary.build_handoff_summary_payload(cycle_payload, action_payload, candidate_payload),
            previous_label=previous_handoff_path.stem.replace("offensive_handoff_summary_", ""),
            current_label=stamp,
        )
        diff_text = cycle_diff.render_cycle_diff(diff_payload)
        _write_json_pair(output_dir, "offensive_cycle_diff", stamp, diff_payload)
        _write_md_pair(output_dir, "offensive_cycle_diff", stamp, diff_text)
        artifact_manifest.extend(
            [
                _manifest_entry(output_dir, "offensive_cycle_diff", stamp, "json"),
                _manifest_entry(output_dir, "offensive_cycle_diff", stamp, "md"),
            ]
        )
        guard_payload = cycle_guard.build_cycle_guard_payload(
            diff_payload,
            action_payload,
            cycle_payload.get("screening_quality", {}) or {},
        )
        guard_text = cycle_guard.render_cycle_guard(guard_payload)
        _write_json_pair(output_dir, "offensive_cycle_guard", stamp, guard_payload)
        _write_md_pair(output_dir, "offensive_cycle_guard", stamp, guard_text)
        artifact_manifest.extend(
            [
                _manifest_entry(output_dir, "offensive_cycle_guard", stamp, "json"),
                _manifest_entry(output_dir, "offensive_cycle_guard", stamp, "md"),
            ]
        )

    latest_update = _latest_protection_decision(cycle_payload, previous_handoff_payload, guard_payload)
    cycle_payload["latest_update"] = latest_update
    if diff_payload is not None:
        cycle_payload["cycle_diff"] = diff_payload
    if guard_payload is not None:
        cycle_payload["cycle_guard"] = guard_payload
    handoff_payload = handoff_summary.build_handoff_summary_payload(
        cycle_payload,
        action_payload,
        candidate_payload,
        diff_payload,
        guard_payload,
    )
    cycle_payload["operator_snapshot"] = _operator_snapshot_from_handoff(handoff_payload, guard_payload)
    handoff_text = handoff_summary.render_handoff_summary(handoff_payload)
    _write_json_pair(output_dir, "offensive_handoff_summary", stamp, handoff_payload)
    _write_md_pair(output_dir, "offensive_handoff_summary", stamp, handoff_text)
    artifact_manifest.extend(
        [
            _manifest_entry(output_dir, "offensive_model_cycle", stamp, "json"),
            _manifest_entry(output_dir, "offensive_model_cycle", stamp, "md"),
            _manifest_entry(output_dir, "offensive_handoff_summary", stamp, "json"),
            _manifest_entry(output_dir, "offensive_handoff_summary", stamp, "md"),
        ]
    )

    cycle_payload["artifact_manifest"] = artifact_manifest
    cycle_text = render_model_cycle(cycle_payload)
    _write_json_pair(output_dir, "offensive_model_cycle", stamp, cycle_payload)
    _write_md_pair(output_dir, "offensive_model_cycle", stamp, cycle_text)
    if latest_update.get("should_promote_latest", True):
        _sync_readme_thread_handoff(REPO_ROOT / "README.md", cycle_payload=cycle_payload)
    elif previous_handoff_path is not None:
        previous_stamp = previous_handoff_path.stem.replace("offensive_handoff_summary_", "")
        _restore_latest_artifacts_from_previous(artifact_manifest, previous_stamp)

    if args.json:
        print(json.dumps(cycle_payload, indent=2))
        return
    print(render_model_cycle(cycle_payload), end="")


if __name__ == "__main__":
    main()

