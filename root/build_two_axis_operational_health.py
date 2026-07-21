from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "ops" / "health"
OUT_JSON = OUT_DIR / "two_axis_operational_health_latest.json"
OUT_MD = OUT_DIR / "two_axis_operational_health_latest.md"
MODEL_DEVELOPMENT_FINDINGS = {
    "MODEL_FACTORY_ATTENTION",
    "MODEL_FACTORY_ARTIFACT_SUMMARY_SCHEMA_STALE",
    "MODEL_FACTORY_LOOP_SUMMARY_ONLY_STALE",
    "MODEL_FACTORY_RUNNING_CONTRACT_STALE",
    "MODEL_FACTORY_CYCLE_OVERDUE",
    "MODEL_ONLY_GUARDRAIL_ATTENTION",
    "BITHUMB_OOS_ROBUSTNESS_CANDIDATE_MISMATCH",
    "BITHUMB_ROBUSTNESS_SOURCE_OOS_MISMATCH",
    "BITHUMB_ROBUSTNESS_OLDER_THAN_OOS",
    "BITHUMB_CURRENT_SIGNAL_OOS_TOP_MISMATCH",
    "KIS_DIRECT_BRIDGE_UNIVERSE_VALIDATION_MISMATCH",
    "KIS_DIRECT_DEVELOPMENT_OLDER_THAN_BRIDGE",
    "KIS_DIRECT_SOURCE_BRIDGE_MISMATCH",
    "KIS_BRIDGE_DIRECT_TOP_PARENT_MISMATCH",
}
LIVE_RUNTIME_FINDINGS = {
    "LOOP_NOT_RUNNING",
    "ERROR_TEXT_IN_STDERR",
    "BITHUMB_GLOBAL_DISABLE_PRESENT",
    "BITHUMB_EXPOSURE_CAP_EXCEEDED",
    "BITHUMB_DAILY_LOSS_CAP_EXCEEDED",
    "KIS_SUBMIT_NOT_ENABLED",
    "KIS_EXECUTION_WARNINGS",
    "MODEL_FACTORY_PROCESS_PREDATES_SOURCE",
    "KIS_ORDER_INTENT_SUBMIT_ALLOWED_ARTIFACT",
    "KIS_ACCOUNT_SNAPSHOT_MISSING",
    "BITHUMB_ACCOUNT_SNAPSHOT_MISSING",
    "KIS_UNRESOLVED_BROKER_ORDERS",
    "BITHUMB_UNRESOLVED_BROKER_ORDERS",
}

PID_FILES = {
    "bithumb_autotrade": ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_loop.pid",
    "kis_plan": ROOT / "ops" / "stock_etf_axis_operation" / "stock_etf_axis_plan_loop.pid",
    "kis_buy": ROOT / "ops" / "stock_etf_axis_operation" / "stock_etf_axis_operation_loop.pid",
    "kis_rebalance": ROOT / "ops" / "kis_position_rebalance" / "kis_position_rebalance_loop.pid",
    "model_factory": ROOT / "ops" / "model_factory_loop" / "two_axis_model_factory_loop.pid",
    "dashboard": ROOT / "ops" / "dashboard" / "pipeline_dashboard_loop.pid",
}

LOOP_PATTERNS = {
    "bithumb_autotrade": "run_bithumb_axis_autotrade_loop.py",
    "kis_plan": "run_kis_daily_trade_window_loop.ps1 -Mode plan",
    "kis_buy": "run_kis_daily_trade_window_loop.ps1 -Mode buy",
    "kis_rebalance": "run_kis_daily_trade_window_loop.ps1 -Mode rebalance",
    "model_factory": "run_two_axis_model_factory_loop.py",
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

STATUS_FILES = {
    "bithumb": ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_latest.json",
    "kis": ROOT / "ops" / "stock_etf_axis_operation" / "stock_etf_axis_operation_latest.json",
    "kis_submit": ROOT / "ops" / "stock_etf_axis_operation" / "kis_stock_etf_order_submit_latest.json",
    "kis_rebalance": ROOT / "ops" / "kis_position_rebalance" / "kis_position_rebalance_latest.json",
    "model_factory": ROOT / "ops" / "model_factory_loop" / "two_axis_model_factory_loop_latest.json",
    "model_factory_running": ROOT / "ops" / "model_factory_loop" / "two_axis_model_factory_loop_running.json",
    "dashboard": ROOT / "ops" / "dashboard" / "pipeline_dashboard_simple_latest.json",
    "direct_development": ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json",
    "bithumb_oos": ROOT / "reports" / "model_factory" / "bithumb_current_actionable_oos_walkforward_latest.json",
    "bithumb_robustness": ROOT / "reports" / "model_factory" / "bithumb_current_actionable_robustness_stress_latest.json",
    "model_inventory": ROOT / "reports" / "operations" / "two_axis_model_inventory_latest.json",
    "limited_policy": ROOT / "ops" / "runstate" / "limited_live_policy.json",
    "bithumb_orca_event": ROOT / "Crypto" / "logs" / "bithumb_axis_portfolio_events" / "orca_event_latest.json",
    "bithumb_orca_state": ROOT / "Crypto" / "logs" / "bithumb_live_orca_portfolio_state.json",
    "bithumb_account_snapshot": ROOT / "ops" / "account_engine" / "bithumb_krw" / "account_snapshot_latest.json",
    "bithumb_target_diff": ROOT / "ops" / "account_engine" / "bithumb_krw" / "target_diff_latest.json",
    "bithumb_reconciliation": ROOT / "ops" / "account_engine" / "bithumb_krw" / "reconciliation_latest.json",
    "kis_account_snapshot": ROOT / "ops" / "account_engine" / "kis_combined_krw" / "account_snapshot_latest.json",
    "kis_target_diff": ROOT / "ops" / "account_engine" / "kis_combined_krw" / "target_diff_latest.json",
    "kis_reconciliation": ROOT / "ops" / "account_engine" / "kis_combined_krw" / "reconciliation_latest.json",
    "kis_bridge": ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_candidate_bridge_latest.json",
}

KIS_LEDGER = ROOT / "ops" / "stock_etf_axis_operation" / "kis_stock_etf_order_ledger.jsonl"
KIS_ORDER_INTENT_CSV = ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_order_intent_latest.csv"

LOG_FILES = {
    "bithumb_stderr": ROOT / "ops" / "bithumb_axis_autotrade" / "bithumb_axis_autotrade_stderr.log",
    "kis_buy_stderr": ROOT / "ops" / "stock_etf_axis_operation" / "stock_etf_axis_operation_stderr.log",
    "kis_rebalance_stderr": ROOT / "ops" / "kis_position_rebalance" / "kis_position_rebalance_stderr.log",
    "model_factory_stderr": ROOT / "ops" / "model_factory_loop" / "two_axis_model_factory_loop_stderr.log",
    "dashboard_stderr": ROOT / "ops" / "dashboard" / "pipeline_dashboard_stderr.log",
}

LOG_STATUS_FILES = {
    "bithumb_stderr": STATUS_FILES["bithumb"],
    "kis_buy_stderr": STATUS_FILES["kis"],
    "kis_rebalance_stderr": STATUS_FILES["kis_rebalance"],
    "model_factory_stderr": STATUS_FILES["model_factory"],
    "dashboard_stderr": STATUS_FILES["dashboard"],
}


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


def load_json(path: Path, name: str | None = None, findings: list[str] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            raise json.JSONDecodeError("empty status file", text, 0)
        data = json.loads(text)
    except json.JSONDecodeError:
        if findings is not None:
            findings.append(f"STATUS_JSON_UNREADABLE:{name or path.name}")
        return {}
    if isinstance(data, dict):
        return data
    if findings is not None:
        findings.append(f"STATUS_JSON_NOT_OBJECT:{name or path.name}")
    return {}


def read_pid(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def summarize_order_intent(rows: list[dict[str, str]]) -> dict[str, Any]:
    submit_allowed_rows = [
        row for row in rows if str(row.get("SubmitAllowed", "")).strip().lower() in {"true", "1", "yes"}
    ]
    return {
        "row_count": len(rows),
        "submit_allowed_count": len(submit_allowed_rows),
        "submit_allowed_symbols": [str(row.get("Symbol", "")) for row in submit_allowed_rows if row.get("Symbol")],
    }


def order_intent_summary_from_bridge(bridge: dict[str, Any], fallback_rows: list[dict[str, str]]) -> dict[str, Any]:
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


def log_tail(path: Path, max_chars: int = 2000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-max_chars:]


def log_has_error(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ["traceback", "exception", "error", "failed", "can't open", "no such file"])


def build_log_status(name: str, path: Path) -> dict[str, Any]:
    tail = log_tail(path, 500)
    raw_has_error_text = log_has_error(tail)
    status_path = LOG_STATUS_FILES.get(name)
    log_mtime = path.stat().st_mtime if path.exists() else None
    status_mtime = status_path.stat().st_mtime if status_path and status_path.exists() else None
    superseded_by_success = (
        bool(raw_has_error_text)
        and log_mtime is not None
        and status_mtime is not None
        and status_mtime > log_mtime
    )
    return {
        "path": str(path),
        "length": path.stat().st_size if path.exists() else 0,
        "mtime_utc": file_mtime_utc(path),
        "status_path": str(status_path) if status_path else "",
        "status_mtime_utc": file_mtime_utc(status_path) if status_path else "",
        "raw_has_error_text": raw_has_error_text,
        "superseded_by_success": superseded_by_success,
        "has_error_text": raw_has_error_text and not superseded_by_success,
        "tail": "" if superseded_by_success else tail,
    }


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def truthy_flag(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def classify_findings(findings: list[str]) -> dict[str, list[str]]:
    return {
        "model_development_or_verification": [
            finding for finding in findings if finding in MODEL_DEVELOPMENT_FINDINGS
        ],
        "live_runtime_or_account": [
            finding for finding in findings if finding in LIVE_RUNTIME_FINDINGS
        ],
        "other": [
            finding
            for finding in findings
            if finding not in MODEL_DEVELOPMENT_FINDINGS and finding not in LIVE_RUNTIME_FINDINGS
        ],
    }


def summarize_no_order_assertions(payload: dict[str, Any]) -> dict[str, Any]:
    assertions = payload.get("no_order_assertions")
    if not isinstance(assertions, dict):
        return {"present": False, "all_order_paths_false": False, "true_flags": []}
    true_flags = sorted(key for key, value in assertions.items() if truthy_flag(value))
    return {"present": True, "all_order_paths_false": not true_flags, "true_flags": true_flags}


def build_model_factory_runtime_freshness(loops: dict[str, dict[str, Any]]) -> dict[str, Any]:
    loop = loops.get("model_factory") or {}
    pid = str(loop.get("detected_pid") or loop.get("pid") or "")
    source_path = ROOT / "run_two_axis_model_factory_loop.py"
    latest_path = STATUS_FILES["model_factory"]
    source_mtime = file_mtime_utc(source_path)
    latest_mtime = file_mtime_utc(latest_path)
    process_created_at = process_creation_time_utc(pid)
    source_dt = parse_utc_timestamp(source_mtime)
    latest_dt = parse_utc_timestamp(latest_mtime)
    process_dt = parse_utc_timestamp(process_created_at)
    process_predates_source = bool(source_dt and process_dt and process_dt < source_dt)
    return {
        "pid": pid,
        "source_path": str(source_path),
        "source_mtime_utc": source_mtime,
        "latest_json_path": str(latest_path),
        "latest_json_mtime_utc": latest_mtime,
        "process_created_at_utc": process_created_at,
        "process_predates_source": process_predates_source,
        "latest_json_not_older_than_source": bool(source_dt and latest_dt and latest_dt >= source_dt),
    }


def build_model_factory_cadence(model_factory_running: dict[str, Any], now_utc: str | None = None) -> dict[str, Any]:
    status = model_factory_running.get("status")
    generated_at = model_factory_running.get("generated_at_utc")
    started_at = model_factory_running.get("cycle_started_at_utc")
    due_at = model_factory_running.get("next_cycle_due_at_utc")
    generated_dt = parse_utc_timestamp(str(generated_at) if generated_at else None)
    started_dt = parse_utc_timestamp(str(started_at) if started_at else None)
    due_dt = parse_utc_timestamp(str(due_at) if due_at else None)
    now_dt = parse_utc_timestamp(now_utc or utc_now())
    is_running_cycle = status == "TWO_AXIS_MODEL_FACTORY_RUNNING"
    seconds_overdue = 0
    if due_dt and now_dt and now_dt > due_dt and not is_running_cycle:
        seconds_overdue = int((now_dt - due_dt).total_seconds())
    elapsed_seconds = None
    if started_dt:
        end_dt = now_dt if is_running_cycle else generated_dt
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
    model_factory: dict[str, Any],
    direct_development: dict[str, Any],
    bithumb_oos: dict[str, Any] | None = None,
    bithumb_robustness: dict[str, Any] | None = None,
    model_inventory: dict[str, Any] | None = None,
) -> dict[str, Any]:
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


def build_model_factory_running_contract(model_factory_running: dict[str, Any]) -> dict[str, Any]:
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


def build_report() -> dict[str, Any]:
    findings: list[str] = []
    statuses = {name: load_json(path, name, findings) for name, path in STATUS_FILES.items()}
    loops = {}
    for name, path in PID_FILES.items():
        file_pid = read_pid(path)
        file_running = pid_running(file_pid)
        detected = find_process_by_pattern(LOOP_PATTERNS.get(name, ""))
        detected_running = bool(detected.get("running"))
        loops[name] = {
            "pid_file": str(path),
            "pid": file_pid,
            "pid_file_running": file_running,
            "detected_pid": detected.get("pid", ""),
            "detected_command_line": detected.get("command_line", ""),
            "running": file_running or detected_running,
            "source": "pid_file" if file_running else ("process_scan" if detected_running else "not_found"),
        }
    logs = {name: build_log_status(name, path) for name, path in LOG_FILES.items()}

    bithumb = statuses["bithumb"]
    kis = statuses["kis"]
    kis_submit = statuses["kis_submit"]
    kis_rebalance = statuses["kis_rebalance"]
    model_factory = statuses["model_factory"]
    model_factory_running = statuses["model_factory_running"]
    direct_development = statuses["direct_development"]
    bithumb_oos = statuses["bithumb_oos"]
    bithumb_robustness = statuses["bithumb_robustness"]
    model_inventory = statuses["model_inventory"]
    dashboard = statuses["dashboard"]
    policy = statuses["limited_policy"]
    orca_event = statuses["bithumb_orca_event"]
    orca_state = statuses["bithumb_orca_state"]
    bithumb_account = statuses["bithumb_account_snapshot"]
    bithumb_diff = statuses["bithumb_target_diff"]
    bithumb_reconciliation = statuses["bithumb_reconciliation"]
    kis_account = statuses["kis_account_snapshot"]
    kis_diff = statuses["kis_target_diff"]
    kis_reconciliation = statuses["kis_reconciliation"]
    standalone_bridge = statuses["kis_bridge"]
    kis_submitted_ledger = [row for row in load_jsonl(KIS_LEDGER) if row.get("status") == "SUBMITTED"]
    kis_ledger_notional = sum(float(row.get("estimated_notional_krw") or 0.0) for row in kis_submitted_ledger)
    bridge = standalone_bridge or kis.get("operating_candidate_bridge") or {}
    kis_repair = bridge.get("tiny_live_executable_repair") or {}
    kis_repair_oos = kis_repair.get("historical_oos_validation") or {}
    kis_order_path_flags = {
        "source_order_paths_allowed": truthy_flag(bridge.get("source_order_paths_allowed", False)),
        "repair_order_paths_allowed": truthy_flag(kis_repair.get("order_paths_allowed", False)),
        "repair_counts_as_live_evidence": truthy_flag(kis_repair.get("counts_as_live_evidence", False)),
        "repair_oos_order_paths_allowed": truthy_flag(kis_repair_oos.get("order_paths_allowed", False)),
        "repair_oos_counts_as_live_evidence": truthy_flag(kis_repair_oos.get("counts_as_live_evidence", False)),
    }
    kis_true_order_path_flags = sorted(key for key, value in kis_order_path_flags.items() if value)
    kis_order_intent_summary = order_intent_summary_from_bridge(bridge, load_csv_rows(KIS_ORDER_INTENT_CSV))
    kis_universe_operational = kis_universe_validation_is_operational(bridge.get("universe_validation_mode"))
    direct_guard = summarize_no_order_assertions(direct_development)
    oos_guard = summarize_no_order_assertions(bithumb_oos)
    robustness_guard = summarize_no_order_assertions(bithumb_robustness)
    kis_bridge_guard = summarize_no_order_assertions(bridge)
    dashboard_guardrails = dashboard.get("model_only_guardrails") or {}
    inventory_kis_sources = (
        ((model_inventory.get("axes") or {}).get("KIS_COMBINED_KRW") or {}).get("verification_sources") or {}
    )
    model_only_guardrails = {
        "source_generated_at_utc": {
            "direct_development": direct_development.get("generated_at_utc"),
            "bithumb_oos": bithumb_oos.get("generated_at") or bithumb_oos.get("generated_at_utc"),
            "bithumb_robustness": bithumb_robustness.get("generated_at") or bithumb_robustness.get("generated_at_utc"),
            "kis_bridge": bridge.get("generated_at_utc"),
            "dashboard": dashboard.get("generated_at_utc"),
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
        "dashboard_all_known_order_paths_false": dashboard_guardrails.get("all_known_order_paths_false"),
        "dashboard_model_only_attention": dashboard_guardrails.get("model_only_attention"),
    }
    model_only_guardrails["all_known_order_paths_false"] = (
        direct_guard["all_order_paths_false"]
        and oos_guard["all_order_paths_false"]
        and robustness_guard["all_order_paths_false"]
        and kis_bridge_guard["all_order_paths_false"]
        and not kis_true_order_path_flags
    )
    model_only_guardrails["model_only_attention"] = (
        not model_only_guardrails["all_known_order_paths_false"]
        or int(kis_order_intent_summary["submit_allowed_count"] or 0) > 0
        or not kis_universe_operational
    )
    bithumb_oos_generated_at = bithumb_oos.get("generated_at") or bithumb_oos.get("generated_at_utc")
    bithumb_robustness_generated_at = bithumb_robustness.get("generated_at") or bithumb_robustness.get("generated_at_utc")
    inventory_bithumb_sources = (
        ((model_inventory.get("axes") or {}).get("BITHUMB_KRW") or {}).get("verification_sources") or {}
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
    model_verification = {
        "direct_development": {
            "status": direct_development.get("status"),
            "generated_at_utc": direct_development.get("generated_at_utc"),
            "crypto_candidate_count": (direct_development.get("crypto") or {}).get("candidate_count"),
            "crypto_oos_pass_count": (direct_development.get("crypto") or {}).get("oos_pass_count"),
            "crypto_validated_pass_count": (direct_development.get("crypto") or {}).get("validated_pass_count"),
            "crypto_archive_signal_triggered_count": (direct_development.get("crypto") or {}).get("archive_signal_triggered_count"),
            "crypto_top_live_signal_triggered_count": (direct_development.get("crypto") or {}).get("top_live_signal_triggered_count"),
            "crypto_top_live_signal_all_verified": ((direct_development.get("crypto") or {}).get("top_live_signal_summary") or {}).get("all_live_verified"),
            "crypto_top_live_near_miss_candidate": (direct_development.get("crypto") or {}).get("top_live_near_miss_candidate"),
            "kis_variant_count": (direct_development.get("kis") or {}).get("conversion_variant_count"),
            "kis_pass_count": (direct_development.get("kis") or {}).get("pass_count"),
            "kis_universe_validation_mode": (direct_development.get("kis") or {}).get("universe_validation_mode"),
            "kis_universe_validation_verifier_status": (direct_development.get("kis") or {}).get("universe_validation_verifier_status"),
            "kis_universe_validation_operation_ready": truthy_flag((direct_development.get("kis") or {}).get("universe_validation_operation_ready", False)),
            "kis_universe_validation_all_verified": truthy_flag((direct_development.get("kis") or {}).get("universe_validation_all_verified", False)),
            "kis_universe_validation_operational": (direct_development.get("kis") or {}).get("universe_validation_operational"),
            "kis_counts_as_live_evidence": truthy_flag((direct_development.get("kis") or {}).get("counts_as_live_evidence", False)),
        },
        "bithumb": {
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
        "kis": {
            "bridge_status": bridge.get("status"),
            "bridge_generated_at_utc": bridge.get("generated_at_utc"),
            "candidate_id": bridge.get("candidate_id"),
            "bridge_execution_warnings": list(bridge.get("execution_warnings") or []),
            "universe_validation_mode": bridge.get("universe_validation_mode"),
            "universe_validation_verifier_status": bridge.get("universe_validation_verifier_status"),
            "universe_validation_operation_ready": truthy_flag(bridge.get("universe_validation_operation_ready", False)),
            "universe_validation_all_verified": truthy_flag(bridge.get("universe_validation_all_verified", False)),
            "universe_validation_blockers": bridge.get("universe_validation_blockers", []),
            "target_symbol_count": len((bridge.get("target_book") or {}).get("symbols") or []),
            "tiny_live_buyable_symbol_count": (bridge.get("target_book") or {}).get("tiny_live_buyable_symbol_count"),
            "repair_status": kis_repair.get("status"),
            "repair_order_paths_allowed": truthy_flag(kis_repair.get("order_paths_allowed", False)),
            "repair_counts_as_live_evidence": truthy_flag(kis_repair.get("counts_as_live_evidence", False)),
            "repair_buyable_count": kis_repair.get("buyable_count"),
            "repair_quality_status": (kis_repair.get("quality") or {}).get("status"),
            "repair_oos_status": kis_repair_oos.get("status"),
            "repair_oos_order_paths_allowed": truthy_flag(kis_repair_oos.get("order_paths_allowed", False)),
            "repair_oos_counts_as_live_evidence": truthy_flag(kis_repair_oos.get("counts_as_live_evidence", False)),
            "repair_oos_months": kis_repair_oos.get("months"),
            "repair_oos_cagr": (kis_repair_oos.get("summary") or {}).get("CAGR"),
            "repair_oos_mdd": (kis_repair_oos.get("summary") or {}).get("MDD"),
            "repair_oos_sharpe": (kis_repair_oos.get("summary") or {}).get("Sharpe"),
            "repair_oos_holdout_cagr": (kis_repair_oos.get("holdout_30pct") or {}).get("CAGR"),
            "repair_oos_cost_cagr": (kis_repair_oos.get("cost_stress_25bps") or {}).get("CAGR"),
            "repair_oos_pass_folds": (kis_repair_oos.get("walkforward") or {}).get("pass_folds"),
            "repair_oos_folds": (kis_repair_oos.get("walkforward") or {}).get("folds"),
            "order_intent_row_count": kis_order_intent_summary["row_count"],
            "order_intent_submit_allowed_count": kis_order_intent_summary["submit_allowed_count"],
            "order_intent_submit_allowed_symbols": kis_order_intent_summary["submit_allowed_symbols"],
            "order_intent_summary_source": kis_order_intent_summary["source"],
            "universe_validation_operational": kis_universe_operational,
        },
    }
    direct_kis_mode = model_verification["direct_development"]["kis_universe_validation_mode"]
    bridge_kis_mode = model_verification["kis"]["universe_validation_mode"]
    direct_source_bridge = (direct_development.get("kis") or {}).get("source_bridge") or {}
    direct_top_kis = ((direct_development.get("kis") or {}).get("top_variants") or [{}])[0]
    direct_top_parent_candidate_id = direct_top_kis.get("parent_candidate_id")
    model_verification["kis"]["direct_top_parent_candidate_id"] = direct_top_parent_candidate_id
    model_verification["kis"]["bridge_matches_direct_top_parent"] = (
        bridge.get("candidate_id") == direct_top_parent_candidate_id
        if bridge.get("candidate_id") and direct_top_parent_candidate_id
        else None
    )
    model_verification["kis"]["direct_bridge_universe_validation_match"] = (
        direct_kis_mode == bridge_kis_mode
        if direct_kis_mode and bridge_kis_mode
        else None
    )
    model_verification["kis"]["direct_not_older_than_bridge"] = artifact_not_older_than(
        model_verification["kis"]["bridge_generated_at_utc"],
        model_verification["direct_development"]["generated_at_utc"],
    )
    model_verification["kis"]["direct_source_bridge_matches_current"] = (
        direct_source_bridge.get("generated_at_utc") == bridge.get("generated_at_utc")
        and direct_source_bridge.get("candidate_id") == bridge.get("candidate_id")
        and direct_source_bridge.get("universe_validation_mode") == bridge.get("universe_validation_mode")
        if direct_source_bridge.get("generated_at_utc")
        and bridge.get("generated_at_utc")
        and direct_source_bridge.get("candidate_id")
        and bridge.get("candidate_id")
        and direct_source_bridge.get("universe_validation_mode")
        and bridge.get("universe_validation_mode")
        else None
    )
    model_factory_runtime = build_model_factory_runtime_freshness(loops)
    model_factory_cadence = build_model_factory_cadence(model_factory_running or model_factory)
    model_factory_running_contract = build_model_factory_running_contract(model_factory_running)
    model_factory_artifact_schema = build_model_factory_artifact_schema(
        model_factory,
        direct_development,
        bithumb_oos,
        bithumb_robustness,
        model_inventory,
    )

    bithumb_safety = bithumb.get("safety") or {}
    kis_submit_safety = kis_submit.get("safety") or {}
    crypto_effective_cap = (
        bithumb_safety.get("effective_cap_krw")
        or bithumb_safety.get("max_total_krw")
        or policy.get("crypto_cap_krw", policy.get("max_krw", 0))
    )
    stock_effective_cap = kis_submit_safety.get("effective_cap_krw") or policy.get("stock_cap_krw", 0)
    caps = {
        "crypto_cap_krw": float(policy.get("crypto_cap_krw", policy.get("max_krw", 0)) or 0),
        "crypto_effective_cap_krw": float(crypto_effective_cap or 0),
        "crypto_max_daily_loss_krw": float(policy.get("crypto_max_daily_loss_krw", policy.get("max_daily_loss_krw", 0)) or 0),
        "stock_cap_krw": float(policy.get("stock_cap_krw", 0) or 0),
        "stock_effective_cap_krw": float(stock_effective_cap or 0),
        "stock_max_daily_loss_krw": float(policy.get("stock_max_daily_loss_krw", policy.get("max_daily_loss_krw", 0)) or 0),
    }
    bithumb_exposure = float(bithumb.get("current_exposure_krw_estimate", 0) or 0)
    bithumb_realized_pnl = float(orca_event.get("cumulative_realized_pnl_krw", 0) or 0)

    if not all(loop["running"] for loop in loops.values()):
        findings.append("LOOP_NOT_RUNNING")
    if any(log["has_error_text"] for log in logs.values()):
        findings.append("ERROR_TEXT_IN_STDERR")
    if truthy_flag(bithumb.get("global_disable_present")):
        findings.append("BITHUMB_GLOBAL_DISABLE_PRESENT")
    if bithumb_exposure > caps["crypto_effective_cap_krw"]:
        findings.append("BITHUMB_EXPOSURE_CAP_EXCEEDED")
    if -bithumb_realized_pnl > caps["crypto_max_daily_loss_krw"]:
        findings.append("BITHUMB_DAILY_LOSS_CAP_EXCEEDED")
    if not truthy_flag(kis.get("submit_enabled")):
        findings.append("KIS_SUBMIT_NOT_ENABLED")
    if kis.get("execution_warnings") or bridge.get("execution_warnings"):
        findings.append("KIS_EXECUTION_WARNINGS")
    if model_factory.get("status") not in {"TWO_AXIS_MODEL_FACTORY_OK", "UNKNOWN", None}:
        findings.append("MODEL_FACTORY_ATTENTION")
    if model_factory_runtime["process_predates_source"]:
        findings.append("MODEL_FACTORY_PROCESS_PREDATES_SOURCE")
    if not model_factory_running_contract["contract_current"]:
        findings.append("MODEL_FACTORY_RUNNING_CONTRACT_STALE")
    if (
        not model_factory_artifact_schema["direct_kis_validation_fields_present"]
        or not model_factory_artifact_schema["bithumb_source_fields_present"]
        or not model_factory_artifact_schema["kis_inventory_fields_present"]
        or not model_factory_artifact_schema["schema_version_current"]
        or not model_factory_artifact_schema["step_manifest_matches_expected"]
        or not model_factory_artifact_schema["model_only_safety_present"]
        or not model_factory_artifact_schema["model_only_safety_no_order_flags"]
        or not model_factory_artifact_schema["model_only_safety_no_submit"]
    ):
        if model_factory_artifact_schema["stale_scope"] == "loop_summary_only":
            findings.append("MODEL_FACTORY_LOOP_SUMMARY_ONLY_STALE")
        else:
            findings.append("MODEL_FACTORY_ARTIFACT_SUMMARY_SCHEMA_STALE")
    if model_factory_cadence["overdue"]:
        findings.append("MODEL_FACTORY_CYCLE_OVERDUE")
    if not model_only_guardrails["all_known_order_paths_false"]:
        findings.append("MODEL_ONLY_GUARDRAIL_ATTENTION")
    if int(kis_order_intent_summary["submit_allowed_count"] or 0) > 0 and model_only_guardrails["all_known_order_paths_false"]:
        findings.append("KIS_ORDER_INTENT_SUBMIT_ALLOWED_ARTIFACT")
    if model_verification["bithumb"]["robustness_matches_oos_top"] is False:
        findings.append("BITHUMB_OOS_ROBUSTNESS_CANDIDATE_MISMATCH")
    if model_verification["bithumb"]["robustness_source_oos_matches_current"] is False:
        findings.append("BITHUMB_ROBUSTNESS_SOURCE_OOS_MISMATCH")
    if model_verification["bithumb"]["robustness_not_older_than_oos"] is False:
        findings.append("BITHUMB_ROBUSTNESS_OLDER_THAN_OOS")
    if model_verification["bithumb"]["inventory_current_signal_matches_oos_top"] is False:
        findings.append("BITHUMB_CURRENT_SIGNAL_OOS_TOP_MISMATCH")
    if model_verification["kis"]["direct_bridge_universe_validation_match"] is False:
        findings.append("KIS_DIRECT_BRIDGE_UNIVERSE_VALIDATION_MISMATCH")
    if model_verification["kis"]["direct_not_older_than_bridge"] is False:
        findings.append("KIS_DIRECT_DEVELOPMENT_OLDER_THAN_BRIDGE")
    if model_verification["kis"]["direct_source_bridge_matches_current"] is False:
        findings.append("KIS_DIRECT_SOURCE_BRIDGE_MISMATCH")
    if model_verification["kis"]["bridge_matches_direct_top_parent"] is False:
        findings.append("KIS_BRIDGE_DIRECT_TOP_PARENT_MISMATCH")
    if not kis_account:
        findings.append("KIS_ACCOUNT_SNAPSHOT_MISSING")
    if not bithumb_account:
        findings.append("BITHUMB_ACCOUNT_SNAPSHOT_MISSING")
    if int(kis_reconciliation.get("unresolved_order_count", 0) or 0) > 0:
        findings.append("KIS_UNRESOLVED_BROKER_ORDERS")
    if int(bithumb_reconciliation.get("unresolved_order_count", 0) or 0) > 0:
        findings.append("BITHUMB_UNRESOLVED_BROKER_ORDERS")

    finding_groups = classify_findings(findings)

    return {
        "generated_at_utc": utc_now(),
        "status": "HEALTH_OK" if not findings else "HEALTH_ATTENTION",
        "findings": findings,
        "finding_groups": finding_groups,
        "model_development_attention": bool(finding_groups["model_development_or_verification"]),
        "live_runtime_attention": bool(finding_groups["live_runtime_or_account"]),
        "loops": loops,
        "trading": {
            "bithumb": {
                "status": bithumb.get("status"),
                "open_position_count": len(bithumb.get("current_open_positions") or {}),
                "exposure_krw": bithumb_exposure,
                "realized_pnl_krw": bithumb_realized_pnl,
                "realized_return_pct": orca_event.get("cumulative_realized_return_pct"),
                "position_status": orca_state.get("status"),
                "last_reason": (orca_state.get("last_decision") or {}).get("reason") or orca_event.get("last_reason"),
                "new_submitted_order_count": bithumb.get("new_submitted_order_count", 0),
            },
            "kis": {
                "status": kis.get("status"),
                "submit_status": kis_submit.get("status"),
                "submitted_count": kis_submit.get("submitted_count", 0),
                "ledger_submitted_count": len(kis_submitted_ledger),
                "ledger_submitted_notional_krw": kis_ledger_notional,
                "rebalance_status": kis_rebalance.get("status"),
                "rebalance_submitted_count": kis_rebalance.get("submitted_count", 0),
                "execution_warnings": kis.get("execution_warnings", []),
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
        "model_verification": model_verification,
        "model_only_guardrails": model_only_guardrails,
        "model_factory_runtime": model_factory_runtime,
        "model_factory_cadence": model_factory_cadence,
        "model_factory_running_contract": model_factory_running_contract,
        "model_factory_artifact_schema": model_factory_artifact_schema,
        "caps": caps,
        "logs": logs,
        "status_files": {name: str(path) for name, path in STATUS_FILES.items()},
    }


def write_md(report: dict[str, Any]) -> None:
    lines = [
        "# Two Axis Operational Health",
        "",
        f"- Generated UTC: `{report['generated_at_utc']}`",
        f"- Status: `{report['status']}`",
        f"- Findings: `{', '.join(report['findings']) if report['findings'] else 'none'}`",
        f"- Model development/verification findings: `{', '.join(report['finding_groups']['model_development_or_verification']) if report['finding_groups']['model_development_or_verification'] else 'none'}`",
        f"- Live runtime/account findings: `{', '.join(report['finding_groups']['live_runtime_or_account']) if report['finding_groups']['live_runtime_or_account'] else 'none'}`",
        "",
        "## Loops",
        "",
        "| Loop | PID | Running |",
        "|---|---:|---:|",
    ]
    for name, row in report["loops"].items():
        lines.append(f"| {name} | {row['pid'] or '-'} | {row['running']} |")
    lines.extend(
        [
            "",
            "## Trading",
            "",
            f"- Bithumb: `{report['trading']['bithumb']['status']}`, position `{report['trading']['bithumb']['position_status']}`, realized PnL `{report['trading']['bithumb']['realized_pnl_krw']:.2f}` KRW.",
            f"- KIS: `{report['trading']['kis']['status']}`, submit `{report['trading']['kis']['submit_status']}`, latest submitted `{report['trading']['kis']['submitted_count']}`, ledger submitted `{report['trading']['kis']['ledger_submitted_count']}`.",
            f"- Account engine Bithumb: source `{report['account_engine']['bithumb']['snapshot_source']}`, positions `{report['account_engine']['bithumb']['position_count']}`, actionable `{report['account_engine']['bithumb']['actionable_count']}`, unresolved `{report['account_engine']['bithumb']['unresolved_order_count']}`.",
            f"- Account engine KIS: source `{report['account_engine']['kis']['snapshot_source']}`, positions `{report['account_engine']['kis']['position_count']}`, actionable `{report['account_engine']['kis']['actionable_count']}`, unresolved `{report['account_engine']['kis']['unresolved_order_count']}`.",
            f"- Direct development: `{report['model_verification']['direct_development']['status']}`, crypto candidates `{report['model_verification']['direct_development']['crypto_candidate_count']}`, crypto OOS `{report['model_verification']['direct_development']['crypto_oos_pass_count']}`, crypto validated `{report['model_verification']['direct_development']['crypto_validated_pass_count']}`, archive triggered `{report['model_verification']['direct_development']['crypto_archive_signal_triggered_count']}`, top live triggered `{report['model_verification']['direct_development']['crypto_top_live_signal_triggered_count']}`, top live verified `{report['model_verification']['direct_development']['crypto_top_live_signal_all_verified']}`, KIS pass `{report['model_verification']['direct_development']['kis_pass_count']}`.",
            f"- Direct Bithumb live near miss: `{(report['model_verification']['direct_development']['crypto_top_live_near_miss_candidate'] or {}).get('candidate_id') or '-'}`, market `{(report['model_verification']['direct_development']['crypto_top_live_near_miss_candidate'] or {}).get('market') or '-'}`, gap `{(report['model_verification']['direct_development']['crypto_top_live_near_miss_candidate'] or {}).get('nearest_trigger_gap')}`, blockers `{', '.join((report['model_verification']['direct_development']['crypto_top_live_near_miss_candidate'] or {}).get('blocking_conditions') or []) or '-'}`.",
            f"- Direct KIS validation: universe `{report['model_verification']['direct_development']['kis_universe_validation_mode']}`, verifier `{report['model_verification']['direct_development']['kis_universe_validation_verifier_status']}`, operation ready `{report['model_verification']['direct_development']['kis_universe_validation_operation_ready']}`, all verified `{report['model_verification']['direct_development']['kis_universe_validation_all_verified']}`, operational `{report['model_verification']['direct_development']['kis_universe_validation_operational']}`, live evidence `{report['model_verification']['direct_development']['kis_counts_as_live_evidence']}`.",
            f"- Bithumb OOS: `{report['model_verification']['bithumb']['oos_status']}`, pass `{report['model_verification']['bithumb']['oos_pass_count']}/{report['model_verification']['bithumb']['oos_evaluated_count']}`, top `{report['model_verification']['bithumb']['oos_top_candidate_id']}` `{report['model_verification']['bithumb']['oos_top_market']}`, order paths `{report['model_verification']['bithumb']['oos_order_paths_allowed']}`, generated `{report['model_verification']['bithumb']['oos_generated_at']}`.",
            f"- Bithumb current signal scout: generated `{report['model_verification']['bithumb']['inventory_current_signal_generated_at_utc'] or report['model_verification']['bithumb']['inventory_current_signal_generated_at'] or '-'}`, evaluated `{report['model_verification']['bithumb']['inventory_current_signal_evaluated_count']}`, triggered `{report['model_verification']['bithumb']['inventory_current_signal_triggered_count']}`.",
            f"- Bithumb inventory current signal: `{report['model_verification']['bithumb']['inventory_current_signal_candidate_id']}`, inventory OOS top `{report['model_verification']['bithumb']['inventory_oos_top_candidate_id']}`, matches OOS top `{report['model_verification']['bithumb']['inventory_current_signal_matches_oos_top']}`, current signal avg fold CAGR `{report['model_verification']['bithumb']['inventory_current_signal_oos_average_fold_cagr']}`, OOS top avg fold CAGR `{report['model_verification']['bithumb']['inventory_oos_top_average_fold_cagr']}`, current signal trades `{report['model_verification']['bithumb']['inventory_current_signal_oos_trade_count']}`, OOS top trades `{report['model_verification']['bithumb']['inventory_oos_top_trade_count']}`.",
            f"- Bithumb current signal selection: policy `{(report['model_verification']['bithumb']['inventory_current_signal_selection_policy'] or {}).get('description') or '-'}`, rank current `{report['model_verification']['bithumb']['inventory_current_signal_selection_rank']}`, OOS top `{report['model_verification']['bithumb']['inventory_oos_top_signal_selection_rank']}`, estimated CAGR current `{report['model_verification']['bithumb']['inventory_current_signal_selection_estimated_cagr']}`, OOS top `{report['model_verification']['bithumb']['inventory_oos_top_signal_selection_estimated_cagr']}`.",
            f"- Bithumb current signal near miss: `{report['model_verification']['bithumb']['inventory_current_signal_near_miss_candidate_id'] or '-'}`, momentum gap `{report['model_verification']['bithumb']['inventory_current_signal_near_miss_momentum_gap']}`, volume gap `{report['model_verification']['bithumb']['inventory_current_signal_near_miss_volume_gap']}`, blockers `{', '.join(report['model_verification']['bithumb']['inventory_current_signal_near_miss_blocking_conditions']) or '-'}`.",
            f"- Bithumb current signal near miss candidates: `{len(report['model_verification']['bithumb']['inventory_current_signal_near_miss_candidates'])}`.",
            f"- Bithumb direct live near miss: `{report['model_verification']['bithumb']['inventory_direct_top_live_near_miss_candidate_id'] or '-'}`, market `{report['model_verification']['bithumb']['inventory_direct_top_live_near_miss_market'] or '-'}`, momentum gap `{report['model_verification']['bithumb']['inventory_direct_top_live_near_miss_momentum_gap']}`, volume gap `{report['model_verification']['bithumb']['inventory_direct_top_live_near_miss_volume_gap']}`, blockers `{', '.join(report['model_verification']['bithumb']['inventory_direct_top_live_near_miss_blocking_conditions']) or '-'}`.",
            f"- Bithumb robustness: `{report['model_verification']['bithumb']['robustness_status']}`, candidate `{report['model_verification']['bithumb']['robustness_candidate_id']}`, matches OOS top `{report['model_verification']['bithumb']['robustness_matches_oos_top']}`, source OOS matches current `{report['model_verification']['bithumb']['robustness_source_oos_matches_current']}`, not older than OOS `{report['model_verification']['bithumb']['robustness_not_older_than_oos']}`, pass `{report['model_verification']['bithumb']['robustness_pass_count']}/{report['model_verification']['bithumb']['robustness_case_count']}`, cost `{report['model_verification']['bithumb']['robustness_cost_pass_count']}`, order paths `{report['model_verification']['bithumb']['robustness_order_paths_allowed']}`.",
            f"- KIS bridge: `{report['model_verification']['kis']['bridge_status']}`, candidate `{report['model_verification']['kis']['candidate_id']}`, buyable `{report['model_verification']['kis']['tiny_live_buyable_symbol_count']}/{report['model_verification']['kis']['target_symbol_count']}`, warnings `{', '.join(report['model_verification']['kis']['bridge_execution_warnings']) or '-'}`.",
            f"- KIS bridge/direct top match: `{report['model_verification']['kis']['bridge_matches_direct_top_parent']}`, direct top parent `{report['model_verification']['kis']['direct_top_parent_candidate_id']}`.",
            f"- KIS universe validation: `{report['model_verification']['kis']['universe_validation_mode']}`, operational `{report['model_verification']['kis']['universe_validation_operational']}`, verifier `{report['model_verification']['kis']['universe_validation_verifier_status']}`, operation ready `{report['model_verification']['kis']['universe_validation_operation_ready']}`, all verified `{report['model_verification']['kis']['universe_validation_all_verified']}`, blockers `{', '.join(report['model_verification']['kis']['universe_validation_blockers']) or '-'}`.",
            f"- KIS direct/bridge universe validation match: `{report['model_verification']['kis']['direct_bridge_universe_validation_match']}`.",
            f"- KIS direct not older than bridge: `{report['model_verification']['kis']['direct_not_older_than_bridge']}`.",
            f"- KIS direct source bridge matches current: `{report['model_verification']['kis']['direct_source_bridge_matches_current']}`.",
            f"- KIS repair OOS: `{report['model_verification']['kis']['repair_oos_status']}`, CAGR `{report['model_verification']['kis']['repair_oos_cagr']}`, MDD `{report['model_verification']['kis']['repair_oos_mdd']}`, folds `{report['model_verification']['kis']['repair_oos_pass_folds']}/{report['model_verification']['kis']['repair_oos_folds']}`, order paths `{report['model_verification']['kis']['repair_oos_order_paths_allowed']}`.",
            f"- KIS verification order paths: repair `{report['model_verification']['kis']['repair_order_paths_allowed']}`, repair OOS `{report['model_verification']['kis']['repair_oos_order_paths_allowed']}`, live evidence `{report['model_verification']['kis']['repair_counts_as_live_evidence']}`, OOS evidence `{report['model_verification']['kis']['repair_oos_counts_as_live_evidence']}`.",
            f"- KIS order intent artifact: rows `{report['model_verification']['kis']['order_intent_row_count']}`, submit allowed `{report['model_verification']['kis']['order_intent_submit_allowed_count']}`, symbols `{', '.join(report['model_verification']['kis']['order_intent_submit_allowed_symbols']) or '-'}`.",
            f"- Model-only guardrails: all known order paths false `{report['model_only_guardrails']['all_known_order_paths_false']}`, KIS true flags `{', '.join(report['model_only_guardrails']['kis_true_order_path_flags']) or '-'}`.",
            f"- KIS bridge assertions false: `{report['model_only_guardrails']['kis_bridge']['all_order_paths_false']}`.",
            f"- Guardrail source times: `{report['model_only_guardrails']['source_generated_at_utc']}`.",
            f"- Model factory runtime freshness: process predates source `{report['model_factory_runtime']['process_predates_source']}`, process `{report['model_factory_runtime']['process_created_at_utc']}`, source `{report['model_factory_runtime']['source_mtime_utc']}`.",
            f"- Model factory latest artifact freshness: latest not older than source `{report['model_factory_runtime']['latest_json_not_older_than_source']}`, latest `{report['model_factory_runtime']['latest_json_mtime_utc']}`.",
            f"- Model factory cadence: elapsed `{report['model_factory_cadence']['elapsed_seconds']}` seconds, next due `{report['model_factory_cadence']['next_cycle_due_at_utc']}`, overdue `{report['model_factory_cadence']['overdue']}`, seconds overdue `{report['model_factory_cadence']['seconds_overdue']}`.",
            f"- Model factory running contract: schema `{report['model_factory_running_contract']['schema_version']}`, current `{report['model_factory_running_contract']['contract_current']}`, status `{report['model_factory_running_contract']['status']}`, step `{report['model_factory_running_contract']['current_step'] or '-'}`, model-only safety `{report['model_factory_running_contract']['model_only_safety_present']}`.",
            f"- Model factory schema version: `{report['model_factory_artifact_schema']['schema_version']}` expected `{report['model_factory_artifact_schema']['expected_schema_version']}`, current `{report['model_factory_artifact_schema']['schema_version_current']}`, step manifest matches `{report['model_factory_artifact_schema']['step_manifest_matches_expected']}`, model-only safety present `{report['model_factory_artifact_schema']['model_only_safety_present']}`, no order flags `{report['model_factory_artifact_schema']['model_only_safety_no_order_flags']}`, no submit `{report['model_factory_artifact_schema']['model_only_safety_no_submit']}`, stale scope `{report['model_factory_artifact_schema']['stale_scope']}`, stale reasons `{', '.join(report['model_factory_artifact_schema']['stale_reasons']) or '-'}`.",
            f"- Model factory artifact schema: direct KIS fields present `{report['model_factory_artifact_schema']['direct_kis_validation_fields_present']}`, missing `{', '.join(report['model_factory_artifact_schema']['missing_direct_development_fields']) or '-'}`; Bithumb source fields present `{report['model_factory_artifact_schema']['bithumb_source_fields_present']}`, missing `{', '.join(report['model_factory_artifact_schema']['missing_bithumb_fields']) or '-'}`; KIS inventory fields present `{report['model_factory_artifact_schema']['kis_inventory_fields_present']}`, missing `{', '.join(report['model_factory_artifact_schema']['missing_kis_inventory_fields']) or '-'}`.",
            f"- Canonical child artifacts: complete `{report['model_factory_artifact_schema']['canonical_child_artifacts_complete']}`, direct fields present `{report['model_factory_artifact_schema']['canonical_direct_development_fields_present']}`, missing direct fields `{', '.join(report['model_factory_artifact_schema']['canonical_missing_direct_development_fields']) or '-'}`, Bithumb sources present `{report['model_factory_artifact_schema']['canonical_bithumb_sources_present']}`, KIS inventory sources present `{report['model_factory_artifact_schema']['canonical_kis_inventory_sources_present']}`.",
            "",
            "## Logs",
            "",
        ]
    )
    for name, row in report["logs"].items():
        lines.append(f"- `{name}`: length `{row['length']}`, has_error_text `{row['has_error_text']}`")
    atomic_write_text(OUT_MD, "\n".join(lines))


def main() -> None:
    report = build_report()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_text(OUT_JSON, json.dumps(report, indent=2, ensure_ascii=False))
    write_md(report)
    print(json.dumps({"status": report["status"], "findings": report["findings"], "json": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
