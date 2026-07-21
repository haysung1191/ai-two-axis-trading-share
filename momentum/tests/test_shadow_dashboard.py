from pathlib import Path
import sys
import types


def test_shadow_dashboard_defaults_point_to_repo_backtests() -> None:
    fake_streamlit = types.SimpleNamespace(
        set_page_config=lambda **kwargs: None,
        cache_data=lambda ttl=None: (lambda fn: fn),
    )
    original_streamlit = sys.modules.get("streamlit")
    sys.modules["streamlit"] = fake_streamlit
    try:
        import tools.dashboards.shadow_dashboard as dashboard

        expected = Path(r"C:\AI\momentum\backtests")
        assert dashboard.DEFAULT_BACKTESTS_DIR == expected
        assert dashboard.DEFAULT_PATHS["ops_summary"] == expected / "kis_shadow_ops_summary.csv"
    finally:
        if original_streamlit is None:
            sys.modules.pop("streamlit", None)
        else:
            sys.modules["streamlit"] = original_streamlit
