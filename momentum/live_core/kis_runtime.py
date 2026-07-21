from __future__ import annotations

import os
from datetime import datetime
from typing import Callable

import config
from live_core.kis_screening_service import run_default_screening


def resolve_etf_mode(env: dict[str, str] | None = None) -> bool:
    env = env or os.environ
    return env.get("SCREENER_MODE", "STOCK").upper() == "ETF"


def build_output_filename(etf_mode: bool, now: datetime | None = None) -> str:
    now = now or datetime.now()
    prefix = "etf_results" if etf_mode else "momentum_results"
    return f"{prefix}_{now.strftime('%Y%m%d_%H%M')}.xlsx"


def save_screening_results(
    df,
    *,
    etf_mode: bool,
    env: dict[str, str] | None = None,
    config_module=config,
    now: datetime | None = None,
) -> str:
    env = env or os.environ
    filename = build_output_filename(etf_mode=etf_mode, now=now)
    use_gcs = bool(getattr(config_module, "GCS_BUCKET_NAME", None))

    if use_gcs:
        filepath = f"gs://{config_module.GCS_BUCKET_NAME}/{filename}"
        try:
            df.to_excel(filepath, index=False)
            print(f"\n결과가 GCS에 저장되었습니다: {filepath}")
            return filepath
        except Exception as exc:
            print(f"\nGCS 저장 실패, 로컬 저장으로 전환합니다: {exc}")

    desktop = os.path.join(str(env["USERPROFILE"]), "Desktop")
    filepath = os.path.join(desktop, filename)
    df.to_excel(filepath, index=False)
    print(f"\n결과가 저장되었습니다: {filepath}")
    return filepath


def run_screener_cli(
    *,
    screening_runner: Callable[..., object] = run_default_screening,
    env: dict[str, str] | None = None,
    config_module=config,
    now: datetime | None = None,
):
    env = env or os.environ
    etf_mode = resolve_etf_mode(env)

    print("====================================")
    print("KIS API ETF 모멘텀 스크리너 시작" if etf_mode else "KIS API 모멘텀 스크리너 시작")

    try:
        df = screening_runner(etf_mode=etf_mode, config_module=config_module)
    except Exception as exc:
        print(f"API 초기화 실패: {exc}")
        print(".env 파일의 APP_KEY, APP_SECRET을 확인해 주세요.")
        return None

    if df is None or df.empty:
        print("스크리닝 결과가 없습니다.")
        return None

    return save_screening_results(
        df,
        etf_mode=etf_mode,
        env=env,
        config_module=config_module,
        now=now,
    )
