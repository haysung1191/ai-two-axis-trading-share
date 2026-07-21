from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\ops\scripts\paper_autotrade_executor.py")
SPEC = importlib.util.spec_from_file_location("paper_autotrade_executor", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
executor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executor)


class PaperAutotradeExecutorTests(unittest.TestCase):
    def test_approved_paper_collection_allows_only_paper_evidence_blockers(self) -> None:
        activation = {
            "status": "blocked",
            "blockers": [
                "paper_promotion_evidence_not_ready",
                "paper_promotion_evidence_has_gaps",
            ],
        }

        self.assertTrue(executor.approved_paper_collection(activation, True))
        self.assertFalse(executor.approved_paper_collection(activation, False))

    def test_approved_paper_collection_rejects_non_paper_collection_blockers(self) -> None:
        activation = {
            "status": "blocked",
            "blockers": [
                "paper_promotion_evidence_not_ready",
                "real_order_safety_violation",
            ],
        }

        self.assertFalse(executor.approved_paper_collection(activation, True))


if __name__ == "__main__":
    unittest.main()
