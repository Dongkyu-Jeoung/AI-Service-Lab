# utils/features.py
# ==========================================================
# 서빙(예측) 시점에 사용하는 Feature Engineering.
#
# 매우 중요: 이 함수는 ai-model/src/feature_engineering.py의 build_features()와
# **반드시 동일한 로직**이어야 한다. 둘이 달라지면 "학습 때 본 피처 분포"와
# "실제 서비스에서 만드는 피처 분포"가 어긋나는 Train/Serve Skew가 발생해서,
# 모델이 이상한 값을 예측하게 된다.
#
# 왜 코드를 공유하지 않고 복사했는가? ai-server는 Docker로 배포될 때 ai-model
# 폴더를 포함하지 않는(서빙 컨테이너는 학습 코드가 필요 없으므로) 독립 컨테이너이기
# 때문이다. 실무에서는 이런 공용 로직을 별도의 패키지로 분리해서 두 서비스가
# 함께 설치하는 방식을 쓰지만, 이 프로젝트는 "ai-model과 ai-server의 책임이
# 분리되어 있다"는 구조를 명확히 보여주는 것이 교육 목표라 의도적으로 각자
# 독립적인 코드를 갖도록 했다 - docs/08_FastAPI.md에서 이 트레이드오프를 설명한다.
# ==========================================================

import pandas as pd


def build_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """원본 OHLCV DataFrame에 ai-model과 동일한 파생 피처를 추가한다."""
    df = raw_df.copy()

    # Moving Average
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()

    # 수익률/변동성
    df["Daily_Return"] = df["Close"].pct_change() * 100
    df["Price_Change"] = df["Close"].diff()
    df["Price_Range"] = df["High"] - df["Low"]
    df["High_Low"] = df["High"] - df["Low"]
    df["Open_Close"] = df["Close"] - df["Open"]

    # 거래량
    df["Volume_Change"] = df["Volume"].pct_change() * 100

    # Lag Feature
    df["Lag1"] = df["Close"].shift(1)
    df["Lag3"] = df["Close"].shift(3)
    df["Lag5"] = df["Close"].shift(5)

    # Rolling Mean/Std
    df["Rolling_Mean_5"] = df["Close"].rolling(window=5).mean()
    df["Rolling_Std_5"] = df["Close"].rolling(window=5).std()

    return df.dropna().copy()
