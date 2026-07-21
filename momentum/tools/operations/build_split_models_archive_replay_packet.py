from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.operations import build_split_models_archive_status as archive_status


ROOT = REPO_ROOT
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"


def build_replay_packet(run_id: str | None = None) -> tuple[str, str]:
    payload = archive_status.build_archive_status_payload(run_id=run_id)
    resolved_run_id = str(payload["archive_run_id"])
    packet_path = ARCHIVE_DIR / resolved_run_id / "shadow_live_transition_packet.md"
    archived_packet = packet_path.read_text(encoding="utf-8") if packet_path.exists() else ""

    lines: list[str] = []
    lines.append("# Split Models Archive Replay Packet")
    lines.append("")
    lines.append(f"- archive run id: `{payload['archive_run_id']}`")
    lines.append(f"- baseline variant: `{payload['baseline_variant']}`")
    lines.append(f"- live readiness: `{payload['live_readiness']}`")
    lines.append(f"- health verdict: `{payload['health_verdict']}`")
    lines.append(f"- drift verdict: `{payload['drift_verdict']}`")
    lines.append(f"- operator gate verdict: `{payload['operator_gate_verdict']}`")
    lines.append(f"- archive consistency verdict: `{payload['archive_consistency_verdict']}`")
    lines.append(f"- archive stability verdict: `{payload['archive_stability_verdict']}`")
    lines.append(f"- archive timeline verdict: `{payload['archive_timeline_verdict']}`")
    lines.append(f"- current holdings: `{payload['current_holdings']}`")
    lines.append(f"- dominant sector: `{payload['dominant_sector']}`")
    lines.append(f"- transition turnover: `{float(payload['transition_turnover'] or 0.0):.2%}`")
    lines.append("")
    lines.append("## Replay Context")
    lines.append(f"- in latest timeline window: `{payload['archive_run_in_timeline']}`")
    if payload.get("archive_run_timeline_rank") is not None:
        lines.append(f"- timeline rank: `{payload['archive_run_timeline_rank']}` of `{payload.get('archive_timeline_window')}`")
    if payload.get("archive_prior_run_id") is not None:
        lines.append(f"- prior run id: `{payload['archive_prior_run_id']}`")
        lines.append(f"- holdings change vs prior: `{payload['holdings_change_vs_prior']}`")
        lines.append(f"- dominant sector changed vs prior: `{payload['dominant_sector_changed_vs_prior']}`")
        lines.append(f"- readiness changed vs prior: `{payload['live_readiness_changed_vs_prior']}`")
        lines.append(f"- operator gate changed vs prior: `{payload['operator_gate_changed_vs_prior']}`")
    if payload.get("archive_next_run_id") is not None:
        lines.append(f"- next run id: `{payload['archive_next_run_id']}`")
    if payload.get("operator_gate_failures"):
        lines.append(f"- operator gate failures: `{'; '.join(str(item) for item in payload['operator_gate_failures'])}`")
    lines.append("")
    lines.append("## Archived Operator Packet")
    if archived_packet:
        lines.append(archived_packet.rstrip())
    else:
        lines.append("_No archived operator packet found for this run._")

    return resolved_run_id, "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)

    resolved_run_id, packet = build_replay_packet(run_id=args.run_id)
    output_path = ARCHIVE_DIR / resolved_run_id / "shadow_archive_replay_packet.md"
    output_path.write_text(packet, encoding="utf-8")
    print(f"archive_run_id={resolved_run_id}")
    print(f"replay_packet_path={output_path}")


if __name__ == "__main__":
    main()
