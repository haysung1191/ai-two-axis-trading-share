from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_manual_snapshot import generate_manual_snapshot
from scripts.manual_today_briefing import build_manual_today_briefing, render_text_today_briefing
from src.config import load_config


def _bool_to_env(value: Any) -> str:
    return "1" if bool(value) else "0"


def prepare_manual_policy_env() -> dict[str, str]:
    cfg = load_config()
    policy_cfg = cfg.policy or {}
    defaults = {
        "TRACE_ENABLED": _bool_to_env(policy_cfg.get("trace_enabled", True)),
        "POLICY_SHADOW_ENABLED": _bool_to_env(policy_cfg.get("shadow_enabled", True)),
        "POLICY_ACTIVE": _bool_to_env(policy_cfg.get("active_enabled", True)),
        "POLICY_SOFT_REJECT_ENABLED": _bool_to_env(policy_cfg.get("soft_reject_enabled", False)),
        "POLICY_MAX_SCORE_DELTA": str(policy_cfg.get("max_score_delta", 0.05)),
    }
    applied: dict[str, str] = {}
    for key, value in defaults.items():
        applied[key] = os.environ.setdefault(key, value)
    return applied


def build_manual_check_payload(
    *,
    artifacts_dir: Path,
    reexport_dir: Path,
    logs_dir: Path,
    trace_count: int = 15,
    max_buy: int = 3,
    max_monitor: int = 5,
    max_checklist_items: int = 3,
    max_operator_baseline: int = 5,
    max_operator_policy_assisted: int = 5,
    max_operator_recheck: int = 5,
) -> dict[str, Any]:
    effective_policy_env = prepare_manual_policy_env()
    snapshot_path = generate_manual_snapshot(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        trace_count=max(1, trace_count),
    )
    snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    run_id = str(snapshot_payload.get("run_id", ""))
    briefing = build_manual_today_briefing(
        artifacts_dir=artifacts_dir,
        reexport_dir=reexport_dir,
        logs_dir=logs_dir,
        run_id=run_id or None,
        max_buy=max_buy,
        max_monitor=max_monitor,
        max_checklist_items=max_checklist_items,
        max_operator_baseline=max_operator_baseline,
        max_operator_policy_assisted=max_operator_policy_assisted,
        max_operator_recheck=max_operator_recheck,
    )
    return {
        "snapshot_path": str(snapshot_path),
        "run_id": run_id,
        "effective_policy_env": effective_policy_env,
        "briefing": briefing,
    }


def render_text_manual_check(payload: dict[str, Any]) -> str:
    lines = [
        f"snapshot_path: {payload.get('snapshot_path', '-')}",
        f"run_id: {payload.get('run_id', '-')}",
        "effective_policy_env:",
    ]
    for key, value in payload.get("effective_policy_env", {}).items():
        lines.append(f"- {key}={value}")
    lines.extend(["", render_text_today_briefing(payload["briefing"])])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a fresh manual snapshot and print the full briefing in one step.")
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--trace-count", type=int, default=15)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--max-buy", type=int, default=3)
    parser.add_argument("--max-monitor", type=int, default=5)
    parser.add_argument("--max-checklist-items", type=int, default=3)
    parser.add_argument("--max-operator-baseline", type=int, default=5)
    parser.add_argument("--max-operator-policy-assisted", type=int, default=5)
    parser.add_argument("--max-operator-recheck", type=int, default=5)
    args = parser.parse_args()

    payload = build_manual_check_payload(
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        logs_dir=Path(args.logs_dir),
        trace_count=max(1, args.trace_count),
        max_buy=max(1, args.max_buy),
        max_monitor=max(1, args.max_monitor),
        max_checklist_items=max(1, args.max_checklist_items),
        max_operator_baseline=max(1, args.max_operator_baseline),
        max_operator_policy_assisted=max(1, args.max_operator_policy_assisted),
        max_operator_recheck=max(1, args.max_operator_recheck),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text_manual_check(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
