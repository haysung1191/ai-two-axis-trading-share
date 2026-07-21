from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domains.evaluation.scorecard import EvaluationScorecard
from app.domains.governance.contracts import ApprovedStrategy, ApprovedStrategyBundle
from app.domains.governance.policy_bundle import PolicyBundleExporter


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _backup_file(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    backup_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_root / path.name)


def _load_scorecards(run_dir: Path) -> dict[str, EvaluationScorecard]:
    path = run_dir / "evaluation_scorecards.json"
    payload = _load_json(path)
    if not isinstance(payload, list):
        return {}
    result: dict[str, EvaluationScorecard] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        scorecard = EvaluationScorecard.model_validate(row)
        result[scorecard.strategy.strategy_id] = scorecard
    return result


def _load_candidate_proposal(run_dir: Path, strategy_name: str) -> dict[str, Any]:
    path = run_dir / "candidates" / strategy_name / "proposal.json"
    if not path.exists():
        return {}
    payload = _load_json(path)
    return payload if isinstance(payload, dict) else {}


def refresh_run_artifacts(
    *,
    run_id: str,
    artifacts_dir: Path,
    reexport_dir: Path,
    backup_root: Path,
) -> dict[str, Any]:
    run_dir = artifacts_dir / run_id
    approved_path = run_dir / "approved_strategy.json"
    approved_payload = _load_json(approved_path)
    approved_bundle = ApprovedStrategyBundle.model_validate(approved_payload)
    scorecards = _load_scorecards(run_dir)
    refresh_time = datetime.now(tz=UTC)

    refreshed_winners: list[ApprovedStrategy] = []
    strategy_lookup: dict[str, dict[str, Any]] = {}
    recovered_parameters = 0

    for winner in approved_bundle.winners:
        scorecard = scorecards.get(winner.strategy_id)
        proposal = _load_candidate_proposal(run_dir, scorecard.strategy.name if scorecard else winner.strategy_id.removesuffix("_approved"))

        params = dict(winner.parameters)
        if not params:
            scorecard_params = dict(scorecard.metadata.strategy_parameters) if scorecard else {}
            proposal_params = proposal.get("parameters", {}) if isinstance(proposal.get("parameters"), dict) else {}
            if scorecard_params:
                params = scorecard_params
            elif proposal_params:
                params = proposal_params
            if params:
                recovered_parameters += 1

        refreshed_winners.append(
            ApprovedStrategy(
                strategy_id=winner.strategy_id,
                approved_at=refresh_time,
                source_run_id=winner.source_run_id,
                symbol=winner.symbol,
                timeframe=winner.timeframe,
                parameters=params,
                metrics=winner.metrics,
                risk_limits=winner.risk_limits,
            )
        )

        if scorecard is not None:
            strategy_lookup[winner.strategy_id] = {
                "name": scorecard.strategy.name,
                "strategy_name": scorecard.strategy.name,
                "source_type": scorecard.strategy.source_type,
                "category": scorecard.strategy.category,
                "parent_strategy": scorecard.strategy.parent_strategy,
            }
        else:
            strategy_lookup[winner.strategy_id] = {
                "name": proposal.get("strategy_name", winner.strategy_id.removesuffix("_approved")),
                "strategy_name": proposal.get("strategy_name", winner.strategy_id.removesuffix("_approved")),
                "source_type": proposal.get("source_type", "new"),
                "category": proposal.get("strategy_category", "mean_reversion"),
                "parent_strategy": proposal.get("parent_strategy"),
            }

    refreshed_bundle = ApprovedStrategyBundle(winners=refreshed_winners, top_k=approved_bundle.top_k)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = backup_root / run_id / timestamp
    _backup_file(approved_path, backup_dir)
    publish_dir = reexport_dir / run_id / "publish"
    _backup_file(publish_dir / "policy_bundle.json", backup_dir)
    _backup_file(publish_dir / "manifest.json", backup_dir)

    approved_path.write_text(refreshed_bundle.model_dump_json(indent=2), encoding="utf-8")

    existing_bundle_path = publish_dir / "policy_bundle.json"
    bundle_mode = "shadow"
    if existing_bundle_path.exists():
        existing_payload = _load_json(existing_bundle_path)
        if isinstance(existing_payload, dict):
            bundle_mode = str(existing_payload.get("bundle_mode", "shadow"))

    exporter = PolicyBundleExporter(root_dir=reexport_dir)
    artifacts = exporter.export(
        run_id=run_id,
        approved_bundle=refreshed_bundle,
        strategy_lookup=strategy_lookup,
        bundle_mode=bundle_mode,
    )

    return {
        "run_id": run_id,
        "approved_strategy_path": str(approved_path),
        "policy_bundle_path": str(artifacts.bundle_path),
        "manifest_path": str(artifacts.manifest_path),
        "backup_dir": str(backup_dir),
        "recovered_parameters": recovered_parameters,
        "bundle_id": artifacts.bundle_payload["bundle_id"],
        "bundle_valid_until": artifacts.bundle_payload["strategies"][0]["valid_until"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh local approved strategy and policy bundle artifacts for manual use.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--backup-dir", default="artifacts_refresh_backups")
    args = parser.parse_args()

    result = refresh_run_artifacts(
        run_id=args.run_id,
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        backup_root=Path(args.backup_dir),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
