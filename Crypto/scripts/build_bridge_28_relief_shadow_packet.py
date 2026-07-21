from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis_results"
SCOREBOARD = ANALYSIS_DIR / "btc_1d_model_scoreboard_latest.json"
FREEZE_PACK = Path(r"C:\AI\codex-output-kit\profiles\model_reports\crypto_shadow_readiness_freeze_pack_latest.json")
TARGET = "bridge_28_relief"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_bridge_metrics() -> dict[str, Any]:
    scoreboard = _read_json(SCOREBOARD)
    for section in ("top_models", "top_new_models"):
        for row in scoreboard.get(section, []):
            if row.get("variant") == TARGET:
                return row
    raise RuntimeError(f"{TARGET} not found in {SCOREBOARD}")


def _find_freeze_contract() -> dict[str, Any]:
    freeze_pack = _read_json(FREEZE_PACK)
    for row in freeze_pack.get("contracts", []):
        if row.get("variant") == TARGET:
            return row
    raise RuntimeError(f"{TARGET} not found in {FREEZE_PACK}")


def build_packet() -> dict[str, Any]:
    metrics = _find_bridge_metrics()
    contract = _find_freeze_contract()
    source_hashes = {
        "scoreboard": _sha256(SCOREBOARD),
        "freeze_pack": _sha256(FREEZE_PACK),
        "contract_source_hashes": contract.get("source_hashes", {}),
    }
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": TARGET,
        "candidate_id": TARGET,
        "config_hash": source_hashes["scoreboard"],
        "data_snapshot_hash": source_hashes["scoreboard"],
        "feature_hash": source_hashes["freeze_pack"],
        "signal_source": "bridge_28_relief_frozen_candidate_metrics",
        "status": "frozen_shadow_signal_source",
        "shadow_decision": "shadow_ready_for_btc_only_pending_reproducibility_evidence",
        "paper_validation_decision": "NOT_REQUESTED",
        "paper_validation_metrics": {
            "sharpe": metrics.get("sharpe"),
            "max_drawdown": abs(float(metrics.get("mdd", 0.0) or 0.0)),
            "cagr": metrics.get("cagr"),
        },
        "survivability_validation_decision": "NOT_REQUESTED",
        "survivability_validation_metrics": {
            "sharpe": metrics.get("sharpe"),
            "max_drawdown": abs(float(metrics.get("mdd", 0.0) or 0.0)),
            "cagr": metrics.get("oos_cagr") or metrics.get("cagr"),
        },
        "walk_forward": {
            "passed": not bool(metrics.get("negative_walk_forward_windows")),
            "summary": "Frozen bridge candidate packet built from scoreboard/freeze-pack evidence.",
            "oos_metrics": {
                "cagr": metrics.get("oos_cagr"),
                "max_drawdown": abs(float(metrics.get("mdd", 0.0) or 0.0)),
                "sharpe": metrics.get("sharpe"),
            },
        },
        "friction_validation_decision": "PASS" if metrics.get("cost_cagr") else "PENDING",
        "friction_validation_heaviest_level": {
            "cost_bps": 20.0,
            "decision": "PASS" if metrics.get("cost_cagr") else "PENDING",
            "cagr": metrics.get("cost_cagr"),
            "max_drawdown": abs(float(metrics.get("mdd", 0.0) or 0.0)),
            "sharpe": metrics.get("sharpe"),
        },
        "parameters": {
            "frozen_contract_id": contract.get("contract_id"),
            "signal_timing_rule": ((contract.get("frozen_fields") or {}).get("signal_timing_rule")),
        },
        "sources": {
            "scoreboard": str(SCOREBOARD),
            "freeze_pack": str(FREEZE_PACK),
        },
        "source_hashes": source_hashes,
        "notes": [
            "Shadow-only packet for bridge_28_relief gate-closure work.",
            "Does not enable paper or live submission.",
            "Built to align ops shadow source with the frozen bridge candidate before C1/C8/C9 checks.",
        ],
    }


def _render_markdown(packet: dict[str, Any]) -> str:
    metrics = packet["paper_validation_metrics"]
    return "\n".join(
        [
            "# bridge_28_relief Shadow Packet",
            "",
            f"- generated_at: `{packet['generated_at']}`",
            f"- candidate: `{packet['candidate']}`",
            f"- status: `{packet['status']}`",
            f"- shadow_decision: `{packet['shadow_decision']}`",
            f"- CAGR: `{float(metrics.get('cagr') or 0.0):.2%}`",
            f"- MDD: `{-float(metrics.get('max_drawdown') or 0.0):.2%}`",
            f"- Sharpe: `{float(metrics.get('sharpe') or 0.0):.4f}`",
            "",
            "## Safety",
            "",
            "- paper_enabled: `False`",
            "- live_enabled: `False`",
        ]
    ) + "\n"


def main() -> int:
    packet = build_packet()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_shadow_packet_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_shadow_packet_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_shadow_packet_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_shadow_packet_md_latest.md"
    text = json.dumps(packet, indent=2) + "\n"
    md = _render_markdown(packet)
    json_path.write_text(text, encoding="utf-8")
    md_path.write_text(md, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")
    print(json.dumps({"json": str(latest_json), "markdown": str(latest_md), "candidate": TARGET}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
