from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _capital_slug(total_capital: float) -> str:
    if float(total_capital).is_integer():
        return str(int(total_capital))
    return str(total_capital).replace(".", "_")


def _run_step(label: str, args: list[str]) -> None:
    print(f"[start] {label}")
    subprocess.run(args, cwd=ROOT, check=True)
    print(f"[done] {label}")


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_latest_index(
    out_path: str | Path,
    *,
    capital_slug: str,
    total_capital: float,
    capital_readiness_details_path: str,
    capital_readiness_summary_path: str,
    plan_path: str,
    summary_path: str,
    preflight_path: str,
    report_path: str,
    submit_results_path: str,
    submit_summary_path: str,
    submit_live: bool,
    check_timestamp: str = "",
    check_json_path: str = "",
    check_md_path: str = "",
    check_history_json_path: str = "",
    check_history_md_path: str = "",
) -> None:
    payload = {
        "capital_slug": capital_slug,
        "total_capital": float(total_capital),
        "capital_readiness_details_path": capital_readiness_details_path,
        "capital_readiness_summary_path": capital_readiness_summary_path,
        "plan_path": plan_path,
        "summary_path": summary_path,
        "preflight_path": preflight_path,
        "report_path": report_path,
        "submit_results_path": submit_results_path,
        "submit_summary_path": submit_summary_path,
        "submit_live_requested": bool(submit_live),
        "check_timestamp": check_timestamp or None,
        "check_json_path": check_json_path or None,
        "check_md_path": check_md_path or None,
        "check_history_json_path": check_history_json_path or None,
        "check_history_md_path": check_history_md_path or None,
        "plan_sha256": _sha256_file(plan_path) if Path(plan_path).exists() else None,
        "summary_sha256": _sha256_file(summary_path) if Path(summary_path).exists() else None,
        "preflight_sha256": _sha256_file(preflight_path) if Path(preflight_path).exists() else None,
        "report_sha256": _sha256_file(report_path) if Path(report_path).exists() else None,
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _enforce_preflight_pass(
    preflight_path: str | Path,
    *,
    plan_path: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, object]:
    payload = _load_json(preflight_path)
    if payload.get("preflight_verdict") != "PASS":
        failures = payload.get("preflight_failures", [])
        joined = ", ".join(str(item) for item in failures) if failures else "unknown_preflight_failure"
        raise SystemExit(f"initial_entry_preflight_failed: {joined}")
    if plan_path is not None:
        expected_plan_hash = payload.get("execution_plan_sha256")
        actual_plan_hash = _sha256_file(plan_path)
        if expected_plan_hash and expected_plan_hash != actual_plan_hash:
            raise SystemExit("initial_entry_preflight_failed: execution_plan_hash_mismatch")
    if summary_path is not None:
        expected_summary_hash = payload.get("execution_summary_sha256")
        actual_summary_hash = _sha256_file(summary_path)
        if expected_summary_hash and expected_summary_hash != actual_summary_hash:
            raise SystemExit("initial_entry_preflight_failed: execution_summary_hash_mismatch")
    print(f"[summary] preflight_verdict={payload.get('preflight_verdict')}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book-path", default=str(SHADOW_DIR / "shadow_current_book.csv"))
    parser.add_argument("--total-capital", type=float, required=True)
    parser.add_argument("--disable-adaptive", action="store_true")
    parser.add_argument("--submit-live", action="store_true")
    parser.add_argument("--capital-readiness-details-path", default="")
    parser.add_argument("--capital-readiness-summary-path", default="")
    parser.add_argument("--plan-path", default="")
    parser.add_argument("--summary-path", default="")
    parser.add_argument("--submit-results-path", default="")
    parser.add_argument("--submit-summary-path", default="")
    parser.add_argument("--preflight-path", default="")
    args = parser.parse_args()

    python = sys.executable
    capital_slug = _capital_slug(args.total_capital)
    readiness_details_path = args.capital_readiness_details_path or str(
        SHADOW_DIR / f"shadow_capital_readiness_{capital_slug}.csv"
    )
    readiness_summary_path = args.capital_readiness_summary_path or str(
        SHADOW_DIR / f"shadow_capital_readiness_summary_{capital_slug}.json"
    )
    plan_path = args.plan_path or str(SHADOW_DIR / f"shadow_live_initial_adaptive_plan_{capital_slug}.csv")
    summary_path = args.summary_path or str(SHADOW_DIR / f"shadow_live_initial_adaptive_summary_{capital_slug}.json")
    submit_results_path = args.submit_results_path or str(
        SHADOW_DIR / f"shadow_live_initial_adaptive_submit_results_{capital_slug}.csv"
    )
    submit_summary_path = args.submit_summary_path or str(
        SHADOW_DIR / f"shadow_live_initial_adaptive_submit_summary_{capital_slug}.json"
    )
    preflight_path = args.preflight_path or str(SHADOW_DIR / f"shadow_live_initial_adaptive_preflight_{capital_slug}.json")
    report_path = str(SHADOW_DIR / f"shadow_live_initial_adaptive_report_{capital_slug}.md")
    latest_index_path = str(SHADOW_DIR / "shadow_live_initial_adaptive_latest.json")

    readiness_args = [
        python,
        "tools/operations/build_split_models_capital_readiness.py",
        "--book-path",
        args.book_path,
        "--details-path",
        readiness_details_path,
        "--summary-path",
        readiness_summary_path,
        "--total-capital",
        str(args.total_capital),
    ]
    _run_step("build capital readiness", readiness_args)

    execution_args = [
        python,
        "tools/operations/execute_split_models_shadow_live_orders.py",
        "--initial-book-path",
        args.book_path,
        "--plan-path",
        plan_path,
        "--summary-path",
        summary_path,
        "--submit-results-path",
        submit_results_path,
        "--total-capital",
        str(args.total_capital),
    ]
    if not args.disable_adaptive:
        execution_args.append("--adaptive-initial-entry")
    _run_step("build initial entry plan", execution_args)

    preflight_args = [
        python,
        "tools/operations/build_split_models_initial_entry_preflight.py",
        "--execution-summary-path",
        summary_path,
        "--execution-plan-path",
        plan_path,
        "--out-path",
        preflight_path,
    ]
    _run_step("build initial entry preflight", preflight_args)

    report_args = [
        python,
        "tools/operations/build_split_models_initial_entry_report.py",
        "--capital-readiness-summary-path",
        readiness_summary_path,
        "--preflight-path",
        preflight_path,
        "--plan-path",
        plan_path,
        "--out-path",
        report_path,
        "--capital-slug",
        capital_slug,
    ]
    _run_step("build initial entry report", report_args)

    if args.submit_live:
        _enforce_preflight_pass(preflight_path, plan_path=plan_path, summary_path=summary_path)
        submit_args = [
            python,
            "tools/operations/execute_split_models_shadow_live_orders.py",
            "--submit-existing-plan-path",
            plan_path,
            "--preflight-path",
            preflight_path,
            "--summary-path",
            submit_summary_path,
            "--submit-results-path",
            submit_results_path,
            "--submit-live",
        ]
        _run_step("submit initial entry orders", submit_args)
        report_with_submit_args = report_args + [
            "--submit-summary-path",
            submit_summary_path,
            "--submit-results-path",
            submit_results_path,
        ]
        _run_step("refresh initial entry report after submit", report_with_submit_args)

    _write_latest_index(
        latest_index_path,
        capital_slug=capital_slug,
        total_capital=args.total_capital,
        capital_readiness_details_path=readiness_details_path,
        capital_readiness_summary_path=readiness_summary_path,
        plan_path=plan_path,
        summary_path=summary_path,
        preflight_path=preflight_path,
        report_path=report_path,
        submit_results_path=submit_results_path,
        submit_summary_path=submit_summary_path,
        submit_live=args.submit_live,
    )

    print("[summary] initial entry artifacts refreshed")
    print(f"[summary] capital_readiness_details_path={readiness_details_path}")
    print(f"[summary] capital_readiness_summary_path={readiness_summary_path}")
    print(f"[summary] plan_path={plan_path}")
    print(f"[summary] summary_path={summary_path}")
    print(f"[summary] preflight_path={preflight_path}")
    print(f"[summary] report_path={report_path}")
    print(f"[summary] latest_index_path={latest_index_path}")
    if args.submit_live:
        print(f"[summary] submit_summary_path={submit_summary_path}")
        print(f"[summary] submit_results_path={submit_results_path}")


if __name__ == "__main__":
    main()
