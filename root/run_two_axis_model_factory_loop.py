from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parent
MOMENTUM_ROOT = ROOT / "momentum"
OPS_DIR = ROOT / "ops" / "model_factory_loop"
LATEST_JSON = OPS_DIR / "two_axis_model_factory_loop_latest.json"
RUNNING_JSON = OPS_DIR / "two_axis_model_factory_loop_running.json"
HISTORY_JSONL = OPS_DIR / "two_axis_model_factory_loop_history.jsonl"
SCHEMA_VERSION = 2
FORBIDDEN_ORDER_FLAGS = {"--submit", "--live", "--paper", "--private-submit", "--broker-submit"}
FORBIDDEN_ORDER_SCRIPT_PATTERNS = {
    "order_submit",
    "broker_submit",
    "private_submit",
    "submit_order",
    "live_order",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    tmp_path.replace(path)


def write_running(payload: dict[str, Any]) -> None:
    write_json(RUNNING_JSON, payload)


def truthy_flag(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def step_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_step(
    label: str,
    command: list[str],
    cwd: Path,
    *,
    timeout_seconds: int,
    cycle_started_at_utc: str,
    step_index: int,
    step_count: int,
    update_running: bool = True,
    running_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = utc_now()
    if update_running:
        running_payload = {
            "generated_at_utc": started,
            "status": "TWO_AXIS_MODEL_FACTORY_RUNNING",
            "cycle_started_at_utc": cycle_started_at_utc,
            "current_step": label,
            "step_index": step_index,
            "step_count": step_count,
            "timeout_seconds": timeout_seconds,
            "command": command,
            "cwd": str(cwd),
        }
        if running_extra:
            running_payload.update(running_extra)
        write_running(running_payload)
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=step_env(),
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "command": command,
            "cwd": str(cwd),
            "started_at_utc": started,
            "finished_at_utc": utc_now(),
            "returncode": None,
            "ok": False,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
            "stdout_tail": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-3000:] if isinstance(exc.stderr, str) else "",
        }
    return {
        "label": label,
        "command": command,
        "cwd": str(cwd),
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "returncode": result.returncode,
        "ok": result.returncode == 0,
        "timed_out": False,
        "timeout_seconds": timeout_seconds,
        "stdout_tail": result.stdout[-3000:],
        "stderr_tail": result.stderr[-3000:],
    }


def write_latest(payload: dict[str, Any]) -> None:
    write_json(LATEST_JSON, payload)


def build_step_manifest(step_defs: list[tuple[str, list[str], Path]]) -> list[dict[str, Any]]:
    return [
        {
            "index": index,
            "label": label,
            "command": command,
            "cwd": str(cwd),
        }
        for index, (label, command, cwd) in enumerate(step_defs, start=1)
    ]


def build_model_only_safety(step_manifest: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_hits = []
    forbidden_script_hits = []
    for row in step_manifest:
        command = row.get("command") if isinstance(row, dict) else []
        if not isinstance(command, list):
            continue
        hits = sorted(flag for flag in FORBIDDEN_ORDER_FLAGS if flag in command)
        if hits:
            forbidden_hits.append(
                {
                    "label": row.get("label"),
                    "forbidden_flags": hits,
                }
            )
        script_hits = sorted(
            pattern
            for arg in command
            for pattern in FORBIDDEN_ORDER_SCRIPT_PATTERNS
            if pattern in str(arg).replace("\\", "/").lower()
        )
        if script_hits:
            forbidden_script_hits.append(
                {
                    "label": row.get("label"),
                    "forbidden_script_patterns": sorted(set(script_hits)),
                }
            )
    return {
        "mode": "model_development_and_verification_only",
        "forbidden_order_flags": sorted(FORBIDDEN_ORDER_FLAGS),
        "forbidden_order_script_patterns": sorted(FORBIDDEN_ORDER_SCRIPT_PATTERNS),
        "forbidden_order_flag_hits": forbidden_hits,
        "forbidden_order_script_hits": forbidden_script_hits,
        "command_manifest_has_no_order_flags": not forbidden_hits and not forbidden_script_hits,
        "order_submission_allowed_by_this_loop": False,
        "broker_submit_allowed_by_this_loop": False,
        "real_orders_allowed_by_this_loop": False,
    }


def build_steps() -> list[tuple[str, list[str], Path]]:
    return [
        ("bithumb parameter sweep", [sys.executable, str(ROOT / "build_bithumb_current_actionable_parameter_sweep.py")], ROOT),
        ("bithumb oos verification", [sys.executable, str(ROOT / "build_bithumb_current_actionable_oos_walkforward.py")], ROOT),
        ("bithumb robustness stress", [sys.executable, str(ROOT / "build_bithumb_current_actionable_robustness_stress.py")], ROOT),
        ("bithumb nonzero signal scout", [sys.executable, str(ROOT / "build_bithumb_current_actionable_nonzero_signal_scout.py")], ROOT),
        ("stock split model pipeline", [sys.executable, "tools/pipelines/run_split_models_pipeline.py"], MOMENTUM_ROOT),
        ("stock operational conversion", [sys.executable, "tools/analysis/refresh_split_models_operational_conversion_state.py"], MOMENTUM_ROOT),
        ("stock operating candidate bridge", [sys.executable, str(ROOT / "build_stock_etf_operating_candidate_bridge.py"), "--format", "text"], ROOT),
        ("two axis direct model development", [sys.executable, str(ROOT / "build_two_axis_direct_model_development.py"), "--max-markets", "10", "--max-evaluations", "2880", "--format", "json"], ROOT),
        ("two axis inventory", [sys.executable, str(ROOT / "build_two_axis_model_inventory.py")], ROOT),
        ("dashboard refresh", [sys.executable, str(ROOT / "build_simple_pipeline_dashboard.py")], ROOT),
    ]


def summarize_no_order_assertions(payload: dict[str, Any]) -> dict[str, Any]:
    assertions = payload.get("no_order_assertions")
    if not isinstance(assertions, dict):
        return {
            "present": False,
            "all_order_paths_false": False,
            "true_flags": [],
        }
    true_flags = sorted(key for key, value in assertions.items() if truthy_flag(value))
    return {
        "present": True,
        "all_order_paths_false": not true_flags,
        "true_flags": true_flags,
    }


def kis_universe_validation_is_operational(mode: object) -> bool:
    normalized = str(mode or "").strip().lower()
    return normalized == "daily_close_presence"


def build_artifact_summary() -> dict[str, Any]:
    direct = read_json(ROOT / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json")
    inventory = read_json(ROOT / "reports" / "operations" / "two_axis_model_inventory_latest.json")
    oos = read_json(ROOT / "reports" / "model_factory" / "bithumb_current_actionable_oos_walkforward_latest.json")
    stress = read_json(ROOT / "reports" / "model_factory" / "bithumb_current_actionable_robustness_stress_latest.json")
    scout = read_json(ROOT / "reports" / "operations" / "bithumb_current_actionable_nonzero_signal_scout_latest.json")
    kis_bridge = read_json(ROOT / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_candidate_bridge_latest.json")

    axes = inventory.get("axes", {}) if isinstance(inventory.get("axes"), dict) else {}
    bithumb = axes.get("BITHUMB_KRW", {}) if isinstance(axes.get("BITHUMB_KRW"), dict) else {}
    kis = axes.get("KIS_COMBINED_KRW", {}) if isinstance(axes.get("KIS_COMBINED_KRW"), dict) else {}
    bithumb_verification_sources = bithumb.get("verification_sources") or {}
    kis_verification_sources = kis.get("verification_sources") or {}
    kis_repair = kis_bridge.get("tiny_live_executable_repair") or {}
    kis_repair_oos = kis_repair.get("historical_oos_validation") or {}
    direct_guard = summarize_no_order_assertions(direct)
    oos_guard = summarize_no_order_assertions(oos)
    stress_guard = summarize_no_order_assertions(stress)
    kis_bridge_guard = summarize_no_order_assertions(kis_bridge)
    kis_order_path_flags = {
        "source_order_paths_allowed": truthy_flag(kis_bridge.get("source_order_paths_allowed", False)),
        "repair_order_paths_allowed": truthy_flag(kis_repair.get("order_paths_allowed", False)),
        "repair_counts_as_live_evidence": truthy_flag(kis_repair.get("counts_as_live_evidence", False)),
        "repair_oos_order_paths_allowed": truthy_flag(kis_repair_oos.get("order_paths_allowed", False)),
        "repair_oos_counts_as_live_evidence": truthy_flag(kis_repair_oos.get("counts_as_live_evidence", False)),
    }
    kis_true_order_path_flags = sorted(key for key, value in kis_order_path_flags.items() if value)
    kis_order_intent_submit_allowed_count = (kis_bridge.get("current_data") or {}).get("order_intent_submit_allowed_count")
    kis_universe_operational = kis_universe_validation_is_operational(kis_bridge.get("universe_validation_mode"))
    all_known_order_paths_false = (
        direct_guard["all_order_paths_false"]
        and oos_guard["all_order_paths_false"]
        and stress_guard["all_order_paths_false"]
        and kis_bridge_guard["all_order_paths_false"]
        and not kis_true_order_path_flags
    )

    return {
        "model_only_guardrails": {
            "source_generated_at_utc": {
                "direct_development": direct.get("generated_at_utc"),
                "bithumb_oos": oos.get("generated_at") or oos.get("generated_at_utc"),
                "bithumb_robustness": stress.get("generated_at") or stress.get("generated_at_utc"),
                "bithumb_signal_scout": first_present(scout.get("generated_at_utc"), scout.get("generated_at")),
                "kis_bridge": kis_bridge.get("generated_at_utc"),
            },
            "direct_development": direct_guard,
            "bithumb_oos": oos_guard,
            "bithumb_robustness": stress_guard,
            "kis_bridge": kis_bridge_guard,
            "kis_order_path_flags": kis_order_path_flags,
            "kis_all_order_paths_false": not kis_true_order_path_flags,
            "kis_true_order_path_flags": kis_true_order_path_flags,
            "kis_order_intent_submit_allowed_count": kis_order_intent_submit_allowed_count,
            "kis_universe_validation_operational": kis_universe_operational,
            "all_known_order_paths_false": all_known_order_paths_false,
            "model_only_attention": (
                not all_known_order_paths_false
                or int(kis_order_intent_submit_allowed_count or 0) > 0
                or not kis_universe_operational
            ),
        },
        "direct_development": {
            "status": direct.get("status"),
            "generated_at_utc": direct.get("generated_at_utc"),
            "crypto_candidate_count": (direct.get("crypto") or {}).get("candidate_count"),
            "crypto_oos_pass_count": (direct.get("crypto") or {}).get("oos_pass_count"),
            "crypto_validated_pass_count": (direct.get("crypto") or {}).get("validated_pass_count"),
            "crypto_archive_signal_triggered_count": (direct.get("crypto") or {}).get("archive_signal_triggered_count"),
            "crypto_top_live_signal_triggered_count": (direct.get("crypto") or {}).get("top_live_signal_triggered_count"),
            "crypto_top_live_signal_all_verified": ((direct.get("crypto") or {}).get("top_live_signal_summary") or {}).get("all_live_verified"),
            "crypto_top_live_near_miss_candidate": (direct.get("crypto") or {}).get("top_live_near_miss_candidate"),
            "crypto_validated_market_count": (direct.get("crypto") or {}).get("validated_market_count"),
            "crypto_validated_markets": (direct.get("crypto") or {}).get("validated_markets"),
            "kis_variant_count": (direct.get("kis") or {}).get("conversion_variant_count"),
            "kis_pass_count": (direct.get("kis") or {}).get("pass_count"),
            "kis_source_bridge": (direct.get("kis") or {}).get("source_bridge"),
            "kis_universe_validation_mode": (direct.get("kis") or {}).get("universe_validation_mode"),
            "kis_universe_validation_verifier_status": (direct.get("kis") or {}).get("universe_validation_verifier_status"),
            "kis_universe_validation_operation_ready": truthy_flag((direct.get("kis") or {}).get("universe_validation_operation_ready", False)),
            "kis_universe_validation_all_verified": truthy_flag((direct.get("kis") or {}).get("universe_validation_all_verified", False)),
            "kis_universe_validation_operational": (direct.get("kis") or {}).get("universe_validation_operational"),
            "kis_counts_as_live_evidence": truthy_flag((direct.get("kis") or {}).get("counts_as_live_evidence", False)),
        },
        "bithumb": {
            "oos_status": oos.get("status"),
            "oos_generated_at": oos.get("generated_at") or oos.get("generated_at_utc"),
            "oos_top_candidate_id": (oos.get("top_oos") or {}).get("candidate_id"),
            "oos_top_market": (oos.get("top_oos") or {}).get("market"),
            "oos_candidate_count": oos.get("candidate_count"),
            "oos_pass_count": (oos.get("aggregate") or {}).get("pass_count"),
            "robustness_status": stress.get("status"),
            "robustness_generated_at": stress.get("generated_at") or stress.get("generated_at_utc"),
            "robustness_source_oos": stress.get("source_oos"),
            "robustness_candidate_id": stress.get("candidate_id"),
            "robustness_pass_count": stress.get("pass_count"),
            "robustness_cost_pass_count": stress.get("cost_pass_count"),
            "signal_scout_status": scout.get("status"),
            "signal_scout_generated_at": first_present(scout.get("generated_at_utc"), scout.get("generated_at")),
            "signal_scout_evaluated_count": first_present(scout.get("evaluated_count"), scout.get("evaluated_candidate_count")),
            "signal_scout_triggered_count": first_present(scout.get("triggered_count"), scout.get("triggered_candidate_count")),
            "signal_scout_top_near_miss": first_present(scout.get("top_near_miss"), scout.get("top_near_miss_candidate")),
            "inventory_current_signal_candidate_id": bithumb_verification_sources.get("current_signal_candidate_id"),
            "inventory_current_signal_matches_oos_top": bithumb_verification_sources.get("current_signal_matches_oos_top"),
            "inventory_oos_top_candidate_id": bithumb_verification_sources.get("oos_top_candidate_id"),
            "inventory_current_signal_selection_policy": bithumb_verification_sources.get("current_signal_selection_policy"),
            "inventory_current_signal_selection_summary": bithumb_verification_sources.get("current_signal_selection_summary"),
            "inventory_oos_top_signal_selection_summary": bithumb_verification_sources.get("oos_top_signal_selection_summary"),
            "inventory_current_signal_top_near_miss": bithumb_verification_sources.get("current_signal_top_near_miss"),
            "inventory_current_signal_top_near_miss_candidates": bithumb_verification_sources.get(
                "current_signal_top_near_miss_candidates"
            ),
            "inventory_direct_top_live_near_miss_candidate": bithumb_verification_sources.get("direct_crypto_top_live_near_miss_candidate"),
            "inventory_current_signal_oos_summary": bithumb_verification_sources.get("current_signal_oos_summary"),
            "inventory_oos_top_summary": bithumb_verification_sources.get("oos_top_summary"),
            "inventory_counts": bithumb.get("counts", {}),
        },
        "kis": {
            "bridge_status": kis_bridge.get("status"),
            "candidate_id": kis_bridge.get("candidate_id"),
            "universe_validation_mode": kis_bridge.get("universe_validation_mode"),
            "universe_validation_operational": kis_universe_operational,
            "target_book_rows": (kis_bridge.get("current_data") or {}).get("target_book_rows"),
            "target_symbols": (kis_bridge.get("target_book") or {}).get("symbols", []),
            "tiny_live_buyable_symbol_count": (kis_bridge.get("target_book") or {}).get("tiny_live_buyable_symbol_count"),
            "tiny_live_repair_status": kis_repair.get("status"),
            "tiny_live_repair_buyable_count": kis_repair.get("buyable_count"),
            "tiny_live_repair_symbols": kis_repair.get("candidate_symbols", []),
            "tiny_live_repair_oos_status": kis_repair_oos.get("status"),
            "tiny_live_repair_oos_cagr": (kis_repair_oos.get("summary") or {}).get("CAGR"),
            "tiny_live_repair_oos_mdd": (kis_repair_oos.get("summary") or {}).get("MDD"),
            "tiny_live_repair_oos_holdout_cagr": (kis_repair_oos.get("holdout_30pct") or {}).get("CAGR"),
            "order_intent_rows": (kis_bridge.get("current_data") or {}).get("order_intent_rows"),
            "order_intent_submit_allowed_count": kis_order_intent_submit_allowed_count,
            "order_intent_submit_allowed_symbols": (kis_bridge.get("current_data") or {}).get("order_intent_submit_allowed_symbols", []),
            "blockers": kis_bridge.get("blockers", []),
            "execution_warnings": kis_bridge.get("execution_warnings", []),
            "inventory_counts": kis.get("counts", {}),
        },
    }


def append_history(payload: dict[str, Any]) -> None:
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_once(*, step_timeout_seconds: int, update_running: bool = True) -> dict[str, Any]:
    cycle_started = utc_now()
    step_defs = build_steps()
    step_manifest = build_step_manifest(step_defs)
    model_only_safety = build_model_only_safety(step_manifest)
    steps = []
    for index, (label, command, cwd) in enumerate(step_defs, start=1):
        steps.append(
            run_step(
                label,
                command,
                cwd,
                timeout_seconds=step_timeout_seconds,
                cycle_started_at_utc=cycle_started,
                step_index=index,
                step_count=len(step_defs),
                update_running=update_running,
                running_extra={
                    "schema_version": SCHEMA_VERSION,
                    "model_only_safety": model_only_safety,
                    "step_manifest": step_manifest,
                },
            )
        )
        if not steps[-1]["ok"]:
            break

    next_status = "TWO_AXIS_MODEL_FACTORY_OK" if all(step["ok"] for step in steps) and len(steps) == len(step_defs) else "TWO_AXIS_MODEL_FACTORY_ATTENTION"
    artifact_summary = build_artifact_summary()
    next_due = None
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "cycle_started_at_utc": cycle_started,
        "status": next_status,
        "model_only_safety": model_only_safety,
        "step_manifest": step_manifest,
        "steps": steps,
        "ok_count": sum(1 for step in steps if step["ok"]),
        "error_count": sum(1 for step in steps if not step["ok"]),
        "completed_step_count": len(steps),
        "planned_step_count": len(step_defs),
        "step_timeout_seconds": step_timeout_seconds,
        "artifact_summary": artifact_summary,
        "latest_json": str(LATEST_JSON),
        "running_json": str(RUNNING_JSON),
        "history_jsonl": str(HISTORY_JSONL),
    }
    write_latest(payload)
    append_history(payload)
    if update_running:
        write_running(
            {
                "schema_version": SCHEMA_VERSION,
                "generated_at_utc": payload["generated_at_utc"],
                "status": next_status,
                "model_only_safety": model_only_safety,
                "cycle_started_at_utc": cycle_started,
                "current_step": None,
                "completed_step_count": len(steps),
                "planned_step_count": len(step_defs),
                "step_manifest": step_manifest,
                "next_cycle_due_at_utc": next_due,
                "latest_json": str(LATEST_JSON),
            }
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=1800)
    parser.add_argument("--step-timeout-seconds", type=int, default=900)
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    while True:
        payload = run_once(step_timeout_seconds=max(60, int(args.step_timeout_seconds)), update_running=bool(args.loop))
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"status={payload['status']} ok={payload['ok_count']} errors={payload['error_count']}")
        if not args.loop:
            return 0
        due_epoch = time.time() + max(300, int(args.interval_seconds))
        due = datetime.fromtimestamp(due_epoch, timezone.utc).isoformat()
        running = read_json(RUNNING_JSON)
        running["next_cycle_due_at_utc"] = due
        write_running(running)
        time.sleep(max(300, int(args.interval_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
