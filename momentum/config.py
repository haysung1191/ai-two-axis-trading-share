import os
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

CANO = os.getenv("KIS_CANO")
ACNT_PRDT_CD = os.getenv("KIS_ACNT_PRDT_CD")

ENV = os.getenv("KIS_ENV", "MOCK")

if ENV == "PROD":
    BASE_URL = "https://openapi.koreainvestment.com:9443"
else:
    BASE_URL = "https://openapivts.koreainvestment.com:29443"

DOMESTIC_FRACTIONAL_ORDER_PATH = os.getenv("KIS_DOMESTIC_FRACTIONAL_ORDER_PATH", "").strip()
DOMESTIC_FRACTIONAL_BUY_TR_ID = os.getenv("KIS_DOMESTIC_FRACTIONAL_BUY_TR_ID", "").strip()
DOMESTIC_FRACTIONAL_SELL_TR_ID = os.getenv("KIS_DOMESTIC_FRACTIONAL_SELL_TR_ID", "").strip()
DOMESTIC_FRACTIONAL_ORDER_DVSN = os.getenv("KIS_DOMESTIC_FRACTIONAL_ORDER_DVSN", "01").strip()

_gcs_bucket = os.getenv("GCS_BUCKET_NAME", "").strip()
GCS_BUCKET_NAME = _gcs_bucket if _gcs_bucket and _gcs_bucket.lower() not in {"none", "null"} else None
