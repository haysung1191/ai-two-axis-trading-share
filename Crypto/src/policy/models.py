from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class PolicyBundleValidationError(ValueError):
    def __init__(self, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.code = code


def require_utc_timestamp(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PolicyBundleValidationError(f"{field_name} must be a timezone-aware ISO8601 timestamp.")
    return value.astimezone(UTC)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PolicyBundleFile(StrictBaseModel):
    name: str
    sha256: str

    @model_validator(mode="after")
    def validate_sha(self) -> "PolicyBundleFile":
        value = self.sha256.strip().lower()
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            raise PolicyBundleValidationError("manifest file sha256 must be a 64-character lowercase hex string.")
        self.sha256 = value
        return self


class PolicyCompatibility(StrictBaseModel):
    scanner_min_version: str
    policy_contract_version: str


class PolicyManifest(StrictBaseModel):
    schema_version: Literal["v1"]
    bundle_id: str
    source_run_id: str
    created_at: datetime
    files: list[PolicyBundleFile]
    compatibility: PolicyCompatibility

    @model_validator(mode="after")
    def validate_manifest(self) -> "PolicyManifest":
        self.created_at = require_utc_timestamp(self.created_at, "created_at")
        if not self.files:
            raise PolicyBundleValidationError("Manifest must contain at least one file entry.")
        return self


class PolicyDecisionRules(StrictBaseModel):
    allow_if: list[str]
    boost_score: float
    reject_if: list[str]

    @model_validator(mode="after")
    def validate_rules(self) -> "PolicyDecisionRules":
        allowed_features = {"close", "ema_20", "ema_50", "volume_zscore", "drawdown_7d"}
        allowed_operators = (" >= ", " <= ", " == ", " != ", " > ", " < ")
        for clause in list(self.allow_if) + list(self.reject_if):
            if not isinstance(clause, str) or not clause.strip():
                raise PolicyBundleValidationError("Policy clauses must be non-empty strings.")
            operator = next((item for item in allowed_operators if item in clause), None)
            if operator is None:
                raise PolicyBundleValidationError(f"Malformed policy clause: {clause}")
            left, right = clause.split(operator, 1)
            if left.strip() not in allowed_features:
                raise PolicyBundleValidationError(f"Unsupported policy clause: {clause}")
            rhs = right.strip()
            if rhs not in allowed_features:
                try:
                    float(rhs)
                except ValueError as exc:
                    raise PolicyBundleValidationError(f"Unsupported policy clause rhs: {clause}") from exc
        return self


class PolicyStrategy(StrictBaseModel):
    strategy_id: str
    status: Literal["APPROVED"]
    symbol_scope: list[str]
    timeframe: str
    policy_type: Literal["filter_and_boost"]
    parameters: dict[str, Any]
    decision_rules: PolicyDecisionRules
    valid_until: datetime
    checksum: str

    @model_validator(mode="after")
    def validate_strategy(self) -> "PolicyStrategy":
        if not self.strategy_id.strip():
            raise PolicyBundleValidationError("strategy_id must be non-empty.")
        self.valid_until = require_utc_timestamp(self.valid_until, "valid_until")
        deduped = sorted({str(item).strip().upper() for item in self.symbol_scope if str(item).strip()})
        if not deduped:
            raise PolicyBundleValidationError(f"Policy strategy '{self.strategy_id}' must have non-empty symbol_scope.")
        self.symbol_scope = deduped
        checksum = self.checksum.strip().lower()
        if not checksum.startswith("sha256:") or len(checksum) != 71:
            raise PolicyBundleValidationError(f"Invalid checksum format for {self.strategy_id}.")
        return self


class PolicyBundle(StrictBaseModel):
    schema_version: Literal["v2"]
    bundle_id: str
    generated_at: datetime
    source_run_id: str
    bundle_mode: Literal["shadow", "active"]
    strategies: list[PolicyStrategy]

    @model_validator(mode="after")
    def validate_bundle(self) -> "PolicyBundle":
        self.generated_at = require_utc_timestamp(self.generated_at, "generated_at")
        if not self.strategies:
            raise PolicyBundleValidationError("Policy bundle must contain at least one strategy.")
        strategy_ids = [item.strategy_id for item in self.strategies]
        if len(strategy_ids) != len(set(strategy_ids)):
            raise PolicyBundleValidationError("Policy bundle contains duplicate strategy_id values.")
        return self


@dataclass(frozen=True)
class PolicyFlags:
    trace_enabled: bool = False
    shadow_enabled: bool = False
    active_enabled: bool = False
    symbol_allowlist: tuple[str, ...] = ()
    max_score_delta: float = 0.15
    soft_reject_enabled: bool = False


@dataclass(frozen=True)
class PolicyRuntimeState:
    status: str
    bundle: PolicyBundle | None
    manifest: PolicyManifest | None
    error: str | None = None


@dataclass(frozen=True)
class PolicyCandidateInput:
    symbol: str
    scanner_score: float
    features: dict[str, float]


@dataclass(frozen=True)
class PolicyEvaluationResult:
    symbol: str
    matched_strategy_id: str | None
    policy_decision: Literal["NEUTRAL", "BOOST", "SOFT_REJECT"]
    policy_score_delta: float
    reasons: tuple[str, ...]
    deterministic_hash: str


def stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_strategy_checksum(strategy_payload: dict[str, Any]) -> str:
    raw = json.dumps(strategy_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_trace_hash(trace_payload: dict[str, Any]) -> str:
    return stable_hash(trace_payload)


def validate_bundle_payload(payload: dict[str, Any], *, now: datetime | None = None) -> PolicyBundle:
    try:
        bundle = PolicyBundle.model_validate(payload)
    except ValidationError as exc:
        raise PolicyBundleValidationError(f"Invalid policy bundle payload: {exc}") from exc

    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    for strategy in bundle.strategies:
        content = strategy.model_dump(mode="json")
        checksum = content.pop("checksum")
        expected = compute_strategy_checksum(content)
        if checksum != expected:
            raise PolicyBundleValidationError(f"Policy strategy checksum mismatch for {strategy.strategy_id}")
        if strategy.valid_until <= current_time:
            raise PolicyBundleValidationError(f"Policy strategy expired: {strategy.strategy_id}", code="expired")
    return bundle
