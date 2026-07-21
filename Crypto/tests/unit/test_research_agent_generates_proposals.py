from app.domains.governance.contracts import Spec
from app.domains.research.research_agent import ResearchAgent


def test_research_agent_generates_proposals() -> None:
    def fake_llm(_: str) -> str:
        return """
{
  "proposals": [
    {
      "strategy_name": "mean_reversion_llm",
      "hypothesis": "Mean reversion in range markets.",
      "market_regime": "range",
      "required_features": ["open", "high", "low", "close", "volume"],
      "parameters": {"window": {"min": 10, "max": 30}, "z_threshold": {"min": 1.0, "max": 2.0}},
      "constraints": {"max_leverage": 1.0, "max_position_size": 0.2},
      "implementation_notes": "Use rolling z-score."
    },
    {
      "strategy_name": "momentum_llm",
      "hypothesis": "Momentum persists in trend regimes.",
      "market_regime": "trend",
      "required_features": ["open", "high", "low", "close", "volume"],
      "parameters": {"fast_window": [10, 40], "slow_window": [50, 200]},
      "constraints": {"max_leverage": 1.0, "max_position_size": 0.2},
      "implementation_notes": "Use fast/slow filters."
    }
  ]
}
"""

    agent = ResearchAgent(llm_callable=fake_llm, default_proposal_count=5)
    proposals = agent.generate_strategy_proposals(
        Spec(run_goal="research", context="unit test", requirements=[], metadata={}),
        n_proposals=5,
    )

    assert len(proposals) == 5
    assert proposals[0].strategy_name == "mean_reversion_llm"
    assert isinstance(proposals[0].parameters.get("window"), float)
    assert "window_range" in proposals[0].parameters
