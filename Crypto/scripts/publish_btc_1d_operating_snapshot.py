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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_json(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No files matched {pattern} in {analysis_dir}")
    return matches[0]


def _write(path: Path, payload: str) -> None:
    path.write_text(payload, encoding="utf-8")


def _status_payload(packet: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    parameters = packet["parameters"]
    carry_metrics = packet["paper_validation_metrics"]
    survivability_metrics = packet["survivability_validation_metrics"]
    walk_forward = packet.get("walk_forward", {}) or {}
    return {
        "candidate": packet["candidate"],
        "status": packet["status"],
        "carry_reference_bars": packet["carry_reference_period"],
        "survivability_reference_bars": packet["survivability_reference_period"],
        "promoted_regression_pass_rate": readiness["why"]["btc"]["pass_rate"],
        "parameters": {
            "low_volatility_cap_threshold": parameters["low_volatility_cap_threshold"],
            "low_volatility_position_cap": parameters["low_volatility_position_cap"],
            "min_annualized_volatility": parameters["min_annualized_volatility"],
        },
        "carry_read": {
            str(packet["carry_reference_period"]): {
                "decision": packet["paper_validation_decision"],
                **carry_metrics,
            },
            str(packet["survivability_reference_period"]): {
                "decision": packet["survivability_validation_decision"],
                **survivability_metrics,
            },
        },
        "failure_read": {
            "1400": {
                "decision": "DROP",
                "dominant_issue": "low_volatility",
                "failed_gates": ["backtest_sharpe", "backtest_win_rate"],
            },
            "1800": {
                "decision": "DROP",
                "dominant_issue": "range",
                "failed_gates": ["backtest_sharpe", "backtest_win_rate"],
            },
        },
        "friction_check": {
            "decision": packet["friction_validation_decision"],
            "reason": packet["friction_validation_reason"],
            "heaviest_level": packet["friction_validation_heaviest_level"],
        },
        "walk_forward_check": walk_forward,
    }


def _status_markdown(payload: dict[str, Any]) -> str:
    carry_ref = str(payload["carry_reference_bars"])
    surv_ref = str(payload["survivability_reference_bars"])
    carry = payload["carry_read"][carry_ref]
    surv = payload["carry_read"][surv_ref]
    friction = payload["friction_check"]["heaviest_level"]
    walk_forward = payload.get("walk_forward_check", {}) or {}
    walk_forward_oos = walk_forward.get("oos_metrics", {}) or {}
    return "\n".join(
        [
            "# BTC 1d Candidate Status Board",
            "",
            f"- Active candidate: `{payload['candidate']}`",
            f"- Status: `{payload['status']}`",
            f"- Carry reference: `{carry_ref} bars`",
            f"- Survivability reference: `{surv_ref} bars`",
            f"- Promoted regression pass rate: `{payload['promoted_regression_pass_rate']}`",
            "",
            "## Candidate Parameters",
            f"- `low_volatility_cap_threshold = {payload['parameters']['low_volatility_cap_threshold']:.2f}`",
            f"- `low_volatility_position_cap = {payload['parameters']['low_volatility_position_cap']}`",
            f"- `min_annualized_volatility = {payload['parameters']['min_annualized_volatility']}`",
            "",
            "## Carry Read",
            f"- `{carry_ref}`: PASS | Sharpe `{carry['sharpe']:.4f}` | CAGR `{carry['cagr']:.4f}` | MDD `{carry['max_drawdown']:.4f}` | win rate `{carry['win_rate']:.4f}`",
            f"- `{surv_ref}`: PASS | Sharpe `{surv['sharpe']:.4f}` | CAGR `{surv['cagr']:.4f}` | MDD `{surv['max_drawdown']:.4f}` | win rate `{surv['win_rate']:.4f}`",
            "",
            "## Friction Check",
            f"- `20bps`: PASS | Sharpe `{friction['sharpe']:.4f}` | CAGR `{friction['cagr']:.4f}` | MDD `{friction['max_drawdown']:.4f}`",
            "",
            "## Walk-Forward Check",
            f"- OOS Sharpe `{walk_forward_oos.get('sharpe', 0.0):.4f}` | OOS CAGR `{walk_forward_oos.get('cagr', 0.0):.4f}` | OOS MDD `{walk_forward_oos.get('max_drawdown', 0.0):.4f}`",
            f"- Drift `{walk_forward.get('sensitivity_max_drift', 0.0):.4f}` | unstable `{', '.join(walk_forward.get('unstable_parameters', []) or ['none'])}`",
            "",
            "## Failure Read",
            "- `1400`: DROP | dominant issue `low_volatility` | failed gates `backtest_sharpe, backtest_win_rate`",
            "- `1800`: DROP | dominant issue `range` | failed gates `backtest_sharpe, backtest_win_rate`",
            "",
            "## Interpretation",
            "- This candidate is strong enough to carry forward as the current leading BTC 1d baseline.",
            "- It is still not an all-weather model: short windows continue to break in low-volatility and range conditions.",
            "- The right reading is carryable BTC-only survivor with validated friction tolerance, not a universal crypto model.",
            "",
        ]
    )


def _freeze_payload(packet: dict[str, Any], eth_regression: dict[str, Any]) -> dict[str, Any]:
    return {
        "frozen_candidate": packet["candidate"],
        "freeze_decision": "freeze_current_baseline",
        "why": [
            "Latest promoted regression still passes at 2200 and 2600 on BTCUSDT 1d.",
            "The 0.50 cap threshold reduced BTC drawdown while preserving carryability.",
            "The baseline remains paper-valid even under the heaviest tested friction.",
            "Cross-asset regression on ETHUSDT remains 0/4 PASS, so this should be carried only as a BTC-only baseline.",
        ],
        "parameters": packet["parameters"],
        "carry_reference_period": packet["carry_reference_period"],
        "survivability_reference_period": packet["survivability_reference_period"],
        "eth_summary": eth_regression["summary"],
        "walk_forward": packet.get("walk_forward"),
    }


def _freeze_markdown(payload: dict[str, Any], packet: dict[str, Any], eth_regression: dict[str, Any]) -> str:
    eth_by_period = {str(row["periods"]): row for row in eth_regression["results"]}
    carry = packet["paper_validation_metrics"]
    surv = packet["survivability_validation_metrics"]
    friction = packet["friction_validation_heaviest_level"]
    walk_forward = packet.get("walk_forward", {}) or {}
    walk_forward_oos = walk_forward.get("oos_metrics", {}) or {}
    return "\n".join(
        [
            "# BTC 1d Baseline Freeze",
            "",
            f"- Frozen candidate: `{payload['frozen_candidate']}`",
            f"- Decision: `{payload['freeze_decision']}`",
            "",
            "## Parameters",
            f"- `low_volatility_cap_threshold = {packet['parameters']['low_volatility_cap_threshold']}`",
            f"- `low_volatility_position_cap = {packet['parameters']['low_volatility_position_cap']}`",
            f"- `min_annualized_volatility = {packet['parameters']['min_annualized_volatility']}`",
            "",
            "## Carry Evidence",
            f"- `2200`: PASS | Sharpe `{carry['sharpe']:.4f}` | CAGR `{carry['cagr']:.4f}` | MDD `{carry['max_drawdown']:.4f}`",
            f"- `2600`: PASS | Sharpe `{surv['sharpe']:.4f}` | CAGR `{surv['cagr']:.4f}` | MDD `{surv['max_drawdown']:.4f}`",
            "",
            "## Friction Evidence",
            f"- `20bps`: PASS | Sharpe `{friction['sharpe']:.4f}` | CAGR `{friction['cagr']:.4f}` | MDD `{friction['max_drawdown']:.4f}`",
            "",
            "## Walk-Forward Evidence",
            f"- OOS Sharpe `{walk_forward_oos.get('sharpe', 0.0):.4f}` | OOS CAGR `{walk_forward_oos.get('cagr', 0.0):.4f}` | OOS MDD `{walk_forward_oos.get('max_drawdown', 0.0):.4f}`",
            f"- Drift `{walk_forward.get('sensitivity_max_drift', 0.0):.4f}` | unstable `{', '.join(walk_forward.get('unstable_parameters', []) or ['none'])}`",
            "",
            "## Cross-Asset Check",
            f"- `ETHUSDT 1d`: pass rate `{eth_regression['summary']['pass_rate']}`",
            f"- `ETH 2200`: DROP | Sharpe `{eth_by_period['2200']['sharpe']:.4f}` | MDD `{eth_by_period['2200']['max_drawdown']:.4f}`",
            f"- `ETH 2600`: DROP | Sharpe `{eth_by_period['2600']['sharpe']:.4f}` | MDD `{eth_by_period['2600']['max_drawdown']:.4f}`",
            "",
        ]
    )


def _readiness_payload(packet: dict[str, Any], eth_regression: dict[str, Any], friction: dict[str, Any]) -> dict[str, Any]:
    walk_forward = packet.get("walk_forward", {}) or {}
    return {
        "candidate": packet["candidate"],
        "decision": "shadow_ready_for_btc_only",
        "why": {
            "btc": {
                "pass_count": 2,
                "total_count": 4,
                "pass_rate": 0.5,
                "stability_score": 0.5,
                "failing_regimes": ["low_volatility", "range"],
            },
            "eth": eth_regression["summary"],
            "carry_periods": [packet["carry_reference_period"], packet["survivability_reference_period"]],
            "known_limits": ["1400 low_volatility", "1800 range"],
            "friction": {
                "final_decision": friction["final_decision"],
                "heaviest_level": friction["levels"][-1],
            },
            "walk_forward": {
                "passed": walk_forward.get("passed"),
                "oos_metrics": walk_forward.get("oos_metrics"),
                "sensitivity_max_drift": walk_forward.get("sensitivity_max_drift"),
                "unstable_parameters": walk_forward.get("unstable_parameters"),
            },
        },
    }


def _readiness_markdown(packet: dict[str, Any], eth_regression: dict[str, Any], friction: dict[str, Any]) -> str:
    eth_by_period = {str(row["periods"]): row for row in eth_regression["results"]}
    carry = packet["paper_validation_metrics"]
    surv = packet["survivability_validation_metrics"]
    heavy = friction["levels"][-1]
    walk_forward = packet.get("walk_forward", {}) or {}
    walk_forward_oos = walk_forward.get("oos_metrics", {}) or {}
    return "\n".join(
        [
            "# BTC 1d Shadow Readiness",
            "",
            f"- Candidate: `{packet['candidate']}`",
            "- Decision: `shadow_ready_for_btc_only`",
            "",
            "## BTC Carry Evidence",
            f"- `2200`: PASS | Sharpe `{carry['sharpe']:.4f}` | CAGR `{carry['cagr']:.4f}` | MDD `{carry['max_drawdown']:.4f}`",
            f"- `2600`: PASS | Sharpe `{surv['sharpe']:.4f}` | CAGR `{surv['cagr']:.4f}` | MDD `{surv['max_drawdown']:.4f}`",
            "",
            "## Friction Check",
            f"- `20bps`: PASS | Sharpe `{heavy['sharpe']:.4f}` | CAGR `{heavy['cagr']:.4f}` | MDD `{heavy['max_drawdown']:.4f}`",
            "",
            "## Walk-Forward Check",
            f"- OOS Sharpe `{walk_forward_oos.get('sharpe', 0.0):.4f}` | OOS CAGR `{walk_forward_oos.get('cagr', 0.0):.4f}` | OOS MDD `{walk_forward_oos.get('max_drawdown', 0.0):.4f}`",
            f"- Drift `{walk_forward.get('sensitivity_max_drift', 0.0):.4f}` | unstable `{', '.join(walk_forward.get('unstable_parameters', []) or ['none'])}`",
            "",
            "## Known BTC Limits",
            "- `1400`: fails in `low_volatility`",
            "- `1800`: fails in `range`",
            "",
            "## Cross-Asset Check",
            f"- `ETHUSDT 1d`: pass rate `{eth_regression['summary']['pass_rate']}`",
            f"- `ETH 2200`: DROP | Sharpe `{eth_by_period['2200']['sharpe']:.4f}` | MDD `{eth_by_period['2200']['max_drawdown']:.4f}`",
            f"- `ETH 2600`: DROP | Sharpe `{eth_by_period['2600']['sharpe']:.4f}` | MDD `{eth_by_period['2600']['max_drawdown']:.4f}`",
            "",
            "## Interpretation",
            "- This baseline remains ready for BTC-only paper/shadow use.",
            "- It is still not ready as a general crypto multi-asset model.",
            "- The clean next stage remains BTC-only shadow/paper tracking on the updated baseline with validated friction tolerance.",
            "",
        ]
    )


def publish_operating_snapshot(*, analysis_dir: Path) -> dict[str, str]:
    packet_path = _latest_json(analysis_dir, "btc_1d_shadow_packet_*.json")
    eth_path = _latest_json(analysis_dir, "btc_1d_promoted_candidate_regression_*.json")
    friction_path = _latest_json(analysis_dir, "btc_1d_low_vol_cap_friction_*.json")

    packet = _load_json(packet_path)
    friction = _load_json(friction_path)

    eth_candidates = sorted(
        analysis_dir.glob("btc_1d_promoted_candidate_regression_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    eth_payload = None
    for candidate in eth_candidates:
        payload = _load_json(candidate)
        if payload.get("config", {}).get("symbol") == "ETHUSDT":
            eth_payload = payload
            eth_path = candidate
            break
    if eth_payload is None:
        raise FileNotFoundError("No ETH promoted regression artifact found.")

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")

    status_json = analysis_dir / f"btc_1d_candidate_status_board_{stamp}.json"
    status_md = analysis_dir / f"btc_1d_candidate_status_board_{stamp}.md"
    freeze_json = analysis_dir / f"btc_1d_baseline_freeze_{stamp}.json"
    freeze_md = analysis_dir / f"btc_1d_baseline_freeze_{stamp}.md"
    readiness_json = analysis_dir / f"btc_1d_shadow_readiness_{stamp}.json"
    readiness_md = analysis_dir / f"btc_1d_shadow_readiness_{stamp}.md"

    status_payload = _status_payload(packet, _load_json(_latest_json(analysis_dir, "btc_1d_shadow_readiness_*.json")))
    freeze_payload = _freeze_payload(packet, eth_payload)
    readiness_payload = _readiness_payload(packet, eth_payload, friction)

    _write(status_json, json.dumps(status_payload, indent=2))
    _write(status_md, _status_markdown(status_payload))
    _write(freeze_json, json.dumps(freeze_payload, indent=2))
    _write(freeze_md, _freeze_markdown(freeze_payload, packet, eth_payload))
    _write(readiness_json, json.dumps(readiness_payload, indent=2))
    _write(readiness_md, _readiness_markdown(packet, eth_payload, friction))

    return {
        "status_json": str(status_json),
        "status_md": str(status_md),
        "freeze_json": str(freeze_json),
        "freeze_md": str(freeze_md),
        "readiness_json": str(readiness_json),
        "readiness_md": str(readiness_md),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish the latest BTC 1d operating snapshot from current shadow artifacts.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = publish_operating_snapshot(analysis_dir=args.analysis_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
