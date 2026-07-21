from app.domains.evaluation.decision_policy import DecisionPolicy
from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.evaluation.scorecard import (
    EvaluationMetadata,
    EvaluationScorecard,
    MultiAssetAggregateMetrics,
    OverfittingMetrics,
    RegimeMetrics,
    SingleAssetSummaryMetrics,
    StrategyIdentity,
)
from app.domains.governance.contracts import Spec
from app.domains.research.research_agent import ResearchAgent


def _scorecard() -> EvaluationScorecard:
    return EvaluationScorecard(
        run_id="run-1",
        strategy=StrategyIdentity(
            name="test_strategy",
            strategy_id="test_strategy_approved",
            source_type="new",
            parent_strategy=None,
            category="mean_reversion",
        ),
        single_asset=SingleAssetSummaryMetrics(
            symbol="BTCUSDT",
            trades=20,
            sharpe=0.8,
            max_drawdown=0.2,
            win_rate=0.5,
            cagr=0.1,
            equity_curve_summary={},
            equity_curve=[],
        ),
        multi_asset=MultiAssetAggregateMetrics(
            sharpe_mean=0.8,
            sharpe_std=3.0,
            drawdown_mean=0.2,
            drawdown_worst=0.3,
        ),
        regime=RegimeMetrics(
            sharpe_by_regime={},
            drawdown_by_regime={},
            sharpe_regime_std=3.0,
        ),
        overfitting=OverfittingMetrics(
            is_metrics={},
            oos_metrics={},
            walk_forward=[],
            sensitivity_drift=0.0,
            unstable_parameters=[],
            flags=["unstable_parameters"],
        ),
        qa_passed=True,
        candidate_pass=False,
        failed_gates=["cross_asset_instability", "regime_instability", "overfitting_flags"],
        passed_gates=[],
        metadata=EvaluationMetadata(
            evaluated_at="2026-03-29T00:00:00+00:00",
            symbols_tested=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            deterministic_seed=42,
            strategy_parameters={},
            dataset_fingerprint="fp",
        ),
    )


def test_research_agent_disables_mutation_when_requested() -> None:
    agent = ResearchAgent(default_proposal_count=4)
    spec = Spec(
        run_goal="test",
        context="test context",
        requirements=[],
        metadata={"mutation_enabled": False, "diversity_enabled": False},
    )

    proposals = agent.generate_strategy_proposals(spec, n_proposals=4)

    assert len(proposals) == 4
    assert all(item.source_type == "new" for item in proposals)


def test_decision_policy_skips_disabled_gates() -> None:
    policy = DecisionPolicy()
    spec = Spec(
        run_goal="test",
        context="test context",
        requirements=[],
        metadata={
            "multi_asset_gate_enabled": False,
            "regime_validation_enabled": False,
            "overfitting_gate_enabled": False,
        },
    )

    result = policy.decide(
        run_id="run-1",
        spec=spec,
        scorecards=[_scorecard()],
        reject_count=0,
        iteration=1,
    )

    assert result["decision_record"]["decision"] == "PASS"


def test_candidate_evaluator_accepts_iso_timestamp_metadata() -> None:
    default_ms = 0
    parsed = CandidateEvaluator._timestamp_to_milliseconds("2024-02-01T00:00:00Z", default_ms)
    assert parsed > 0
