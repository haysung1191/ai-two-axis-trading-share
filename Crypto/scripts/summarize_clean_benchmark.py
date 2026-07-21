from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_summary_rows(artifacts_root: Path) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for run_dir in sorted([path for path in artifacts_root.iterdir() if path.is_dir()], key=lambda p: p.name):
        spec_path = run_dir / "spec.json"
        decision_path = run_dir / "decision_record.json"
        leaderboard_path = run_dir / "run_leaderboard.json"
        if not (spec_path.exists() and decision_path.exists() and leaderboard_path.exists()):
            continue
        spec = _load_json(spec_path)
        metadata = spec.get("metadata", {})
        group = str(metadata.get("benchmark_group", "")).strip()
        if not group:
            continue
        decision = _load_json(decision_path)
        leaderboard = _load_json(leaderboard_path)
        entries = leaderboard.get("entries", [])
        top = entries[0] if isinstance(entries, list) and entries else {}
        grouped[group].append(
            {
                "decision": str(decision.get("decision", "UNKNOWN")),
                "top_sharpe": _safe_float(top.get("sharpe", 0.0)),
                "top_drawdown": _safe_float(top.get("max_drawdown", 0.0)),
                "top_sharpe_std": _safe_float(top.get("sharpe_std", 0.0)),
                "top_regime_std": _safe_float(top.get("sharpe_regime_std", 0.0)),
                "top_trades": _safe_int(top.get("trades", 0)),
            }
        )

    rows: list[dict[str, Any]] = []
    for group, records in sorted(grouped.items()):
        total = len(records)
        pass_count = sum(1 for row in records if row["decision"] == "PASS")
        pause_count = sum(1 for row in records if row["decision"] == "PAUSE")
        fail_count = sum(1 for row in records if row["decision"] == "FAIL")
        rows.append(
            {
                "group": group,
                "runs": total,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "pause_count": pause_count,
                "pass_rate": round(pass_count / total, 6) if total else 0.0,
                "mean_top_sharpe": round(sum(row["top_sharpe"] for row in records) / total, 6) if total else 0.0,
                "mean_top_drawdown": round(sum(row["top_drawdown"] for row in records) / total, 6) if total else 0.0,
                "mean_top_sharpe_std": round(sum(row["top_sharpe_std"] for row in records) / total, 6) if total else 0.0,
                "mean_top_regime_std": round(sum(row["top_regime_std"] for row in records) / total, 6) if total else 0.0,
                "mean_top_trades": round(sum(row["top_trades"] for row in records) / total, 6) if total else 0.0,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize clean benchmark runs grouped by benchmark_group.")
    parser.add_argument("--artifacts-root", default="artifacts")
    parser.add_argument("--output", default="paper_results/clean_benchmark_summary.csv")
    args = parser.parse_args()

    rows = build_summary_rows(Path(args.artifacts_root))
    _write_csv(Path(args.output), rows)
    print(f"Wrote summary to {args.output}")


if __name__ == "__main__":
    main()
