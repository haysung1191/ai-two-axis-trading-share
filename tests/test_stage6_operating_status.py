from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_stage6_operating_status.py")
SPEC = importlib.util.spec_from_file_location("build_stage6_operating_status", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
status_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(status_mod)


class Stage6OperatingStatusTests(unittest.TestCase):
    def test_report_distinguishes_running_stage6_from_cand022_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage6 = root / "stage6.json"
            cand022 = root / "cand022.json"
            supervisor = root / "supervisor.json"
            slip = root / "slip.json"
            stage6.write_text(
                json.dumps(
                    {
                        "status": "running",
                        "run_id": "run1",
                        "cycles_completed": 3,
                        "cycles_requested": 288,
                        "shadow_queue_candidates": ["CAND-001"],
                        "last_signal_recorded_at": "2026-05-14T19:34:40+09:00",
                        "last_signal_ok": True,
                        "last_readiness_ok": True,
                        "last_symbol_count": 6,
                        "last_residual_blockers": ["data_operation_ready_not_verified"],
                    }
                ),
                encoding="utf-8",
            )
            cand022.write_text(
                json.dumps(
                    {
                        "stage6_reached": False,
                        "completion_decision": "NOT_COMPLETE",
                        "completion_percent_by_checklist": 90.5,
                        "missing_or_blocked_check_ids": ["dispatch_sent_confirmation_recorded"],
                    }
                ),
                encoding="utf-8",
            )
            supervisor.write_text(
                json.dumps(
                    {
                        "cand022_provider_watch_continuity": {
                            "status": "WATCHER_CONTINUITY_OK",
                            "needs_new_watcher": False,
                            "min_remaining_minutes": 10,
                            "max_remaining_minutes": 200,
                            "provider_return_watch_blockers": ["returned_provider_csvs_missing"],
                        },
                        "loops": [
                            {
                                "name": "kis_stage6_shadow_signal_recorder",
                                "running_before": {"matches": [{"process_id": 111}]},
                                "action": {"reason": "already_running"},
                            },
                            {
                                "name": "cand022_provider_return_watch",
                                "running_before": {"matches": [{"process_id": 222}]},
                                "action": {"reason": "already_running"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            slip.write_text(
                json.dumps(
                    {
                        "alternate_path": {
                            "latest_dry_run_status": "DRY_RUN_READY_EXACT_INSTRUCTION_BUT_NOT_EXECUTED",
                            "latest_dry_run_exact_match": True,
                            "latest_dry_run_execute_requested": False,
                            "latest_dry_run_confirm_apply": False,
                            "execute_command": "python apply --execute",
                        }
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch.object(status_mod, "STAGE6_SUMMARY", stage6),
                patch.object(status_mod, "CAND022_AUDIT", cand022),
                patch.object(status_mod, "SUPERVISOR", supervisor),
                patch.object(status_mod, "TWO_PATH_SLIP", slip),
            ):
                report = status_mod.build_report("2026-05-14T19:40:00+09:00")

        self.assertEqual(report["status"], "STAGE6_RUNNING_CAND022_NOT_COMPLETE")
        self.assertTrue(report["broader_stage6_operation"]["running"])
        self.assertEqual(report["broader_stage6_operation"]["shadow_queue_candidates"], ["CAND-001"])
        self.assertEqual(report["broader_stage6_operation"]["supervisor_loop_pids"], [111])
        self.assertFalse(report["cand022_stage6"]["stage6_reached"])
        self.assertEqual(report["cand022_stage6"]["completion_percent"], 90.5)
        self.assertEqual(report["cand022_provider_watch"]["supervisor_loop_pids"], [222])
        self.assertEqual(report["cand022_provider_watch"]["continuity_status"], "WATCHER_CONTINUITY_OK")
        self.assertEqual(
            report["cand022_shadow_only_alternate"]["latest_dry_run_status"],
            "DRY_RUN_READY_EXACT_INSTRUCTION_BUT_NOT_EXECUTED",
        )
        self.assertFalse(report["safety"]["live_enabled"])
        self.assertIn("does_not_apply_shadow_exception", report["non_goals"])
        md = status_mod.render_md(report)
        self.assertIn("Broader Stage 6 Operation", md)
        self.assertIn("CAND-022 Stage 6", md)
        self.assertIn("NOT_COMPLETE", md)


if __name__ == "__main__":
    unittest.main()
