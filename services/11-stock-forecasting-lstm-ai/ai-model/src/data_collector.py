# data_collector.py
# ==========================================================
# STEP 1. 데이터 수집
#
# Yahoo Finance(yfinance)에서 종목의 일봉(OHLCV) 데이터를 내려받는다.
# 매번 새로 다운로드하면 느리고 Yahoo Finance API가 429(Too Many
# Requests)를 반환할 수 있으므로, 한 번 받은 데이터는 CSV로 캐싱한다.
# ==========================================================

import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import DATA_DIR, INTERVAL, PERIOD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _cache_path(ticker: str) -> Path:
    return DATA_DIR / f"{ticker}_{PERIOD}_{INTERVAL}.csv"


def fetch_stock_data(ticker: str, period: str = PERIOD, interval: str = INTERVAL, use_cache: bool = True) -> pd.DataFrame:
    """Yahoo Finance에서 OHLCV 데이터를 받아온다.

    Args:
        ticker: 종목 코드 (예: "AAPL")
        period: 조회 기간 (예: "5y")
        interval: 봉 간격 (예: "1d")
        use_cache: True면 이전에 받아둔 CSV가 있을 경우 그것을 재사용한다.

    Returns:
        DatetimeIndex를 가진 DataFrame (컬럼: Open, High, Low, Close, Volume)

    Raises:
        ValueError: 데이터를 하나도 받지 못한 경우 (잘못된 티커 등)
    """
    cache_file = _cache_path(ticker)

    if use_cache and cache_file.exists():
        logger.info("캐시된 데이터 사용: %s", cache_file.name)
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        return df

    logger.info("Yahoo Finance에서 %s 데이터 다운로드 중 (period=%s, interval=%s)...", ticker, period, interval)
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)

    if df.empty:
        raise ValueError(f"'{ticker}'에 대한 데이터를 받아오지 못했습니다. 티커를 확인하세요.")

    # yfinance가 최근 버전에서 MultiIndex 컬럼(Ticker 레벨 포함)을 반환하는 경우가 있어
    # 단일 레벨 컬럼으로 정리한다 (Open, High, Low, Close, Volume).
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_file)
    logger.info("데이터 저장 완료: %s (%d행)", cache_file.name, len(df))

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Yahoo Finance 주가 데이터 수집")
    parser.add_argument("--ticker", default="AAPL", help="종목 코드 (기본값: AAPL)")
    parser.add_argument("--no-cache", action="store_true", help="캐시를 무시하고 새로 다운로드")
    args = parser.parse_args()

    data = fetch_stock_data(args.ticker, use_cache=not args.no_cache)
    print(data.tail())
    print(f"\n총 {len(data)}행, 기간: {data.index.min().date()} ~ {data.index.max().date()}")
