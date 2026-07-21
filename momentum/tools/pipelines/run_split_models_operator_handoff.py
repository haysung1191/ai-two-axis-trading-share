from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.operations import build_split_models_shadow_status as shadow_status


ROOT = REPO_ROOT
RUNTIME_STATUS_PATH = ROOT / "output" / "split_models_shadow" / "shadow_operator_runtime_status.json"
LIVE_PACKET_PATH = ROOT / "output" / "split_models_shadow" / "shadow_live_transition_packet.md"
ARCHIVE_CONSISTENCY_PATH = ROOT / "output" / "split_models_shadow_archive" / "archive_consistency_report.json"
ARCHIVE_STABILITY_PATH = ROOT / "output" / "split_models_shadow_archive" / "archive_stability_report.json"
ARCHIVE_TIMELINE_PATH = ROOT / "output" / "split_models_shadow_archive" / "archive_timeline_report.json"
ARCHIVE_REPLAY_PACKET_NAME = "shadow_archive_replay_packet.md"


def _run_step(label: str, args: list[str]) -> None:
    print(f"[start] {label}")
    subprocess.run(args, cwd=ROOT, check=True)
    print(f"[done] {label}")


def _write_runtime_status(print_json: bool = False) -> None:
    payload = shadow_status.build_status_payload()
    RUNTIME_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[summary] runtime_status_path={RUNTIME_STATUS_PATH}")
    if print_json:
        print(json.dumps(payload, indent=2))


def _sync_files_to_latest_archive(paths: list[Path]) -> None:
    delta_path = ROOT / "output" / "split_models_shadow_archive" / "archive_latest_delta.json"
    if not delta_path.exists():
        return
    delta = json.loads(delta_path.read_text(encoding="utf-8"))
    latest_run_id = delta.get("latest_run_id")
    if not latest_run_id:
        return
    latest_dir = delta_path.parent / str(latest_run_id)
    latest_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, latest_dir / path.name)


def _load_runtime_status() -> dict[str, object]:
    return json.loads(RUNTIME_STATUS_PATH.read_text(encoding="utf-8"))


def _enforce_operational_gate() -> None:
    payload = _load_runtime_status()
    failures = list(payload.get("operator_gate_failures", []))
    if payload.get("archive_stability_verdict") != "PASS":
        failures.append(f"archive_stability_verdict={payload.get('archive_stability_verdict')}")
    if failures:
        joined = ", ".join(failures)
        raise SystemExit(f"operator_gate_failed: {joined}")
    print(f"[summary] operator_gate={payload.get('operator_gate_verdict', 'PASS')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--total-capital", type=float, default=None)
    parser.add_argument("--refresh-shadow", action="store_true")
    parser.add_argument("--refresh-reference", action="store_true")
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-not-go", action="store_true")
    args = parser.parse_args()

    python = sys.executable

    if args.status_only:
        print("[start] show shadow status")
        _write_runtime_status(print_json=args.json)
        if args.fail_on_not_go:
            _enforce_operational_gate()
        print("[done] show shadow status")
        return

    if args.refresh_shadow:
        _run_step("build shadow report", [python, "tools/operations/build_split_models_shadow_report.py"])

    _run_step(
        "build canonical transition",
        [python, "tools/analysis/analyze_split_models_live_transition.py", "--canonical-shadow"],
    )

    rebalance_args = [python, "tools/operations/build_split_models_rebalance_orders.py"]
    if args.total_capital is not None:
        rebalance_args.extend(["--total-capital", str(args.total_capital)])
    _run_step("build rebalance orders", rebalance_args)

    if args.refresh_reference:
        _run_step(
            "refresh shadow drift reference",
            [python, "tools/operations/check_split_models_shadow_drift.py", "--refresh-reference"],
        )
    else:
        _run_step("check shadow drift", [python, "tools/operations/check_split_models_shadow_drift.py"])

    _run_step("build live readiness", [python, "tools/operations/build_split_models_live_readiness.py"])
    _run_step("build live packet", [python, "tools/operations/build_split_models_live_packet.py"])
    _write_runtime_status(print_json=False)
    _run_step("archive operator handoff", [python, "tools/operations/archive_split_models_operator_handoff.py"])
    _run_step("build archive delta", [python, "tools/operations/build_split_models_archive_delta.py"])
    _write_runtime_status(print_json=False)
    _sync_files_to_latest_archive([RUNTIME_STATUS_PATH])
    _run_step("refresh archive delta", [python, "tools/operations/build_split_models_archive_delta.py"])
    _run_step("check archive consistency", [python, "tools/operations/check_split_models_archive_consistency.py"])
    _run_step("build archive stability", [python, "tools/operations/build_split_models_archive_stability.py"])
    _run_step("build archive timeline", [python, "tools/operations/build_split_models_archive_timeline.py"])
    _run_step("build latest archive replay packet", [python, "tools/operations/build_split_models_archive_replay_packet.py"])
    _write_runtime_status(print_json=False)
    _run_step("refresh live packet after consistency", [python, "tools/operations/build_split_models_live_packet.py"])
    _sync_files_to_latest_archive(
        [
            RUNTIME_STATUS_PATH,
            LIVE_PACKET_PATH,
            ARCHIVE_CONSISTENCY_PATH,
            ARCHIVE_STABILITY_PATH,
            ARCHIVE_TIMELINE_PATH,
        ]
    )
    _run_step("refresh archive delta after consistency", [python, "tools/operations/build_split_models_archive_delta.py"])
    if args.fail_on_not_go:
        _enforce_operational_gate()

    print("[summary] operator handoff artifacts refreshed")
    print(f"[summary] output_dir={ROOT / 'output' / 'split_models_shadow'}")


if __name__ == "__main__":
    main()
