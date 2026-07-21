from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "ops" / "dashboard"
HTML_PATH = OUT_DIR / "pipeline_dashboard_simple.html"
SUMMARY_PATH = OUT_DIR / "pipeline_dashboard_simple_latest.json"

BITHUMB_STATUS = ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_latest.json"
BITHUMB_LOOP_PID = ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_loop.pid"
BITHUMB_ORCA_STATE = ROOT / "Crypto" / "logs" / "bithumb_live_orca_portfolio_state.json"
BITHUMB_ORCA_EVENT = ROOT / "Crypto" / "logs" / "bithumb_axis_portfolio_events" / "orca_event_latest.json"
BITHUMB_ACCOUNT_SNAPSHOT = ROOT / "ops" / "account_engine" / "bithumb_krw" / "account_snapshot_latest.json"
BITHUMB_TARGET_DIFF = ROOT / "ops" / "account_engine" / "bithumb_krw" / "target_diff_latest.json"
BITHUMB_RECONCILIATION = ROOT / "ops" / "account_engine" / "bithumb_krw" / "reconciliation_latest.json"

KIS_STATUS = ROOT / "ops" / "stock_etf_axis_operation" / "stock_etf_axis_operation_latest.json"
KIS_SUBMIT = ROOT / "ops" / "stock_etf_axis_operation" / "kis_stock_etf_order_submit_latest.json"
KIS_LEDGER = ROOT / "ops" / "stock_etf_axis_operation" / "kis_stock_etf_order_ledger.jsonl"
KIS_ORDER_INTENT_CSV = ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_order_intent_latest.csv"
KIS_PLAN_PID = ROOT / "ops" / "stock_etf_axis_operation" / "stock_etf_axis_plan_loop.pid"
KIS_LOOP_PID = ROOT / "ops" / "stock_etf_axis_operation" / "stock_etf_axis_operation_loop.pid"
KIS_REBALANCE_STATUS = ROOT / "ops" / "kis_position_rebalance" / "kis_position_rebalance_latest.json"
KIS_REBALANCE_PID = ROOT / "ops" / "kis_position_rebalance" / "kis_position_rebalance_loop.pid"
KIS_ACCOUNT_SNAPSHOT = ROOT / "ops" / "account_engine" / "kis_combined_krw" / "account_snapshot_latest.json"
KIS_TARGET_DIFF = ROOT / "ops" / "account_engine" / "kis_combined_krw" / "target_diff_latest.json"
KIS_RECONCILIATION = ROOT / "ops" / "account_engine" / "kis_combined_krw" / "reconciliation_latest.json"
KIS_BRIDGE_STATUS = ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_candidate_bridge_latest.json"

MODEL_FACTORY_STATUS = ROOT / "ops" / "model_factory_loop" / "two_axis_model_factory_loop_latest.json"
MODEL_FACTORY_RUNNING = ROOT / "ops" / "model_factory_loop" / "two_axis_model_factory_loop_running.json"
MODEL_FACTORY_PID = ROOT / "ops" / "model_factory_loop" / "two_axis_model_factory_loop.pid"
DIRECT_DEVELOPMENT_STATUS = ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json"
BITHUMB_OOS_STATUS = ROOT / "reports" / "model_factory" / "bithumb_current_actionable_oos_walkforward_latest.json"
BITHUMB_ROBUSTNESS_STATUS = ROOT / "reports" / "model_factory" / "bithumb_current_actionable_robustness_stress_latest.json"
MODEL_INVENTORY_STATUS = ROOT / "reports" / "operations" / "two_axis_model_inventory_latest.json"
DASHBOARD_PID = ROOT / "ops" / "dashboard" / "pipeline_dashboard_loop.pid"

LOOP_PATTERNS = {
    "model_factory": "run_two_axis_model_factory_loop.py",
    "bithumb": "run_bithumb_axis_autotrade_loop.py",
    "kis_plan": "run_kis_daily_trade_window_loop.ps1 -Mode plan",
    "kis_buy": "run_kis_daily_trade_window_loop.ps1 -Mode buy",
    "kis_rebalance": "run_kis_daily_trade_window_loop.ps1 -Mode rebalance",
    "dashboard": "build_simple_pipeline_dashboard.py",
}
EXPECTED_MODEL_FACTORY_SCHEMA_VERSION = 2
EXPECTED_MODEL_FACTORY_STEP_LABELS = [
    "bithumb parameter sweep",
    "bithumb oos verification",
    "bithumb robustness stress",
    "bithumb nonzero signal scout",
    "stock split model pipeline",
    "stock operational conversion",
    "stock operating candidate bridge",
    "two axis direct model development",
    "two axis inventory",
    "dashboard refresh",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def file_mtime_utc(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return {}
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def read_pid(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def pid_running(pid: str) -> bool:
    if not pid:
        return False
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ '1' }} else {{ '0' }}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == "1"


def process_creation_time_utc(pid: str) -> str:
    if not pid or not pid.isdigit():
        return ""
    command = (
        "$p = Get-CimInstance Win32_Process -Filter "
        + json.dumps(f"ProcessId = {pid}")
        + "; if ($p) { $p.CreationDate.ToUniversalTime().ToString('o') }"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def find_process_by_pattern(pattern: str) -> dict[str, str | bool]:
    if not pattern:
        return {"pid": "", "running": False, "command_line": ""}
    command = (
        "$pattern = " + json.dumps(pattern) + "; "
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -match [regex]::Escape($pattern) } | "
        "Select-Object -First 1 ProcessId,CommandLine | ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    text = result.stdout.strip()
    if not text:
        return {"pid": "", "running": False, "command_line": ""}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"pid": "", "running": False, "command_line": ""}
    if isinstance(data, list):
        data = data[0] if data else {}
    pid = str(data.get("ProcessId", "") or "")
    return {
        "pid": pid,
        "running": bool(pid),
        "command_line": str(data.get("CommandLine", "") or ""),
    }


def loop_pid(path: Path, loop_name: str) -> dict[str, str | bool]:
    file_pid = read_pid(path)
    if pid_running(file_pid):
        return {"pid": file_pid, "running": True, "source": "pid_file"}
    detected = find_process_by_pattern(LOOP_PATTERNS.get(loop_name, ""))
    if detected.get("running"):
        return {"pid": detected.get("pid", ""), "running": True, "source": "process_scan"}
    return {"pid": file_pid, "running": False, "source": "not_found"}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def summarize_order_intent(rows: list[dict[str, str]]) -> dict[str, object]:
    submit_allowed_rows = [
        row for row in rows if str(row.get("SubmitAllowed", "")).strip().lower() in {"true", "1", "yes"}
    ]
    return {
        "row_count": len(rows),
        "submit_allowed_count": len(submit_allowed_rows),
        "submit_allowed_symbols": [str(row.get("Symbol", "")) for row in submit_allowed_rows if row.get("Symbol")],
    }


def order_intent_summary_from_bridge(bridge: dict, fallback_rows: list[dict[str, str]]) -> dict[str, object]:
    current_data = bridge.get("current_data") if isinstance(bridge.get("current_data"), dict) else {}
    if "order_intent_submit_allowed_count" in current_data or "order_intent_rows" in current_data:
        return {
            "row_count": int(current_data.get("order_intent_rows") or 0),
            "submit_allowed_count": int(current_data.get("order_intent_submit_allowed_count") or 0),
            "submit_allowed_symbols": list(current_data.get("order_intent_submit_allowed_symbols") or []),
            "source": "bridge_current_data",
        }
    summary = summarize_order_intent(fallback_rows)
    summary["source"] = "order_intent_csv"
    return summary


def kis_universe_validation_is_operational(mode: object) -> bool:
    normalized = str(mode or "").strip().lower()
    return normalized == "daily_close_presence"


def artifact_not_older_than(source_generated_at: object, dependent_generated_at: object) -> bool | None:
    source_dt = parse_utc_timestamp(str(source_generated_at) if source_generated_at else None)
    dependent_dt = parse_utc_timestamp(str(dependent_generated_at) if dependent_generated_at else None)
    if not source_dt or not dependent_dt:
        return None
    return dependent_dt >= source_dt


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def krw(value: object) -> str:
    try:
        return f"{float(value):,.0f} KRW"
    except (TypeError, ValueError):
        return "-"


def esc(value: object) -> str:
    return html.escape(str(value))


def truthy_flag(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def summarize_no_order_assertions(payload: dict) -> dict:
    assertions = payload.get("no_order_assertions")
    if not isinstance(assertions, dict):
        return {"present": False, "all_order_paths_false": False, "true_flags": []}
    true_flags = sorted(key for key, value in assertions.items() if truthy_flag(value))
    return {"present": True, "all_order_paths_false": not true_flags, "true_flags": true_flags}


def summarize_top_candidates(candidates: object, limit: int = 5) -> list[dict]:
    if not isinstance(candidates, list):
        return []
    rows = []
    for candidate in candidates[:limit]:
        if not isinstance(candidate, dict):
            continue
        metrics = candidate.get("metrics") or {}
        holdout = candidate.get("holdout_validation") or {}
        holdout_metrics = holdout.get("holdout") or {}
        archive_signal = candidate.get("current_signal") or {}
        archive_gap = candidate.get("current_signal_gap") or {}
        live_signal = candidate.get("live_current_signal") or {}
        live_gap = candidate.get("live_current_signal_gap") or {}
        live_data = candidate.get("live_current_signal_data") or {}
        rows.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "parent_candidate_id": candidate.get("parent_candidate_id"),
                "market": candidate.get("market"),
                "symbol": candidate.get("symbol"),
                "status": candidate.get("status"),
                "fixed_exposure_cap": candidate.get("fixed_exposure_cap"),
                "cagr": metrics.get("cagr") or candidate.get("estimated_cagr"),
                "mdd": metrics.get("mdd") or candidate.get("estimated_mdd"),
                "sharpe": metrics.get("sharpe") or candidate.get("source_sharpe"),
                "profit_factor": metrics.get("profit_factor"),
                "trade_count": metrics.get("trade_count"),
                "holdout_cagr": holdout_metrics.get("cagr"),
                "archive_signal_triggered": archive_signal.get("triggered"),
                "archive_signal_nearest_gap": archive_gap.get("nearest_trigger_gap"),
                "live_signal_triggered": live_signal.get("triggered"),
                "live_signal_nearest_gap": live_gap.get("nearest_trigger_gap"),
                "live_signal_data_status": live_data.get("status"),
                "live_signal_latest_timestamp": live_data.get("latest_timestamp"),
                "order_paths_allowed": truthy_flag(candidate.get("order_paths_allowed", False)),
                "counts_as_live_evidence": truthy_flag(candidate.get("counts_as_live_evidence", False)),
            }
        )
    return rows


def build_model_factory_runtime_freshness(loop_state: dict[str, dict]) -> dict:
    model_factory = loop_state.get("model_factory") or {}
    pid = str(model_factory.get("pid") or "")
    source_path = ROOT / "run_two_axis_model_factory_loop.py"
    latest_path = MODEL_FACTORY_STATUS
    source_mtime = file_mtime_utc(source_path)
    latest_mtime = file_mtime_utc(latest_path)
    process_created_at = process_creation_time_utc(pid)
    source_dt = parse_utc_timestamp(source_mtime)
    latest_dt = parse_utc_timestamp(latest_mtime)
    process_dt = parse_utc_timestamp(process_created_at)
    return {
        "pid": pid,
        "source_path": str(source_path),
        "source_mtime_utc": source_mtime,
        "latest_json_path": str(latest_path),
        "latest_json_mtime_utc": latest_mtime,
        "process_created_at_utc": process_created_at,
        "process_predates_source": bool(source_dt and process_dt and process_dt < source_dt),
        "latest_json_not_older_than_source": bool(source_dt and latest_dt and latest_dt >= source_dt),
    }


def build_model_factory_cadence(model_factory_running: dict, now_utc: str | None = None) -> dict:
    status = model_factory_running.get("status")
    generated_at = model_factory_running.get("generated_at_utc")
    started_at = model_factory_running.get("cycle_started_at_utc")
    due_at = model_factory_running.get("next_cycle_due_at_utc")
    generated_dt = parse_utc_timestamp(str(generated_at) if generated_at else None)
    started_dt = parse_utc_timestamp(str(started_at) if started_at else None)
    due_dt = parse_utc_timestamp(str(due_at) if due_at else None)
    now_dt = parse_utc_timestamp(now_utc or utc_now())
    seconds_overdue = 0
    if due_dt and now_dt and now_dt > due_dt and status != "TWO_AXIS_MODEL_FACTORY_RUNNING":
        seconds_overdue = int((now_dt - due_dt).total_seconds())
    elapsed_seconds = None
    if started_dt:
        end_dt = now_dt if status == "TWO_AXIS_MODEL_FACTORY_RUNNING" else generated_dt
        if end_dt and end_dt >= started_dt:
            elapsed_seconds = int((end_dt - started_dt).total_seconds())
    return {
        "status": status,
        "generated_at_utc": generated_at,
        "cycle_started_at_utc": started_at,
        "elapsed_seconds": elapsed_seconds,
        "current_step": model_factory_running.get("current_step"),
        "step_index": model_factory_running.get("step_index"),
        "step_count": model_factory_running.get("step_count"),
        "completed_step_count": model_factory_running.get("completed_step_count"),
        "planned_step_count": model_factory_running.get("planned_step_count") or model_factory_running.get("step_count"),
        "next_cycle_due_at_utc": due_at,
        "seconds_overdue": seconds_overdue,
        "overdue": seconds_overdue > 0,
    }


def build_model_factory_artifact_schema(
    model_factory: dict,
    direct_development: dict,
    bithumb_oos: dict | None = None,
    bithumb_robustness: dict | None = None,
    model_inventory: dict | None = None,
) -> dict[str, object]:
    direct_summary = ((model_factory.get("artifact_summary") or {}).get("direct_development") or {})
    bithumb_summary = ((model_factory.get("artifact_summary") or {}).get("bithumb") or {})
    kis_summary = ((model_factory.get("artifact_summary") or {}).get("kis") or {})
    direct_kis = direct_development.get("kis") or {}
    bithumb_oos = bithumb_oos or {}
    bithumb_robustness = bithumb_robustness or {}
    model_inventory = model_inventory or {}
    inventory_axes = model_inventory.get("axes") if isinstance(model_inventory.get("axes"), dict) else {}
    inventory_bithumb_sources = ((inventory_axes.get("BITHUMB_KRW") or {}).get("verification_sources") or {})
    inventory_kis_sources = ((inventory_axes.get("KIS_COMBINED_KRW") or {}).get("verification_sources") or {})
    expected_field_map = {
        "source_bridge": "kis_source_bridge",
        "universe_validation_mode": "kis_universe_validation_mode",
        "universe_validation_verifier_status": "kis_universe_validation_verifier_status",
        "universe_validation_operation_ready": "kis_universe_validation_operation_ready",
        "universe_validation_all_verified": "kis_universe_validation_all_verified",
        "universe_validation_operational": "kis_universe_validation_operational",
        "counts_as_live_evidence": "kis_counts_as_live_evidence",
    }
    direct_crypto = direct_development.get("crypto") or {}
    direct_crypto_expected_field_map = {
        "archive_signal_triggered_count": "crypto_archive_signal_triggered_count",
        "top_live_signal_triggered_count": "crypto_top_live_signal_triggered_count",
        "top_live_signal_summary": "crypto_top_live_signal_all_verified",
        "top_live_near_miss_candidate": "crypto_top_live_near_miss_candidate",
    }
    missing_fields = [
        summary_field
        for source_field, summary_field in expected_field_map.items()
        if source_field in direct_kis and summary_field not in direct_summary
    ]
    missing_fields.extend(
        summary_field
        for source_field, summary_field in direct_crypto_expected_field_map.items()
        if source_field in direct_crypto and summary_field not in direct_summary
    )
    bithumb_expected_field_map = {
        "oos_generated_at": bool(bithumb_oos.get("generated_at") or bithumb_oos.get("generated_at_utc")),
        "oos_top_candidate_id": bool((bithumb_oos.get("top_oos") or {}).get("candidate_id")),
        "oos_top_market": bool((bithumb_oos.get("top_oos") or {}).get("market")),
        "robustness_generated_at": bool(bithumb_robustness.get("generated_at") or bithumb_robustness.get("generated_at_utc")),
        "robustness_source_oos": bool(bithumb_robustness.get("source_oos")),
        "inventory_current_signal_generated_at_utc": bool(inventory_bithumb_sources.get("current_signal_generated_at_utc")),
        "inventory_current_signal_evaluated_count": "current_signal_evaluated_count" in inventory_bithumb_sources,
        "inventory_current_signal_triggered_count": "current_signal_triggered_count" in inventory_bithumb_sources,
        "inventory_current_signal_candidate_id": bool(inventory_bithumb_sources.get("current_signal_candidate_id")),
        "inventory_current_signal_matches_oos_top": "current_signal_matches_oos_top" in inventory_bithumb_sources,
        "inventory_oos_top_candidate_id": bool(inventory_bithumb_sources.get("oos_top_candidate_id")),
        "inventory_current_signal_selection_policy": bool(inventory_bithumb_sources.get("current_signal_selection_policy")),
        "inventory_current_signal_selection_summary": bool(inventory_bithumb_sources.get("current_signal_selection_summary")),
        "inventory_oos_top_signal_selection_summary": bool(inventory_bithumb_sources.get("oos_top_signal_selection_summary")),
        "inventory_current_signal_top_near_miss": bool(inventory_bithumb_sources.get("current_signal_top_near_miss")),
        "inventory_current_signal_top_near_miss_candidates": bool(
            inventory_bithumb_sources.get("current_signal_top_near_miss_candidates")
        ),
        "inventory_current_signal_oos_summary": bool(inventory_bithumb_sources.get("current_signal_oos_summary")),
        "inventory_oos_top_summary": bool(inventory_bithumb_sources.get("oos_top_summary")),
    }
    missing_bithumb_fields = [
        summary_field
        for summary_field, expected in bithumb_expected_field_map.items()
        if expected and summary_field not in bithumb_summary
    ]
    kis_inventory_expected_field_map = {
        "bridge_universe_validation_mode": bool(inventory_kis_sources.get("bridge_universe_validation_mode")),
        "bridge_universe_validation_verifier_status": bool(
            inventory_kis_sources.get("bridge_universe_validation_verifier_status")
        ),
        "direct_source_bridge": bool(inventory_kis_sources.get("direct_source_bridge")),
    }
    missing_kis_inventory_fields = [
        summary_field
        for summary_field, expected in kis_inventory_expected_field_map.items()
        if expected and summary_field not in kis_summary
    ]
    canonical_direct_missing_fields = [
        source_field
        for source_field in expected_field_map
        if direct_kis and source_field not in direct_kis
    ]
    canonical_direct_missing_fields.extend(
        source_field
        for source_field in direct_crypto_expected_field_map
        if direct_crypto and source_field not in direct_crypto
    )
    step_manifest = model_factory.get("step_manifest") if isinstance(model_factory.get("step_manifest"), list) else []
    step_manifest_labels = [
        row.get("label")
        for row in step_manifest
        if isinstance(row, dict)
    ]
    model_only_safety = model_factory.get("model_only_safety") if isinstance(model_factory.get("model_only_safety"), dict) else {}
    model_only_safety_present = bool(model_only_safety)
    model_only_safety_no_order_flags = model_only_safety.get("command_manifest_has_no_order_flags") is True
    model_only_safety_no_submit = (
        model_only_safety.get("order_submission_allowed_by_this_loop") is False
        and model_only_safety.get("broker_submit_allowed_by_this_loop") is False
        and model_only_safety.get("real_orders_allowed_by_this_loop") is False
    )
    stale_reasons = []
    if model_factory.get("schema_version") != EXPECTED_MODEL_FACTORY_SCHEMA_VERSION:
        stale_reasons.append("schema_version_missing_or_old")
    if step_manifest_labels != EXPECTED_MODEL_FACTORY_STEP_LABELS:
        stale_reasons.append("step_manifest_missing_or_mismatch")
    if not model_only_safety_present:
        stale_reasons.append("model_only_safety_missing")
    elif not model_only_safety_no_order_flags or not model_only_safety_no_submit:
        stale_reasons.append("model_only_safety_not_enforced")
    if missing_fields:
        stale_reasons.append("direct_development_summary_missing_fields")
    if missing_bithumb_fields:
        stale_reasons.append("bithumb_summary_missing_fields")
    if missing_kis_inventory_fields:
        stale_reasons.append("kis_inventory_summary_missing_fields")
    canonical_child_artifacts_complete = (
        not canonical_direct_missing_fields
        and any(bithumb_expected_field_map.values())
        and any(kis_inventory_expected_field_map.values())
    )
    if stale_reasons and canonical_child_artifacts_complete:
        stale_scope = "loop_summary_only"
    elif stale_reasons:
        stale_scope = "loop_summary_and_canonical_children"
    else:
        stale_scope = "none"
    return {
        "schema_version": model_factory.get("schema_version"),
        "expected_schema_version": EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
        "schema_version_current": model_factory.get("schema_version") == EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
        "step_manifest_labels": step_manifest_labels,
        "expected_step_labels": EXPECTED_MODEL_FACTORY_STEP_LABELS,
        "step_manifest_matches_expected": step_manifest_labels == EXPECTED_MODEL_FACTORY_STEP_LABELS,
        "model_only_safety_present": model_only_safety_present,
        "model_only_safety_no_order_flags": model_only_safety_no_order_flags,
        "model_only_safety_no_submit": model_only_safety_no_submit,
        "model_only_safety": model_only_safety,
        "stale_reasons": stale_reasons,
        "stale_scope": stale_scope,
        "direct_kis_validation_fields_expected": bool(direct_kis),
        "direct_kis_validation_fields_present": not missing_fields,
        "missing_direct_development_fields": missing_fields,
        "bithumb_source_fields_expected": any(bithumb_expected_field_map.values()),
        "bithumb_source_fields_present": not missing_bithumb_fields,
        "missing_bithumb_fields": missing_bithumb_fields,
        "kis_inventory_fields_expected": any(kis_inventory_expected_field_map.values()),
        "kis_inventory_fields_present": not missing_kis_inventory_fields,
        "missing_kis_inventory_fields": missing_kis_inventory_fields,
        "canonical_direct_development_fields_present": not canonical_direct_missing_fields,
        "canonical_missing_direct_development_fields": canonical_direct_missing_fields,
        "canonical_bithumb_sources_present": any(bithumb_expected_field_map.values()),
        "canonical_kis_inventory_sources_present": any(kis_inventory_expected_field_map.values()),
        "canonical_child_artifacts_complete": canonical_child_artifacts_complete,
    }


def build_model_factory_running_contract(model_factory_running: dict) -> dict[str, object]:
    step_manifest = (
        model_factory_running.get("step_manifest")
        if isinstance(model_factory_running.get("step_manifest"), list)
        else []
    )
    step_manifest_labels = [
        row.get("label")
        for row in step_manifest
        if isinstance(row, dict)
    ]
    model_only_safety = (
        model_factory_running.get("model_only_safety")
        if isinstance(model_factory_running.get("model_only_safety"), dict)
        else {}
    )
    model_only_safety_present = bool(model_only_safety)
    model_only_safety_no_order_flags = model_only_safety.get("command_manifest_has_no_order_flags") is True
    model_only_safety_no_submit = (
        model_only_safety.get("order_submission_allowed_by_this_loop") is False
        and model_only_safety.get("broker_submit_allowed_by_this_loop") is False
        and model_only_safety.get("real_orders_allowed_by_this_loop") is False
    )
    return {
        "schema_version": model_factory_running.get("schema_version"),
        "expected_schema_version": EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
        "schema_version_current": model_factory_running.get("schema_version") == EXPECTED_MODEL_FACTORY_SCHEMA_VERSION,
        "status": model_factory_running.get("status"),
        "current_step": model_factory_running.get("current_step"),
        "step_manifest_matches_expected": step_manifest_labels == EXPECTED_MODEL_FACTORY_STEP_LABELS,
        "model_only_safety_present": model_only_safety_present,
        "model_only_safety_no_order_flags": model_only_safety_no_order_flags,
        "model_only_safety_no_submit": model_only_safety_no_submit,
        "contract_current": (
            model_factory_running.get("schema_version") == EXPECTED_MODEL_FACTORY_SCHEMA_VERSION
            and step_manifest_labels == EXPECTED_MODEL_FACTORY_STEP_LABELS
            and model_only_safety_present
            and model_only_safety_no_order_flags
            and model_only_safety_no_submit
        ),
    }


def build_summary() -> dict:
    bithumb = load_json(BITHUMB_STATUS)
    kis = load_json(KIS_STATUS)
    kis_submit = load_json(KIS_SUBMIT)
    kis_ledger = load_jsonl(KIS_LEDGER)
    kis_rebalance = load_json(KIS_REBALANCE_STATUS)
    model_factory = load_json(MODEL_FACTORY_STATUS)
    model_factory_running = load_json(MODEL_FACTORY_RUNNING)
    direct_development = load_json(DIRECT_DEVELOPMENT_STATUS)
    bithumb_oos = load_json(BITHUMB_OOS_STATUS)
    bithumb_robustness = load_json(BITHUMB_ROBUSTNESS_STATUS)
    model_inventory = load_json(MODEL_INVENTORY_STATUS)
    orca_state = load_json(BITHUMB_ORCA_STATE)
    orca_event = load_json(BITHUMB_ORCA_EVENT)
    bithumb_account = load_json(BITHUMB_ACCOUNT_SNAPSHOT)
    bithumb_diff = load_json(BITHUMB_TARGET_DIFF)
    bithumb_reconciliation = load_json(BITHUMB_RECONCILIATION)
    kis_account = load_json(KIS_ACCOUNT_SNAPSHOT)
    kis_diff = load_json(KIS_TARGET_DIFF)
    kis_reconciliation = load_json(KIS_RECONCILIATION)
    standalone_bridge = load_json(KIS_BRIDGE_STATUS)

    bridge = standalone_bridge or kis.get("operating_candidate_bridge") or {}
    kis_order_intent_summary = order_intent_summary_from_bridge(bridge, load_csv_rows(KIS_ORDER_INTENT_CSV))
    kis_universe_operational = kis_universe_validation_is_operational(bridge.get("universe_validation_mode"))
    kis_counts = kis.get("counts") or {}
    kis_target = (bridge.get("target_book") or {})
    kis_tiny_live_repair = bridge.get("tiny_live_executable_repair") or {}
    kis_tiny_live_repair_oos = kis_tiny_live_repair.get("historical_oos_validation") or {}
    kis_direct_recommendation = bridge.get("direct_development_recommendation") or {}
    kis_execution_warnings = list(kis.get("execution_warnings") or bridge.get("execution_warnings") or [])
    bithumb_safety = bithumb.get("safety") or {}
    kis_order_path_flags = {
        "source_order_paths_allowed": truthy_flag(bridge.get("source_order_paths_allowed", False)),
        "repair_order_paths_allowed": truthy_flag(kis_tiny_live_repair.get("order_paths_allowed", False)),
        "repair_counts_as_live_evidence": truthy_flag(kis_tiny_live_repair.get("counts_as_live_evidence", False)),
        "repair_oos_order_paths_allowed": truthy_flag(kis_tiny_live_repair_oos.get("order_paths_allowed", False)),
        "repair_oos_counts_as_live_evidence": truthy_flag(kis_tiny_live_repair_oos.get("counts_as_live_evidence", False)),
    }
    kis_true_order_path_flags = sorted(key for key, value in kis_order_path_flags.items() if value)
    direct_guard = summarize_no_order_assertions(direct_development)
    oos_guard = summarize_no_order_assertions(bithumb_oos)
    robustness_guard = summarize_no_order_assertions(bithumb_robustness)
    kis_bridge_guard = summarize_no_order_assertions(bridge)
    all_known_order_paths_false = (
        direct_guard["all_order_paths_false"]
        and oos_guard["all_order_paths_false"]
        and robustness_guard["all_order_paths_false"]
        and kis_bridge_guard["all_order_paths_false"]
        and not kis_true_order_path_flags
    )
    model_only_attention = (
        not all_known_order_paths_false
        or int(kis_order_intent_summary["submit_allowed_count"] or 0) > 0
        or not kis_universe_operational
    )
    loop_state = {
        "model_factory": loop_pid(MODEL_FACTORY_PID, "model_factory"),
        "bithumb": loop_pid(BITHUMB_LOOP_PID, "bithumb"),
        "kis_plan": loop_pid(KIS_PLAN_PID, "kis_plan"),
        "kis_buy": loop_pid(KIS_LOOP_PID, "kis_buy"),
        "kis_rebalance": loop_pid(KIS_REBALANCE_PID, "kis_rebalance"),
        "dashboard": loop_pid(DASHBOARD_PID, "dashboard"),
    }
    model_factory_runtime = build_model_factory_runtime_freshness(loop_state)
    model_factory_cadence = build_model_factory_cadence(model_factory_running)
    model_factory_running_contract = build_model_factory_running_contract(model_factory_running)
    model_factory_artifact_schema = build_model_factory_artifact_schema(
        model_factory,
        direct_development,
        bithumb_oos,
        bithumb_robustness,
        model_inventory,
    )

    bithumb_ready = truthy_flag(bithumb.get("submit_enabled")) and not truthy_flag(bithumb.get("global_disable_present"))
    kis_ready = truthy_flag(kis.get("submit_enabled")) and not list(kis.get("blockers") or [])
    model_factory_summary_current = (
        model_factory.get("status") == "TWO_AXIS_MODEL_FACTORY_OK"
        and model_factory_artifact_schema["schema_version_current"]
        and model_factory_artifact_schema["step_manifest_matches_expected"]
        and model_factory_artifact_schema["model_only_safety_present"]
        and model_factory_artifact_schema["model_only_safety_no_order_flags"]
        and model_factory_artifact_schema["model_only_safety_no_submit"]
    )
    model_ready = model_factory_summary_current or int(kis_counts.get("model_factory_ready_experiments", 0) or 0) > 0
    direct_ready = direct_development.get("status") == "TWO_AXIS_DIRECT_DEVELOPMENT_OK"
    has_position_loop = bool(kis_rebalance) and bool(kis_submit)
    model_factory_loop_status = model_factory_running.get("status") or model_factory.get("status", "UNKNOWN")
    model_factory_loop_detail = (
        f"step={model_factory_running.get('step_index', '-')}/{model_factory_running.get('step_count', '-')}: {model_factory_running.get('current_step')}"
        if model_factory_loop_status == "TWO_AXIS_MODEL_FACTORY_RUNNING"
        else f"ok={model_factory.get('ok_count', '-')}, errors={model_factory.get('error_count', '-')}"
    )

    completion = {
        "model_development_loop": 0.95 if model_ready and direct_ready else (0.85 if direct_ready else 0.55),
        "model_verification_loop": (
            0.90
            if model_factory_summary_current and int(kis_counts.get("verified_registry_candidates_all_axes", 0) or 0)
            else (0.75 if model_factory_artifact_schema["canonical_child_artifacts_complete"] else 0.45)
        ),
        "promotion_to_live_loop": 0.90 if bithumb_ready and kis_ready else 0.65,
        "autotrade_position_loop": 0.80 if has_position_loop else 0.55,
        "performance_dashboard": 1.00,
    }

    realized_pnl = float(orca_event.get("cumulative_realized_pnl_krw") or 0.0)
    realized_return = float(orca_event.get("cumulative_realized_return_pct") or 0.0)
    kis_submitted_ledger = [row for row in kis_ledger if row.get("status") == "SUBMITTED"]
    kis_ledger_notional = sum(float(row.get("estimated_notional_krw") or 0.0) for row in kis_submitted_ledger)
    bithumb_oos_generated_at = bithumb_oos.get("generated_at") or bithumb_oos.get("generated_at_utc")
    bithumb_robustness_generated_at = bithumb_robustness.get("generated_at") or bithumb_robustness.get("generated_at_utc")
    inventory_bithumb_sources = (
        ((model_inventory.get("axes") or {}).get("BITHUMB_KRW") or {}).get("verification_sources") or {}
    )
    inventory_kis_sources = (
        ((model_inventory.get("axes") or {}).get("KIS_COMBINED_KRW") or {}).get("verification_sources") or {}
    )
    inventory_current_signal_oos = inventory_bithumb_sources.get("current_signal_oos_summary") or {}
    inventory_oos_top = inventory_bithumb_sources.get("oos_top_summary") or {}
    inventory_current_signal_selection = inventory_bithumb_sources.get("current_signal_selection_summary") or {}
    inventory_oos_top_signal_selection = inventory_bithumb_sources.get("oos_top_signal_selection_summary") or {}
    inventory_current_signal_near_miss = inventory_bithumb_sources.get("current_signal_top_near_miss") or {}
    inventory_current_signal_near_miss_candidates = (
        inventory_bithumb_sources.get("current_signal_top_near_miss_candidates") or []
    )
    inventory_direct_live_near_miss = inventory_bithumb_sources.get("direct_crypto_top_live_near_miss_candidate") or {}

    return {
        "generated_at_utc": utc_now(),
        "overall_completion": sum(completion.values()) / len(completion),
        "completion": completion,
        "loops": {
            "model_factory": {
                "status": model_factory_loop_status,
                "pid": loop_state["model_factory"]["pid"],
                "running": loop_state["model_factory"]["running"],
                "pid_source": loop_state["model_factory"]["source"],
                "detail": model_factory_loop_detail,
            },
            "direct_development": {
                "status": direct_development.get("status", "UNKNOWN"),
                "pid": loop_state["model_factory"]["pid"],
                "running": loop_state["model_factory"]["running"],
                "pid_source": loop_state["model_factory"]["source"],
                "detail": (
                    f"crypto_oos={(direct_development.get('crypto') or {}).get('oos_pass_count', '-')}, "
                    f"validated={(direct_development.get('crypto') or {}).get('validated_pass_count', '-')}, "
                    f"archive_sig={(direct_development.get('crypto') or {}).get('archive_signal_triggered_count', '-')}, "
                    f"live_sig={(direct_development.get('crypto') or {}).get('top_live_signal_triggered_count', '-')}, "
                    f"markets={(direct_development.get('crypto') or {}).get('validated_market_count', '-')}, "
                    f"kis_pass={(direct_development.get('kis') or {}).get('pass_count', '-')}"
                ),
            },
            "bithumb": {
                "status": bithumb.get("status", "UNKNOWN"),
                "pid": loop_state["bithumb"]["pid"],
                "running": loop_state["bithumb"]["running"],
                "pid_source": loop_state["bithumb"]["source"],
                "detail": f"scanned={bithumb.get('universe_scanned_count', 0)}, oos={bithumb.get('oos_candidate_count', 0)}",
            },
            "kis_buy": {
                "status": kis.get("status", "UNKNOWN"),
                "pid": loop_state["kis_buy"]["pid"],
                "running": loop_state["kis_buy"]["running"],
                "pid_source": loop_state["kis_buy"]["source"],
                "detail": f"submit={kis_submit.get('status', 'UNKNOWN')}",
            },
            "kis_plan": {
                "status": "RUNNING" if loop_state["kis_plan"]["running"] else "UNKNOWN",
                "pid": loop_state["kis_plan"]["pid"],
                "running": loop_state["kis_plan"]["running"],
                "pid_source": loop_state["kis_plan"]["source"],
                "detail": "daily close plan window=15:40 KST",
            },
            "kis_rebalance": {
                "status": kis_rebalance.get("status", "UNKNOWN"),
                "pid": loop_state["kis_rebalance"]["pid"],
                "running": loop_state["kis_rebalance"]["running"],
                "pid_source": loop_state["kis_rebalance"]["source"],
                "detail": f"orders={kis_rebalance.get('order_count', 0)}, submitted={kis_rebalance.get('submitted_count', 0)}",
            },
            "dashboard": {
                "status": "RUNNING" if loop_state["dashboard"]["running"] else "UNKNOWN",
                "pid": loop_state["dashboard"]["pid"],
                "running": loop_state["dashboard"]["running"],
                "pid_source": loop_state["dashboard"]["source"],
                "detail": "refresh=60s",
            },
        },
        "trading": {
            "bithumb": {
                "status": bithumb.get("status", "UNKNOWN"),
                "markets": bithumb.get("oos_markets", []),
                "open_positions": list((bithumb.get("current_open_positions") or {}).keys()),
                "exposure_krw": bithumb.get("current_exposure_krw_estimate", 0),
                "cap_krw": bithumb_safety.get("max_total_krw"),
                "base_cap_krw": bithumb_safety.get("base_cap_krw"),
                "effective_cap_krw": bithumb_safety.get("effective_cap_krw", bithumb_safety.get("max_total_krw")),
                "cap_ratchet": bithumb_safety.get("cap_ratchet", {}),
                "realized_pnl_krw": realized_pnl,
                "realized_return_pct": realized_return,
                "last_reason": (orca_state.get("last_decision") or {}).get("reason") or orca_event.get("last_reason"),
                "position_status": orca_state.get("status") or "NONE",
            },
            "kis": {
                "status": kis.get("status", "UNKNOWN"),
                "order_submit_status": kis_submit.get("status", "UNKNOWN"),
                "symbols": kis_target.get("symbols", []),
                "gross_target_weight": kis_target.get("gross_target_weight", 0),
                "cash_weight": kis_target.get("cash_weight", 0),
                "tiny_live_buyable_symbol_count": kis_target.get("tiny_live_buyable_symbol_count", 0),
                "tiny_live_unbuyable_symbols": kis_target.get("tiny_live_unbuyable_symbols", []),
                "estimated_buyable_notional_krw": kis_target.get("estimated_buyable_notional_krw", 0),
                "execution_warnings": kis_execution_warnings,
                "tiny_live_repair_status": kis_tiny_live_repair.get("status"),
                "tiny_live_repair_symbols": kis_tiny_live_repair.get("candidate_symbols", []),
                "tiny_live_repair_buyable_count": kis_tiny_live_repair.get("buyable_count", 0),
                "tiny_live_repair_oos_status": kis_tiny_live_repair_oos.get("status"),
                "tiny_live_repair_oos_cagr": (kis_tiny_live_repair_oos.get("summary") or {}).get("CAGR"),
                "tiny_live_repair_oos_mdd": (kis_tiny_live_repair_oos.get("summary") or {}).get("MDD"),
                "tiny_live_repair_oos_holdout_cagr": (kis_tiny_live_repair_oos.get("holdout_30pct") or {}).get("CAGR"),
                "tiny_live_repair_active_month_coverage": kis_tiny_live_repair_oos.get("active_month_coverage"),
                "submitted_count": kis_submit.get("submitted_count", 0),
                "base_cap_krw": ((kis_submit.get("safety") or {}).get("base_cap_krw")),
                "effective_cap_krw": ((kis_submit.get("safety") or {}).get("effective_cap_krw")),
                "cap_ratchet": ((kis_submit.get("safety") or {}).get("cap_ratchet", {})),
                "ledger_submitted_count": len(kis_submitted_ledger),
                "ledger_submitted_notional_krw": kis_ledger_notional,
                "rebalance_status": kis_rebalance.get("status", "UNKNOWN"),
                "direct_recommended_parent": kis_direct_recommendation.get("parent_candidate_id"),
                "direct_recommended_cap": kis_direct_recommendation.get("fixed_exposure_cap"),
            },
        },
        "account_engine": {
            "bithumb": {
                "snapshot_source": bithumb_account.get("source"),
                "position_count": bithumb_account.get("position_count", 0),
                "cash_krw": bithumb_account.get("cash_krw"),
                "actionable_count": bithumb_diff.get("actionable_count", 0),
                "unresolved_order_count": bithumb_reconciliation.get("unresolved_order_count", 0),
            },
            "kis": {
                "snapshot_source": kis_account.get("source"),
                "position_count": kis_account.get("position_count", 0),
                "cash_krw": kis_account.get("cash_krw"),
                "actionable_count": kis_diff.get("actionable_count", 0),
                "unresolved_order_count": kis_reconciliation.get("unresolved_order_count", 0),
            },
        },
        "model_only_guardrails": {
            "source_generated_at_utc": {
                "direct_development": direct_development.get("generated_at_utc"),
                "bithumb_oos": bithumb_oos.get("generated_at") or bithumb_oos.get("generated_at_utc"),
                "bithumb_robustness": bithumb_robustness.get("generated_at") or bithumb_robustness.get("generated_at_utc"),
                "kis_bridge": bridge.get("generated_at_utc"),
            },
            "direct_development": direct_guard,
            "bithumb_oos": oos_guard,
            "bithumb_robustness": robustness_guard,
            "kis_bridge": kis_bridge_guard,
            "kis_order_path_flags": kis_order_path_flags,
            "kis_all_order_paths_false": not kis_true_order_path_flags,
            "kis_true_order_path_flags": kis_true_order_path_flags,
            "kis_order_intent_submit_allowed_count": kis_order_intent_summary["submit_allowed_count"],
            "kis_order_intent_summary_source": kis_order_intent_summary["source"],
            "kis_universe_validation_operational": kis_universe_operational,
            "all_known_order_paths_false": all_known_order_paths_false,
            "model_only_attention": model_only_attention,
        },
        "model_factory_runtime": model_factory_runtime,
        "model_factory_cadence": model_factory_cadence,
        "model_factory_running_contract": model_factory_running_contract,
        "model_factory_artifact_schema": model_factory_artifact_schema,
        "performance": {
            "direct_development": {
                "crypto_candidates": (direct_development.get("crypto") or {}).get("candidate_count", 0),
                "crypto_oos_pass": (direct_development.get("crypto") or {}).get("oos_pass_count", 0),
                "crypto_validated_pass": (direct_development.get("crypto") or {}).get("validated_pass_count", 0),
                "crypto_validated_market_count": (direct_development.get("crypto") or {}).get("validated_market_count", 0),
                "crypto_validated_markets": (direct_development.get("crypto") or {}).get("validated_markets", []),
                "crypto_archive_signal_triggered_count": (direct_development.get("crypto") or {}).get("archive_signal_triggered_count", 0),
                "crypto_top_live_signal_triggered_count": (direct_development.get("crypto") or {}).get("top_live_signal_triggered_count", 0),
                "crypto_top_live_signal_all_verified": ((direct_development.get("crypto") or {}).get("top_live_signal_summary") or {}).get("all_live_verified"),
                "crypto_top_live_signal_data_source_by_market": ((direct_development.get("crypto") or {}).get("top_live_signal_summary") or {}).get("data_source_by_market", {}),
                "crypto_top_live_near_miss_candidate": (direct_development.get("crypto") or {}).get("top_live_near_miss_candidate"),
                "kis_variants": (direct_development.get("kis") or {}).get("conversion_variant_count", 0),
                "kis_pass": (direct_development.get("kis") or {}).get("pass_count", 0),
                "kis_universe_validation_mode": (direct_development.get("kis") or {}).get("universe_validation_mode"),
                "kis_universe_validation_verifier_status": (direct_development.get("kis") or {}).get("universe_validation_verifier_status"),
                "kis_universe_validation_operation_ready": truthy_flag((direct_development.get("kis") or {}).get("universe_validation_operation_ready", False)),
                "kis_universe_validation_all_verified": truthy_flag((direct_development.get("kis") or {}).get("universe_validation_all_verified", False)),
                "kis_universe_validation_operational": (direct_development.get("kis") or {}).get("universe_validation_operational"),
                "kis_counts_as_live_evidence": truthy_flag((direct_development.get("kis") or {}).get("counts_as_live_evidence", False)),
                "top_crypto": summarize_top_candidates((direct_development.get("crypto") or {}).get("top_candidates"), 5),
                "top_kis": summarize_top_candidates((direct_development.get("kis") or {}).get("top_variants"), 5),
            },
            "kis_backtest": {
                "before_cagr": (bridge.get("before") or {}).get("cagr"),
                "before_mdd": (bridge.get("before") or {}).get("mdd"),
                "before_sharpe": (bridge.get("before") or {}).get("sharpe"),
                "estimated_cagr": (bridge.get("proposed_conversion") or {}).get("estimated_cagr"),
                "estimated_mdd": (bridge.get("proposed_conversion") or {}).get("estimated_mdd"),
            },
            "kis_verification": {
                "bridge_status": bridge.get("status"),
                "bridge_generated_at_utc": bridge.get("generated_at_utc"),
                "candidate_id": bridge.get("candidate_id"),
                "direct_top_parent_candidate_id": (((direct_development.get("kis") or {}).get("top_variants") or [{}])[0]).get("parent_candidate_id"),
                "universe_validation_mode": bridge.get("universe_validation_mode"),
                "universe_validation_verifier_status": bridge.get("universe_validation_verifier_status"),
                "universe_validation_operation_ready": truthy_flag(bridge.get("universe_validation_operation_ready", False)),
                "universe_validation_all_verified": truthy_flag(bridge.get("universe_validation_all_verified", False)),
                "universe_validation_blockers": bridge.get("universe_validation_blockers", []),
                "target_symbol_count": len(kis_target.get("symbols") or []),
                "tiny_live_buyable_symbol_count": kis_target.get("tiny_live_buyable_symbol_count", 0),
                "repair_status": kis_tiny_live_repair.get("status"),
                "repair_order_paths_allowed": truthy_flag(kis_tiny_live_repair.get("order_paths_allowed", False)),
                "repair_counts_as_live_evidence": truthy_flag(kis_tiny_live_repair.get("counts_as_live_evidence", False)),
                "repair_buyable_count": kis_tiny_live_repair.get("buyable_count", 0),
                "repair_quality_status": (kis_tiny_live_repair.get("quality") or {}).get("status"),
                "repair_oos_status": kis_tiny_live_repair_oos.get("status"),
                "repair_oos_order_paths_allowed": truthy_flag(kis_tiny_live_repair_oos.get("order_paths_allowed", False)),
                "repair_oos_counts_as_live_evidence": truthy_flag(kis_tiny_live_repair_oos.get("counts_as_live_evidence", False)),
                "repair_oos_months": kis_tiny_live_repair_oos.get("months"),
                "repair_oos_cagr": (kis_tiny_live_repair_oos.get("summary") or {}).get("CAGR"),
                "repair_oos_mdd": (kis_tiny_live_repair_oos.get("summary") or {}).get("MDD"),
                "repair_oos_sharpe": (kis_tiny_live_repair_oos.get("summary") or {}).get("Sharpe"),
                "repair_oos_holdout_cagr": (kis_tiny_live_repair_oos.get("holdout_30pct") or {}).get("CAGR"),
                "repair_oos_cost_cagr": (kis_tiny_live_repair_oos.get("cost_stress_25bps") or {}).get("CAGR"),
                "repair_oos_pass_folds": (kis_tiny_live_repair_oos.get("walkforward") or {}).get("pass_folds"),
                "repair_oos_folds": (kis_tiny_live_repair_oos.get("walkforward") or {}).get("folds"),
                "order_intent_row_count": kis_order_intent_summary["row_count"],
                "order_intent_submit_allowed_count": kis_order_intent_summary["submit_allowed_count"],
                "order_intent_submit_allowed_symbols": kis_order_intent_summary["submit_allowed_symbols"],
                "order_intent_summary_source": kis_order_intent_summary["source"],
                "universe_validation_operational": kis_universe_operational,
                "direct_bridge_universe_validation_match": (
                    (direct_development.get("kis") or {}).get("universe_validation_mode") == bridge.get("universe_validation_mode")
                    if (direct_development.get("kis") or {}).get("universe_validation_mode") and bridge.get("universe_validation_mode")
                    else None
                ),
                "direct_not_older_than_bridge": artifact_not_older_than(
                    bridge.get("generated_at_utc"),
                    direct_development.get("generated_at_utc"),
                ),
                "direct_source_bridge_matches_current": (
                    ((direct_development.get("kis") or {}).get("source_bridge") or {}).get("generated_at_utc") == bridge.get("generated_at_utc")
                    and ((direct_development.get("kis") or {}).get("source_bridge") or {}).get("candidate_id") == bridge.get("candidate_id")
                    and ((direct_development.get("kis") or {}).get("source_bridge") or {}).get("universe_validation_mode") == bridge.get("universe_validation_mode")
                    if ((direct_development.get("kis") or {}).get("source_bridge") or {}).get("generated_at_utc")
                    and bridge.get("generated_at_utc")
                    and ((direct_development.get("kis") or {}).get("source_bridge") or {}).get("candidate_id")
                    and bridge.get("candidate_id")
                    and ((direct_development.get("kis") or {}).get("source_bridge") or {}).get("universe_validation_mode")
                    and bridge.get("universe_validation_mode")
                    else None
                ),
                "bridge_matches_direct_top_parent": (
                    bridge.get("candidate_id") == (((direct_development.get("kis") or {}).get("top_variants") or [{}])[0]).get("parent_candidate_id")
                    if bridge.get("candidate_id")
                    and (((direct_development.get("kis") or {}).get("top_variants") or [{}])[0]).get("parent_candidate_id")
                    else None
                ),
            },
            "bithumb_verification": {
                "oos_status": bithumb_oos.get("status"),
                "oos_generated_at": bithumb_oos_generated_at,
                "oos_candidate_count": (bithumb_oos.get("aggregate") or {}).get("candidate_count")
                or bithumb_oos.get("candidate_count"),
                "oos_evaluated_count": (bithumb_oos.get("aggregate") or {}).get("evaluated_count"),
                "oos_pass_count": (bithumb_oos.get("aggregate") or {}).get("pass_count"),
                "oos_top_candidate_id": (bithumb_oos.get("top_oos") or {}).get("candidate_id"),
                "oos_top_market": (bithumb_oos.get("top_oos") or {}).get("market"),
                "inventory_current_signal_generated_at": inventory_bithumb_sources.get("current_signal_generated_at"),
                "inventory_current_signal_generated_at_utc": inventory_bithumb_sources.get("current_signal_generated_at_utc"),
                "inventory_current_signal_evaluated_count": inventory_bithumb_sources.get("current_signal_evaluated_count"),
                "inventory_current_signal_triggered_count": inventory_bithumb_sources.get("current_signal_triggered_count"),
                "inventory_current_signal_candidate_id": inventory_bithumb_sources.get("current_signal_candidate_id"),
                "inventory_current_signal_matches_oos_top": inventory_bithumb_sources.get("current_signal_matches_oos_top"),
                "inventory_oos_top_candidate_id": inventory_bithumb_sources.get("oos_top_candidate_id"),
                "inventory_current_signal_selection_policy": inventory_bithumb_sources.get("current_signal_selection_policy"),
                "inventory_current_signal_selection_rank": inventory_current_signal_selection.get("selection_rank"),
                "inventory_oos_top_signal_selection_rank": inventory_oos_top_signal_selection.get("selection_rank"),
                "inventory_current_signal_selection_estimated_cagr": inventory_current_signal_selection.get("estimated_cagr"),
                "inventory_oos_top_signal_selection_estimated_cagr": inventory_oos_top_signal_selection.get("estimated_cagr"),
                "inventory_current_signal_near_miss_candidate_id": inventory_current_signal_near_miss.get("candidate_id"),
                "inventory_current_signal_near_miss_momentum_gap": inventory_current_signal_near_miss.get("momentum_gap"),
                "inventory_current_signal_near_miss_volume_gap": inventory_current_signal_near_miss.get("volume_gap"),
                "inventory_current_signal_near_miss_blocking_conditions": inventory_current_signal_near_miss.get("blocking_conditions", []),
                "inventory_current_signal_near_miss_candidates": inventory_current_signal_near_miss_candidates,
                "inventory_direct_top_live_near_miss_candidate_id": inventory_direct_live_near_miss.get("candidate_id"),
                "inventory_direct_top_live_near_miss_market": inventory_direct_live_near_miss.get("market"),
                "inventory_direct_top_live_near_miss_momentum_gap": inventory_direct_live_near_miss.get("momentum_gap"),
                "inventory_direct_top_live_near_miss_volume_gap": inventory_direct_live_near_miss.get("volume_gap"),
                "inventory_direct_top_live_near_miss_blocking_conditions": inventory_direct_live_near_miss.get("blocking_conditions", []),
                "inventory_current_signal_oos_average_fold_cagr": inventory_current_signal_oos.get("average_fold_cagr"),
                "inventory_oos_top_average_fold_cagr": inventory_oos_top.get("average_fold_cagr"),
                "inventory_current_signal_oos_trade_count": inventory_current_signal_oos.get("total_trade_count"),
                "inventory_oos_top_trade_count": inventory_oos_top.get("total_trade_count"),
                "oos_order_paths_allowed": truthy_flag(bithumb_oos.get("order_paths_allowed", False)),
                "robustness_status": bithumb_robustness.get("status"),
                "robustness_generated_at": bithumb_robustness_generated_at,
                "robustness_candidate_id": bithumb_robustness.get("candidate_id"),
                "robustness_pass_count": bithumb_robustness.get("pass_count"),
                "robustness_cost_pass_count": bithumb_robustness.get("cost_pass_count"),
                "robustness_case_count": bithumb_robustness.get("case_count"),
                "robustness_order_paths_allowed": truthy_flag(bithumb_robustness.get("order_paths_allowed", False)),
                "robustness_matches_oos_top": (
                    (bithumb_oos.get("top_oos") or {}).get("candidate_id") == bithumb_robustness.get("candidate_id")
                    if (bithumb_oos.get("top_oos") or {}).get("candidate_id") and bithumb_robustness.get("candidate_id")
                    else None
                ),
                "robustness_source_oos_matches_current": (
                    (bithumb_robustness.get("source_oos") or {}).get("top_candidate_id") == (bithumb_oos.get("top_oos") or {}).get("candidate_id")
                    and (bithumb_robustness.get("source_oos") or {}).get("generated_at") == bithumb_oos_generated_at
                    if (bithumb_robustness.get("source_oos") or {}).get("top_candidate_id")
                    and (bithumb_oos.get("top_oos") or {}).get("candidate_id")
                    and (bithumb_robustness.get("source_oos") or {}).get("generated_at")
                    and bithumb_oos_generated_at
                    else None
                ),
                "robustness_not_older_than_oos": artifact_not_older_than(
                    bithumb_oos_generated_at,
                    bithumb_robustness_generated_at,
                ),
            },
        },
    }


def card(title: str, value: str, sub: str = "") -> str:
    return f"""
    <section class="card">
      <div class="label">{esc(title)}</div>
      <div class="value">{esc(value)}</div>
      <div class="sub">{esc(sub)}</div>
    </section>
    """


def render_html(summary: dict) -> str:
    completion = summary["completion"]
    loops = summary["loops"]
    trading = summary["trading"]
    account_engine = summary.get("account_engine", {})
    guardrails = summary.get("model_only_guardrails", {})
    model_factory_runtime = summary.get("model_factory_runtime", {})
    model_factory_cadence = summary.get("model_factory_cadence", {})
    model_factory_running_contract = summary.get("model_factory_running_contract", {})
    model_factory_artifact_schema = summary.get("model_factory_artifact_schema", {})
    direct_dev = summary["performance"]["direct_development"]
    kis_bt = summary["performance"]["kis_backtest"]
    kis_verification = summary["performance"].get("kis_verification", {})
    bithumb_verification = summary["performance"].get("bithumb_verification", {})
    kis_order_intent_submit_allowed_count = int(kis_verification.get("order_intent_submit_allowed_count") or 0)
    model_only_attention = (
        (not bool(guardrails.get("all_known_order_paths_false")))
        or kis_order_intent_submit_allowed_count > 0
        or not bool(guardrails.get("kis_universe_validation_operational"))
    )

    progress_rows = [
        ("Model dev loop", completion["model_development_loop"], loops["direct_development"]["detail"]),
        ("Verification loop", completion["model_verification_loop"], f"verified={loops['model_factory']['status']}"),
        ("Live promotion loop", completion["promotion_to_live_loop"], "Bithumb live + KIS ready"),
        ("Position loop", completion["autotrade_position_loop"], loops["kis_rebalance"]["detail"]),
        ("Dashboard", completion["performance_dashboard"], "HTML + JSON refresh"),
    ]
    progress_html = "\n".join(
        f"""
        <div class="progress-row">
          <div class="progress-head"><span>{esc(name)}</span><strong>{pct(value)}</strong></div>
          <div class="bar"><i style="width:{value * 100:.1f}%"></i></div>
          <div class="hint">{esc(detail)}</div>
        </div>
        """
        for name, value, detail in progress_rows
    )

    loop_rows = "\n".join(
        f"<tr><td>{esc(name)}</td><td>{esc(row['status'])}</td><td>{esc(row['pid'] or '-')}</td><td>{esc(row['detail'])}</td></tr>"
        for name, row in loops.items()
    )
    top_crypto = (direct_dev["top_crypto"][0] or {}) if direct_dev["top_crypto"] else {}
    top_kis = (direct_dev["top_kis"][0] or {}) if direct_dev["top_kis"] else {}

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="60">
  <title>AI Trading Pipeline</title>
  <style>
    :root {{
      --bg: #f5f6f8;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #687385;
      --line: #d9dee7;
      --accent: #1f7a5c;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); font-family: Arial, "Malgun Gothic", sans-serif; letter-spacing: 0; }}
    main {{ width: min(1120px, calc(100vw - 28px)); margin: 22px auto 42px; }}
    header {{ display: flex; justify-content: space-between; gap: 18px; margin-bottom: 16px; border-bottom: 1px solid var(--line); padding-bottom: 14px; }}
    h1 {{ margin: 0; font-size: 24px; }}
    h2 {{ margin: 0 0 12px; font-size: 16px; }}
    .stamp, .sub, .hint, li {{ color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }}
    .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }}
    .card, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    .label {{ color: var(--muted); font-size: 12px; margin-bottom: 8px; }}
    .value {{ font-size: 22px; font-weight: 700; line-height: 1.15; }}
    .progress-row {{ padding: 10px 0; border-top: 1px solid var(--line); }}
    .progress-row:first-of-type {{ border-top: 0; }}
    .progress-head {{ display: flex; justify-content: space-between; gap: 10px; font-size: 14px; }}
    .bar {{ height: 9px; background: #e8ecf2; border-radius: 999px; overflow: hidden; margin: 8px 0 6px; }}
    .bar i {{ display: block; height: 100%; background: var(--accent); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; padding: 8px 6px; border-top: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; }}
    ul {{ margin: 0; padding-left: 18px; }}
    @media (max-width: 820px) {{ .grid, .two {{ grid-template-columns: 1fr; }} header {{ display: block; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>AI Trading Pipeline</h1>
      <div class="stamp">Auto refresh 60s · {esc(summary["generated_at_utc"])}</div>
    </div>
  </header>

  <div class="grid">
    {card("Overall", pct(summary["overall_completion"]), "dev / verify / live / position / dashboard")}
    {card("Bithumb", trading["bithumb"]["status"], f"exposure {krw(trading['bithumb']['exposure_krw'])} / cap {krw(trading['bithumb']['cap_krw'])}")}
    {card("KIS", trading["kis"]["order_submit_status"], f"{trading['kis']['tiny_live_buyable_symbol_count']}/{len(trading['kis']['symbols'])} buyable, ledger {trading['kis']['ledger_submitted_count']} / {krw(trading['kis']['ledger_submitted_notional_krw'])}")}
    {card("Direct Dev", f"{direct_dev['crypto_validated_pass']} / {direct_dev['kis_pass']}", f"crypto markets {direct_dev['crypto_validated_market_count']}, OOS {direct_dev['crypto_oos_pass']}, live sig {direct_dev.get('crypto_top_live_signal_triggered_count')}")}
    {card("Model Only", "CHECK" if model_only_attention else "OK", f"KIS order flags {len(guardrails.get('kis_true_order_path_flags') or [])}, intent allowed {kis_order_intent_submit_allowed_count}")}
    {card("Model Code", "STALE PID" if model_factory_runtime.get("process_predates_source") else "CURRENT", f"pid {model_factory_runtime.get('pid') or '-'}")}
    {card("Model Contract", "CURRENT" if model_factory_running_contract.get("contract_current") and model_factory_artifact_schema.get("schema_version_current") else "STALE", f"running {model_factory_running_contract.get('contract_current')}, latest {model_factory_artifact_schema.get('schema_version_current')}")}
    {card("Model Cadence", "OVERDUE" if model_factory_cadence.get("overdue") else "ON TIME", f"elapsed {model_factory_cadence.get('elapsed_seconds') or '-'}s, next {model_factory_cadence.get('next_cycle_due_at_utc') or '-'}")}
  </div>

  <div class="two">
    <section class="panel">
      <h2>Pipeline Completion</h2>
      {progress_html}
    </section>
    <section class="panel">
      <h2>Loop Status</h2>
      <table>
        <tr><th>Loop</th><th>Status</th><th>PID</th><th>Detail</th></tr>
        {loop_rows}
      </table>
    </section>
  </div>

  <div class="two">
    <section class="panel">
      <h2>Direct Development</h2>
      <ul>
        <li>Crypto: candidates {esc(direct_dev["crypto_candidates"])}, OOS pass {esc(direct_dev["crypto_oos_pass"])}, validated pass {esc(direct_dev["crypto_validated_pass"])}, markets {esc(direct_dev["crypto_validated_market_count"])}</li>
        <li>Crypto signal check: archive triggered {esc(direct_dev.get("crypto_archive_signal_triggered_count"))}, top live triggered {esc(direct_dev.get("crypto_top_live_signal_triggered_count"))}, top live verified {esc(direct_dev.get("crypto_top_live_signal_all_verified"))}</li>
        <li>KIS: variants {esc(direct_dev["kis_variants"])}, pass {esc(direct_dev["kis_pass"])}</li>
        <li>Top crypto: {esc(top_crypto.get("candidate_id", "-"))} / CAGR {pct(float(top_crypto.get("cagr") or 0))} / MDD {pct(float(top_crypto.get("mdd") or 0))} / archive signal {esc(top_crypto.get("archive_signal_triggered"))} gap {esc(top_crypto.get("archive_signal_nearest_gap"))} / live signal {esc(top_crypto.get("live_signal_triggered"))} gap {esc(top_crypto.get("live_signal_nearest_gap"))} / live data {esc(top_crypto.get("live_signal_data_status") or "-")} {esc(top_crypto.get("live_signal_latest_timestamp") or "-")} / order paths {esc(top_crypto.get("order_paths_allowed"))} / live evidence {esc(top_crypto.get("counts_as_live_evidence"))}</li>
        <li>Top KIS: {esc(top_kis.get("candidate_id", "-"))} / parent {esc(top_kis.get("parent_candidate_id") or "-")} / cap {esc(top_kis.get("fixed_exposure_cap") or "-")} / CAGR {pct(float(top_kis.get("cagr") or 0))} / MDD {pct(float(top_kis.get("mdd") or 0))} / order paths {esc(top_kis.get("order_paths_allowed"))} / live evidence {esc(top_kis.get("counts_as_live_evidence"))}</li>
      </ul>
    </section>
    <section class="panel">
      <h2>Trading</h2>
      <ul>
        <li>Bithumb candidates: {esc(", ".join(trading["bithumb"]["markets"]) or "-")}</li>
        <li>Bithumb open: {esc(", ".join(trading["bithumb"]["open_positions"]) or "-")}</li>
        <li>KIS target symbols: {esc(", ".join(trading["kis"]["symbols"]) or "-")}</li>
        <li>KIS tiny-live buyable: {esc(trading["kis"]["tiny_live_buyable_symbol_count"])}/{esc(len(trading["kis"]["symbols"]))}, estimated notional {krw(trading["kis"]["estimated_buyable_notional_krw"])}</li>
        <li>KIS execution warnings: {esc(", ".join(trading["kis"]["execution_warnings"]) or "-")}</li>
        <li>KIS tiny-live repair: {esc(trading["kis"].get("tiny_live_repair_status") or "-")} / OOS {esc(trading["kis"].get("tiny_live_repair_oos_status") or "-")} / CAGR {pct(float(trading["kis"].get("tiny_live_repair_oos_cagr") or 0))} / MDD {pct(float(trading["kis"].get("tiny_live_repair_oos_mdd") or 0))} / holdout {pct(float(trading["kis"].get("tiny_live_repair_oos_holdout_cagr") or 0))}</li>
        <li>KIS tiny-live repair symbols: {esc(trading["kis"].get("tiny_live_repair_buyable_count") or 0)} buyable / {esc(", ".join(trading["kis"].get("tiny_live_repair_symbols") or []) or "-")} / active months {pct(float(trading["kis"].get("tiny_live_repair_active_month_coverage") or 0))}</li>
        <li>KIS target exposure: {pct(float(trading["kis"]["gross_target_weight"] or 0))}, cash {pct(float(trading["kis"]["cash_weight"] or 0))}</li>
        <li>KIS direct recommendation: {esc(trading["kis"].get("direct_recommended_parent") or "-")} / cap {esc(trading["kis"].get("direct_recommended_cap") or "-")}</li>
        <li>KIS rebalance: {esc(trading["kis"]["rebalance_status"])}</li>
      </ul>
    </section>
  </div>

  <div class="two">
    <section class="panel">
      <h2>Account Engine</h2>
      <ul>
        <li>Bithumb account: source {esc((account_engine.get("bithumb") or {}).get("snapshot_source") or "-")}, positions {esc((account_engine.get("bithumb") or {}).get("position_count", 0))}, cash {krw((account_engine.get("bithumb") or {}).get("cash_krw"))}</li>
        <li>Bithumb diff: actionable {esc((account_engine.get("bithumb") or {}).get("actionable_count", 0))}, unresolved orders {esc((account_engine.get("bithumb") or {}).get("unresolved_order_count", 0))}</li>
        <li>KIS account: source {esc((account_engine.get("kis") or {}).get("snapshot_source") or "-")}, positions {esc((account_engine.get("kis") or {}).get("position_count", 0))}, cash {krw((account_engine.get("kis") or {}).get("cash_krw"))}</li>
        <li>KIS diff: actionable {esc((account_engine.get("kis") or {}).get("actionable_count", 0))}, unresolved orders {esc((account_engine.get("kis") or {}).get("unresolved_order_count", 0))}</li>
      </ul>
    </section>
    <section class="panel">
      <h2>Model-Only Guardrails</h2>
      <ul>
        <li>All known order paths false: {esc(guardrails.get("all_known_order_paths_false"))}</li>
        <li>Source times: {esc(guardrails.get("source_generated_at_utc") or {})}</li>
        <li>Direct development: {esc((guardrails.get("direct_development") or {}).get("all_order_paths_false"))}</li>
        <li>Bithumb OOS: {esc((guardrails.get("bithumb_oos") or {}).get("all_order_paths_false"))}</li>
        <li>Bithumb robustness: {esc((guardrails.get("bithumb_robustness") or {}).get("all_order_paths_false"))}</li>
        <li>KIS bridge assertions: {esc((guardrails.get("kis_bridge") or {}).get("all_order_paths_false"))}</li>
        <li>KIS order-path flags: {esc(", ".join(guardrails.get("kis_true_order_path_flags") or []) or "-")}</li>
        <li>Model factory runtime: process predates source {esc(model_factory_runtime.get("process_predates_source"))}, process {esc(model_factory_runtime.get("process_created_at_utc") or "-")}, source {esc(model_factory_runtime.get("source_mtime_utc") or "-")}, latest not older than source {esc(model_factory_runtime.get("latest_json_not_older_than_source"))}, latest {esc(model_factory_runtime.get("latest_json_mtime_utc") or "-")}</li>
        <li>Model factory cadence: elapsed {esc(model_factory_cadence.get("elapsed_seconds") or "-")} seconds, next due {esc(model_factory_cadence.get("next_cycle_due_at_utc") or "-")}, overdue {esc(model_factory_cadence.get("overdue"))}, seconds overdue {esc(model_factory_cadence.get("seconds_overdue", 0))}</li>
        <li>Model factory running contract: schema {esc(model_factory_running_contract.get("schema_version"))} / current {esc(model_factory_running_contract.get("contract_current"))} / status {esc(model_factory_running_contract.get("status") or "-")} / step {esc(model_factory_running_contract.get("current_step") or "-")} / model-only safety {esc(model_factory_running_contract.get("model_only_safety_present"))}</li>
        <li>Model factory schema version: {esc(model_factory_artifact_schema.get("schema_version"))} expected {esc(model_factory_artifact_schema.get("expected_schema_version"))} / current {esc(model_factory_artifact_schema.get("schema_version_current"))} / step manifest matches {esc(model_factory_artifact_schema.get("step_manifest_matches_expected"))} / model-only safety {esc(model_factory_artifact_schema.get("model_only_safety_present"))} / no order flags {esc(model_factory_artifact_schema.get("model_only_safety_no_order_flags"))} / no submit {esc(model_factory_artifact_schema.get("model_only_safety_no_submit"))} / stale scope {esc(model_factory_artifact_schema.get("stale_scope") or "-")} / stale reasons {esc(", ".join(model_factory_artifact_schema.get("stale_reasons") or []) or "-")}</li>
        <li>Model factory artifact schema: direct KIS fields present {esc(model_factory_artifact_schema.get("direct_kis_validation_fields_present"))} / missing {esc(", ".join(model_factory_artifact_schema.get("missing_direct_development_fields") or []) or "-")} / Bithumb source fields present {esc(model_factory_artifact_schema.get("bithumb_source_fields_present"))} / missing {esc(", ".join(model_factory_artifact_schema.get("missing_bithumb_fields") or []) or "-")} / KIS inventory fields present {esc(model_factory_artifact_schema.get("kis_inventory_fields_present"))} / missing {esc(", ".join(model_factory_artifact_schema.get("missing_kis_inventory_fields") or []) or "-")}</li>
        <li>Canonical child artifacts: complete {esc(model_factory_artifact_schema.get("canonical_child_artifacts_complete"))} / direct fields present {esc(model_factory_artifact_schema.get("canonical_direct_development_fields_present"))} / missing direct fields {esc(", ".join(model_factory_artifact_schema.get("canonical_missing_direct_development_fields") or []) or "-")} / Bithumb sources present {esc(model_factory_artifact_schema.get("canonical_bithumb_sources_present"))} / KIS inventory sources present {esc(model_factory_artifact_schema.get("canonical_kis_inventory_sources_present"))}</li>
      </ul>
    </section>
  </div>

  <div class="two">
    <section class="panel">
      <h2>Performance</h2>
      <ul>
        <li>Bithumb ORCA: {esc(trading["bithumb"]["position_status"])} / {esc(trading["bithumb"]["last_reason"] or "-")} / {krw(trading["bithumb"]["realized_pnl_krw"])} / {float(trading["bithumb"]["realized_return_pct"] or 0):.2f}%</li>
        <li>Bithumb OOS: {esc(bithumb_verification.get("oos_status") or "-")} / pass {esc(bithumb_verification.get("oos_pass_count") or 0)}/{esc(bithumb_verification.get("oos_evaluated_count") or 0)} / top {esc(bithumb_verification.get("oos_top_candidate_id") or "-")} {esc(bithumb_verification.get("oos_top_market") or "")} / order paths {esc(bithumb_verification.get("oos_order_paths_allowed"))} / generated {esc(bithumb_verification.get("oos_generated_at") or "-")}</li>
        <li>Bithumb current signal scout: generated {esc(bithumb_verification.get("inventory_current_signal_generated_at_utc") or bithumb_verification.get("inventory_current_signal_generated_at") or "-")} / evaluated {esc(bithumb_verification.get("inventory_current_signal_evaluated_count"))} / triggered {esc(bithumb_verification.get("inventory_current_signal_triggered_count"))}</li>
        <li>Bithumb inventory signal: current {esc(bithumb_verification.get("inventory_current_signal_candidate_id") or "-")} / inventory OOS top {esc(bithumb_verification.get("inventory_oos_top_candidate_id") or "-")} / matches OOS top {esc(bithumb_verification.get("inventory_current_signal_matches_oos_top"))} / avg fold CAGR {pct(float(bithumb_verification.get("inventory_current_signal_oos_average_fold_cagr") or 0))} vs {pct(float(bithumb_verification.get("inventory_oos_top_average_fold_cagr") or 0))} / trades {esc(bithumb_verification.get("inventory_current_signal_oos_trade_count") or 0)} vs {esc(bithumb_verification.get("inventory_oos_top_trade_count") or 0)}</li>
        <li>Bithumb signal selection: policy {esc((bithumb_verification.get("inventory_current_signal_selection_policy") or {}).get("description") or "-")} / rank current {esc(bithumb_verification.get("inventory_current_signal_selection_rank") or "-")} vs OOS top {esc(bithumb_verification.get("inventory_oos_top_signal_selection_rank") or "-")} / estimated CAGR {pct(float(bithumb_verification.get("inventory_current_signal_selection_estimated_cagr") or 0))} vs {pct(float(bithumb_verification.get("inventory_oos_top_signal_selection_estimated_cagr") or 0))}</li>
        <li>Bithumb signal near miss: {esc(bithumb_verification.get("inventory_current_signal_near_miss_candidate_id") or "-")} / momentum gap {esc(bithumb_verification.get("inventory_current_signal_near_miss_momentum_gap"))} / volume gap {esc(bithumb_verification.get("inventory_current_signal_near_miss_volume_gap"))} / blockers {esc(", ".join(bithumb_verification.get("inventory_current_signal_near_miss_blocking_conditions") or []) or "-")}</li>
        <li>Bithumb signal near miss candidates: {esc(len(bithumb_verification.get("inventory_current_signal_near_miss_candidates") or []))}</li>
        <li>Bithumb direct live near miss: {esc(bithumb_verification.get("inventory_direct_top_live_near_miss_candidate_id") or "-")} / market {esc(bithumb_verification.get("inventory_direct_top_live_near_miss_market") or "-")} / momentum gap {esc(bithumb_verification.get("inventory_direct_top_live_near_miss_momentum_gap"))} / volume gap {esc(bithumb_verification.get("inventory_direct_top_live_near_miss_volume_gap"))} / blockers {esc(", ".join(bithumb_verification.get("inventory_direct_top_live_near_miss_blocking_conditions") or []) or "-")}</li>
        <li>Bithumb robustness: {esc(bithumb_verification.get("robustness_status") or "-")} / candidate {esc(bithumb_verification.get("robustness_candidate_id") or "-")} / matches OOS top {esc(bithumb_verification.get("robustness_matches_oos_top"))} / source OOS matches current {esc(bithumb_verification.get("robustness_source_oos_matches_current"))} / not older than OOS {esc(bithumb_verification.get("robustness_not_older_than_oos"))} / pass {esc(bithumb_verification.get("robustness_pass_count") or 0)}/{esc(bithumb_verification.get("robustness_case_count") or 0)} / cost {esc(bithumb_verification.get("robustness_cost_pass_count") or 0)} / order paths {esc(bithumb_verification.get("robustness_order_paths_allowed"))}</li>
        <li>KIS live: {esc(trading["kis"]["order_submit_status"])} / latest submitted {esc(trading["kis"]["submitted_count"])} / ledger submitted {esc(trading["kis"]["ledger_submitted_count"])} / {krw(trading["kis"]["ledger_submitted_notional_krw"])}</li>
        <li>KIS backtest: CAGR {pct(float(kis_bt["before_cagr"] or 0))}, MDD {pct(float(kis_bt["before_mdd"] or 0))}, Sharpe {float(kis_bt["before_sharpe"] or 0):.2f}</li>
        <li>KIS converted: estimated CAGR {pct(float(kis_bt["estimated_cagr"] or 0))}, estimated MDD {pct(float(kis_bt["estimated_mdd"] or 0))}</li>
        <li>KIS direct development: variants {esc(direct_dev.get("kis_variants") or 0)} / pass {esc(direct_dev.get("kis_pass") or 0)} / universe {esc(direct_dev.get("kis_universe_validation_mode") or "-")} / verifier {esc(direct_dev.get("kis_universe_validation_verifier_status") or "-")} / operation ready {esc(direct_dev.get("kis_universe_validation_operation_ready"))} / all verified {esc(direct_dev.get("kis_universe_validation_all_verified"))} / operational {esc(direct_dev.get("kis_universe_validation_operational"))} / live evidence {esc(direct_dev.get("kis_counts_as_live_evidence"))}</li>
        <li>KIS verification: {esc(kis_verification.get("bridge_status") or "-")} / repair {esc(kis_verification.get("repair_status") or "-")} / OOS {esc(kis_verification.get("repair_oos_status") or "-")} / folds {esc(kis_verification.get("repair_oos_pass_folds") or 0)}/{esc(kis_verification.get("repair_oos_folds") or 0)}</li>
        <li>KIS universe validation: {esc(kis_verification.get("universe_validation_mode") or "-")} / operational {esc(kis_verification.get("universe_validation_operational"))} / verifier {esc(kis_verification.get("universe_validation_verifier_status") or "-")} / operation ready {esc(kis_verification.get("universe_validation_operation_ready"))} / all verified {esc(kis_verification.get("universe_validation_all_verified"))} / blockers {esc(", ".join(kis_verification.get("universe_validation_blockers") or []) or "-")}</li>
        <li>KIS direct/bridge universe validation match: {esc(kis_verification.get("direct_bridge_universe_validation_match"))}</li>
        <li>KIS direct not older than bridge: {esc(kis_verification.get("direct_not_older_than_bridge"))}</li>
        <li>KIS direct source bridge matches current: {esc(kis_verification.get("direct_source_bridge_matches_current"))}</li>
        <li>KIS bridge/direct top match: {esc(kis_verification.get("bridge_matches_direct_top_parent"))} / direct top parent {esc(kis_verification.get("direct_top_parent_candidate_id") or "-")}</li>
        <li>KIS verification order paths: repair {esc(kis_verification.get("repair_order_paths_allowed"))} / repair OOS {esc(kis_verification.get("repair_oos_order_paths_allowed"))} / live evidence {esc(kis_verification.get("repair_counts_as_live_evidence"))} / OOS evidence {esc(kis_verification.get("repair_oos_counts_as_live_evidence"))}</li>
        <li>KIS order intent artifact: rows {esc(kis_verification.get("order_intent_row_count") or 0)} / submit allowed {esc(kis_verification.get("order_intent_submit_allowed_count") or 0)} / symbols {esc(", ".join(kis_verification.get("order_intent_submit_allowed_symbols") or []) or "-")}</li>
      </ul>
    </section>
  </div>
</main>
</body>
</html>
"""


def main() -> None:
    summary = build_summary()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_text(SUMMARY_PATH, json.dumps(summary, indent=2, ensure_ascii=False))
    atomic_write_text(HTML_PATH, render_html(summary))
    print(str(HTML_PATH))


if __name__ == "__main__":
    main()
