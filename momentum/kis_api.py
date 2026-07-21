import json
import os
from datetime import datetime, timedelta

import requests

import config


class KISApi:
    @property
    def domestic_fractional_orders_supported(self):
        return bool(
            config.DOMESTIC_FRACTIONAL_ORDER_PATH
            and config.DOMESTIC_FRACTIONAL_BUY_TR_ID
            and config.DOMESTIC_FRACTIONAL_SELL_TR_ID
        )


    TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".token_cache.json")

    def __init__(self):
        self.base_url = config.BASE_URL
        self.app_key = config.APP_KEY
        self.app_secret = config.APP_SECRET
        self.access_token = None
        missing = []
        if not self.app_key:
            missing.append("KIS_APP_KEY")
        if not self.app_secret:
            missing.append("KIS_APP_SECRET")
        if not config.CANO:
            missing.append("KIS_CANO")
        if not config.ACNT_PRDT_CD:
            missing.append("KIS_ACNT_PRDT_CD")
        if missing:
            raise ValueError(f"missing KIS credentials: {', '.join(missing)}")
        self._load_or_refresh_token()

    def _read_local_cache(self):
        if not os.path.exists(self.TOKEN_FILE):
            return {}
        try:
            with open(self.TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_local_cache(self, cache_data):
        with open(self.TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

    def _read_gcs_cache(self):
        from google.cloud import storage

        storage_client = storage.Client()
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(".token_cache.json")
        if not blob.exists():
            return {}
        return json.loads(blob.download_as_string())

    def _write_gcs_cache(self, cache_data):
        from google.cloud import storage

        storage_client = storage.Client()
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(".token_cache.json")
        blob.upload_from_string(json.dumps(cache_data))

    def _load_or_refresh_token(self):
        import time

        use_gcs = bool(getattr(config, "GCS_BUCKET_NAME", None))
        cache = {}

        if use_gcs:
            try:
                cache = self._read_gcs_cache()
                if cache:
                    print("토큰 캐시 로드 완료 (GCS)")
            except Exception as e:
                print(f"GCS 토큰 캐시 로드 실패, 로컬 캐시로 전환: {e}")
                cache = self._read_local_cache()
        else:
            cache = self._read_local_cache()

        if cache and time.time() - cache.get("timestamp", 0) < 86400:
            self.access_token = cache.get("token")
            if self.access_token:
                print("캐시된 토큰 로드 완료")
                return

        self._request_token()

    def _request_token(self):
        import time

        print("토큰 발급 중...")
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=15)
        if res.status_code != 200:
            print("토큰 발급 실패:", res.status_code, res.text)
            raise Exception("Access Token Error")

        self.access_token = res.json().get("access_token")
        cache_data = {"token": self.access_token, "timestamp": time.time()}

        use_gcs = bool(getattr(config, "GCS_BUCKET_NAME", None))
        if use_gcs:
            try:
                self._write_gcs_cache(cache_data)
                print("토큰 발급 완료 (GCS 캐시 저장)")
                return
            except Exception as e:
                print(f"GCS 토큰 캐시 저장 실패, 로컬 캐시로 전환: {e}")

        self._write_local_cache(cache_data)
        print("토큰 발급 완료 (로컬 캐시 저장)")

    def get_headers(self, tr_id):
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def _request_hashkey(self, payload):
        url = f"{self.base_url}/uapi/hashkey"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        if res.status_code != 200:
            raise RuntimeError(f"hashkey request failed: status={res.status_code} body={res.text[:240]}")
        hashkey = res.json().get("HASH")
        if not hashkey:
            raise RuntimeError(f"hashkey missing in response: {res.text[:240]}")
        return hashkey

    def _request(self, method, path, tr_id, *, params=None, payload=None, need_hashkey=False):
        url = f"{self.base_url}{path}"
        method_upper = method.upper()

        def send_once():
            headers = self.get_headers(tr_id)
            if need_hashkey and payload is not None:
                headers["hashkey"] = self._request_hashkey(payload)
            if method_upper == "GET":
                return requests.get(url, headers=headers, params=params, timeout=15)
            return requests.post(url, headers=headers, data=json.dumps(payload or {}), timeout=15)

        res = send_once()
        if res.status_code != 200 and self._response_is_expired_token(res):
            self._request_token()
            res = send_once()

        if res.status_code != 200:
            raise RuntimeError(f"KIS request failed path={path} status={res.status_code} body={res.text[:240]}")

        body = res.json()
        if self._body_is_expired_token(body):
            self._request_token()
            res = send_once()
            if res.status_code != 200:
                raise RuntimeError(f"KIS request failed path={path} status={res.status_code} body={res.text[:240]}")
            body = res.json()
        if body.get("rt_cd") not in (None, "0"):
            raise RuntimeError(
                f"KIS business error path={path} tr_id={tr_id} rt_cd={body.get('rt_cd')} "
                f"msg_cd={body.get('msg_cd')} msg1={body.get('msg1')}"
            )
        return body

    @staticmethod
    def _body_is_expired_token(body):
        return isinstance(body, dict) and str(body.get("msg_cd") or "").strip().upper() == "EGW00123"

    @classmethod
    def _response_is_expired_token(cls, response):
        try:
            body = response.json()
        except Exception:
            try:
                body = json.loads(response.text)
            except Exception:
                return "EGW00123" in str(getattr(response, "text", ""))
        return cls._body_is_expired_token(body)

    def get_domestic_quote(self, symbol):
        body = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            "FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
            },
        )
        output = body.get("output", {}) or {}
        price = output.get("stck_prpr") or output.get("stck_clpr")
        if price in (None, "", "0"):
            raise RuntimeError(f"domestic quote missing price for {symbol}")
        return {
            "symbol": symbol,
            "market": "KR",
            "price": float(price),
            "raw": output,
        }

    def get_overseas_quote(self, exchange_code, symbol):
        body = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/price",
            "HHDFS00000300",
            params={
                "AUTH": "",
                "EXCD": exchange_code,
                "SYMB": symbol,
            },
        )
        output = body.get("output", {}) or {}
        price = output.get("last") or output.get("ovrs_nmix_prpr") or output.get("base")
        if price in (None, "", "0"):
            raise RuntimeError(f"overseas quote missing price for {symbol} on {exchange_code}")
        return {
            "symbol": symbol,
            "market": "US",
            "exchange_code": exchange_code,
            "price": float(price),
            "raw": output,
        }

    def get_overseas_quote_detail(self, exchange_code, symbol):
        body = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/price-detail",
            "HHDFS76200200",
            params={
                "AUTH": "",
                "EXCD": exchange_code,
                "SYMB": symbol,
            },
        )
        return body.get("output", {}) or {}

    def get_overseas_daily_prices(self, exchange_code, symbol, *, base_date="", period="0", adjusted="1"):
        body = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/dailyprice",
            "HHDFS76240000",
            params={
                "AUTH": "",
                "EXCD": exchange_code,
                "SYMB": symbol,
                "GUBN": period,
                "BYMD": base_date,
                "MODP": adjusted,
            },
        )
        return body.get("output2", []) or body.get("output", []) or []

    def search_overseas_stocks(self, exchange_code, *, market_trigger="000000", name="", market_type="00"):
        body = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/inquire-search",
            "HHDFS76410000",
            params={
                "AUTH": "",
                "EXCD": exchange_code,
                "CO_YN_PRICECUR": "",
                "CO_ST_PRICECUR": "",
                "CO_EN_PRICECUR": "",
                "CO_YN_RATE": "",
                "CO_ST_RATE": "",
                "CO_EN_RATE": "",
                "CO_YN_VALX": "",
                "CO_ST_VALX": "",
                "CO_EN_VALX": "",
                "CO_YN_SHAR": "",
                "CO_ST_SHAR": "",
                "CO_EN_SHAR": "",
                "CO_YN_VOLUME": "",
                "CO_ST_VOLUME": "",
                "CO_EN_VOLUME": "",
                "CO_YN_AMT": "",
                "CO_ST_AMT": "",
                "CO_EN_AMT": "",
                "CO_YN_EPS": "",
                "CO_ST_EPS": "",
                "CO_EN_EPS": "",
                "CO_YN_PER": "",
                "CO_ST_PER": "",
                "CO_EN_PER": "",
                "KEYB": market_trigger,
                "NATION": "",
                "EXCHANGE": exchange_code,
                "SIC": "",
                "SYMB": name,
                "MKT_TP": market_type,
            },
        )
        return body.get("output2", []) or body.get("output", []) or []

    def get_overseas_product_info(self, exchange_code, symbol):
        body = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/search-info",
            "CTPF1702R",
            params={
                "PRDT_TYPE_CD": "512",
                "PDNO": symbol,
            },
        )
        output = body.get("output", {}) or {}
        if isinstance(output, list):
            return output[0] if output else {}
        return output

    def get_usd_krw_rate(self):
        for exchange_code, symbol in (("NAS", "GILD"), ("NYS", "CAT")):
            output = self.get_overseas_quote_detail(exchange_code, symbol)
            for field in ("t_rate", "p_rate"):
                value = output.get(field)
                if value not in (None, "", "0"):
                    return float(value)
        raise RuntimeError("usd/krw rate missing from overseas price-detail response")

    def place_domestic_cash_order(self, symbol, side, quantity, *, order_type="market", price=None):
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        is_prod = config.ENV == "PROD"
        if side.upper() == "BUY":
            tr_id = "TTTC0012U" if is_prod else "VTTC0012U"
        elif side.upper() == "SELL":
            tr_id = "TTTC0011U" if is_prod else "VTTC0011U"
        else:
            raise ValueError("side must be BUY or SELL")

        if order_type == "market":
            ord_dvsn = "01"
            ord_unpr = "0"
        elif order_type == "limit":
            if price is None:
                raise ValueError("price is required for limit order")
            ord_dvsn = "00"
            ord_unpr = str(int(round(float(price))))
        else:
            raise ValueError("order_type must be market or limit")

        payload = {
            "CANO": config.CANO,
            "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
            "PDNO": symbol,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(int(quantity)),
            "ORD_UNPR": ord_unpr,
        }
        return self._request(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-cash",
            tr_id,
            payload=payload,
            need_hashkey=True,
        )

    def place_domestic_fractional_order(self, symbol, side, *, notional_krw, quantity=None, order_type="market"):
        if not self.domestic_fractional_orders_supported:
            raise NotImplementedError(
                "KIS domestic fractional order endpoint is not configured for this API client; "
                "set KIS_DOMESTIC_FRACTIONAL_ORDER_PATH and buy/sell TR IDs after verifying the official API."
            )
        if order_type != "market":
            raise ValueError("fractional domestic orders currently support market/notional orders only")
        if float(notional_krw) <= 0:
            raise ValueError("notional_krw must be positive")

        side_upper = side.upper()
        if side_upper == "BUY":
            tr_id = config.DOMESTIC_FRACTIONAL_BUY_TR_ID
        elif side_upper == "SELL":
            tr_id = config.DOMESTIC_FRACTIONAL_SELL_TR_ID
        else:
            raise ValueError("side must be BUY or SELL")

        payload = {
            "CANO": config.CANO,
            "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
            "PDNO": symbol,
            "ORD_DVSN": config.DOMESTIC_FRACTIONAL_ORDER_DVSN,
            "ORD_AMT": str(int(round(float(notional_krw)))),
            "ORD_UNPR": "0",
        }
        if quantity is not None:
            payload["ORD_QTY"] = f"{float(quantity):.8f}".rstrip("0").rstrip(".")
        return self._request(
            "POST",
            config.DOMESTIC_FRACTIONAL_ORDER_PATH,
            tr_id,
            payload=payload,
            need_hashkey=True,
        )

    def get_domestic_balance(self):
        is_prod = config.ENV == "PROD"
        tr_id = "TTTC8434R" if is_prod else "VTTC8434R"
        body = self._request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id,
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )
        return body.get("output1", []) or []

    def get_domestic_balance_detail(self):
        is_prod = config.ENV == "PROD"
        tr_id = "TTTC8434R" if is_prod else "VTTC8434R"
        body = self._request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id,
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )
        return body

    def get_domestic_available_cash_krw(self):
        body = self.get_domestic_balance_detail()
        output2 = body.get("output2") or {}
        if isinstance(output2, list):
            output2 = output2[0] if output2 else {}
        candidates = [
            output2.get("ord_psbl_cash"),
            output2.get("ORD_PSBL_CASH"),
            output2.get("dnca_tot_amt"),
            output2.get("DNCA_TOT_AMT"),
            output2.get("nxdy_excc_amt"),
            output2.get("NXDY_EXCC_AMT"),
            output2.get("prvs_rcdl_excc_amt"),
            output2.get("PRVS_RCDL_EXCC_AMT"),
        ]
        for value in candidates:
            if value in (None, ""):
                continue
            try:
                amount = float(str(value).replace(",", ""))
            except (TypeError, ValueError):
                continue
            if amount >= 0:
                return amount
        return None

    def get_overseas_balance(self, exchange_code="NASD", currency="USD"):
        is_prod = config.ENV == "PROD"
        tr_id = "TTTS3012R" if is_prod else "VTTS3012R"
        body = self._request(
            "GET",
            "/uapi/overseas-stock/v1/trading/inquire-balance",
            tr_id,
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "OVRS_EXCG_CD": exchange_code,
                "TR_CRCY_CD": currency,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
        )
        return body.get("output1", []) or body.get("output", []) or []

    def get_domestic_order_executions(
        self,
        start_date,
        end_date,
        *,
        symbol="",
        side="00",
        execution_status="00",
        order_no="",
    ):
        """Return source-backed domestic order/fill rows from the KIS account API."""

        is_prod = config.ENV == "PROD"
        tr_id = "TTTC0081R" if is_prod else "VTTC0081R"
        body = self._request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
            tr_id,
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "INQR_STRT_DT": str(start_date),
                "INQR_END_DT": str(end_date),
                "SLL_BUY_DVSN_CD": str(side),
                "PDNO": str(symbol),
                "CCLD_DVSN": str(execution_status),
                "INQR_DVSN": "00",
                "INQR_DVSN_3": "00",
                "ORD_GNO_BRNO": "",
                "ODNO": str(order_no),
                "INQR_DVSN_1": "",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
                "EXCG_ID_DVSN_CD": "ALL",
            },
        )
        return body.get("output1", []) or body.get("output", []) or []

    def get_overseas_order_executions(
        self,
        start_date,
        end_date,
        *,
        symbol="%",
        exchange_code="%",
        side="00",
        execution_status="00",
    ):
        """Return source-backed overseas order/fill rows from the KIS account API."""

        is_prod = config.ENV == "PROD"
        tr_id = "TTTS3035R" if is_prod else "VTTS3035R"
        body = self._request(
            "GET",
            "/uapi/overseas-stock/v1/trading/inquire-ccnl",
            tr_id,
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "PDNO": str(symbol),
                "ORD_STRT_DT": str(start_date),
                "ORD_END_DT": str(end_date),
                "SLL_BUY_DVSN": str(side),
                "CCLD_NCCS_DVSN": str(execution_status),
                "OVRS_EXCG_CD": str(exchange_code),
                "SORT_SQN": "DS",
                "ORD_DT": "",
                "ORD_GNO_BRNO": "",
                "ODNO": "",
                "CTX_AREA_NK200": "",
                "CTX_AREA_FK200": "",
            },
        )
        return body.get("output", []) or body.get("output1", []) or []

    def get_domestic_period_trade_profit(
        self,
        start_date,
        end_date,
        *,
        symbol="",
        sort="02",
        cash_balance="00",
    ):
        """Return source-backed KR realized trade rows including fee/tax fields.

        This is a read-only account query.  The official response exposes
        per-row ``fee``/``tl_tax`` and aggregate fee/tax fields.  Callers must
        preserve missing values instead of estimating them.
        """

        return self._request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-period-trade-profit",
            "TTTC8715R",
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "SORT_DVSN": str(sort),
                "INQR_STRT_DT": str(start_date),
                "INQR_END_DT": str(end_date),
                "CBLC_DVSN": str(cash_balance),
                "PDNO": str(symbol),
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )

    def get_overseas_period_transactions(
        self,
        start_date,
        end_date,
        *,
        exchange_code,
        symbol="",
        side="00",
        loan_code="",
    ):
        """Return source-backed overseas stock transactions and fee fields.

        The official period-transaction response keeps foreign-currency and
        KRW fee components separate.  This method intentionally returns the
        full response body so reconciliation code can retain that distinction.
        """

        return self._request(
            "GET",
            "/uapi/overseas-stock/v1/trading/inquire-period-trans",
            "CTOS4001R",
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "ERLM_STRT_DT": str(start_date),
                "ERLM_END_DT": str(end_date),
                "OVRS_EXCG_CD": str(exchange_code),
                "PDNO": str(symbol),
                "SLL_BUY_DVSN_CD": str(side),
                "LOAN_DVSN_CD": str(loan_code),
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )

    def get_overseas_orderable_amount(self, exchange_code, symbol, price, *, currency="USD"):
        if price is None or float(price) <= 0:
            raise ValueError("positive price is required for overseas orderable amount")
        is_prod = config.ENV == "PROD"
        tr_id = "TTTS3007R" if is_prod else "VTTS3007R"
        body = self._request(
            "GET",
            "/uapi/overseas-stock/v1/trading/inquire-psamount",
            tr_id,
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
                "OVRS_EXCG_CD": exchange_code,
                "OVRS_ORD_UNPR": f"{float(price):.2f}",
                "ITEM_CD": symbol,
                "TR_CRCY_CD": currency,
            },
        )
        output = body.get("output") or {}
        if isinstance(output, list):
            output = output[0] if output else {}
        return output

    def get_overseas_foreign_margin(self):
        is_prod = config.ENV == "PROD"
        tr_id = "TTTC2101R" if is_prod else "VTTC2101R"
        return self._request(
            "GET",
            "/uapi/overseas-stock/v1/trading/foreign-margin",
            tr_id,
            params={
                "CANO": config.CANO,
                "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
            },
        )

    def place_overseas_order(self, symbol, side, quantity, *, ovrs_excg_cd, price):
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if price is None or float(price) <= 0:
            raise ValueError("positive price is required for overseas order")

        is_prod = config.ENV == "PROD"
        if side.upper() == "BUY":
            tr_id = "TTTT1002U" if is_prod else "VTTT1002U"
            sll_type = ""
        elif side.upper() == "SELL":
            tr_id = "TTTT1006U" if is_prod else "VTTT1006U"
            sll_type = "00"
        else:
            raise ValueError("side must be BUY or SELL")

        payload = {
            "CANO": config.CANO,
            "ACNT_PRDT_CD": config.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": ovrs_excg_cd,
            "PDNO": symbol,
            "ORD_QTY": str(int(quantity)),
            "OVRS_ORD_UNPR": f"{float(price):.2f}",
            "CTAC_TLNO": "",
            "MGCO_APTM_ODNO": "",
            "SLL_TYPE": sll_type,
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": "00",
        }
        return self._request(
            "POST",
            "/uapi/overseas-stock/v1/trading/order",
            tr_id,
            payload=payload,
            need_hashkey=True,
        )

    def get_historical_prices(self, symbol, start_date, end_date, period="D", max_records=260):
        import time

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        all_prices = []
        current_end = end_date

        while len(all_prices) < max_records:
            headers = self.get_headers("FHKST03010100")
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": current_end,
                "FID_PERIOD_DIV_CODE": period,
                # Use adjusted price to reduce split/rights-induced return spikes.
                "FID_ORG_ADJ_PRC": "1",
            }

            res = None
            for attempt in range(3):
                try:
                    res = requests.get(url, headers=headers, params=params, timeout=10)
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    if attempt < 2:
                        time.sleep(2 ** (attempt + 1))
                    else:
                        print(f"[WARN] price request network fail symbol={symbol} end={current_end}")
                        return all_prices

            if res is None or res.status_code != 200:
                status = None if res is None else res.status_code
                text = "" if res is None else res.text[:240]
                print(f"[WARN] price request bad response symbol={symbol} status={status} body={text}")
                break

            body = res.json()
            data = body.get("output2", [])
            if not data:
                msg_cd = body.get("msg_cd", "")
                msg1 = body.get("msg1", "")
                rt_cd = body.get("rt_cd", "")
                if msg_cd or msg1 or rt_cd:
                    print(f"[WARN] empty price data symbol={symbol} rt_cd={rt_cd} msg_cd={msg_cd} msg={msg1}")
                break

            all_prices.extend(data)

            last_date = data[-1].get("stck_bsop_date", "")
            if not last_date or last_date <= start_date:
                break

            last_dt = datetime.strptime(last_date, "%Y%m%d")
            current_end = (last_dt - timedelta(days=1)).strftime("%Y%m%d")
            if current_end < start_date:
                break

            time.sleep(0.06)

        return all_prices[:max_records]


if __name__ == "__main__":
    api = KISApi()
    print("API 객체 생성 완료")
