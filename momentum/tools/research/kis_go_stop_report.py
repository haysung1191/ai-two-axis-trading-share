import argparse
import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Dict, List, Optional, Tuple


@dataclass
class CheckResult:
    status: str
    reason: str


@dataclass
class InputSnapshot:
    ops_summary: Dict[str, str]
    health: Dict[str, str]
    portfolio_asof: Optional[str]
    ordersheet_tradedate: Optional[str]
    ordersheet_path: Optional[Path]
    runbook_path: Optional[Path]
    runbook_order_sheet_type: Optional[str]
    runbook_version: Optional[str]


REQUIRED_OUTPUT_FIELDS = [
    "Decision",
    "DecisionDate",
    "PortfolioAsOfDate",
    "OrderSheetTradeDate",
    "HealthStatus",
    "DailyCheckStatus",
    "SourceFresh",
    "ReadinessFresh",
    "PortfolioFile",
    "OrderSheetFile",
    "RunbookVersion",
    "MismatchSummary",
    "BlockingReason",
]


def read_single_row_csv(path: Path) -> Optional[Dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            return None
        return rows[-1]
    except Exception:
        return None


def read_runbook_order_sheet_type(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("- order sheet"):
            parts = stripped.split(":", 1)
            if len(parts) == 2:
                value = parts[1].strip()
                if value:
                    return value
    return None


def read_runbook_version(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("- version"):
            parts = stripped.split(":", 1)
            if len(parts) == 2:
                value = parts[1].strip()
                if value:
                    return value
    return None


def pick_order_sheet(backtests_dir: Path) -> Tuple[Optional[Path], Optional[str]]:
    initial = backtests_dir / "etf_riskbudget_micro_live_initial_sheet_3000000krw.csv"
    rebalance = backtests_dir / "etf_riskbudget_micro_live_rebalance_sheet_3000000krw.csv"

    has_initial = initial.exists()
    has_rebalance = rebalance.exists()

    if has_initial and not has_rebalance:
        return initial, "initial"
    if has_rebalance and not has_initial:
        return rebalance, "rebalance"
    if has_initial and has_rebalance:
        # Prefer the more recently modified file.
        chosen = max([initial, rebalance], key=lambda p: p.stat().st_mtime)
        return chosen, "initial" if chosen == initial else "rebalance"
    return None, None


def load_snapshot(base: Path) -> InputSnapshot:
    backtests_dir = base / "backtests"
    docs_dir = base / "docs"

    ops_path = backtests_dir / "kis_shadow_ops_summary.csv"
    health_path = backtests_dir / "kis_shadow_health.csv"
    portfolio_path = backtests_dir / "kis_shadow_portfolio.csv"
    runbook_path = docs_dir / "etf_riskbudget_micro_live_runbook.md"

    ops_summary = read_single_row_csv(ops_path) or {}
    health = read_single_row_csv(health_path) or {}
    portfolio_row = read_single_row_csv(portfolio_path) or {}
    portfolio_asof = portfolio_row.get("AsOfDate") if portfolio_row else None

    ordersheet_path, ordersheet_type = pick_order_sheet(backtests_dir)
    ordersheet_row = read_single_row_csv(ordersheet_path) if ordersheet_path else None
    ordersheet_tradedate = ordersheet_row.get("TradeDate") if ordersheet_row else None

    runbook_order_sheet_type = read_runbook_order_sheet_type(runbook_path) if runbook_path.exists() else None
    runbook_version = read_runbook_version(runbook_path) if runbook_path.exists() else None

    return InputSnapshot(
        ops_summary=ops_summary,
        health=health,
        portfolio_asof=portfolio_asof,
        ordersheet_tradedate=ordersheet_tradedate,
        ordersheet_path=ordersheet_path,
        runbook_path=runbook_path if runbook_path.exists() else None,
        runbook_order_sheet_type=runbook_order_sheet_type,
        runbook_version=runbook_version,
    )


def validate_inputs(snapshot: InputSnapshot) -> List[str]:
    missing = []
    if not snapshot.ops_summary:
        missing.append("kis_shadow_ops_summary.csv")
    if not snapshot.health:
        missing.append("kis_shadow_health.csv")
    if snapshot.portfolio_asof is None:
        missing.append("kis_shadow_portfolio.csv")
    if snapshot.ordersheet_path is None or snapshot.ordersheet_tradedate is None:
        missing.append("order_sheet")
    if snapshot.runbook_path is None:
        missing.append("etf_riskbudget_micro_live_runbook.md")
    return missing


def decide(snapshot: InputSnapshot) -> Dict[str, str]:
    mismatch_summary = []
    blocking_reason = []

    missing_inputs = validate_inputs(snapshot)
    if missing_inputs:
        return {
            "Decision": "STOP",
            "DecisionDate": str(date.today()),
            "PortfolioAsOfDate": snapshot.portfolio_asof or "",
            "OrderSheetTradeDate": snapshot.ordersheet_tradedate or "",
            "HealthStatus": snapshot.health.get("HealthStatus", ""),
            "DailyCheckStatus": snapshot.ops_summary.get("DailyCheckStatus", ""),
            "SourceFresh": snapshot.health.get("SourceFresh", ""),
            "ReadinessFresh": snapshot.health.get("ReadinessFresh", ""),
            "PortfolioFile": "backtests/kis_shadow_portfolio.csv",
            "OrderSheetFile": str(snapshot.ordersheet_path) if snapshot.ordersheet_path else "",
            "RunbookVersion": snapshot.runbook_version or "unknown",
            "MismatchSummary": "missing:" + ",".join(missing_inputs),
            "BlockingReason": "missing required inputs",
        }

    health_status = snapshot.health.get("HealthStatus", "")
    source_fresh = snapshot.health.get("SourceFresh", "")
    readiness_fresh = snapshot.health.get("ReadinessFresh", "")
    daily_check_status = snapshot.ops_summary.get("DailyCheckStatus", "")

    if source_fresh != "1" or readiness_fresh != "1" or health_status != "OK":
        blocking_reason.append("health not OK or freshness failed")

    if daily_check_status != "GO":
        blocking_reason.append("daily check not GO")

    if snapshot.portfolio_asof != snapshot.ordersheet_tradedate:
        mismatch_summary.append("portfolio date != order sheet date")
        blocking_reason.append("date mismatch")

    # Runbook vs order sheet type check (if runbook indicates type)
    if snapshot.runbook_order_sheet_type and snapshot.ordersheet_path:
        normalized = snapshot.runbook_order_sheet_type.lower()
        if "initial" in normalized and "initial" not in snapshot.ordersheet_path.name:
            mismatch_summary.append("runbook expects initial order sheet")
            blocking_reason.append("order sheet type mismatch")
        if "rebalance" in normalized and "rebalance" not in snapshot.ordersheet_path.name:
            mismatch_summary.append("runbook expects rebalance order sheet")
            blocking_reason.append("order sheet type mismatch")

    if blocking_reason:
        decision = "STOP"
    else:
        decision = "GO"

    return {
        "Decision": decision,
        "DecisionDate": str(date.today()),
        "PortfolioAsOfDate": snapshot.portfolio_asof or "",
        "OrderSheetTradeDate": snapshot.ordersheet_tradedate or "",
        "HealthStatus": health_status,
        "DailyCheckStatus": daily_check_status,
        "SourceFresh": source_fresh,
        "ReadinessFresh": readiness_fresh,
        "PortfolioFile": "backtests/kis_shadow_portfolio.csv",
        "OrderSheetFile": str(snapshot.ordersheet_path) if snapshot.ordersheet_path else "",
        "RunbookVersion": snapshot.runbook_version or "unknown",
        "MismatchSummary": "; ".join(mismatch_summary) if mismatch_summary else "",
        "BlockingReason": "; ".join(blocking_reason) if blocking_reason else "",
    }


def write_output(path: Path, payload: Dict[str, str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerow(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".", help="Project root")
    parser.add_argument("--out", default="backtests/kis_go_stop_report.csv")
    args = parser.parse_args()

    base = Path(args.base).resolve()
    out_path = (base / args.out).resolve()

    snapshot = load_snapshot(base)
    payload = decide(snapshot)
    write_output(out_path, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())