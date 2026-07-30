# feature_engineering.py
# ==========================================================
# STEP 3. Feature Engineering
#
# 원본 OHLCV(시가/고가/저가/종가/거래량) 5개 컬럼만으로는 LSTM이 "추세"나
# "변동성" 같은 패턴을 스스로 학습하기 어렵다. 사람이 미리 계산해서
# 힌트를 주는 것이 Feature Engineering이다. 각 피처마다 "왜 이걸 넣는가"를
# 주석으로 함께 남긴다 - docs/04_FeatureEngineering.md에서 더 자세히 설명한다.
# ==========================================================

import pandas as pd


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """이동평균(MA) - 단기 노이즈를 걷어내고 추세(Trend)를 보여준다.

    MA5(1주일), MA20(1개월), MA60(3개월) 세 가지 기간을 함께 보면
    단기/중기/장기 추세를 동시에 파악할 수 있다.
    """
    df = df.copy()
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()
    return df


def add_return_features(df: pd.DataFrame) -> pd.DataFrame:
    """수익률/변동성 관련 피처.

    - Daily_Return: 전일 대비 등락률(%). 절대 가격(300달러 vs 30달러)과
      무관하게 "얼마나 변했는가"를 비교 가능한 형태로 만들어준다.
    - Price_Change: 전일 대비 절대 가격 변화.
    - Price_Range / High_Low: 하루 중 가격 변동폭(고가-저가) - 변동성 지표.
    - Open_Close: 시가 대비 종가 변화 - 그날 하루의 "방향성" 지표.
    """
    df = df.copy()
    df["Daily_Return"] = df["Close"].pct_change() * 100
    df["Price_Change"] = df["Close"].diff()
    df["Price_Range"] = df["High"] - df["Low"]
    df["High_Low"] = df["High"] - df["Low"]  # Price_Range와 동일 지표를 다른 이름으로도 노출(문서 표기 일치)
    df["Open_Close"] = df["Close"] - df["Open"]
    return df


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """거래량 변화율. 거래량이 급증하는 날은 큰 뉴스/이벤트가 있었을 가능성이 높다."""
    df = df.copy()
    df["Volume_Change"] = df["Volume"].pct_change() * 100
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Lag Feature - "N일 전 종가"를 오늘 행에 그대로 붙여넣는다.

    LSTM은 순서(시퀀스) 자체를 학습하지만, Lag Feature를 명시적으로 추가해주면
    "가장 최근 값에 더 큰 비중을 둬야 한다"는 힌트를 모델에 직접 제공할 수 있다.
    """
    df = df.copy()
    df["Lag1"] = df["Close"].shift(1)
    df["Lag3"] = df["Close"].shift(3)
    df["Lag5"] = df["Close"].shift(5)
    return df


def add_rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Rolling Mean/Std - 최근 window일의 평균/표준편차.

    Rolling Mean은 MA와 비슷하지만, Rolling Std는 "최근 며칠간 가격이
    얼마나 출렁였는가"(변동성)를 숫자 하나로 요약해준다.
    """
    df = df.copy()
    df[f"Rolling_Mean_{window}"] = df["Close"].rolling(window=window).mean()
    df[f"Rolling_Std_{window}"] = df["Close"].rolling(window=window).std()
    return df


def build_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """전체 Feature Engineering 파이프라인을 순서대로 적용한다.

    Args:
        raw_df: data_collector.fetch_stock_data()가 반환한 원본 OHLCV DataFrame

    Returns:
        파생 피처가 모두 추가된 DataFrame. rolling/lag 계산으로 생긴 앞부분의
        NaN 행은 제거한 상태로 반환한다(모델 입력에 결측치가 들어가면 안 되므로).
    """
    df = raw_df.copy()
    df = add_moving_averages(df)
    df = add_return_features(df)
    df = add_volume_features(df)
    df = add_lag_features(df)
    df = add_rolling_features(df, window=5)

    before = len(df)
    df = df.dropna().copy()
    after = len(df)
    if before != after:
        # MA60, Lag5 등 가장 긴 window(60일) 때문에 앞부분 최대 60행 정도가
        # NaN이 되어 제거된다 - 정상적인 현상이다.
        print(f"[feature_engineering] Feature 계산으로 생긴 결측 행 {before - after}개 제거 (남은 행: {after})")

    return df


if __name__ == "__main__":
    from data_collector import fetch_stock_data

    raw = fetch_stock_data("AAPL")
    features = build_features(raw)
    print(features.tail())
    print(f"\n최종 컬럼: {list(features.columns)}")
