from datetime import UTC, datetime
from pathlib import Path

from app.domains.evaluation.scorecard import (
    EvaluationMetadata,
    EvaluationScorecard,
    MultiAssetAggregateMetrics,
    OverfittingMetrics,
    RegimeMetrics,
    SingleAssetSummaryMetrics,
    StrategyIdentity,
)
from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import Spec, StrategyProposalSet
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow


def test_research_node_produces_valid_strategy_proposal(tmp_path: Path) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
    )
    state = {
        "run_id": "run-research-1",
        "spec": Spec(
            run_goal="research proposal generation",
            context="unit test",
            requirements=[],
            metadata={},
        ).model_dump(mode="json"),
    }

    updates = workflow._research_node(state)
    proposal_set = StrategyProposalSet.model_validate(updates["strategy_proposal"])
    candidates = updates["strategy_candidates"]

    assert len(proposal_set.proposals) == 10
    assert len(candidates) == 10
    assert all(item.required_features == ["open", "high", "low", "close", "volume"] for item in proposal_set.proposals)
    assert any(item.strategy_name == "krw_low_vol_breakout" for item in proposal_set.proposals)
    assert any(item.strategy_name == "krw_btc_swing_trend" for item in proposal_set.proposals)


def test_research_node_uses_single_asset_btc_seed_set(tmp_path: Path) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
    )
    state = {
        "run_id": "run-research-btc-only",
        "spec": Spec(
            run_goal="research proposal generation",
            context="single asset btc unit test",
            requirements=[],
            metadata={"symbols": ["KRW-BTC"], "ohlcv_interval": "4h"},
        ).model_dump(mode="json"),
    }

    updates = workflow._research_node(state)
    proposal_set = StrategyProposalSet.model_validate(updates["strategy_proposal"])

    names = {item.strategy_name for item in proposal_set.proposals}
    assert "krw_btc_swing_trend" in names
    assert "krw_btc_mean_reversion" in names
    assert "krw_low_vol_breakout" not in names
    assert "krw_trend_pullback_reaccel" not in names
    assert "krw_volume_surge_breakout" not in names


def test_evaluate_node_writes_scorecard_into_sanitized_candidate_dir(tmp_path: Path, monkeypatch) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
    )
    run_id = "run-evaluate-1"
    scorecard = EvaluationScorecard(
        run_id=run_id,
        strategy=StrategyIdentity(
            name="Breakout/Trend:Test?",
            strategy_id="strategy-1",
            source_type="new",
            category="momentum",
        ),
        single_asset=SingleAssetSummaryMetrics(symbol="BTCUSDT", trades=10, sharpe=1.2, max_drawdown=0.1, win_rate=0.5, cagr=0.2),
        multi_asset=MultiAssetAggregateMetrics(sharpe_mean=1.2),
        regime=RegimeMetrics(),
        overfitting=OverfittingMetrics(),
        qa_passed=True,
        candidate_pass=True,
        metadata=EvaluationMetadata(symbols_tested=["BTCUSDT"], evaluated_at=datetime.now(UTC), deterministic_seed=42),
    )

    monkeypatch.setattr(workflow._candidate_evaluator, "evaluate_candidates", lambda **kwargs: [scorecard])
    monkeypatch.setattr(
        workflow._candidate_evaluator,
        "scorecard_to_compatibility_payload",
        lambda s: {
            "strategy_name": s.strategy.name,
            "backtest_report": {"strategy_name": s.strategy.name},
            "overfitting_report": {},
            "risk_report": {},
        },
    )
    monkeypatch.setattr(
        workflow._candidate_evaluator,
        "serialize_scorecards",
        lambda scorecards: "[" + ",".join(s.model_dump_json() for s in scorecards) + "]",
    )

    state = {
        "run_id": run_id,
        "spec": Spec(
            run_goal="evaluate sanitized paths",
            context="unit test",
            requirements=[],
            metadata={},
        ).model_dump(mode="json"),
        "strategy_proposal": StrategyProposalSet(proposals=[]).model_dump(mode="json"),
        "engineered_strategies": [
            {
                "strategy_name": "Breakout/Trend:Test?",
                "strategy_category": "momentum",
                "source_type": "new",
                "parent_strategy": None,
                "file_path": str(tmp_path / "artifacts" / run_id / "strategies" / "Breakout_Trend_Test_.py"),
                "parameters": {},
                "constraints": [],
            }
        ],
    }

    workflow._evaluate_node(state)

    sanitized_dir = tmp_path / "artifacts" / run_id / "candidates" / "Breakout_Trend_Test_"
    assert (sanitized_dir / "scorecard.json").exists()


def test_safe_artifact_name_avoids_windows_reserved_names(tmp_path: Path) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
    )
    assert workflow._safe_artifact_name("CON") == "strategy_CON"
    assert workflow._safe_artifact_name("LPT1.py") == "strategy_LPT1.py"
