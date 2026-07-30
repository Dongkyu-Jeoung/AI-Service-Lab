# model.py
# ==========================================================
# STEP 6. LSTM 모델 구축
#
# 구조: LSTM -> Dropout -> LSTM -> Dropout -> Dense -> Dense(출력 1개)
#
# - LSTM 층을 2개 쌓은 이유: 첫 번째 층은 "60일 시퀀스 전체의 패턴"을
#   요약하고, 두 번째 층은 그 요약을 다시 한번 정제한다. 층을 깊게
#   쌓을수록 복잡한 패턴을 잡아낼 잠재력은 커지지만, 과적합 위험도 커진다.
# - Dropout: 학습 중 일부 뉴런을 무작위로 꺼서 특정 뉴런에 과의존하는 것을
#   막는다(과적합 방지 기법).
# - Dense(1): 최종적으로 숫자 하나(다음 날 Close, 스케일링된 값)를 출력한다.
# ==========================================================

from tensorflow import keras
from tensorflow.keras import layers

from config import DENSE_UNITS, DROPOUT_RATE, LEARNING_RATE, LSTM_UNITS_1, LSTM_UNITS_2


def build_lstm_model(input_shape: tuple[int, int]) -> keras.Model:
    """LSTM 시계열 예측 모델을 만든다.

    Args:
        input_shape: (LOOKBACK, n_features) - 예) (60, 19)

    Returns:
        컴파일까지 완료된 Keras 모델
    """
    model = keras.Sequential(
        [
            layers.Input(shape=input_shape),
            layers.LSTM(LSTM_UNITS_1, return_sequences=True),
            layers.Dropout(DROPOUT_RATE),
            layers.LSTM(LSTM_UNITS_2, return_sequences=False),
            layers.Dropout(DROPOUT_RATE),
            layers.Dense(DENSE_UNITS, activation="relu"),
            layers.Dense(1),  # 회귀(연속값) 출력이므로 activation 없음
        ],
        name="stock_lstm_forecaster",
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="mean_squared_error",
        metrics=["mean_absolute_error"],
    )

    return model


if __name__ == "__main__":
    m = build_lstm_model(input_shape=(60, 19))
    m.summary()
