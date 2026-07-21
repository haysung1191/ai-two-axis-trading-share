from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.policy.models import (
    PolicyBundleValidationError,
    PolicyFlags,
    PolicyManifest,
    PolicyRuntimeState,
    validate_bundle_payload,
)

class PolicyBundleLoader:
    def __init__(self, bundle_path: str, manifest_path: str | None = None) -> None:
        self._bundle_path = Path(bundle_path)
        self._manifest_path = Path(manifest_path) if manifest_path else None

    def load(self, flags: PolicyFlags) -> PolicyRuntimeState:
        if not (flags.shadow_enabled or flags.active_enabled or flags.trace_enabled):
            return PolicyRuntimeState(status="disabled", bundle=None, manifest=None)

        if not self._bundle_path.exists():
            return PolicyRuntimeState(status="missing", bundle=None, manifest=None, error="bundle file not found")

        try:
            bundle_bytes = self._bundle_path.read_bytes()
            payload = json.loads(bundle_bytes.decode("utf-8"))
            bundle = validate_bundle_payload(payload)
            manifest = None
            if self._manifest_path and self._manifest_path.exists():
                manifest = PolicyManifest.model_validate(json.loads(self._manifest_path.read_text(encoding="utf-8")))
                self._validate_manifest(manifest, bundle_bytes=bundle_bytes, bundle=bundle)
            return PolicyRuntimeState(status="loaded", bundle=bundle, manifest=manifest)
        except PolicyBundleValidationError as exc:
            status = "expired" if exc.code == "expired" else "invalid"
            return PolicyRuntimeState(status=status, bundle=None, manifest=None, error=str(exc))
        except Exception as exc:
            return PolicyRuntimeState(status="invalid", bundle=None, manifest=None, error=str(exc))

    def _validate_manifest(self, manifest: PolicyManifest, *, bundle_bytes: bytes, bundle) -> None:
        if manifest.compatibility.policy_contract_version != "v2":
            raise ValueError("Unsupported policy contract version in manifest.")
        if manifest.bundle_id != bundle.bundle_id:
            raise ValueError("Manifest bundle_id does not match policy bundle.")
        if manifest.source_run_id != bundle.source_run_id:
            raise ValueError("Manifest source_run_id does not match policy bundle.")

        target = None
        for file_entry in manifest.files:
            if file_entry.name == self._bundle_path.name:
                target = file_entry
                break

        if target is None:
            raise ValueError("Manifest missing bundle file entry.")

        actual_sha = hashlib.sha256(bundle_bytes).hexdigest()
        if actual_sha != target.sha256:
            raise ValueError("Policy bundle checksum mismatch.")
