import unittest

import build_goal_session_duplicate_review_packet as packet_builder


class GoalSessionDuplicateReviewPacketTest(unittest.TestCase):
    def test_detects_duplicate_goal_sessions_without_cleanup(self) -> None:
        processes = [
            {
                "ProcessId": 101,
                "ParentProcessId": 1,
                "Name": "codex.exe",
                "CommandLine": 'codex.exe --enable goals --cd C:\\AI --no-alt-screen "/goal C:\\AI model-development factory goal"',
            },
            {
                "ProcessId": 102,
                "ParentProcessId": 2,
                "Name": "codex.exe",
                "CommandLine": 'codex.exe --enable goals --cd "C:\\AI" --no-alt-screen "/goal C:\\AI model-development factory goal"',
            },
            {
                "ProcessId": 201,
                "ParentProcessId": 3,
                "Name": "python.exe",
                "CommandLine": "python C:\\AI\\run_gatekeeper_refresh_loop.py --cycles 288",
            },
        ]

        packet = packet_builder.build_packet(processes)

        self.assertEqual(packet["status"], "DUPLICATE_GOAL_SESSIONS_DETECTED")
        self.assertEqual(packet["model_factory_goal_process_chain_count"], 2)
        self.assertEqual(packet["model_factory_goal_codex_process_count"], 2)
        self.assertEqual(packet["duplicate_model_factory_goal_process_count"], 1)
        self.assertEqual(packet["model_factory_goal_process_ids"], [101, 102])
        self.assertEqual(packet["safe_loop_process_count"], 1)
        self.assertFalse(packet["auto_cleanup_allowed"])
        self.assertFalse(packet["stop_process_executed"])
        self.assertFalse(packet["safety"]["does_stop_processes"])
        self.assertFalse(packet["safety"]["does_enable_live"])
        self.assertFalse(packet["safety"]["does_submit_orders"])

    def test_single_goal_session_is_not_duplicate(self) -> None:
        packet = packet_builder.build_packet(
            [
                {
                    "ProcessId": 101,
                    "ParentProcessId": 1,
                    "Name": "codex.exe",
                    "CommandLine": 'codex.exe --enable goals --cd C:\\AI --no-alt-screen "/goal C:\\AI model-development factory goal"',
                }
            ]
        )

        self.assertEqual(packet["status"], "SINGLE_OR_NO_GOAL_SESSION")
        self.assertEqual(packet["model_factory_goal_codex_process_count"], 1)
        self.assertEqual(packet["duplicate_model_factory_goal_process_count"], 0)
        self.assertFalse(packet["auto_cleanup_allowed"])


if __name__ == "__main__":
    unittest.main()
