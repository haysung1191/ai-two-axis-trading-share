from __future__ import annotations

from scripts.btc_1d_contract_health_constants import (
    HEALTH_ORDER_ALIAS,
    HEALTH_ORDER_CANONICAL,
    HEALTH_ORDER_DEPRECATION_MESSAGE,
)
from scripts.check_btc_1d_contract_health import build_parser as build_contract_health_parser
from tests.unit.test_btc_1d_operating_cli_help_contract import STANDARD_ORDER_TEXT


def test_contract_cli_help_and_alias_migration_wording_are_jointly_locked() -> None:
    description = build_contract_health_parser().description

    assert description is not None
    assert STANDARD_ORDER_TEXT in description
    assert f"{HEALTH_ORDER_ALIAS} is a deprecated alias for {HEALTH_ORDER_CANONICAL}." in description
    assert HEALTH_ORDER_DEPRECATION_MESSAGE == (
        f"Deprecated alias for {HEALTH_ORDER_CANONICAL}. Prefer {HEALTH_ORDER_CANONICAL}."
    )
