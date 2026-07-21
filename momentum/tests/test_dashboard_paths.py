from pathlib import Path
import sys
import types

import pandas as pd

import config


class _DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def metric(self, *args, **kwargs):
        return None

    def markdown(self, *args, **kwargs):
        return None

    def caption(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None

    def dataframe(self, *args, **kwargs):
        return None

    def plotly_chart(self, *args, **kwargs):
        return None

    def line_chart(self, *args, **kwargs):
        return None


class _DummyStyler:
    def __init__(self, frame):
        self._frame = frame

    def format(self, *args, **kwargs):
        return self._frame

    def map(self, *args, **kwargs):
        return self._frame


def test_dashboard_repo_root_paths_and_docker_entrypoint() -> None:
    fake_streamlit = types.SimpleNamespace()
    fake_streamlit.set_page_config = lambda **kwargs: None
    fake_streamlit.cache_data = lambda ttl=None: (lambda fn: fn)
    fake_streamlit.sidebar = types.SimpleNamespace(
        header=lambda *args, **kwargs: None,
        radio=lambda *args, **kwargs: "개별종목",
        number_input=lambda *args, **kwargs: 50000,
        slider=lambda *args, **kwargs: (0.0, 100.0),
        checkbox=lambda *args, **kwargs: True,
    )
    fake_streamlit.warning = lambda *args, **kwargs: None
    fake_streamlit.error = lambda *args, **kwargs: None
    fake_streamlit.info = lambda *args, **kwargs: None
    fake_streamlit.caption = lambda *args, **kwargs: None
    fake_streamlit.markdown = lambda *args, **kwargs: None
    fake_streamlit.metric = lambda *args, **kwargs: None
    fake_streamlit.title = lambda *args, **kwargs: None
    fake_streamlit.dataframe = lambda *args, **kwargs: None
    fake_streamlit.plotly_chart = lambda *args, **kwargs: None
    fake_streamlit.line_chart = lambda *args, **kwargs: None
    fake_streamlit.checkbox = lambda *args, **kwargs: True
    fake_streamlit.stop = lambda: None
    fake_streamlit.columns = lambda spec: [_DummyContext() for _ in range(spec if isinstance(spec, int) else len(spec))]
    fake_streamlit.tabs = lambda labels: [_DummyContext() for _ in labels]

    fake_px = types.SimpleNamespace(
        scatter=lambda *args, **kwargs: types.SimpleNamespace(update_layout=lambda **kw: None),
        bar=lambda *args, **kwargs: types.SimpleNamespace(update_layout=lambda **kw: None),
        line=lambda *args, **kwargs: types.SimpleNamespace(update_layout=lambda **kw: None),
    )

    orig_read_excel = pd.read_excel
    orig_read_csv = pd.read_csv
    orig_style = pd.DataFrame.style
    orig_bucket = config.GCS_BUCKET_NAME
    original_streamlit = sys.modules.get("streamlit")
    original_plotly = sys.modules.get("plotly")
    original_plotly_express = sys.modules.get("plotly.express")

    def fake_read_excel(*args, **kwargs):
        return pd.DataFrame(
            [
                {
                    "Code": "000001",
                    "Name": "TEST",
                    "volume_20d_avg": 100000,
                    "MAD_gap_pct": 10.0,
                    "avg_momentum": 12.0,
                    "current_price": 10000,
                    "MRAT": 1.1,
                    "momentum_1m": 3.0,
                    "momentum_3m": 5.0,
                    "momentum_6m": 7.0,
                    "momentum_12m": 9.0,
                }
            ]
        )

    def fake_read_csv(path, *args, **kwargs):
        path_str = str(path)
        if path_str.endswith("kis_bt_auto_summary.csv"):
            return pd.DataFrame([{"FinalNAV": 1.0, "CAGR": 0.1, "MDD": -0.1, "Sharpe": 1.0, "AvgTurnover": 0.2}])
        if path_str.endswith("kis_bt_auto_nav.csv"):
            return pd.DataFrame([{"date": "2026-01-31", "StrategyA": 1.0}])
        if path_str.endswith("kis_shadow_ops_summary.csv"):
            return pd.DataFrame([{"DailyCheckStatus": "GO", "DailyCheckComment": "", "HealthStatus": "OK", "Strategy": "X", "RecommendedStrategy": "X", "RecommendedStrategyMatch": 1, "AsOfDate": "2026-01-31", "RunId": "R1", "Recommendation": "HOLD", "TurnoverEstimate": 0.0, "MissingPriceCount": 0, "HoldingsCount": 1, "PortfolioRowCount": 1, "WeightSum": 1.0, "ShadowNAV": 1000000, "Cash": 0, "GrossExposure": 1.0}])
        if path_str.endswith("kis_shadow_health.csv"):
            return pd.DataFrame([{"SourceFresh": "YES", "MissingPriceCount": 0, "TurnoverEstimate": 0.0}])
        if path_str.endswith("kis_shadow_rebalance_diff.csv"):
            return pd.DataFrame([{"RunId": "R1", "Action": "HOLD", "Code": "000001", "WeightChange": 0.0}])
        if path_str.endswith("kis_shadow_nav.csv"):
            return pd.DataFrame([{"Date": "2026-01-31", "ShadowNAV": 1000000, "Cash": 0, "GrossExposure": 1.0}])
        if path_str.endswith("kis_shadow_exceptions.csv"):
            return pd.DataFrame([{"RunId": "R1", "Severity": "INFO", "Category": "None", "Metric": "None"}])
        if path_str.endswith("kis_shadow_portfolio.csv"):
            return pd.DataFrame([{"RunId": "R1", "Code": "000001", "Name": "TEST", "TargetWeight": 1.0}])
        if path_str.endswith("kis_live_readiness.csv"):
            return pd.DataFrame([{"Recommendation": "START_X", "Strategy": "X", "ReadinessTier": "A"}])
        return orig_read_csv(path, *args, **kwargs)

    pd.read_excel = fake_read_excel
    pd.read_csv = fake_read_csv
    pd.DataFrame.style = property(lambda self: _DummyStyler(self))
    config.GCS_BUCKET_NAME = None
    sys.modules["streamlit"] = fake_streamlit
    sys.modules["plotly"] = types.SimpleNamespace(express=fake_px)
    sys.modules["plotly.express"] = fake_px
    sys.modules.pop("tools.dashboards.dashboard", None)
    try:
        import tools.dashboards.dashboard as dashboard

        assert dashboard.REPO_ROOT == Path(r"C:\AI\momentum")
        _, _, summary_uri, nav_uri = dashboard.load_backtest_data()
        assert Path(summary_uri).parent == dashboard.REPO_ROOT
        assert Path(nav_uri).parent == dashboard.REPO_ROOT
        _, shadow_paths = dashboard.load_shadow_data()
        assert Path(shadow_paths["ops"]).parent == dashboard.REPO_ROOT / "backtests"
        docker_text = Path(r"C:\AI\momentum\Dockerfile.web").read_text(encoding="utf-8")
        assert "streamlit run tools/dashboards/dashboard.py" in docker_text
    finally:
        pd.read_excel = orig_read_excel
        pd.read_csv = orig_read_csv
        pd.DataFrame.style = orig_style
        config.GCS_BUCKET_NAME = orig_bucket
        if original_streamlit is None:
            sys.modules.pop("streamlit", None)
        else:
            sys.modules["streamlit"] = original_streamlit
        if original_plotly is None:
            sys.modules.pop("plotly", None)
        else:
            sys.modules["plotly"] = original_plotly
        if original_plotly_express is None:
            sys.modules.pop("plotly.express", None)
        else:
            sys.modules["plotly.express"] = original_plotly_express
