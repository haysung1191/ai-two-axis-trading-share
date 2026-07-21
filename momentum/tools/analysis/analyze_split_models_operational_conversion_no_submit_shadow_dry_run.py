from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_no_submit_shadow_dry_run"
SHADOW_SUMMARY_JSON = ROOT / "output" / "split_models_shadow" / "shadow_live_execution_summary.json"
SHADOW_INITIAL_ADAPTIVE_JSON = ROOT / "output" / "split_models_shadow" / "shadow_live_initial_adaptive_latest.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _build_markdown(summary: dict[str, object]) -> str:
    checks = "\n".join(
        f"- `{row['id']}`: {'PASS' if row['passed'] else 'BLOCK'}; {', '.join(row['missing_or_blocked']) or 'ok'}"
        for row in summary["checklist"]
    )
    return f"""# Split Models Operational Conversion No-Submit Shadow Dry Run

Generated: `{summary['generated_at']}`

## Status

- Decision: `{summary['decision']}`
- Evidence: `{summary['evidence']}`

## Checklist

{checks}
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shadow_summary = _load_json(SHADOW_SUMMARY_JSON)
    adaptive = _load_json(SHADOW_INITIAL_ADAPTIVE_JSON)
    submit_mode = shadow_summary.get("submit_mode")
    submit_live_requested = adaptive.get("submit_live_requested")
    checklist = [
        {
            "id": "shadow_summary_exists",
            "passed": bool(shadow_summary),
            "evidence": str(SHADOW_SUMMARY_JSON),
            "missing_or_blocked": [] if shadow_summary else ["shadow_live_execution_summary_missing"],
        },
        {
            "id": "submit_mode_is_dry_run",
            "passed": submit_mode == "dry_run",
            "evidence": str(SHADOW_SUMMARY_JSON),
            "missing_or_blocked": [] if submit_mode == "dry_run" else [f"submit_mode={submit_mode}"],
        },
        {
            "id": "submit_live_not_requested",
            "passed": submit_live_requested is False,
            "evidence": str(SHADOW_INITIAL_ADAPTIVE_JSON),
            "missing_or_blocked": []
            if submit_live_requested is False
            else [f"submit_live_requested={submit_live_requested}"],
        },
    ]
    blockers = [
        blocker
        for row in checklist
        if not row["passed"]
        for blocker in row["missing_or_blocked"]
    ]
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "PASS_NO_SUBMIT_SHADOW_DRY_RUN" if not blockers else "BLOCK_NO_SUBMIT_SHADOW_DRY_RUN",
        "evidence": str(SHADOW_SUMMARY_JSON),
        "checklist": checklist,
        "remaining_blockers": blockers,
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "no_submit_shadow_dry_run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "no_submit_shadow_dry_run.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
