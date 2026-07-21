from __future__ import annotations

import glob
import os
from io import BytesIO, StringIO

import pandas as pd

try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover
    def tqdm(x, **kwargs):  # type: ignore
        return x


def write_csv_any(df: pd.DataFrame, path: str, index: bool) -> None:
    if path.startswith("gs://"):
        from google.cloud import storage

        no_scheme = path.replace("gs://", "", 1)
        bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        sio = StringIO()
        df.to_csv(sio, index=index, encoding="utf-8-sig")
        blob.upload_from_string(sio.getvalue(), content_type="text/csv; charset=utf-8")
        return
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    df.to_csv(path, index=index, encoding="utf-8-sig")


def list_price_files(base: str, market: str) -> list[str]:
    if base.startswith("gs://"):
        from google.cloud import storage

        no_scheme = base.replace("gs://", "", 1)
        bucket_name, prefix = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=f"{prefix}/{market}/")
        return [f"gs://{bucket_name}/{b.name}" for b in blobs if b.name.endswith(".csv.gz")]
    return glob.glob(os.path.join(base, market, "*.csv.gz"))


def read_price_file(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            no_scheme = path.replace("gs://", "", 1)
            bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
            raw = storage.Client().bucket(bucket_name).blob(blob_name).download_as_bytes()
            df = pd.read_csv(BytesIO(raw), compression="gzip", parse_dates=["date"])
        else:
            df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        if {"date", "close"}.issubset(df.columns):
            out = df[["date", "close"]].copy()
            if "volume" in df.columns:
                out["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
            else:
                out["volume"] = 0.0
            return out.dropna(subset=["date", "close"])
    except Exception as e:
        print(f"[WARN] read_price_file failed path={path} err={e}")
    return pd.DataFrame(columns=["date", "close", "volume"])


def build_market_matrices(base: str, market: str, max_files: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    files = sorted(list_price_files(base, market))
    if max_files > 0:
        files = files[:max_files]

    rows = []
    prefix = "S_" if market == "stock" else "E_"
    for f in tqdm(files, desc=f"Load {market} prices"):
        code = os.path.basename(f).replace(".csv.gz", "")
        df = read_price_file(f)
        if df.empty:
            continue
        df["ticker"] = prefix + code.zfill(6)
        df["traded_value"] = pd.to_numeric(df["close"], errors="coerce").fillna(0.0) * pd.to_numeric(
            df["volume"], errors="coerce"
        ).fillna(0.0)
        rows.append(df[["date", "ticker", "close", "traded_value"]])

    if not rows:
        return pd.DataFrame(), pd.DataFrame()
    long_df = pd.concat(rows, ignore_index=True)
    close = long_df.pivot(index="date", columns="ticker", values="close").sort_index()
    traded_value = long_df.pivot(index="date", columns="ticker", values="traded_value").sort_index()
    return close, traded_value


def build_close_matrix(base: str, market: str, max_files: int) -> pd.DataFrame:
    close, _ = build_market_matrices(base, market, max_files)
    return close
