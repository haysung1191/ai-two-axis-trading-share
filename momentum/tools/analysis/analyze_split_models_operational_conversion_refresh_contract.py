from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_refresh_contract"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Refresh Contract",
        "",
        "## Entrypoint Roles",
        "",
        f"- refresh command: `{summary['refresh_command']}`",
        f"- sync command: `{summary['sync_command']}`",
        f"- doctor command: `{summary['doctor_command']}`",
        "",
        "## Refresh Scope",
        "",
    ]
    for item in summary["refresh_outputs"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Contract Rule",
            "",
            f"- verdict: `{summary['verdict']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    current_state = _load_json(CURRENT_STATE_JSON)
    refresh_outputs = [
        "candidate ladder",
        "OOS registration",
        "OOS validation",
        "no-submit shadow dry-run",
        "OOS robustness gate",
        "promotion recommendation",
        "follow-up contract",
        "representative challenger closure",
        "representative decision",
        "probe contract",
        "refresh contract",
        "entrypoint contract",
        "verdict",
        "promotion gate",
        "status snapshot",
        "current state",
        "manifest",
        "handoff",
        "closure",
        "dashboard",
    ]
    summary = {
        "refresh_contract_version": 1,
        "refresh_command": str(current_state["refresh_command"]),
        "sync_command": str(current_state["sync_command"]),
        "doctor_command": str(current_state["doctor_command"]),
        "refresh_outputs": refresh_outputs,
        "verdict": (
            "treat refresh as the cheap full-refresh entrypoint for the entire canonical chain. "
            "Treat sync as refresh plus consistency check. Treat doctor as sync plus terminal summary."
        ),
    }

    (OUTPUT_DIR / "refresh_contract_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "refresh_contract.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
