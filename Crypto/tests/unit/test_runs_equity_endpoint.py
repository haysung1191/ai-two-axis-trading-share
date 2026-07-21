import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.api.routes.runs import StartRunRequest


def test_runs_equity_endpoint_returns_equity_series(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "artifacts" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "backtest_reports.json").write_text(
        json.dumps(
            [
                {"strategy_name": "alpha", "equity_curve": [1.0, 1.1, 1.2]},
                {"strategy_name": "beta", "equity_curve": [1.0, 0.9, 0.95]},
            ]
        ),
        encoding="utf-8",
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/runs/run-1/equity")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-1"
    assert len(payload["series"]) == 2
    assert payload["series"][0]["strategy_name"] == "alpha"


def test_runs_equity_endpoint_supports_strategy_filter(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "artifacts" / "run-2"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "backtest_reports.json").write_text(
        json.dumps(
            [
                {"strategy_name": "alpha", "equity_curve": [1.0, 1.1]},
                {"strategy_name": "beta", "equity_curve": [1.0, 0.95]},
            ]
        ),
        encoding="utf-8",
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/runs/run-2/equity?strategy_name=beta")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["series"]) == 1
    assert payload["series"][0]["strategy_name"] == "beta"
    assert payload["series"][0]["equity_curve"] == [1.0, 0.95]


def test_start_run_request_defaults_to_krw_symbols_and_hourly_interval() -> None:
    from app.api import routes as routes_pkg

    routes_pkg.runs._default_krw_research_symbols = lambda: [  # type: ignore[attr-defined]
        "KRW-BTC",
        "KRW-ETH",
        "KRW-SOL",
        "KRW-XRP",
        "KRW-ADA",
        "KRW-DOGE",
        "KRW-LINK",
        "KRW-AVAX",
        "KRW-DOT",
        "KRW-TRX",
        "KRW-XLM",
        "KRW-HBAR",
        "KRW-SUI",
        "KRW-APT",
        "KRW-ATOM",
        "KRW-ARB",
        "KRW-OP",
        "KRW-AAVE",
        "KRW-NEAR",
        "KRW-ETC",
        "KRW-UNI",
    ]
    request = StartRunRequest(title="KRW defaults", description="Ensure research spec stays on KRW market")

    spec = request.to_spec()

    assert spec.metadata["symbols"][0] == "KRW-BTC"
    assert len(spec.metadata["symbols"]) == 21
    assert spec.metadata["symbols"][1:4] == ["KRW-ETH", "KRW-SOL", "KRW-XRP"]
    assert spec.metadata["ohlcv_interval"] == "1h"
    assert "BTCUSDT" not in spec.metadata["symbols"]


def test_start_run_request_accepts_4h_interval() -> None:
    from app.api import routes as routes_pkg

    routes_pkg.runs._default_krw_research_symbols = lambda: [  # type: ignore[attr-defined]
        "KRW-BTC",
        "KRW-ETH",
        "KRW-SOL",
        "KRW-XRP",
        "KRW-ADA",
        "KRW-DOGE",
        "KRW-LINK",
        "KRW-AVAX",
        "KRW-DOT",
        "KRW-TRX",
        "KRW-XLM",
        "KRW-HBAR",
        "KRW-SUI",
        "KRW-APT",
        "KRW-ATOM",
        "KRW-ARB",
        "KRW-OP",
        "KRW-AAVE",
        "KRW-NEAR",
        "KRW-ETC",
        "KRW-UNI",
    ]
    request = StartRunRequest(title="KRW 4h", description="Ensure research spec supports 4h", ohlcv_interval="4h")

    spec = request.to_spec()

    assert spec.metadata["ohlcv_interval"] == "4h"
    assert spec.metadata["symbols"][0] == "KRW-BTC"
