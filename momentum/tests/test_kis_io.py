from pathlib import Path

import pandas as pd

from live_core.kis_io import build_market_matrices, list_price_files, read_price_file, write_csv_any


def test_write_csv_any_local(tmp_path: Path):
    path = tmp_path / "subdir" / "sample.csv"
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    write_csv_any(df, str(path), index=False)
    assert path.exists()
    loaded = pd.read_csv(path, encoding="utf-8-sig")
    assert loaded.to_dict(orient="list") == {"a": [1, 2], "b": ["x", "y"]}


def test_list_and_read_price_files_local(tmp_path: Path):
    stock_dir = tmp_path / "stock"
    stock_dir.mkdir()
    price_path = stock_dir / "123456.csv.gz"
    df = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "close": [100.0, 102.0],
            "volume": [10, 20],
        }
    )
    df.to_csv(price_path, index=False, compression="gzip")

    files = list_price_files(str(tmp_path), "stock")
    assert files == [str(price_path)]

    loaded = read_price_file(str(price_path))
    assert list(loaded.columns) == ["date", "close", "volume"]
    assert len(loaded) == 2
    assert float(loaded.iloc[1]["close"]) == 102.0


def test_build_market_matrices_local(tmp_path: Path):
    etf_dir = tmp_path / "etf"
    etf_dir.mkdir()
    for code, close0 in [("069500", 10.0), ("357870", 20.0)]:
        pd.DataFrame(
            {
                "date": ["2024-01-02", "2024-01-03"],
                "close": [close0, close0 + 1],
                "volume": [100, 200],
            }
        ).to_csv(etf_dir / f"{code}.csv.gz", index=False, compression="gzip")

    close, traded_value = build_market_matrices(str(tmp_path), "etf", max_files=0)
    assert list(close.columns) == ["E_069500", "E_357870"]
    assert list(traded_value.columns) == ["E_069500", "E_357870"]
    assert float(close.iloc[0]["E_069500"]) == 10.0
    assert float(traded_value.iloc[1]["E_357870"]) == 21.0 * 200
