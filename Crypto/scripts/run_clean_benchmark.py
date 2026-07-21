from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import Spec
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.service import GovernanceRunService

DEFAULT_GROUPS = [
    "full_system",
    "no_mutation",
    "no_regime_validation",
    "no_multi_asset_gate",
    "no_overfitting_gate",
    "search_budget_stress",
    "cost_friction_stress",
]


def build_base_metadata() -> dict[str, Any]:
    return {
        "strategy_name": "benchmark_validation",
        "position_size": 0.1,
        "expected_max_drawdown": 0.05,
        "fee_bps": 8.0,
        "slippage_bps": 8.0,
        "min_sharpe": 0.3,
        "max_drawdown": 0.4,
        "min_win_rate": 0.4,
        "min_cagr": 0.0,
        "proposal_count": 10,
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        "ohlcv_interval": "1h",
        "ohlcv_start_ts": "2024-01-01T00:00:00Z",
        "ohlcv_end_ts": "2024-02-01T00:00:00Z",
        "evaluation_workers": 4,
        "allow_synthetic_ohlcv_fallback": False,
        "mutation_enabled": True,
        "diversity_enabled": True,
        "multi_asset_gate_enabled": True,
        "regime_validation_enabled": True,
        "overfitting_gate_enabled": True,
        "benchmark_profile": "clean_benchmark_v1",
        "timeframe": "1h",
    }


def build_group_metadata(group_name: str, repetition: int) -> dict[str, Any]:
    metadata = build_base_metadata()
    metadata["benchmark_group"] = group_name
    metadata["benchmark_repetition"] = repetition

    if group_name == "no_mutation":
        metadata["mutation_enabled"] = False
    elif group_name == "no_regime_validation":
        metadata["regime_validation_enabled"] = False
    elif group_name == "no_multi_asset_gate":
        metadata["multi_asset_gate_enabled"] = False
    elif group_name == "no_overfitting_gate":
        metadata["overfitting_gate_enabled"] = False
    elif group_name == "search_budget_stress":
        metadata["proposal_count"] = 20
        metadata["benchmark_stress"] = "proposal_count_20"
    elif group_name == "cost_friction_stress":
        metadata["fee_bps"] = 20.0
        metadata["slippage_bps"] = 20.0
        metadata["benchmark_stress"] = "fee_slippage_20bps"

    return metadata


def build_spec(group_name: str, repetition: int) -> Spec:
    metadata = build_group_metadata(group_name, repetition)
    return Spec(
        run_goal=f"Clean benchmark {group_name}",
        context="Controlled benchmark batch for governance-aware strategy validation paper.",
        requirements=[
            "benchmark-batch",
            f"group:{group_name}",
            "strategy-validation-only",
            "deterministic-seed:42",
        ],
        metadata=metadata,
    )


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run clean benchmark batches for the paper.")
    parser.add_argument("--groups", nargs="*", default=DEFAULT_GROUPS)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-iterations", type=int, default=6)
    parser.add_argument("--artifacts-root", default="artifacts")
    parser.add_argument("--logs-root", default="logs")
    parser.add_argument(
        "--manifest",
        default="paper_results/clean_benchmark_manifest.json",
        help="Path to write the batch manifest.",
    )
    parser.add_argument("--talk-delay-sec", type=float, default=0.0)
    args = parser.parse_args()

    service = GovernanceRunService(
        artifact_store=ArtifactStore(root_dir=Path(args.artifacts_root)),
        run_logger=RunLogger(root_dir=Path(args.logs_root)),
        talk_delay_sec=args.talk_delay_sec,
    )

    manifest_runs: list[dict[str, Any]] = []
    for group_name in args.groups:
        for repetition in range(1, max(1, args.repetitions) + 1):
            spec = build_spec(group_name, repetition)
            result = service.start_run(spec=spec, max_iterations=args.max_iterations)
            state = result["state"]
            manifest_runs.append(
                {
                    "run_id": result["run_id"],
                    "group": group_name,
                    "repetition": repetition,
                    "decision": str(state.get("status") or state.get("decision_record", {}).get("decision", "UNKNOWN")),
                    "spec_metadata": spec.metadata,
                }
            )
            print(f"[{group_name} #{repetition}] run_id={result['run_id']}")

    manifest = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "groups": list(args.groups),
        "repetitions": args.repetitions,
        "max_iterations": args.max_iterations,
        "runs": manifest_runs,
    }
    write_manifest(Path(args.manifest), manifest)
    print(f"Wrote manifest to {args.manifest}")


if __name__ == "__main__":
    main()
