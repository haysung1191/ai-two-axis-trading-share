from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ATTACK_MAIN = {
    "label": "ratio112_tighter_stop_main",
    "cagr": 0.4243,
    "max_drawdown": 0.1609,
    "sharpe": 1.5613,
}

ATTACK_BACKUP = {
    "label": "ratio111_tighter_stop_backup",
    "cagr": 0.4154,
    "max_drawdown": 0.1609,
    "sharpe": 1.5348,
}


@dataclass(frozen=True)
class CandidateArtifact:
    family: str
    artifact_path: Path


DEFAULT_CANDIDATES: tuple[CandidateArtifact, ...] = (
    CandidateArtifact(
        family="volatility_spike_reversal_continuation",
        artifact_path=Path("analysis_results/btc_1d_volatility_spike_reversal_continuation_high_cagr_batch_20260415T171339Z.json"),
    ),
    CandidateArtifact(
        family="post_spike_consolidation_breakout",
        artifact_path=Path("analysis_results/btc_1d_post_spike_consolidation_breakout_high_cagr_batch_20260415T170649Z.json"),
    ),
    CandidateArtifact(
        family="volatility_expansion_pullthrough",
        artifact_path=Path("analysis_results/btc_1d_volatility_expansion_pullthrough_high_cagr_batch_20260415T174435Z.json"),
    ),
    CandidateArtifact(
        family="impulse_flag_breakout",
        artifact_path=Path("analysis_results/btc_1d_impulse_flag_breakout_high_cagr_batch_20260415T171751Z.json"),
    ),
    CandidateArtifact(
        family="narrow_range_expansion_drift",
        artifact_path=Path("analysis_results/btc_1d_narrow_range_expansion_drift_high_cagr_batch_20260415T170126Z.json"),
    ),
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_candidate_path(candidate: CandidateArtifact, analysis_results_dir: Path) -> Path | None:
    if candidate.artifact_path.exists():
        return candidate.artifact_path
    pattern = f"btc_1d_{candidate.family}_high_cagr_batch_*.json"
    matches = sorted(analysis_results_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def _best_result(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results", [])
    if not results:
        raise ValueError("results missing")
    return max(results, key=lambda item: (float(item.get("cagr", 0.0)), -float(item.get("max_drawdown", 1.0)), float(item.get("sharpe", 0.0))))


def _attack_conversion_label(result: dict[str, Any]) -> str:
    cagr = float(result["cagr"])
    mdd = float(result["max_drawdown"])
    if cagr >= 0.35 and mdd <= 0.30:
        return "attack_near_miss_hold"
    if cagr >= 0.20 and mdd <= 0.20:
        return "defensive_hold_only"
    return "kill_for_attack_conversion"


def _to_pct(value: float) -> float:
    return round(value * 100.0, 2)


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# BTC 1d Attack Conversion Candidate Screen",
        "",
        f"- attack_main: `{payload['attack_main']['label']}` `{payload['attack_main']['cagr_pct']}% / {payload['attack_main']['mdd_pct']}% / Sharpe {payload['attack_main']['sharpe']}`",
        f"- attack_backup: `{payload['attack_backup']['label']}` `{payload['attack_backup']['cagr_pct']}% / {payload['attack_backup']['mdd_pct']}% / Sharpe {payload['attack_backup']['sharpe']}`",
        "",
        "| family | best variant | CAGR | MDD | Sharpe | vs main CAGR gap | verdict |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['family']} | {row['variant_label']} | {row['cagr_pct']}% | {row['mdd_pct']}% | {row['sharpe']} | {row['cagr_gap_to_main_pct']}% | {row['attack_conversion_label']} |"
        )
    lines.extend(
        [
            "",
            "## Summary",
            f"- top_attack_conversion_candidate: `{payload['summary']['top_attack_conversion_candidate']}`",
            f"- best_defensive_hold: `{payload['summary']['best_defensive_hold']}`",
            f"- attack_conversion_nonstarters: `{', '.join(payload['summary']['attack_conversion_nonstarters'])}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_attack_conversion_screen(
    *,
    analysis_results_dir: Path = Path("analysis_results"),
    artifacts: tuple[CandidateArtifact, ...] = DEFAULT_CANDIDATES,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    for candidate in artifacts:
        artifact_path = _resolve_candidate_path(candidate, analysis_results_dir)
        if artifact_path is None:
            rows.append(
                {
                    "family": candidate.family,
                    "artifact_path": str(candidate.artifact_path),
                    "strategy_name": "missing_archived_artifact",
                    "variant_label": "missing_archived_artifact",
                    "decision": "not_available",
                    "cagr": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe": 0.0,
                    "trades": 0,
                    "completed_trades": 0,
                    "cagr_pct": 0.0,
                    "mdd_pct": 0.0,
                    "cagr_gap_to_main_pct": round(0.0 - _to_pct(ATTACK_MAIN["cagr"]), 2),
                    "mdd_gap_to_main_pct": round(0.0 - _to_pct(ATTACK_MAIN["max_drawdown"]), 2),
                    "attack_conversion_label": "missing_archived_artifact",
                }
            )
            continue
        payload = _load_json(artifact_path)
        best = _best_result(payload)
        row = {
            "family": candidate.family,
            "artifact_path": str(artifact_path),
            "strategy_name": best["strategy_name"],
            "variant_label": best["variant_label"],
            "decision": best["decision"],
            "cagr": float(best["cagr"]),
            "max_drawdown": float(best["max_drawdown"]),
            "sharpe": round(float(best["sharpe"]), 4),
            "trades": int(best["trades"]),
            "completed_trades": int(best["completed_trades"]),
        }
        row["cagr_pct"] = _to_pct(row["cagr"])
        row["mdd_pct"] = _to_pct(row["max_drawdown"])
        row["cagr_gap_to_main_pct"] = round(row["cagr_pct"] - _to_pct(ATTACK_MAIN["cagr"]), 2)
        row["mdd_gap_to_main_pct"] = round(row["mdd_pct"] - _to_pct(ATTACK_MAIN["max_drawdown"]), 2)
        row["attack_conversion_label"] = _attack_conversion_label(row)
        rows.append(row)

    rows.sort(key=lambda item: (-item["cagr"], item["max_drawdown"], -item["sharpe"]))

    defensive_holds = [row for row in rows if row["attack_conversion_label"] == "defensive_hold_only"]
    attack_holds = [row for row in rows if row["attack_conversion_label"] == "attack_near_miss_hold"]
    nonstarters = [
        row["family"]
        for row in rows
        if row["attack_conversion_label"] in {"kill_for_attack_conversion", "missing_archived_artifact"}
    ]

    summary = {
        "top_attack_conversion_candidate": attack_holds[0]["family"] if attack_holds else "none",
        "best_defensive_hold": defensive_holds[0]["family"] if defensive_holds else "none",
        "attack_conversion_nonstarters": nonstarters,
    }

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    output_json = analysis_results_dir / f"btc_1d_attack_conversion_candidate_screen_{stamp}.json"
    output_md = analysis_results_dir / f"btc_1d_attack_conversion_candidate_screen_{stamp}.md"

    result = {
        "generated_at": stamp,
        "attack_main": {
            "label": ATTACK_MAIN["label"],
            "cagr_pct": _to_pct(ATTACK_MAIN["cagr"]),
            "mdd_pct": _to_pct(ATTACK_MAIN["max_drawdown"]),
            "sharpe": ATTACK_MAIN["sharpe"],
        },
        "attack_backup": {
            "label": ATTACK_BACKUP["label"],
            "cagr_pct": _to_pct(ATTACK_BACKUP["cagr"]),
            "mdd_pct": _to_pct(ATTACK_BACKUP["max_drawdown"]),
            "sharpe": ATTACK_BACKUP["sharpe"],
        },
        "rows": rows,
        "summary": summary,
        "analysis_result_json": str(output_json),
        "analysis_result_md": str(output_md),
    }

    analysis_results_dir.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(result), encoding="utf-8")
    return result


def main() -> int:
    result = build_attack_conversion_screen()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
