from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_tiny_live_completion_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_tiny_live_completion_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class Cand022TinyLiveCompletionAuditTests(unittest.TestCase):
    def test_audit_reports_not_complete_when_kis_intake_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sources = self.write_source_set(tmp_path, complete=False)
            audit = audit_mod.build_audit("2026-05-14T00:00:00+09:00", sources)

        self.assertEqual(audit["completion_decision"], "NOT_COMPLETE")
        self.assertIn("intake_templates_complete", audit["failed_required_check_ids"])
        self.assertIn("provider_response_validated", audit["failed_required_check_ids"])
        self.assertIn("provider_response_gap_matrix_closed", audit["failed_required_check_ids"])
        self.assertIn("provider_response_import_preview_ready", audit["failed_required_check_ids"])
        self.assertIn("BLOCK_INTAKE_ROWS_INCOMPLETE", json.dumps(audit["prompt_to_artifact_checklist"]))
        self.assertFalse(audit["safety"]["order_intent_created"])

    def test_audit_can_reach_complete_only_when_every_required_artifact_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sources = self.write_source_set(tmp_path, complete=True)
            audit = audit_mod.build_audit("2026-05-14T00:00:00+09:00", sources)

        self.assertEqual(audit["completion_decision"], "COMPLETE")
        self.assertEqual(audit["failed_required_check_ids"], [])
        self.assertFalse(audit["safety"]["broker_submit_allowed"])

    def write_source_set(self, root: Path, complete: bool) -> dict[str, Path]:
        paths = {key: root / f"{key}.json" for key in audit_mod.SOURCE_FILES if key != "human_mandate"}
        paths["human_mandate"] = root / "human_mandate.yaml"

        self.write_json(
            paths["preconditions"],
            {
                "summary": {
                    "stage5_internal_evidence_passed": True,
                    "cap_compliant_preintent_route_count": 1,
                },
                "failed_required_checks": [] if complete else ["kis_order_constraints_all_latest_symbols"],
            },
        )
        self.write_json(
            paths["pretrade_firewall"],
            {
                "summary": {
                    "decision": "PASS" if complete else "BLOCK",
                    "order_intent_created": True if complete else False,
                },
                "blockers": [] if complete else ["pretrade_firewall_default_block"],
            },
        )
        self.write_json(
            paths["stage6_shadow"],
            {
                "shadow_queue_allowed": complete,
                "shadow_passed": complete,
                "blockers": [] if complete else ["stage6_shadow_readiness_block"],
            },
        )
        self.write_json(
            paths["pit_manifest"],
            {
                "status": "PASS_OPERATION_READY_MANIFEST" if complete else "BLOCK_OPERATION_READY_MANIFEST",
                "operation_ready": complete,
                "component_status": {},
                "blockers": [] if complete else ["membership_verifier_not_operation_ready"],
            },
        )
        self.write_json(
            paths["data_requirements"],
            {
                "status": "READY_FOR_CANONICAL_REVIEW" if complete else "BLOCKED_AWAITING_AUTHORITATIVE_DATA_ROWS",
                "remaining_blockers": [] if complete else ["authoritative_membership_rows_required_for_latest_cand022_holdings"],
            },
        )
        self.write_json(
            paths["provider_response_validator"],
            {
                "status": "READY_TO_IMPORT_PROVIDER_RESPONSE_TO_INTAKE_REVIEW" if complete else "BLOCK_PROVIDER_RESPONSE_NOT_READY",
                "blockers": [] if complete else ["membership_response_empty"],
            },
        )
        self.write_json(
            paths["provider_response_gap_matrix"],
            {
                "status": "PASS_PROVIDER_RESPONSE_GAP_MATRIX_CLOSED" if complete else "BLOCK_PROVIDER_RESPONSE_GAPS_REMAIN",
                "missing_counts": {"membership": 0 if complete else 1, "event_or_no_event": 0, "replay": 0},
                "total_missing_response_rows": 0 if complete else 1,
            },
        )
        self.write_json(
            paths["provider_response_import_preview"],
            {
                "status": "READY_FOR_MANUAL_INTAKE_IMPORT_REVIEW" if complete else "BLOCK_PROVIDER_RESPONSE_IMPORT",
                "blockers": [] if complete else ["provider_response_validator_not_ready"],
            },
        )
        self.write_json(
            paths["intake_templates"],
            {
                "status": "READY_TO_COPY_INTAKE_TO_CANONICAL_REVIEW" if complete else "BLOCK_INTAKE_ROWS_INCOMPLETE",
                "blockers": [] if complete else ["membership_intake_rows_incomplete_or_not_operation_ready"],
            },
        )
        self.write_json(
            paths["canonical_promotion_preview"],
            {
                "status": "READY_FOR_HUMAN_CANONICAL_APPEND_REVIEW" if complete else "BLOCK_CANONICAL_PROMOTION_PREVIEW",
                "blockers": [] if complete else ["intake_templates_not_ready_for_canonical_review"],
            },
        )
        status_pairs = {
            "membership_verifier": "PASS_MEMBERSHIP_FILES_VERIFIED",
            "delisting_event_verifier": "PASS_DELISTING_EVENT_FILE_VERIFIED",
            "delisting_no_event_coverage_verifier": "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED",
            "delisting_replay_verifier": "PASS_DELISTING_REPLAY_VERIFIED",
            "delisting_symbol_policy": "PASS_DELISTING_SYMBOL_POLICY_VERIFIED",
            "rebalance_membership_filter": "PASS_REBALANCE_MEMBERSHIP_FILTER_PROOF",
            "upgrade_plan": "READY_FOR_REGISTRY_REVIEW",
            "operator_decision_packet": "READY",
        }
        for key, pass_status in status_pairs.items():
            self.write_json(paths[key], {"status": pass_status if complete else f"BLOCK_{key.upper()}", "blockers": [] if complete else [f"{key}_blocked"]})
        if not complete:
            self.write_json(paths["delisting_event_verifier"], {"status": "BLOCK_DELISTING_EVENT_FILE_NOT_VERIFIED", "blockers": ["event_rows_missing"]})
            self.write_json(paths["delisting_no_event_coverage_verifier"], {"status": "BLOCK_DELISTING_NO_EVENT_COVERAGE_NOT_VERIFIED", "blockers": ["no_event_rows_missing"]})
            self.write_json(paths["upgrade_plan"], {"status": "BLOCKED_DATA_UPGRADE_REQUIRED", "remaining_blockers": ["point_in_time_universe_not_verified"]})

        paths["human_mandate"].write_text(
            "\n".join(
                [
                    f"mandate_status: {'COMPLETE' if complete else 'CAPS_PROVIDED'}",
                    "max_order_krw: 100000",
                    "max_daily_loss_krw: 20000",
                    "max_total_loss_krw: 100000",
                    f"reporting_policy: {'email_3h' if complete else 'null'}",
                    f"incident_policy_confirmed: {'true' if complete else 'null'}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return paths

    def write_json(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
