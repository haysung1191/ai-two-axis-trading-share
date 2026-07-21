from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\build_kis_api_document_gap_report.py")
SPEC = importlib.util.spec_from_file_location("build_kis_api_document_gap_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
gap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gap)


class KisApiDocumentGapReportTests(unittest.TestCase):
    def test_old_domestic_order_tr_id_is_blocker(self) -> None:
        with patch.object(
            gap,
            "current_kis_code_signals",
            return_value={
                "uses_domestic_cash_order_old_buy_tr": True,
                "uses_domestic_cash_order_old_sell_tr": False,
                "uses_domestic_cash_order_new_buy_tr": False,
                "uses_domestic_cash_order_new_sell_tr": False,
                "uses_overseas_us_buy_tr": True,
                "uses_overseas_us_sell_tr": True,
                "uses_domestic_daily_itemchartprice": True,
                "uses_overseas_dailyprice": False,
                "uses_overseas_search": False,
                "uses_overseas_product_info": False,
            },
        ), patch.object(gap, "find_doc_path", return_value=Path("doc.xlsx")), patch.object(
            gap,
            "workbook_sheet_rows",
            return_value={
                i: {"name": label, "rows": [["API 명", label], ["실전 TR_ID", "TR"], ["URL 명", "/url"]]}
                for i, label in gap.WATCHED_SHEET_INDEXES.items()
            },
        ):
            report = gap.build_report()

        self.assertIn("DOMESTIC_ORDER_USES_OLD_TR_ID", report["blockers"])
        self.assertIn("OVERSEAS_DAILY_HISTORY_API_NOT_IMPLEMENTED", report["blockers"])


if __name__ == "__main__":
    unittest.main()
