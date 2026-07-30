# evaluate.py
# ==========================================================
# STEP 8. 평가  +  Baseline 비교
#
# LSTM이 정말 "쓸모 있는" 모델인지 확인하려면, 아주 단순한 방법(Baseline)과
# 비교해봐야 한다. LSTM이 Baseline보다 못하면, 아무리 복잡한 모델이어도
# 실패작이다 - "복잡하다고 항상 더 좋은 건 아니다"를 직접 증명하는 단계.
# ==========================================================

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import koreanize_matplotlib  # noqa: F401 - import만으로 matplotlib 기본 폰트를 한글 지원 폰트로 바꿔준다
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

plt.rcParams["axes.unicode_minus"] = False


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """MAE, RMSE, MAPE, R² 네 가지 지표를 한 번에 계산한다.

    - MAE (Mean Absolute Error): 평균적으로 몇 달러 틀렸는가. 단위가 원본과
      같아서(달러) 직관적으로 이해하기 쉽다.
    - RMSE (Root Mean Squared Error): MAE와 비슷하지만 큰 오차에 더 큰
      벌점을 준다(제곱 후 평균, 다시 루트). 가끔 크게 틀리는 걸 싫어할 때 참고.
    - MAPE (Mean Absolute Percentage Error): 오차를 "퍼센트"로 표현.
      "평균적으로 몇 % 틀렸는가"라 종목 가격대(30달러 vs 300달러)와 무관하게
      비교할 수 있다.
    - R² (결정계수): 1에 가까울수록 모델이 데이터의 변동을 잘 설명한다는 뜻.
      0이면 "그냥 평균값으로 찍는 것"과 다를 바 없다는 뜻이고, 음수면 그보다도 못하다.
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
    r2 = r2_score(y_true, y_pred)

    return {"MAE": round(float(mae), 4), "RMSE": round(rmse, 4), "MAPE": round(mape, 4), "R2": round(float(r2), 4)}


def naive_forecast(y_true_prices: np.ndarray) -> np.ndarray:
    """Baseline 1: Naive Forecast — "내일도 오늘과 같을 것이다".

    가장 단순한 예측 방법이지만, 주가처럼 하루 사이 변화가 크지 않은
    시계열에서는 의외로 잘 맞는 경우가 많다. LSTM이 이걸 못 이기면 문제.
    """
    return np.roll(y_true_prices, 1)  # 하루씩 밀어서 "어제 값 = 오늘 예측"으로 사용


def moving_average_forecast(y_true_prices: np.ndarray, window: int = 5) -> np.ndarray:
    """Baseline 2: Moving Average Forecast — "최근 N일 평균이 내일 값일 것이다"."""
    series = pd.Series(y_true_prices)
    ma = series.rolling(window=window).mean().shift(1)  # 오늘 예측 = 어제까지의 N일 평균
    return ma.to_numpy()


def compare_with_baselines(y_true_prices: np.ndarray, lstm_pred_prices: np.ndarray) -> pd.DataFrame:
    """Naive, Moving Average, LSTM 세 가지 예측 방식의 성능을 표로 비교한다."""
    naive_pred = naive_forecast(y_true_prices)
    ma_pred = moving_average_forecast(y_true_prices)

    # 앞부분에 NaN/워밍업 구간이 생기는 방식(MA)이 있으므로, 세 방식 모두
    # 공정하게 비교하려면 유효한 구간만 잘라서 비교한다.
    valid_start = 5  # moving_average_forecast의 window(5)만큼 앞부분 제외
    y_valid = y_true_prices[valid_start:]

    rows = []
    for name, pred in [
        ("Naive Forecast", naive_pred[valid_start:]),
        (f"Moving Average(5)", ma_pred[valid_start:]),
        ("LSTM", lstm_pred_prices[valid_start:]),
    ]:
        metrics = compute_metrics(y_valid, pred)
        rows.append({"Model": name, **metrics})

    return pd.DataFrame(rows)


def plot_loss_curve(history, output_path: Path) -> None:
    """학습(Train) vs 검증(Validation) Loss 곡선.

    두 선이 함께 내려가면 정상 학습. Train Loss만 계속 내려가고
    Validation Loss가 다시 올라가기 시작하면 과적합(Overfitting) 신호다 -
    EarlyStopping이 바로 이 시점을 감지해서 학습을 멈춰준다.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(history.history["loss"], label="Train Loss")
    ax.plot(history.history["val_loss"], label="Validation Loss")
    ax.set_title("Loss Curve (MSE)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.legend()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_prediction_vs_actual(dates, y_true_prices: np.ndarray, y_pred_prices: np.ndarray, output_path: Path) -> None:
    """실제값 vs 예측값 Line Chart — 예측이 실제 추세를 잘 따라가는지 한눈에 확인."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dates, y_true_prices, label="실제값 (Actual)", color="#0f172a", linewidth=1.3)
    ax.plot(dates, y_pred_prices, label="예측값 (Predicted)", color="#dc2626", linewidth=1.3, linestyle="--")
    ax.set_title("실제값 vs 예측값 (Test 구간)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Close ($)")
    ax.legend()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_residuals(y_true_prices: np.ndarray, y_pred_prices: np.ndarray, output_path: Path) -> None:
    """Residual Plot — (실제값 - 예측값)의 분포. 0 근처에 무작위로 흩어져
    있으면 좋은 신호, 특정 구간에서 일관되게 치우쳐 있으면 모델이 그 구간의
    패턴을 놓치고 있다는 뜻이다.
    """
    residuals = y_true_prices - y_pred_prices

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].scatter(range(len(residuals)), residuals, alpha=0.5, color="#6d28d9", s=10)
    axes[0].axhline(0, color="red", linestyle="--", linewidth=1)
    axes[0].set_title("Residuals (실제 - 예측)")
    axes[0].set_xlabel("Test 샘플 순서")
    axes[0].set_ylabel("잔차 ($)")

    axes[1].hist(residuals, bins=40, color="#0891b2", alpha=0.8)
    axes[1].set_title("Residual 분포")
    axes[1].set_xlabel("잔차 ($)")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
