
import io
from pathlib import Path

import pandas as pd
import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKTESTS_DIR = REPO_ROOT / "backtests"
DEFAULT_PATHS = {
    "ops_summary": DEFAULT_BACKTESTS_DIR / "kis_shadow_ops_summary.csv",
    "health": DEFAULT_BACKTESTS_DIR / "kis_shadow_health.csv",
    "diff": DEFAULT_BACKTESTS_DIR / "kis_shadow_rebalance_diff.csv",
    "nav": DEFAULT_BACKTESTS_DIR / "kis_shadow_nav.csv",
    "exceptions": DEFAULT_BACKTESTS_DIR / "kis_shadow_exceptions.csv",
    "portfolio": DEFAULT_BACKTESTS_DIR / "kis_shadow_portfolio.csv",
    "live_readiness": DEFAULT_BACKTESTS_DIR / "kis_live_readiness.csv",
}
STATUS_COLOR = {"GO": "green", "REVIEW": "orange", "STOP": "red"}
HEALTH_COLOR = {"OK": "green", "WARNING": "orange", "STALE": "red", "ERROR": "red"}
SEVERITY_COLOR = {"INFO": "blue", "WARNING": "orange", "ERROR": "red"}

st.set_page_config(
    page_title="Shadow Ops Dashboard",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=60)
def _read_csv(path_str: str) -> pd.DataFrame:
    path_str = path_str.strip()
    if not path_str:
        return pd.DataFrame()
    if path_str.startswith("gs://"):
        from google.cloud import storage

        bucket_name, blob_name = _split_gcs_uri(path_str)
        client = storage.Client()
        text = client.bucket(bucket_name).blob(blob_name).download_as_text(encoding="utf-8")
        return pd.read_csv(io.StringIO(text))
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _split_gcs_uri(uri: str) -> tuple[str, str]:
    no_scheme = uri[5:]
    bucket, _, blob = no_scheme.partition("/")
    return bucket, blob


def load_optional_csv(label: str, path_str: str) -> pd.DataFrame:
    try:
        return _read_csv(path_str)
    except FileNotFoundError:
        st.warning(f"{label} ??? ????: {path_str}")
    except Exception as exc:
        st.warning(f"{label} ?? ??: {exc}")
    return pd.DataFrame()


def latest_value(df: pd.DataFrame, column: str, default=None):
    if df.empty or column not in df.columns:
        return default
    return df.iloc[0][column]


def metric_text(value, kind: str | None = None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    if kind == "pct":
        return f"{float(value):.2%}"
    if kind == "money":
        return f"{float(value):,.0f}"
    if kind == "float":
        return f"{float(value):.4f}"
    if kind == "int":
        return f"{int(value):,}"
    return str(value)


def severity_badge(value: str, palette: dict[str, str]) -> str:
    color = palette.get(str(value), "gray")
    return f":{color}[**{value}**]"


def latest_run_df(df: pd.DataFrame, latest_only: bool) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    if latest_only and "RunId" in out.columns:
        out = out[out["RunId"] == out.iloc[0]["RunId"]].copy()
    return out


def compute_change_intensity(diff_df: pd.DataFrame) -> dict[str, object]:
    if diff_df.empty:
        return {
            "TotalChangedCount": 0,
            "BuyExitCount": 0,
            "IncreaseDecreaseCount": 0,
            "MaxAbsoluteWeightChange": 0.0,
            "MaxWeightChangeCode": "N/A",
        }
    display = diff_df.copy()
    non_hold = display[display["Action"] != "HOLD"].copy() if "Action" in display.columns else display.iloc[0:0].copy()
    max_abs = 0.0
    max_code = "N/A"
    if not display.empty and "WeightChange" in display.columns:
        display["AbsWeightChange"] = display["WeightChange"].abs()
        top = display.sort_values(["AbsWeightChange", "Code"], ascending=[False, True]).head(1)
        if not top.empty:
            max_abs = float(top.iloc[0]["AbsWeightChange"])
            max_code = str(top.iloc[0].get("Code", "N/A"))
    return {
        "TotalChangedCount": int(len(non_hold)),
        "BuyExitCount": int((display["Action"].isin(["BUY", "EXIT"])).sum()) if "Action" in display.columns else 0,
        "IncreaseDecreaseCount": int((display["Action"].isin(["INCREASE", "DECREASE"])).sum()) if "Action" in display.columns else 0,
        "MaxAbsoluteWeightChange": max_abs,
        "MaxWeightChangeCode": max_code,
    }


def summarize_status_reason(ops_df: pd.DataFrame, health_df: pd.DataFrame, diff_df: pd.DataFrame) -> str | None:
    if ops_df.empty:
        return None
    row = ops_df.iloc[0]
    daily = str(row.get("DailyCheckStatus", "N/A"))
    health = str(row.get("HealthStatus", "N/A"))
    mismatch = int(row.get("RecommendedStrategyMatch", 0)) != 1
    missing_prices = float(row.get("MissingPriceCount", 0) or 0)
    turnover = float(row.get("TurnoverEstimate", 0) or 0)

    if daily == "GO":
        return None
    if health in {"STALE", "ERROR"}:
        return f"{daily} because health status is {health}"
    if mismatch:
        return f"{daily} because strategy mismatch was detected"
    if missing_prices > 0:
        return f"{daily} because missing prices were detected"
    if turnover >= 0.25:
        return f"{daily} because turnover exceeded review threshold"
    if not diff_df.empty and "Action" in diff_df.columns and (diff_df["Action"] != "HOLD").any():
        return f"{daily} because rebalance changes were detected"
    return f"{daily} because operator review is required"


def render_header(ops_df: pd.DataFrame) -> None:
    st.title("KIS Shadow Operations Dashboard")
    if ops_df.empty:
        st.error("?? ?? ??? ?? ????.")
        return
    row = ops_df.iloc[0]
    mismatch = int(row.get("RecommendedStrategyMatch", 0)) != 1
    if mismatch:
        st.warning("MISMATCH: ?? shadow ??? ?? ?? ??? ???? ????.")
    left, right = st.columns([2, 3])
    with left:
        st.markdown(f"### {severity_badge(row.get('DailyCheckStatus', 'N/A'), STATUS_COLOR)}")
        st.caption(row.get("DailyCheckComment", ""))
    with right:
        st.markdown(
            " | ".join(
                [
                    f"**DailyCheckStatus:** {severity_badge(row.get('DailyCheckStatus', 'N/A'), STATUS_COLOR)}",
                    f"**HealthStatus:** {severity_badge(row.get('HealthStatus', 'N/A'), HEALTH_COLOR)}",
                    f"**Strategy:** `{row.get('Strategy', 'N/A')}`",
                    f"**AsOfDate:** `{row.get('AsOfDate', 'N/A')}`",
                    f"**RunId:** `{row.get('RunId', 'N/A')}`",
                ]
            )
        )
        match_badge = ":green[**MATCH**]" if not mismatch else ":red[**MISMATCH**]"
        st.markdown(
            f"**Strategy Alignment:** {match_badge} | "
            f"**Recommended:** `{row.get('RecommendedStrategy', 'N/A')}`"
        )
        st.markdown(f"**Recommendation:** `{row.get('Recommendation', 'N/A')}`")


def render_kpis(ops_df: pd.DataFrame, diff_df: pd.DataFrame) -> None:
    if ops_df.empty:
        return
    row = ops_df.iloc[0]
    change = compute_change_intensity(diff_df)
    cols = st.columns(4)
    metrics = [
        ("TurnoverEstimate", metric_text(row.get("TurnoverEstimate"), "pct")),
        ("MissingPriceCount", metric_text(row.get("MissingPriceCount"), "int")),
        ("HoldingsCount", metric_text(row.get("HoldingsCount"), "int")),
        ("PortfolioRowCount", metric_text(row.get("PortfolioRowCount"), "int")),
        ("WeightSum", metric_text(row.get("WeightSum"), "pct")),
        ("ShadowNAV", metric_text(row.get("ShadowNAV"), "money")),
        ("Cash", metric_text(row.get("Cash"), "money")),
        ("GrossExposure", metric_text(row.get("GrossExposure"), "pct")),
    ]
    for idx, (label, value) in enumerate(metrics):
        cols[idx % 4].metric(label, value)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TotalChangedCount", metric_text(change["TotalChangedCount"], "int"))
    c2.metric("BuyExitCount", metric_text(change["BuyExitCount"], "int"))
    c3.metric("IncreaseDecreaseCount", metric_text(change["IncreaseDecreaseCount"], "int"))
    c4.metric("MaxAbsoluteWeightChange", metric_text(change["MaxAbsoluteWeightChange"], "pct"))
    c5.metric("MaxWeightChangeCode", str(change["MaxWeightChangeCode"]))


def render_rebalance(diff_df: pd.DataFrame, latest_only: bool) -> None:
    st.subheader("Rebalance Summary")
    if diff_df.empty:
        st.info("???? diff ??? ?? ????.")
        return
    display = latest_run_df(diff_df, latest_only=latest_only)
    counts = {action: int((display["Action"] == action).sum()) for action in ["BUY", "EXIT", "INCREASE", "DECREASE", "HOLD"]}
    cols = st.columns(5)
    for idx, action in enumerate(["BUY", "EXIT", "INCREASE", "DECREASE", "HOLD"]):
        cols[idx].metric(action, counts[action])
    if "WeightChange" in display.columns:
        display["AbsWeightChange"] = display["WeightChange"].abs()
        display = display.sort_values(["AbsWeightChange", "Code"], ascending=[False, True])
    table_cols = [
        "Code", "PrevWeight", "NewWeight", "WeightChange", "Action", "EstimatedPrice", "Notes",
    ]
    table_cols = [c for c in table_cols if c in display.columns]
    st.dataframe(display[table_cols], width="stretch", height=320)


def render_exceptions(exc_df: pd.DataFrame, latest_only: bool) -> None:
    st.subheader("Exceptions")
    if exc_df.empty:
        st.info("?? ??? ?? ????.")
        return
    display = latest_run_df(exc_df, latest_only=latest_only)
    sev_order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    display["SeverityOrder"] = display["Severity"].map(sev_order).fillna(9)
    display = display.sort_values(["SeverityOrder", "Category", "Metric"]).drop(columns=["SeverityOrder"])
    warning_count = int((display["Severity"] == "WARNING").sum()) if "Severity" in display.columns else 0
    error_count = int((display["Severity"] == "ERROR").sum()) if "Severity" in display.columns else 0
    if warning_count > 0 or error_count > 0:
        st.markdown(
            f"**Warnings:** {warning_count} | **Errors:** {error_count}"
        )
    else:
        st.caption("Warnings: 0 | Errors: 0")

    def color_severity(value: str) -> str:
        color = {"ERROR": "#ffdddd", "WARNING": "#fff1cc", "INFO": "#ddeeff"}.get(str(value), "")
        return f"background-color: {color}"

    st.dataframe(display.style.map(color_severity, subset=["Severity"]), width="stretch", height=220)


def render_nav(nav_df: pd.DataFrame, latest_only: bool) -> None:
    st.subheader("Shadow NAV")
    if nav_df.empty:
        st.info("NAV ??? ?? ????.")
        return
    display = nav_df.copy()
    if "Date" in display.columns:
        display["Date"] = pd.to_datetime(display["Date"], errors="coerce")
        display = display.sort_values("Date")
    if latest_only and len(display) > 60:
        display = display.tail(60)
    if {"Date", "ShadowNAV"}.issubset(display.columns):
        nav_chart = display.set_index("Date")[["ShadowNAV"]]
        st.line_chart(nav_chart, height=260)
    c1, c2 = st.columns(2)
    with c1:
        if {"Date", "Cash"}.issubset(display.columns):
            st.line_chart(display.set_index("Date")[["Cash"]], height=180)
    with c2:
        if {"Date", "GrossExposure"}.issubset(display.columns):
            st.line_chart(display.set_index("Date")[["GrossExposure"]], height=180)


def render_portfolio(port_df: pd.DataFrame, latest_only: bool) -> None:
    st.subheader("Target Portfolio")
    if port_df.empty:
        st.info("????? ??? ?? ????.")
        return
    display = port_df.copy()
    if latest_only and "RunId" in display.columns:
        display = display[display["RunId"] == display.iloc[0]["RunId"]].copy()
    if "TargetWeight" in display.columns:
        display = display.sort_values(["TargetWeight", "Code"], ascending=[False, True])
    table_cols = [
        "Code", "Name", "AssetType", "TargetWeight", "CurrentPrice", "SignalRank", "Score", "RegimeState", "Notes",
    ]
    table_cols = [c for c in table_cols if c in display.columns]
    st.dataframe(display[table_cols], width="stretch", height=420)


def render_sidebar() -> dict[str, str]:
    st.sidebar.header("CSV Paths")
    if st.sidebar.button("Refresh"):
        st.cache_data.clear()
    paths = {}
    for key, default in DEFAULT_PATHS.items():
        paths[key] = st.sidebar.text_input(key, value=str(default))
    st.sidebar.markdown("---")
    st.sidebar.caption("???? ?? backtests ?????. gs:// ??? ?????.")
    return paths


def render_recent_history(ops_df: pd.DataFrame, health_df: pd.DataFrame) -> None:
    st.markdown("**Recent Run History**")
    if ops_df.empty:
        st.info("?? ?? ??? ??? ? ????.")
        return
    ops_view = ops_df.copy()
    if "RunStartedAt" in ops_view.columns:
        ops_view["RunStartedAt"] = pd.to_datetime(ops_view["RunStartedAt"], errors="coerce")
        ops_view = ops_view.sort_values("RunStartedAt", ascending=False)
    if not health_df.empty:
        health_cols = [c for c in ["RunId", "HealthStatus"] if c in health_df.columns]
        if "RunId" in health_cols and "HealthStatus" in health_cols and "HealthStatus" not in ops_view.columns:
            ops_view = ops_view.merge(health_df[health_cols].drop_duplicates(), on="RunId", how="left")
    cols = [c for c in ["RunStartedAt", "RunId", "DailyCheckStatus", "HealthStatus", "Strategy", "TurnoverEstimate"] if c in ops_view.columns]
    history = ops_view[cols].head(5).copy()
    if "RunStartedAt" in history.columns:
        history["RunStartedAt"] = history["RunStartedAt"].dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    def color_status(value: str) -> str:
        color = {"STOP": "#ffdddd", "REVIEW": "#fff1cc", "GO": "#ddffdd", "OK": "#ddffdd", "WARNING": "#fff1cc", "STALE": "#ffdddd", "ERROR": "#ffdddd"}.get(str(value), "")
        return f"background-color: {color}"

    subset = [c for c in ["DailyCheckStatus", "HealthStatus"] if c in history.columns]
    styled = history.style
    if subset:
        styled = styled.map(color_status, subset=subset)
    st.dataframe(styled, width="stretch", height=220)


def main() -> None:
    paths = render_sidebar()
    latest_only = st.sidebar.checkbox("Latest run only", value=True)

    ops_df = load_optional_csv("shadow ops summary", paths["ops_summary"])
    health_df = load_optional_csv("shadow health", paths["health"])
    diff_df = load_optional_csv("shadow rebalance diff", paths["diff"])
    nav_df = load_optional_csv("shadow nav", paths["nav"])
    exc_df = load_optional_csv("shadow exceptions", paths["exceptions"])
    port_df = load_optional_csv("shadow portfolio", paths["portfolio"])
    live_df = load_optional_csv("live readiness", paths["live_readiness"])

    render_header(ops_df)
    latest_diff_df = latest_run_df(diff_df, latest_only=latest_only)
    render_kpis(ops_df, latest_diff_df)
    st.info(
        "Daily read order: 1) GO/REVIEW/STOP  2) MATCH/MISMATCH  "
        "3) MissingPriceCount and TurnoverEstimate  4) Exceptions  5) Rebalance changes"
    )
    reason = summarize_status_reason(ops_df, health_df, latest_diff_df)
    if reason:
        st.warning(reason)
    render_recent_history(ops_df, health_df)

    if not health_df.empty:
        row = health_df.iloc[0]
        st.caption(
            f"Health detail: SourceFresh={row.get('SourceFresh', 'N/A')}, "
            f"MissingPriceCount={row.get('MissingPriceCount', 'N/A')}, "
            f"TurnoverEstimate={metric_text(row.get('TurnoverEstimate'), 'pct')}"
        )
    if not live_df.empty and "Recommendation" in live_df.columns:
        recommended = live_df.loc[live_df["Recommendation"].astype(str).str.contains("START_", na=False)].head(1)
        if not recommended.empty:
            st.caption(
                f"Paper-trading recommendation source: {recommended.iloc[0].get('Strategy', 'N/A')} / "
                f"{recommended.iloc[0].get('ReadinessTier', 'N/A')}"
            )

    tab1, tab2, tab3, tab4 = st.tabs(["Exceptions", "Rebalance", "NAV", "Portfolio"])
    with tab1:
        render_exceptions(exc_df, latest_only=latest_only)
    with tab2:
        render_rebalance(diff_df, latest_only=latest_only)
    with tab3:
        render_nav(nav_df, latest_only=latest_only)
    with tab4:
        render_portfolio(port_df, latest_only=latest_only)


if __name__ == "__main__":
    main()
