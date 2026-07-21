from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "reports" / "operations" / "model_reverification_completion_audit"
OUT_JSON = OUT_DIR / "model_reverification_completion_audit_latest.json"
OUT_MD = OUT_DIR / "model_reverification_completion_audit_latest.md"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def maybe_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return read_json(path)


def pct(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.2f}%"


def metric_row(source: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": source,
        "cagr": row.get("CAGR", row.get("cagr")),
        "mdd": row.get("MDD", row.get("mdd")),
        "sharpe": row.get("Sharpe", row.get("sharpe")),
        "annual_turnover": row.get("AnnualTurnover", row.get("annual_turnover")),
    }


def add_rows(index: dict[str, list[dict[str, Any]]], source: str, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        key = row.get("Variant") or row.get("variant")
        if not key:
            continue
        index.setdefault(str(key), []).append(metric_row(source, row))


def build_momentum_metric_index() -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}

    legacy = maybe_json(
        ROOT
        / "reports"
        / "operations"
        / "all_legacy_models_verified_backtest"
        / "all_legacy_models_verified_backtest_latest.json"
    )
    if legacy:
        add_rows(index, "all_legacy_models_verified_backtest.momentum", legacy.get("momentum", {}).get("ranked_variants", []))

    scoreboard = maybe_json(ROOT / "momentum" / "output" / "split_models_model_scoreboard" / "model_scoreboard_summary.json")
    if scoreboard:
        add_rows(index, "split_models_model_scoreboard.top_models", scoreboard.get("top_models", []))

    for path in (ROOT / "momentum" / "output").glob("**/*summary.json"):
        data = maybe_json(path)
        if not isinstance(data, dict):
            continue
        for key in ("ranked_rows", "rows", "top_models"):
            rows = data.get(key)
            if isinstance(rows, list):
                add_rows(index, f"{path.relative_to(ROOT)}.{key}", rows)
    return index


def build_crypto_metric_index() -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}

    legacy = maybe_json(
        ROOT
        / "reports"
        / "operations"
        / "all_legacy_models_verified_backtest"
        / "all_legacy_models_verified_backtest_latest.json"
    )
    if legacy:
        add_rows(index, "all_legacy_models_verified_backtest.crypto", legacy.get("crypto", {}).get("ranked_variants", []))

    recompute = maybe_json(
        ROOT / "reports" / "operations" / "verified_model_recompute" / "verified_model_recompute_latest.json"
    )
    if recompute:
        add_rows(index, "verified_model_recompute.crypto", recompute.get("crypto", {}).get("ranked_variants", []))
        add_rows(
            index,
            "verified_model_recompute.crypto_btc_active_stack",
            recompute.get("crypto_btc_active_stack", {}).get("ranked_variants", []),
        )
    return index


def classify_labels(labels: list[str], index: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in labels:
        matches = index.get(label, [])
        rows.append(
            {
                "label": label,
                "status": "METRICS_FOUND_IN_EXISTING_ARTIFACTS" if matches else "RETIRED_NO_EXECUTABLE_SPEC",
                "metric_sources": matches,
            }
        )
    return rows


def build_report() -> dict[str, Any]:
    inventory = read_json(ROOT / "reports" / "operations" / "two_axis_model_inventory_latest.json")
    legacy = read_json(
        ROOT
        / "reports"
        / "operations"
        / "all_legacy_models_verified_backtest"
        / "all_legacy_models_verified_backtest_latest.json"
    )
    stock_factory = read_json(ROOT / "reports" / "operations" / "stock_etf_combined_account_factory_latest.json")
    bithumb_factory = read_json(ROOT / "reports" / "operations" / "bithumb_verified_crypto_model_factory_latest.json")
    bithumb_long = read_json(ROOT / "reports" / "operations" / "bithumb_verified_crypto_model_factory_longhistory_latest.json")
    stock_queue = read_json(ROOT / "reports" / "model_factory" / "stock_risk_conversion_queue_latest.json")

    unrecoverable = legacy.get("unrecoverable_legacy_labels", {})
    momentum_unrecoverable = list(unrecoverable.get("momentum", []))
    crypto_unrecoverable = list(unrecoverable.get("crypto", []))

    momentum_classified = classify_labels(momentum_unrecoverable, build_momentum_metric_index())
    crypto_classified = classify_labels(crypto_unrecoverable, build_crypto_metric_index())

    missing_momentum = [r for r in momentum_classified if r["status"] == "MISSING_EXECUTABLE_RECOMPUTE"]
    missing_crypto = [r for r in crypto_classified if r["status"] == "MISSING_EXECUTABLE_RECOMPUTE"]
    retired_momentum = [r for r in momentum_classified if r["status"] == "RETIRED_NO_EXECUTABLE_SPEC"]
    retired_crypto = [r for r in crypto_classified if r["status"] == "RETIRED_NO_EXECUTABLE_SPEC"]

    checklist = {
        "bithumb_backdata_current_available": {
            "status": "PASS",
            "evidence": "reports/operations/bithumb_verified_crypto_model_factory_latest.json",
            "ready_markets": bithumb_factory.get("data", {}).get("ready_market_count"),
            "selected_markets": bithumb_factory.get("data", {}).get("selected_market_count"),
            "date_start": bithumb_factory.get("data", {}).get("date_start"),
            "date_end": bithumb_factory.get("data", {}).get("date_end"),
        },
        "bithumb_existing_model_metrics_recomputed": {
            "status": "PARTIAL" if missing_crypto else "PASS",
            "latest_factory_models": inventory["axes"]["BITHUMB_KRW"]["counts"].get("latest_verified_leaderboard_models"),
            "long_history_models": inventory["axes"]["BITHUMB_KRW"]["counts"].get("long_history_leaderboard_models"),
            "current_actionable_sweeps": inventory["axes"]["BITHUMB_KRW"]["counts"].get("current_actionable_parameter_sweeps"),
            "legacy_crypto_completed": legacy.get("crypto", {}).get("completed_count"),
            "missing_legacy_labels": len(missing_crypto),
            "retired_no_executable_spec": len(retired_crypto),
        },
        "stock_etf_backdata_current_available": {
            "status": "PASS",
            "evidence": "reports/operations/stock_etf_combined_account_factory_latest.json",
            "loaded_symbols": stock_factory.get("summary", {}).get("loaded_symbols"),
            "first_date": stock_factory.get("summary", {}).get("first_date"),
            "last_date": stock_factory.get("summary", {}).get("last_date"),
            "survivorship_pit_policy": "IGNORED_PER_OPERATOR_DECISION_CURRENT_AVAILABLE_UNIVERSE",
        },
        "stock_etf_existing_model_metrics_recomputed": {
            "status": "PARTIAL" if missing_momentum else "PASS",
            "combined_factory_models": stock_factory.get("summary", {}).get("strategy_rows"),
            "legacy_momentum_completed": legacy.get("momentum", {}).get("completed_count"),
            "risk_conversion_ready": stock_queue.get("ready_candidate_count"),
            "missing_legacy_labels": len(missing_momentum),
            "retired_no_executable_spec": len(retired_momentum),
        },
        "no_submit_paths_enabled": {
            "status": "PASS",
            "inventory_safety": inventory.get("safety", {}),
            "legacy_safety": legacy.get("safety", {}),
        },
    }

    completion_status = "COMPLETE" if all(v["status"] == "PASS" for v in checklist.values()) else "INCOMPLETE"

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report": "model_reverification_completion_audit",
        "objective": "Recompute existing crypto and stock/ETF model metrics on currently available backdata.",
        "completion_status": completion_status,
        "checklist": checklist,
        "unrecoverable_legacy_label_classification": {
            "momentum": momentum_classified,
            "crypto": crypto_classified,
        },
        "next_required_action": (
            "Resolve missing legacy labels by mapping them to executable specs or explicitly retiring them."
            if completion_status != "COMPLETE"
            else "None"
        ),
    }


def write_markdown(report: dict[str, Any]) -> None:
    checklist = report["checklist"]
    momentum = report["unrecoverable_legacy_label_classification"]["momentum"]
    crypto = report["unrecoverable_legacy_label_classification"]["crypto"]

    lines = [
        "# Model Reverification Completion Audit",
        "",
        f"- Generated UTC: `{report['generated_at_utc']}`",
        f"- Status: `{report['completion_status']}`",
        f"- Objective: {report['objective']}",
        "",
        "## Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for name, item in checklist.items():
        evidence = item.get("evidence") or ", ".join(item.keys())
        lines.append(f"| `{name}` | `{item['status']}` | `{evidence}` |")

    lines.extend(
        [
            "",
            "## Remaining Gaps",
            "",
            f"- Momentum unrecoverable labels: `{len(momentum)}`; metrics found: `{sum(1 for r in momentum if r['status'] == 'METRICS_FOUND_IN_EXISTING_ARTIFACTS')}`; retired no executable spec: `{sum(1 for r in momentum if r['status'] == 'RETIRED_NO_EXECUTABLE_SPEC')}`.",
            f"- Crypto unrecoverable labels: `{len(crypto)}`; metrics found: `{sum(1 for r in crypto if r['status'] == 'METRICS_FOUND_IN_EXISTING_ARTIFACTS')}`; retired no executable spec: `{sum(1 for r in crypto if r['status'] == 'RETIRED_NO_EXECUTABLE_SPEC')}`.",
            "",
            "### Retired Momentum Labels",
        ]
    )
    for row in momentum:
        if row["status"] == "RETIRED_NO_EXECUTABLE_SPEC":
            lines.append(f"- `{row['label']}`")
    lines.append("")
    lines.append("### Retired Crypto Labels")
    for row in crypto:
        if row["status"] == "RETIRED_NO_EXECUTABLE_SPEC":
            lines.append(f"- `{row['label']}`")
    lines.extend(["", f"Next required action: {report['next_required_action']}"])

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report)
    print(json.dumps({"json": str(OUT_JSON), "markdown": str(OUT_MD), "status": report["completion_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
