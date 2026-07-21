from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\AI")
REPORT_JSON = ROOT / "reports/operations/workspace_cleanup_plan_latest.json"
REPORT_MD = ROOT / "reports/operations/workspace_cleanup_plan_latest.md"

PROTECTED_PATHS = [
    "overnight_runs/DISABLE_DUAL_REPO_RESEARCH_LOOP",
    "overnight_runs/latest_run_summary.json",
    "overnight_runs/small_autotrade_activation_packet_latest.json",
    "overnight_runs/small_account_risk_budget_latest.json",
    "ops/runstate/kill_switch.json",
    "research_lane_stage1/latest",
    "research_lane_stage2/latest",
    "research_lane_stage3/latest",
    "reports/operations/pipeline_direct_recheck_latest.json",
    "reports/operations/pipeline_direct_blocker_packet_latest.json",
    "reports/operations/pipeline_direct_next_command_latest.json",
    "reports/operations/pipeline_blocked_runtime_safety_snapshot_latest.json",
]

CLEANED_PATHS = [
    "reports/operations/runs",
    "logs",
    "__pycache__",
    ".pytest_cache",
    "overnight_runs/*stdout*",
]

ARCHIVE_CANDIDATE_POLICIES = {
    "Crypto/analysis_results": {
        "store_role": "active_crypto_research_outputs",
        "retention_requirement": "preserve_latest_and_candidate_linked_outputs_before_archive",
        "recommended_action": "archive_policy_required_no_direct_delete",
    },
    "research_lane_stage2/runs": {
        "store_role": "conversion_lane_run_evidence",
        "retention_requirement": "preserve_latest_ranked_variants_and_preserved_sources_before_archive",
        "recommended_action": "archive_policy_required_no_direct_delete",
    },
    "gatekeeper/artifacts/candidate_events_latest.jsonl": {
        "store_role": "gatekeeper_event_log",
        "retention_requirement": "snapshot_or_compact_with_replay_verification_before_archive",
        "recommended_action": "compact_or_archive_policy_required_no_direct_delete",
    },
    "gatekeeper/gatekeeper.sqlite": {
        "store_role": "gatekeeper_database",
        "retention_requirement": "backup_and_integrity_check_required_before_archive",
        "recommended_action": "backup_policy_required_no_direct_delete",
    },
    "research_lane_stage1/runs": {
        "store_role": "research_lane_run_evidence",
        "retention_requirement": "preserve_latest_top_candidates_and_conversion_queue_before_archive",
        "recommended_action": "archive_policy_required_no_direct_delete",
    },
    "overnight_runs": {
        "store_role": "runtime_handoff_history",
        "retention_requirement": "preserve_latest_summary_activation_packet_risk_budget_and_disable_guard",
        "recommended_action": "retention_limit_policy_required_no_direct_delete",
    },
    "reports/operations/runs": {
        "store_role": "cleaned_duplicate_timestamped_operation_reports",
        "retention_requirement": "keep_empty_or_latest_only",
        "recommended_action": "already_cleaned_keep_empty",
    },
    "logs": {
        "store_role": "cleaned_stale_console_logs",
        "retention_requirement": "keep_empty_until_new_active_run",
        "recommended_action": "already_cleaned_keep_empty",
    },
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def path_stats(path: Path) -> dict:
    if not path.exists():
        return {
            "path": rel(path) if path != ROOT else str(path),
            "type": "missing",
            "exists": False,
            "file_count": 0,
            "mb": 0.0,
            "bytes": 0,
        }
    if path.is_file():
        size = path.stat().st_size
        return {
            "path": rel(path),
            "type": "file",
            "exists": True,
            "file_count": 1,
            "mb": round(size / 1024 / 1024, 4),
            "bytes": size,
        }
    file_count = 0
    size = 0
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            file_path = Path(dirpath) / filename
            try:
                size += file_path.stat().st_size
                file_count += 1
            except OSError:
                continue
    return {
        "path": rel(path),
        "type": "dir",
        "exists": True,
        "file_count": file_count,
        "mb": round(size / 1024 / 1024, 2),
        "bytes": size,
    }


def suffix_counts(files: list[Path]) -> dict:
    counts: dict[str, int] = {}
    for path in files:
        suffix = path.suffix.lower() or "<none>"
        counts[suffix] = counts.get(suffix, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def build_plan() -> dict:
    top_level = sorted((path_stats(p) for p in ROOT.iterdir()), key=lambda row: row["mb"], reverse=True)
    root_files = [p for p in ROOT.iterdir() if p.is_file()]
    root_py = sorted(p.name for p in root_files if p.suffix.lower() == ".py")
    archive_candidates = [
        path_stats(ROOT / "Crypto/analysis_results"),
        path_stats(ROOT / "research_lane_stage2/runs"),
        path_stats(ROOT / "gatekeeper/artifacts/candidate_events_latest.jsonl"),
        path_stats(ROOT / "gatekeeper/gatekeeper.sqlite"),
        path_stats(ROOT / "research_lane_stage1/runs"),
        path_stats(ROOT / "overnight_runs"),
        path_stats(ROOT / "reports/operations/runs"),
        path_stats(ROOT / "logs"),
    ]
    for row in archive_candidates:
        row.update(ARCHIVE_CANDIDATE_POLICIES.get(row["path"], {}))
    protected = [{"path": p, "exists": (ROOT / p).exists()} for p in PROTECTED_PATHS]
    cleaned = [{"path": p, "exists": bool(list(ROOT.glob(p)))} for p in CLEANED_PATHS]
    total_file_count = sum(row["file_count"] for row in top_level)
    total_size = sum(row["bytes"] for row in top_level)
    return {
        "schema_version": "1.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(ROOT),
        "purpose": "Current non-destructive cleanup map for C:\\AI after duplicate report/log/cache cleanup.",
        "safety_policy": {
            "delete_now": "none",
            "move_now": "none",
            "paper_enabled_change": "forbidden",
            "live_enabled_change": "forbidden",
            "broker_submit_change": "forbidden",
            "do_not_delete_paths": PROTECTED_PATHS,
        },
        "current_totals": {
            "file_count": total_file_count,
            "bytes": total_size,
            "gb": round(total_size / 1024 / 1024 / 1024, 3),
        },
        "top_level_largest": top_level[:30],
        "root_files": {
            "total_root_files": len(root_files),
            "suffix_counts": suffix_counts(root_files),
            "root_py_total": len(root_py),
            "root_py_samples": root_py[:40],
        },
        "protected_path_status": protected,
        "recently_cleaned_path_status": cleaned,
        "archive_candidates": archive_candidates,
        "single_next_action": "Do not delete active evidence stores directly; next cleanup requires an explicit archive/retention policy for Crypto analysis_results, research_lane_stage2/runs, and gatekeeper stores.",
    }


def render_md(plan: dict) -> str:
    lines = [
        "# Workspace Cleanup Plan",
        "",
        f"- generated_at_utc: `{plan['generated_at_utc']}`",
        f"- root: `{plan['root']}`",
        f"- current_files: `{plan['current_totals']['file_count']}`",
        f"- current_gb: `{plan['current_totals']['gb']}`",
        "- delete_now: `none`",
        "- move_now: `none`",
        f"- single_next_action: {plan['single_next_action']}",
        "",
        "## Largest Top-Level Areas",
        "",
        "| path | type | files | MB |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in plan["top_level_largest"][:15]:
        lines.append(f"| `{row['path']}` | {row['type']} | {row['file_count']} | {row['mb']} |")
    lines.extend(["", "## Archive Candidates", "", "| path | files | MB | exists |", "| --- | ---: | ---: | --- |"])
    for row in plan["archive_candidates"]:
        lines.append(f"| `{row['path']}` | {row['file_count']} | {row['mb']} | {row['exists']} |")
    lines.extend(["", "## Do Not Delete", ""])
    for row in plan["protected_path_status"]:
        lines.append(f"- `{row['path']}` exists=`{row['exists']}`")
    lines.extend(["", "## Recently Cleaned Paths", ""])
    for row in plan["recently_cleaned_path_status"]:
        lines.append(f"- `{row['path']}` exists_or_matches=`{row['exists']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    plan = build_plan()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(plan), encoding="utf-8")
    print(json.dumps({"status": "PASS", "current_gb": plan["current_totals"]["gb"], "latest_json": str(REPORT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
