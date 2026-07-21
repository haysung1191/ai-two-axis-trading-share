import glob
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import config

REPO_ROOT = Path(__file__).resolve().parents[2]

st.set_page_config(
    page_title="Momentum Screener Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

STATUS_COLOR = {"GO": "green", "REVIEW": "orange", "STOP": "red"}
HEALTH_COLOR = {"OK": "green", "WARNING": "orange", "STALE": "red", "ERROR": "red"}
SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    mom_cols = ["momentum_1m", "momentum_3m", "momentum_6m", "momentum_12m"]
    for col in mom_cols:
        if col not in out.columns:
            out[col] = 0.0

    # Score components
    pos_count = (out[mom_cols] > 0).sum(axis=1)  # 0..4
    score_momentum_consistency = pos_count * 10  # 0..40

    avg_mom = out["avg_momentum"].clip(lower=-20, upper=80)
    score_avg_momentum = ((avg_mom + 20) / 100 * 25)  # 0..25

    # Favor moderate trend strength; too far above MA can be unstable.
    mrat_dist = (out["MRAT"] - 1.35).abs()
    score_mrat = (20 - (mrat_dist * 25)).clip(lower=0, upper=20)  # 0..20

    # Prefer positive but not extreme MAD gap.
    mad_gap = out["MAD_gap_pct"]
    score_mad = (15 - (mad_gap - 20).abs() * 0.25).clip(lower=0, upper=15)  # 0..15

    out["buy_score"] = (score_momentum_consistency + score_avg_momentum + score_mrat + score_mad).round(1)

    # Overheat warning
    out["overheat_warning"] = "정상"
    out.loc[(out["MAD_gap_pct"] >= 60) | (out["MRAT"] >= 1.9), "overheat_warning"] = "주의"
    out.loc[(out["MAD_gap_pct"] >= 100) | (out["MRAT"] >= 2.3) | (out["momentum_1m"] >= 45), "overheat_warning"] = "과열"

    return out


@st.cache_data(ttl=300)
def load_latest_data(mode="STOCK"):
    prefix = "etf_results_" if mode == "ETF" else "momentum_results_"
    bucket_name = config.GCS_BUCKET_NAME

    def load_local():
        data_dir = str(REPO_ROOT)
        files = glob.glob(os.path.join(data_dir, f"{prefix}*.xlsx"))
        if not files:
            return None, None
        latest_file = max(files, key=os.path.getmtime)
        file_date = datetime.fromtimestamp(os.path.getmtime(latest_file)).strftime("%Y-%m-%d %H:%M")
        try:
            return pd.read_excel(latest_file), file_date
        except Exception as e:
            st.error(f"Error loading local file: {e}")
            return None, None

    if bucket_name:
        try:
            from google.cloud import storage

            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(prefix=prefix))
            if blobs:
                latest_blob = max(blobs, key=lambda b: b.updated)
                file_date = latest_blob.updated.strftime("%Y-%m-%d %H:%M")
                file_uri = f"gs://{bucket_name}/{latest_blob.name}"
                return pd.read_excel(file_uri), file_date
        except Exception as e:
            st.warning(f"GCS read failed, trying local files: {e}")

    return load_local()


@st.cache_data(ttl=300)
def load_backtest_data():
    bucket_name = config.GCS_BUCKET_NAME
    summary_uri = None
    nav_uri = None

    if bucket_name:
        summary_uri = f"gs://{bucket_name}/backtests/kis_bt_auto_summary.csv"
        nav_uri = f"gs://{bucket_name}/backtests/kis_bt_auto_nav.csv"
    else:
        base_dir = str(REPO_ROOT)
        summary_uri = os.path.join(base_dir, "kis_bt_auto_summary.csv")
        nav_uri = os.path.join(base_dir, "kis_bt_auto_nav.csv")

    try:
        summary_df = pd.read_csv(summary_uri)
        nav_df = pd.read_csv(nav_uri)
        if "date" in nav_df.columns:
            nav_df["date"] = pd.to_datetime(nav_df["date"])
        return summary_df, nav_df, summary_uri, nav_uri
    except Exception:
        return None, None, summary_uri, nav_uri


@st.cache_data(ttl=300)
def load_shadow_data():
    bucket_name = config.GCS_BUCKET_NAME

    def resolve_path(filename: str) -> str:
        if bucket_name:
            return f"gs://{bucket_name}/backtests/{filename}"
        base_dir = str(REPO_ROOT)
        return os.path.join(base_dir, "backtests", filename)

    files = {
        "ops": "kis_shadow_ops_summary.csv",
        "health": "kis_shadow_health.csv",
        "diff": "kis_shadow_rebalance_diff.csv",
        "nav": "kis_shadow_nav.csv",
        "exceptions": "kis_shadow_exceptions.csv",
        "portfolio": "kis_shadow_portfolio.csv",
        "readiness": "kis_live_readiness.csv",
    }
    loaded = {}
    paths = {key: resolve_path(name) for key, name in files.items()}
    for key, path in paths.items():
        try:
            df = pd.read_csv(path)
            if key == "nav" and "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            loaded[key] = df
        except Exception:
            loaded[key] = None
    return loaded, paths


def format_metric(value, kind: str | None = None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if kind == "pct":
        return f"{float(value):.2%}"
    if kind == "money":
        return f"{float(value):,.0f}"
    if kind == "int":
        return f"{int(value):,}"
    return str(value)


def status_badge(value: str, palette: dict[str, str]) -> str:
    color = palette.get(str(value), "gray")
    return f":{color}[**{value}**]"


st.sidebar.header("필터 옵션")
screener_mode = st.sidebar.radio("스크리너 모드", options=["개별종목", "ETF"], index=0)
mode_key = "ETF" if screener_mode == "ETF" else "STOCK"

df, last_updated = load_latest_data(mode=mode_key)

st.title("KIS 모멘텀 & MAD 스크리너 대시보드")

if df is None:
    st.warning("결과 파일을 찾을 수 없습니다. 먼저 스크리너를 실행하세요.")
    st.stop()

required_cols = ["volume_20d_avg", "MAD_gap_pct", "avg_momentum", "Name", "Code", "current_price", "MRAT"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"필수 컬럼이 없습니다: {', '.join(missing)}")
    st.stop()

df = add_signals(df)

min_volume = st.sidebar.number_input("최소 20일 평균 거래량", min_value=0, value=50000, step=10000)
min_mad, max_mad = st.sidebar.slider(
    "MAD 괴리율(%) 범위",
    float(df["MAD_gap_pct"].min()),
    float(df["MAD_gap_pct"].max()),
    (0.0, float(df["MAD_gap_pct"].max())),
)
sort_by_score = st.sidebar.checkbox("매수 후보 점수순 정렬", value=True)

filtered_df = df[
    (df["volume_20d_avg"] >= min_volume)
    & (df["MAD_gap_pct"] >= min_mad)
    & (df["MAD_gap_pct"] <= max_mad)
].copy()
if sort_by_score:
    filtered_df = filtered_df.sort_values(by=["buy_score", "avg_momentum"], ascending=[False, False])
filtered_df = filtered_df.reset_index(drop=True)
filtered_df.index = filtered_df.index + 1

st.markdown(f"**마지막 업데이트:** `{last_updated}` | **전체 종목 수:** `{len(df)}`")
st.caption("매수점수(0-100): 모멘텀 일관성 + 평균 모멘텀 + MRAT 안정성 + MAD 과열 회피를 합산한 참고 지표")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("조건부합 종목 수", f"{len(filtered_df)}")
with col2:
    top_mad = filtered_df["MAD_gap_pct"].max() if not filtered_df.empty else 0
    st.metric("최고 MAD 괴리율", f"{top_mad:.2f}%")
with col3:
    top_stock = filtered_df.iloc[0]["Name"] if not filtered_df.empty else "N/A"
    st.metric("현재 1위", top_stock)
with col4:
    top_score = filtered_df["buy_score"].max() if not filtered_df.empty else 0
st.metric("최고 매수점수", f"{top_score:.1f}")

st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["데이터 테이블", "상세 차트", "백테스트", "운영 모니터링"])

with tab1:
    display_cols = [
        "Code",
        "Name",
        "buy_score",
        "overheat_warning",
        "MAD_gap_pct",
        "MRAT",
        "momentum_1m",
        "momentum_3m",
        "momentum_6m",
        "momentum_12m",
        "avg_momentum",
        "current_price",
        "volume_20d_avg",
    ]
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[display_cols]

    st.dataframe(
        display_df.style.format(
            {
                "buy_score": "{:.1f}",
                "MAD_gap_pct": "{:.2f}%",
                "MRAT": "{:.3f}",
                "momentum_1m": "{:.2f}%",
                "momentum_3m": "{:.2f}%",
                "momentum_6m": "{:.2f}%",
                "momentum_12m": "{:.2f}%",
                "avg_momentum": "{:.2f}%",
                "current_price": "{:,.0f}",
                "volume_20d_avg": "{:,.0f}",
            }
        ),
        width="stretch",
        height=600,
    )

with tab2:
    if filtered_df.empty:
        st.info("조건에 맞는 종목이 없습니다.")
    else:
        top_100 = filtered_df.head(100)
        fig1 = px.scatter(
            top_100,
            x="momentum_1m",
            y="momentum_3m",
            color="MAD_gap_pct",
            hover_name="Name",
            hover_data=["Code", "current_price"],
            labels={
                "momentum_1m": "1개월 수익률(%)",
                "momentum_3m": "3개월 수익률(%)",
                "MAD_gap_pct": "MAD 괴리율",
            },
            color_continuous_scale="Viridis",
        )
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, width="stretch")

        st.markdown("---")

        top_30 = filtered_df.head(30)
        fig2 = px.bar(
            top_30,
            x="Name",
            y="volume_20d_avg",
            color="MAD_gap_pct",
            labels={"volume_20d_avg": "20일 평균 거래량", "Name": "종목명"},
            color_continuous_scale="Blues",
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, width="stretch")

with tab3:
    bt_summary, bt_nav, summary_uri, nav_uri = load_backtest_data()
    st.caption("주의: 현재 백테스트는 생존편향/유니버스 고정 편향이 있을 수 있어 실거래 성과보다 높게 나올 수 있습니다.")
    if bt_summary is None or bt_nav is None:
        st.info("백테스트 결과 파일이 아직 없습니다.")
        st.caption(f"찾는 파일: {summary_uri}, {nav_uri}")
    else:
        st.markdown("**전략 성과 요약**")
        st.dataframe(
            bt_summary.style.format(
                {
                    "FinalNAV": "{:.4f}",
                    "CAGR": "{:.2%}",
                    "MDD": "{:.2%}",
                    "Sharpe": "{:.3f}",
                    "AvgTurnover": "{:.3f}",
                }
            ),
            width="stretch",
        )

        nav_cols = [c for c in bt_nav.columns if c != "date"]
        if "date" in bt_nav.columns and nav_cols:
            nav_long = bt_nav.melt(id_vars=["date"], value_vars=nav_cols, var_name="Strategy", value_name="NAV")
            fig3 = px.line(nav_long, x="date", y="NAV", color="Strategy", labels={"date": "날짜", "NAV": "누적자산(NAV)"})
            fig3.update_layout(height=500)
            st.plotly_chart(fig3, width="stretch")

with tab4:
    shadow, shadow_paths = load_shadow_data()
    ops_df = shadow["ops"]
    health_df = shadow["health"]
    diff_df = shadow["diff"]
    nav_df = shadow["nav"]
    exceptions_df = shadow["exceptions"]
    portfolio_df = shadow["portfolio"]
    readiness_df = shadow["readiness"]

    st.caption("일일 페이퍼 운영 모니터링 탭입니다. 주문 실행은 하지 않습니다.")

    if ops_df is None or ops_df.empty:
        st.warning("운영 요약 파일이 없습니다.")
        st.caption(f"찾는 파일: {shadow_paths['ops']}")
    else:
        latest_only = st.checkbox("최신 실행만 보기", value=True, key="shadow_latest_only")
        ops_view = ops_df.copy()
        if latest_only and "RunId" in ops_view.columns:
            ops_view = ops_view[ops_view["RunId"] == ops_view.iloc[0]["RunId"]]
        ops_row = ops_view.iloc[0]

        left, right = st.columns([2, 3])
        with left:
            st.markdown(f"### {status_badge(ops_row.get('DailyCheckStatus', 'N/A'), STATUS_COLOR)}")
            st.caption(ops_row.get("DailyCheckComment", ""))
        with right:
            st.markdown(
                " | ".join(
                    [
                        f"**Health:** {status_badge(ops_row.get('HealthStatus', 'N/A'), HEALTH_COLOR)}",
                        f"**전략:** `{ops_row.get('Strategy', 'N/A')}`",
                        f"**추천 전략:** `{ops_row.get('RecommendedStrategy', 'N/A')}`",
                        f"**일치 여부:** `{ops_row.get('RecommendedStrategyMatch', 'N/A')}`",
                        f"**기준일:** `{ops_row.get('AsOfDate', 'N/A')}`",
                        f"**실행 ID:** `{ops_row.get('RunId', 'N/A')}`",
                    ]
                )
            )
            st.markdown(f"**운영 권고:** `{ops_row.get('Recommendation', 'N/A')}`")

        k1, k2, k3, k4 = st.columns(4)
        metrics = [
            ("회전율 추정", format_metric(ops_row.get("TurnoverEstimate"), "pct")),
            ("누락 가격 수", format_metric(ops_row.get("MissingPriceCount"), "int")),
            ("보유 종목 수", format_metric(ops_row.get("HoldingsCount"), "int")),
            ("포트폴리오 행 수", format_metric(ops_row.get("PortfolioRowCount"), "int")),
            ("비중 합계", format_metric(ops_row.get("WeightSum"), "pct")),
            ("가상 NAV", format_metric(ops_row.get("ShadowNAV"), "money")),
            ("현금", format_metric(ops_row.get("Cash"), "money")),
            ("총 익스포저", format_metric(ops_row.get("GrossExposure"), "pct")),
        ]
        for idx, (label, value) in enumerate(metrics):
            [k1, k2, k3, k4][idx % 4].metric(label, value)

        if health_df is not None and not health_df.empty:
            hrow = health_df.iloc[0]
            st.caption(
                f"상세 상태: 최신성={hrow.get('SourceFresh', 'N/A')}, "
                f"누락 가격 수={hrow.get('MissingPriceCount', 'N/A')}, "
                f"회전율 추정={format_metric(hrow.get('TurnoverEstimate'), 'pct')}"
            )
        if readiness_df is not None and not readiness_df.empty and "Recommendation" in readiness_df.columns:
            recommended = readiness_df.loc[
                readiness_df["Recommendation"].astype(str).str.contains("START_", na=False)
            ].head(1)
            if not recommended.empty:
                st.caption(
                    f"현재 추천 페이퍼 전략: {recommended.iloc[0].get('Strategy', 'N/A')} / "
                    f"{recommended.iloc[0].get('ReadinessTier', 'N/A')}"
                )

        st.markdown("---")
        st.markdown("**리밸런스 요약**")
        if diff_df is None or diff_df.empty:
            st.info("리밸런스 변경 파일이 없습니다.")
            st.caption(f"찾는 파일: {shadow_paths['diff']}")
        else:
            diff_view = diff_df.copy()
            if latest_only and "RunId" in diff_view.columns:
                diff_view = diff_view[diff_view["RunId"] == ops_row.get("RunId")]
            diff_counts = {action: int((diff_view["Action"] == action).sum()) for action in ["BUY", "EXIT", "INCREASE", "DECREASE", "HOLD"]}
            d1, d2, d3, d4, d5 = st.columns(5)
            d1.metric("신규 편입", diff_counts["BUY"])
            d2.metric("전량 제외", diff_counts["EXIT"])
            d3.metric("비중 확대", diff_counts["INCREASE"])
            d4.metric("비중 축소", diff_counts["DECREASE"])
            d5.metric("유지", diff_counts["HOLD"])

            diff_view["AbsWeightChange"] = diff_view["WeightChange"].abs()
            diff_view = diff_view.sort_values(["AbsWeightChange", "Code"], ascending=[False, True])
            st.dataframe(
                diff_view[[c for c in ["Code", "PrevWeight", "NewWeight", "WeightChange", "Action", "EstimatedPrice", "Notes"] if c in diff_view.columns]],
                width="stretch",
                height=260,
            )

        st.markdown("---")
        st.markdown("**예외 및 경고**")
        if exceptions_df is None or exceptions_df.empty:
            st.info("예외 요약 파일이 없습니다.")
            st.caption(f"찾는 파일: {shadow_paths['exceptions']}")
        else:
            exc_view = exceptions_df.copy()
            if latest_only and "RunId" in exc_view.columns:
                exc_view = exc_view[exc_view["RunId"] == ops_row.get("RunId")]
            exc_view["SeverityOrder"] = exc_view["Severity"].map(SEVERITY_ORDER).fillna(9)
            exc_view = exc_view.sort_values(["SeverityOrder", "Category", "Metric"]).drop(columns=["SeverityOrder"])

            def color_severity(value):
                color = {"ERROR": "#ffdddd", "WARNING": "#fff1cc", "INFO": "#ddeeff"}.get(str(value), "")
                return f"background-color: {color}"

            st.dataframe(
                exc_view.style.map(color_severity, subset=["Severity"]),
                width="stretch",
                height=220,
            )

        st.markdown("---")
        st.markdown("**가상 NAV 추이**")
        if nav_df is None or nav_df.empty:
            st.info("가상 NAV 파일이 없습니다.")
            st.caption(f"찾는 파일: {shadow_paths['nav']}")
        else:
            nav_view = nav_df.copy().sort_values("Date") if "Date" in nav_df.columns else nav_df.copy()
            if latest_only and len(nav_view) > 60:
                nav_view = nav_view.tail(60)
            if {"Date", "ShadowNAV"}.issubset(nav_view.columns):
                st.line_chart(nav_view.set_index("Date")[["ShadowNAV"]], height=240)
            n1, n2 = st.columns(2)
            with n1:
                if {"Date", "Cash"}.issubset(nav_view.columns):
                    st.line_chart(nav_view.set_index("Date")[["Cash"]], height=160)
            with n2:
                if {"Date", "GrossExposure"}.issubset(nav_view.columns):
                    st.line_chart(nav_view.set_index("Date")[["GrossExposure"]], height=160)

        st.markdown("---")
        st.markdown("**목표 포트폴리오**")
        if portfolio_df is None or portfolio_df.empty:
            st.info("목표 포트폴리오 파일이 없습니다.")
            st.caption(f"찾는 파일: {shadow_paths['portfolio']}")
        else:
            port_view = portfolio_df.copy()
            if latest_only and "RunId" in port_view.columns:
                port_view = port_view[port_view["RunId"] == ops_row.get("RunId")]
            port_view = port_view.sort_values(["TargetWeight", "Code"], ascending=[False, True])
            st.dataframe(
                port_view[[c for c in ["Code", "Name", "AssetType", "TargetWeight", "CurrentPrice", "SignalRank", "Score", "RegimeState", "Notes"] if c in port_view.columns]],
                width="stretch",
                height=380,
            )

st.markdown("---")
st.caption("Developed by Antigravity Assistant | Data source: KIS Open API")
