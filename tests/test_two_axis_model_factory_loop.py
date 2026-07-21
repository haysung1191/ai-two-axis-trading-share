from __future__ import annotations

import json
import subprocess
from pathlib import Path

import run_two_axis_model_factory_loop as loop


def test_run_step_timeout_records_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loop, "RUNNING_JSON", tmp_path / "running.json")

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=kwargs.get("args", ["x"]), timeout=1)

    monkeypatch.setattr(loop.subprocess, "run", fake_run)
    result = loop.run_step(
        "slow step",
        ["python", "slow.py"],
        tmp_path,
        timeout_seconds=1,
        cycle_started_at_utc="2026-05-17T00:00:00+00:00",
        step_index=1,
        step_count=1,
    )

    assert not result["ok"]
    assert result["timed_out"]
    assert result["timeout_seconds"] == 1
    running = json.loads((tmp_path / "running.json").read_text(encoding="utf-8"))
    assert running["status"] == "TWO_AXIS_MODEL_FACTORY_RUNNING"
    assert running["current_step"] == "slow step"


def test_run_step_forces_utf8_child_output(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loop, "RUNNING_JSON", tmp_path / "running.json")
    captured = {}

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(args=kwargs.get("args", ["x"]), returncode=0, stdout="재영솔루텍\n", stderr="")

    monkeypatch.setattr(loop.subprocess, "run", fake_run)
    monkeypatch.setattr(loop, "step_env", lambda: {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})

    result = loop.run_step(
        "utf8 step",
        ["python", "utf8.py"],
        tmp_path,
        timeout_seconds=60,
        cycle_started_at_utc="2026-05-17T00:00:00+00:00",
        step_index=1,
        step_count=1,
    )

    assert result["ok"]
    assert result["stdout_tail"] == "재영솔루텍\n"
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"
    assert captured["env"]["PYTHONUTF8"] == "1"
    assert captured["env"]["PYTHONIOENCODING"] == "utf-8"


def test_run_step_can_skip_running_status_update_for_one_shot(monkeypatch, tmp_path: Path) -> None:
    running = tmp_path / "running.json"
    running.write_text('{"status":"KEEP","next_cycle_due_at_utc":"2026-05-18T19:30:00+00:00"}', encoding="utf-8")
    monkeypatch.setattr(loop, "RUNNING_JSON", running)

    monkeypatch.setattr(
        loop.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=kwargs.get("args", ["x"]), returncode=0, stdout="", stderr=""),
    )

    result = loop.run_step(
        "one shot",
        ["python", "step.py"],
        tmp_path,
        timeout_seconds=60,
        cycle_started_at_utc="2026-05-17T00:00:00+00:00",
        step_index=1,
        step_count=1,
        update_running=False,
    )

    assert result["ok"]
    assert json.loads(running.read_text(encoding="utf-8"))["status"] == "KEEP"


def test_run_step_running_status_includes_extra_contract(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loop, "RUNNING_JSON", tmp_path / "running.json")
    monkeypatch.setattr(
        loop.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=kwargs.get("args", ["x"]), returncode=0, stdout="", stderr=""),
    )

    result = loop.run_step(
        "contracted step",
        ["python", "step.py"],
        tmp_path,
        timeout_seconds=60,
        cycle_started_at_utc="2026-05-17T00:00:00+00:00",
        step_index=1,
        step_count=1,
        running_extra={
            "schema_version": loop.SCHEMA_VERSION,
            "model_only_safety": {"command_manifest_has_no_order_flags": True},
        },
    )

    running = json.loads((tmp_path / "running.json").read_text(encoding="utf-8"))
    assert result["ok"]
    assert running["schema_version"] == loop.SCHEMA_VERSION
    assert running["model_only_safety"]["command_manifest_has_no_order_flags"]


def test_read_json_returns_empty_dict_for_partial_or_non_object_file(tmp_path: Path) -> None:
    partial = tmp_path / "partial.json"
    partial.write_text("{", encoding="utf-8")
    assert loop.read_json(partial) == {}

    non_object = tmp_path / "list.json"
    non_object.write_text("[1, 2, 3]", encoding="utf-8")
    assert loop.read_json(non_object) == {}


def test_build_artifact_summary_reads_latest_files(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path
    monkeypatch.setattr(loop, "ROOT", root)
    (root / "reports" / "operations").mkdir(parents=True)
    (root / "reports" / "model_factory").mkdir(parents=True)
    (root / "ops" / "stock_etf_operating_candidate_bridge").mkdir(parents=True)

    (root / "reports" / "operations" / "two_axis_model_inventory_latest.json").write_text(
        json.dumps(
            {
                "axes": {
                    "BITHUMB_KRW": {
                        "counts": {"current_actionable_oos_pass": 6},
                        "verification_sources": {
                            "oos_top_candidate_id": "oos1",
                            "current_signal_candidate_id": "signal2",
                            "current_signal_matches_oos_top": False,
                            "current_signal_selection_policy": {"sort_keys": ["source_conversion.estimated_cagr"]},
                            "current_signal_selection_summary": {"selection_rank": 1, "estimated_cagr": 1.2},
                            "oos_top_signal_selection_summary": {"selection_rank": 2, "estimated_cagr": 1.1},
                            "current_signal_top_near_miss": {"candidate_id": "near1", "momentum_gap": -0.01, "volume_gap": -0.3},
                            "current_signal_top_near_miss_candidates": [
                                {"candidate_id": "near1", "momentum_gap": -0.01, "volume_gap": -0.3},
                                {"candidate_id": "near2", "momentum_gap": -0.02, "volume_gap": -0.2},
                            ],
                            "direct_crypto_top_live_near_miss_candidate": {"candidate_id": "direct_near1", "market": "KRW-BTC", "momentum_gap": -0.02, "volume_gap": -0.4},
                            "current_signal_oos_summary": {"average_fold_cagr": 0.8, "total_trade_count": 17},
                            "oos_top_summary": {"average_fold_cagr": 0.9, "total_trade_count": 19},
                        },
                    },
                    "KIS_COMBINED_KRW": {
                        "counts": {"stock_risk_conversion_ready": 3},
                        "verification_sources": {
                            "bridge_universe_validation_mode": "daily_close_presence",
                            "bridge_universe_validation_verifier_status": "NOT_REQUIRED",
                            "direct_source_bridge": {"candidate_id": "stock-top"},
                        },
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (root / "reports" / "model_factory" / "bithumb_current_actionable_oos_walkforward_latest.json").write_text(
        json.dumps(
            {
                "status": "OOS_WALKFORWARD_PASS",
                "generated_at": "2026-05-18T22:16:03+09:00",
                "candidate_count": 9,
                "aggregate": {"pass_count": 6},
                "top_oos": {"candidate_id": "oos1", "market": "KRW-ORCA"},
                "no_order_assertions": {"live_allowed_by_this_report": False, "real_orders_allowed_by_this_report": False},
            }
        ),
        encoding="utf-8",
    )
    (root / "reports" / "model_factory" / "bithumb_current_actionable_robustness_stress_latest.json").write_text(
        json.dumps(
            {
                "status": "ROBUSTNESS_STRESS_PASS",
                "generated_at": "2026-05-18T22:16:04+09:00",
                "source_oos": {"generated_at": "2026-05-18T22:16:03+09:00", "top_candidate_id": "oos1", "top_market": "KRW-ORCA"},
                "candidate_id": "orca",
                "pass_count": 7,
                "cost_pass_count": 1,
                "no_order_assertions": {"live_allowed_by_this_report": False, "real_orders_allowed_by_this_report": False},
            }
        ),
        encoding="utf-8",
    )
    (root / "reports" / "operations" / "bithumb_current_actionable_nonzero_signal_scout_latest.json").write_text(
        json.dumps(
            {
                "status": "NO_CURRENT_NONZERO_SIGNAL_FOUND",
                "generated_at_utc": "2026-05-18T22:16:05+00:00",
                "evaluated_count": 9,
                "triggered_count": 0,
                "top_near_miss": {
                    "candidate_id": "near-scout",
                    "nearest_trigger_gap": -0.25,
                    "blockers": ["volume_ratio_below_floor"],
                },
                "safety": {
                    "does_emit_order_signal": False,
                    "does_write_order_intent": False,
                    "broker_submit_allowed_by_this_report": False,
                    "real_orders": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "reports" / "model_factory" / "two_axis_direct_model_development_latest.json").write_text(
        json.dumps(
            {
                "status": "TWO_AXIS_DIRECT_DEVELOPMENT_OK",
                "generated_at_utc": "2026-05-18T00:00:01+00:00",
                "crypto": {
                    "candidate_count": 1,
                    "oos_pass_count": 1,
                    "validated_pass_count": 1,
                    "archive_signal_triggered_count": 1,
                    "top_live_signal_triggered_count": 0,
                    "top_live_signal_summary": {"all_live_verified": True},
                    "top_live_near_miss_candidate": {"candidate_id": "direct_near2", "market": "KRW-ETH", "momentum_gap": -0.01, "volume_gap": -0.2},
                },
                "kis": {
                    "conversion_variant_count": 1,
                    "pass_count": 1,
                    "source_bridge": {
                        "generated_at_utc": "2026-05-18T00:00:00+00:00",
                        "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
                        "candidate_id": "stock-top",
                        "universe_validation_mode": "daily_close_presence",
                    },
                    "universe_validation_mode": "daily_close_presence",
                    "universe_validation_verifier_status": "NOT_REQUIRED",
                    "universe_validation_operation_ready": True,
                    "universe_validation_all_verified": True,
                    "universe_validation_operational": True,
                    "counts_as_live_evidence": True,
                },
                "no_order_assertions": {"live_allowed_by_this_report": False, "real_orders_allowed_by_this_report": False},
            }
        ),
        encoding="utf-8",
    )
    (root / "ops" / "stock_etf_operating_candidate_bridge" / "stock_etf_operating_candidate_bridge_latest.json").write_text(
        json.dumps(
            {
                "status": "OPERATING_CANDIDATE_CONNECTED_SUBMIT_READY",
                "generated_at_utc": "2026-05-18T00:00:00+00:00",
                "candidate_id": "stock-top",
                "no_order_assertions": {"live_allowed_by_this_report": False, "real_orders_allowed_by_this_report": False},
                "universe_validation_mode": "daily_close_presence",
                "current_data": {
                    "target_book_rows": 6,
                    "order_intent_rows": 2,
                    "order_intent_submit_allowed_count": 1,
                    "order_intent_submit_allowed_symbols": ["049630"],
                },
                "target_book": {"symbols": ["069500"], "tiny_live_buyable_symbol_count": 1},
                "tiny_live_executable_repair": {
                    "status": "TINY_LIVE_REPAIR_RESEARCH_READY",
                    "order_paths_allowed": False,
                    "counts_as_live_evidence": False,
                    "buyable_count": 3,
                    "candidate_symbols": ["049630", "036170", "138360"],
                    "historical_oos_validation": {
                        "status": "TINY_LIVE_REPAIR_OOS_PASS",
                        "order_paths_allowed": False,
                        "counts_as_live_evidence": False,
                        "summary": {"CAGR": 0.10, "MDD": -0.11},
                        "holdout_30pct": {"CAGR": 0.30},
                    },
                },
                "execution_warnings": ["KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE"],
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )

    summary = loop.build_artifact_summary()

    assert summary["bithumb"]["oos_pass_count"] == 6
    assert summary["bithumb"]["oos_generated_at"] == "2026-05-18T22:16:03+09:00"
    assert summary["bithumb"]["oos_top_candidate_id"] == "oos1"
    assert summary["bithumb"]["oos_top_market"] == "KRW-ORCA"
    assert summary["bithumb"]["robustness_candidate_id"] == "orca"
    assert summary["bithumb"]["robustness_generated_at"] == "2026-05-18T22:16:04+09:00"
    assert summary["bithumb"]["robustness_source_oos"]["top_candidate_id"] == "oos1"
    assert summary["bithumb"]["signal_scout_status"] == "NO_CURRENT_NONZERO_SIGNAL_FOUND"
    assert summary["bithumb"]["signal_scout_generated_at"] == "2026-05-18T22:16:05+00:00"
    assert summary["bithumb"]["signal_scout_evaluated_count"] == 9
    assert summary["bithumb"]["signal_scout_triggered_count"] == 0
    assert summary["bithumb"]["signal_scout_top_near_miss"]["candidate_id"] == "near-scout"
    assert summary["bithumb"]["inventory_current_signal_candidate_id"] == "signal2"
    assert not summary["bithumb"]["inventory_current_signal_matches_oos_top"]
    assert summary["bithumb"]["inventory_oos_top_candidate_id"] == "oos1"
    assert summary["bithumb"]["inventory_current_signal_selection_policy"]["sort_keys"] == [
        "source_conversion.estimated_cagr"
    ]
    assert summary["bithumb"]["inventory_current_signal_selection_summary"]["selection_rank"] == 1
    assert summary["bithumb"]["inventory_oos_top_signal_selection_summary"]["estimated_cagr"] == 1.1
    assert summary["bithumb"]["inventory_current_signal_top_near_miss"]["candidate_id"] == "near1"
    assert summary["bithumb"]["inventory_current_signal_top_near_miss_candidates"][1]["candidate_id"] == "near2"
    assert summary["bithumb"]["inventory_current_signal_oos_summary"]["average_fold_cagr"] == 0.8
    assert summary["bithumb"]["inventory_oos_top_summary"]["total_trade_count"] == 19
    assert summary["direct_development"]["generated_at_utc"] == "2026-05-18T00:00:01+00:00"
    assert summary["direct_development"]["crypto_archive_signal_triggered_count"] == 1
    assert summary["direct_development"]["crypto_top_live_signal_triggered_count"] == 0
    assert summary["direct_development"]["crypto_top_live_signal_all_verified"]
    assert summary["direct_development"]["crypto_top_live_near_miss_candidate"]["candidate_id"] == "direct_near2"
    assert summary["bithumb"]["inventory_direct_top_live_near_miss_candidate"]["candidate_id"] == "direct_near1"
    assert summary["direct_development"]["kis_universe_validation_mode"] == "daily_close_presence"
    assert summary["direct_development"]["kis_source_bridge"]["candidate_id"] == "stock-top"
    assert summary["direct_development"]["kis_universe_validation_verifier_status"] == "NOT_REQUIRED"
    assert summary["direct_development"]["kis_universe_validation_operation_ready"]
    assert summary["direct_development"]["kis_universe_validation_all_verified"]
    assert summary["direct_development"]["kis_universe_validation_operational"]
    assert summary["direct_development"]["kis_counts_as_live_evidence"]
    assert summary["kis"]["candidate_id"] == "stock-top"
    assert summary["kis"]["universe_validation_mode"] == "daily_close_presence"
    assert summary["kis"]["universe_validation_operational"]
    assert summary["kis"]["target_symbols"] == ["069500"]
    assert summary["kis"]["tiny_live_repair_buyable_count"] == 3
    assert summary["kis"]["tiny_live_repair_oos_status"] == "TINY_LIVE_REPAIR_OOS_PASS"
    assert summary["kis"]["tiny_live_repair_oos_holdout_cagr"] == 0.30
    assert summary["kis"]["order_intent_rows"] == 2
    assert summary["kis"]["order_intent_submit_allowed_count"] == 1
    assert summary["kis"]["order_intent_submit_allowed_symbols"] == ["049630"]
    assert summary["kis"]["execution_warnings"] == ["KIS_TINY_LIVE_LOW_BUYABLE_COVERAGE"]
    assert summary["model_only_guardrails"]["all_known_order_paths_false"]
    assert summary["model_only_guardrails"]["model_only_attention"]
    assert summary["model_only_guardrails"]["kis_order_intent_submit_allowed_count"] == 1
    assert summary["model_only_guardrails"]["kis_universe_validation_operational"]
    assert summary["model_only_guardrails"]["source_generated_at_utc"]["bithumb_signal_scout"] == "2026-05-18T22:16:05+00:00"
    assert summary["model_only_guardrails"]["source_generated_at_utc"]["kis_bridge"] == "2026-05-18T00:00:00+00:00"
    assert summary["model_only_guardrails"]["kis_bridge"]["all_order_paths_false"]
    assert summary["model_only_guardrails"]["kis_all_order_paths_false"]


def test_summarize_no_order_assertions_reports_true_flags() -> None:
    summary = loop.summarize_no_order_assertions(
        {
            "no_order_assertions": {
                "live_allowed_by_this_report": "False",
                "real_orders_allowed_by_this_report": True,
            }
        }
    )

    assert summary["present"]
    assert not summary["all_order_paths_false"]
    assert summary["true_flags"] == ["real_orders_allowed_by_this_report"]


def test_truthy_flag_treats_false_string_as_false() -> None:
    assert loop.truthy_flag(True)
    assert loop.truthy_flag("True")
    assert not loop.truthy_flag(False)
    assert not loop.truthy_flag("False")
    assert not loop.truthy_flag("")


def test_first_present_preserves_zero_and_false() -> None:
    assert loop.first_present(None, 0, 3) == 0
    assert loop.first_present(None, False, True) is False
    assert loop.first_present(None, None) is None


def test_append_history_writes_jsonl(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loop, "OPS_DIR", tmp_path)
    monkeypatch.setattr(loop, "HISTORY_JSONL", tmp_path / "history.jsonl")

    loop.append_history({"status": "OK", "ok_count": 1})

    lines = (tmp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["status"] == "OK"


def test_write_json_replaces_latest_with_valid_json(tmp_path: Path) -> None:
    target = tmp_path / "latest.json"
    target.write_text(json.dumps({"status": "OLD"}), encoding="utf-8")

    loop.write_json(target, {"status": "NEW", "count": 2})

    assert json.loads(target.read_text(encoding="utf-8")) == {"status": "NEW", "count": 2}
    assert not (tmp_path / ".latest.json.tmp").exists()


def test_stock_bridge_step_uses_text_output_to_keep_loop_history_compact() -> None:
    steps = loop.build_steps()
    bridge_steps = [command for label, command, _cwd in steps if label == "stock operating candidate bridge"]

    assert bridge_steps
    assert "--format" in bridge_steps[0]
    assert bridge_steps[0][bridge_steps[0].index("--format") + 1] == "text"


def test_build_step_manifest_records_ordered_step_contract() -> None:
    manifest = loop.build_step_manifest(loop.build_steps())

    assert manifest[0]["index"] == 1
    assert manifest[0]["label"] == "bithumb parameter sweep"
    assert manifest[-1]["index"] == len(manifest)
    assert manifest[-1]["label"] == "dashboard refresh"
    assert len(manifest) == len(loop.build_steps())


def test_build_model_only_safety_reports_no_order_flags_for_current_manifest() -> None:
    safety = loop.build_model_only_safety(loop.build_step_manifest(loop.build_steps()))

    assert safety["mode"] == "model_development_and_verification_only"
    assert safety["command_manifest_has_no_order_flags"]
    assert safety["forbidden_order_flag_hits"] == []
    assert safety["forbidden_order_script_hits"] == []
    assert not safety["order_submission_allowed_by_this_loop"]
    assert not safety["broker_submit_allowed_by_this_loop"]
    assert not safety["real_orders_allowed_by_this_loop"]


def test_build_model_only_safety_flags_submit_commands() -> None:
    safety = loop.build_model_only_safety(
        [
            {
                "label": "bad step",
                "command": ["python", "bad.py", "--submit"],
                "cwd": "C:\\AI",
            }
        ]
    )

    assert not safety["command_manifest_has_no_order_flags"]
    assert safety["forbidden_order_flag_hits"] == [
        {"label": "bad step", "forbidden_flags": ["--submit"]}
    ]


def test_build_model_only_safety_flags_submit_scripts_without_submit_flag() -> None:
    safety = loop.build_model_only_safety(
        [
            {
                "label": "bad script",
                "command": ["python", "kis_stock_etf_order_submit.py"],
                "cwd": "C:\\AI",
            }
        ]
    )

    assert not safety["command_manifest_has_no_order_flags"]
    assert safety["forbidden_order_flag_hits"] == []
    assert safety["forbidden_order_script_hits"] == [
        {"label": "bad script", "forbidden_script_patterns": ["order_submit"]}
    ]


def test_stock_bridge_runs_before_direct_and_inventory_so_artifacts_share_fresh_bridge() -> None:
    labels = [label for label, _command, _cwd in loop.build_steps()]

    assert labels.index("stock operating candidate bridge") < labels.index("two axis direct model development")
    assert labels.index("stock operating candidate bridge") < labels.index("two axis inventory")
    assert labels.index("two axis direct model development") < labels.index("two axis inventory")


def test_stock_bridge_runs_direct_inventory_and_dashboard_without_pit_steps() -> None:
    labels = [label for label, _command, _cwd in loop.build_steps()]

    assert labels.index("stock operating candidate bridge") < labels.index("two axis direct model development")
    assert labels.index("two axis direct model development") < labels.index("two axis inventory")
    assert labels.index("two axis inventory") < labels.index("dashboard refresh")
    assert not any("pit" in label.lower() or "membership" in label.lower() for label in labels)


def test_model_factory_steps_do_not_use_broker_submit_or_live_flags() -> None:
    forbidden = {"--submit", "--live", "--private-submit", "--broker-submit"}

    for label, command, _cwd in loop.build_steps():
        assert not forbidden.intersection(command), label


def test_run_once_writes_schema_version_and_step_manifest(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loop, "LATEST_JSON", tmp_path / "latest.json")
    monkeypatch.setattr(loop, "RUNNING_JSON", tmp_path / "running.json")
    monkeypatch.setattr(loop, "HISTORY_JSONL", tmp_path / "history.jsonl")
    monkeypatch.setattr(loop, "OPS_DIR", tmp_path)
    monkeypatch.setattr(
        loop,
        "build_steps",
        lambda: [("safe verification step", ["python", "safe.py"], tmp_path)],
    )
    monkeypatch.setattr(
        loop,
        "run_step",
        lambda label, command, cwd, **kwargs: {
            "label": label,
            "command": command,
            "cwd": str(cwd),
            "ok": True,
            "returncode": 0,
        },
    )
    monkeypatch.setattr(loop, "build_artifact_summary", lambda: {"direct_development": {"status": "OK"}})

    payload = loop.run_once(step_timeout_seconds=60)

    assert payload["schema_version"] == loop.SCHEMA_VERSION
    assert payload["step_manifest"][0]["label"] == "safe verification step"
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    running = json.loads((tmp_path / "running.json").read_text(encoding="utf-8"))
    assert latest["schema_version"] == loop.SCHEMA_VERSION
    assert running["schema_version"] == loop.SCHEMA_VERSION
    assert running["step_manifest"][0]["command"] == ["python", "safe.py"]
    assert latest["model_only_safety"]["mode"] == "model_development_and_verification_only"
    assert latest["model_only_safety"]["command_manifest_has_no_order_flags"]
    assert not latest["model_only_safety"]["order_submission_allowed_by_this_loop"]
    assert running["model_only_safety"]["command_manifest_has_no_order_flags"]


def test_bithumb_signal_scout_runs_after_oos_and_before_inventory() -> None:
    labels = [label for label, _command, _cwd in loop.build_steps()]

    assert labels.index("bithumb parameter sweep") < labels.index("bithumb oos verification")
    assert labels.index("bithumb oos verification") < labels.index("bithumb nonzero signal scout")
    assert labels.index("bithumb robustness stress") < labels.index("bithumb nonzero signal scout")
    assert labels.index("bithumb nonzero signal scout") < labels.index("two axis inventory")


def test_dashboard_refresh_runs_after_inventory_so_it_uses_latest_verification_snapshot() -> None:
    labels = [label for label, _command, _cwd in loop.build_steps()]

    assert labels.index("two axis inventory") < labels.index("dashboard refresh")
    assert labels.index("bithumb nonzero signal scout") < labels.index("dashboard refresh")
    assert labels.index("two axis direct model development") < labels.index("dashboard refresh")
