from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_manual_summary(path: Path) -> None:
    payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "manual_brief": {
            "watchlist": [
                {
                    "symbol": "BTC",
                    "rank": 1,
                    "action": "BUY",
                    "reference_price_krw": 150000000.0,
                    "suggested_stop_price_krw": 145000000.0,
                    "suggested_take_profit_price_krw": 160000000.0,
                    "risk_reward_ratio": 2.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "Scheduled by the baseline scanner.",
                }
            ]
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_execution_contract_screen(
    path: Path,
    *,
    paper_execution_read: str,
    paper_ledger_snapshot_read: str,
    execution_contract_aligned: bool,
    paper_ledger_snapshot_summary_aligned: bool,
    paper_execution_contract_checked_aligned: bool = True,
    paper_execution_contract_aligned_aligned: bool = True,
    paper_execution_contract_checked_summary_aligned: bool = True,
    paper_execution_contract_aligned_summary_aligned: bool = True,
    paper_execution_contract_checked_aligned_entry_aligned: bool = True,
    paper_execution_contract_aligned_aligned_entry_aligned: bool = True,
    paper_execution_contract_checked_summary_aligned_entry_aligned: bool = True,
    paper_execution_contract_aligned_summary_aligned_entry_aligned: bool = True,
    paper_execution_contract_checked_aligned_summary_aligned: bool = True,
    paper_execution_contract_aligned_aligned_summary_aligned: bool = True,
    paper_execution_contract_checked_summary_aligned_summary_aligned: bool = True,
    paper_execution_contract_aligned_summary_aligned_summary_aligned: bool = True,
) -> None:
    payload = {
        "execution_contract_summary": {
            "execution_contract_read": (
                f"execution contract | {'aligned' if execution_contract_aligned else 'drifted'} | "
                f"{paper_execution_read}"
            ),
            "paper_execution_read": paper_execution_read,
            "paper_ledger_snapshot_read": paper_ledger_snapshot_read,
            "paper_execution_contract_checked_aligned": paper_execution_contract_checked_aligned,
            "paper_execution_contract_aligned_aligned": paper_execution_contract_aligned_aligned,
            "paper_execution_contract_checked_summary_aligned": paper_execution_contract_checked_summary_aligned,
            "paper_execution_contract_aligned_summary_aligned": paper_execution_contract_aligned_summary_aligned,
            "paper_execution_contract_checked_aligned_entry_aligned": paper_execution_contract_checked_aligned_entry_aligned,
            "paper_execution_contract_aligned_aligned_entry_aligned": paper_execution_contract_aligned_aligned_entry_aligned,
            "paper_execution_contract_checked_summary_aligned_entry_aligned": paper_execution_contract_checked_summary_aligned_entry_aligned,
            "paper_execution_contract_aligned_summary_aligned_entry_aligned": paper_execution_contract_aligned_summary_aligned_entry_aligned,
            "paper_execution_contract_checked_aligned_summary_aligned": paper_execution_contract_checked_aligned_summary_aligned,
            "paper_execution_contract_aligned_aligned_summary_aligned": paper_execution_contract_aligned_aligned_summary_aligned,
            "paper_execution_contract_checked_summary_aligned_summary_aligned": paper_execution_contract_checked_summary_aligned_summary_aligned,
            "paper_execution_contract_aligned_summary_aligned_summary_aligned": paper_execution_contract_aligned_summary_aligned_summary_aligned,
            "paper_ledger_snapshot_summary_aligned": paper_ledger_snapshot_summary_aligned,
        },
        "execution_contract_verdict": {
            "execution_contract_aligned": execution_contract_aligned,
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_run_bithumb_paper_nightly_script_outputs_json(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    exit_path = tmp_path / "exit_snapshot.json"
    exit_path.write_text(
        json.dumps(
            {
                "run_id": "1h:test-close",
                "candle_close_utc": "2026-04-16T13:00:00Z",
                "market_ohlc": {
                    "KRW-BTC": {
                        "open": 151000000.0,
                        "high": 161000000.0,
                        "low": 149000000.0,
                        "close": 160500000.0,
                    }
                },
                "standard_check_order_reference": ["practical", "research", "contract", "brief"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    ledger_path = tmp_path / "paper_ledger.json"
    execution_contract_screen_path = tmp_path / "execution_contract_screen_latest.json"
    _write_execution_contract_screen(
        execution_contract_screen_path,
        paper_execution_read="paper execution | track=operating | applied=1 | closed=0 | open=1",
        paper_ledger_snapshot_read="paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1",
        execution_contract_aligned=True,
        paper_ledger_snapshot_summary_aligned=True,
    )
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path("scripts/run_bithumb_paper_nightly.py")),
        "--logs-dir",
        str(logs_dir),
        "--ledger-json",
        str(ledger_path),
        "--output-dir",
        str(output_dir),
        "--exit-json",
        str(exit_path),
        "--execution-contract-screen-json",
        str(execution_contract_screen_path),
        "--notional-krw",
        "250000",
        "--max-orders",
        "1",
        "--track",
        "operating",
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["paper_execution_read"] == "paper execution | track=operating | applied=1 | closed=0 | open=1"
    assert payload["paper_ledger_snapshot_read"] == "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1"
    assert payload["intent_count"] == 1
    assert payload["signed_request_count"] == 1
    assert payload["paper_applied_count"] == 1
    assert payload["paper_closed_count"] == 0
    assert payload["paper_open_count"] == 1
    assert payload["paper_exit_duplicate_run"] is False
    assert payload["paper_ledger_consistent"] is True
    assert payload["execution_contract_checked"] is True
    assert payload["execution_contract_aligned"] is True
    assert payload["execution_contract_paper_execution_read_aligned"] is True
    assert payload["execution_contract_paper_ledger_snapshot_aligned"] is True
    assert payload["execution_contract_paper_ledger_snapshot_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_checked_aligned"] is True
    assert payload["paper_execution_contract_aligned_aligned"] is True
    assert payload["paper_execution_contract_checked_summary_aligned"] is True
    assert payload["paper_execution_contract_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert payload["paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert payload["paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert payload["paper_ledger_consistency"]["open_position_count"] == 1
    assert payload["paper_ledger_snapshot"]["open_position_count"] == 1
    assert payload["paper_ledger_snapshot"]["order_count"] == 1
    assert Path(payload["artifacts"]["plan_json"]).exists()
    assert Path(payload["artifacts"]["signed_preview_json"]).exists()
    assert Path(payload["artifacts"]["summary_json"]).exists()
    assert Path(payload["artifacts"]["summary_md"]).exists()
    summary_md = Path(payload["artifacts"]["summary_md"]).read_text(encoding="utf-8")
    assert "Paper execution read: `paper execution | track=operating | applied=1 | closed=0 | open=1`" in summary_md
    assert "Paper ledger snapshot: `paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1`" in summary_md
    assert "Paper exit duplicate run: `False`" in summary_md
    assert "Paper ledger consistent: `True`" in summary_md
    assert "Execution contract aligned: `True`" in summary_md
    assert "Paper execution contract checked aligned: `True`" in summary_md
    assert "Paper execution contract aligned aligned: `True`" in summary_md
    assert "Paper execution contract checked summary aligned: `True`" in summary_md
    assert "Paper execution contract aligned summary aligned: `True`" in summary_md
    assert "Paper execution contract checked aligned entry aligned: `True`" in summary_md
    assert "Paper execution contract aligned aligned entry aligned: `True`" in summary_md
    assert "Paper execution contract checked summary aligned entry aligned: `True`" in summary_md
    assert "Paper execution contract aligned summary aligned entry aligned: `True`" in summary_md
    assert "Paper execution contract checked aligned summary aligned: `True`" in summary_md
    assert "Paper execution contract aligned aligned summary aligned: `True`" in summary_md
    assert "Paper execution contract checked summary aligned summary aligned: `True`" in summary_md
    assert "Paper execution contract aligned summary aligned summary aligned: `True`" in summary_md
    saved_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    open_positions = [row for row in saved_ledger["positions"] if row["status"] == "OPEN"]
    assert len(open_positions) == 1
    assert open_positions[0]["run_id"] == "1h:test"


def test_run_bithumb_paper_nightly_flags_execution_contract_drift(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    ledger_path = tmp_path / "paper_ledger.json"
    execution_contract_screen_path = tmp_path / "execution_contract_screen_latest.json"
    _write_execution_contract_screen(
        execution_contract_screen_path,
        paper_execution_read="paper execution | track=operating | applied=0 | closed=0 | open=0",
        paper_ledger_snapshot_read="paper ledger | open=0 | closed=0 | exit_fills=0 | orders=0 | fills=0",
        execution_contract_aligned=False,
        paper_ledger_snapshot_summary_aligned=False,
    )
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path("scripts/run_bithumb_paper_nightly.py")),
        "--logs-dir",
        str(logs_dir),
        "--ledger-json",
        str(ledger_path),
        "--output-dir",
        str(output_dir),
        "--execution-contract-screen-json",
        str(execution_contract_screen_path),
        "--notional-krw",
        "250000",
        "--max-orders",
        "1",
        "--track",
        "operating",
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)

    assert payload["execution_contract_checked"] is True
    assert payload["execution_contract_aligned"] is False
    assert payload["execution_contract_paper_execution_read_aligned"] is False
    assert payload["execution_contract_paper_ledger_snapshot_aligned"] is False
    assert payload["execution_contract_paper_ledger_snapshot_summary_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_checked_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is True
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is True
    assert payload["paper_execution_read"] == "paper execution | track=operating | applied=1 | closed=0 | open=1"
    assert payload["paper_ledger_snapshot_read"] == "paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1"


def test_run_bithumb_paper_nightly_normalizes_legacy_duplicate_ledger_rows(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    ledger_path = tmp_path / "paper_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "orders": [
                    {
                        "order_id": "paper-order-1h-test-01",
                        "run_id": "1h:test",
                        "market": "KRW-BTC",
                        "symbol": "BTC",
                        "status": "FILLED_PAPER",
                    },
                    {
                        "order_id": "paper-order-1h-test-01",
                        "run_id": "1h:test",
                        "market": "KRW-BTC",
                        "symbol": "BTC",
                        "status": "FILLED_PAPER",
                    },
                ],
                "fills": [
                    {"fill_id": "paper-fill-1h-test-01", "order_id": "paper-order-1h-test-01"},
                    {"fill_id": "paper-fill-1h-test-01", "order_id": "paper-order-1h-test-01"},
                ],
                "positions": [
                    {
                        "position_id": "paper-pos-1h-test-01",
                        "opened_from_order_id": "paper-order-1h-test-01",
                        "run_id": "1h:test",
                        "market": "KRW-BTC",
                        "symbol": "BTC",
                        "status": "CLOSED",
                        "opened_at": "2026-04-16T12:00:00Z",
                        "closed_at": "2026-04-16T13:00:00Z",
                    },
                    {
                        "position_id": "paper-pos-1h-test-01",
                        "opened_from_order_id": "paper-order-1h-test-01",
                        "run_id": "1h:test",
                        "market": "KRW-BTC",
                        "symbol": "BTC",
                        "status": "OPEN",
                        "opened_at": "2026-04-16T12:00:00Z",
                    },
                ],
                "closed_positions": [
                    {"position_id": "paper-pos-1h-test-01", "exit_run_id": "1h:close"},
                    {"position_id": "paper-pos-1h-test-01", "exit_run_id": "1h:close"},
                ],
                "exit_fills": [
                    {"fill_id": "paper-exit-1h-close-01", "position_id": "paper-pos-1h-test-01"},
                    {"fill_id": "paper-exit-1h-close-01", "position_id": "paper-pos-1h-test-01"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path("scripts/run_bithumb_paper_nightly.py")),
        "--logs-dir",
        str(logs_dir),
        "--ledger-json",
        str(ledger_path),
        "--output-dir",
        str(output_dir),
        "--notional-krw",
        "250000",
        "--max-orders",
        "1",
        "--track",
        "operating",
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)

    assert payload["paper_applied_count"] == 0
    assert payload["paper_duplicate_count"] == 1
    assert payload["paper_ledger_consistent"] is True
    assert payload["paper_ledger_snapshot"]["open_position_count"] == 0
    assert payload["paper_ledger_snapshot"]["closed_position_count"] == 1
    assert payload["paper_ledger_snapshot"]["exit_fill_count"] == 1
    assert payload["paper_ledger_snapshot"]["order_count"] == 1
    assert payload["paper_ledger_snapshot"]["fill_count"] == 1


def test_run_bithumb_paper_nightly_reads_execution_contract_self_check_alignment(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    ledger_path = tmp_path / "paper_ledger.json"
    execution_contract_screen_path = tmp_path / "execution_contract_screen_latest.json"
    _write_execution_contract_screen(
        execution_contract_screen_path,
        paper_execution_read="paper execution | track=operating | applied=1 | closed=0 | open=1",
        paper_ledger_snapshot_read="paper ledger | open=1 | closed=0 | exit_fills=0 | orders=1 | fills=1",
        execution_contract_aligned=False,
        paper_ledger_snapshot_summary_aligned=False,
        paper_execution_contract_checked_aligned=False,
        paper_execution_contract_aligned_aligned=False,
        paper_execution_contract_checked_summary_aligned=False,
        paper_execution_contract_aligned_summary_aligned=False,
        paper_execution_contract_checked_aligned_entry_aligned=False,
        paper_execution_contract_aligned_aligned_entry_aligned=False,
        paper_execution_contract_checked_summary_aligned_entry_aligned=False,
        paper_execution_contract_aligned_summary_aligned_entry_aligned=False,
        paper_execution_contract_checked_aligned_summary_aligned=False,
        paper_execution_contract_aligned_aligned_summary_aligned=False,
        paper_execution_contract_checked_summary_aligned_summary_aligned=False,
        paper_execution_contract_aligned_summary_aligned_summary_aligned=False,
    )
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path("scripts/run_bithumb_paper_nightly.py")),
        "--logs-dir",
        str(logs_dir),
        "--ledger-json",
        str(ledger_path),
        "--output-dir",
        str(output_dir),
        "--execution-contract-screen-json",
        str(execution_contract_screen_path),
        "--notional-krw",
        "250000",
        "--max-orders",
        "1",
        "--track",
        "operating",
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)

    assert payload["execution_contract_checked"] is True
    assert payload["execution_contract_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_checked_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_aligned_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_checked_aligned_entry_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_entry_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_entry_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_entry_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_checked_aligned_summary_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_aligned_aligned_summary_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_checked_summary_aligned_summary_aligned"] is False
    assert payload["execution_contract_paper_execution_contract_aligned_summary_aligned_summary_aligned"] is False
    assert payload["paper_execution_contract_checked_aligned"] is False
    assert payload["paper_execution_contract_aligned_aligned"] is False
    assert payload["paper_execution_contract_checked_summary_aligned"] is False
    assert payload["paper_execution_contract_aligned_summary_aligned"] is False
    assert payload["paper_execution_contract_checked_aligned_entry_aligned"] is False
    assert payload["paper_execution_contract_aligned_aligned_entry_aligned"] is False
    assert payload["paper_execution_contract_checked_summary_aligned_entry_aligned"] is False
    assert payload["paper_execution_contract_aligned_summary_aligned_entry_aligned"] is False
    assert payload["paper_execution_contract_checked_aligned_summary_aligned"] is False
    assert payload["paper_execution_contract_aligned_aligned_summary_aligned"] is False
    assert payload["paper_execution_contract_checked_summary_aligned_summary_aligned"] is False
    assert payload["paper_execution_contract_aligned_summary_aligned_summary_aligned"] is False


def test_run_bithumb_paper_nightly_is_idempotent_on_same_run(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    exit_path = tmp_path / "exit_snapshot.json"
    exit_path.write_text(
        json.dumps(
            {
                "run_id": "1h:test-close",
                "candle_close_utc": "2026-04-16T13:00:00Z",
                "market_ohlc": {
                    "KRW-BTC": {
                        "open": 151000000.0,
                        "high": 161000000.0,
                        "low": 149000000.0,
                        "close": 160500000.0,
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    ledger_path = tmp_path / "paper_ledger.json"
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path("scripts/run_bithumb_paper_nightly.py")),
        "--logs-dir",
        str(logs_dir),
        "--ledger-json",
        str(ledger_path),
        "--output-dir",
        str(output_dir),
        "--exit-json",
        str(exit_path),
        "--notional-krw",
        "250000",
        "--max-orders",
        "1",
        "--track",
        "operating",
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
    ]

    subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)

    payload = json.loads(result.stdout)
    assert payload["paper_applied_count"] == 0
    assert payload["paper_rejected_count"] == 0
    assert payload["paper_duplicate_count"] == 1
    assert payload["paper_closed_count"] == 0
    assert payload["paper_open_count"] == 1
    assert payload["paper_exit_duplicate_run"] is True
    assert payload["paper_ledger_consistent"] is True
    assert payload["paper_ledger_snapshot"]["open_position_count"] == 1

    saved_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert len(saved_ledger["orders"]) == 1
    assert len(saved_ledger["fills"]) == 1
    assert saved_ledger["closed_positions"] == []
    assert saved_ledger["exit_fills"] == []
    open_positions = [row for row in saved_ledger["positions"] if row["status"] == "OPEN"]
    assert len(open_positions) == 1
    assert open_positions[0]["run_id"] == "1h:test"


def test_run_bithumb_paper_nightly_exits_open_position_before_new_entry(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    exit_path = tmp_path / "exit_snapshot.json"
    exit_path.write_text(
        json.dumps(
            {
                "run_id": "1h:test-close",
                "candle_close_utc": "2026-04-16T12:00:00Z",
                "market_ohlc": {
                    "KRW-BTC": {
                        "open": 151000000.0,
                        "high": 161000000.0,
                        "low": 149000000.0,
                        "close": 160500000.0,
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    ledger_path = tmp_path / "paper_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-04-16T11:59:00Z",
                "updated_at": "2026-04-16T11:59:00Z",
                "ledger_version": "paper_execution_v1",
                "account_currency": "KRW",
                "last_run_id": "1h:prior",
                "last_candle_close_utc": "2026-04-16T11:00:00Z",
                "orders": [],
                "fills": [],
                "positions": [
                    {
                        "position_id": "paper-pos-prior-01",
                        "opened_from_order_id": "paper-order-prior-01",
                        "run_id": "1h:prior",
                        "venue": "bithumb",
                        "market": "KRW-BTC",
                        "symbol": "BTC",
                        "status": "OPEN",
                        "strategy_track": "operating",
                        "entry_price_krw": 150000000.0,
                        "quote_amount_krw": 250000.0,
                        "qty": 250000.0 / 150000000.0,
                        "suggested_stop_price_krw": 145000000.0,
                        "suggested_take_profit_price_krw": 160000000.0,
                        "time_exit_utc": None,
                        "opened_at": "2026-04-16T11:00:00Z",
                    }
                ],
                "rejections": [],
                "closed_positions": [],
                "exit_fills": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(Path("scripts/run_bithumb_paper_nightly.py")),
        "--logs-dir",
        str(logs_dir),
        "--ledger-json",
        str(ledger_path),
        "--output-dir",
        str(output_dir),
        "--exit-json",
        str(exit_path),
        "--notional-krw",
        "250000",
        "--max-orders",
        "1",
        "--track",
        "operating",
        "--access-key",
        "ak",
        "--secret-key",
        "sk",
        "--client-order-prefix",
        "nightly",
        "--format",
        "json",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)

    assert payload["paper_applied_count"] == 1
    assert payload["paper_rejected_count"] == 0
    assert payload["paper_closed_count"] == 1
    assert payload["paper_open_count"] == 1
    assert payload["paper_exit_duplicate_run"] is False
    assert payload["paper_ledger_consistent"] is True
    assert payload["paper_ledger_snapshot"]["closed_position_count"] == 1

    saved_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    closed_positions = saved_ledger["closed_positions"]
    open_positions = [row for row in saved_ledger["positions"] if row["status"] == "OPEN"]
    assert len(closed_positions) == 1
    assert closed_positions[0]["run_id"] == "1h:prior"
    assert closed_positions[0]["exit_reason"] == "TP"
    assert len(open_positions) == 1
    assert open_positions[0]["run_id"] == "1h:test"
    assert open_positions[0]["market"] == "KRW-BTC"
