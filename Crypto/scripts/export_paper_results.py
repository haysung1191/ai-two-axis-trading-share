from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _iter_run_dirs(artifacts_root: Path) -> list[Path]:
    if not artifacts_root.exists():
        return []
    return sorted([path for path in artifacts_root.iterdir() if path.is_dir()], key=lambda p: p.name)


def collect_candidate_metrics(artifacts_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_dir in _iter_run_dirs(artifacts_root):
        candidates_root = run_dir / "candidates"
        if not candidates_root.exists():
            continue
        for candidate_dir in sorted([path for path in candidates_root.iterdir() if path.is_dir()], key=lambda p: p.name):
            scorecard_path = candidate_dir / "scorecard.json"
            if not scorecard_path.exists():
                continue
            payload = _load_json(scorecard_path)
            strategy = payload.get("strategy", {})
            single_asset = payload.get("single_asset", {})
            multi_asset = payload.get("multi_asset", {})
            regime = payload.get("regime", {})
            overfitting = payload.get("overfitting", {})
            failed_gates = payload.get("failed_gates", [])
            rows.append(
                {
                    "run_id": str(payload.get("run_id", run_dir.name)),
                    "strategy_name": str(strategy.get("name", candidate_dir.name)),
                    "strategy_id": str(strategy.get("strategy_id", "")),
                    "source_type": str(strategy.get("source_type", "")),
                    "parent_strategy": "" if strategy.get("parent_strategy") is None else str(strategy.get("parent_strategy")),
                    "category": str(strategy.get("category", "")),
                    "candidate_pass": bool(payload.get("candidate_pass", False)),
                    "qa_passed": bool(payload.get("qa_passed", False)),
                    "trades": _safe_int(single_asset.get("trades", 0)),
                    "single_sharpe": _safe_float(single_asset.get("sharpe", 0.0)),
                    "single_cagr": _safe_float(single_asset.get("cagr", 0.0)),
                    "single_drawdown": _safe_float(single_asset.get("max_drawdown", 0.0)),
                    "sharpe_mean": _safe_float(multi_asset.get("sharpe_mean", 0.0)),
                    "sharpe_std": _safe_float(multi_asset.get("sharpe_std", 0.0)),
                    "drawdown_mean": _safe_float(multi_asset.get("drawdown_mean", 0.0)),
                    "drawdown_worst": _safe_float(multi_asset.get("drawdown_worst", 0.0)),
                    "sharpe_regime_std": _safe_float(regime.get("sharpe_regime_std", 0.0)),
                    "overfitting_flag_count": len(overfitting.get("flags", [])),
                    "failed_gates": "|".join(sorted(str(gate) for gate in failed_gates)),
                }
            )
    return rows


def collect_decision_outcomes(artifacts_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_dir in _iter_run_dirs(artifacts_root):
        decision_path = run_dir / "decision_record.json"
        leaderboard_path = run_dir / "run_leaderboard.json"
        if not decision_path.exists():
            continue
        decision = _load_json(decision_path)
        top_strategy = ""
        top_sharpe = 0.0
        if leaderboard_path.exists():
            leaderboard = _load_json(leaderboard_path)
            entries = leaderboard.get("entries", [])
            if isinstance(entries, list) and entries:
                top = entries[0]
                top_strategy = str(top.get("strategy_name", ""))
                top_sharpe = _safe_float(top.get("sharpe", 0.0))
        rows.append(
            {
                "run_id": run_dir.name,
                "decision": str(decision.get("decision", "")),
                "iteration": _safe_int(decision.get("iteration", 0)),
                "reject_count": _safe_int(decision.get("reject_count", 0)),
                "failed_gates": "|".join(sorted(str(gate) for gate in decision.get("failed_gates", []))),
                "top_strategy": top_strategy,
                "top_sharpe": top_sharpe,
            }
        )
    return rows


def collect_rejection_reasons(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_counter: Counter[str] = Counter()
    run_map: dict[str, set[str]] = {}
    for row in candidate_rows:
        run_id = str(row.get("run_id", ""))
        gates = [gate for gate in str(row.get("failed_gates", "")).split("|") if gate]
        for gate in gates:
            gate_counter[gate] += 1
            run_map.setdefault(gate, set()).add(run_id)
    rows = [
        {
            "failed_gate": gate,
            "candidate_count": count,
            "run_count": len(run_map.get(gate, set())),
        }
        for gate, count in sorted(gate_counter.items(), key=lambda item: (-item[1], item[0]))
    ]
    return rows


def collect_lineage_rows(registry_path: Path) -> list[dict[str, Any]]:
    if not registry_path.exists():
        return []
    payload = _load_json(registry_path)
    strategies = payload.get("strategies", [])
    rows: list[dict[str, Any]] = []
    if not isinstance(strategies, list):
        return rows
    for entry in strategies:
        if not isinstance(entry, dict):
            continue
        runs = entry.get("runs", [])
        rows.append(
            {
                "strategy_id": str(entry.get("strategy_id", "")),
                "source_type": str(entry.get("source_type", "")),
                "parent_strategy": "" if entry.get("parent_strategy") is None else str(entry.get("parent_strategy")),
                "first_seen_run": str(entry.get("first_seen_run", "")),
                "latest_run": str(entry.get("latest_run", "")),
                "best_sharpe": _safe_float(entry.get("best_sharpe", 0.0)),
                "best_cagr": _safe_float(entry.get("best_cagr", 0.0)),
                "best_drawdown": _safe_float(entry.get("best_drawdown", 0.0)),
                "run_count": len(runs) if isinstance(runs, list) else 0,
            }
        )
    return rows


def collect_source_type_stats(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in candidate_rows:
        grouped.setdefault(str(row.get("source_type", "")), []).append(row)
    rows: list[dict[str, Any]] = []
    for source_type, entries in sorted(grouped.items(), key=lambda item: item[0]):
        pass_count = sum(1 for row in entries if bool(row.get("candidate_pass", False)))
        sharpe_values = [_safe_float(row.get("sharpe_mean", 0.0)) for row in entries]
        rows.append(
            {
                "source_type": source_type,
                "candidate_count": len(entries),
                "pass_count": pass_count,
                "pass_rate": round((pass_count / len(entries)) if entries else 0.0, 6),
                "mean_sharpe": round(sum(sharpe_values) / len(sharpe_values), 6) if sharpe_values else 0.0,
            }
        )
    return rows


def collect_category_stats(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in candidate_rows:
        grouped.setdefault(str(row.get("category", "")), []).append(row)
    rows: list[dict[str, Any]] = []
    for category, entries in sorted(grouped.items(), key=lambda item: item[0]):
        pass_count = sum(1 for row in entries if bool(row.get("candidate_pass", False)))
        sharpe_values = [_safe_float(row.get("sharpe_mean", 0.0)) for row in entries]
        rows.append(
            {
                "category": category,
                "candidate_count": len(entries),
                "pass_count": pass_count,
                "pass_rate": round((pass_count / len(entries)) if entries else 0.0, 6),
                "mean_sharpe": round(sum(sharpe_values) / len(sharpe_values), 6) if sharpe_values else 0.0,
            }
        )
    return rows


def collect_terminal_state_stats(decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter(str(row.get("decision", "")) for row in decision_rows)
    total = max(1, sum(counter.values()))
    return [
        {
            "decision": decision,
            "run_count": count,
            "run_rate": round(count / total, 6),
        }
        for decision, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def collect_lineage_edges(lineage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "parent_strategy": str(row.get("parent_strategy", "")),
            "strategy_id": str(row.get("strategy_id", "")),
            "source_type": str(row.get("source_type", "")),
        }
        for row in lineage_rows
        if str(row.get("parent_strategy", ""))
    ]


def collect_candidate_funnel(
    candidate_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    lineage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    run_ids = {str(row.get("run_id", "")) for row in candidate_rows}
    pass_count = sum(1 for row in candidate_rows if bool(row.get("candidate_pass", False)))
    approved_runs = sum(1 for row in decision_rows if str(row.get("decision", "")) == "PASS")
    approved_strategies = len(lineage_rows)
    return [
        {"stage": "runs", "count": len(run_ids)},
        {"stage": "candidates_evaluated", "count": len(candidate_rows)},
        {"stage": "candidates_passed", "count": pass_count},
        {"stage": "approved_runs", "count": approved_runs},
        {"stage": "approved_strategies_in_registry", "count": approved_strategies},
    ]


def collect_figure_summary(
    candidate_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    rejection_rows: list[dict[str, Any]],
    source_type_rows: list[dict[str, Any]],
    category_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "candidate_count": len(candidate_rows),
        "run_count": len(decision_rows),
        "pass_candidate_count": sum(1 for row in candidate_rows if bool(row.get("candidate_pass", False))),
        "pass_run_count": sum(1 for row in decision_rows if str(row.get("decision", "")) == "PASS"),
        "top_rejection_gate": rejection_rows[0]["failed_gate"] if rejection_rows else "",
        "source_types": source_type_rows,
        "categories": category_rows,
    }


def export_paper_results(
    artifacts_root: Path,
    output_dir: Path,
    registry_path: Path,
) -> dict[str, Path]:
    candidate_rows = collect_candidate_metrics(artifacts_root)
    decision_rows = collect_decision_outcomes(artifacts_root)
    rejection_rows = collect_rejection_reasons(candidate_rows)
    lineage_rows = collect_lineage_rows(registry_path)
    source_type_rows = collect_source_type_stats(candidate_rows)
    category_rows = collect_category_stats(candidate_rows)
    terminal_state_rows = collect_terminal_state_stats(decision_rows)
    lineage_edges = collect_lineage_edges(lineage_rows)
    candidate_funnel = collect_candidate_funnel(candidate_rows, decision_rows, lineage_rows)
    figure_summary = collect_figure_summary(
        candidate_rows=candidate_rows,
        decision_rows=decision_rows,
        rejection_rows=rejection_rows,
        source_type_rows=source_type_rows,
        category_rows=category_rows,
    )

    outputs = {
        "candidate_metrics": output_dir / "candidate_metrics.csv",
        "decision_outcomes": output_dir / "decision_outcomes.csv",
        "rejection_reasons": output_dir / "rejection_reasons.csv",
        "lineage_stats": output_dir / "lineage_stats.csv",
        "source_type_stats": output_dir / "source_type_stats.csv",
        "category_stats": output_dir / "category_stats.csv",
        "terminal_state_stats": output_dir / "terminal_state_stats.csv",
        "lineage_edges": output_dir / "lineage_edges.csv",
        "candidate_funnel": output_dir / "candidate_funnel.csv",
        "figure_summary": output_dir / "figure_summary.json",
    }
    _write_csv(outputs["candidate_metrics"], candidate_rows)
    _write_csv(outputs["decision_outcomes"], decision_rows)
    _write_csv(outputs["rejection_reasons"], rejection_rows)
    _write_csv(outputs["lineage_stats"], lineage_rows)
    _write_csv(outputs["source_type_stats"], source_type_rows)
    _write_csv(outputs["category_stats"], category_rows)
    _write_csv(outputs["terminal_state_stats"], terminal_state_rows)
    _write_csv(outputs["lineage_edges"], lineage_edges)
    _write_csv(outputs["candidate_funnel"], candidate_funnel)
    _write_json(outputs["figure_summary"], figure_summary)
    return outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export paper-ready CSV summaries from run artifacts.")
    parser.add_argument("--artifacts-root", type=Path, default=Path("artifacts"))
    parser.add_argument("--output-dir", type=Path, default=Path("paper_results"))
    parser.add_argument("--registry-path", type=Path, default=Path("strategy_registry.json"))
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    outputs = export_paper_results(
        artifacts_root=args.artifacts_root,
        output_dir=args.output_dir,
        registry_path=args.registry_path,
    )
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
