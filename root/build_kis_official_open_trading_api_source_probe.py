from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract

KST = ZoneInfo("Asia/Seoul")
OFFICIAL_REPO_URL = "https://github.com/koreainvestment/open-trading-api"
DEFAULT_REPO = ROOT / "external_sources/open-trading-api"
REPORT_JSON = ROOT / "reports/operations/kis_official_open_trading_api_source_probe_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_official_open_trading_api_source_probe_latest.md"
SAFETY = intake_contract.SAFETY

CURRENT_MASTER_URL_FAMILIES = {
    "kis_korea_stocks": [
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
        "https://new.real.download.dws.co.kr/common/master/konex_code.mst.zip",
    ],
    "kis_korea_etfs": [
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
    ],
    "kis_us_stocks": [
        "https://new.real.download.dws.co.kr/common/master/nasmst.cod.zip",
        "https://new.real.download.dws.co.kr/common/master/nysmst.cod.zip",
        "https://new.real.download.dws.co.kr/common/master/amsmst.cod.zip",
    ],
    "kis_us_etfs": [
        "https://new.real.download.dws.co.kr/common/master/nasmst.cod.zip",
        "https://new.real.download.dws.co.kr/common/master/nysmst.cod.zip",
        "https://new.real.download.dws.co.kr/common/master/amsmst.cod.zip",
    ],
}


def _stocks_info_files(repo: Path) -> list[dict[str, object]]:
    stocks_info = repo / "stocks_info"
    if not stocks_info.exists():
        return []
    return [
        {"name": path.name, "size_bytes": path.stat().st_size}
        for path in sorted(stocks_info.iterdir(), key=lambda p: p.name.lower())
        if path.is_file()
    ]


def _git_history(repo: Path) -> dict[str, object]:
    git_dir = repo / ".git"
    if not git_dir.exists():
        return {"commit_count_touching_stocks_info": 0, "earliest_commit_date": "", "latest_commit_date": "", "recent_commits": []}
    try:
        count = subprocess.check_output(
            ["git", "-C", str(repo), "rev-list", "--count", "HEAD", "--", "stocks_info"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).strip()
        log = subprocess.check_output(
            ["git", "-C", str(repo), "log", "--date=short", "--pretty=%H%x09%ad%x09%s", "--", "stocks_info"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).splitlines()
    except (subprocess.SubprocessError, OSError):
        return {"commit_count_touching_stocks_info": 0, "earliest_commit_date": "", "latest_commit_date": "", "recent_commits": []}
    commits = []
    for line in log[:12]:
        parts = line.split("\t", 2)
        if len(parts) == 3:
            commits.append({"commit": parts[0], "date": parts[1], "subject": parts[2]})
    dates = [row["date"] for row in commits]
    return {
        "commit_count_touching_stocks_info": int(count or 0),
        "earliest_commit_date": log[-1].split("\t", 2)[1] if log else "",
        "latest_commit_date": dates[0] if dates else "",
        "recent_commits": commits,
    }


def _axis_reports() -> list[dict[str, object]]:
    return [
        {
            "axis": "kis_korea_stocks",
            "official_current_master_available": True,
            "historical_pit_membership_available": False,
            "survivorship_free_delisted_history_available": False,
            "replacement_worklist_operation_ready": False,
            "usable_for": ["current master sanity check", "symbol parser reference"],
            "not_usable_for": ["axis-wide point-in-time membership replacement", "survivorship-free delisted row recovery"],
        },
        {
            "axis": "kis_korea_etfs",
            "official_current_master_available": True,
            "historical_pit_membership_available": False,
            "survivorship_free_delisted_history_available": False,
            "replacement_worklist_operation_ready": False,
            "usable_for": ["current ETP flag sanity check"],
            "not_usable_for": ["axis-wide point-in-time ETF membership replacement"],
        },
        {
            "axis": "kis_us_stocks",
            "official_current_master_available": True,
            "historical_pit_membership_available": False,
            "survivorship_free_delisted_history_available": False,
            "replacement_worklist_operation_ready": False,
            "usable_for": ["current overseas stock master sanity check"],
            "not_usable_for": ["US historical listing intervals", "delisted symbol recovery"],
        },
        {
            "axis": "kis_us_etfs",
            "official_current_master_available": True,
            "historical_pit_membership_available": False,
            "survivorship_free_delisted_history_available": False,
            "replacement_worklist_operation_ready": False,
            "usable_for": ["current overseas ETP type sanity check"],
            "not_usable_for": ["US ETF historical listing intervals", "delisted ETF recovery"],
        },
    ]


def build_report(generated_at: str | None = None, repo: Path = DEFAULT_REPO) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    files = _stocks_info_files(repo)
    license_file_exists = any((repo / name).exists() for name in ("LICENSE", "LICENSE.md", "COPYING"))
    blockers = [
        "official_repo_samples_are_current_master_downloaders_not_historical_pit_membership",
        "official_repo_does_not_provide_survivorship_free_delisted_membership_history",
        "operation_ready_replacement_rows_remain_zero",
    ]
    if not license_file_exists:
        blockers.append("official_repo_has_no_license_file_for_code_copying")
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": "REVIEW_ONLY_NOT_OPERATION_READY_FOR_AXIS_WIDE_PIT",
        "operation_ready": False,
        "official_repo_url": OFFICIAL_REPO_URL,
        "local_repo_path": str(repo),
        "license_file_exists": license_file_exists,
        "stocks_info_file_count": len(files),
        "stocks_info_files": files,
        "stocks_info_git_history": _git_history(repo),
        "current_master_url_families": CURRENT_MASTER_URL_FAMILIES,
        "axis_reports": _axis_reports(),
        "accepted_for_replacement_worklist_fill": False,
        "operation_ready_replacement_row_count": 0,
        "blockers": blockers,
        "single_next_action": "Keep KIS official repo as a current-master parser reference only; acquire licensed or exchange-official historical membership data for replacement_* worklists.",
        "non_goals": [
            "does_not_copy_external_code_into_C_AI",
            "does_not_fill_replacement_worklists_from_current_snapshot_only",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
        "source_files": {"official_repo": str(repo)},
    }


def render_md(report: dict) -> str:
    axis_lines = "\n".join(
        f"- `{row['axis']}`: current_master=`{str(row['official_current_master_available']).lower()}`, "
        f"historical_pit=`{str(row['historical_pit_membership_available']).lower()}`, "
        f"replacement_ready=`{str(row['replacement_worklist_operation_ready']).lower()}`"
        for row in report.get("axis_reports", [])
    )
    blockers = ", ".join(report.get("blockers", [])) or "none"
    return (
        "# KIS Official Open Trading API Source Probe\n\n"
        f"- Status: `{report['status']}`\n"
        f"- Accepted for replacement worklist fill: `{str(report['accepted_for_replacement_worklist_fill']).lower()}`\n"
        f"- Operation-ready replacement rows: `{report['operation_ready_replacement_row_count']}`\n"
        f"- License file exists: `{str(report['license_file_exists']).lower()}`\n"
        f"- Blockers: `{blockers}`\n"
        f"- Single next action: {report['single_next_action']}\n\n"
        "## Axis Decision\n\n"
        f"{axis_lines}\n"
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "operation_ready": report["operation_ready"], "latest_json": str(REPORT_JSON), "safety": SAFETY}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
