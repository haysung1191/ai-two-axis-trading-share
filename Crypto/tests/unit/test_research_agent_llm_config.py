from app.domains.research.research_agent import ResearchAgent


def test_research_agent_llm_config_detection(monkeypatch) -> None:
    monkeypatch.delenv("RESEARCH_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("RESEARCH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("RESEARCH_LLM_MODEL", raising=False)
    assert ResearchAgent.is_llm_configured() is False

    monkeypatch.setenv("RESEARCH_LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
    monkeypatch.setenv("RESEARCH_LLM_API_KEY", "test-key")
    monkeypatch.setenv("RESEARCH_LLM_MODEL", "gemini-2.0-flash")
    assert ResearchAgent.is_llm_configured() is True
