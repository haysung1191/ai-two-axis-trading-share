from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.operations import build_split_models_archive_compare as archive_compare
from tools.operations import build_split_models_archive_replay_packet as archive_replay_packet


ROOT = REPO_ROOT
ARCHIVE_DIR = ROOT / "output" / "split_models_shadow_archive"


def build_compare_packet(base_run_id: str, target_run_id: str) -> str:
    payload = archive_compare.build_archive_compare_payload(base_run_id, target_run_id)
    _, base_packet = archive_replay_packet.build_replay_packet(base_run_id)
    _, target_packet = archive_replay_packet.build_replay_packet(target_run_id)

    lines: list[str] = []
    lines.append("# Split Models Archive Compare Packet")
    lines.append("")
    lines.append(f"- base run id: `{payload['base_run_id']}`")
    lines.append(f"- target run id: `{payload['target_run_id']}`")
    lines.append(f"- baseline variant changed: `{payload['baseline_variant_changed']}`")
    lines.append(f"- live readiness changed: `{payload['live_readiness_changed']}`")
    lines.append(f"- health changed: `{payload['health_changed']}`")
    lines.append(f"- drift changed: `{payload['drift_changed']}`")
    lines.append(f"- operator gate changed: `{payload['operator_gate_changed']}`")
    lines.append(f"- archive consistency changed: `{payload['archive_consistency_changed']}`")
    lines.append(f"- archive stability changed: `{payload['archive_stability_changed']}`")
    lines.append(f"- archive timeline changed: `{payload['archive_timeline_changed']}`")
    lines.append(f"- holdings change: `{payload['holdings_change']}`")
    lines.append(f"- dominant sector changed: `{payload['dominant_sector_changed']}`")
    lines.append(f"- transition turnover change: `{float(payload['transition_turnover_change']):.6f}`")
    lines.append(f"- actionable rows change: `{payload['actionable_rows_change']}`")
    lines.append("")
    lines.append("## Base Replay Packet")
    lines.append(base_packet.rstrip())
    lines.append("")
    lines.append("## Target Replay Packet")
    lines.append(target_packet.rstrip())
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-run-id", required=True)
    parser.add_argument("--target-run-id", required=True)
    args = parser.parse_args(argv)

    packet = build_compare_packet(args.base_run_id, args.target_run_id)
    output_path = (
        ARCHIVE_DIR
        / f"compare_{args.base_run_id}_vs_{args.target_run_id}.md"
    )
    output_path.write_text(packet, encoding="utf-8")
    print(f"compare_packet_path={output_path}")


if __name__ == "__main__":
    main()
