from src.policy.runtime import read_policy_flags


def test_allowlist_parsing_edge_cases(monkeypatch) -> None:
    monkeypatch.setenv("POLICY_SYMBOL_ALLOWLIST", " krw-btc , KRW-BTC, ,krw-eth ")
    flags = read_policy_flags()
    assert flags.symbol_allowlist == ("KRW-BTC", "KRW-ETH")


def test_policy_max_score_delta_invalid_value_fallback(monkeypatch) -> None:
    monkeypatch.setenv("POLICY_MAX_SCORE_DELTA", "not-a-number")
    flags = read_policy_flags()
    assert flags.max_score_delta == 0.15


def test_invalid_boolean_env_falls_back_to_safe_default(monkeypatch) -> None:
    monkeypatch.setenv("POLICY_ACTIVE", "flase")
    flags = read_policy_flags()
    assert flags.active_enabled is False
