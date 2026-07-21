import unittest

import build_loop_contract_drift_report as report


class LoopContractDriftReportTests(unittest.TestCase):
    def test_process_running_matches_script(self):
        processes = [{"ProcessId": 123, "CommandLine": r"python C:\AI\run_gatekeeper_refresh_loop.py --cycles 1"}]

        running, pids = report.process_running("run_gatekeeper_refresh_loop.py", processes)

        self.assertTrue(running)
        self.assertEqual(pids, [123])

    def test_classify_loop_flags_max_hours_stopped_process(self):
        spec = {
            "name": "crypto_recursive_improvement",
            "script": "run_crypto_recursive_improvement_loop.py",
            "lane": "research",
            "required_when": "pipeline_active",
            "latest_path": report.ROOT / "does_not_exist.json",
        }

        original = report.read_json
        try:
            report.read_json = lambda path: {"stop_reason": "max_hours_reached", "cycles_completed": 80}
            row = report.classify_loop(spec, [])
        finally:
            report.read_json = original

        self.assertFalse(row["running"])
        self.assertIn("PROCESS_NOT_RUNNING", row["blockers"])
        self.assertIn("ENDED_BY_MAX_HOURS", row["blockers"])

    def test_report_never_enables_live(self):
        payload = report.build_report()

        self.assertFalse(payload["live_safety"]["does_enable_live"])
        self.assertFalse(payload["live_safety"]["does_enable_private_submit"])
        self.assertFalse(payload["live_safety"]["does_allow_real_orders"])


if __name__ == "__main__":
    unittest.main()
