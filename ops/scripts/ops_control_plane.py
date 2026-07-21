from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\AI\ops")
CONTRACTS_CRYPTO = ROOT / "contracts" / "crypto"
REGISTRY_DB = ROOT / "registry" / "ops_registry.sqlite"
RUNSTATE = ROOT / "runstate"
KILL_SWITCH = RUNSTATE / "kill_switch.json"
GLOBAL_DISABLE_FILE = RUNSTATE / "DISABLE_ALL_TRADING"
SHADOW_SIGNALS = ROOT / "signals" / "shadow"
ORDER_INTENTS = ROOT / "orders" / "intents"
PAPER_SIM = ROOT / "paper_sim"
REPORTS = ROOT / "reports"

FREEZE_PACK = Path(
    r"C:\AI\codex-output-kit\profiles\model_reports\crypto_shadow_readiness_freeze_pack_latest.json"
)
STAGE_QUEUE = Path(
    r"C:\AI\codex-output-kit\profiles\model_reports\stage_gated_experiment_queue_latest.json"
)
BTC_SHADOW_PACKET = Path(r"C:\AI\Crypto\analysis_results\btc_1d_shadow_packet_latest.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_dirs() -> None:
    for path in [
        CONTRACTS_CRYPTO,
        REGISTRY_DB.parent,
        RUNSTATE,
        SHADOW_SIGNALS,
        ORDER_INTENTS,
        PAPER_SIM,
        REPORTS,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    if not KILL_SWITCH.exists():
        write_json(
            KILL_SWITCH,
            {
                "schema_version": "1.0",
                "shadow_enabled": True,
                "paper_enabled": False,
                "live_enabled": False,
                "kill_switch_mode": "cancel_only",
                "updated_at_utc": utc_now(),
                "note": "Default ops v1: shadow-only. Paper/live remain disabled.",
            },
        )


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(REGISTRY_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS contracts (
                contract_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                contract_path TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contract_state_events (
                event_id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS risk_decisions (
                decision_id TEXT PRIMARY KEY,
                signal_id TEXT NOT NULL,
                contract_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_intents (
                order_intent_id TEXT PRIMARY KEY,
                signal_id TEXT NOT NULL,
                contract_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS execution_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                contract_id TEXT,
                signal_id TEXT,
                order_intent_id TEXT,
                severity TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS paper_sim_fills (
                fill_id TEXT PRIMARY KEY,
                order_intent_id TEXT NOT NULL,
                signal_id TEXT NOT NULL,
                contract_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                target_weight REAL NOT NULL,
                fill_weight REAL NOT NULL,
                fill_status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                created_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS paper_sim_positions (
                contract_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                simulated_weight REAL NOT NULL,
                source_fill_id TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                PRIMARY KEY (contract_id, symbol)
            );
            """
        )


def append_event(
    conn: sqlite3.Connection,
    event_type: str,
    payload: dict[str, Any],
    *,
    contract_id: str | None = None,
    signal_id: str | None = None,
    order_intent_id: str | None = None,
    severity: str = "INFO",
) -> str:
    created = utc_now()
    event_seed = {
        "event_type": event_type,
        "contract_id": contract_id,
        "signal_id": signal_id,
        "order_intent_id": order_intent_id,
        "created_at_utc": created,
        "payload": payload,
    }
    event_id = stable_hash(event_seed)
    payload_hash = stable_hash(payload)
    conn.execute(
        """
        INSERT OR IGNORE INTO execution_events
        (event_id, event_type, contract_id, signal_id, order_intent_id, severity,
         payload_json, payload_hash, created_at_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            event_type,
            contract_id,
            signal_id,
            order_intent_id,
            severity,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            payload_hash,
            created,
        ),
    )
    return event_id


def contract_from_freeze(frozen: dict[str, Any]) -> dict[str, Any]:
    metrics = frozen.get("candidate_metrics", {})
    model_id = frozen.get("variant") or frozen.get("contract_id")
    source_contract_id = frozen["contract_id"]
    contract_id = f"crypto.shadow.{source_contract_id}"
    generated = utc_now()
    payload = {
        "schema_version": "1.0",
        "contract_id": contract_id,
        "source_frozen_contract_id": source_contract_id,
        "model_id": model_id,
        "asset_class": "crypto",
        "symbols": ["BTC-USD"],
        "timeframe": "1d",
        "mode": "shadow",
        "status": "shadow_contract_pending_validation",
        "allowed_modes": ["shadow"],
        "broker_adapter": "shadow_only",
        "allow_live_submit": False,
        "generated_at_utc": generated,
        "expires_at_utc": None,
        "source_repo": r"C:\AI\Crypto",
        "source_freeze_pack": str(FREEZE_PACK),
        "source_hashes": frozen.get("source_hashes", {}),
        "candidate_metrics": metrics,
        "gate_state": {
            "freeze_artifacts_present": frozen.get("gate", {}).get("freeze_artifacts_present") is True,
            "signal_reproducibility": frozen.get("gate", {}).get("signal_reproducibility", "pending"),
            "candle_finalization": frozen.get("gate", {}).get("candle_finalization", "pending"),
            "research_vs_shadow_data_consistency": frozen.get("gate", {}).get(
                "research_vs_shadow_data_consistency", "pending"
            ),
            "cost_slippage_stress": frozen.get("gate", {}).get("cost_slippage_stress", "pending"),
            "delayed_execution_stress": frozen.get("gate", {}).get(
                "delayed_execution_stress", "pending"
            ),
        },
        "sizing_policy": {
            "type": "shadow_target_weight_cap",
            "max_model_weight": 0.20,
            "max_symbol_weight": 0.20,
            "max_order_notional_pct_of_sleeve": 0.05,
            "max_leverage": 1.0,
        },
        "risk_policy": {
            "daily_loss_pause_pct": 0.005,
            "daily_loss_stop_pct": 0.010,
            "max_contract_drawdown_pct": 0.12,
            "max_spread_bps": 20,
            "max_slippage_bps": 25,
            "stale_signal_minutes": 90,
            "require_finalized_daily_bar": True,
        },
        "order_policy": {
            "intent_only": True,
            "submit_to_broker": False,
            "order_style": "shadow_limit_or_market_fallback",
            "time_in_force": "shadow_day",
            "client_order_id_prefix": "SHADOW",
        },
        "deactivation_rules": {
            "signal_mismatch_count": 1,
            "critical_exception_count": 1,
            "unreconciled_position_minutes": 30,
            "duplicate_intent_violation": 1,
        },
        "approval": {
            "approved_by": "system_generated_from_freeze_pack",
            "approved_at_utc": generated,
            "manual_live_approval": False,
        },
    }
    payload["payload_hash"] = stable_hash(payload)
    return payload


def contract_from_btc_shadow_packet(packet: dict[str, Any]) -> dict[str, Any] | None:
    candidate = packet.get("candidate") if isinstance(packet, dict) else None
    if not candidate:
        return None
    generated = utc_now()
    contract_id = f"crypto.shadow.{candidate}_current_signal_source"
    payload = {
        "schema_version": "1.0",
        "contract_id": contract_id,
        "source_frozen_contract_id": candidate,
        "model_id": candidate,
        "asset_class": "crypto",
        "symbols": ["BTC-USD"],
        "timeframe": "1d",
        "mode": "shadow",
        "status": "shadow_contract_signal_source_current",
        "allowed_modes": ["shadow"],
        "broker_adapter": "shadow_only",
        "allow_live_submit": False,
        "generated_at_utc": generated,
        "expires_at_utc": None,
        "source_repo": r"C:\AI\Crypto",
        "source_freeze_pack": str(BTC_SHADOW_PACKET),
        "source_hashes": {
            "btc_shadow_packet_hash": stable_hash(packet),
        },
        "candidate_metrics": {
            "paper_validation_decision": packet.get("paper_validation_decision"),
            "survivability_validation_decision": packet.get("survivability_validation_decision"),
            "shadow_decision": packet.get("shadow_decision"),
            "walk_forward_passed": (packet.get("walk_forward") or {}).get("passed")
            if isinstance(packet.get("walk_forward"), dict)
            else None,
        },
        "gate_state": {
            "signal_source_aligned": True,
            "source": "btc_1d_shadow_packet_latest",
            "freeze_artifacts_present": False,
            "note": "Current signal-source contract. Promote to frozen contract only after matching freeze pack exists.",
        },
        "sizing_policy": {
            "type": "shadow_target_weight_cap",
            "max_model_weight": 0.20,
            "max_symbol_weight": 0.20,
            "max_order_notional_pct_of_sleeve": 0.05,
            "max_leverage": 1.0,
        },
        "risk_policy": {
            "daily_loss_pause_pct": 0.005,
            "daily_loss_stop_pct": 0.010,
            "max_contract_drawdown_pct": 0.12,
            "max_spread_bps": 20,
            "max_slippage_bps": 25,
            "stale_signal_minutes": 90,
            "require_finalized_daily_bar": True,
        },
        "order_policy": {
            "intent_only": True,
            "submit_to_broker": False,
            "order_style": "shadow_limit_or_market_fallback",
            "time_in_force": "shadow_day",
            "client_order_id_prefix": "SHADOW",
        },
        "deactivation_rules": {
            "signal_mismatch_count": 1,
            "critical_exception_count": 1,
            "unreconciled_position_minutes": 30,
            "duplicate_intent_violation": 1,
        },
        "approval": {
            "approved_by": "system_generated_from_current_shadow_packet",
            "approved_at_utc": generated,
            "manual_live_approval": False,
        },
    }
    payload["payload_hash"] = stable_hash(payload)
    return payload


def promote_crypto_shadow() -> dict[str, Any]:
    init_db()
    freeze_pack = read_json(FREEZE_PACK)
    btc_packet = read_json(BTC_SHADOW_PACKET, default={})
    promoted: list[dict[str, Any]] = []
    frozen_contracts = [contract_from_freeze(frozen) for frozen in freeze_pack.get("contracts", [])]
    packet_contract = contract_from_btc_shadow_packet(btc_packet)
    if packet_contract and packet_contract["contract_id"] not in {
        contract.get("contract_id") for contract in frozen_contracts
    }:
        frozen_contracts.append(packet_contract)
    with connect() as conn:
        for contract in frozen_contracts:
            path = CONTRACTS_CRYPTO / f"{contract['contract_id']}.json"
            write_json(path, contract)
            payload_hash = stable_hash(contract)
            now = utc_now()
            conn.execute(
                """
                INSERT INTO contracts
                (contract_id, model_id, asset_class, mode, status, contract_path,
                 payload_hash, created_at_utc, updated_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(contract_id) DO UPDATE SET
                    status=excluded.status,
                    contract_path=excluded.contract_path,
                    payload_hash=excluded.payload_hash,
                    updated_at_utc=excluded.updated_at_utc
                """,
                (
                    contract["contract_id"],
                    contract["model_id"],
                    contract["asset_class"],
                    contract["mode"],
                    contract["status"],
                    str(path),
                    payload_hash,
                    now,
                    now,
                ),
            )
            state_payload = {
                "event_type": "ContractPromotedFromFreezePack",
                "contract_id": contract["contract_id"],
                "source_frozen_contract_id": contract["source_frozen_contract_id"],
                "contract_path": str(path),
                "payload_hash": payload_hash,
                "signal_source_aligned": contract["model_id"] == btc_packet.get("candidate"),
            }
            state_id = stable_hash(state_payload)
            conn.execute(
                """
                INSERT OR IGNORE INTO contract_state_events
                (event_id, contract_id, event_type, payload_json, payload_hash, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    state_id,
                    contract["contract_id"],
                    "ContractPromotedFromFreezePack",
                    json.dumps(state_payload, ensure_ascii=False, sort_keys=True),
                    stable_hash(state_payload),
                    now,
                ),
            )
            append_event(
                conn,
                "ContractPromotedFromFreezePack",
                state_payload,
                contract_id=contract["contract_id"],
            )
            promoted.append({"contract_id": contract["contract_id"], "path": str(path)})
    report = {
        "generated_at_utc": utc_now(),
        "source_freeze_pack": str(FREEZE_PACK),
        "source_signal_packet": str(BTC_SHADOW_PACKET),
        "source_signal_candidate": btc_packet.get("candidate") if isinstance(btc_packet, dict) else None,
        "promoted_count": len(promoted),
        "contracts": promoted,
    }
    write_json(REPORTS / "crypto_shadow_contract_promotion_latest.json", report)
    return report


def kill_state() -> dict[str, Any]:
    state = read_json(KILL_SWITCH, default={})
    state["global_disable_file_present"] = GLOBAL_DISABLE_FILE.exists()
    return state


def active_contracts(*, include_pending_validation: bool = False) -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT contract_id, contract_path FROM contracts
            WHERE mode='shadow' AND status LIKE 'shadow_contract%'
            ORDER BY contract_id
            """
        ).fetchall()
    contracts = []
    for _, path_text in rows:
        path = Path(path_text)
        if path.exists():
            contracts.append(read_json(path))
    current_source = latest_btc_target_snapshot().get("source_candidate")
    aligned = [
        contract
        for contract in contracts
        if current_source
        and contract.get("model_id") == current_source
        and contract.get("status") == "shadow_contract_signal_source_current"
    ]
    if aligned:
        if not include_pending_validation:
            return aligned
        pending_validation = [
            contract
            for contract in contracts
            if contract.get("status") == "shadow_contract_pending_validation"
        ]
        return aligned + pending_validation
    return contracts


def latest_btc_target_snapshot() -> dict[str, Any]:
    packet = read_json(BTC_SHADOW_PACKET, default={})
    walk_forward = packet.get("walk_forward", {}) if isinstance(packet, dict) else {}
    oos_metrics = walk_forward.get("oos_metrics", {}) if isinstance(walk_forward, dict) else {}
    trade_ledger = oos_metrics.get("trade_ledger", []) if isinstance(oos_metrics, dict) else []
    equity_timestamps = oos_metrics.get("equity_timestamps", []) if isinstance(oos_metrics, dict) else []
    asof = equity_timestamps[-1] if equity_timestamps else packet.get("generated_at", utc_now())
    open_trade = None
    if isinstance(trade_ledger, list):
        for trade in reversed(trade_ledger):
            if not isinstance(trade, dict):
                continue
            entry = trade.get("entry_timestamp")
            exit_ts = trade.get("exit_timestamp")
            if entry and (not exit_ts or str(exit_ts) > str(asof)):
                open_trade = trade
                break
    if open_trade:
        action = "SET_TARGET_POSITION"
        side = "long"
        target_weight = 0.20
        reason = "latest_btc_shadow_packet_has_open_long_trade"
    else:
        action = "SET_TARGET_POSITION"
        side = "flat"
        target_weight = 0.0
        reason = "latest_btc_shadow_packet_has_no_open_trade"
    snapshot = {
        "available": bool(packet),
        "source_path": str(BTC_SHADOW_PACKET),
        "packet_generated_at": packet.get("generated_at") if isinstance(packet, dict) else None,
        "source_candidate": packet.get("candidate") if isinstance(packet, dict) else None,
        "shadow_decision": packet.get("shadow_decision") if isinstance(packet, dict) else None,
        "asof_utc": asof,
        "symbol": "BTC-USD",
        "market": "KRW-BTC",
        "timeframe": "1d",
        "action": action,
        "side": side,
        "target_weight": target_weight,
        "target_quantity": None,
        "reason": reason,
        "open_trade": open_trade,
        "latest_trade": trade_ledger[-1] if isinstance(trade_ledger, list) and trade_ledger else None,
        "metrics": {
            "paper_validation_decision": packet.get("paper_validation_decision") if isinstance(packet, dict) else None,
            "survivability_validation_decision": packet.get("survivability_validation_decision") if isinstance(packet, dict) else None,
            "walk_forward_passed": walk_forward.get("passed") if isinstance(walk_forward, dict) else None,
        },
    }
    return snapshot


def build_shadow_signal(contract: dict[str, Any]) -> dict[str, Any]:
    target = latest_btc_target_snapshot()
    asof = target.get("asof_utc") or utc_now()
    signal_core = {
        "contract_id": contract["contract_id"],
        "model_id": contract["model_id"],
        "asof_utc": asof,
        "symbol": target.get("symbol") or contract["symbols"][0],
        "mode": "shadow",
        "action": target.get("action"),
        "target_weight": target.get("target_weight"),
        "side": target.get("side"),
    }
    signal_id = stable_hash(signal_core)
    signal = {
        "schema_version": "1.0",
        "signal_id": signal_id,
        "generated_at_utc": utc_now(),
        "bar_close_ts_utc": asof,
        "contract_id": contract["contract_id"],
        "model_id": contract["model_id"],
        "asset_class": contract["asset_class"],
        "symbol": target.get("symbol") or contract["symbols"][0],
        "market": target.get("market"),
        "timeframe": contract["timeframe"],
        "mode": "shadow",
        "action": target.get("action"),
        "side": target.get("side"),
        "target_weight": target.get("target_weight"),
        "target_quantity": target.get("target_quantity"),
        "reason": target.get("reason"),
        "idempotency_key": signal_id,
        "provenance": {
            "contract_payload_hash": contract.get("payload_hash"),
            "source_freeze_pack": contract.get("source_freeze_pack"),
            "source_signal_artifact": target.get("source_path"),
            "source_candidate": target.get("source_candidate"),
            "source_shadow_decision": target.get("shadow_decision"),
            "source_model_mismatch_warning": (
                target.get("source_candidate") not in {contract.get("model_id"), contract.get("source_frozen_contract_id")}
            ),
            "target_snapshot_hash": stable_hash(target),
        },
    }
    return signal


def risk_decision_for_signal(signal: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    state = kill_state()
    failed: list[str] = []
    if state.get("global_disable_file_present"):
        failed.append("GLOBAL_DISABLE_FILE_PRESENT")
    if not state.get("shadow_enabled", False):
        failed.append("SHADOW_DISABLED")
    if contract.get("mode") != "shadow":
        failed.append("CONTRACT_NOT_SHADOW_MODE")
    if contract.get("allow_live_submit") is not False:
        failed.append("CONTRACT_LIVE_SUBMIT_NOT_FALSE")
    if signal.get("action") != "SET_TARGET_POSITION":
        failed.append("UNSUPPORTED_SIGNAL_ACTION")
    if signal.get("target_weight") is None:
        failed.append("NO_TARGET_POSITION_SIGNAL")
    if (
        contract.get("status") == "shadow_contract_pending_validation"
        and (signal.get("provenance") or {}).get("source_model_mismatch_warning") is True
    ):
        failed.append("SOURCE_MODEL_MISMATCH_PENDING_VALIDATION")
    decision = "rejected_no_order" if failed else "approved_shadow_intent"
    reason = ",".join(failed) if failed else "SHADOW_RISK_PASS"
    payload = {
        "schema_version": "1.0",
        "decision_id": stable_hash(
            {
                "signal_id": signal["signal_id"],
                "contract_id": contract["contract_id"],
                "reason": reason,
            }
        ),
        "created_at_utc": utc_now(),
        "signal_id": signal["signal_id"],
        "contract_id": contract["contract_id"],
        "decision": decision,
        "reason": reason,
        "checks": {
            "global_disable_file_present": state.get("global_disable_file_present"),
            "shadow_enabled": state.get("shadow_enabled"),
            "paper_enabled": state.get("paper_enabled"),
            "live_enabled": state.get("live_enabled"),
            "contract_mode": contract.get("mode"),
            "allow_live_submit": contract.get("allow_live_submit"),
        },
    }
    return payload


def build_order_intent(signal: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    core = {
        "signal_id": signal["signal_id"],
        "contract_id": signal["contract_id"],
        "mode": "shadow",
        "action": signal["action"],
    }
    intent_id = stable_hash(core)
    return {
        "schema_version": "1.0",
        "order_intent_id": intent_id,
        "created_at_utc": utc_now(),
        "signal_id": signal["signal_id"],
        "contract_id": signal["contract_id"],
        "mode": "shadow",
        "status": "shadow_planned_no_submit" if decision["decision"] == "approved_shadow_intent" else "no_order_required",
        "broker_submit_allowed": False,
        "reason": decision["reason"],
        "symbol": signal["symbol"],
        "market": signal.get("market"),
        "side": signal.get("side"),
        "target_weight": signal.get("target_weight"),
        "target_quantity": signal.get("target_quantity"),
        "idempotency_key": intent_id,
    }


def run_shadow(*, include_pending_validation: bool = False) -> dict[str, Any]:
    init_db()
    contracts = active_contracts(include_pending_validation=include_pending_validation)
    outputs: list[dict[str, Any]] = []
    with connect() as conn:
        for contract in contracts:
            signal = build_shadow_signal(contract)
            signal_path = SHADOW_SIGNALS / f"{signal['signal_id']}.json"
            write_json(signal_path, signal)
            signal_hash = stable_hash(signal)
            now = utc_now()
            conn.execute(
                """
                INSERT OR IGNORE INTO signals
                (signal_id, contract_id, mode, payload_json, payload_hash, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    signal["signal_id"],
                    signal["contract_id"],
                    "shadow",
                    json.dumps(signal, ensure_ascii=False, sort_keys=True),
                    signal_hash,
                    now,
                ),
            )
            decision = risk_decision_for_signal(signal, contract)
            decision_hash = stable_hash(decision)
            conn.execute(
                """
                INSERT OR IGNORE INTO risk_decisions
                (decision_id, signal_id, contract_id, decision, reason,
                 payload_json, payload_hash, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision["decision_id"],
                    signal["signal_id"],
                    signal["contract_id"],
                    decision["decision"],
                    decision["reason"],
                    json.dumps(decision, ensure_ascii=False, sort_keys=True),
                    decision_hash,
                    decision["created_at_utc"],
                ),
            )
            intent = build_order_intent(signal, decision)
            intent_path = ORDER_INTENTS / f"{intent['order_intent_id']}.json"
            write_json(intent_path, intent)
            intent_hash = stable_hash(intent)
            conn.execute(
                """
                INSERT OR IGNORE INTO order_intents
                (order_intent_id, signal_id, contract_id, mode, status,
                 payload_json, payload_hash, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intent["order_intent_id"],
                    signal["signal_id"],
                    signal["contract_id"],
                    "shadow",
                    intent["status"],
                    json.dumps(intent, ensure_ascii=False, sort_keys=True),
                    intent_hash,
                    intent["created_at_utc"],
                ),
            )
            append_event(
                conn,
                "ShadowIntentPlanned",
                {"signal": signal, "risk_decision": decision, "order_intent": intent},
                contract_id=signal["contract_id"],
                signal_id=signal["signal_id"],
                order_intent_id=intent["order_intent_id"],
                severity="INFO",
            )
            outputs.append(
                {
                    "contract_id": signal["contract_id"],
                    "signal_id": signal["signal_id"],
                    "risk_decision": decision["decision"],
                    "risk_reason": decision["reason"],
                    "order_intent_id": intent["order_intent_id"],
                    "order_intent_status": intent["status"],
                }
            )
    report = {
        "generated_at_utc": utc_now(),
        "mode": "shadow",
        "contract_count": len(contracts),
        "planned_count": len(outputs),
        "include_pending_validation": include_pending_validation,
        "outputs": outputs,
        "safety": {
            "broker_submit_allowed": False,
            "paper_enabled": kill_state().get("paper_enabled"),
            "live_enabled": kill_state().get("live_enabled"),
        },
    }
    write_json(REPORTS / "shadow_control_plane_latest.json", report)
    return report


def status_report() -> dict[str, Any]:
    init_db()
    with connect() as conn:
        counts = {
            "contracts": conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0],
            "signals": conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0],
            "risk_decisions": conn.execute("SELECT COUNT(*) FROM risk_decisions").fetchone()[0],
            "order_intents": conn.execute("SELECT COUNT(*) FROM order_intents").fetchone()[0],
            "events": conn.execute("SELECT COUNT(*) FROM execution_events").fetchone()[0],
        }
        contract_rows = conn.execute(
            """
            SELECT contract_id, model_id, mode, status, updated_at_utc
            FROM contracts
            ORDER BY updated_at_utc DESC, contract_id
            """
        ).fetchall()
    report = {
        "generated_at_utc": utc_now(),
        "counts": counts,
        "kill_state": kill_state(),
        "contracts": [
            {
                "contract_id": row[0],
                "model_id": row[1],
                "mode": row[2],
                "status": row[3],
                "updated_at_utc": row[4],
            }
            for row in contract_rows
        ],
        "registry_path": str(REGISTRY_DB),
    }
    write_json(REPORTS / "ops_status_latest.json", report)
    write_markdown_status(report)
    return report


def safety_self_test() -> dict[str, Any]:
    init_db()
    had_global_disable = GLOBAL_DISABLE_FILE.exists()
    global_disable_text = GLOBAL_DISABLE_FILE.read_text(encoding="utf-8") if had_global_disable else None
    if GLOBAL_DISABLE_FILE.exists():
        GLOBAL_DISABLE_FILE.unlink()

    first = run_shadow()
    second = run_shadow()
    first_intents = [row.get("order_intent_id") for row in first.get("outputs", [])]
    second_intents = [row.get("order_intent_id") for row in second.get("outputs", [])]
    duplicate_idempotency_passed = bool(first_intents) and first_intents == second_intents

    GLOBAL_DISABLE_FILE.write_text("self-test kill switch\n", encoding="utf-8")
    try:
        blocked = run_shadow()
    finally:
        GLOBAL_DISABLE_FILE.unlink(missing_ok=True)

    blocked_outputs = blocked.get("outputs", [])
    kill_switch_passed = bool(blocked_outputs) and all(
        (
            "GLOBAL_KILL_SWITCH_ACTIVE" in str(row.get("risk_reason") or "")
            or "GLOBAL_DISABLE_FILE_PRESENT" in str(row.get("risk_reason") or "")
        )
        and row.get("order_intent_status") == "no_order_required"
        for row in blocked_outputs
    )

    restored = run_shadow()
    restored_outputs = restored.get("outputs", [])
    restored_passed = bool(restored_outputs) and all(
        (
            row.get("risk_decision") == "approved_shadow_intent"
            and row.get("order_intent_status") == "shadow_planned_no_submit"
        )
        or (
            row.get("risk_decision") == "rejected_no_order"
            and row.get("risk_reason") == "SOURCE_MODEL_MISMATCH_PENDING_VALIDATION"
            and row.get("order_intent_status") == "no_order_required"
        )
        for row in restored_outputs
    )

    report = {
        "generated_at_utc": utc_now(),
        "mode": "shadow_safety_self_test",
        "duplicate_idempotency_passed": duplicate_idempotency_passed,
        "kill_switch_passed": kill_switch_passed,
        "restored_after_kill_switch_passed": restored_passed,
        "paper_enabled": False,
        "live_enabled": False,
        "broker_submit_allowed": False,
        "first_order_intent_ids": first_intents,
        "second_order_intent_ids": second_intents,
        "blocked_outputs": blocked_outputs,
        "restored_outputs": restored_outputs,
    }
    write_json(REPORTS / "ops_safety_self_test_latest.json", report)
    if had_global_disable:
        GLOBAL_DISABLE_FILE.write_text(global_disable_text or "broker/live/private submit disabled by default\n", encoding="utf-8")
    status_report()
    return report


def shadow_health_report() -> dict[str, Any]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT payload_json, created_at_utc
            FROM execution_events
            WHERE event_type='ShadowIntentPlanned'
            ORDER BY created_at_utc DESC
            LIMIT 200
            """
        ).fetchall()

    sessions: list[dict[str, Any]] = []
    for payload_json, created_at in rows:
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            payload = {}
        decision = payload.get("risk_decision") or {}
        intent = payload.get("order_intent") or {}
        signal = payload.get("signal") or {}
        clean = (
            decision.get("decision") == "approved_shadow_intent"
            and decision.get("reason") == "SHADOW_RISK_PASS"
            and intent.get("status") == "shadow_planned_no_submit"
            and intent.get("broker_submit_allowed") is False
            and signal.get("target_weight") is not None
        )
        expected_control_block = (
            decision.get("decision") == "rejected_no_order"
            and (
                "GLOBAL_KILL_SWITCH_ACTIVE" in str(decision.get("reason") or "")
                or "GLOBAL_DISABLE_FILE_PRESENT" in str(decision.get("reason") or "")
            )
            and intent.get("status") == "no_order_required"
            and intent.get("broker_submit_allowed") is False
        )
        expected_validation_block = (
            decision.get("decision") == "rejected_no_order"
            and "SOURCE_MODEL_MISMATCH_PENDING_VALIDATION" in str(decision.get("reason") or "")
            and intent.get("status") == "no_order_required"
            and intent.get("broker_submit_allowed") is False
        )
        sessions.append(
            {
                "created_at_utc": created_at,
                "contract_id": signal.get("contract_id") or intent.get("contract_id"),
                "signal_id": signal.get("signal_id"),
                "order_intent_id": intent.get("order_intent_id"),
                "target_weight": signal.get("target_weight"),
                "risk_decision": decision.get("decision"),
                "risk_reason": decision.get("reason"),
                "order_intent_status": intent.get("status"),
                "broker_submit_allowed": intent.get("broker_submit_allowed"),
                "clean": clean,
                "expected_control_block": expected_control_block,
                "expected_validation_block": expected_validation_block,
            }
        )

    consecutive_clean = 0
    for session in sessions:
        if session["clean"]:
            consecutive_clean += 1
        elif session["expected_control_block"] or session["expected_validation_block"]:
            continue
        else:
            break
    unexpected_failures = [
        session
        for session in sessions
        if not session["clean"]
        and not session["expected_control_block"]
        and not session["expected_validation_block"]
    ][:10]
    expected_control_blocks = [session for session in sessions if session["expected_control_block"]][:10]
    expected_validation_blocks = [
        session for session in sessions if session["expected_validation_block"] and not session["expected_control_block"]
    ][:10]
    latest_actionable = next(
        (
            session
            for session in sessions
            if not session["expected_control_block"] and not session["expected_validation_block"]
        ),
        None,
    )
    latest_actionable_clean = bool(latest_actionable and latest_actionable["clean"])
    report = {
        "generated_at_utc": utc_now(),
        "mode": "shadow_health",
        "health": "green" if latest_actionable_clean else "yellow" if sessions else "red",
        "consecutive_clean_shadow_events": consecutive_clean,
        "recent_event_count": len(sessions),
        "unexpected_failure_count": len(unexpected_failures),
        "recent_failures": unexpected_failures,
        "expected_control_block_count": len(expected_control_blocks),
        "expected_control_blocks": expected_control_blocks,
        "expected_validation_block_count": len(expected_validation_blocks),
        "expected_validation_blocks": expected_validation_blocks,
        "paper_enabled": False,
        "live_enabled": False,
        "broker_submit_allowed": False,
        "paper_eligibility": {
            "required_clean_shadow_events": 21,
            "current_clean_shadow_events": consecutive_clean,
            "eligible": consecutive_clean >= 21 and not unexpected_failures,
        },
    }
    write_json(REPORTS / "shadow_health_latest.json", report)
    return report


def _latest_shadow_payloads() -> list[dict[str, Any]]:
    report = read_json(REPORTS / "shadow_control_plane_latest.json", default={})
    outputs = report.get("outputs", []) if isinstance(report, dict) else []
    payloads: list[dict[str, Any]] = []
    with connect() as conn:
        for output in outputs:
            intent_id = output.get("order_intent_id")
            if not intent_id:
                continue
            row = conn.execute(
                """
                SELECT payload_json
                FROM execution_events
                WHERE event_type='ShadowIntentPlanned' AND order_intent_id=?
                ORDER BY created_at_utc DESC
                LIMIT 1
                """,
                (intent_id,),
            ).fetchone()
            if not row:
                continue
            try:
                payloads.append(json.loads(row[0]))
            except json.JSONDecodeError:
                continue
    return payloads


def paper_sim_harness() -> dict[str, Any]:
    init_db()
    state = kill_state()
    if state.get("paper_enabled") or state.get("live_enabled"):
        report = {
            "generated_at_utc": utc_now(),
            "mode": "paper_sim_harness",
            "status": "blocked",
            "reason": "PAPER_OR_LIVE_ENABLED_UNEXPECTEDLY",
            "paper_enabled": state.get("paper_enabled"),
            "live_enabled": state.get("live_enabled"),
            "real_orders": 0,
            "private_submit_used": False,
        }
        write_json(REPORTS / "paper_sim_harness_latest.json", report)
        return report

    shadow_payloads = _latest_shadow_payloads()
    fills: list[dict[str, Any]] = []
    reconciliations: list[dict[str, Any]] = []
    with connect() as conn:
        for payload in shadow_payloads:
            signal = payload.get("signal") or {}
            decision = payload.get("risk_decision") or {}
            intent = payload.get("order_intent") or {}
            if decision.get("decision") != "approved_shadow_intent":
                continue
            if intent.get("status") != "shadow_planned_no_submit":
                continue
            contract_id = str(signal.get("contract_id") or intent.get("contract_id"))
            signal_id = str(signal.get("signal_id") or intent.get("signal_id"))
            order_intent_id = str(intent.get("order_intent_id"))
            symbol = str(signal.get("symbol") or intent.get("symbol") or "UNKNOWN")
            target_weight = float(signal.get("target_weight") or 0.0)
            fill = {
                "schema_version": "1.0",
                "fill_id": stable_hash(
                    {
                        "mode": "paper_sim",
                        "order_intent_id": order_intent_id,
                        "signal_id": signal_id,
                        "target_weight": target_weight,
                    }
                ),
                "created_at_utc": utc_now(),
                "mode": "paper_sim_harness",
                "contract_id": contract_id,
                "signal_id": signal_id,
                "order_intent_id": order_intent_id,
                "symbol": symbol,
                "target_weight": target_weight,
                "fill_weight": target_weight,
                "fill_status": "simulated_filled_no_submit",
                "fees_bps": 0.0,
                "spread_bps": 0.0,
                "slippage_bps": 0.0,
                "real_order_submitted": False,
                "private_submit_used": False,
            }
            fill_hash = stable_hash(fill)
            conn.execute(
                """
                INSERT OR IGNORE INTO paper_sim_fills
                (fill_id, order_intent_id, signal_id, contract_id, symbol, target_weight,
                 fill_weight, fill_status, payload_json, payload_hash, created_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fill["fill_id"],
                    order_intent_id,
                    signal_id,
                    contract_id,
                    symbol,
                    target_weight,
                    fill["fill_weight"],
                    fill["fill_status"],
                    json.dumps(fill, ensure_ascii=False, sort_keys=True),
                    fill_hash,
                    fill["created_at_utc"],
                ),
            )
            conn.execute(
                """
                INSERT INTO paper_sim_positions
                (contract_id, symbol, simulated_weight, source_fill_id, updated_at_utc)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(contract_id, symbol) DO UPDATE SET
                    simulated_weight=excluded.simulated_weight,
                    source_fill_id=excluded.source_fill_id,
                    updated_at_utc=excluded.updated_at_utc
                """,
                (contract_id, symbol, target_weight, fill["fill_id"], fill["created_at_utc"]),
            )
            append_event(
                conn,
                "PaperSimulatedFill",
                fill,
                contract_id=contract_id,
                signal_id=signal_id,
                order_intent_id=order_intent_id,
            )
            fills.append(fill)
            position = conn.execute(
                """
                SELECT simulated_weight
                FROM paper_sim_positions
                WHERE contract_id=? AND symbol=?
                """,
                (contract_id, symbol),
            ).fetchone()
            simulated_weight = float(position[0]) if position else 0.0
            reconciliations.append(
                {
                    "contract_id": contract_id,
                    "symbol": symbol,
                    "target_weight": target_weight,
                    "simulated_weight": simulated_weight,
                    "difference": round(simulated_weight - target_weight, 12),
                    "ok": abs(simulated_weight - target_weight) <= 1e-9,
                }
            )

    report = {
        "generated_at_utc": utc_now(),
        "mode": "paper_sim_harness",
        "status": "pass"
        if fills and all(row["ok"] for row in reconciliations)
        else "blocked" if not fills else "fail",
        "paper_enabled": False,
        "live_enabled": False,
        "real_orders": 0,
        "private_submit_used": False,
        "simulated_fill_count": len(fills),
        "reconciliation_ok": bool(fills) and all(row["ok"] for row in reconciliations),
        "unreconciled_count": sum(1 for row in reconciliations if not row["ok"]),
        "fills": fills,
        "reconciliations": reconciliations,
        "paper_promotion_note": "Harness only. Paper mode remains disabled until explicit promotion and clean shadow review.",
    }
    write_json(REPORTS / "paper_sim_harness_latest.json", report)
    write_json(PAPER_SIM / "paper_sim_harness_latest.json", report)
    return report


def write_markdown_status(report: dict[str, Any]) -> None:
    lines = [
        "# Ops Control Plane Status",
        "",
        f"Generated: {report['generated_at_utc']}",
        "",
        "## Counts",
        "",
    ]
    for key, value in report["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- shadow_enabled: {report['kill_state'].get('shadow_enabled')}",
            f"- paper_enabled: {report['kill_state'].get('paper_enabled')}",
            f"- live_enabled: {report['kill_state'].get('live_enabled')}",
            f"- global_disable_file_present: {report['kill_state'].get('global_disable_file_present')}",
            "",
            "## Contracts",
            "",
            "| contract | model | mode | status |",
            "|---|---|---|---|",
        ]
    )
    for contract in report["contracts"]:
        lines.append(
            f"| {contract['contract_id']} | {contract['model_id']} | "
            f"{contract['mode']} | {contract['status']} |"
        )
    write_json(REPORTS / "ops_status_latest.md.json", {"markdown": "\n".join(lines) + "\n"})
    (REPORTS / "ops_status_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow-only ops control plane")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("promote-crypto-shadow")
    run_shadow_parser = sub.add_parser("run-shadow")
    run_shadow_parser.add_argument(
        "--include-pending-validation",
        action="store_true",
        help="Also emit validation-only shadow events for pending contracts. Mismatched sources are rejected no-order.",
    )
    sub.add_parser("report")
    sub.add_parser("self-test-safety")
    sub.add_parser("shadow-health")
    sub.add_parser("paper-sim-harness")
    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print(json.dumps(status_report(), ensure_ascii=False, indent=2))
    elif args.command == "promote-crypto-shadow":
        print(json.dumps(promote_crypto_shadow(), ensure_ascii=False, indent=2))
    elif args.command == "run-shadow":
        print(
            json.dumps(
                run_shadow(include_pending_validation=bool(args.include_pending_validation)),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "report":
        print(json.dumps(status_report(), ensure_ascii=False, indent=2))
    elif args.command == "self-test-safety":
        print(json.dumps(safety_self_test(), ensure_ascii=False, indent=2))
    elif args.command == "shadow-health":
        print(json.dumps(shadow_health_report(), ensure_ascii=False, indent=2))
    elif args.command == "paper-sim-harness":
        print(json.dumps(paper_sim_harness(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
