from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


PAPER_EXECUTION_CONTRACT_FIELDS = [
    "paper_execution_contract_checked",
    "paper_execution_contract_aligned",
    "paper_execution_contract_checked_aligned",
    "paper_execution_contract_aligned_aligned",
    "paper_execution_contract_checked_summary_aligned",
    "paper_execution_contract_aligned_summary_aligned",
    "paper_execution_contract_checked_aligned_entry_aligned",
    "paper_execution_contract_aligned_aligned_entry_aligned",
    "paper_execution_contract_checked_summary_aligned_entry_aligned",
    "paper_execution_contract_aligned_summary_aligned_entry_aligned",
    "paper_execution_contract_checked_aligned_summary_aligned",
    "paper_execution_contract_aligned_aligned_summary_aligned",
    "paper_execution_contract_checked_summary_aligned_summary_aligned",
    "paper_execution_contract_aligned_summary_aligned_summary_aligned",
]

CONTRACT_HEALTH_FIELDS = [
    "contract_health_operating_contract_aligned",
    "contract_health_paper_execution_contract_aligned",
    "contract_health_contracts_are_well_partitioned",
]


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    regression_lock_test = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    operating_brief_path = analysis_dir / "btc_1d_operating_brief_latest.json"
    operating_index_path = analysis_dir / "btc_1d_operating_index_latest.json"
    research_brief_path = analysis_dir / "btc_1d_research_stack_operating_brief_latest.json"

    operating_brief = _load_json(operating_brief_path)
    operating_index = _load_json(operating_index_path)
    research_brief = _load_json(research_brief_path)
    paper_execution_contract_alignment = {
        field: bool(operating_brief.get(field, False)) == bool(operating_index.get(field, False))
        for field in PAPER_EXECUTION_CONTRACT_FIELDS
    }
    paper_execution_contract_read = {
        "operating_brief": {
            field: bool(operating_brief.get(field, False)) for field in PAPER_EXECUTION_CONTRACT_FIELDS
        },
        "operating_index": {
            field: bool(operating_index.get(field, False)) for field in PAPER_EXECUTION_CONTRACT_FIELDS
        },
    }
    contract_health_read = {
        "operating_brief": {
            field: bool(operating_brief.get(field, False)) for field in CONTRACT_HEALTH_FIELDS
        },
        "operating_index": {
            field: bool(operating_index.get(field, False)) for field in CONTRACT_HEALTH_FIELDS
        },
    }

    contracts = [
        {
            "label": "operating_brief",
            "path": str(operating_brief_path),
            "quick_read_order_version": operating_brief.get("quick_read_order_version"),
            "quick_read_order": operating_brief.get("quick_read_order", []),
            "standard_check_order": operating_brief.get("standard_check_order", []),
            "paper_execution_contract": paper_execution_contract_read["operating_brief"],
        },
        {
            "label": "operating_index",
            "path": str(operating_index_path),
            "quick_read_order_version": operating_index.get("quick_read_order_version"),
            "quick_read_order": operating_index.get("quick_read_order", []),
            "standard_check_order": operating_index.get("standard_check_order", []),
            "paper_execution_contract": paper_execution_contract_read["operating_index"],
        },
        {
            "label": "research_stack_operating_brief",
            "path": str(research_brief_path),
            "quick_read_order_version": research_brief.get("quick_read_order_version"),
            "quick_read_order": research_brief.get("quick_read_order", []),
            "standard_check_order": research_brief.get("standard_check_order", []),
        },
    ]

    operating_contract_aligned = (
        contracts[0]["quick_read_order_version"] == contracts[1]["quick_read_order_version"]
        and contracts[0]["quick_read_order"] == contracts[1]["quick_read_order"]
    )
    paper_execution_contract_aligned = all(paper_execution_contract_alignment.values())
    research_contract_distinct = (
        contracts[2]["quick_read_order_version"] != contracts[0]["quick_read_order_version"]
        and contracts[2]["quick_read_order"] != contracts[0]["quick_read_order"]
    )
    contract_health_alignment = {
        "contract_health_operating_contract_aligned": (
            contract_health_read["operating_brief"]["contract_health_operating_contract_aligned"]
            == operating_contract_aligned
            and contract_health_read["operating_index"]["contract_health_operating_contract_aligned"]
            == operating_contract_aligned
        ),
        "contract_health_paper_execution_contract_aligned": (
            contract_health_read["operating_brief"]["contract_health_paper_execution_contract_aligned"]
            == paper_execution_contract_aligned
            and contract_health_read["operating_index"]["contract_health_paper_execution_contract_aligned"]
            == paper_execution_contract_aligned
        ),
        "contract_health_contracts_are_well_partitioned": (
            contract_health_read["operating_brief"]["contract_health_contracts_are_well_partitioned"]
            == (
                operating_contract_aligned
                and paper_execution_contract_aligned
                and research_contract_distinct
            )
            and contract_health_read["operating_index"]["contract_health_contracts_are_well_partitioned"]
            == (
                operating_contract_aligned
                and paper_execution_contract_aligned
                and research_contract_distinct
            )
        ),
    }
    contract_health_aligned = all(contract_health_alignment.values())

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "regression_lock_test": regression_lock_test,
        "contracts": contracts,
        "contract_summary": {
            "operating_brief_version": contracts[0]["quick_read_order_version"],
            "operating_index_version": contracts[1]["quick_read_order_version"],
            "research_stack_version": contracts[2]["quick_read_order_version"],
            "operating_contract_aligned": operating_contract_aligned,
            "paper_execution_contract_aligned": paper_execution_contract_aligned,
            "paper_execution_contract_alignment": paper_execution_contract_alignment,
            "contract_health_read": contract_health_read,
            "contract_health_alignment": contract_health_alignment,
            "contract_health_aligned": contract_health_aligned,
            "research_contract_distinct": research_contract_distinct,
            "shared_standard_check_order": contracts[0]["standard_check_order"],
        },
        "contract_verdict": {
            "preferred_operating_contract_version": contracts[0]["quick_read_order_version"],
            "preferred_research_contract_version": contracts[2]["quick_read_order_version"],
            "contracts_are_well_partitioned": (
                operating_contract_aligned
                and paper_execution_contract_aligned
                and research_contract_distinct
            ),
            "reason": (
                "Operating brief and operating index should share the same operating_v3 quick-read contract, "
                "share the same paper execution self-check mirror, keep contract health mirrors aligned with "
                "the quick-read contract truth, while the research brief should keep "
                "its distinct research_stack_v2 ordering."
            ),
        },
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Quick Read Contract Screen",
        "",
        f"- Operating brief version: `{report['contract_summary']['operating_brief_version']}`",
        f"- Operating index version: `{report['contract_summary']['operating_index_version']}`",
        f"- Research stack version: `{report['contract_summary']['research_stack_version']}`",
        f"- Operating contract aligned: `{report['contract_summary']['operating_contract_aligned']}`",
        f"- Paper execution contract aligned: `{report['contract_summary']['paper_execution_contract_aligned']}`",
        f"- Contract health aligned: `{report['contract_summary']['contract_health_aligned']}`",
        f"- Research contract distinct: `{report['contract_summary']['research_contract_distinct']}`",
        f"- Shared standard check order: `{report['contract_summary']['shared_standard_check_order']}`",
        f"- Contracts well partitioned: `{report['contract_verdict']['contracts_are_well_partitioned']}`",
        f"- Reason: {report['contract_verdict']['reason']}",
        "- Regression lock: `tests/unit/test_btc_1d_operating_cli_help_contract.py`",
        "",
    ]
    for contract in report["contracts"]:
        lines.extend(
            [
                f"## {contract['label']}",
                f"- path: `{contract['path']}`",
                f"- version: `{contract['quick_read_order_version']}`",
                f"- standard check order: `{contract['standard_check_order']}`",
                f"- order: `{contract['quick_read_order']}`",
                (
                    f"- paper execution contract: `{contract.get('paper_execution_contract', {})}`"
                    if contract["label"] != "research_stack_operating_brief"
                    else ""
                ),
                (
                    f"- contract health: `{report['contract_summary']['contract_health_read'].get(contract['label'], {})}`"
                    if contract["label"] != "research_stack_operating_brief"
                    else ""
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _write_latest_aliases(json_path: Path, md_path: Path) -> dict:
    latest_json = json_path.with_name("btc_1d_quick_read_contract_screen_latest.json")
    latest_md = md_path.with_name("btc_1d_quick_read_contract_screen_md_latest.md")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "btc_1d_quick_read_contract_screen": str(latest_json),
        "btc_1d_quick_read_contract_screen_md": str(latest_md),
    }


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_quick_read_contract_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_quick_read_contract_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    latest_aliases = _write_latest_aliases(json_path, md_path)
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_aliases": latest_aliases,
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
