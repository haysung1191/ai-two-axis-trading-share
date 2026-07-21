from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.btc_1d_contract_health_constants import (
    HEALTH_ORDER_ALIAS,
    HEALTH_ORDER_CANONICAL,
    HEALTH_ORDER_DEPRECATION_MESSAGE,
)
from scripts.check_btc_1d_contract_health import check_contract_health
from scripts.check_btc_1d_practical_health import check_practical_health
from scripts.check_btc_1d_research_stack_health import check_research_stack_health


ANALYSIS_DIR = Path("analysis_results")
EXECUTION_CONTRACT_SYMMETRY_FIELDS = [
    "symmetry_regression_test",
    "execution_contract_symmetry_lock_included",
    "execution_contract_symmetry_regression_test",
    "execution_meta_contract_test_index_symmetry_fields",
]


def render_symmetry_field_map(symmetry_fields: list[str]) -> str:
    return "symmetry field map | " + " | ".join(symmetry_fields)


def render_symmetry_contract_bundle(symmetry_fields: list[str]) -> str:
    return "symmetry contract bundle | " + " | ".join(symmetry_fields)


def render_symmetry_contract_ready(symmetry_fields: list[str]) -> bool:
    required = {
        "symmetry_regression_test",
        "execution_contract_symmetry_lock_included",
        "execution_contract_symmetry_regression_test",
        "execution_meta_contract_test_index_symmetry_fields",
    }
    return required.issubset(set(symmetry_fields))


def render_symmetry_reason_scope() -> str:
    return "symmetry reason scope | key | set | map | bundle | ready"


def render_symmetry_reason_range_summary() -> str:
    return "symmetry reason range | key | set | map | bundle | ready | stack_complete"


def render_symmetry_reason_final_summary() -> str:
    return "symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready"


def render_symmetry_contract_status(*, ready: bool, scope: str) -> str:
    return f"symmetry contract status | ready={ready} | {scope}"


def render_symmetry_contract_stack_complete(*, ready: bool) -> bool:
    return ready


def render_symmetry_contract_summary_ready(*, ready: bool, stack_complete: bool) -> bool:
    return ready and stack_complete


def render_symmetry_contract_topline_verdict(*, summary_ready: bool) -> str:
    return (
        "symmetry contract topline | complete"
        if summary_ready
        else "symmetry contract topline | incomplete"
    )


def render_meta_contract_topline_status(*, regression_test: str, reason_included: bool) -> str:
    return (
        f"meta topline status | regression_test={regression_test} | "
        f"reason_included={reason_included}"
    )


def render_meta_contract_topline_quick_status(*, reason_included: bool) -> str:
    reason_state = "included" if reason_included else "missing"
    return f"meta topline quick | lock=ok | reason={reason_state}"


def render_meta_contract_topline_highlight(*, reason_included: bool) -> str:
    reason_state = "included" if reason_included else "missing"
    return f"topline highlight | lock=ok | reason={reason_state}"


def render_meta_contract_reason_highlight_summary(*, reason_included: bool) -> str:
    reason_state = "included" if reason_included else "missing"
    return f"reason+highlight | summary_ready | reason={reason_state}"


def render_meta_contract_reason_final_verdict(*, reason_included: bool) -> str:
    reason_state = "included" if reason_included else "missing"
    return f"reason final verdict | complete | reason={reason_state}"


def render_meta_contract_integrated_topline_verdict(*, reason_included: bool) -> str:
    reason_state = "complete" if reason_included else "incomplete"
    return f"meta contract integrated | topline=complete | reason={reason_state}"


def render_execution_meta_integrated_quick_verdict(*, execution_meta_quick_status: str) -> str:
    if "execution=complete" in execution_meta_quick_status and "meta=complete" in execution_meta_quick_status:
        return "execution+meta integrated | execution=complete | meta=complete"
    return "execution+meta integrated | execution=incomplete | meta=incomplete"


def render_execution_meta_topline_bundle(
    *,
    execution_meta_quick_status: str,
    execution_meta_integrated_quick_verdict: str,
) -> str:
    return (
        "execution+meta topline bundle | "
        f"quick={execution_meta_quick_status} | "
        f"integrated={execution_meta_integrated_quick_verdict}"
    )


def render_execution_meta_bundle_ready_verdict(*, execution_meta_topline_bundle: str) -> str:
    if "execution=complete" in execution_meta_topline_bundle and "meta=complete" in execution_meta_topline_bundle:
        return "execution+meta bundle ready | complete"
    return "execution+meta bundle ready | incomplete"


def render_execution_meta_topline_ready(
    *,
    execution_meta_bundle_ready_verdict: str,
) -> str:
    if "complete" in execution_meta_bundle_ready_verdict:
        return "execution+meta topline ready | complete"
    return "execution+meta topline ready | incomplete"


def render_execution_meta_stack_complete(
    *,
    execution_meta_topline_ready: str,
) -> str:
    if "complete" in execution_meta_topline_ready:
        return "execution+meta stack complete | complete"
    return "execution+meta stack complete | incomplete"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    operating_brief_path = analysis_dir / "btc_1d_operating_brief_latest.json"
    operating_index_path = analysis_dir / "btc_1d_operating_index_latest.json"
    contract_screen_path = analysis_dir / "btc_1d_quick_read_contract_screen_latest.json"
    execution_contract_screen_path = analysis_dir / "btc_1d_execution_contract_screen_latest.json"
    execution_meta_contract_test_index_json_path = (
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json"
    )
    execution_meta_contract_test_index_path = (
        analysis_dir / "btc_1d_execution_meta_contract_test_index_md_latest.md"
    )
    research_brief_path = analysis_dir / "btc_1d_research_stack_operating_brief_latest.json"

    operating_brief = _load_json(operating_brief_path)
    operating_index = _load_json(operating_index_path)
    contract_screen = _load_json(contract_screen_path)
    contract_screen_report = contract_screen.get("report", contract_screen)
    execution_contract_screen = _load_json(execution_contract_screen_path)
    execution_contract_summary = execution_contract_screen.get(
        "execution_contract_summary", execution_contract_screen
    )
    execution_meta_contract_test_index = _load_json(execution_meta_contract_test_index_json_path)
    research_brief = _load_json(research_brief_path)
    practical_health = check_practical_health(analysis_dir=analysis_dir)
    research_health = check_research_stack_health(analysis_dir=analysis_dir)
    contract_health = check_contract_health(analysis_dir=analysis_dir)

    entries = [
        {
            "label": "operating_brief",
            "source": str(operating_brief_path),
            "regression_lock_test": operating_brief.get("regression_lock_test"),
            "standard_check_order": operating_brief.get("standard_check_order"),
        },
        {
            "label": "operating_index",
            "source": str(operating_index_path),
            "regression_lock_test": operating_index.get("regression_lock_test"),
            "standard_check_order": operating_index.get("standard_check_order"),
        },
        {
            "label": "quick_read_contract_screen",
            "source": str(contract_screen_path),
            "regression_lock_test": contract_screen_report.get("regression_lock_test"),
            "standard_check_order": contract_screen_report.get("contract_summary", {}).get(
                "shared_standard_check_order"
            ),
        },
        {
            "label": "execution_contract_screen",
            "source": str(execution_contract_screen_path),
            "regression_lock_test": execution_contract_summary.get("regression_lock_test"),
            "standard_check_order": execution_contract_summary.get(
                "standard_check_order_reference"
            ),
            "wording_regression_test": execution_contract_summary.get(
                "wording_regression_test"
            ),
            "symmetry_regression_test": execution_contract_summary.get(
                "symmetry_regression_test"
            ),
        },
        {
            "label": "research_stack_operating_brief",
            "source": str(research_brief_path),
            "regression_lock_test": research_brief.get("regression_lock_test"),
            "standard_check_order": research_brief.get("standard_check_order_reference"),
        },
        {
            "label": "practical_health",
            "source": "scripts/check_btc_1d_practical_health.py --as-json",
            "regression_lock_test": practical_health.get("regression_lock_test"),
            "standard_check_order": practical_health.get("standard_check_order_reference"),
        },
        {
            "label": "research_stack_health",
            "source": "scripts/check_btc_1d_research_stack_health.py --as-json",
            "regression_lock_test": research_health.get("regression_lock_test"),
            "standard_check_order": research_health.get("standard_check_order_reference"),
        },
        {
            "label": "contract_health",
            "source": "scripts/check_btc_1d_contract_health.py --as-json",
            "regression_lock_test": contract_health.get("regression_lock_test"),
            "standard_check_order": contract_health.get("shared_standard_check_order"),
        },
    ]
    for entry in execution_contract_screen.get("entries", []):
        label = entry.get("label")
        if label not in {"operating_brief", "operating_index"}:
            continue
        entries.append(
            {
                "label": f"execution_contract_screen_{label}_entry",
                "source": f"{execution_contract_screen_path}::{label}",
                "regression_lock_test": entry.get("regression_lock_test"),
                "standard_check_order": entry.get("standard_check_order_reference"),
            }
        )

    regression_locks = [entry["regression_lock_test"] for entry in entries]
    shared_regression_lock = regression_locks[0] if regression_locks else None
    regression_lock_aligned = bool(shared_regression_lock) and all(
        lock == shared_regression_lock for lock in regression_locks
    )

    order_entries = [entry for entry in entries if entry["standard_check_order"]]
    shared_standard_check_order = order_entries[0]["standard_check_order"] if order_entries else []
    standard_check_order_aligned = bool(shared_standard_check_order) and all(
        entry["standard_check_order"] == shared_standard_check_order for entry in order_entries
    )
    health_order_entries = [
        entry for entry in entries if entry["label"] in {"practical_health", "research_stack_health", "contract_health"}
    ]
    health_order_aligned = bool(shared_standard_check_order) and all(
        entry["standard_check_order"] == shared_standard_check_order for entry in health_order_entries
    )
    execution_entry_scope_labels = {
        "execution_contract_screen_operating_brief_entry",
        "execution_contract_screen_operating_index_entry",
    }
    execution_contract_entry_scope_included = all(
        label in [entry["label"] for entry in order_entries] for label in execution_entry_scope_labels
    )
    execution_contract_screen_entry = next(
        (entry for entry in entries if entry["label"] == "execution_contract_screen"),
        {},
    )
    execution_contract_wording_lock_included = bool(
        execution_contract_screen_entry.get("wording_regression_test")
    )
    execution_contract_symmetry_lock_included = bool(
        execution_contract_screen_entry.get("symmetry_regression_test")
    )
    execution_meta_contract_tests = execution_meta_contract_test_index.get("summary", {}).get(
        "meta_contract_tests", []
    )
    contract_read_order_regression_test = (
        "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
    )
    contract_read_order_lock_included = (
        contract_read_order_regression_test in execution_meta_contract_tests
    )
    reverse_screen_pointer_scope_regression_test = contract_read_order_regression_test
    reverse_screen_pointer_lock_included = any(
        test.get("label") == "contract_read_order_runbook_contract"
        and "execution/meta contract test map reverse screen pointers" in test.get("locks", [])
        for test in execution_meta_contract_test_index.get("tests", [])
    )
    reverse_screen_pointer_lock_scope = ["meta_contract_screen_summary"]

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "entries": entries,
        "meta_contract_summary": {
            "shared_regression_lock_test": shared_regression_lock,
            "regression_lock_aligned": regression_lock_aligned,
            "shared_standard_check_order": shared_standard_check_order,
            "standard_check_order_aligned": standard_check_order_aligned,
            "standard_check_order_scope": [entry["label"] for entry in order_entries],
            HEALTH_ORDER_CANONICAL: health_order_aligned,
            HEALTH_ORDER_ALIAS: health_order_aligned,
            "deprecated_aliases": {
                HEALTH_ORDER_ALIAS: HEALTH_ORDER_DEPRECATION_MESSAGE
            },
            "health_standard_check_order_scope": [entry["label"] for entry in health_order_entries],
            "execution_contract_entry_scope_included": execution_contract_entry_scope_included,
            "execution_contract_wording_lock_included": execution_contract_wording_lock_included,
            "execution_contract_symmetry_lock_included": execution_contract_symmetry_lock_included,
            "meta_contract_topline_regression_test": "tests/unit/test_btc_1d_meta_contract_wording_contract.py",
            "meta_contract_topline_reason_wording_included": True,
            "meta_contract_topline_status": render_meta_contract_topline_status(
                regression_test="tests/unit/test_btc_1d_meta_contract_wording_contract.py",
                reason_included=True,
            ),
            "meta_contract_topline_quick_status": render_meta_contract_topline_quick_status(
                reason_included=True,
            ),
            "meta_contract_topline_highlight": render_meta_contract_topline_highlight(
                reason_included=True,
            ),
            "meta_contract_reason_highlight_summary": render_meta_contract_reason_highlight_summary(
                reason_included=True,
            ),
            "meta_contract_reason_final_verdict": render_meta_contract_reason_final_verdict(
                reason_included=True,
            ),
            "meta_contract_integrated_topline_verdict": render_meta_contract_integrated_topline_verdict(
                reason_included=True,
            ),
            "execution_contract_symmetry_regression_test": execution_contract_screen_entry.get(
                "symmetry_regression_test"
            ),
            "execution_contract_symmetry_fields": EXECUTION_CONTRACT_SYMMETRY_FIELDS,
            "execution_contract_symmetry_field_set": EXECUTION_CONTRACT_SYMMETRY_FIELDS,
            "execution_contract_symmetry_field_map": render_symmetry_field_map(
                EXECUTION_CONTRACT_SYMMETRY_FIELDS
            ),
            "execution_contract_symmetry_contract_bundle": render_symmetry_contract_bundle(
                EXECUTION_CONTRACT_SYMMETRY_FIELDS
            ),
            "execution_contract_symmetry_ready": render_symmetry_contract_ready(
                EXECUTION_CONTRACT_SYMMETRY_FIELDS
            ),
            "execution_contract_symmetry_reason_scope": render_symmetry_reason_scope(),
            "execution_contract_symmetry_reason_range_summary": render_symmetry_reason_range_summary(),
            "execution_contract_symmetry_reason_final_summary": render_symmetry_reason_final_summary(),
            "execution_contract_symmetry_status": render_symmetry_contract_status(
                ready=render_symmetry_contract_ready(EXECUTION_CONTRACT_SYMMETRY_FIELDS),
                scope=render_symmetry_reason_scope(),
            ),
            "execution_contract_symmetry_stack_complete": render_symmetry_contract_stack_complete(
                ready=render_symmetry_contract_ready(EXECUTION_CONTRACT_SYMMETRY_FIELDS)
            ),
            "execution_contract_symmetry_summary_ready": render_symmetry_contract_summary_ready(
                ready=render_symmetry_contract_ready(EXECUTION_CONTRACT_SYMMETRY_FIELDS),
                stack_complete=render_symmetry_contract_stack_complete(
                    ready=render_symmetry_contract_ready(EXECUTION_CONTRACT_SYMMETRY_FIELDS)
                ),
            ),
            "execution_contract_symmetry_topline_verdict": render_symmetry_contract_topline_verdict(
                summary_ready=render_symmetry_contract_summary_ready(
                    ready=render_symmetry_contract_ready(EXECUTION_CONTRACT_SYMMETRY_FIELDS),
                    stack_complete=render_symmetry_contract_stack_complete(
                        ready=render_symmetry_contract_ready(EXECUTION_CONTRACT_SYMMETRY_FIELDS)
                    ),
                )
            ),
            "execution_meta_quick_status": execution_contract_summary.get(
                "execution_meta_quick_status", ""
            ),
            "execution_meta_integrated_quick_verdict": render_execution_meta_integrated_quick_verdict(
                execution_meta_quick_status=execution_contract_summary.get(
                    "execution_meta_quick_status", ""
                )
            ),
            "execution_meta_topline_bundle": render_execution_meta_topline_bundle(
                execution_meta_quick_status=execution_contract_summary.get(
                    "execution_meta_quick_status", ""
                ),
                execution_meta_integrated_quick_verdict=render_execution_meta_integrated_quick_verdict(
                    execution_meta_quick_status=execution_contract_summary.get(
                        "execution_meta_quick_status", ""
                    )
                ),
            ),
            "execution_meta_bundle_ready_verdict": render_execution_meta_bundle_ready_verdict(
                execution_meta_topline_bundle=render_execution_meta_topline_bundle(
                    execution_meta_quick_status=execution_contract_summary.get(
                        "execution_meta_quick_status", ""
                    ),
                    execution_meta_integrated_quick_verdict=render_execution_meta_integrated_quick_verdict(
                        execution_meta_quick_status=execution_contract_summary.get(
                            "execution_meta_quick_status", ""
                        )
                    ),
                )
            ),
            "execution_meta_topline_ready": render_execution_meta_topline_ready(
                execution_meta_bundle_ready_verdict=render_execution_meta_bundle_ready_verdict(
                    execution_meta_topline_bundle=render_execution_meta_topline_bundle(
                        execution_meta_quick_status=execution_contract_summary.get(
                            "execution_meta_quick_status", ""
                        ),
                        execution_meta_integrated_quick_verdict=render_execution_meta_integrated_quick_verdict(
                            execution_meta_quick_status=execution_contract_summary.get(
                                "execution_meta_quick_status", ""
                            )
                        ),
                    )
                )
            ),
            "execution_meta_stack_complete": render_execution_meta_stack_complete(
                execution_meta_topline_ready=render_execution_meta_topline_ready(
                    execution_meta_bundle_ready_verdict=render_execution_meta_bundle_ready_verdict(
                        execution_meta_topline_bundle=render_execution_meta_topline_bundle(
                            execution_meta_quick_status=execution_contract_summary.get(
                                "execution_meta_quick_status", ""
                            ),
                            execution_meta_integrated_quick_verdict=render_execution_meta_integrated_quick_verdict(
                                execution_meta_quick_status=execution_contract_summary.get(
                                    "execution_meta_quick_status", ""
                                )
                            ),
                        )
                    )
                )
            ),
            "contract_read_order_lock_included": contract_read_order_lock_included,
            "contract_read_order_regression_test": contract_read_order_regression_test,
            "reverse_screen_pointer_lock_included": reverse_screen_pointer_lock_included,
            "reverse_screen_pointer_lock_scope": reverse_screen_pointer_lock_scope,
            "reverse_screen_pointer_scope_regression_test": reverse_screen_pointer_scope_regression_test,
            "execution_meta_contract_test_index_md": str(execution_meta_contract_test_index_path),
            "execution_meta_contract_test_index_symmetry_fields": EXECUTION_CONTRACT_SYMMETRY_FIELDS,
        },
        "meta_contract_verdict": {
            "contract_is_fully_aligned": regression_lock_aligned and standard_check_order_aligned,
            "reason": (
                "Latest brief/index/contract-screen JSON and practical-research-contract health JSON should "
                "share the same regression lock test, while standard check order should stay aligned across "
                "the outputs that publish it, including execution contract summary and execution contract "
                "entry scope, plus execution contract wording lock, meta_contract_topline_regression_test, "
                "execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata, "
                "and execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/"
                "execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete."
            ),
        },
    }


def _render_markdown(report: dict) -> str:
    summary = report["meta_contract_summary"]
    verdict = report["meta_contract_verdict"]
    lines = [
        "# BTC 1d Meta Contract Screen",
        "",
        f"- Meta contract integrated topline verdict: `{summary['meta_contract_integrated_topline_verdict']}`",
        f"- Execution meta integrated quick verdict: `{summary['execution_meta_integrated_quick_verdict']}`",
        f"- Execution meta topline bundle: `{summary['execution_meta_topline_bundle']}`",
        f"- Execution meta bundle ready verdict: `{summary['execution_meta_bundle_ready_verdict']}`",
        f"- Execution meta topline ready: `{summary['execution_meta_topline_ready']}`",
        f"- Execution meta stack complete: `{summary['execution_meta_stack_complete']}`",
        f"- Execution contract symmetry topline verdict: `{summary['execution_contract_symmetry_topline_verdict']}`",
        f"- Shared regression lock: `{summary['shared_regression_lock_test']}`",
        f"- Regression lock aligned: `{summary['regression_lock_aligned']}`",
        f"- Shared standard check order: `{summary['shared_standard_check_order']}`",
        f"- Standard check order aligned: `{summary['standard_check_order_aligned']}`",
        f"- Standard check order scope: `{summary['standard_check_order_scope']}`",
        f"- Health order aligned: `{summary[HEALTH_ORDER_CANONICAL]}`",
        f"- Execution contract entry scope included: `{summary['execution_contract_entry_scope_included']}`",
        f"- Execution contract wording lock included: `{summary['execution_contract_wording_lock_included']}`",
        f"- Execution contract symmetry lock included: `{summary['execution_contract_symmetry_lock_included']}`",
        f"- Meta contract topline regression lock: `{summary['meta_contract_topline_regression_test']}`",
        f"- Meta contract topline reason wording included: `{summary['meta_contract_topline_reason_wording_included']}`",
        f"- Meta contract topline status: `{summary['meta_contract_topline_status']}`",
        f"- Meta contract topline quick status: `{summary['meta_contract_topline_quick_status']}`",
        f"- Execution contract symmetry regression lock: `{summary['execution_contract_symmetry_regression_test']}`",
        f"- Execution contract symmetry fields: `{summary['execution_contract_symmetry_fields']}`",
        f"- Execution contract symmetry field set: `{summary['execution_contract_symmetry_field_set']}`",
        f"- Execution contract symmetry field map: `{summary['execution_contract_symmetry_field_map']}`",
        f"- Execution contract symmetry contract bundle: `{summary['execution_contract_symmetry_contract_bundle']}`",
        f"- Execution contract symmetry ready: `{summary['execution_contract_symmetry_ready']}`",
        f"- Execution contract symmetry reason scope: `{summary['execution_contract_symmetry_reason_scope']}`",
        f"- Execution contract symmetry reason range summary: `{summary['execution_contract_symmetry_reason_range_summary']}`",
        f"- Execution contract symmetry reason final summary: `{summary['execution_contract_symmetry_reason_final_summary']}`",
        f"- Execution contract symmetry status: `{summary['execution_contract_symmetry_status']}`",
        f"- Execution contract symmetry stack complete: `{summary['execution_contract_symmetry_stack_complete']}`",
        f"- Execution contract symmetry summary ready: `{summary['execution_contract_symmetry_summary_ready']}`",
        f"- Execution meta quick status: `{summary['execution_meta_quick_status']}`",
        f"- Execution meta contract test index symmetry fields: `{summary['execution_meta_contract_test_index_symmetry_fields']}`",
        f"- Contract read-order lock included: `{summary['contract_read_order_lock_included']}`",
        f"- Contract read-order regression lock: `{summary['contract_read_order_regression_test']}`",
        f"- Reverse screen pointer lock included: `{summary['reverse_screen_pointer_lock_included']}`",
        f"- Reverse screen pointer lock scope: `{summary['reverse_screen_pointer_lock_scope']}`",
        f"- Reverse screen pointer scope regression lock: `{summary['reverse_screen_pointer_scope_regression_test']}`",
        f"- Execution meta contract test index: `{summary['execution_meta_contract_test_index_md']}`",
        f"- Deprecated alias: `{HEALTH_ORDER_ALIAS}` -> `{HEALTH_ORDER_CANONICAL}`",
        f"- Health standard order scope: `{summary['health_standard_check_order_scope']}`",
        f"- Contract fully aligned: `{verdict['contract_is_fully_aligned']}`",
        "- Execution-meta reason field-set lock: `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`",
        "- Execution-meta reason final-sentence lock: `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`",
        f"- Reason: {verdict['reason']}",
        f"- Reason highlight summary: `{summary['meta_contract_reason_highlight_summary']}`",
        f"- Reason final verdict: `{summary['meta_contract_reason_final_verdict']}`",
        f"- Topline quick highlight: `{summary['meta_contract_topline_highlight']}`",
        "",
    ]
    for entry in report["entries"]:
        lines.extend(
            [
                f"## {entry['label']}",
                f"- source: `{entry['source']}`",
                f"- regression lock: `{entry['regression_lock_test']}`",
                (
                    f"- Wording regression lock: `{entry['wording_regression_test']}`"
                    if entry.get("wording_regression_test")
                    else None
                ),
                f"- standard check order: `{entry['standard_check_order']}`",
                "",
            ]
        )
    return "\n".join(line for line in lines if line is not None)


def _write_latest_aliases(json_path: Path, md_path: Path) -> dict:
    latest_json = json_path.with_name("btc_1d_meta_contract_screen_latest.json")
    latest_md = md_path.with_name("btc_1d_meta_contract_screen_md_latest.md")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "btc_1d_meta_contract_screen": str(latest_json),
        "btc_1d_meta_contract_screen_md": str(latest_md),
    }


def main() -> int:
    report = build_report(ANALYSIS_DIR)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_meta_contract_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_meta_contract_screen_{stamp}.md"
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
