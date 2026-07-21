import json
from pathlib import Path

from app.domains.governance.contracts import Spec
from app.domains.research.research_agent import ResearchAgent
from app.domains.strategy.registry import StrategyRegistry


def test_research_agent_includes_mutation_proposals_from_registry(tmp_path: Path) -> None:
    registry_path = tmp_path / "strategy_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "strategies": [
                    {
                        "strategy_id": "mean_reversion_v3_approved",
                        "first_seen_run": "run-a",
                        "latest_run": "run-z",
                        "best_sharpe": 1.8,
                        "best_cagr": 0.2,
                        "best_drawdown": 0.08,
                        "runs": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def fake_llm(_: str) -> str:
        return json.dumps(
            {
                "proposals": [
                    {
                        "strategy_name": "breakout_new",
                        "source_type": "new",
                        "parent_strategy": None,
                        "hypothesis": "new strategy",
                        "market_regime": "volatility",
                        "required_features": ["open", "high", "low", "close", "volume"],
                        "parameters": {"lookback": {"min": 20, "max": 50}},
                        "constraints": {"max_leverage": 1.0, "max_position_size": 0.2},
                        "implementation_notes": "notes",
                    }
                ]
            }
        )

    agent = ResearchAgent(
        llm_callable=fake_llm,
        default_proposal_count=10,
        strategy_registry=StrategyRegistry(registry_path=registry_path),
    )
    proposals = agent.generate_strategy_proposals(
        Spec(run_goal="mutation test", context="unit", requirements=[], metadata={}),
        n_proposals=10,
    )

    assert len(proposals) == 10
    mutation = [p for p in proposals if p.source_type == "mutation"]
    assert mutation
    assert mutation[0].parent_strategy == "mean_reversion_v3_approved"
    assert any(p.strategy_name.startswith("mean_reversion_") for p in mutation)


def test_strategy_registry_stores_parent_strategy_lineage(tmp_path: Path) -> None:
    registry = StrategyRegistry(registry_path=tmp_path / "strategy_registry.json")
    registry.update_strategy(
        strategy_id="mean_reversion_v4_approved",
        run_id="run-2",
        sharpe=1.9,
        cagr=0.25,
        drawdown=0.07,
        source_type="mutation",
        parent_strategy="mean_reversion_v3_approved",
    )
    payload = registry.load()
    entry = payload["strategies"][0]
    assert entry["source_type"] == "mutation"
    assert entry["parent_strategy"] == "mean_reversion_v3_approved"
    assert entry["runs"][0]["parent_strategy"] == "mean_reversion_v3_approved"
