import sqlite3
import sys
import types
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.policy_sanity_check import run_check
from src.policy.loader import PolicyBundleLoader
from src.policy.models import PolicyFlags, compute_strategy_checksum


def _bundle_payload() -> dict:
    strategy = {
        "strategy_id": "strat-1",
        "status": "APPROVED",
        "symbol_scope": ["KRW-BTC"],
        "timeframe": "1h",
        "policy_type": "filter_and_boost",
        "parameters": {"category": "momentum"},
        "decision_rules": {
            "allow_if": ["close > ema_20", "ema_20 > ema_50"],
            "boost_score": 0.1,
            "reject_if": ["drawdown_7d > 0.2000"],
        },
        "valid_until": "2099-01-01T00:00:00Z",
    }
    strategy["checksum"] = compute_strategy_checksum(strategy)
    return {
        "schema_version": "v2",
        "bundle_id": "bundle-1",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_run_id": "run-1",
        "bundle_mode": "shadow",
        "strategies": [strategy],
    }


def test_dashboard_renders_when_selection_trace_table_missing(tmp_path, monkeypatch) -> None:
    jinja2_stub = types.ModuleType("jinja2")

    class _Env:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def get_template(self, name: str):
            return types.SimpleNamespace(render=lambda **kwargs: "ok")

    jinja2_stub.Environment = _Env
    jinja2_stub.FileSystemLoader = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "jinja2", jinja2_stub)

    from jobs import dashboard as dashboard_app

    db_path = tmp_path / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript((Path("migrations") / "001_init.sql").read_text(encoding="utf-8"))
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    data = dashboard_app._get_data()
    assert data["recent_selection_traces"] == []


def test_loader_safe_when_bundle_directory_exists_but_files_absent(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "policy" / "current"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    state = PolicyBundleLoader(
        bundle_path=str(bundle_dir / "policy_bundle.json"),
        manifest_path=str(bundle_dir / "manifest.json"),
    ).load(PolicyFlags(trace_enabled=True))
    assert state.status == "missing"


def test_manifest_only_case_stays_safe(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "policy" / "current"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "manifest.json").write_text("{}", encoding="utf-8")
    state = PolicyBundleLoader(
        bundle_path=str(bundle_dir / "policy_bundle.json"),
        manifest_path=str(bundle_dir / "manifest.json"),
    ).load(PolicyFlags(trace_enabled=True))
    assert state.status == "missing"


def test_sanity_command_works_against_baseline_state(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "state.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.delenv("POLICY_BUNDLE_PATH", raising=False)
    monkeypatch.delenv("POLICY_MANIFEST_PATH", raising=False)
    result = run_check()
    assert result["trace_table_exists"] is True
    assert result["policy_bundle"]["status"] in {"disabled", "missing"}


def test_sanity_check_warns_when_active_mode_disables_trace(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "state.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("TRACE_ENABLED", "0")
    monkeypatch.setenv("POLICY_ACTIVE", "1")
    monkeypatch.delenv("POLICY_BUNDLE_PATH", raising=False)
    monkeypatch.delenv("POLICY_MANIFEST_PATH", raising=False)

    result = run_check()

    assert "POLICY_ACTIVE is enabled while TRACE_ENABLED is disabled." in result["warnings"]


def test_sanity_check_warns_when_loaded_policy_trace_lags_latest_run(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "state.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("TRACE_ENABLED", "1")
    monkeypatch.setenv("POLICY_ACTIVE", "1")
    bundle_dir = tmp_path / "policy" / "current"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundle_dir / "policy_bundle.json"
    manifest_path = bundle_dir / "manifest.json"
    bundle = _bundle_payload()
    bundle_bytes = json.dumps(bundle, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8")
    manifest = {
        "schema_version": "v1",
        "bundle_id": "bundle-1",
        "source_run_id": "run-1",
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "files": [{"name": "policy_bundle.json", "sha256": hashlib.sha256(bundle_bytes).hexdigest()}],
        "compatibility": {"scanner_min_version": "1.0.0", "policy_contract_version": "v2"},
    }
    bundle_path.write_bytes(bundle_bytes)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")
    monkeypatch.setenv("POLICY_BUNDLE_PATH", str(bundle_path))
    monkeypatch.setenv("POLICY_MANIFEST_PATH", str(manifest_path))

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript((Path("migrations") / "001_init.sql").read_text(encoding="utf-8"))
    conn.executescript((Path("migrations") / "002_selection_trace.sql").read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO runs(run_id, candle_close_ts_ms, status) VALUES (?, ?, 'COMPLETED')",
        ("1h:1", 3600000),
    )
    conn.execute(
        "INSERT INTO selection_trace(ts, symbol, scanner_score, policy_bundle_id, policy_decision, policy_score_delta, risk_pass, final_decision, trace_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("1970-01-01T00:00:00Z", "BTC", 1.0, "bundle-1", "NEUTRAL", 0.0, 1, "SCHEDULED", "{}"),
    )
    conn.commit()
    conn.close()

    result = run_check()

    assert result["policy_bundle"]["status"] == "loaded"
    assert result["latest_completed_run"]["candle_close_utc"] == "1970-01-01T01:00:00Z"
    assert "Policy bundle is loaded but selection_trace has not caught up to the latest completed run." in result["warnings"]
