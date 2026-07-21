import json

from app.domains.governance.contracts import Spec
from app.domains.research.research_agent import CATEGORIES, ResearchAgent


def test_research_agent_diversity() -> None:
    def fake_llm(_: str) -> str:
        proposals = []
        for i in range(10):
            proposals.append(
                {
                    "strategy_name": f"candidate_{i}",
                    "strategy_category": CATEGORIES[i % len(CATEGORIES)],
                    "source_type": "new",
                    "parent_strategy": None,
                    "hypothesis": "diverse strategy",
                    "market_regime": "trend" if i % 2 == 0 else "range",
                    "required_features": ["open", "high", "low", "close", "volume"],
                    "parameters": {"window": {"min": 10, "max": 30}},
                    "constraints": {"max_leverage": 1.0, "max_position_size": 0.2},
                    "implementation_notes": "notes",
                }
            )
        return json.dumps({"proposals": proposals})

    agent = ResearchAgent(llm_callable=fake_llm, default_proposal_count=10)
    result = agent.generate_strategy_proposals(
        Spec(run_goal="diversity", context="unit", requirements=[], metadata={}),
    )

    assert len(result) == 10
    categories = {p.strategy_category for p in result}
    assert categories == set(CATEGORIES)
    new_count = len([p for p in result if p.source_type == "new"])
    mutation_count = len([p for p in result if p.source_type == "mutation"])
    assert new_count == 5
    assert mutation_count == 5
