from __future__ import annotations

from scripts.check_btc_1d_contract_health import build_parser as build_contract_health_parser
from scripts.check_btc_1d_practical_health import build_parser as build_practical_health_parser
from scripts.check_btc_1d_research_stack_health import build_parser as build_research_stack_health_parser
from scripts.check_btc_1d_shadow_health import build_parser as build_shadow_health_parser
from scripts.print_btc_1d_operating_brief import build_parser as build_operating_brief_parser
from scripts.run_btc_1d_shadow_update import build_parser as build_shadow_update_parser


STANDARD_ORDER_TEXT = "practical -> research -> contract -> brief"


def test_operating_cli_help_descriptions_share_standard_order_wording() -> None:
    descriptions = [
        build_operating_brief_parser().description,
        build_shadow_update_parser().description,
        build_practical_health_parser().description,
        build_research_stack_health_parser().description,
        build_contract_health_parser().description,
        build_shadow_health_parser().description,
    ]

    assert all(description is not None for description in descriptions)
    assert all(STANDARD_ORDER_TEXT in description for description in descriptions if description is not None)


def test_shadow_and_contract_health_parsers_expose_machine_json_flag() -> None:
    shadow_args = build_shadow_health_parser().parse_args(["--as-json"])
    contract_args = build_contract_health_parser().parse_args(["--as-json"])

    assert shadow_args.as_json is True
    assert contract_args.as_json is True
