from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_stage_loop_restructure_completion_audit.py")
SPEC = importlib.util.spec_from_file_location("build_stage_loop_restructure_completion_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class StageLoopRestructureCompletionAuditTests(unittest.TestCase):
    def test_completion_requires_shadow_paper_optional_stage9_wait_and_safety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = root / "AGENTS.md"
            impl = root / "build_stage13_completion_audit.py"
            agents.write_text("contract", encoding="utf-8")
            impl.write_text("impl", encoding="utf-8")
            stage13 = {
                "failed_required_stage_ids": ["stage9"],
                "current_target_stage_id": 9,
                "canonical_stage_source": str(agents),
                "stage_policy_implementation": str(impl),
                "prompt_to_artifact_checklist": [
                    {"stage_id": "retired_shadow_paper_state", "passed": True}
                ],
                "safety": audit.SAFETY,
            }
            stage_status = {
                "stages": [
                    {"id": 6, "autonomous_action": "OPTIONAL_DIAGNOSTIC_ONLY_NOT_REQUIRED"},
                    {"id": 7, "autonomous_action": "OPTIONAL_DIAGNOSTIC_ONLY_NOT_REQUIRED"},
                ],
                "safety": audit.SAFETY,
            }
            direct_next = {
                "status": "WAITING_FOR_EXACT_LIVE_APPROVAL_OR_NO_SUBMIT_POLICY",
                "next_command": "LIVE APPROVE <max_krw> <max_daily_loss_krw> <max_total_loss_krw>",
                "safety": audit.SAFETY,
            }
            direct_blocker = {
                "direct_blockers": [{"axis": "PIPELINE_STAGE9"}],
                "safety": audit.SAFETY,
            }
            payloads = [stage13, stage_status, direct_next, direct_blocker]

            with patch.object(audit, "read_json", side_effect=payloads):
                report = audit.build_report("2026-05-16T00:00:00")

        self.assertEqual(report["completion_decision"], "COMPLETE")
        self.assertEqual(report["missing_or_weak_requirements"], [])

    def test_completion_fails_if_shadow_loop_is_required(self) -> None:
        class Spec:
            def __init__(self, script: str, required: bool) -> None:
                self.script = script
                self.required = required

        class Supervisor:
            @staticmethod
            def loop_specs():
                return [Spec("run_stage6_shadow_loop.py", True)]

        with patch.object(audit, "load_supervisor_module", return_value=Supervisor):
            report = audit.build_report("2026-05-16T00:00:00")

        self.assertEqual(report["completion_decision"], "NOT_COMPLETE")
        self.assertIn("supervisor_required_loops_exclude_shadow_and_paper", report["missing_or_weak_requirements"])


if __name__ == "__main__":
    unittest.main()
