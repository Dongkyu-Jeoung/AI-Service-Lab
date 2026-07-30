# preprocessing.py
# ==========================================================
# STEP 4. Scaling  +  STEP 5. Sequence 생성
#
# 이 파일에서 가장 중요한 규칙: Data Leakage(데이터 누수) 방지.
#
#   "Scaler는 반드시 Train 데이터에만 fit()하고,
#    Validation/Test 데이터는 transform()만 한다."
#
# 왜냐하면 MinMaxScaler는 데이터의 최솟값/최댓값을 "기억"하는데, 만약
# Validation/Test 데이터까지 포함해서 fit()하면 모델이 학습 단계에서
# "미래 데이터의 최댓값/최솟값 정보"를 미리 알고 있는 셈이 된다. 이건
# 실전에서는 있을 수 없는 일이다(미래는 아직 안 왔으니까). 이렇게 학습
# 단계에서 미래 정보가 새어 들어가는 것을 Data Leakage라고 부른다.
# ==========================================================

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from config import LOOKBACK, TARGET_COLUMN, TRAIN_RATIO, VAL_RATIO


@dataclass
class SplitResult:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


def split_data(df: pd.DataFrame, train_ratio: float = TRAIN_RATIO, val_ratio: float = VAL_RATIO) -> SplitResult:
    """시간 순서를 지켜서 Train/Validation/Test로 나눈다.

    일반적인 머신러닝은 데이터를 무작위로 섞어서 나누지만(train_test_split의
    shuffle=True), 시계열 데이터는 **절대 섞으면 안 된다**. 과거 데이터로
    미래를 예측하는 것이 목표인데, 섞어버리면 미래 데이터가 학습에 끼어들어가
    실제로는 절대 불가능한 "미래를 보고 학습"하는 상황이 벌어진다.

    그래서 시간 순서 그대로, 앞쪽 구간을 Train, 그다음을 Validation,
    가장 최근 구간을 Test로 자른다.
    """
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()

    return SplitResult(train=train_df, val=val_df, test=test_df)


def fit_scaler(train_df: pd.DataFrame, feature_columns: list[str]) -> MinMaxScaler:
    """Train 데이터에만 fit()한다. 이 함수 밖에서는 절대 fit()을 다시 호출하지 않는다."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(train_df[feature_columns])
    return scaler


def transform_data(df: pd.DataFrame, scaler: MinMaxScaler, feature_columns: list[str]) -> np.ndarray:
    """이미 fit된 scaler로 transform()만 수행한다."""
    return scaler.transform(df[feature_columns])


def create_sequences(scaled_array: np.ndarray, target_col_index: int, lookback: int = LOOKBACK) -> tuple[np.ndarray, np.ndarray]:
    """스케일링된 2차원 배열(행=날짜, 열=피처)을 LSTM 입력용 3차원 시퀀스로 변환한다.

    예) lookback=60이면:
        X[0] = 0~59일째 데이터 (60일치, 전체 피처)   -> y[0] = 60일째 Close
        X[1] = 1~60일째 데이터 (60일치, 전체 피처)   -> y[1] = 61일째 Close
        ...
    즉 "최근 60일을 보고 다음 하루의 Close를 맞히는" 학습 샘플을 만드는 것이다.

    Args:
        scaled_array: shape (n_rows, n_features)
        target_col_index: 예측 대상(Close)이 몇 번째 컬럼인지
        lookback: 시퀀스 길이

    Returns:
        X: shape (n_samples, lookback, n_features)
        y: shape (n_samples,)
    """
    X, y = [], []
    for i in range(lookback, len(scaled_array)):
        X.append(scaled_array[i - lookback:i])
        y.append(scaled_array[i, target_col_index])
    return np.array(X), np.array(y)


def inverse_transform_target(scaler: MinMaxScaler, scaled_values: np.ndarray, target_col_index: int, n_features: int) -> np.ndarray:
    """스케일링된 target(Close) 값만 원래 가격 단위(달러)로 복원한다.

    MinMaxScaler는 여러 컬럼을 한꺼번에 스케일링했기 때문에, 역변환도
    "같은 개수의 컬럼을 가진 배열"이 필요하다. target 값 하나만 알고 있을 때는
    나머지 컬럼을 0으로 채운 더미 배열을 만들어 역변환한 뒤, target 컬럼만
    꺼내는 방식을 쓴다 - 실무에서 자주 쓰는 관용적인 트릭이다.
    """
    scaled_values = np.asarray(scaled_values).reshape(-1)
    dummy = np.zeros((len(scaled_values), n_features))
    dummy[:, target_col_index] = scaled_values
    inversed = scaler.inverse_transform(dummy)
    return inversed[:, target_col_index]


if __name__ == "__main__":
    from config import FEATURE_COLUMNS
    from data_collector import fetch_stock_data
    from feature_engineering import build_features

    raw = fetch_stock_data("AAPL")
    features = build_features(raw)

    split = split_data(features)
    print(f"Train: {len(split.train)}행, Val: {len(split.val)}행, Test: {len(split.test)}행")

    scaler = fit_scaler(split.train, FEATURE_COLUMNS)
    train_scaled = transform_data(split.train, scaler, FEATURE_COLUMNS)

    target_idx = FEATURE_COLUMNS.index(TARGET_COLUMN)
    X_train, y_train = create_sequences(train_scaled, target_idx)
    print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
