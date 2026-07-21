from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from src.config import load_config
from src.db import apply_migrations, connect
from src.policy.runtime import load_policy_state, read_policy_flags


def _iso_utc_from_ms(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_check() -> dict:
    load_dotenv()
    cfg = load_config()
    flags = read_policy_flags()
    state = load_policy_state(flags)
    bundle_path = Path(os.getenv("POLICY_BUNDLE_PATH", "policy/current/policy_bundle.json"))
    manifest_path = Path(os.getenv("POLICY_MANIFEST_PATH", "policy/current/manifest.json"))

    conn = connect(cfg.db_path)
    try:
        apply_migrations(conn)
        trace_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='selection_trace'"
        ).fetchone() is not None
        trace_rows = 0
        latest_trace_ts = None
        if trace_exists:
            trace_rows = int(conn.execute("SELECT COUNT(*) AS n FROM selection_trace").fetchone()["n"])
            latest_trace = conn.execute("SELECT ts FROM selection_trace ORDER BY ts DESC LIMIT 1").fetchone()
            latest_trace_ts = str(latest_trace["ts"]) if latest_trace else None
        latest_completed_run = conn.execute(
            """
            SELECT run_id, candle_close_ts_ms, completed_at
            FROM runs
            WHERE status='COMPLETED'
            ORDER BY candle_close_ts_ms DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    warnings: list[str] = []
    if flags.active_enabled and not flags.trace_enabled:
        warnings.append("POLICY_ACTIVE is enabled while TRACE_ENABLED is disabled.")
    if state.status == "loaded" and not bundle_path.exists():
        warnings.append(f"Loaded policy bundle is missing on disk: {bundle_path}")
    if state.status == "loaded" and not manifest_path.exists():
        warnings.append(f"Loaded policy manifest is missing on disk: {manifest_path}")

    latest_completed_payload = None
    if latest_completed_run is not None:
        expected_trace_ts = _iso_utc_from_ms(int(latest_completed_run["candle_close_ts_ms"]))
        latest_completed_payload = {
            "run_id": str(latest_completed_run["run_id"]),
            "candle_close_utc": expected_trace_ts,
            "completed_at": latest_completed_run["completed_at"],
        }
        if state.status == "loaded" and flags.trace_enabled and (latest_trace_ts is None or latest_trace_ts < expected_trace_ts):
            warnings.append(
                "Policy bundle is loaded but selection_trace has not caught up to the latest completed run."
            )

    return {
        "db_path": str(Path(cfg.db_path)),
        "trace_table_exists": trace_exists,
        "trace_rows": trace_rows,
        "latest_trace_ts": latest_trace_ts,
        "latest_completed_run": latest_completed_payload,
        "policy_flags": {
            "trace_enabled": flags.trace_enabled,
            "shadow_enabled": flags.shadow_enabled,
            "active_enabled": flags.active_enabled,
            "soft_reject_enabled": flags.soft_reject_enabled,
            "symbol_allowlist": list(flags.symbol_allowlist),
            "max_score_delta": flags.max_score_delta,
        },
        "policy_paths": {
            "bundle_path": str(bundle_path),
            "bundle_exists": bundle_path.exists(),
            "manifest_path": str(manifest_path),
            "manifest_exists": manifest_path.exists(),
        },
        "policy_bundle": {
            "status": state.status,
            "bundle_id": state.bundle.bundle_id if state.bundle else None,
            "error": state.error,
        },
        "warnings": warnings,
    }


def main() -> int:
    print(json.dumps(run_check(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
