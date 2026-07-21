from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domains.governance.contracts import ApprovedStrategy, ApprovedStrategyBundle
from app.domains.governance.policy_bundle import (
    DEFAULT_KRW_SHADOW_UNIVERSE,
    PolicyBundleExportError,
    PolicyBundleExporter,
)
from src.policy.models import validate_bundle_payload


def _approved_bundle(*, symbol: str = "BTCUSDT", parameters: dict | None = None) -> ApprovedStrategyBundle:
    return ApprovedStrategyBundle(
        winners=[
            ApprovedStrategy(
                strategy_id="momentum_alpha_approved",
                approved_at=datetime.now(UTC),
                source_run_id="bundle-pass-1",
                symbol=symbol,
                timeframe="1h",
                parameters=parameters or {},
                metrics={"sharpe": 1.8},
                risk_limits={"position_size": 0.1},
            )
        ]
    )


def _strategy_lookup(*, category: str = "momentum") -> dict[str, dict]:
    return {
        "momentum_alpha_approved": {
            "name": "momentum_alpha",
            "strategy_name": "momentum_alpha",
            "source_type": "new",
            "category": category,
            "parent_strategy": None,
        }
    }


def test_policy_bundle_export_defaults_generic_shadow_scope_to_universe(tmp_path: Path) -> None:
    exporter = PolicyBundleExporter(root_dir=tmp_path / "artifacts")
    artifacts = exporter.export(
        run_id="bundle-pass-1",
        approved_bundle=_approved_bundle(),
        strategy_lookup=_strategy_lookup(category="momentum"),
        bundle_mode="shadow",
    )

    bundle = artifacts.bundle_payload
    assert bundle["schema_version"] == "v2"
    assert bundle["strategies"][0]["strategy_id"] == "momentum_alpha_approved"
    assert bundle["strategies"][0]["symbol_scope"] == list(DEFAULT_KRW_SHADOW_UNIVERSE)
    assert len(bundle["strategies"][0]["symbol_scope"]) == len(set(bundle["strategies"][0]["symbol_scope"]))
    assert validate_bundle_payload(bundle).bundle_id == bundle["bundle_id"]


def test_policy_bundle_export_keeps_single_scope_when_requested(tmp_path: Path) -> None:
    exporter = PolicyBundleExporter(root_dir=tmp_path / "artifacts")
    artifacts = exporter.export(
        run_id="bundle-pass-1",
        approved_bundle=_approved_bundle(parameters={"policy_scope_mode": "single"}),
        strategy_lookup=_strategy_lookup(category="mean_reversion"),
        bundle_mode="shadow",
    )

    bundle = artifacts.bundle_payload
    assert bundle["strategies"][0]["symbol_scope"] == ["KRW-BTC"]
    assert validate_bundle_payload(bundle).bundle_id == bundle["bundle_id"]


def test_policy_bundle_export_keeps_active_mode_single_scope_for_backward_compatibility(tmp_path: Path) -> None:
    exporter = PolicyBundleExporter(root_dir=tmp_path / "artifacts")
    artifacts = exporter.export(
        run_id="bundle-pass-1",
        approved_bundle=_approved_bundle(),
        strategy_lookup=_strategy_lookup(category="trend_following"),
        bundle_mode="active",
    )

    assert artifacts.bundle_payload["strategies"][0]["symbol_scope"] == ["KRW-BTC"]


def test_policy_bundle_export_supports_explicit_universe_scope(tmp_path: Path) -> None:
    exporter = PolicyBundleExporter(root_dir=tmp_path / "artifacts")
    artifacts = exporter.export(
        run_id="bundle-pass-1",
        approved_bundle=_approved_bundle(
            parameters={
                "policy_scope_mode": "universe",
                "policy_export_universe": ["krw-eth", "KRW-BTC", "KRW-ETH", " KRW-SOL "],
            }
        ),
        strategy_lookup=_strategy_lookup(category="momentum"),
        bundle_mode="shadow",
    )

    assert artifacts.bundle_payload["strategies"][0]["symbol_scope"] == ["KRW-BTC", "KRW-ETH", "KRW-SOL"]


def test_policy_bundle_export_normalizes_explicit_scope_to_runtime_symbols(tmp_path: Path) -> None:
    exporter = PolicyBundleExporter(root_dir=tmp_path / "artifacts")
    artifacts = exporter.export(
        run_id="bundle-pass-1",
        approved_bundle=_approved_bundle(
            parameters={
                "policy_scope_mode": "universe",
                "policy_export_universe": ["btcusdt", "ETHUSDT", "krw-xrp"],
            }
        ),
        strategy_lookup=_strategy_lookup(category="momentum"),
        bundle_mode="shadow",
    )

    assert artifacts.bundle_payload["strategies"][0]["symbol_scope"] == ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
    assert validate_bundle_payload(artifacts.bundle_payload).bundle_id == artifacts.bundle_payload["bundle_id"]


def test_policy_bundle_export_rejects_empty_explicit_scope(tmp_path: Path) -> None:
    exporter = PolicyBundleExporter(root_dir=tmp_path / "artifacts")

    with pytest.raises(PolicyBundleExportError, match="empty"):
        exporter.export(
            run_id="bundle-pass-1",
            approved_bundle=_approved_bundle(parameters={"symbol_scope": []}),
            strategy_lookup=_strategy_lookup(category="momentum"),
            bundle_mode="shadow",
        )
