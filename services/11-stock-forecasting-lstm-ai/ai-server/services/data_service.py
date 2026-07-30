# services/data_service.py
# ==========================================================
# 실시간(요청 시점 기준 최신) 주가 데이터를 Yahoo Finance에서 가져온다.
# ai-model의 data_collector.py와 달리, 여기서는 디스크 캐싱을 하지 않는다 -
# 예측은 "가장 최신 데이터"를 기준으로 해야 의미가 있기 때문이다.
# ==========================================================

import pandas as pd
import yfinance as yf

from core.config import MIN_HISTORY_DAYS


def fetch_recent_data(ticker: str, period: str = MIN_HISTORY_DAYS) -> pd.DataFrame:
    """예측/차트에 사용할 최근 OHLCV 데이터를 가져온다.

    Raises:
        ValueError: 데이터를 하나도 받지 못한 경우
    """
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)

    if df.empty:
        raise ValueError(f"'{ticker}' 종목의 데이터를 가져오지 못했습니다.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"
    return df[["Open", "High", "Low", "Close", "Volume"]].copy()


def get_recent_chart_data(ticker: str, display_days: int = 90) -> list[dict]:
    """React 화면의 '최근 주가 차트'용 데이터. Close와 함께 MA5/20/60을 계산해서
    반환한다 - MA60을 온전히 그리려면 표시 구간보다 60일 더 여유 있게 데이터를
    받아온 뒤, 마지막에 화면에 보여줄 구간(display_days)만 잘라낸다.
    """
    raw_df = fetch_recent_data(ticker)

    close = raw_df["Close"]
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()

    result_df = raw_df.tail(display_days)
    ma5, ma20, ma60 = ma5.tail(display_days), ma20.tail(display_days), ma60.tail(display_days)

    points = []
    for date, row in result_df.iterrows():
        points.append(
            {
                "date": str(date.date()),
                "close": round(float(row["Close"]), 2),
                "ma5": None if pd.isna(ma5[date]) else round(float(ma5[date]), 2),
                "ma20": None if pd.isna(ma20[date]) else round(float(ma20[date]), 2),
                "ma60": None if pd.isna(ma60[date]) else round(float(ma60[date]), 2),
            }
        )
    return points
