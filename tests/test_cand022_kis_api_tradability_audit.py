from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_kis_api_tradability_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_kis_api_tradability_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class Cand022KisApiTradabilityAuditTests(unittest.TestCase):
    def test_current_cand022_us_symbols_have_exchange_mappings(self) -> None:
        expected = {
            "CAT": ("NYSE", "NYS"),
            "DOW": ("NYSE", "NYS"),
            "GEV": ("NYSE", "NYS"),
            "XLE": ("AMEX", "AMS"),
            "XOM": ("NYSE", "NYS"),
        }

        for symbol, pair in expected.items():
            self.assertEqual(audit_mod.resolve_us_exchange(symbol), pair)

    def test_unknown_symbol_still_reports_missing_mapping(self) -> None:
        self.assertEqual(audit_mod.resolve_us_exchange("NO_SUCH_SYMBOL"), (None, None))


if __name__ == "__main__":
    unittest.main()
