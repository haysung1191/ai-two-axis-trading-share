from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
PROBE_CONTRACT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_probe_contract" / "probe_contract_summary.json"
)
REFRESH_CONTRACT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_refresh_contract" / "refresh_contract_summary.json"
)
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_entrypoint_contract"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Entrypoint Contract",
        "",
        "## Use This When",
        "",
        f"- human interactive entrypoint: `{summary['primary_human_command']}`",
        f"- machine gate entrypoint: `{summary['gate_probe_command']}`",
        f"- cheap full-refresh entrypoint: `{summary['refresh_command']}`",
        f"- refresh plus validation entrypoint: `{summary['sync_command']}`",
        f"- terminal summary entrypoint: `{summary['doctor_command']}`",
        "",
        "## Canonical Files",
        "",
        f"- primary read file: `{summary['primary_read_file']}`",
        f"- representative decision file: `{summary['representative_decision_file']}`",
        f"- probe contract file: `{summary['probe_contract_file']}`",
        f"- refresh contract file: `{summary['refresh_contract_file']}`",
        "",
        "## Contract Rule",
        "",
        f"- verdict: `{summary['verdict']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    current_state = _load_json(CURRENT_STATE_JSON)
    probe_contract = _load_json(PROBE_CONTRACT_JSON)
    refresh_contract = _load_json(REFRESH_CONTRACT_JSON)

    summary = {
        "entrypoint_contract_version": 1,
        "primary_human_command": str(current_state["primary_human_command"]),
        "gate_probe_command": str(current_state["gate_probe_command"]),
        "refresh_command": str(current_state["refresh_command"]),
        "sync_command": str(current_state["sync_command"]),
        "doctor_command": str(current_state["doctor_command"]),
        "primary_read_file": str(current_state["primary_read_file"]),
        "representative_decision_file": str(current_state["representative_decision_file"]),
        "probe_contract_file": str(current_state["probe_contract_file"]),
        "refresh_contract_file": str(current_state["refresh_contract_file"]),
        "verdict": (
            f"use `{current_state['primary_human_command']}` for the normal human entrypoint, "
            f"`{current_state['gate_probe_command']}` for machine gate checks, "
            f"`{current_state['refresh_command']}` when you only need the canonical chain refreshed, "
            f"`{current_state['sync_command']}` when you need refresh plus consistency verification, "
            f"and `{current_state['doctor_command']}` when you want sync plus a terminal-readable summary. "
            f"The machine-facing semantics are defined by `{current_state['probe_contract_file']}`, "
            f"and the refresh/sync/doctor role split is defined by `{current_state['refresh_contract_file']}`."
        ),
        "probe_contract_verdict": str(probe_contract["verdict"]),
        "refresh_contract_verdict": str(refresh_contract["verdict"]),
    }

    (OUTPUT_DIR / "entrypoint_contract_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "entrypoint_contract.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
