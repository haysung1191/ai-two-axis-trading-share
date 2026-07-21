from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ANALYSIS_DIR = Path("analysis_results")
REGRESSION_LOCK_TEST = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
WORDING_REGRESSION_TEST = "tests/unit/test_btc_1d_execution_contract_wording_contract.py"
SYMMETRY_REGRESSION_TEST = "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py"
STANDARD_CHECK_ORDER_REFERENCE = ["practical", "research", "contract", "brief"]
SYMMETRY_FIELDS = [
    "symmetry_regression_test",
    "execution_contract_symmetry_lock_included",
    "execution_contract_symmetry_regression_test",
    "execution_meta_contract_test_index_symmetry_fields",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_execution_contract_read(
    *,
    execution_contract_aligned: bool,
    paper_execution_read: str,
) -> str:
    aligned_label = "aligned" if execution_contract_aligned else "drifted"
    if paper_execution_read:
        return f"execution contract | {aligned_label} | {paper_execution_read}"
    return f"execution contract | {aligned_label}"


def render_execution_contract_health_line(
    *,
    execution_health_line: str,
    execution_contract_read: str,
) -> str:
    if execution_health_line and execution_contract_read:
        return f"{execution_health_line} || {execution_contract_read}"
    return execution_health_line or execution_contract_read


def render_paper_ledger_snapshot_read(snapshot: dict | None) -> str:
    payload = snapshot or {}
    return (
        "paper ledger | "
        f"open={int(payload.get('open_position_count', 0))} | "
        f"closed={int(payload.get('closed_position_count', 0))} | "
        f"exit_fills={int(payload.get('exit_fill_count', 0))} | "
        f"orders={int(payload.get('order_count', 0))} | "
        f"fills={int(payload.get('fill_count', 0))}"
    )


def _paper_summary_contract_bool(summary: dict, field: str, legacy_field: str) -> bool:
    return bool(summary.get(field, summary.get(legacy_field, False)))


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


def render_execution_meta_quick_status(
    *,
    execution_contract_aligned: bool,
    meta_contract_integrated_topline_verdict: str,
) -> str:
    execution_state = "complete" if execution_contract_aligned else "incomplete"
    meta_state = "complete" if "topline=complete" in meta_contract_integrated_topline_verdict else "incomplete"
    return f"execution+meta quick | execution={execution_state} | meta={meta_state}"


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


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    operating_brief_path = analysis_dir / "btc_1d_operating_brief_latest.json"
    operating_index_path = analysis_dir / "btc_1d_operating_index_latest.json"
    paper_nightly_path = analysis_dir / "btc_1d_paper_nightly_summary_latest.json"
    quick_read_contract_screen_path = (
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json"
    )
    meta_contract_screen_path = analysis_dir / "btc_1d_meta_contract_screen_latest.json"
    execution_meta_contract_test_index_json_path = (
        analysis_dir / "btc_1d_execution_meta_contract_test_index_latest.json"
    )
    execution_meta_contract_test_index_path = (
        analysis_dir / "btc_1d_execution_meta_contract_test_index_md_latest.md"
    )

    operating_brief = _load_json(operating_brief_path)
    operating_index = _load_json(operating_index_path)
    paper_nightly = _load_json(paper_nightly_path)
    quick_read_contract_screen = _load_json(quick_read_contract_screen_path)
    quick_read_contract_summary = quick_read_contract_screen.get(
        "contract_summary", quick_read_contract_screen
    )
    meta_contract_screen = _load_json(meta_contract_screen_path)
    meta_contract_summary = meta_contract_screen.get(
        "meta_contract_summary", meta_contract_screen
    )
    execution_meta_contract_test_index = _load_json(execution_meta_contract_test_index_json_path)

    entries = [
        {
            "label": "operating_brief",
            "source": str(operating_brief_path),
            "regression_lock_test": operating_brief.get("regression_lock_test", REGRESSION_LOCK_TEST),
            "standard_check_order_reference": operating_brief.get(
                "standard_check_order", STANDARD_CHECK_ORDER_REFERENCE
            ),
            "execution_health_line": operating_brief.get("execution_health_line", ""),
            "paper_nightly_health_line": operating_brief.get("paper_nightly_health_line", ""),
            "paper_execution_read": operating_brief.get("paper_execution_read", ""),
            "contract_health_aligned": bool(
                operating_brief.get("contract_health_aligned", False)
            ),
            "paper_execution_contract_checked": bool(
                operating_brief.get("paper_execution_contract_checked", False)
            ),
            "paper_execution_contract_aligned": bool(
                operating_brief.get("paper_execution_contract_aligned", False)
            ),
            "paper_execution_contract_checked_aligned": bool(
                operating_brief.get("paper_execution_contract_checked_aligned", False)
            ),
            "paper_execution_contract_aligned_aligned": bool(
                operating_brief.get("paper_execution_contract_aligned_aligned", False)
            ),
            "paper_execution_contract_checked_summary_aligned": bool(
                operating_brief.get("paper_execution_contract_checked_summary_aligned", False)
            ),
            "paper_execution_contract_aligned_summary_aligned": bool(
                operating_brief.get("paper_execution_contract_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_checked_aligned_entry_aligned": bool(
                operating_brief.get("paper_execution_contract_checked_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_aligned_aligned_entry_aligned": bool(
                operating_brief.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_checked_summary_aligned_entry_aligned": bool(
                operating_brief.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": bool(
                operating_brief.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_checked_aligned_summary_aligned": bool(
                operating_brief.get("paper_execution_contract_checked_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_aligned_aligned_summary_aligned": bool(
                operating_brief.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_checked_summary_aligned_summary_aligned": bool(
                operating_brief.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": bool(
                operating_brief.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
            ),
            "paper_ledger_snapshot_read": operating_brief.get(
                "paper_ledger_snapshot_read",
                render_paper_ledger_snapshot_read(operating_brief.get("paper_ledger_snapshot")),
            ),
        },
        {
            "label": "operating_index",
            "source": str(operating_index_path),
            "regression_lock_test": operating_index.get("regression_lock_test", REGRESSION_LOCK_TEST),
            "standard_check_order_reference": operating_index.get(
                "standard_check_order", STANDARD_CHECK_ORDER_REFERENCE
            ),
            "execution_health_line": operating_index.get("execution_health_line", ""),
            "paper_nightly_health_line": operating_index.get("paper_nightly_health_line", ""),
            "paper_execution_read": operating_index.get("paper_execution_read", ""),
            "contract_health_aligned": bool(
                operating_index.get("contract_health_aligned", False)
            ),
            "paper_execution_contract_checked": bool(
                operating_index.get("paper_execution_contract_checked", False)
            ),
            "paper_execution_contract_aligned": bool(
                operating_index.get("paper_execution_contract_aligned", False)
            ),
            "paper_execution_contract_checked_aligned": bool(
                operating_index.get("paper_execution_contract_checked_aligned", False)
            ),
            "paper_execution_contract_aligned_aligned": bool(
                operating_index.get("paper_execution_contract_aligned_aligned", False)
            ),
            "paper_execution_contract_checked_summary_aligned": bool(
                operating_index.get("paper_execution_contract_checked_summary_aligned", False)
            ),
            "paper_execution_contract_aligned_summary_aligned": bool(
                operating_index.get("paper_execution_contract_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_checked_aligned_entry_aligned": bool(
                operating_index.get("paper_execution_contract_checked_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_aligned_aligned_entry_aligned": bool(
                operating_index.get("paper_execution_contract_aligned_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_checked_summary_aligned_entry_aligned": bool(
                operating_index.get("paper_execution_contract_checked_summary_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": bool(
                operating_index.get("paper_execution_contract_aligned_summary_aligned_entry_aligned", False)
            ),
            "paper_execution_contract_checked_aligned_summary_aligned": bool(
                operating_index.get("paper_execution_contract_checked_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_aligned_aligned_summary_aligned": bool(
                operating_index.get("paper_execution_contract_aligned_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_checked_summary_aligned_summary_aligned": bool(
                operating_index.get("paper_execution_contract_checked_summary_aligned_summary_aligned", False)
            ),
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": bool(
                operating_index.get("paper_execution_contract_aligned_summary_aligned_summary_aligned", False)
            ),
            "paper_ledger_snapshot_read": operating_index.get(
                "paper_ledger_snapshot_read",
                render_paper_ledger_snapshot_read(operating_index.get("paper_ledger_snapshot")),
            ),
        },
    ]

    execution_health_line = entries[0]["execution_health_line"]
    paper_nightly_health_line = entries[0]["paper_nightly_health_line"]
    paper_execution_read = entries[0]["paper_execution_read"]

    execution_health_aligned = all(
        entry["execution_health_line"] == execution_health_line for entry in entries
    )
    paper_nightly_health_aligned = all(
        entry["paper_nightly_health_line"] == paper_nightly_health_line for entry in entries
    )
    paper_execution_read_aligned = all(
        entry["paper_execution_read"] == paper_execution_read for entry in entries
    )
    contract_health_aligned_read = entries[0]["contract_health_aligned"]
    contract_health_entry_aligned = all(
        entry["contract_health_aligned"] == contract_health_aligned_read for entry in entries
    )
    paper_execution_contract_checked = entries[0]["paper_execution_contract_checked"]
    paper_execution_contract_aligned_read = entries[0]["paper_execution_contract_aligned"]
    paper_execution_contract_checked_aligned = all(
        entry["paper_execution_contract_checked"] == paper_execution_contract_checked
        for entry in entries
    )
    paper_execution_contract_aligned_aligned = all(
        entry["paper_execution_contract_aligned"] == paper_execution_contract_aligned_read
        for entry in entries
    )
    paper_ledger_snapshot_read = entries[0]["paper_ledger_snapshot_read"]
    paper_ledger_snapshot_aligned = all(
        entry["paper_ledger_snapshot_read"] == paper_ledger_snapshot_read for entry in entries
    )
    paper_summary_snapshot_read = paper_nightly.get(
        "paper_ledger_snapshot_read",
        render_paper_ledger_snapshot_read(paper_nightly.get("paper_ledger_snapshot")),
    )
    paper_summary_execution_contract_checked = bool(
        paper_nightly.get("execution_contract_checked", False)
    )
    paper_summary_execution_contract_aligned = bool(
        paper_nightly.get("execution_contract_aligned", False)
    )
    quick_read_contract_health_aligned = bool(
        quick_read_contract_summary.get("contract_health_aligned", False)
    )
    paper_summary_execution_contract_checked_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_checked_aligned",
        "execution_contract_paper_execution_contract_checked_aligned",
    )
    paper_summary_execution_contract_aligned_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_aligned_aligned",
        "execution_contract_paper_execution_contract_aligned_aligned",
    )
    paper_summary_execution_contract_checked_summary_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_checked_summary_aligned",
        "execution_contract_paper_execution_contract_checked_summary_aligned",
    )
    paper_summary_execution_contract_aligned_summary_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_aligned_summary_aligned",
        "execution_contract_paper_execution_contract_aligned_summary_aligned",
    )
    paper_summary_execution_contract_checked_aligned_entry_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_checked_aligned_entry_aligned",
        "execution_contract_paper_execution_contract_checked_aligned_entry_aligned",
    )
    paper_summary_execution_contract_aligned_aligned_entry_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_aligned_aligned_entry_aligned",
        "execution_contract_paper_execution_contract_aligned_aligned_entry_aligned",
    )
    paper_summary_execution_contract_checked_summary_aligned_entry_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_checked_summary_aligned_entry_aligned",
        "execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned",
    )
    paper_summary_execution_contract_aligned_summary_aligned_entry_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_aligned_summary_aligned_entry_aligned",
        "execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned",
    )
    paper_summary_execution_contract_checked_aligned_summary_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_checked_aligned_summary_aligned",
        "execution_contract_paper_execution_contract_checked_aligned_summary_aligned",
    )
    paper_summary_execution_contract_aligned_aligned_summary_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_aligned_aligned_summary_aligned",
        "execution_contract_paper_execution_contract_aligned_aligned_summary_aligned",
    )
    paper_summary_execution_contract_checked_summary_aligned_summary_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_checked_summary_aligned_summary_aligned",
        "execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned",
    )
    paper_summary_execution_contract_aligned_summary_aligned_summary_aligned = _paper_summary_contract_bool(
        paper_nightly,
        "paper_execution_contract_aligned_summary_aligned_summary_aligned",
        "execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned",
    )
    paper_ledger_snapshot_summary_aligned = paper_ledger_snapshot_read == paper_summary_snapshot_read
    paper_execution_contract_checked_summary_aligned = (
        paper_execution_contract_checked == paper_summary_execution_contract_checked
    )
    paper_execution_contract_aligned_summary_aligned = (
        paper_execution_contract_aligned_read == paper_summary_execution_contract_aligned
    )
    contract_health_summary_aligned = (
        contract_health_aligned_read == quick_read_contract_health_aligned
    )
    paper_execution_contract_checked_aligned_read = entries[0][
        "paper_execution_contract_checked_aligned"
    ]
    paper_execution_contract_aligned_aligned_read = entries[0][
        "paper_execution_contract_aligned_aligned"
    ]
    paper_execution_contract_checked_summary_aligned_read = entries[0][
        "paper_execution_contract_checked_summary_aligned"
    ]
    paper_execution_contract_aligned_summary_aligned_read = entries[0][
        "paper_execution_contract_aligned_summary_aligned"
    ]
    paper_execution_contract_checked_aligned_entry_aligned_read = entries[0][
        "paper_execution_contract_checked_aligned_entry_aligned"
    ]
    paper_execution_contract_aligned_aligned_entry_aligned_read = entries[0][
        "paper_execution_contract_aligned_aligned_entry_aligned"
    ]
    paper_execution_contract_checked_summary_aligned_entry_aligned_read = entries[0][
        "paper_execution_contract_checked_summary_aligned_entry_aligned"
    ]
    paper_execution_contract_aligned_summary_aligned_entry_aligned_read = entries[0][
        "paper_execution_contract_aligned_summary_aligned_entry_aligned"
    ]
    paper_execution_contract_checked_aligned_summary_aligned_read = entries[0][
        "paper_execution_contract_checked_aligned_summary_aligned"
    ]
    paper_execution_contract_aligned_aligned_summary_aligned_read = entries[0][
        "paper_execution_contract_aligned_aligned_summary_aligned"
    ]
    paper_execution_contract_checked_summary_aligned_summary_aligned_read = entries[0][
        "paper_execution_contract_checked_summary_aligned_summary_aligned"
    ]
    paper_execution_contract_aligned_summary_aligned_summary_aligned_read = entries[0][
        "paper_execution_contract_aligned_summary_aligned_summary_aligned"
    ]
    paper_execution_contract_checked_aligned_entry_aligned = all(
        entry["paper_execution_contract_checked_aligned_entry_aligned"]
        == paper_execution_contract_checked_aligned_entry_aligned_read
        for entry in entries
    )
    paper_execution_contract_aligned_aligned_entry_aligned = all(
        entry["paper_execution_contract_aligned_aligned_entry_aligned"]
        == paper_execution_contract_aligned_aligned_entry_aligned_read
        for entry in entries
    )
    paper_execution_contract_checked_summary_aligned_entry_aligned = all(
        entry["paper_execution_contract_checked_summary_aligned_entry_aligned"]
        == paper_execution_contract_checked_summary_aligned_entry_aligned_read
        for entry in entries
    )
    paper_execution_contract_aligned_summary_aligned_entry_aligned = all(
        entry["paper_execution_contract_aligned_summary_aligned_entry_aligned"]
        == paper_execution_contract_aligned_summary_aligned_entry_aligned_read
        for entry in entries
    )
    paper_execution_contract_checked_aligned_summary_aligned = (
        paper_execution_contract_checked_aligned_summary_aligned_read
        == paper_summary_execution_contract_checked_aligned_summary_aligned
    )
    paper_execution_contract_aligned_aligned_summary_aligned = (
        paper_execution_contract_aligned_aligned_summary_aligned_read
        == paper_summary_execution_contract_aligned_aligned_summary_aligned
    )
    paper_execution_contract_checked_summary_aligned_summary_aligned = (
        paper_execution_contract_checked_summary_aligned_summary_aligned_read
        == paper_summary_execution_contract_checked_summary_aligned_summary_aligned
    )
    paper_execution_contract_aligned_summary_aligned_summary_aligned = (
        paper_execution_contract_aligned_summary_aligned_summary_aligned_read
        == paper_summary_execution_contract_aligned_summary_aligned_summary_aligned
    )

    paper_paths = {
        "paper_nightly_summary": operating_index.get("paper_nightly_summary", ""),
        "paper_nightly_summary_md": operating_index.get("paper_nightly_summary_md", ""),
    }

    execution_contract_aligned = (
        execution_health_aligned
        and paper_nightly_health_aligned
        and paper_execution_read_aligned
        and contract_health_entry_aligned
        and contract_health_summary_aligned
        and paper_execution_contract_checked_aligned
        and paper_execution_contract_aligned_aligned
        and paper_execution_contract_checked_summary_aligned
        and paper_execution_contract_aligned_summary_aligned
        and paper_execution_contract_checked_aligned_entry_aligned
        and paper_execution_contract_aligned_aligned_entry_aligned
        and paper_execution_contract_checked_summary_aligned_entry_aligned
        and paper_execution_contract_aligned_summary_aligned_entry_aligned
        and paper_execution_contract_checked_aligned_summary_aligned
        and paper_execution_contract_aligned_aligned_summary_aligned
        and paper_execution_contract_checked_summary_aligned_summary_aligned
        and paper_execution_contract_aligned_summary_aligned_summary_aligned
        and paper_ledger_snapshot_aligned
        and paper_ledger_snapshot_summary_aligned
    )
    execution_contract_read = render_execution_contract_read(
        execution_contract_aligned=execution_contract_aligned,
        paper_execution_read=paper_execution_read,
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
    reverse_screen_pointer_lock_scope = ["execution_contract_screen_summary"]

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "entries": entries,
        "paper_nightly_summary": {
            "source": str(paper_nightly_path),
            "paper_execution_read": paper_nightly.get("paper_execution_read", ""),
            "paper_execution_contract_checked": paper_summary_execution_contract_checked,
            "paper_execution_contract_aligned": paper_summary_execution_contract_aligned,
            "paper_execution_contract_checked_aligned": (
                paper_summary_execution_contract_checked_aligned
            ),
            "paper_execution_contract_aligned_aligned": (
                paper_summary_execution_contract_aligned_aligned
            ),
            "paper_execution_contract_checked_summary_aligned": (
                paper_summary_execution_contract_checked_summary_aligned
            ),
            "paper_execution_contract_aligned_summary_aligned": (
                paper_summary_execution_contract_aligned_summary_aligned
            ),
            "paper_execution_contract_checked_aligned_entry_aligned": (
                paper_summary_execution_contract_checked_aligned_entry_aligned
            ),
            "paper_execution_contract_aligned_aligned_entry_aligned": (
                paper_summary_execution_contract_aligned_aligned_entry_aligned
            ),
            "paper_execution_contract_checked_summary_aligned_entry_aligned": (
                paper_summary_execution_contract_checked_summary_aligned_entry_aligned
            ),
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": (
                paper_summary_execution_contract_aligned_summary_aligned_entry_aligned
            ),
            "paper_execution_contract_checked_aligned_summary_aligned": (
                paper_summary_execution_contract_checked_aligned_summary_aligned
            ),
            "paper_execution_contract_aligned_aligned_summary_aligned": (
                paper_summary_execution_contract_aligned_aligned_summary_aligned
            ),
            "paper_execution_contract_checked_summary_aligned_summary_aligned": (
                paper_summary_execution_contract_checked_summary_aligned_summary_aligned
            ),
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": (
                paper_summary_execution_contract_aligned_summary_aligned_summary_aligned
            ),
            "paper_nightly_health_line": paper_nightly.get("paper_nightly_health_line", ""),
            "intent_count": paper_nightly.get("intent_count"),
            "signed_request_count": paper_nightly.get("signed_request_count"),
            "paper_applied_count": paper_nightly.get("paper_applied_count"),
            "paper_duplicate_count": paper_nightly.get("paper_duplicate_count"),
            "paper_closed_count": paper_nightly.get("paper_closed_count"),
            "paper_open_count": paper_nightly.get("paper_open_count"),
            "paper_ledger_snapshot_read": paper_nightly.get(
                "paper_ledger_snapshot_read",
                render_paper_ledger_snapshot_read(paper_nightly.get("paper_ledger_snapshot")),
            ),
        },
        "execution_contract_summary": {
            "regression_lock_test": REGRESSION_LOCK_TEST,
            "wording_regression_test": WORDING_REGRESSION_TEST,
            "symmetry_regression_test": SYMMETRY_REGRESSION_TEST,
            "symmetry_fields": SYMMETRY_FIELDS,
            "symmetry_field_set": SYMMETRY_FIELDS,
            "symmetry_field_map": render_symmetry_field_map(SYMMETRY_FIELDS),
            "symmetry_contract_bundle": render_symmetry_contract_bundle(SYMMETRY_FIELDS),
            "symmetry_contract_ready": render_symmetry_contract_ready(SYMMETRY_FIELDS),
            "symmetry_reason_scope": render_symmetry_reason_scope(),
            "symmetry_reason_range_summary": render_symmetry_reason_range_summary(),
            "symmetry_reason_final_summary": render_symmetry_reason_final_summary(),
            "symmetry_contract_status": render_symmetry_contract_status(
                ready=render_symmetry_contract_ready(SYMMETRY_FIELDS),
                scope=render_symmetry_reason_scope(),
            ),
            "symmetry_contract_stack_complete": render_symmetry_contract_stack_complete(
                ready=render_symmetry_contract_ready(SYMMETRY_FIELDS)
            ),
            "symmetry_contract_summary_ready": render_symmetry_contract_summary_ready(
                ready=render_symmetry_contract_ready(SYMMETRY_FIELDS),
                stack_complete=render_symmetry_contract_stack_complete(
                    ready=render_symmetry_contract_ready(SYMMETRY_FIELDS)
                ),
            ),
            "symmetry_contract_topline_verdict": render_symmetry_contract_topline_verdict(
                summary_ready=render_symmetry_contract_summary_ready(
                    ready=render_symmetry_contract_ready(SYMMETRY_FIELDS),
                    stack_complete=render_symmetry_contract_stack_complete(
                        ready=render_symmetry_contract_ready(SYMMETRY_FIELDS)
                    ),
                )
            ),
            "meta_contract_integrated_topline_verdict": meta_contract_summary.get(
                "meta_contract_integrated_topline_verdict", ""
            ),
            "execution_meta_quick_status": render_execution_meta_quick_status(
                execution_contract_aligned=execution_contract_aligned,
                meta_contract_integrated_topline_verdict=meta_contract_summary.get(
                    "meta_contract_integrated_topline_verdict", ""
                ),
            ),
            "execution_meta_integrated_quick_verdict": meta_contract_summary.get(
                "execution_meta_integrated_quick_verdict", ""
            ),
            "execution_meta_topline_bundle": render_execution_meta_topline_bundle(
                execution_meta_quick_status=render_execution_meta_quick_status(
                    execution_contract_aligned=execution_contract_aligned,
                    meta_contract_integrated_topline_verdict=meta_contract_summary.get(
                        "meta_contract_integrated_topline_verdict", ""
                    ),
                ),
                execution_meta_integrated_quick_verdict=meta_contract_summary.get(
                    "execution_meta_integrated_quick_verdict", ""
                ),
            ),
            "execution_meta_bundle_ready_verdict": render_execution_meta_bundle_ready_verdict(
                execution_meta_topline_bundle=render_execution_meta_topline_bundle(
                    execution_meta_quick_status=render_execution_meta_quick_status(
                        execution_contract_aligned=execution_contract_aligned,
                        meta_contract_integrated_topline_verdict=meta_contract_summary.get(
                            "meta_contract_integrated_topline_verdict", ""
                        ),
                    ),
                    execution_meta_integrated_quick_verdict=meta_contract_summary.get(
                        "execution_meta_integrated_quick_verdict", ""
                    ),
                )
            ),
            "execution_meta_topline_ready": render_execution_meta_topline_ready(
                execution_meta_bundle_ready_verdict=render_execution_meta_bundle_ready_verdict(
                    execution_meta_topline_bundle=render_execution_meta_topline_bundle(
                        execution_meta_quick_status=render_execution_meta_quick_status(
                            execution_contract_aligned=execution_contract_aligned,
                            meta_contract_integrated_topline_verdict=meta_contract_summary.get(
                                "meta_contract_integrated_topline_verdict", ""
                            ),
                        ),
                        execution_meta_integrated_quick_verdict=meta_contract_summary.get(
                            "execution_meta_integrated_quick_verdict", ""
                        ),
                    )
                )
            ),
            "execution_meta_stack_complete": render_execution_meta_stack_complete(
                execution_meta_topline_ready=render_execution_meta_topline_ready(
                    execution_meta_bundle_ready_verdict=render_execution_meta_bundle_ready_verdict(
                        execution_meta_topline_bundle=render_execution_meta_topline_bundle(
                            execution_meta_quick_status=render_execution_meta_quick_status(
                                execution_contract_aligned=execution_contract_aligned,
                                meta_contract_integrated_topline_verdict=meta_contract_summary.get(
                                    "meta_contract_integrated_topline_verdict", ""
                                ),
                            ),
                            execution_meta_integrated_quick_verdict=meta_contract_summary.get(
                                "execution_meta_integrated_quick_verdict", ""
                            ),
                        )
                    )
                )
            ),
            "execution_meta_contract_test_index_md": str(execution_meta_contract_test_index_path),
            "execution_meta_contract_test_index_symmetry_fields": SYMMETRY_FIELDS,
            "contract_read_order_lock_included": contract_read_order_lock_included,
            "contract_read_order_regression_test": contract_read_order_regression_test,
            "reverse_screen_pointer_lock_included": reverse_screen_pointer_lock_included,
            "reverse_screen_pointer_lock_scope": reverse_screen_pointer_lock_scope,
            "reverse_screen_pointer_scope_regression_test": reverse_screen_pointer_scope_regression_test,
            "standard_check_order_reference": STANDARD_CHECK_ORDER_REFERENCE,
            "execution_contract_health_line": render_execution_contract_health_line(
                execution_health_line=execution_health_line,
                execution_contract_read=execution_contract_read,
            ),
            "execution_contract_read": execution_contract_read,
            "execution_health_line": execution_health_line,
            "paper_nightly_health_line": paper_nightly_health_line,
            "paper_execution_read": paper_execution_read,
            "contract_health_aligned_read": contract_health_aligned_read,
            "quick_read_contract_health_aligned": quick_read_contract_health_aligned,
            "paper_execution_contract_checked": paper_execution_contract_checked,
            "paper_execution_contract_aligned": paper_execution_contract_aligned_read,
            "paper_execution_contract_checked_aligned_read": (
                paper_execution_contract_checked_aligned_read
            ),
            "paper_execution_contract_aligned_aligned_read": (
                paper_execution_contract_aligned_aligned_read
            ),
            "paper_execution_contract_checked_summary_aligned_read": (
                paper_execution_contract_checked_summary_aligned_read
            ),
            "paper_execution_contract_aligned_summary_aligned_read": (
                paper_execution_contract_aligned_summary_aligned_read
            ),
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
            "execution_health_aligned": execution_health_aligned,
            "paper_nightly_health_aligned": paper_nightly_health_aligned,
            "paper_execution_read_aligned": paper_execution_read_aligned,
            "contract_health_entry_aligned": contract_health_entry_aligned,
            "contract_health_summary_aligned": contract_health_summary_aligned,
            "paper_execution_contract_checked_aligned": paper_execution_contract_checked_aligned,
            "paper_execution_contract_aligned_aligned": paper_execution_contract_aligned_aligned,
            "paper_execution_contract_checked_summary_aligned": paper_execution_contract_checked_summary_aligned,
            "paper_execution_contract_aligned_summary_aligned": paper_execution_contract_aligned_summary_aligned,
            "paper_execution_contract_checked_aligned_entry_aligned": (
                paper_execution_contract_checked_aligned_entry_aligned
            ),
            "paper_execution_contract_aligned_aligned_entry_aligned": (
                paper_execution_contract_aligned_aligned_entry_aligned
            ),
            "paper_execution_contract_checked_summary_aligned_entry_aligned": (
                paper_execution_contract_checked_summary_aligned_entry_aligned
            ),
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": (
                paper_execution_contract_aligned_summary_aligned_entry_aligned
            ),
            "paper_execution_contract_checked_aligned_summary_aligned": (
                paper_execution_contract_checked_aligned_summary_aligned
            ),
            "paper_execution_contract_aligned_aligned_summary_aligned": (
                paper_execution_contract_aligned_aligned_summary_aligned
            ),
            "paper_execution_contract_checked_summary_aligned_summary_aligned": (
                paper_execution_contract_checked_summary_aligned_summary_aligned
            ),
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": (
                paper_execution_contract_aligned_summary_aligned_summary_aligned
            ),
            "paper_ledger_snapshot_aligned": paper_ledger_snapshot_aligned,
            "paper_ledger_snapshot_summary_aligned": paper_ledger_snapshot_summary_aligned,
            "paper_summary_paths": paper_paths,
        },
        "execution_contract_verdict": {
            "execution_contract_aligned": execution_contract_aligned,
            "reason": (
                "Operating brief and operating index should publish the same execution health line, "
                "paper nightly health line, paper execution read, contract health aligned state, and paper ledger snapshot read from the latest paper nightly summary/quick-read contract truth, "
                "while symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata and "
                "execution_meta_quick_status/execution_meta_integrated_quick_verdict/execution_meta_topline_bundle/"
                "execution_meta_bundle_ready_verdict/execution_meta_topline_ready/execution_meta_stack_complete "
                "should stay aligned across the execution contract summary."
            ),
        },
    }


def _render_markdown(report: dict) -> str:
    summary = report["execution_contract_summary"]
    paper = report["paper_nightly_summary"]
    verdict = report["execution_contract_verdict"]
    lines = [
        "# BTC 1d Execution Contract Screen",
        "",
        f"- Symmetry contract topline verdict: `{summary['symmetry_contract_topline_verdict']}`",
        f"- Meta contract integrated topline verdict: `{summary['meta_contract_integrated_topline_verdict']}`",
        f"- Execution meta quick status: `{summary['execution_meta_quick_status']}`",
        f"- Execution meta integrated quick verdict: `{summary['execution_meta_integrated_quick_verdict']}`",
        f"- Execution meta topline bundle: `{summary['execution_meta_topline_bundle']}`",
        f"- Execution meta bundle ready verdict: `{summary['execution_meta_bundle_ready_verdict']}`",
        f"- Execution meta topline ready: `{summary['execution_meta_topline_ready']}`",
        f"- Execution meta stack complete: `{summary['execution_meta_stack_complete']}`",
        f"- Execution contract health: `{summary['execution_contract_health_line']}`",
        f"- Execution contract read: `{summary['execution_contract_read']}`",
        f"- Regression lock: `{summary['regression_lock_test']}`",
        f"- Wording regression lock: `{summary['wording_regression_test']}`",
        f"- Symmetry regression lock: `{summary['symmetry_regression_test']}`",
        f"- Symmetry fields: `{summary['symmetry_fields']}`",
        f"- Symmetry field set: `{summary['symmetry_field_set']}`",
        f"- Symmetry field map: `{summary['symmetry_field_map']}`",
        f"- Symmetry contract bundle: `{summary['symmetry_contract_bundle']}`",
        f"- Symmetry contract ready: `{summary['symmetry_contract_ready']}`",
        f"- Symmetry reason scope: `{summary['symmetry_reason_scope']}`",
        f"- Symmetry reason range summary: `{summary['symmetry_reason_range_summary']}`",
        f"- Symmetry reason final summary: `{summary['symmetry_reason_final_summary']}`",
        f"- Symmetry contract status: `{summary['symmetry_contract_status']}`",
        f"- Symmetry contract stack complete: `{summary['symmetry_contract_stack_complete']}`",
        f"- Symmetry contract summary ready: `{summary['symmetry_contract_summary_ready']}`",
        f"- Execution meta contract test index: `{summary['execution_meta_contract_test_index_md']}`",
        f"- Execution meta contract test index symmetry fields: `{summary['execution_meta_contract_test_index_symmetry_fields']}`",
        f"- Contract read-order lock included: `{summary['contract_read_order_lock_included']}`",
        f"- Contract read-order regression lock: `{summary['contract_read_order_regression_test']}`",
        f"- Reverse screen pointer lock included: `{summary['reverse_screen_pointer_lock_included']}`",
        f"- Reverse screen pointer lock scope: `{summary['reverse_screen_pointer_lock_scope']}`",
        f"- Reverse screen pointer scope regression lock: `{summary['reverse_screen_pointer_scope_regression_test']}`",
        f"- Standard check order: `{' > '.join(summary['standard_check_order_reference'])}`",
        f"- Execution health aligned: `{summary['execution_health_aligned']}`",
        f"- Paper nightly health aligned: `{summary['paper_nightly_health_aligned']}`",
        f"- Paper execution read aligned: `{summary['paper_execution_read_aligned']}`",
        f"- Contract health entry aligned: `{summary['contract_health_entry_aligned']}`",
        f"- Contract health summary aligned: `{summary['contract_health_summary_aligned']}`",
        f"- Paper execution contract checked aligned: `{summary['paper_execution_contract_checked_aligned']}`",
        f"- Paper execution contract aligned aligned: `{summary['paper_execution_contract_aligned_aligned']}`",
        f"- Paper execution contract checked summary aligned: `{summary['paper_execution_contract_checked_summary_aligned']}`",
        f"- Paper execution contract aligned summary aligned: `{summary['paper_execution_contract_aligned_summary_aligned']}`",
        (
            "- Paper execution contract checked aligned entry aligned: "
            f"`{summary['paper_execution_contract_checked_aligned_entry_aligned']}`"
        ),
        (
            "- Paper execution contract aligned aligned entry aligned: "
            f"`{summary['paper_execution_contract_aligned_aligned_entry_aligned']}`"
        ),
        (
            "- Paper execution contract checked summary aligned entry aligned: "
            f"`{summary['paper_execution_contract_checked_summary_aligned_entry_aligned']}`"
        ),
        (
            "- Paper execution contract aligned summary aligned entry aligned: "
            f"`{summary['paper_execution_contract_aligned_summary_aligned_entry_aligned']}`"
        ),
        (
            "- Paper execution contract checked aligned summary aligned: "
            f"`{summary['paper_execution_contract_checked_aligned_summary_aligned']}`"
        ),
        (
            "- Paper execution contract aligned aligned summary aligned: "
            f"`{summary['paper_execution_contract_aligned_aligned_summary_aligned']}`"
        ),
        (
            "- Paper execution contract checked summary aligned summary aligned: "
            f"`{summary['paper_execution_contract_checked_summary_aligned_summary_aligned']}`"
        ),
        (
            "- Paper execution contract aligned summary aligned summary aligned: "
            f"`{summary['paper_execution_contract_aligned_summary_aligned_summary_aligned']}`"
        ),
        f"- Paper ledger snapshot aligned: `{summary['paper_ledger_snapshot_aligned']}`",
        f"- Paper ledger snapshot summary aligned: `{summary['paper_ledger_snapshot_summary_aligned']}`",
        f"- Execution contract aligned: `{verdict['execution_contract_aligned']}`",
        f"- Execution health: `{summary['execution_health_line']}`",
        f"- Paper nightly: `{summary['paper_nightly_health_line']}`",
        f"- Paper execution read: `{summary['paper_execution_read']}`",
        f"- Contract health aligned: `{summary['contract_health_aligned_read']}`",
        (
            "- Quick-read contract health aligned truth: "
            f"`{summary['quick_read_contract_health_aligned']}`"
        ),
        f"- Paper execution contract checked: `{summary['paper_execution_contract_checked']}`",
        f"- Paper execution contract aligned: `{summary['paper_execution_contract_aligned']}`",
        f"- Paper ledger snapshot: `{summary['paper_ledger_snapshot_read']}`",
        f"- Paper nightly summary execution contract checked: `{paper['paper_execution_contract_checked']}`",
        f"- Paper nightly summary execution contract aligned: `{paper['paper_execution_contract_aligned']}`",
        (
            "- Paper nightly summary execution contract checked aligned: "
            f"`{paper.get('paper_execution_contract_checked_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract aligned aligned: "
            f"`{paper.get('paper_execution_contract_aligned_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract checked summary aligned: "
            f"`{paper.get('paper_execution_contract_checked_summary_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract aligned summary aligned: "
            f"`{paper.get('paper_execution_contract_aligned_summary_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract checked aligned entry aligned: "
            f"`{paper.get('paper_execution_contract_checked_aligned_entry_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract aligned aligned entry aligned: "
            f"`{paper.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract checked summary aligned entry aligned: "
            f"`{paper.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract aligned summary aligned entry aligned: "
            f"`{paper.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract checked aligned summary aligned: "
            f"`{paper.get('paper_execution_contract_checked_aligned_summary_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract aligned aligned summary aligned: "
            f"`{paper.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract checked summary aligned summary aligned: "
            f"`{paper.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
        ),
        (
            "- Paper nightly summary execution contract aligned summary aligned summary aligned: "
            f"`{paper.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
        ),
        f"- Paper nightly summary snapshot: `{paper['paper_ledger_snapshot_read']}`",
        f"- Paper summary json: `{summary['paper_summary_paths']['paper_nightly_summary']}`",
        f"- Paper summary md: `{summary['paper_summary_paths']['paper_nightly_summary_md']}`",
        "- Execution-meta reason field-set lock: `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`",
        "- Execution-meta reason final-sentence lock: `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Paper Nightly Summary",
        f"- source: `{paper['source']}`",
        f"- intent_count: `{paper['intent_count']}`",
        f"- signed_request_count: `{paper['signed_request_count']}`",
        f"- paper_applied_count: `{paper['paper_applied_count']}`",
        f"- paper_duplicate_count: `{paper['paper_duplicate_count']}`",
        f"- paper_closed_count: `{paper['paper_closed_count']}`",
        f"- paper_open_count: `{paper['paper_open_count']}`",
        f"- paper_execution_contract_checked: `{paper['paper_execution_contract_checked']}`",
        f"- paper_execution_contract_aligned: `{paper['paper_execution_contract_aligned']}`",
        f"- paper_execution_contract_checked_aligned: `{paper.get('paper_execution_contract_checked_aligned', False)}`",
        f"- paper_execution_contract_aligned_aligned: `{paper.get('paper_execution_contract_aligned_aligned', False)}`",
        (
            f"- paper_execution_contract_checked_summary_aligned: "
            f"`{paper.get('paper_execution_contract_checked_summary_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_aligned_summary_aligned: "
            f"`{paper.get('paper_execution_contract_aligned_summary_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_checked_aligned_entry_aligned: "
            f"`{paper.get('paper_execution_contract_checked_aligned_entry_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_aligned_aligned_entry_aligned: "
            f"`{paper.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_checked_summary_aligned_entry_aligned: "
            f"`{paper.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_aligned_summary_aligned_entry_aligned: "
            f"`{paper.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_checked_aligned_summary_aligned: "
            f"`{paper.get('paper_execution_contract_checked_aligned_summary_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_aligned_aligned_summary_aligned: "
            f"`{paper.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_checked_summary_aligned_summary_aligned: "
            f"`{paper.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
        ),
        (
            f"- paper_execution_contract_aligned_summary_aligned_summary_aligned: "
            f"`{paper.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
        ),
        f"- paper_ledger_snapshot: `{paper['paper_ledger_snapshot_read']}`",
        "",
    ]
    for entry in report["entries"]:
        lines.extend(
            [
                f"## {entry['label']}",
                f"- source: `{entry['source']}`",
                f"- regression_lock_test: `{entry['regression_lock_test']}`",
                f"- standard_check_order_reference: `{' > '.join(entry['standard_check_order_reference'])}`",
                f"- execution_health_line: `{entry['execution_health_line']}`",
                f"- paper_nightly_health_line: `{entry['paper_nightly_health_line']}`",
                f"- paper_execution_read: `{entry['paper_execution_read']}`",
                f"- contract_health_aligned: `{entry.get('contract_health_aligned', False)}`",
                f"- paper_execution_contract_checked: `{entry['paper_execution_contract_checked']}`",
                f"- paper_execution_contract_aligned: `{entry['paper_execution_contract_aligned']}`",
                (
                    f"- paper_execution_contract_checked_aligned: "
                    f"`{entry['paper_execution_contract_checked_aligned']}`"
                ),
                (
                    f"- paper_execution_contract_aligned_aligned: "
                    f"`{entry['paper_execution_contract_aligned_aligned']}`"
                ),
                (
                    f"- paper_execution_contract_checked_summary_aligned: "
                    f"`{entry['paper_execution_contract_checked_summary_aligned']}`"
                ),
                (
                    f"- paper_execution_contract_aligned_summary_aligned: "
                    f"`{entry['paper_execution_contract_aligned_summary_aligned']}`"
                ),
                (
                    f"- paper_execution_contract_checked_aligned_entry_aligned: "
                    f"`{entry.get('paper_execution_contract_checked_aligned_entry_aligned', False)}`"
                ),
                (
                    f"- paper_execution_contract_aligned_aligned_entry_aligned: "
                    f"`{entry.get('paper_execution_contract_aligned_aligned_entry_aligned', False)}`"
                ),
                (
                    f"- paper_execution_contract_checked_summary_aligned_entry_aligned: "
                    f"`{entry.get('paper_execution_contract_checked_summary_aligned_entry_aligned', False)}`"
                ),
                (
                    f"- paper_execution_contract_aligned_summary_aligned_entry_aligned: "
                    f"`{entry.get('paper_execution_contract_aligned_summary_aligned_entry_aligned', False)}`"
                ),
                (
                    f"- paper_execution_contract_checked_aligned_summary_aligned: "
                    f"`{entry.get('paper_execution_contract_checked_aligned_summary_aligned', False)}`"
                ),
                (
                    f"- paper_execution_contract_aligned_aligned_summary_aligned: "
                    f"`{entry.get('paper_execution_contract_aligned_aligned_summary_aligned', False)}`"
                ),
                (
                    f"- paper_execution_contract_checked_summary_aligned_summary_aligned: "
                    f"`{entry.get('paper_execution_contract_checked_summary_aligned_summary_aligned', False)}`"
                ),
                (
                    f"- paper_execution_contract_aligned_summary_aligned_summary_aligned: "
                    f"`{entry.get('paper_execution_contract_aligned_summary_aligned_summary_aligned', False)}`"
                ),
                f"- paper_ledger_snapshot_read: `{entry['paper_ledger_snapshot_read']}`",
                "",
            ]
        )
    return "\n".join(lines)


def _write_latest_aliases(json_path: Path, md_path: Path) -> dict:
    latest_json = json_path.with_name("btc_1d_execution_contract_screen_latest.json")
    latest_md = md_path.with_name("btc_1d_execution_contract_screen_md_latest.md")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "btc_1d_execution_contract_screen": str(latest_json),
        "btc_1d_execution_contract_screen_md": str(latest_md),
    }


def main() -> int:
    report = build_report(ANALYSIS_DIR)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_execution_contract_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_execution_contract_screen_{stamp}.md"
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
