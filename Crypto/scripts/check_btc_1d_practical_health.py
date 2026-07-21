from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a one-line BTC 1d practical health check from latest practical artifacts. "
            "Standard operating check order: practical -> research -> contract -> brief."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--as-json", action="store_true")
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_practical_health(*, analysis_dir: Path) -> dict[str, Any]:
    gate = _load_json(analysis_dir / "btc_1d_practical_promotion_gate_latest.json")
    brief = _load_json(analysis_dir / "btc_1d_operating_brief_latest.json")
    regression_lock_test = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    standard_check_order_reference = brief.get(
        "standard_check_order",
        ["practical", "research", "contract", "brief"],
    )

    status_label = gate.get("status_label", gate.get("decision", "unknown"))
    caveats = gate.get("caveats", [])
    carry_metrics = gate.get("carry_metrics", {})

    return {
        "regression_lock_test": regression_lock_test,
        "standard_check_order_reference": standard_check_order_reference,
        "ok": gate.get("ok", False),
        "status_label": status_label,
        "candidate": gate.get("candidate", brief.get("candidate", "unknown")),
        "scope": gate.get("scope", brief.get("scope", "unknown")),
        "caveat_count": len(caveats),
        "caveats": caveats,
        "sharpe": carry_metrics.get("sharpe"),
        "cagr": carry_metrics.get("cagr"),
        "max_drawdown": carry_metrics.get("max_drawdown"),
        "attack_challenger_remote_monitoring_deployment_handoff_ready": bool(
            brief.get("attack_challenger_remote_monitoring_deployment_handoff_ready", False)
        ),
        "attack_challenger_next_step": str(brief.get("attack_challenger_next_step", "")),
        "attack_challenger_bridge_report": str(
            brief.get("attack_challenger_bridge_report", "")
        ),
    }


def render_practical_health_line(result: dict[str, Any]) -> str:
    ok = "True" if result["ok"] else "False"
    sharpe = result["sharpe"]
    cagr = result["cagr"]
    max_drawdown = result["max_drawdown"]
    sharpe_part = f"{sharpe:.4f}" if isinstance(sharpe, (int, float)) else "n/a"
    cagr_part = f"{cagr:.2%}" if isinstance(cagr, (int, float)) else "n/a"
    mdd_part = f"{max_drawdown:.2%}" if isinstance(max_drawdown, (int, float)) else "n/a"
    return (
        f"BTC 1d practical health | status={result['status_label']} | ok={ok} | "
        f"candidate={result['candidate']} | sharpe={sharpe_part} | cagr={cagr_part} | "
        f"mdd={mdd_part} | caveats={result['caveat_count']}"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_practical_health(analysis_dir=args.analysis_dir)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(render_practical_health_line(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
