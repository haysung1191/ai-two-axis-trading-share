from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.manual.briefing import build_hourly_manual_brief


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ms_to_utc(value: Any) -> str | None:
    ts_ms = _safe_int(value)
    if ts_ms is None:
        return None
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except (OverflowError, OSError, ValueError):
        return None


def _dt_to_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_run_summary(logs_dir: Path, run_id: str | None) -> Path:
    candidate_names = [
        "manual_snapshot_{run_suffix}.json",
        "hourly_run_{run_suffix}.json",
    ]
    if run_id:
        run_suffix = run_id.replace(":", "_")
        for pattern in candidate_names:
            path = logs_dir / pattern.format(run_suffix=run_suffix)
            if path.exists():
                return path
        raise FileNotFoundError(f"Run summary not found for run_id={run_id}")

    candidates = list(logs_dir.glob("hourly_run_*.json")) + list(logs_dir.glob("manual_snapshot_*.json"))
    if not candidates:
        raise FileNotFoundError("No hourly_run_*.json or manual_snapshot_*.json files found.")

    ranked: list[tuple[datetime, int, float, Path]] = []
    fallback_min = datetime(1970, 1, 1, tzinfo=UTC)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if isinstance(payload, dict) and (
            isinstance(payload.get("manual_brief"), dict) or isinstance(payload.get("signals"), list)
        ):
            candle_close = payload.get("candle_close_utc")
            dt = None
            if isinstance(candle_close, str):
                try:
                    dt = datetime.fromisoformat(candle_close.replace("Z", "+00:00"))
                except ValueError:
                    dt = None
            kind_rank = 1 if path.name.startswith("manual_snapshot_") else 0
            ranked.append((dt or fallback_min, kind_rank, path.stat().st_mtime, path))
    if ranked:
        ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        return ranked[0][3]
    raise FileNotFoundError("No readable hourly run summary found.")


def _resolve_db_path(logs_dir: Path) -> Path | None:
    candidates = [
        logs_dir.parent / "state.db",
        Path.cwd() / "state.db",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_signal_snapshot(
    conn: sqlite3.Connection,
    *,
    run_id: str | None,
    symbol: str | None,
) -> dict[str, Any] | None:
    if not symbol:
        return None

    cur = conn.cursor()
    try:
        row = cur.execute(
            """
            SELECT features_json, suggested_stop_dist, suggested_tp_dist, suggested_time_exit_ts_ms
            FROM signals
            WHERE run_id = ? AND symbol = ?
            ORDER BY rank ASC, id ASC
            LIMIT 1
            """,
            (run_id, symbol),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if row is None:
        return None
    features_json, stop_dist, tp_dist, time_exit_ts_ms = row
    features = {}
    if isinstance(features_json, str):
        try:
            parsed = json.loads(features_json)
            if isinstance(parsed, dict):
                features = parsed
        except json.JSONDecodeError:
            features = {}
    close = _safe_float(features.get("close"))
    stop_dist_value = _safe_float(stop_dist)
    tp_dist_value = _safe_float(tp_dist)
    return {
        "reference_price_krw": close,
        "suggested_stop_price_krw": (
            close - stop_dist_value if close is not None and stop_dist_value is not None else None
        ),
        "suggested_take_profit_price_krw": (
            close + tp_dist_value if close is not None and tp_dist_value is not None else None
        ),
        "risk_reward_ratio": (
            tp_dist_value / stop_dist_value
            if stop_dist_value not in (None, 0.0) and tp_dist_value is not None
            else None
        ),
        "time_exit_utc": _ms_to_utc(time_exit_ts_ms),
    }


def _load_paper_order_snapshot(
    conn: sqlite3.Connection,
    *,
    run_id: str | None,
    symbol: str | None,
) -> dict[str, Any] | None:
    if not symbol:
        return None

    cur = conn.cursor()
    try:
        row = cur.execute(
            """
            SELECT entry_fill, entry_open, stop_price, tp_price, stop_dist, tp_dist, time_exit_ts_ms
            FROM paper_orders
            WHERE run_id = ? AND symbol = ?
            ORDER BY entry_ts_ms DESC, id DESC
            LIMIT 1
            """,
            (run_id, symbol),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if row is None:
        return None
    entry_fill, entry_open, stop_price, tp_price, stop_dist, tp_dist, time_exit_ts_ms = row
    reference_price = _safe_float(entry_fill)
    if reference_price is None:
        reference_price = _safe_float(entry_open)
    stop_dist_value = _safe_float(stop_dist)
    tp_dist_value = _safe_float(tp_dist)
    stop_price_value = _safe_float(stop_price)
    tp_price_value = _safe_float(tp_price)
    if stop_price_value is None and reference_price is not None and stop_dist_value is not None:
        stop_price_value = reference_price - stop_dist_value
    if tp_price_value is None and reference_price is not None and tp_dist_value is not None:
        tp_price_value = reference_price + tp_dist_value
    return {
        "reference_price_krw": reference_price,
        "suggested_stop_price_krw": stop_price_value,
        "suggested_take_profit_price_krw": tp_price_value,
        "risk_reward_ratio": (
            tp_dist_value / stop_dist_value
            if stop_dist_value not in (None, 0.0) and tp_dist_value is not None
            else None
        ),
        "time_exit_utc": _ms_to_utc(time_exit_ts_ms),
    }


def _merge_missing_fields(target: dict[str, Any], patch: dict[str, Any] | None) -> dict[str, Any]:
    if not patch:
        return target
    for key, value in patch.items():
        if target.get(key) in (None, "") and value not in (None, ""):
            target[key] = value
    return target


def _enrich_legacy_recommendations(
    recommendations: list[dict[str, Any]],
    *,
    run_id: str | None,
    logs_dir: Path,
) -> list[dict[str, Any]]:
    db_path = _resolve_db_path(logs_dir)
    if db_path is None:
        return recommendations

    try:
        conn = sqlite3.connect(str(db_path))
    except sqlite3.Error:
        return recommendations

    try:
        enriched: list[dict[str, Any]] = []
        for row in recommendations:
            item = dict(row)
            signal_snapshot = _load_signal_snapshot(conn, run_id=run_id, symbol=str(item.get("symbol") or ""))
            paper_snapshot = _load_paper_order_snapshot(conn, run_id=run_id, symbol=str(item.get("symbol") or ""))
            item = _merge_missing_fields(item, signal_snapshot)
            item = _merge_missing_fields(item, paper_snapshot)
            enriched.append(item)
        return enriched
    finally:
        conn.close()


def load_manual_brief(logs_dir: Path, run_id: str | None = None) -> dict[str, Any]:
    summary_path = _find_run_summary(logs_dir, run_id)
    payload = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid run summary payload: {summary_path}")

    brief = payload.get("manual_brief")
    recommendations = payload.get("manual_recommendations")
    source_kind = "manual_snapshot" if summary_path.name.startswith("manual_snapshot_") else "hourly_run"
    if not isinstance(recommendations, list):
        signals = payload.get("signals", [])
        if not isinstance(signals, list):
            raise ValueError(f"manual_recommendations missing in {summary_path}")
        recommendations = [_legacy_signal_to_recommendation(row) for row in signals if isinstance(row, dict)]
        recommendations = _enrich_legacy_recommendations(
            recommendations,
            run_id=str(payload.get("run_id") or ""),
            logs_dir=logs_dir,
        )
        source_kind = "legacy_signals"

    if not isinstance(brief, dict):
        brief = build_hourly_manual_brief(
            run_id=str(payload.get("run_id", "")),
            candle_close_utc=str(payload.get("candle_close_utc", "")),
            signals=recommendations,
        )

    return {
        "summary_path": str(summary_path),
        "run_id": payload.get("run_id"),
        "candle_close_utc": payload.get("candle_close_utc"),
        "metadata": payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {},
        "source_metadata": {
            "source_kind": source_kind,
            "summary_mtime_utc": _dt_to_utc(datetime.fromtimestamp(summary_path.stat().st_mtime, tz=UTC)),
        },
        "manual_brief": brief,
        "manual_recommendations": recommendations,
    }


def _legacy_signal_to_recommendation(row: dict[str, Any]) -> dict[str, Any]:
    blocked_reason = row.get("blocked_reason")
    final_decision = "SCHEDULED" if not blocked_reason else f"CANCELED:{blocked_reason}"
    if blocked_reason is None:
        action = "BUY"
        action_reason = "Scheduled by the baseline scanner."
    elif str(blocked_reason) in {"MAX_CONCURRENT", "MAX_NEW_PER_DAY", "COOLDOWN"}:
        action = "HOLD"
        action_reason = "Operational capacity or cooldown guardrail blocked entry."
    else:
        action = "NO_BUY"
        action_reason = "Guardrail blocked the trade."

    return {
        "symbol": row.get("symbol"),
        "rank": row.get("rank"),
        "action": action,
        "action_reason": action_reason,
        "policy_materiality": (
            "entry_reversal"
            if bool(row.get("scheduled_due_to_policy"))
            else ("near_miss" if bool(row.get("near_miss_after_policy")) else "none")
        ),
        "reference_price_krw": None,
        "suggested_stop_price_krw": None,
        "suggested_take_profit_price_krw": None,
        "risk_reward_ratio": None,
        "time_exit_utc": None,
        "final_decision": final_decision,
        "scheduled_due_to_policy": bool(row.get("scheduled_due_to_policy")),
        "near_miss_after_policy": bool(row.get("near_miss_after_policy")),
        "blocked_reason": blocked_reason,
    }


def render_text_brief(payload: dict[str, Any]) -> str:
    brief = payload["manual_brief"]
    lines = [
        f"run_id: {payload.get('run_id', '-')}",
        f"candle_close_utc: {payload.get('candle_close_utc', '-')}",
        f"source: {payload.get('summary_path', '-')}",
        "",
        f"headline: {brief.get('headline', '-')}",
    ]

    summary = brief.get("summary", {})
    lines.extend(
        [
            "summary:",
            f"- BUY: {int(summary.get('buy_count', 0))}",
            f"- HOLD: {int(summary.get('hold_count', 0))}",
            f"- NO_BUY: {int(summary.get('no_buy_count', 0))}",
            f"- policy_reversal: {int(summary.get('scheduled_due_to_policy_count', 0))}",
            f"- near_miss_after_policy: {int(summary.get('near_miss_after_policy_count', 0))}",
            "",
            "notes:",
        ]
    )
    for note in brief.get("notes", []):
        lines.append(f"- {note}")

    lines.append("")
    lines.append("watchlist:")
    for row in brief.get("watchlist", []):
        ref = _safe_float(row.get("reference_price_krw"))
        stop = _safe_float(row.get("suggested_stop_price_krw"))
        take_profit = _safe_float(row.get("suggested_take_profit_price_krw"))
        rr = _safe_float(row.get("risk_reward_ratio"))
        lines.append(
            "  "
            + " | ".join(
                [
                    str(row.get("symbol", "-")),
                    f"action={row.get('action', '-')}",
                    f"rank={row.get('rank', '-')}",
                    f"ref={ref:,.1f}" if ref is not None else "ref=-",
                    f"stop={stop:,.1f}" if stop is not None else "stop=-",
                    f"tp={take_profit:,.1f}" if take_profit is not None else "tp=-",
                    f"rr={rr:.2f}" if rr is not None else "rr=-",
                    f"decision={row.get('final_decision', '-')}",
                ]
            )
        )
        lines.append(f"    note: {row.get('action_reason', '-')}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the latest manual trading brief from hourly run artifacts.")
    parser.add_argument("--run-id", default=None, help="Optional run_id like 1h:1773572400000")
    parser.add_argument("--logs-dir", default="logs", help="Directory containing hourly_run_*.json files")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = load_manual_brief(Path(args.logs_dir), run_id=args.run_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text_brief(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
