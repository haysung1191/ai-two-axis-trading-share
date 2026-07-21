from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.apply_bithumb_exit_snapshot_paper import load_exit_snapshot
from scripts.build_bithumb_execution_plan import load_manual_brief
from scripts.execute_bithumb_execution_plan import build_signed_request_preview
from src.execution import build_bithumb_entry_plan
from src.execution.paper_execution_ledger import (
    apply_execution_plan_to_paper_ledger,
    apply_exit_snapshot_to_paper_ledger,
    load_paper_execution_ledger,
    save_paper_execution_ledger,
)


def _load_plan_from_logs(
    *,
    logs_dir: Path,
    run_id: str | None,
    notional_krw: float,
    max_orders: int,
    strategy_track: str,
) -> dict[str, Any]:
    brief_payload = load_manual_brief(logs_dir, run_id=run_id)
    return build_bithumb_entry_plan(
        brief_payload,
        notional_krw=notional_krw,
        max_orders=max_orders,
        strategy_track=strategy_track,
    )


def _render_text_summary(payload: dict[str, Any]) -> str:
    lines = [
        f"run_id: {payload.get('run_id', '-')}",
        f"candle_close_utc: {payload.get('candle_close_utc', '-')}",
        f"strategy_track: {payload.get('strategy_track', '-')}",
        f"paper_execution_read: {payload.get('paper_execution_read', '-')}",
        f"paper_ledger_snapshot_read: {payload.get('paper_ledger_snapshot_read', '-')}",
        f"intent_count: {payload.get('intent_count', 0)}",
        f"signed_request_count: {payload.get('signed_request_count', 0)}",
        f"paper_applied_count: {payload.get('paper_applied_count', 0)}",
        f"paper_rejected_count: {payload.get('paper_rejected_count', 0)}",
        f"paper_duplicate_count: {payload.get('paper_duplicate_count', 0)}",
        f"paper_closed_count: {payload.get('paper_closed_count', 0)}",
        f"paper_open_count: {payload.get('paper_open_count', 0)}",
        f"paper_exit_duplicate_run: {payload.get('paper_exit_duplicate_run', False)}",
        f"paper_ledger_consistent: {payload.get('paper_ledger_consistent', False)}",
        f"execution_contract_checked: {payload.get('execution_contract_checked', False)}",
        f"execution_contract_aligned: {payload.get('execution_contract_aligned', False)}",
        "execution_contract_paper_execution_read_aligned: "
        f"{payload.get('execution_contract_paper_execution_read_aligned', False)}",
        "execution_contract_paper_ledger_snapshot_aligned: "
        f"{payload.get('execution_contract_paper_ledger_snapshot_aligned', False)}",
        "execution_contract_paper_ledger_snapshot_summary_aligned: "
        f"{payload.get('execution_contract_paper_ledger_snapshot_summary_aligned', False)}",
        "execution_contract_paper_execution_contract_checked_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_checked_aligned', False)}",
        "execution_contract_paper_execution_contract_aligned_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_aligned_aligned', False)}",
        "execution_contract_paper_execution_contract_checked_summary_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_checked_summary_aligned', False)}",
        "execution_contract_paper_execution_contract_aligned_summary_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned', False)}",
        "execution_contract_paper_execution_contract_checked_aligned_entry_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_checked_aligned_entry_aligned', False)}",
        "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_aligned_aligned_entry_aligned', False)}",
        "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned', False)}",
        "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}",
        "execution_contract_paper_execution_contract_checked_aligned_summary_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_checked_aligned_summary_aligned', False)}",
        "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_aligned_aligned_summary_aligned', False)}",
        "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned', False)}",
        "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned: "
        f"{payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}",
        "paper_execution_contract_checked_aligned: "
        f"{payload.get('paper_execution_contract_checked_aligned', False)}",
        "paper_execution_contract_aligned_aligned: "
        f"{payload.get('paper_execution_contract_aligned_aligned', False)}",
        "paper_execution_contract_checked_summary_aligned: "
        f"{payload.get('paper_execution_contract_checked_summary_aligned', False)}",
        "paper_execution_contract_aligned_summary_aligned: "
        f"{payload.get('paper_execution_contract_aligned_summary_aligned', False)}",
        "paper_execution_contract_checked_aligned_entry_aligned: "
        f"{payload.get('paper_execution_contract_checked_aligned_entry_aligned', False)}",
        "paper_execution_contract_aligned_aligned_entry_aligned: "
        f"{payload.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}",
        "paper_execution_contract_checked_summary_aligned_entry_aligned: "
        f"{payload.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}",
        "paper_execution_contract_aligned_summary_aligned_entry_aligned: "
        f"{payload.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}",
        "paper_execution_contract_checked_aligned_summary_aligned: "
        f"{payload.get('paper_execution_contract_checked_aligned_summary_aligned', False)}",
        "paper_execution_contract_aligned_aligned_summary_aligned: "
        f"{payload.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}",
        "paper_execution_contract_checked_summary_aligned_summary_aligned: "
        f"{payload.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}",
        "paper_execution_contract_aligned_summary_aligned_summary_aligned: "
        f"{payload.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}",
        "",
        "artifacts:",
        f"  plan_json: {payload.get('artifacts', {}).get('plan_json', '-')}",
        f"  signed_preview_json: {payload.get('artifacts', {}).get('signed_preview_json', '-')}",
        f"  ledger_json: {payload.get('artifacts', {}).get('ledger_json', '-')}",
        f"  summary_json: {payload.get('artifacts', {}).get('summary_json', '-')}",
    ]
    return "\n".join(lines)


def _render_markdown_summary(payload: dict[str, Any]) -> str:
    artifacts = payload.get("artifacts", {})
    return "\n".join(
        [
            "# Bithumb Paper Nightly Summary",
            "",
            f"- Paper execution read: `{payload.get('paper_execution_read', '-')}`",
            f"- Paper ledger snapshot: `{payload.get('paper_ledger_snapshot_read', '-')}`",
            f"- Run id: `{payload.get('run_id', '-')}`",
            f"- Candle close UTC: `{payload.get('candle_close_utc', '-')}`",
            f"- Strategy track: `{payload.get('strategy_track', '-')}`",
            f"- Intent count: `{payload.get('intent_count', 0)}`",
            f"- Signed request count: `{payload.get('signed_request_count', 0)}`",
            f"- Paper applied count: `{payload.get('paper_applied_count', 0)}`",
            f"- Paper rejected count: `{payload.get('paper_rejected_count', 0)}`",
            f"- Paper duplicate count: `{payload.get('paper_duplicate_count', 0)}`",
            f"- Paper closed count: `{payload.get('paper_closed_count', 0)}`",
            f"- Paper open count: `{payload.get('paper_open_count', 0)}`",
            f"- Paper exit duplicate run: `{payload.get('paper_exit_duplicate_run', False)}`",
            f"- Paper ledger consistent: `{payload.get('paper_ledger_consistent', False)}`",
            f"- Execution contract checked: `{payload.get('execution_contract_checked', False)}`",
            f"- Execution contract aligned: `{payload.get('execution_contract_aligned', False)}`",
            (
                "- Execution contract paper execution read aligned: "
                f"`{payload.get('execution_contract_paper_execution_read_aligned', False)}`"
            ),
            (
                "- Execution contract paper ledger snapshot aligned: "
                f"`{payload.get('execution_contract_paper_ledger_snapshot_aligned', False)}`"
            ),
            (
                "- Execution contract paper ledger snapshot summary aligned: "
                f"`{payload.get('execution_contract_paper_ledger_snapshot_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_checked_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_aligned_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked summary aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_checked_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned summary aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked aligned entry aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_checked_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned aligned entry aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked summary aligned entry aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned summary aligned entry aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked aligned summary aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_checked_aligned_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned aligned summary aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract checked summary aligned summary aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
            ),
            (
                "- Execution contract paper execution contract aligned summary aligned summary aligned: "
                f"`{payload.get('execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked aligned: "
                f"`{payload.get('paper_execution_contract_checked_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned aligned: "
                f"`{payload.get('paper_execution_contract_aligned_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked summary aligned: "
                f"`{payload.get('paper_execution_contract_checked_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned summary aligned: "
                f"`{payload.get('paper_execution_contract_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked aligned entry aligned: "
                f"`{payload.get('paper_execution_contract_checked_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned aligned entry aligned: "
                f"`{payload.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked summary aligned entry aligned: "
                f"`{payload.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned summary aligned entry aligned: "
                f"`{payload.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked aligned summary aligned: "
                f"`{payload.get('paper_execution_contract_checked_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned aligned summary aligned: "
                f"`{payload.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract checked summary aligned summary aligned: "
                f"`{payload.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
            ),
            (
                "- Paper execution contract aligned summary aligned summary aligned: "
                f"`{payload.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
            ),
            "",
            "## Artifacts",
            f"- Plan JSON: `{artifacts.get('plan_json', '-')}`",
            f"- Signed preview JSON: `{artifacts.get('signed_preview_json', '-')}`",
            f"- Ledger JSON: `{artifacts.get('ledger_json', '-')}`",
            f"- Summary JSON: `{artifacts.get('summary_json', '-')}`",
            f"- Summary MD: `{artifacts.get('summary_md', '-')}`",
            f"- Exit JSON: `{artifacts.get('exit_json', '-')}`",
            "",
        ]
    )


def render_paper_nightly_health_line(payload: dict[str, Any]) -> str:
    return (
        "BTC 1d paper nightly"
        f" | track={payload.get('strategy_track', '-')}"
        f" | intents={payload.get('intent_count', 0)}"
        f" | signed={payload.get('signed_request_count', 0)}"
        f" | applied={payload.get('paper_applied_count', 0)}"
        f" | closed={payload.get('paper_closed_count', 0)}"
        f" | open={payload.get('paper_open_count', 0)}"
    )


def render_paper_execution_read(payload: dict[str, Any]) -> str:
    return (
        "paper execution"
        f" | track={payload.get('strategy_track', '-')}"
        f" | applied={payload.get('paper_applied_count', 0)}"
        f" | closed={payload.get('paper_closed_count', 0)}"
        f" | open={payload.get('paper_open_count', 0)}"
    )


def render_paper_ledger_snapshot_read(snapshot: dict[str, Any] | None) -> str:
    payload = snapshot or {}
    return (
        "paper ledger | "
        f"open={int(payload.get('open_position_count', 0))} | "
        f"closed={int(payload.get('closed_position_count', 0))} | "
        f"exit_fills={int(payload.get('exit_fill_count', 0))} | "
        f"orders={int(payload.get('order_count', 0))} | "
        f"fills={int(payload.get('fill_count', 0))}"
    )


def _build_ledger_consistency_summary(
    ledger: dict[str, Any],
    last_exit: dict[str, Any],
    last_apply: dict[str, Any],
) -> dict[str, Any]:
    open_position_count = len([row for row in ledger.get("positions", []) if row.get("status") == "OPEN"])
    exit_open_count = int(last_exit.get("open_count", 0) or 0)
    applied_count = int(last_apply.get("applied_count", 0) or 0)
    checks = {
        "open_positions_match_exit_plus_apply": (exit_open_count + applied_count) == open_position_count,
        "closed_positions_container_present": isinstance(ledger.get("closed_positions", []), list),
        "exit_fills_container_present": isinstance(ledger.get("exit_fills", []), list),
    }
    return {
        "open_position_count": open_position_count,
        "expected_open_position_count": exit_open_count + applied_count,
        "closed_position_count": len(ledger.get("closed_positions", [])),
        "exit_fill_count": len(ledger.get("exit_fills", [])),
        "checks": checks,
        "consistent": all(checks.values()),
    }


def _build_ledger_snapshot(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "open_position_count": len([row for row in ledger.get("positions", []) if row.get("status") == "OPEN"]),
        "closed_position_count": len(ledger.get("closed_positions", [])),
        "exit_fill_count": len(ledger.get("exit_fills", [])),
        "order_count": len(ledger.get("orders", [])),
        "fill_count": len(ledger.get("fills", [])),
    }


def _load_execution_contract_alignment(
    *,
    summary: dict[str, Any],
    execution_contract_screen_json: Path | None,
) -> dict[str, Any]:
    screen_path = execution_contract_screen_json
    if screen_path is None:
        default_path = PROJECT_ROOT / "analysis_results" / "btc_1d_execution_contract_screen_latest.json"
        screen_path = default_path if default_path.exists() else None
    if screen_path is None or not screen_path.exists():
        return {
            "execution_contract_checked": False,
            "execution_contract_source": str(screen_path) if screen_path else None,
            "execution_contract_aligned": False,
            "execution_contract_read": "",
            "execution_contract_paper_execution_read_aligned": False,
            "execution_contract_paper_ledger_snapshot_aligned": False,
            "execution_contract_paper_ledger_snapshot_summary_aligned": False,
            "execution_contract_paper_execution_contract_checked_aligned": False,
            "execution_contract_paper_execution_contract_aligned_aligned": False,
            "execution_contract_paper_execution_contract_checked_summary_aligned": False,
            "execution_contract_paper_execution_contract_aligned_summary_aligned": False,
            "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": False,
            "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": False,
            "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": False,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
            "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": False,
            "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": False,
            "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": False,
            "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
            "paper_execution_contract_checked_aligned": False,
            "paper_execution_contract_aligned_aligned": False,
            "paper_execution_contract_checked_summary_aligned": False,
            "paper_execution_contract_aligned_summary_aligned": False,
            "paper_execution_contract_checked_aligned_entry_aligned": False,
            "paper_execution_contract_aligned_aligned_entry_aligned": False,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": False,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": False,
            "paper_execution_contract_checked_aligned_summary_aligned": False,
            "paper_execution_contract_aligned_aligned_summary_aligned": False,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": False,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": False,
        }

    execution_contract_payload = json.loads(screen_path.read_text(encoding="utf-8-sig"))
    execution_contract_summary = execution_contract_payload.get("execution_contract_summary", {})
    execution_contract_verdict = execution_contract_payload.get("execution_contract_verdict", {})
    return {
        "execution_contract_checked": True,
        "execution_contract_source": str(screen_path),
        "execution_contract_aligned": bool(
            execution_contract_verdict.get("execution_contract_aligned", False)
        ),
        "execution_contract_read": execution_contract_summary.get("execution_contract_read", ""),
        "execution_contract_paper_execution_read_aligned": (
            execution_contract_summary.get("paper_execution_read", "") == summary.get("paper_execution_read", "")
        ),
        "execution_contract_paper_ledger_snapshot_aligned": (
            execution_contract_summary.get("paper_ledger_snapshot_read", "")
            == summary.get("paper_ledger_snapshot_read", "")
        ),
        "execution_contract_paper_ledger_snapshot_summary_aligned": bool(
            execution_contract_summary.get("paper_ledger_snapshot_summary_aligned", False)
        ),
        "execution_contract_paper_execution_contract_checked_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_aligned", False)
        ),
        "execution_contract_paper_execution_contract_aligned_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_aligned", False)
        ),
        "execution_contract_paper_execution_contract_checked_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_summary_aligned", False)
        ),
        "execution_contract_paper_execution_contract_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_summary_aligned", False)
        ),
        "execution_contract_paper_execution_contract_checked_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_aligned_entry_aligned", False)
        ),
        "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
        ),
        "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
        ),
        "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
        ),
        "execution_contract_paper_execution_contract_checked_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_aligned_summary_aligned", False)
        ),
        "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
        ),
        "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
        ),
        "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
        ),
        "paper_execution_contract_checked_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_aligned", False)
        ),
        "paper_execution_contract_aligned_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_aligned", False)
        ),
        "paper_execution_contract_checked_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_summary_aligned", False)
        ),
        "paper_execution_contract_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_summary_aligned", False)
        ),
        "paper_execution_contract_checked_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_aligned_entry_aligned", False)
        ),
        "paper_execution_contract_aligned_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
        ),
        "paper_execution_contract_checked_summary_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
        ),
        "paper_execution_contract_aligned_summary_aligned_entry_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
        ),
        "paper_execution_contract_checked_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_aligned_summary_aligned", False)
        ),
        "paper_execution_contract_aligned_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
        ),
        "paper_execution_contract_checked_summary_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
        ),
        "paper_execution_contract_aligned_summary_aligned_summary_aligned": bool(
            execution_contract_summary.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
        ),
    }


def run_nightly_paper(
    *,
    logs_dir: Path,
    run_id: str | None,
    ledger_json: Path,
    output_dir: Path,
    exit_json: Path | None,
    execution_contract_screen_json: Path | None = None,
    notional_krw: float,
    max_orders: int,
    strategy_track: str,
    access_key: str,
    secret_key: str,
    client_order_prefix: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = _load_plan_from_logs(
        logs_dir=logs_dir,
        run_id=run_id,
        notional_krw=notional_krw,
        max_orders=max_orders,
        strategy_track=strategy_track,
    )
    signed_preview = build_signed_request_preview(
        plan,
        access_key=access_key,
        secret_key=secret_key,
        client_order_prefix=client_order_prefix,
    )

    ledger = load_paper_execution_ledger(ledger_json)
    if exit_json:
        # Evaluate exits for the freshly closed candle before admitting new intents.
        # This avoids rejecting a valid re-entry solely because the prior position
        # was still marked OPEN at the start of the nightly cycle.
        ledger = apply_exit_snapshot_to_paper_ledger(ledger, load_exit_snapshot(exit_json))
    ledger = apply_execution_plan_to_paper_ledger(ledger, plan)
    save_paper_execution_ledger(ledger_json, ledger)

    safe_run_id = str(plan.get("run_id") or "unknown").replace(":", "-")
    plan_json = output_dir / f"bithumb_execution_plan_{safe_run_id}.json"
    signed_preview_json = output_dir / f"bithumb_signed_preview_{safe_run_id}.json"
    summary_json = output_dir / f"bithumb_paper_nightly_summary_{safe_run_id}.json"
    summary_md = output_dir / f"bithumb_paper_nightly_summary_{safe_run_id}.md"
    plan_json.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    signed_preview_json.write_text(json.dumps(signed_preview, ensure_ascii=False, indent=2), encoding="utf-8")

    last_apply = ledger.get("last_apply_summary", {})
    last_exit = ledger.get("last_exit_summary", {})
    ledger_consistency = _build_ledger_consistency_summary(ledger, last_exit, last_apply)
    paper_ledger_snapshot = _build_ledger_snapshot(ledger)
    summary = {
        "run_id": plan.get("run_id"),
        "candle_close_utc": plan.get("candle_close_utc"),
        "strategy_track": plan.get("strategy_track"),
        "intent_count": plan.get("intent_count", 0),
        "signed_request_count": signed_preview.get("intent_count", 0),
        "paper_applied_count": last_apply.get("applied_count", 0),
        "paper_rejected_count": last_apply.get("rejected_count", 0),
        "paper_duplicate_count": last_apply.get("duplicate_count", 0),
        "paper_closed_count": last_exit.get("closed_count", 0),
        "paper_open_count": len([row for row in ledger.get("positions", []) if row.get("status") == "OPEN"]),
        "paper_exit_duplicate_run": bool(last_exit.get("duplicate_run", False)),
        "paper_ledger_consistent": bool(ledger_consistency.get("consistent", False)),
        "paper_ledger_consistency": ledger_consistency,
        "paper_ledger_snapshot": paper_ledger_snapshot,
        "artifacts": {
            "plan_json": str(plan_json),
            "signed_preview_json": str(signed_preview_json),
            "ledger_json": str(ledger_json),
            "summary_json": str(summary_json),
            "summary_md": str(summary_md),
            "exit_json": str(exit_json) if exit_json else None,
        },
        "standard_check_order_reference": plan.get("standard_check_order_reference", []),
    }
    summary["paper_execution_read"] = render_paper_execution_read(summary)
    summary["paper_ledger_snapshot_read"] = render_paper_ledger_snapshot_read(paper_ledger_snapshot)
    summary.update(
        _load_execution_contract_alignment(
            summary=summary,
            execution_contract_screen_json=execution_contract_screen_json,
        )
    )
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_md.write_text(_render_markdown_summary(summary), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the nightly Bithumb paper pipeline from manual brief to signed preview to paper ledger. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--logs-dir", default="logs", help="Directory containing hourly_run_*.json files")
    parser.add_argument("--run-id", default=None, help="Optional run_id like 1h:1773572400000")
    parser.add_argument("--ledger-json", default="artifacts/paper_execution/bithumb_paper_ledger.json")
    parser.add_argument("--output-dir", default="artifacts/paper_execution")
    parser.add_argument("--exit-json", default=None, help="Optional exit snapshot JSON path")
    parser.add_argument(
        "--execution-contract-screen-json",
        default=None,
        help="Optional execution contract screen JSON path for nightly/contract alignment checks",
    )
    parser.add_argument("--notional-krw", type=float, default=100000.0)
    parser.add_argument("--max-orders", type=int, default=1)
    parser.add_argument("--track", choices=["operating", "attack"], default="operating")
    parser.add_argument("--access-key", required=True)
    parser.add_argument("--secret-key", required=True)
    parser.add_argument("--client-order-prefix", default="nightly")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    summary = run_nightly_paper(
        logs_dir=Path(args.logs_dir),
        run_id=args.run_id,
        ledger_json=Path(args.ledger_json),
        output_dir=Path(args.output_dir),
        exit_json=Path(args.exit_json) if args.exit_json else None,
        execution_contract_screen_json=(
            Path(args.execution_contract_screen_json)
            if args.execution_contract_screen_json
            else None
        ),
        notional_krw=float(args.notional_krw),
        max_orders=int(args.max_orders),
        strategy_track=str(args.track),
        access_key=str(args.access_key),
        secret_key=str(args.secret_key),
        client_order_prefix=str(args.client_order_prefix),
    )
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(_render_text_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
