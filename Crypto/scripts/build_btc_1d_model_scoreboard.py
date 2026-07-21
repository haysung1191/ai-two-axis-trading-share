from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis_results"
ARTIFACTS_DIR = ROOT / "artifacts"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_negative_drawdown(value: object) -> float:
    return -abs(float(value or 0.0))


def _latest_interval_run_files() -> list[Path]:
    run_files = sorted(ARTIFACTS_DIR.glob("*/run_leaderboard.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not run_files:
        return []
    latest_day = datetime.fromtimestamp(run_files[0].stat().st_mtime, tz=UTC).date()
    return [
        path
        for path in run_files
        if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).date() == latest_day
    ]


def _interval_models(run_files: list[Path]) -> tuple[list[dict[str, object]], list[str]]:
    seen: dict[str, dict[str, object]] = {}
    run_ids: list[str] = []
    for path in run_files:
        payload = _read_json(path)
        run_ids.append(str(payload.get("run_id", path.parent.name)))
        for entry in payload.get("entries", []):
            strategy_name = str(entry.get("strategy_name", "")).strip()
            if not strategy_name:
                continue
            existing = seen.get(strategy_name)
            if existing is None or float(entry.get("cagr", 0.0) or 0.0) > float(existing.get("cagr", 0.0) or 0.0):
                seen[strategy_name] = {
                    "variant": strategy_name,
                    "role": "interval_new_model",
                    "cagr": float(entry.get("cagr", 0.0) or 0.0),
                    "mdd": _as_negative_drawdown(entry.get("max_drawdown", 0.0)),
                    "sharpe": float(entry.get("sharpe", 0.0) or 0.0),
                    "cost_cagr": None,
                    "oos_cagr": None,
                    "turnover": None,
                    "negative_walk_forward_windows": None,
                    "source_run_id": payload.get("run_id", path.parent.name),
                }
    rows = sorted(seen.values(), key=lambda row: (row["cagr"], -row["mdd"]), reverse=True)
    return rows, run_ids


def build_payload() -> dict[str, object]:
    research_payload = _read_json(ANALYSIS_DIR / "btc_1d_research_stack_operating_brief_latest.json")
    board_payload = _read_json(ANALYSIS_DIR / "btc_1d_attack_experiment_board_latest.json")
    queue_payload = _read_json(ANALYSIS_DIR / "btc_1d_attack_execution_queue_latest.json")
    interval_run_files = _latest_interval_run_files()
    interval_rows, run_ids = _interval_models(interval_run_files)

    top_models: list[dict[str, object]] = []
    for key in ("attack_main", "attack_backup", "attack_challenger"):
        model = research_payload["models"][key]
        top_models.append(
            {
                "variant": model["label"],
                "role": key,
                "cagr": float(model["base_cagr"]),
                "mdd": _as_negative_drawdown(model["base_mdd"]),
                "sharpe": float(model["base_sharpe"]),
                "cost_cagr": float(model.get("cost20_cagr") or 0.0),
                "oos_cagr": float(model.get("oos_cagr") or 0.0),
                "turnover": None,
                "negative_walk_forward_windows": model.get("negative_walk_forward_windows"),
            }
        )

    near_miss = research_payload["models"]["highest_priority_near_miss"]
    top_models.append(
        {
            "variant": near_miss["label"],
            "role": "highest_priority_near_miss",
            "cagr": float(near_miss["base_cagr"]),
            "mdd": _as_negative_drawdown(near_miss["base_mdd"]),
            "sharpe": float(near_miss["base_sharpe"]),
            "cost_cagr": None,
            "oos_cagr": None,
            "turnover": None,
            "negative_walk_forward_windows": None,
        }
    )

    payload = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "repo": "crypto",
        "report_focus": "model_metrics",
        "new_models_this_interval": len(interval_rows),
        "interval_run_count": len(run_ids),
        "interval_run_ids": run_ids[:20],
        "queue_next_step": queue_payload["queue_summary"]["next_step_now"],
        "queue_runner": queue_payload["queue_summary"]["next_runner_now"],
        "board_next_research_step": board_payload["attack_research_focus"]["next_research_step_now"],
        "top_models": sorted(top_models, key=lambda row: (row["cagr"], -row["mdd"]), reverse=True),
        "top_new_models": interval_rows[:5],
    }
    return payload


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# BTC 1d Model Scoreboard",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- new_models_this_interval: `{payload['new_models_this_interval']}`",
        f"- interval_run_count: `{payload['interval_run_count']}`",
        f"- queue_next_step: `{payload['queue_next_step']}`",
        f"- queue_runner: `{payload['queue_runner']}`",
        f"- board_next_research_step: `{payload['board_next_research_step']}`",
        "",
        "| role | variant | CAGR | MDD | Sharpe | cost20_CAGR | OOS_CAGR | negWF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["top_models"]:
        neg_wf = row.get("negative_walk_forward_windows")
        lines.append(
            "| {role} | `{variant}` | {cagr:.2%} | {mdd:.2%} | {sharpe:.4f} | {cost_cagr} | {oos_cagr} | {neg_wf} |".format(
                role=row["role"],
                variant=row["variant"],
                cagr=float(row["cagr"]),
                mdd=float(row["mdd"]),
                sharpe=float(row["sharpe"]),
                cost_cagr=("none" if row.get("cost_cagr") in {None, ""} else f"{float(row['cost_cagr']):.2%}"),
                oos_cagr=("none" if row.get("oos_cagr") in {None, ""} else f"{float(row['oos_cagr']):.2%}"),
                neg_wf=("none" if neg_wf in (None, "") else neg_wf),
            )
        )
    lines.extend(
        [
            "",
            "## Top New Models",
            "",
            "| variant | CAGR | MDD | Sharpe | run_id |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["top_new_models"]:
        lines.append(
            "| `{variant}` | {cagr:.2%} | {mdd:.2%} | {sharpe:.4f} | `{run_id}` |".format(
                variant=row["variant"],
                cagr=float(row["cagr"]),
                mdd=float(row["mdd"]),
                sharpe=float(row["sharpe"]),
                run_id=row["source_run_id"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_payload()
    markdown = render_markdown(payload)
    summary_path = ANALYSIS_DIR / "btc_1d_model_scoreboard_latest.json"
    markdown_path = ANALYSIS_DIR / "btc_1d_model_scoreboard_md_latest.md"
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
    print(json.dumps({"summary_path": str(summary_path), "markdown_path": str(markdown_path), "payload": payload}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
