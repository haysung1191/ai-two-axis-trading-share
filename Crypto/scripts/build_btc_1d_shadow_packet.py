from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON payload: {path}")
    return payload


def _latest_json(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No files matched {pattern} in {analysis_dir}")
    return matches[0]


def _latest_paper_validation_for_period(analysis_dir: Path, period: int | None) -> Path | None:
    if period is None:
        return None
    matches = sorted(
        analysis_dir.glob("btc_1d_ema_trend_atr_exit_paper_validation_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in matches:
        payload = _load_json(path)
        config = payload.get("config", {})
        if int(config.get("periods", -1)) == int(period):
            return path
    return None


def _latest_eth_regression(analysis_dir: Path) -> Path | None:
    matches = sorted(
        analysis_dir.glob("btc_1d_promoted_candidate_regression_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in matches:
        payload = _load_json(path)
        if payload.get("config", {}).get("symbol") == "ETHUSDT":
            return path
    return None


def _latest_walk_forward_for_period(analysis_dir: Path, period: int | None) -> Path | None:
    if period is None:
        return None
    matches = sorted(
        analysis_dir.glob("btc_1d_walk_forward_diagnostic_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in matches:
        payload = _load_json(path)
        if int(payload.get("config", {}).get("periods", -1)) == int(period):
            return path
    return None


def build_shadow_packet(
    *,
    analysis_dir: Path,
    carry_paper_path: Path | None = None,
    survivability_paper_path: Path | None = None,
    friction_path: Path | None = None,
    walk_forward_path: Path | None = None,
) -> dict[str, Any]:
    freeze_path = _latest_json(analysis_dir, "btc_1d_baseline_freeze_*.json")
    status_path = _latest_json(analysis_dir, "btc_1d_candidate_status_board_*.json")
    readiness_path = _latest_json(analysis_dir, "btc_1d_shadow_readiness_*.json")
    effective_friction_path = friction_path or _latest_json(analysis_dir, "btc_1d_low_vol_cap_friction_*.json")
    eth_regression_path = _latest_eth_regression(analysis_dir)

    freeze_payload = _load_json(freeze_path)
    status_payload = _load_json(status_path)
    readiness_payload = _load_json(readiness_path)
    friction_payload = _load_json(effective_friction_path)
    eth_regression_payload = _load_json(eth_regression_path) if eth_regression_path else None
    carry_reference_period = status_payload.get("carry_reference_period") or status_payload.get("carry_reference_bars")
    survivability_reference_period = status_payload.get("survivability_reference_period") or status_payload.get(
        "survivability_reference_bars"
    )
    effective_carry_paper_path = carry_paper_path or _latest_paper_validation_for_period(analysis_dir, carry_reference_period) or _latest_json(
        analysis_dir, "btc_1d_ema_trend_atr_exit_paper_validation_*.json"
    )
    effective_survivability_paper_path = survivability_paper_path or _latest_paper_validation_for_period(
        analysis_dir, survivability_reference_period
    )
    effective_walk_forward_path = walk_forward_path or _latest_walk_forward_for_period(analysis_dir, carry_reference_period)

    carry_paper_payload = _load_json(effective_carry_paper_path)
    survivability_paper_payload = _load_json(effective_survivability_paper_path) if effective_survivability_paper_path else None
    walk_forward_payload = _load_json(effective_walk_forward_path) if effective_walk_forward_path else None

    carry_decision = carry_paper_payload.get("decision_record", {})
    carry_metrics = carry_decision.get("key_metrics", {})
    survivability_decision = (
        survivability_paper_payload.get("decision_record", {}) if survivability_paper_payload else {}
    )
    survivability_metrics = survivability_decision.get("key_metrics", {})
    walk_forward = walk_forward_payload.get("overfitting", {}) if walk_forward_payload else {}
    walk_forward_oos_metrics = walk_forward.get("oos_metrics", {}) if walk_forward else {}
    strategy_config = carry_paper_payload.get("config", {})
    extra_parameters = strategy_config.get("extra_parameters", {})
    friction_levels = friction_payload.get("levels", [])
    heaviest_friction = friction_levels[-1] if friction_levels else None
    eth_summary = eth_regression_payload.get("summary", {}) if eth_regression_payload else None
    eth_results = eth_regression_payload.get("results", []) if eth_regression_payload else []
    eth_by_period = {str(row.get("periods")): row for row in eth_results}

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": status_payload.get("active_candidate") or status_payload.get("candidate"),
        "status": status_payload.get("status"),
        "shadow_decision": readiness_payload.get("decision"),
        "paper_validation_decision": carry_decision.get("decision"),
        "paper_validation_metrics": carry_metrics,
        "survivability_validation_decision": survivability_decision.get("decision") if survivability_decision else None,
        "survivability_validation_metrics": survivability_metrics if survivability_decision else None,
        "walk_forward": {
            "passed": walk_forward.get("passed"),
            "summary": walk_forward.get("summary"),
            "oos_metrics": walk_forward_oos_metrics,
            "sensitivity_max_drift": walk_forward.get("sensitivity_max_drift"),
            "unstable_parameters": walk_forward.get("unstable_parameters"),
        }
        if walk_forward_payload
        else None,
        "friction_validation_decision": friction_payload.get("final_decision"),
        "friction_validation_reason": friction_payload.get("decision_reason"),
        "friction_validation_heaviest_level": heaviest_friction,
        "eth_regression_summary": eth_summary,
        "eth_regression_read": {
            "2200": eth_by_period.get("2200"),
            "2600": eth_by_period.get("2600"),
        }
        if eth_regression_payload
        else None,
        "parameters": {
            "ema_fast_window": strategy_config.get("ema_fast_window"),
            "ema_slow_window": strategy_config.get("ema_slow_window"),
            "atr_window": strategy_config.get("atr_window"),
            "atr_multiple": strategy_config.get("atr_multiple"),
            "time_stop_bars": strategy_config.get("time_stop_bars"),
            "regime_exit_confirmation_bars": extra_parameters.get("regime_exit_confirmation_bars"),
            "volatility_window": extra_parameters.get("volatility_window"),
            "volatility_target": extra_parameters.get("volatility_target"),
            "min_position_size": extra_parameters.get("min_position_size"),
            "min_annualized_volatility": extra_parameters.get("min_annualized_volatility"),
            "low_volatility_cap_threshold": extra_parameters.get("low_volatility_cap_threshold"),
            "low_volatility_position_cap": extra_parameters.get("low_volatility_position_cap"),
        },
        "carry_reference_period": carry_reference_period,
        "survivability_reference_period": survivability_reference_period,
        "sources": {
            "freeze": str(freeze_path),
            "status_board": str(status_path),
            "shadow_readiness": str(readiness_path),
            "friction_validation": str(effective_friction_path),
            "eth_regression": str(eth_regression_path) if eth_regression_path else None,
            "paper_validation": str(effective_carry_paper_path),
            "survivability_validation": str(effective_survivability_paper_path) if effective_survivability_paper_path else None,
            "walk_forward": str(effective_walk_forward_path) if effective_walk_forward_path else None,
        },
        "notes": [
            "BTC-only candidate.",
            "Carry on 2200/2600, weak on 1400/1800.",
            "Do not treat as a general multi-asset crypto model.",
        ],
    }


def _render_markdown(packet: dict[str, Any]) -> str:
    metrics = packet.get("paper_validation_metrics", {})
    survivability_metrics = packet.get("survivability_validation_metrics", {}) or {}
    walk_forward = packet.get("walk_forward", {}) or {}
    walk_forward_oos = walk_forward.get("oos_metrics", {}) or {}
    friction_metrics = packet.get("friction_validation_heaviest_level", {}) or {}
    eth_summary = packet.get("eth_regression_summary", {}) or {}
    eth_read = packet.get("eth_regression_read", {}) or {}
    eth_2200 = eth_read.get("2200", {}) or {}
    eth_2600 = eth_read.get("2600", {}) or {}
    parameters = packet.get("parameters", {})
    lines = [
        "# BTC 1d Shadow Packet",
        "",
        f"- Candidate: `{packet.get('candidate', '-')}`",
        f"- Status: `{packet.get('status', '-')}`",
        f"- Shadow decision: `{packet.get('shadow_decision', '-')}`",
        f"- Carry paper validation: `{packet.get('paper_validation_decision', '-')}`",
        f"- Survivability paper validation: `{packet.get('survivability_validation_decision', '-')}`",
        f"- Friction validation: `{packet.get('friction_validation_decision', '-')}`",
        "",
        "## Carry Metrics",
        f"- Sharpe: `{metrics.get('sharpe', '-')}`",
        f"- CAGR: `{metrics.get('cagr', '-')}`",
        f"- MDD: `{metrics.get('max_drawdown', '-')}`",
        f"- Win rate: `{metrics.get('win_rate', '-')}`",
        f"- Trades: `{metrics.get('trades', '-')}`",
        f"- Completed trades: `{metrics.get('completed_trades', '-')}`",
        "",
        "## Survivability Metrics",
        f"- Sharpe: `{survivability_metrics.get('sharpe', '-')}`",
        f"- CAGR: `{survivability_metrics.get('cagr', '-')}`",
        f"- MDD: `{survivability_metrics.get('max_drawdown', '-')}`",
        f"- Win rate: `{survivability_metrics.get('win_rate', '-')}`",
        f"- Trades: `{survivability_metrics.get('trades', '-')}`",
        f"- Completed trades: `{survivability_metrics.get('completed_trades', '-')}`",
        "",
        "## Heaviest Friction Check",
        f"- Cost level: `{friction_metrics.get('cost_bps', '-')}` bps fee + `{friction_metrics.get('cost_bps', '-')}` bps slippage",
        f"- Decision: `{friction_metrics.get('decision', '-')}`",
        f"- Sharpe: `{friction_metrics.get('sharpe', '-')}`",
        f"- CAGR: `{friction_metrics.get('cagr', '-')}`",
        f"- MDD: `{friction_metrics.get('max_drawdown', '-')}`",
        f"- Win rate: `{friction_metrics.get('win_rate', '-')}`",
        f"- Trades: `{friction_metrics.get('trades', '-')}`",
        f"- Reason: {packet.get('friction_validation_reason', '-')}",
        "",
        "## Walk-Forward Check",
        f"- Passed: `{walk_forward.get('passed', '-')}`",
        f"- OOS Sharpe: `{walk_forward_oos.get('sharpe', '-')}`",
        f"- OOS CAGR: `{walk_forward_oos.get('cagr', '-')}`",
        f"- OOS MDD: `{walk_forward_oos.get('max_drawdown', '-')}`",
        f"- Sensitivity drift: `{walk_forward.get('sensitivity_max_drift', '-')}`",
        f"- Unstable parameters: `{', '.join(walk_forward.get('unstable_parameters', []) or ['none'])}`",
        "",
        "## ETH Cross-Asset Check",
        f"- Pass rate: `{eth_summary.get('pass_rate', '-')}`",
        f"- `ETH 2200` Sharpe: `{eth_2200.get('sharpe', '-')}` | MDD: `{eth_2200.get('max_drawdown', '-')}` | Decision: `{eth_2200.get('decision', '-')}`",
        f"- `ETH 2600` Sharpe: `{eth_2600.get('sharpe', '-')}` | MDD: `{eth_2600.get('max_drawdown', '-')}` | Decision: `{eth_2600.get('decision', '-')}`",
        "",
        "## Parameters",
    ]
    for key, value in parameters.items():
        lines.append(f"- `{key} = {value}`")
    lines.extend(
        [
            "",
            "## Scope",
            f"- Carry reference: `{packet.get('carry_reference_period', '-')}`",
            f"- Survivability reference: `{packet.get('survivability_reference_period', '-')}`",
            "",
            "## Notes",
        ]
    )
    for note in packet.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def write_shadow_packet(
    *,
    analysis_dir: Path,
    output_dir: Path,
    carry_paper_path: Path | None = None,
    survivability_paper_path: Path | None = None,
    friction_path: Path | None = None,
    walk_forward_path: Path | None = None,
) -> dict[str, Any]:
    packet = build_shadow_packet(
        analysis_dir=analysis_dir,
        carry_paper_path=carry_paper_path,
        survivability_paper_path=survivability_paper_path,
        friction_path=friction_path,
        walk_forward_path=walk_forward_path,
    )
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"btc_1d_shadow_packet_{stamp}.json"
    md_path = output_dir / f"btc_1d_shadow_packet_{stamp}.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(packet), encoding="utf-8")
    return {"packet": packet, "json_path": str(json_path), "md_path": str(md_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a BTC 1d shadow packet from the latest frozen baseline artifacts.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis_results"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = write_shadow_packet(analysis_dir=args.analysis_dir, output_dir=args.output_dir)
    print(json.dumps({"json": result["json_path"], "md": result["md_path"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
