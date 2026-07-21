from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_public_dashboard_export.py")
SPEC = importlib.util.spec_from_file_location("build_public_dashboard_export", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
public_export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(public_export)


class PublicDashboardExportTests(unittest.TestCase):
    def test_public_export_has_one_active_render_html_definition(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8-sig")
        self.assertEqual(source.count("\ndef render_html("), 1)

    def test_write_json_escapes_non_ascii_for_powershell_readability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "public_summary.json"
            public_export.write_json(out_path, {"axis": "가상화폐", "status": "PASS"})
            text = out_path.read_text(encoding="utf-8")

        self.assertIn("\\uac00\\uc0c1\\ud654\\ud3d0", text)
        self.assertNotIn("가상화폐", text)
        self.assertEqual(json.loads(text), {"axis": "가상화폐", "status": "PASS"})

    def test_review_packet_summary_uses_public_safe_order_submission_field(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "stock_conversion_review_packet": {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "candidate_id": "stock_aggressive__trim22",
                "blocker_count": 0,
                "proposed_conversion": {"estimated_cagr": 0.459, "estimated_mdd": -0.199},
                "robustness_stress": {
                    "queue_coverage": {
                        "target_count": 5,
                        "ready_candidate_count": 5,
                        "covered_candidate_count": 5,
                        "stress_pass_candidate_count": 3,
                        "top5_full_coverage": True,
                        "all_covered_candidates_safe": True,
                    }
                },
                "sizing_repair": {
                    "status": "SIZING_REPAIR_READY",
                    "repair_ready_count": 2,
                    "repairs": [
                        {
                            "candidate_id": "stock_aggressive__switchcarry_gap02_top2",
                            "lane": "kis_stocks",
                            "repair_status": "SIZING_REPAIR_READY",
                            "current_fixed_exposure_cap": 0.59,
                            "recommended_fixed_exposure_cap": 0.55,
                            "recommended_overlay": "fixed_exposure_055",
                            "repair_pass_count": 4,
                            "source_path": r"C:\AI\reports\model_factory\stock_risk_conversion_sizing_repair_latest.json",
                            "broker_submit_allowed_by_this_report": False,
                        }
                    ],
                },
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        packet = summary["stock_conversion_review_packet"]
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(packet["candidate_id"], "stock_aggressive__trim22")
        self.assertEqual(packet["top5_target_count"], 5)
        self.assertEqual(packet["top5_ready_candidate_count"], 5)
        self.assertEqual(packet["top5_covered_candidate_count"], 5)
        self.assertEqual(packet["top5_stress_pass_candidate_count"], 3)
        self.assertEqual(packet["sizing_repair_ready_count"], 2)
        self.assertEqual(packet["stress_pass_plus_repair_ready_count"], 5)
        self.assertEqual(packet["sizing_repair_candidates"][0]["candidate_id"], "stock_aggressive__switchcarry_gap02_top2")
        self.assertEqual(packet["sizing_repair_candidates"][0]["recommended_overlay"], "fixed_exposure_055")
        self.assertEqual(packet["sizing_repair_candidates"][0]["repair_pass_count"], 4)
        self.assertTrue(packet["top5_full_coverage"])
        self.assertTrue(packet["top5_all_covered_candidates_safe"])
        self.assertFalse(packet["order_submission_allowed_by_this_report"])
        self.assertIn("top-5 coverage", rendered)
        self.assertIn("5/5", rendered)
        self.assertIn("Stock Conversion Sizing Repair Candidates", rendered)
        self.assertIn("stock_aggressive__switchcarry_gap02_top2", rendered)
        self.assertIn("fixed_exposure_055", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("C:\\AI", rendered)

    def test_experiment_queue_top_queue_preserves_public_safe_evidence_summary(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "model_factory_experiment_queue": {
                "status": "PASS",
                "summary": {"experiment_count": 1, "ready_experiment_count": 1},
                "top_queue": [
                    {
                        "experiment_id": "stock_child",
                        "candidate_id": "stock_a",
                        "repo": "momentum",
                        "lane": "conversion",
                        "experiment_type": "stock_etf_fixed_exposure_child_review",
                        "priority": "P0",
                        "status": "READY",
                        "frozen_scope": {"scope": "risk_conversion_only_no_order_paths"},
                        "gatekeeper_review": {"blockers": []},
                        "evidence_summary": {
                            "before_cagr": 0.7,
                            "estimated_mdd": -0.199,
                            "broker_submit_allowed_by_this_report": False,
                            "source_path": r"C:\AI\reports\model_factory\secret.json",
                        },
                    }
                ],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        evidence = summary["model_factory_experiment_queue"]["top_queue"][0]["evidence_summary"]
        self.assertEqual(evidence["before_cagr"], 0.7)
        self.assertEqual(evidence["estimated_mdd"], -0.199)
        self.assertNotIn("broker_submit_allowed_by_this_report", evidence)
        self.assertNotIn("source_path", evidence)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("C:\\AI", rendered)

    def test_stock_portfolio_sleeve_summary_is_public_and_no_order(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "stock_portfolio_sleeve_review": {
                "status": "PORTFOLIO_SLEEVE_REVIEW_READY",
                "ready_for_gatekeeper_review": True,
                "sleeve_policy": {
                    "component_count": 5,
                    "target_component_count": 5,
                    "total_effective_exposure": 0.606,
                    "max_effective_component_exposure": 0.13,
                    "max_lane_weight": 0.6,
                    "source_path": r"C:\AI\reports\model_factory\stock_portfolio_sleeve_review_latest.json",
                },
                "sleeve_metrics": {
                    "estimated_sleeve_cagr": 0.4404,
                    "weighted_mdd_proxy": -0.1933,
                    "stress_pass_candidate_count": 5,
                    "repaired_candidate_count": 2,
                },
                "counts_as_paper_or_live_evidence": False,
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        sleeve = summary["stock_portfolio_sleeve_review"]
        self.assertEqual(sleeve["status"], "PORTFOLIO_SLEEVE_REVIEW_READY")
        self.assertTrue(sleeve["ready_for_gatekeeper_review"])
        self.assertEqual(sleeve["component_count"], 5)
        self.assertEqual(sleeve["target_component_count"], 5)
        self.assertEqual(sleeve["stress_pass_candidate_count"], 5)
        self.assertEqual(sleeve["repaired_candidate_count"], 2)
        self.assertFalse(sleeve["counts_as_paper_or_live_evidence"])
        self.assertFalse(sleeve["order_submission_allowed_by_this_report"])
        self.assertFalse(sleeve["real_orders_allowed_by_this_report"])
        self.assertIn("Stock Portfolio Sleeve Review", rendered)
        self.assertIn("total effective exposure", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("C:\\AI", rendered)

    def test_btc_eth_alternate_repair_child_summary_is_public_and_no_order(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "btc_eth_intraday_robustness_repair_alternate_child": {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_for_gatekeeper_review": True,
                "base_candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001",
                "primary_child_candidate_id": "robustrepair_445",
                "top_alternate_candidate_id": "robustrepair_441",
                "alternate_pass_child_count": 11,
                "top_alternate_child_count": 5,
                "repair_pass_count": 42,
                "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
                "counts_as_paper_or_live_evidence": False,
                "promotion_allowed_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
                "path": r"C:\AI\reports\model_factory\btc_eth_intraday_robustness_repair_alternate_child_packet_latest.json",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        alternate = summary["btc_eth_intraday_robustness_repair_alternate_child"]
        self.assertEqual(alternate["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertTrue(alternate["ready_for_gatekeeper_review"])
        self.assertEqual(alternate["top_alternate_candidate_id"], "robustrepair_441")
        self.assertEqual(alternate["alternate_pass_child_count"], 11)
        self.assertEqual(
            alternate["exact_phrase_to_record"],
            "REVIEW_BTC_ETH_INTRADAY_ALTERNATE_REPAIR_CHILDREN_ONLY",
        )
        self.assertFalse(alternate["counts_as_paper_or_live_evidence"])
        self.assertFalse(alternate["order_submission_allowed_by_this_report"])
        self.assertFalse(alternate["real_orders_allowed_by_this_report"])
        self.assertIn("BTC/ETH Intraday Alternate Repair Children", rendered)
        self.assertIn("robustrepair_441", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("C:\\AI", rendered)

    def test_paper_smoke_packet_summary_is_public_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "paper_smoke_gatekeeper_review_packet": {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "review_ready": True,
                "blocker_count": 0,
                "recommended_gatekeeper_lane": "PAPER_SMOKE_REVIEW_READY",
                "evidence_summary": {
                    "paper_cycles_completed": 177,
                    "combined_non_flat_signal_count": 2,
                    "combined_executable_order_evidence_count": 2,
                    "extended_paper_ready": False,
                    "historical_replay_non_flat_excluded": 197,
                },
                "permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        packet = summary["paper_smoke_gatekeeper_review_packet"]
        self.assertEqual(packet["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertTrue(packet["review_ready"])
        self.assertEqual(packet["blocker_count"], 0)
        self.assertFalse(packet["extended_paper_ready"])
        self.assertFalse(packet["promotion_allowed_by_this_packet"])
        self.assertFalse(packet["live_allowed_by_this_packet"])
        self.assertFalse(packet["real_orders_allowed_by_this_packet"])
        self.assertIn("Paper-Smoke Gatekeeper Review Packet", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_paper_smoke_human_decision_draft_summary_is_public_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "paper_smoke_human_decision_draft": {
                "status": "DRAFT_READY",
                "candidate_profile": "small_account_growth_paper",
                "blocker_count": 0,
                "allowed_decisions": ["ACKNOWLEDGE_PAPER_SMOKE_REVIEW_ONLY", "REJECT", "DEFER"],
                "draft_path": r"C:\AI\reports\model_factory\paper_smoke_gatekeeper_decision_draft.json",
                "safety": {
                    "does_write_final_human_decision_file": False,
                    "does_acknowledge_only": True,
                    "does_enable_paper": False,
                    "does_enable_live": False,
                    "does_allow_broker_submit": False,
                    "does_allow_private_submit": False,
                    "does_allow_real_orders": False,
                    "does_change_capital": False,
                    "real_orders": 0,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        draft = summary["paper_smoke_human_decision_draft"]
        self.assertEqual(draft["status"], "DRAFT_READY")
        self.assertEqual(draft["candidate_profile"], "small_account_growth_paper")
        self.assertEqual(draft["blocker_count"], 0)
        self.assertTrue(draft["does_acknowledge_only"])
        self.assertFalse(draft["does_write_final_human_decision_file"])
        self.assertFalse(draft["does_enable_paper"])
        self.assertFalse(draft["does_enable_live"])
        self.assertFalse(draft["order_submission_allowed_by_this_draft"])
        self.assertFalse(draft["real_orders_allowed_by_this_draft"])
        self.assertEqual(draft["real_orders"], 0)
        self.assertIn("Paper-Smoke Human Decision Draft", rendered)
        self.assertNotIn("draft_path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_gatekeeper_pending_decision_board_summary_is_public_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "gatekeeper_pending_decision_board": {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "decision_count": 4,
                "ready_decision_count": 4,
                "blocked_decision_count": 0,
                "risk_guard_status": "PASS",
                "next_decision": {
                    "decision_id": "paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                },
                "items": [
                    {
                        "decision_id": "paper_smoke_review",
                        "decision_type": "gatekeeper_paper_smoke_review",
                        "candidate_id": "small_account_growth_paper",
                        "lane": "portfolio",
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "closed": False,
                        "recommended_decision": "REVIEW_PAPER_SMOKE_ONLY",
                        "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                        "review_only_effect": "Records evidence review only.",
                        "source_path": r"C:\AI\reports\model_factory\paper_smoke_gatekeeper_review_packet_latest.json",
                        "human_decision_path": r"C:\AI\reports\model_factory\decision.json",
                        "evidence_summary": {"paper_cycles_completed": 204},
                        "blockers": [],
                    }
                ],
                "board_permissions": {
                    "promotion_allowed_by_this_board": False,
                    "shadow_registration_allowed_by_this_board": False,
                    "live_allowed_by_this_board": False,
                    "broker_submit_allowed_by_this_board": False,
                    "real_orders_allowed_by_this_board": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        board = summary["gatekeeper_pending_decision_board"]
        self.assertEqual(board["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(board["ready_decision_count"], 4)
        self.assertEqual(board["next_decision_id"], "paper_smoke_review")
        self.assertFalse(board["promotion_allowed_by_this_board"])
        self.assertFalse(board["shadow_registration_allowed_by_this_board"])
        self.assertFalse(board["live_allowed_by_this_board"])
        self.assertFalse(board["order_submission_allowed_by_this_board"])
        self.assertFalse(board["real_orders_allowed_by_this_board"])
        self.assertFalse(board["items"][0]["closed"])
        self.assertEqual(board["items"][0]["exact_phrase_to_record"], "REVIEW_PAPER_SMOKE_ONLY")
        self.assertEqual(board["items"][0]["review_only_effect"], "Records evidence review only.")
        self.assertIn("Gatekeeper Pending Decision Board", rendered)
        self.assertIn("Gatekeeper Pending Decision Items", rendered)
        self.assertIn("REVIEW_PAPER_SMOKE_ONLY", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("human_decision_path", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_gatekeeper_pending_board_public_summary_includes_stale_decision_mismatch(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "gatekeeper_pending_decision_board": {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "decision_count": 1,
                "ready_decision_count": 1,
                "blocked_decision_count": 0,
                "risk_guard_status": "PASS",
                "next_decision": {
                    "decision_id": "bithumb_current_actionable_shadow_review",
                    "candidate_id": "current_candidate",
                },
                "items": [
                    {
                        "decision_id": "bithumb_current_actionable_shadow_review",
                        "decision_type": "shadow_registration_review",
                        "candidate_id": "current_candidate",
                        "recorded_candidate_id": "stale_candidate",
                        "decision_candidate_match": False,
                        "lane": "bithumb_1d",
                        "status": "INVALID_HUMAN_GATEKEEPER_DECISION",
                        "ready_for_human_review": True,
                        "recommended_decision": "DEFER_OR_APPROVE_SHADOW_REVIEW_ONLY",
                        "source_path": r"C:\AI\reports\model_factory\template.json",
                        "human_decision_path": r"C:\AI\reports\model_factory\decision.json",
                        "evidence_summary": {
                            "estimated_cagr": 0.94,
                            "runtime_limits": {
                                "broker_submit_allowed": False,
                                "private_submit_allowed": False,
                            },
                            "source_action_packet": r"C:\AI\reports\model_factory\packet.json",
                        },
                        "blockers": ["HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH"],
                    }
                ],
                "board_permissions": {
                    "promotion_allowed_by_this_board": False,
                    "shadow_registration_allowed_by_this_board": False,
                    "live_allowed_by_this_board": False,
                    "broker_submit_allowed_by_this_board": False,
                    "real_orders_allowed_by_this_board": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        item = summary["gatekeeper_pending_decision_board"]["items"][0]
        self.assertEqual(item["recorded_candidate_id"], "stale_candidate")
        self.assertFalse(item["decision_candidate_match"])
        self.assertIn("HUMAN_GATEKEEPER_DECISION_CANDIDATE_MISMATCH", item["blockers"])
        self.assertNotIn("runtime_limits", item["evidence_summary"])
        self.assertNotIn("source_action_packet", item["evidence_summary"])
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("human_decision_path", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_gatekeeper_review_phrase_packet_summary_is_public_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "gatekeeper_review_decision_phrase_packet": {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_for_human_gatekeeper_review": True,
                "ready_phrase_count": 6,
                "blocked_decision_count": 1,
                "next_phrase": {
                    "decision_id": "paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                    "source_path": r"C:\AI\reports\model_factory\paper_smoke_gatekeeper_review_packet_latest.json",
                },
                "ready_phrases": [
                    {
                        "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                        "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                        "lane": "bithumb_1d",
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                        "review_only_effect": "Records evidence review only.",
                        "source_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_family_parameter_repair_gatekeeper_packet_latest.json",
                        "blockers": [],
                    }
                ],
                "packet_permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        packet = summary["gatekeeper_review_decision_phrase_packet"]
        self.assertEqual(packet["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertTrue(packet["ready_for_human_gatekeeper_review"])
        self.assertEqual(packet["ready_phrase_count"], 6)
        self.assertEqual(packet["next_exact_phrase_to_record"], "REVIEW_PAPER_SMOKE_ONLY")
        self.assertEqual(
            packet["ready_phrases"][0]["exact_phrase_to_record"],
            "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
        )
        self.assertFalse(packet["promotion_allowed_by_this_packet"])
        self.assertFalse(packet["shadow_registration_allowed_by_this_packet"])
        self.assertFalse(packet["paper_enabled_by_this_packet"])
        self.assertFalse(packet["live_allowed_by_this_packet"])
        self.assertFalse(packet["order_submission_allowed_by_this_packet"])
        self.assertFalse(packet["real_orders_allowed_by_this_packet"])
        self.assertIn("Gatekeeper Review Decision Phrase Packet", rendered)
        self.assertIn("Gatekeeper Ready Review Phrases", rendered)
        self.assertIn("REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_gatekeeper_review_ready_phrases_flow_from_pipeline_dashboard_source(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "gatekeeper_review_decision_phrase_packet": {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_for_human_gatekeeper_review": True,
                "ready_phrase_count": 1,
                "blocked_decision_count": 0,
                "next_phrase": {"exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY"},
                "ready_phrases": [
                    {
                        "decision_id": "btc_eth_intraday_robustness_repair_review",
                        "candidate_id": "btc_eth_intraday_momentum_btc_4h_sweep001_robustrepair_445",
                        "lane": "btc_eth_intraday",
                        "status": "ROBUSTNESS_REPAIR_READY",
                        "exact_phrase_to_record": "REVIEW_BTC_ETH_INTRADAY_ROBUSTNESS_REPAIR_ONLY",
                        "review_only_effect": "Records evidence review only.",
                        "safe_evidence_summary": {
                            "best_cost_pass_count": 2,
                            "best_cost_total_return": 0.068,
                            "source_path": r"C:\AI\private\should_not_export.json",
                            "broker_submit_allowed_by_this_report": False,
                            "private_submit_allowed_by_this_report": False,
                        },
                        "human_decision_state": {
                            "expected_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                            "recorded_candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
                            "decision_candidate_match": False,
                            "source_path": r"C:\AI\private\should_not_export.json",
                        },
                        "human_decision_draft_status": "DRAFT_READY",
                        "human_decision_draft_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                        "blockers": [],
                    }
                ],
                "packet_permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        self.assertEqual(
            summary["gatekeeper_review_decision_phrase_packet"]["ready_phrases"][0]["exact_phrase_to_record"],
            "REVIEW_BTC_ETH_INTRADAY_ROBUSTNESS_REPAIR_ONLY",
        )
        state = summary["gatekeeper_review_decision_phrase_packet"]["ready_phrases"][0]["human_decision_state"]
        self.assertEqual(
            state["expected_candidate_id"],
            "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
        )
        self.assertEqual(
            state["recorded_candidate_id"],
            "bithumb_current_actionable_pola_1d_long_freeze001_sweep1354",
        )
        self.assertFalse(state["decision_candidate_match"])
        self.assertNotIn("source_path", state)
        evidence = summary["gatekeeper_review_decision_phrase_packet"]["ready_phrases"][0]["evidence_summary"]
        self.assertEqual(evidence["best_cost_pass_count"], 2)
        self.assertEqual(evidence["best_cost_total_return"], 0.068)
        self.assertNotIn("source_path", evidence)
        self.assertNotIn("broker_submit_allowed_by_this_report", evidence)
        self.assertNotIn("private_submit_allowed_by_this_report", evidence)
        self.assertEqual(
            summary["gatekeeper_review_decision_phrase_packet"]["ready_phrases"][0]["human_decision_draft_status"],
            "DRAFT_READY",
        )
        self.assertEqual(
            summary["gatekeeper_review_decision_phrase_packet"]["ready_phrases"][0][
                "human_decision_draft_candidate_id"
            ],
            "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
        )
        self.assertIn("Gatekeeper Ready Review Phrases", rendered)
        self.assertIn("REVIEW_BTC_ETH_INTRADAY_ROBUSTNESS_REPAIR_ONLY", rendered)
        self.assertIn("best_cost_pass_count", rendered)
        self.assertIn("draft=DRAFT_READY", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("broker_submit", rendered)

    def test_bithumb_family_parameter_repair_public_summary_is_numeric_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "gatekeeper_pending_decision_board": {
                "items": [
                    {
                        "decision_id": "bithumb_current_actionable_family_parameter_repair_review",
                        "candidate_id": "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355",
                        "lane": "bithumb_1d",
                        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                        "ready_for_human_review": True,
                        "exact_phrase_to_record": "REVIEW_FAMILY_PARAMETER_REPAIR_EVIDENCE_ONLY",
                        "review_only_effect": "Records evidence review only.",
                        "evidence_summary": {
                            "market": "KRW-POLA",
                            "timeframe": "1d",
                            "estimated_cagr": 1.0605,
                            "estimated_mdd": -0.2,
                            "source_trade_count": 17,
                            "oos_fold_count": 3,
                            "oos_pass_fold_count": 2,
                            "oos_total_trade_count": 17,
                            "robustness_status": "ROBUSTNESS_STRESS_PASS",
                            "robustness_case_count": 7,
                            "robustness_pass_count": 4,
                            "robustness_cost_pass_count": 2,
                            "repair_evaluated_trial_count": 10,
                            "repair_oos_pass_candidate_count": 3,
                            "repair_robustness_pass_candidate_count": 1,
                            "source_path": r"C:\AI\reports\model_factory\bithumb_current_actionable_family_parameter_repair_gatekeeper_packet_latest.json",
                            "broker_submit_allowed_by_this_packet": False,
                            "private_submit_allowed_by_this_packet": False,
                        },
                    }
                ]
            },
            "gatekeeper_review_decision_phrase_packet": {
                "packet_permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        repair = summary["bithumb_family_parameter_repair_review"]
        self.assertEqual(repair["candidate_id"], "bithumb_current_actionable_pola_1d_long_freeze001_sweep1355")
        self.assertEqual(repair["market"], "KRW-POLA")
        self.assertEqual(repair["oos_pass_fold_count"], 2)
        self.assertEqual(repair["oos_fold_count"], 3)
        self.assertEqual(repair["oos_total_trade_count"], 17)
        self.assertEqual(repair["robustness_pass_count"], 4)
        self.assertEqual(repair["robustness_case_count"], 7)
        self.assertEqual(repair["robustness_cost_pass_count"], 2)
        self.assertEqual(repair["repair_oos_pass_candidate_count"], 3)
        self.assertEqual(repair["repair_robustness_pass_candidate_count"], 1)
        self.assertFalse(repair["promotion_allowed_by_this_review"])
        self.assertFalse(repair["order_submission_allowed_by_this_review"])
        self.assertFalse(repair["real_orders_allowed_by_this_review"])
        self.assertIn("Bithumb Family Parameter Repair Review", rendered)
        self.assertIn("bithumb_current_actionable_pola_1d_long_freeze001_sweep1355", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_model_factory_queue_coverage_audit_public_summary_is_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-04T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "model_factory_queue_coverage_audit": {
                "status": "PASS",
                "summary": {
                    "ready_decision_count": 13,
                    "queue_item_count": 20,
                    "covered_ready_decision_count": 13,
                    "missing_ready_decision_count": 0,
                    "unsafe_queue_item_count": 0,
                    "unexpected_duplicate_source_decision_count": 0,
                },
                "missing_ready_decision_ids": [],
                "unsafe_queue_experiment_ids": [],
                "coverage_rows": [
                    {
                        "decision_id": "bithumb_non_orca_entry_source_rebuild_review",
                        "candidate_id": "entrysource_029",
                        "priority_score": 84,
                        "covered": True,
                        "queue_item_count": 1,
                        "queue_scopes": ["entry_source_rebuild_evidence_review_only_no_order_paths"],
                        "queue_experiment_ids": [
                            r"C:\AI\reports\model_factory\private_path_should_not_surface.json"
                        ],
                    }
                ],
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        audit = summary["model_factory_queue_coverage_audit"]
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["ready_decision_count"], 13)
        self.assertEqual(audit["covered_ready_decision_count"], 13)
        self.assertEqual(audit["missing_ready_decision_count"], 0)
        self.assertEqual(audit["unsafe_queue_item_count"], 0)
        self.assertFalse(audit["order_submission_allowed_by_this_report"])
        self.assertFalse(audit["real_orders_allowed_by_this_report"])
        self.assertIn("Model Factory Queue Coverage Audit", rendered)
        self.assertIn("entry_source_rebuild_evidence_review_only_no_order_paths", rendered)
        self.assertNotIn("private_path_should_not_surface", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_bithumb_orca_robustness_repair_public_summary_is_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "bithumb_orca_robustness_repair": {
                "status": "ORCA_ROBUSTNESS_REPAIR_ITERATE",
                "ready_for_gatekeeper_review": False,
                "base_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "market": "KRW-ORCA",
                "trial_count": 3888,
                "evaluated_robustness_count": 24,
                "oos_pass_candidate_count": 24,
                "robustness_pass_candidate_count": 0,
                "best_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_orcarepair_2392",
                "best_robustness_status": "ROBUSTNESS_STRESS_ITERATE",
                "promotion_allowed_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
                "path": r"C:\AI\reports\model_factory\bithumb_current_actionable_orca_robustness_repair_latest.json",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        repair = summary["bithumb_orca_robustness_repair"]
        self.assertEqual(repair["status"], "ORCA_ROBUSTNESS_REPAIR_ITERATE")
        self.assertEqual(repair["trial_count"], 3888)
        self.assertEqual(repair["evaluated_robustness_count"], 24)
        self.assertEqual(repair["oos_pass_candidate_count"], 24)
        self.assertEqual(repair["robustness_pass_candidate_count"], 0)
        self.assertFalse(repair["ready_for_gatekeeper_review"])
        self.assertFalse(repair["order_submission_allowed_by_this_report"])
        self.assertFalse(repair["real_orders_allowed_by_this_report"])
        self.assertIn("Bithumb ORCA Robustness Repair", rendered)
        self.assertIn("bithumb_current_actionable_orca_1d_long_freeze001_orcarepair_2392", rendered)
        self.assertNotIn("path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_bithumb_family_diversity_failure_public_summary_is_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-04T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "bithumb_family_diversity_failure_review": {
                "status": "FAMILY_DIVERSITY_FAILURE_REVIEW_READY",
                "ready_for_gatekeeper_review": True,
                "family_diversity_status": "FAMILY_DIVERSITY_ITERATE",
                "current_oos_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "current_oos_market": "KRW-ORCA",
                "evaluated_candidate_count": 2,
                "failure_candidate_count": 2,
                "dominant_failure_dimension": "enough_pass_folds",
                "failure_dimension_counts": {"enough_pass_folds": 2, "enough_positive_folds": 2},
                "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
                "counts_as_paper_or_live_evidence": False,
                "promotion_allowed_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
                "path": r"C:\AI\reports\model_factory\bithumb_current_actionable_family_diversity_failure_review_latest.json",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        failure = summary["bithumb_family_diversity_failure_review"]
        self.assertEqual(failure["status"], "FAMILY_DIVERSITY_FAILURE_REVIEW_READY")
        self.assertEqual(failure["failure_candidate_count"], 2)
        self.assertEqual(failure["dominant_failure_dimension"], "enough_pass_folds")
        self.assertEqual(failure["recommended_research_action"], "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE")
        self.assertFalse(failure["counts_as_paper_or_live_evidence"])
        self.assertFalse(failure["order_submission_allowed_by_this_report"])
        self.assertFalse(failure["real_orders_allowed_by_this_report"])
        self.assertNotIn("path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_bithumb_alternate_robustness_failure_public_summary_is_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-04T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "bithumb_alternate_robustness_failure_review": {
                "status": "BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_REVIEW_READY",
                "ready_for_gatekeeper_review": True,
                "candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "current_oos_candidate_id": "bithumb_current_actionable_orca_1d_long_freeze001_sweep1507",
                "alternate_robustness_status": "ALTERNATE_ROBUSTNESS_ITERATE",
                "candidate_result_count": 6,
                "evaluated_oos_pass_candidate_count": 6,
                "robustness_pass_candidate_count": 0,
                "best_alternate_candidate_id": None,
                "recommended_action": (
                    "STOP_TREATING_OOS_ALTERNATES_AS_GATEKEEPER_RELIEF_REQUIRE_ROBUSTNESS_OR_NEW_FAMILY"
                ),
                "oos_alternates_count_as_gatekeeper_relief": False,
                "counts_as_paper_or_live_evidence": False,
                "promotion_allowed_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
                "path": r"C:\AI\reports\model_factory\bithumb_current_actionable_alternate_robustness_failure_review_latest.json",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        failure = summary["bithumb_alternate_robustness_failure_review"]
        self.assertEqual(failure["status"], "BITHUMB_ALTERNATE_ROBUSTNESS_FAILURE_REVIEW_READY")
        self.assertEqual(failure["candidate_result_count"], 6)
        self.assertEqual(failure["evaluated_oos_pass_candidate_count"], 6)
        self.assertEqual(failure["robustness_pass_candidate_count"], 0)
        self.assertFalse(failure["oos_alternates_count_as_gatekeeper_relief"])
        self.assertFalse(failure["counts_as_paper_or_live_evidence"])
        self.assertFalse(failure["order_submission_allowed_by_this_report"])
        self.assertFalse(failure["real_orders_allowed_by_this_report"])
        self.assertIn("Bithumb Alternate Robustness Failure Review", rendered)
        self.assertIn("ALTERNATE_ROBUSTNESS_ITERATE", rendered)
        self.assertNotIn("path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_bithumb_non_orca_family_repair_spec_public_summary_is_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-04T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "bithumb_non_orca_family_pass_fold_repair_spec": {
                "status": "READY_FOR_RESEARCH_SPEC_REVIEW",
                "ready_for_research_spec_review": True,
                "experiment_id": "bithumb_non_orca_family_pass_fold_repair__orca",
                "dominant_failure_dimension": "enough_pass_folds",
                "recommended_research_action": "REPAIR_NON_ORCA_PASS_FOLD_COVERAGE",
                "repair_target_count": 2,
                "counts_as_paper_or_live_evidence": False,
                "promotion_allowed_by_this_report": False,
                "live_allowed_by_this_report": False,
                "broker_submit_allowed_by_this_report": False,
                "private_submit_allowed_by_this_report": False,
                "real_orders_allowed_by_this_report": False,
                "path": r"C:\AI\reports\model_factory\bithumb_non_orca_family_pass_fold_repair_spec_latest.json",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        repair_spec = summary["bithumb_non_orca_family_pass_fold_repair_spec"]
        self.assertEqual(repair_spec["status"], "READY_FOR_RESEARCH_SPEC_REVIEW")
        self.assertEqual(repair_spec["repair_target_count"], 2)
        self.assertFalse(repair_spec["counts_as_paper_or_live_evidence"])
        self.assertFalse(repair_spec["order_submission_allowed_by_this_report"])
        self.assertFalse(repair_spec["real_orders_allowed_by_this_report"])
        self.assertNotIn("path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_gatekeeper_review_phrase_packet_derives_ready_boolean_when_source_omits_it(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "gatekeeper_review_decision_phrase_packet": {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_phrase_count": 1,
                "blocked_decision_count": 0,
                "next_phrase": {
                    "decision_id": "paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                },
                "board_permissions": {
                    "promotion_allowed_by_this_packet": False,
                    "shadow_registration_allowed_by_this_packet": False,
                    "paper_enabled_by_this_packet": False,
                    "live_allowed_by_this_packet": False,
                    "broker_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
            finally:
                public_export.DASHBOARD_JSON = original

        self.assertTrue(summary["gatekeeper_review_decision_phrase_packet"]["ready_for_human_gatekeeper_review"])

    def test_gatekeeper_decision_priority_is_public_and_sanitized(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "gatekeeper_decision_priority": {
                "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW",
                "ready_decision_count": 7,
                "blocked_decision_count": 1,
                "next_decision": {
                    "decision_id": "paper_smoke_review",
                    "candidate_id": "small_account_growth_paper",
                    "priority_score": 100,
                    "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                },
                "ready_decisions": [
                    {
                        "decision_id": "paper_smoke_review",
                        "candidate_id": "small_account_growth_paper",
                        "lane": "portfolio",
                        "status": "READY_FOR_GATEKEEPER_REVIEW",
                        "priority_score": 100,
                        "priority_reason": "Current promotion-gate evidence review.",
                        "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
                        "review_only_effect": "Records evidence review only.",
                        "evidence_summary": {
                            "paper_cycles_completed": 252,
                            "source_path": r"C:\AI\reports\private.json",
                            "broker_submit_allowed_by_this_report": False,
                            "private_submit_allowed_by_this_report": False,
                        },
                        "blockers": [],
                    }
                ],
                "permissions": {
                    "promotion_allowed_by_this_report": False,
                    "shadow_registration_allowed_by_this_report": False,
                    "paper_enabled_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        priority = summary["gatekeeper_decision_priority"]
        self.assertEqual(priority["status"], "READY_FOR_HUMAN_GATEKEEPER_REVIEW")
        self.assertEqual(priority["next_decision_id"], "paper_smoke_review")
        self.assertEqual(priority["next_priority_score"], 100)
        self.assertFalse(priority["live_allowed_by_this_report"])
        self.assertFalse(priority["order_submission_allowed_by_this_report"])
        self.assertEqual(priority["ready_decisions"][0]["evidence_summary"]["paper_cycles_completed"], 252)
        self.assertNotIn("source_path", priority["ready_decisions"][0]["evidence_summary"])
        self.assertNotIn("broker_submit_allowed_by_this_report", priority["ready_decisions"][0]["evidence_summary"])
        self.assertIn("Gatekeeper Decision Priority", rendered)
        self.assertIn("REVIEW_PAPER_SMOKE_ONLY", rendered)
        self.assertNotIn("source_path", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_kis_environment_and_live_preflight_summary_are_public_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "kis_environment_readiness": {
                "status": "BLOCKED",
                "missing_requirements": ["app_key", "app_secret", "account_no", "account_product_code"],
                "secret_values_inspected": False,
                "secret_values_written": False,
                "safety": {
                    "does_call_kis_api": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
            "kis_environment_operator_handoff": {
                "status": "WAITING_FOR_OPERATOR_ENV_VALUES",
                "missing_requirements": ["app_key", "app_secret"],
                "operator_setup_template": "C:\\AI\\reports\\live_readiness\\kis_environment_operator_setup_template.ps1",
                "preferred_env_names": {"app_key": "KIS_APP_KEY", "app_secret": "KIS_APP_SECRET"},
                "powershell_setup_placeholders": ["$env:KIS_APP_KEY = '<KIS_APP_KEY>'"],
                "verification_commands_after_operator_sets_values": [
                    "python .\\build_kis_environment_readiness_report.py",
                    "python .\\build_stock_live_preflight_packet.py",
                ],
                "safety": {
                    "secret_values_included": False,
                    "secret_values_inspected": False,
                    "secret_values_written": False,
                    "does_set_environment": False,
                    "does_call_kis_api": False,
                    "does_enable_live": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                    "real_orders": 0,
                },
            },
            "goal_unblock_verification_packet": {
                "status": "WAITING_FOR_BLOCKER_CLEARANCE",
                "blocker_count": 2,
                "blocker_deliverables": ["current_paper_activation_gate", "two_axis_model_factory_scope"],
                "unblock_summary": {
                    "kis_missing_requirements": ["app_key", "app_secret"],
                    "kis_local_coverage_ready": True,
                    "kis_api_environment_ready": False,
                    "paper_cycles_completed": 252,
                    "paper_cycles_target": 288,
                    "paper_cycles_missing": 36,
                    "non_flat_signal_count": 54,
                    "non_flat_signal_target": 5,
                    "executable_order_count": 54,
                    "executable_order_target": 5,
                    "promotion_review_ready": False,
                    "historical_replay_counts_as_promotion_evidence": False,
                    "paper_cycle_source": {
                        "source": r"C:\AI\overnight_runs\paper_autotrade_loop_latest.json",
                        "cycle_source": "paper_autotrade_loop_latest.cycles_completed",
                        "paper_loop_cycles_completed": 252,
                        "paper_loop_last_status": "ok",
                        "paper_loop_activate": False,
                        "paper_loop_cycles_requested": 1,
                        "progress_delta_cycles": 0,
                        "gatekeeper_refresh_does_not_increment_this_counter": True,
                        "requires_explicit_paper_activation_for_new_active_cycles": True,
                    },
                },
                "recheck_readiness": {
                    "status": "WAITING_FOR_BLOCKER_CLEARANCE",
                    "ready_recheck_lanes": [],
                    "kis_recheck_ready": False,
                    "paper_recheck_ready": False,
                },
                "verification_steps": [
                    {
                        "blocker": "two_axis_model_factory_scope",
                        "operator_input_required": True,
                        "commands": ["python .\\build_kis_environment_readiness_report.py"],
                        "expected_pass_conditions": {"kis_environment_readiness_status": "READY"},
                        "current_status": {"kis_handoff_status": "WAITING_FOR_OPERATOR_ENV_VALUES"},
                    },
                    {
                        "blocker": "current_paper_activation_gate",
                        "operator_input_required": False,
                        "commands": ["python .\\build_paper_promotion_evidence_report.py"],
                        "expected_pass_conditions": {"paper_cycles_completed_min": 288},
                        "current_status": {
                            "paper_cycles_completed": 252,
                            "paper_cycles_target": 288,
                            "paper_cycle_source": {
                                "source": r"C:\AI\overnight_runs\paper_autotrade_loop_latest.json",
                                "cycle_source": "paper_autotrade_loop_latest.cycles_completed",
                                "paper_loop_cycles_completed": 252,
                                "gatekeeper_refresh_does_not_increment_this_counter": True,
                            },
                        },
                    }
                ],
                "completion_recheck_commands": [
                    "python .\\build_goal_model_factory_requirement_checklist.py"
                ],
                "safety": {
                    "broker_submit_allowed_by_this_packet": False,
                    "private_submit_allowed_by_this_packet": False,
                    "real_orders_allowed_by_this_packet": False,
                },
            },
            "pipeline_live_preflight_reconfiguration": {
                "status": "RECONFIGURED_WITH_BLOCKERS",
                "current_blockers": {
                    "crypto": ["CURRENT_CRYPTO_SIGNAL_HAS_NO_NONZERO_ORDER"],
                    "kis_environment": ["app_key", "app_secret"],
                    "stock": ["KIS_ENV_MISSING"],
                },
                "safety": {"live_enabled": False, "real_orders": 0},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        kis = summary["kis_environment_readiness"]
        live = summary["pipeline_live_preflight_reconfiguration"]
        self.assertEqual(kis["status"], "BLOCKED")
        self.assertEqual(kis["missing_requirements"], ["app_key", "app_secret", "account_no", "account_product_code"])
        self.assertFalse(kis["secret_values_inspected"])
        self.assertFalse(kis["secret_values_written"])
        self.assertFalse(kis["does_call_kis_api"])
        self.assertFalse(kis["real_orders_allowed_by_this_report"])
        handoff = summary["kis_environment_operator_handoff"]
        self.assertEqual(handoff["status"], "WAITING_FOR_OPERATOR_ENV_VALUES")
        self.assertEqual(handoff["missing_requirements"], ["app_key", "app_secret"])
        self.assertEqual(handoff["operator_setup_template"], "kis_environment_operator_setup_template.ps1")
        self.assertFalse(handoff["secret_values_included"])
        self.assertFalse(handoff["secret_values_inspected"])
        self.assertFalse(handoff["secret_values_written"])
        self.assertFalse(handoff["does_set_environment"])
        self.assertFalse(handoff["does_call_kis_api"])
        self.assertFalse(handoff["does_enable_live"])
        self.assertFalse(handoff["order_submission_allowed_by_this_report"])
        self.assertFalse(handoff["real_orders_allowed_by_this_report"])
        self.assertEqual(handoff["real_orders"], 0)
        unblock = summary["goal_unblock_verification_packet"]
        self.assertEqual(unblock["status"], "WAITING_FOR_BLOCKER_CLEARANCE")
        self.assertEqual(unblock["blocker_count"], 2)
        self.assertEqual(unblock["unblock_summary"]["paper_cycles_missing"], 36)
        self.assertEqual(unblock["unblock_summary"]["non_flat_signal_count"], 54)
        self.assertFalse(unblock["unblock_summary"]["historical_replay_counts_as_promotion_evidence"])
        self.assertEqual(unblock["recheck_readiness"]["status"], "WAITING_FOR_BLOCKER_CLEARANCE")
        self.assertFalse(unblock["recheck_readiness"]["kis_recheck_ready"])
        self.assertFalse(unblock["recheck_readiness"]["paper_recheck_ready"])
        self.assertEqual(unblock["verification_steps"][0]["blocker"], "two_axis_model_factory_scope")
        self.assertEqual(
            unblock["unblock_summary"]["paper_cycle_source"]["cycle_source"],
            "paper_autotrade_loop_latest.cycles_completed",
        )
        self.assertNotIn("source", unblock["unblock_summary"]["paper_cycle_source"])
        self.assertEqual(
            unblock["verification_steps"][1]["current_status"]["paper_cycle_source"]["cycle_source"],
            "paper_autotrade_loop_latest.cycles_completed",
        )
        self.assertNotIn("source", unblock["verification_steps"][1]["current_status"]["paper_cycle_source"])
        self.assertEqual(live["status"], "RECONFIGURED_WITH_BLOCKERS")
        self.assertEqual(live["kis_environment_blockers"], ["app_key", "app_secret"])
        self.assertFalse(live["live_enabled"])
        self.assertEqual(live["real_orders"], 0)
        self.assertIn("KIS Environment Readiness", rendered)
        self.assertIn("KIS Environment Operator Handoff", rendered)
        self.assertIn("kis_environment_operator_setup_template.ps1", rendered)
        self.assertIn("Goal Unblock Verification Packet", rendered)
        self.assertIn("Goal Unblock Verification Steps", rendered)
        self.assertIn("WAITING_FOR_BLOCKER_CLEARANCE", rendered)
        self.assertIn("252/288", rendered)
        self.assertIn("54/5", rendered)
        self.assertIn("Pipeline Live Preflight Reconfiguration", rendered)
        self.assertNotIn("powershell_setup_placeholders", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_crypto_nonzero_order_readiness_summary_is_public_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "crypto_nonzero_order_readiness": {
                "status": "BLOCKED",
                "blockers": [
                    "CURRENT_CRYPTO_ACTION_NOT_BUY_OR_SELL",
                    "CURRENT_CRYPTO_TARGET_WEIGHT_ZERO",
                    "CURRENT_CRYPTO_DELTA_WEIGHT_ZERO",
                ],
                "selected_sleeve": {"candidate_id": "bridge_28_relief"},
                "current_order_candidate": {
                    "action": "HOLD",
                    "target_weight": 0.0,
                    "delta_weight": 0.0,
                    "has_nonzero_order": False,
                },
                "safety": {
                    "does_call_bithumb_api": False,
                    "broker_submit_allowed_by_this_report": False,
                    "private_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        crypto = summary["crypto_nonzero_order_readiness"]
        self.assertEqual(crypto["status"], "BLOCKED")
        self.assertEqual(crypto["selected_candidate"], "bridge_28_relief")
        self.assertEqual(crypto["action"], "HOLD")
        self.assertFalse(crypto["has_nonzero_order"])
        self.assertFalse(crypto["does_call_bithumb_api"])
        self.assertFalse(crypto["real_orders_allowed_by_this_report"])
        self.assertIn("CURRENT_CRYPTO_TARGET_WEIGHT_ZERO", crypto["blockers"])
        self.assertIn("Crypto Nonzero Order Readiness", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_event_stall_triage_summary_is_public_and_safe(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "paper_event_stall_triage": {
                "status": "READY_FOR_STALL_REVIEW",
                "review_ready": True,
                "blocker_count": 0,
                "stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WARN_STALL",
                    "slowest_gate_dimension": "non_flat_signals",
                },
                "evidence_gap_summary": {
                    "non_flat_signals_missing": 3,
                    "executable_orders_missing": 3,
                },
                "replay_policy": {
                    "historical_replay_non_flat_count": 197,
                    "counts_as_extended_paper_promotion": False,
                    "counts_as_live_readiness": False,
                },
                "permissions": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        triage = summary["paper_event_stall_triage"]
        self.assertEqual(triage["status"], "READY_FOR_STALL_REVIEW")
        self.assertTrue(triage["review_ready"])
        self.assertEqual(triage["blocker_count"], 0)
        self.assertFalse(triage["counts_as_extended_paper_promotion"])
        self.assertFalse(triage["counts_as_live_readiness"])
        self.assertFalse(triage["promotion_allowed_by_this_report"])
        self.assertFalse(triage["live_allowed_by_this_report"])
        self.assertFalse(triage["order_submission_allowed_by_this_report"])
        self.assertFalse(triage["real_orders_allowed_by_this_report"])
        self.assertIn("Paper Evidence Event Stall Triage", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_velocity_monitor_summary_keeps_paper_evidence_gaps_public(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
                "paper_velocity_monitor": {
                    "status": "COLLECT_EVIDENCE",
                    "readiness_summary": {
                        "paper_evidence_readiness_percent": 40.0,
                        "dominant_blocking_dimensions": ["non_flat_signals", "executable_orders"],
                    },
                    "gap_summary": {
                        "paper_cycles_missing": 143,
                        "non_flat_signals_missing": 3,
                        "executable_orders_missing": 3,
                },
                "velocity_proximity_summary": {
                    "live_like_target_count": 8,
                    "already_non_flat_target_count": 2,
                    "nearest_flat_target": {
                        "market": "KRW-ETH",
                        "timeframe": "1h",
                        "non_flat_trigger_gap": 0.0015,
                        "broker_submit_allowed": False,
                    },
                },
                "safety": {
                    "historical_replay_excluded": True,
                    "broker_submit_allowed": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        monitor = summary["paper_velocity_monitor"]
        self.assertEqual(monitor["status"], "COLLECT_EVIDENCE")
        self.assertEqual(monitor["paper_evidence_readiness_percent"], 40.0)
        self.assertEqual(monitor["dominant_blocking_dimensions"], ["non_flat_signals", "executable_orders"])
        self.assertEqual(monitor["paper_cycles_missing"], 143)
        self.assertEqual(monitor["non_flat_signals_missing"], 3)
        self.assertEqual(monitor["executable_orders_missing"], 3)
        self.assertEqual(monitor["live_like_target_count"], 8)
        self.assertEqual(monitor["already_non_flat_target_count"], 2)
        self.assertEqual(monitor["nearest_flat_target_market"], "KRW-ETH")
        self.assertEqual(monitor["nearest_flat_target_timeframe"], "1h")
        self.assertEqual(monitor["nearest_flat_trigger_gap"], 0.0015)
        self.assertFalse(monitor["nearest_flat_order_submission_allowed"])
        self.assertTrue(monitor["historical_replay_excluded"])
        self.assertIn("live-like target count", rendered)
        self.assertIn("already non-flat target count", rendered)
        self.assertIn("KRW-ETH 1h", rendered)
        self.assertIn("0.0015", rendered)
        self.assertIn("nearest flat order submission allowed", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_operational_warnings_are_exported_without_sensitive_fields(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "operator_summary": {
                "operational_status": "WARN",
                "blocker_count": 0,
                "warning_count": 2,
                "expected_collect_evidence_warning_count": 2,
                "actionable_warning_count": 0,
                "warnings": [
                    "NON_PASS_STATUS:paper_promotion_evidence:KEEP_PAPER_COLLECT_EVIDENCE",
                    "NON_PASS_STATUS:capital_allocator_decision:KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE",
                ],
                "expected_collect_evidence_warnings": [
                    "NON_PASS_STATUS:paper_promotion_evidence:KEEP_PAPER_COLLECT_EVIDENCE",
                    "NON_PASS_STATUS:capital_allocator_decision:KEEP_CURRENT_PAPER_CAP_COLLECT_EVIDENCE",
                ],
                "actionable_warnings": [],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        self.assertEqual(len(summary["operational_warnings"]), 2)
        self.assertEqual(summary["operational_warning_summary"]["actionable_warning_count"], 0)
        self.assertEqual(summary["operational_warning_summary"]["expected_collect_evidence_warning_count"], 2)
        self.assertEqual(summary["operational_actionable_warnings"], [])
        self.assertEqual(len(summary["operational_expected_collect_evidence_warnings"]), 2)
        self.assertIn("KEEP_PAPER_COLLECT_EVIDENCE", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("CommandLine", rendered)

    def test_stock_risk_conversion_queue_summary_is_public_and_no_order(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "stock_risk_conversion_queue": {
                "status": "READY_FOR_GATEKEEPER_REVIEW",
                "target_count": 5,
                "ready_candidate_count": 5,
                "blocked_candidate_count": 0,
                "top_candidate": {
                    "candidate_id": "stock_aggressive__trim22",
                    "lane": "kis_etfs",
                    "before": {"cagr": 0.706, "mdd": -0.306},
                    "proposed_conversion": {
                        "fixed_exposure_cap": 0.65,
                        "estimated_cagr": 0.459,
                        "estimated_mdd": -0.199,
                    },
                },
                "no_order_assertions": {
                    "promotion_allowed_by_this_report": False,
                    "live_allowed_by_this_report": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders_allowed_by_this_report": False,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        queue = summary["stock_risk_conversion_queue"]
        self.assertEqual(queue["status"], "READY_FOR_GATEKEEPER_REVIEW")
        self.assertEqual(queue["target_count"], 5)
        self.assertEqual(queue["ready_candidate_count"], 5)
        self.assertEqual(queue["top_candidate_id"], "stock_aggressive__trim22")
        self.assertFalse(queue["promotion_allowed_by_this_report"])
        self.assertFalse(queue["order_submission_allowed_by_this_report"])
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_completion_audit_summary_exports_not_complete_reason(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "goal_completion_audit": {
                "status": "NOT_COMPLETE",
                "completion_allowed": False,
                "pass_count": 7,
                "total_count": 9,
                "incomplete_count": 1,
                "missing_or_incomplete": [
                    {
                        "requirement": "Accumulate enough live-like paper promotion evidence",
                        "status": "INCOMPLETE",
                    }
                ],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        audit = summary["goal_completion_audit"]
        self.assertEqual(audit["status"], "NOT_COMPLETE")
        self.assertFalse(audit["completion_allowed"])
        self.assertEqual(audit["pass_count"], 7)
        self.assertEqual(audit["total_count"], 9)
        self.assertEqual(audit["first_incomplete_requirement"], "Accumulate enough live-like paper promotion evidence")
        self.assertIn("7/9", rendered)
        self.assertIn("NOT_COMPLETE", rendered)

    def test_requirement_checklist_summary_exports_goal_requirement_status(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "goal_requirement_checklist": {
                "status": "NOT_COMPLETE",
                "completion_allowed": False,
                "pass_count": 5,
                "total_count": 6,
                "incomplete_count": 1,
                "unexpected_incomplete_count": 0,
                "unexpected_incomplete_requirements": [],
                "first_incomplete_requirement": "Accumulate enough live-like paper promotion evidence before completion",
                "items": [
                    {
                        "requirement": "Keep a file-backed progress record for each iteration",
                        "status": "PASS",
                        "evidence": {
                            "progress_entry_count": 155,
                            "latest_iteration_number": 131,
                            "latest_iteration_heading": "## 2026-05-04 Iteration 131 Result",
                            "open_iteration_count": 0,
                        },
                    }
                ],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        checklist = summary["goal_requirement_checklist"]
        self.assertEqual(checklist["status"], "NOT_COMPLETE")
        self.assertFalse(checklist["completion_allowed"])
        self.assertEqual(checklist["pass_count"], 5)
        self.assertEqual(checklist["total_count"], 6)
        self.assertEqual(checklist["unexpected_incomplete_count"], 0)
        self.assertEqual(checklist["first_incomplete_requirement"], "Accumulate enough live-like paper promotion evidence before completion")
        self.assertEqual(checklist["progress"]["progress_entry_count"], 155)
        self.assertEqual(checklist["progress"]["latest_iteration_number"], 131)
        self.assertEqual(checklist["progress"]["open_iteration_count"], 0)
        self.assertIn("Goal Requirement Checklist", rendered)
        self.assertIn("latest progress iteration", rendered)
        self.assertNotIn("C:\\AI", rendered)

    def test_remaining_blockers_public_summary_includes_paper_cycle_source(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "goal_remaining_blockers": {
                "status": "BLOCKED",
                "blocker_count": 1,
                "codex_unblockable_now_count": 0,
                "approval_required_count": 1,
                "operator_input_blocker_count": 1,
                "blockers": [
                    {
                        "deliverable": "current_paper_activation_gate",
                        "blocker_type": "paper_cycle_evidence",
                        "status": "KEEP_PAPER_COLLECT_EVIDENCE",
                        "codex_can_unblock_without_operator": False,
                        "approval_required_before_codex_action": True,
                        "required_operator_action": (
                            "Either wait for already-approved paper-cycle evidence to advance, or provide approval."
                        ),
                        "required_approval_phrase": "PAPER APPROVE small_account_growth_paper",
                        "unblock_condition": "Collect enough live-like paper cycles.",
                        "codex_safe_next_action": (
                            "Keep reporting and monitoring only; do not run paper activation cycles without approval."
                        ),
                        "paper_cycle_source": {
                            "source": r"C:\AI\overnight_runs\paper_autotrade_loop_latest.json",
                            "cycle_source": "paper_autotrade_loop_latest.cycles_completed",
                            "paper_loop_cycles_completed": 252,
                            "progress_delta_cycles": 0,
                            "gatekeeper_refresh_does_not_increment_this_counter": True,
                            "requires_explicit_paper_activation_for_new_active_cycles": True,
                        },
                    }
                ],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        blocker = summary["goal_remaining_blockers"]["blockers"][0]
        self.assertEqual(summary["goal_remaining_blockers"]["codex_unblockable_now_count"], 0)
        self.assertEqual(summary["goal_remaining_blockers"]["approval_required_count"], 1)
        self.assertEqual(summary["goal_remaining_blockers"]["operator_input_blocker_count"], 1)
        self.assertEqual(blocker["paper_cycle_source"]["cycle_source"], "paper_autotrade_loop_latest.cycles_completed")
        self.assertFalse(blocker["codex_can_unblock_without_operator"])
        self.assertTrue(blocker["approval_required_before_codex_action"])
        self.assertIn("already-approved paper-cycle evidence", blocker["required_operator_action"])
        self.assertNotIn("required_approval_phrase", blocker)
        self.assertEqual(blocker["paper_cycle_source"]["paper_loop_cycles_completed"], 252)
        self.assertTrue(blocker["paper_cycle_source"]["gatekeeper_refresh_does_not_increment_this_counter"])
        self.assertTrue(blocker["paper_cycle_source"]["requires_explicit_paper_activation_for_new_active_cycles"])
        self.assertIn("paper_autotrade_loop_latest.cycles_completed", rendered)
        self.assertIn("Codex can unblock now", rendered)
        self.assertIn("approval required", rendered)
        self.assertIn("already-approved paper-cycle evidence", rendered)
        self.assertNotIn("PAPER APPROVE small_account_growth_paper", rendered)
        self.assertIn("refresh does not increment source", rendered)
        self.assertNotIn("refresh increments source", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_paper_evidence_acceleration_summary_is_public_and_sanitized(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "paper_acceleration_summary": {
                "multi_asset_market_count": 406,
                "intraday_signal_count": 4,
                "eligible_live_paper_signal_count": 410,
                "eligible_non_flat_signal_count": 53,
                "virtual_executable_order_count": 53,
                "new_signal_count_this_run": 0,
                "seen_signal_count": 725,
                "source": r"C:\AI\ops\reports\paper_evidence_acceleration_latest.json",
                "broker_submit_allowed": False,
                "private_submit_used": False,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        acceleration = summary["paper_evidence_acceleration"]
        self.assertEqual(acceleration["multi_asset_market_count"], 406)
        self.assertEqual(acceleration["eligible_non_flat_signal_count"], 53)
        self.assertEqual(acceleration["virtual_executable_order_count"], 53)
        self.assertEqual(acceleration["seen_signal_count"], 725)
        self.assertIn("Paper Evidence Acceleration", rendered)
        self.assertIn("eligible live-paper signals", rendered)
        self.assertNotIn("C:\\AI", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_progress_delta_summary_exports_paper_velocity_fields(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "paper_progress_delta": {
                "status": "COLLECT_EVIDENCE",
                "current": {
                    "paper_cycles_completed": 147,
                    "paper_cycles_target": 288,
                },
                "delta_from_previous": {
                    "paper_cycles_delta": 2,
                    "non_flat_delta": 1,
                    "executable_delta": 1,
                },
                "pace_summary": {
                    "eta_status": "STALLED_ON_EVENT_EVIDENCE",
                    "slowest_gate_dimension": "non_flat_signals",
                    "estimated_hours_to_cycle_target": 9.85,
                    "promotion_review_eta_hours": None,
                },
                "event_stall_summary": {
                    "event_stall_status": "EVENT_EVIDENCE_STALLED",
                    "stall_severity": "WARN_STALL",
                    "safe_next_action": "Continue safe paper loop, but monitor nearest flat target and stall age closely.",
                    "non_flat_signals": {
                        "hours_since_last_increase": 1.95,
                        "paper_cycles_since_last_increase": 24,
                    },
                    "executable_orders": {
                        "hours_since_last_increase": 1.95,
                        "paper_cycles_since_last_increase": 24,
                    },
                },
                "history_count": 3,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        progress = summary["paper_progress_delta"]
        self.assertEqual(progress["status"], "COLLECT_EVIDENCE")
        self.assertEqual(progress["paper_cycles_completed"], 147)
        self.assertEqual(progress["paper_cycles_target"], 288)
        self.assertEqual(progress["paper_cycles_delta"], 2)
        self.assertEqual(progress["non_flat_delta"], 1)
        self.assertEqual(progress["executable_delta"], 1)
        self.assertEqual(progress["pace_eta_status"], "STALLED_ON_EVENT_EVIDENCE")
        self.assertEqual(progress["slowest_gate_dimension"], "non_flat_signals")
        self.assertEqual(progress["estimated_hours_to_cycle_target"], 9.85)
        self.assertIsNone(progress["promotion_review_eta_hours"])
        self.assertEqual(progress["event_stall_status"], "EVENT_EVIDENCE_STALLED")
        self.assertEqual(progress["stall_severity"], "WARN_STALL")
        self.assertIn("monitor nearest flat target", progress["stall_safe_next_action"])
        self.assertEqual(progress["non_flat_hours_since_last_increase"], 1.95)
        self.assertEqual(progress["executable_hours_since_last_increase"], 1.95)
        self.assertEqual(progress["non_flat_paper_cycles_since_last_increase"], 24)
        self.assertEqual(progress["history_count"], 3)
        self.assertIn("Paper Evidence Progress Delta", rendered)
        self.assertIn("slowest gate dimension", rendered)
        self.assertIn("non_flat_signals", rendered)
        self.assertIn("event stall status", rendered)
        self.assertIn("EVENT_EVIDENCE_STALLED", rendered)
        self.assertIn("stall severity", rendered)
        self.assertIn("WARN_STALL", rendered)
        self.assertNotIn("broker_submit", rendered)
        self.assertNotIn("private_submit", rendered)

    def test_review_stack_refresh_status_is_public(self) -> None:
        source = {
            "generated_at_utc": "2026-05-03T00:00:00+00:00",
            "performance_summary": {},
            "paper_evidence": {},
            "top_axis_models": {},
            "safety": {"live_enabled": False, "real_orders": 0},
            "paper_review_stack_refresh": {
                "status": "PASS",
                "paper_progress": {
                    "paper_cycles_completed": 149,
                    "paper_cycles_target": 288,
                    "paper_cycles_missing": 139,
                },
                "completion_audit": {"status": "NOT_COMPLETE"},
                "goal_requirement_checklist": {
                    "unexpected_incomplete_count": 0,
                    "unexpected_incomplete_requirements": [],
                },
                "realtime_risk_guard": {"status": "PASS"},
                "public_export_checks": {
                    "goal_requirement_checklist_status": "NOT_COMPLETE",
                    "goal_requirement_checklist_surface_present": True,
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_json = Path(tmp) / "dashboard.json"
            dashboard_json.write_text(json.dumps(source), encoding="utf-8")
            original = public_export.DASHBOARD_JSON
            public_export.DASHBOARD_JSON = dashboard_json
            try:
                summary = public_export.build_public_summary()
                rendered = json.dumps(summary, ensure_ascii=False) + public_export.render_html(summary)
            finally:
                public_export.DASHBOARD_JSON = original

        refresh = summary["paper_review_stack_refresh"]
        self.assertEqual(refresh["status"], "PASS")
        self.assertEqual(refresh["paper_cycles_completed"], 149)
        self.assertEqual(refresh["completion_audit_status"], "NOT_COMPLETE")
        self.assertEqual(refresh["unexpected_checklist_incomplete_count"], 0)
        self.assertEqual(refresh["unexpected_checklist_incomplete_requirements"], [])
        self.assertEqual(refresh["risk_guard_status"], "PASS")
        self.assertEqual(refresh["public_requirement_checklist_status"], "NOT_COMPLETE")
        self.assertTrue(refresh["public_requirement_checklist_surface_present"])
        self.assertIn("Paper Evidence Review Stack Refresh", rendered)


if __name__ == "__main__":
    unittest.main()
