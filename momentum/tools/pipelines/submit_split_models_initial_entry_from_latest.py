from __future__ import annotations

import argparse
from datetime import datetime
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.pipelines import run_split_models_initial_entry as initial_entry_runner


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, object]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _require_path(payload: dict[str, object], key: str) -> str:
    value = str(payload.get(key, "") or "")
    if not value:
        raise SystemExit(f"latest_index_invalid: missing_{key}")
    path = Path(value)
    if not path.exists():
        raise SystemExit(f"latest_index_invalid: missing_file_for_{key}")
    return str(path)


def _enforce_latest_index_integrity(payload: dict[str, object]) -> dict[str, str]:
    required_paths = {
        "capital_readiness_summary_path": _require_path(payload, "capital_readiness_summary_path"),
        "plan_path": _require_path(payload, "plan_path"),
        "summary_path": _require_path(payload, "summary_path"),
        "preflight_path": _require_path(payload, "preflight_path"),
        "report_path": _require_path(payload, "report_path"),
    }
    hash_mapping = {
        "plan_path": "plan_sha256",
        "summary_path": "summary_sha256",
        "preflight_path": "preflight_sha256",
        "report_path": "report_sha256",
    }
    for path_key, hash_key in hash_mapping.items():
        expected_hash = payload.get(hash_key)
        if expected_hash:
            actual_hash = initial_entry_runner._sha256_file(required_paths[path_key])
            if actual_hash != expected_hash:
                raise SystemExit(f"latest_index_invalid: {hash_key}_mismatch")
    return required_paths


def _build_check_payload(
    latest_index_path: str | Path,
    latest_payload: dict[str, object],
    paths: dict[str, str],
) -> dict[str, object]:
    capital_readiness = _load_json(paths["capital_readiness_summary_path"])
    preflight = _load_json(paths["preflight_path"])
    return {
        "check_verdict": "PASS",
        "submit_mode": "check_only",
        "latest_index_path": str(latest_index_path),
        "capital_slug": str(latest_payload.get("capital_slug", "") or "unknown"),
        "total_capital": float(latest_payload.get("total_capital", 0.0) or 0.0),
        "plan_path": paths["plan_path"],
        "summary_path": paths["summary_path"],
        "preflight_path": paths["preflight_path"],
        "report_path": paths["report_path"],
        "plan_sha256": str(latest_payload.get("plan_sha256", "") or ""),
        "summary_sha256": str(latest_payload.get("summary_sha256", "") or ""),
        "preflight_sha256": str(latest_payload.get("preflight_sha256", "") or ""),
        "report_sha256": str(latest_payload.get("report_sha256", "") or ""),
        "preflight_verdict": str(preflight.get("preflight_verdict", "") or ""),
        "live_readiness": str(preflight.get("live_readiness", "") or ""),
        "operator_gate_verdict": str(preflight.get("operator_gate_verdict", "") or ""),
        "archive_stability_verdict": str(preflight.get("archive_stability_verdict", "") or ""),
        "planned_count": int(preflight.get("planned_count", 0) or 0),
        "skipped_count": int(preflight.get("skipped_count", 0) or 0),
        "planned_symbols": list(preflight.get("planned_symbols", []) or []),
        "planned_quantity_total": int(preflight.get("planned_quantity_total", 0) or 0),
        "estimated_order_notional_krw_total": float(preflight.get("estimated_order_notional_krw_total", 0.0) or 0.0),
        "fundable_count_at_capital": int(capital_readiness.get("fundable_count_at_capital", 0) or 0),
        "fundable_symbols_at_capital": list(capital_readiness.get("fundable_symbols_at_capital", []) or []),
        "min_capital_all_holdings_one_share_krw": float(
            capital_readiness.get("min_capital_all_holdings_one_share_krw", 0.0) or 0.0
        ),
    }


def _build_check_markdown(payload: dict[str, object]) -> str:
    planned_symbols = ", ".join(str(item) for item in payload.get("planned_symbols", [])) or "-"
    fundable_symbols = ", ".join(str(item) for item in payload.get("fundable_symbols_at_capital", [])) or "-"
    lines = [
        "# Split Models Initial Entry Check",
        "",
        f"- Check verdict: `{payload.get('check_verdict', '-')}`",
        f"- Submit mode: `{payload.get('submit_mode', '-')}`",
        f"- Capital slug: `{payload.get('capital_slug', '-')}`",
        f"- Total capital: `{float(payload.get('total_capital', 0.0)):,.0f}`",
        f"- Preflight verdict: `{payload.get('preflight_verdict', '-')}`",
        f"- Live readiness: `{payload.get('live_readiness', '-')}`",
        f"- Operator gate: `{payload.get('operator_gate_verdict', '-')}`",
        f"- Archive stability: `{payload.get('archive_stability_verdict', '-')}`",
        "",
        "## Orders",
        "",
        f"- Planned count: `{payload.get('planned_count', 0)}`",
        f"- Skipped count: `{payload.get('skipped_count', 0)}`",
        f"- Planned symbols: `{planned_symbols}`",
        f"- Planned quantity total: `{payload.get('planned_quantity_total', 0)}`",
        f"- Estimated order notional total: `{float(payload.get('estimated_order_notional_krw_total', 0.0)):,.0f} KRW`",
        "",
        "## Capital Readiness",
        "",
        f"- Fundable count at capital: `{payload.get('fundable_count_at_capital', 0)}`",
        f"- Fundable symbols at capital: `{fundable_symbols}`",
        f"- Minimum capital for one share across all holdings: `{float(payload.get('min_capital_all_holdings_one_share_krw', 0.0)):,.0f} KRW`",
        "",
        "## Integrity",
        "",
        f"- Latest index path: `{payload.get('latest_index_path', '-')}`",
        f"- Plan path: `{payload.get('plan_path', '-')}`",
        f"- Plan sha256: `{payload.get('plan_sha256', '-')}`",
        f"- Summary path: `{payload.get('summary_path', '-')}`",
        f"- Summary sha256: `{payload.get('summary_sha256', '-')}`",
        f"- Preflight path: `{payload.get('preflight_path', '-')}`",
        f"- Preflight sha256: `{payload.get('preflight_sha256', '-')}`",
        f"- Report path: `{payload.get('report_path', '-')}`",
        f"- Report sha256: `{payload.get('report_sha256', '-')}`",
        "",
    ]
    return "\n".join(lines)


def _timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def _attach_check_snapshot_to_submit_summary(
    submit_summary_path: str | Path,
    *,
    check_timestamp: str,
    check_json_path: str,
    check_md_path: str,
    check_history_json_path: str,
    check_history_md_path: str,
) -> None:
    path = Path(submit_summary_path)
    if not path.exists():
        raise SystemExit("submit_summary_missing_after_live_submit")
    payload = _load_json(path)
    payload["check_timestamp"] = check_timestamp
    payload["check_json_path"] = check_json_path
    payload["check_md_path"] = check_md_path
    payload["check_history_json_path"] = check_history_json_path
    payload["check_history_md_path"] = check_history_md_path
    _write_json(path, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--latest-index-path",
        default=str(SHADOW_DIR / "shadow_live_initial_adaptive_latest.json"),
    )
    parser.add_argument("--submit-live", action="store_true")
    args = parser.parse_args()

    latest_index_path = Path(args.latest_index_path)
    if not latest_index_path.exists():
        raise SystemExit("latest_index_invalid: missing_latest_index")

    payload = _load_json(latest_index_path)
    paths = _enforce_latest_index_integrity(payload)
    capital_slug = str(payload.get("capital_slug", "") or "unknown")
    total_capital = float(payload.get("total_capital", 0.0) or 0.0)
    check_timestamp = _timestamp_slug()
    check_json_path = str(SHADOW_DIR / "shadow_live_initial_adaptive_check_latest.json")
    check_md_path = str(SHADOW_DIR / "shadow_live_initial_adaptive_check_latest.md")
    check_history_json_path = str(SHADOW_DIR / f"shadow_live_initial_adaptive_check_{check_timestamp}.json")
    check_history_md_path = str(SHADOW_DIR / f"shadow_live_initial_adaptive_check_{check_timestamp}.md")
    submit_results_path = str(
        payload.get("submit_results_path") or (SHADOW_DIR / f"shadow_live_initial_adaptive_submit_results_{capital_slug}.csv")
    )
    submit_summary_path = str(
        payload.get("submit_summary_path") or (SHADOW_DIR / f"shadow_live_initial_adaptive_submit_summary_{capital_slug}.json")
    )

    initial_entry_runner._enforce_preflight_pass(
        paths["preflight_path"],
        plan_path=paths["plan_path"],
        summary_path=paths["summary_path"],
    )
    check_payload = _build_check_payload(latest_index_path, payload, paths)
    check_payload["check_timestamp"] = check_timestamp
    _write_json(check_json_path, check_payload)
    _write_json(check_history_json_path, check_payload)
    Path(check_md_path).write_text(_build_check_markdown(check_payload), encoding="utf-8")
    Path(check_history_md_path).write_text(_build_check_markdown(check_payload), encoding="utf-8")
    initial_entry_runner._write_latest_index(
        latest_index_path,
        capital_slug=capital_slug,
        total_capital=total_capital,
        capital_readiness_details_path=str(payload.get("capital_readiness_details_path", "") or ""),
        capital_readiness_summary_path=paths["capital_readiness_summary_path"],
        plan_path=paths["plan_path"],
        summary_path=paths["summary_path"],
        preflight_path=paths["preflight_path"],
        report_path=paths["report_path"],
        submit_results_path=submit_results_path,
        submit_summary_path=submit_summary_path,
        submit_live=bool(payload.get("submit_live_requested", False)),
        check_timestamp=check_timestamp,
        check_json_path=check_json_path,
        check_md_path=check_md_path,
        check_history_json_path=check_history_json_path,
        check_history_md_path=check_history_md_path,
    )

    print(f"[summary] latest_index_path={latest_index_path}")
    print(f"[summary] capital_slug={capital_slug}")
    print(f"[summary] total_capital={total_capital}")
    print(f"[summary] plan_path={paths['plan_path']}")
    print(f"[summary] preflight_path={paths['preflight_path']}")
    print(f"[summary] report_path={paths['report_path']}")
    print(f"[summary] check_timestamp={check_timestamp}")
    print(f"[summary] check_json_path={check_json_path}")
    print(f"[summary] check_md_path={check_md_path}")
    print(f"[summary] check_history_json_path={check_history_json_path}")
    print(f"[summary] check_history_md_path={check_history_md_path}")

    if not args.submit_live:
        print("[summary] submit_mode=check_only")
        return

    python = sys.executable
    subprocess.run(
        [
            python,
            "tools/operations/execute_split_models_shadow_live_orders.py",
            "--submit-existing-plan-path",
            paths["plan_path"],
            "--summary-path",
            submit_summary_path,
            "--submit-results-path",
            submit_results_path,
            "--preflight-path",
            paths["preflight_path"],
            "--submit-live",
        ],
        cwd=ROOT,
        check=True,
    )
    _attach_check_snapshot_to_submit_summary(
        submit_summary_path,
        check_timestamp=check_timestamp,
        check_json_path=check_json_path,
        check_md_path=check_md_path,
        check_history_json_path=check_history_json_path,
        check_history_md_path=check_history_md_path,
    )

    subprocess.run(
        [
            python,
            "tools/operations/build_split_models_initial_entry_report.py",
            "--capital-readiness-summary-path",
            paths["capital_readiness_summary_path"],
            "--preflight-path",
            paths["preflight_path"],
            "--plan-path",
            paths["plan_path"],
            "--out-path",
            paths["report_path"],
            "--capital-slug",
            capital_slug,
            "--submit-summary-path",
            submit_summary_path,
            "--submit-results-path",
            submit_results_path,
        ],
        cwd=ROOT,
        check=True,
    )

    initial_entry_runner._write_latest_index(
        latest_index_path,
        capital_slug=capital_slug,
        total_capital=total_capital,
        capital_readiness_details_path=str(payload.get("capital_readiness_details_path", "") or ""),
        capital_readiness_summary_path=paths["capital_readiness_summary_path"],
        plan_path=paths["plan_path"],
        summary_path=paths["summary_path"],
        preflight_path=paths["preflight_path"],
        report_path=paths["report_path"],
        submit_results_path=submit_results_path,
        submit_summary_path=submit_summary_path,
        submit_live=True,
        check_timestamp=check_timestamp,
        check_json_path=check_json_path,
        check_md_path=check_md_path,
        check_history_json_path=check_history_json_path,
        check_history_md_path=check_history_md_path,
    )

    print("[summary] submit_mode=live")
    print(f"[summary] submit_summary_path={submit_summary_path}")
    print(f"[summary] submit_results_path={submit_results_path}")


if __name__ == "__main__":
    main()
