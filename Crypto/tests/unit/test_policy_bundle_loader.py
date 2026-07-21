import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.policy.loader import PolicyBundleLoader
from src.policy.models import PolicyFlags, compute_strategy_checksum


def _base_strategy() -> dict:
    return {
        "strategy_id": "strat-1",
        "status": "APPROVED",
        "symbol_scope": ["KRW-BTC"],
        "timeframe": "1h",
        "policy_type": "filter_and_boost",
        "parameters": {"category": "momentum"},
        "decision_rules": {
            "allow_if": ["close > ema_20"],
            "boost_score": 0.1,
            "reject_if": ["volume_zscore < -0.5000"],
        },
        "valid_until": (datetime.now(UTC) + timedelta(days=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _with_checksum(strategy: dict) -> dict:
    payload = dict(strategy)
    payload.pop("checksum", None)
    payload["symbol_scope"] = sorted({str(item).strip().upper() for item in payload.get("symbol_scope", []) if str(item).strip()})
    payload["checksum"] = compute_strategy_checksum(payload)
    return payload


def _write_bundle(tmp_path: Path, *, bundle_override=None, manifest_override=None, write_manifest: bool = True) -> tuple[Path, Path]:
    bundle = {
        "schema_version": "v2",
        "bundle_id": "policy_test",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_run_id": "run-1",
        "bundle_mode": "shadow",
        "strategies": [_with_checksum(_base_strategy())],
    }
    if bundle_override:
        bundle.update(bundle_override)
    if "strategies" in bundle:
        bundle["strategies"] = [_with_checksum(item) for item in bundle["strategies"]]

    bundle_path = tmp_path / "policy_bundle.json"
    bundle_bytes = json.dumps(bundle, sort_keys=True, indent=2).encode("utf-8")
    bundle_path.write_bytes(bundle_bytes)

    manifest_path = tmp_path / "manifest.json"
    if write_manifest:
        manifest = {
            "schema_version": "v1",
            "bundle_id": bundle["bundle_id"],
            "source_run_id": bundle["source_run_id"],
            "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "files": [{"name": "policy_bundle.json", "sha256": hashlib.sha256(bundle_bytes).hexdigest()}],
            "compatibility": {"scanner_min_version": "1.0.0", "policy_contract_version": "v2"},
        }
        if manifest_override:
            manifest.update(manifest_override)
        manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
    return bundle_path, manifest_path


def test_valid_policy_bundle_loads(tmp_path: Path) -> None:
    strategy = _base_strategy()
    strategy["symbol_scope"] = ["KRW-BTC", "krw-btc"]
    bundle_path, manifest_path = _write_bundle(tmp_path, bundle_override={"strategies": [strategy]})
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "loaded"
    assert state.bundle is not None
    assert state.bundle.strategies[0].symbol_scope == ["KRW-BTC"]


def test_missing_manifest_with_valid_bundle_loads(tmp_path: Path) -> None:
    bundle_path, manifest_path = _write_bundle(tmp_path, write_manifest=False)
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "loaded"
    assert state.bundle is not None
    assert state.manifest is None


def test_missing_file_falls_back_cleanly(tmp_path: Path) -> None:
    state = PolicyBundleLoader(str(tmp_path / "missing.json"), str(tmp_path / "missing_manifest.json")).load(PolicyFlags(trace_enabled=True))
    assert state.status == "missing"
    assert state.bundle is None


def test_invalid_schema_version_rejected(tmp_path: Path) -> None:
    bundle_path, manifest_path = _write_bundle(tmp_path, bundle_override={"schema_version": "v9"})
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "invalid"


def test_expired_bundle_rejected_with_expired_status(tmp_path: Path) -> None:
    expired = _base_strategy()
    expired["valid_until"] = (datetime.now(UTC) - timedelta(days=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    bundle_path, manifest_path = _write_bundle(tmp_path, bundle_override={"strategies": [expired]})
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "expired"


def test_checksum_mismatch_rejected(tmp_path: Path) -> None:
    bundle_path, manifest_path = _write_bundle(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "deadbeef" * 8
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "invalid"


def test_duplicate_strategy_ids_rejected(tmp_path: Path) -> None:
    strategy = _base_strategy()
    other = _base_strategy()
    bundle_path, manifest_path = _write_bundle(tmp_path, bundle_override={"strategies": [strategy, other]})
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "invalid"
    assert "duplicate strategy_id" in str(state.error).lower()


def test_unknown_rule_key_rejected(tmp_path: Path) -> None:
    strategy = _base_strategy()
    strategy["decision_rules"] = {
        "allow_if": ["close > ema_20"],
        "boost_score": 0.1,
        "reject_if": [],
        "bogus": True,
    }
    bundle_path, manifest_path = _write_bundle(tmp_path, bundle_override={"strategies": [strategy]})
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "invalid"


def test_malformed_timestamp_rejected(tmp_path: Path) -> None:
    strategy = _base_strategy()
    strategy["valid_until"] = "not-a-timestamp"
    bundle_path, manifest_path = _write_bundle(tmp_path, bundle_override={"strategies": [strategy]})
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "invalid"


def test_partial_invalid_json_file_rejected(tmp_path: Path) -> None:
    bundle_path = tmp_path / "policy_bundle.json"
    bundle_path.write_text('{"schema_version": "v2"', encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "invalid"


def test_empty_strategies_bundle_rejected(tmp_path: Path) -> None:
    bundle_path, manifest_path = _write_bundle(tmp_path, bundle_override={"strategies": []})
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(PolicyFlags(trace_enabled=True))
    assert state.status == "invalid"
