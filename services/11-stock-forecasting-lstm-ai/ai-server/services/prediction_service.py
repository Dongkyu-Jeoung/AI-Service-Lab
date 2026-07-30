# services/prediction_service.py
# ==========================================================
# STEP 10(FastAPI)의 핵심 로직. "최근 60일 데이터를 넣으면 다음 거래일
# Close를 예측한다"는 이 프로젝트 전체의 목표를 실제로 수행하는 함수.
# ==========================================================

import numpy as np

from core.config import TARGET_COLUMN
from services.data_service import fetch_recent_data
from services.model_loader import ModelBundle, load_model_bundle
from utils.features import build_features


def _inverse_transform_target(scaler, scaled_value: float, target_col_index: int, n_features: int) -> float:
    """스케일링된 예측값 하나를 원래 가격(달러) 단위로 되돌린다.

    ai-model/src/preprocessing.py의 inverse_transform_target()과 동일한 원리:
    나머지 컬럼을 0으로 채운 더미 배열을 만들어 역변환한 뒤 target 컬럼만 꺼낸다.
    """
    dummy = np.zeros((1, n_features))
    dummy[0, target_col_index] = scaled_value
    inversed = scaler.inverse_transform(dummy)
    return float(inversed[0, target_col_index])


def predict_next_close(ticker: str) -> dict:
    """다음 거래일 Close 가격을 예측한다.

    Raises:
        FileNotFoundError: 학습된 모델이 없는 경우 (model_loader에서 발생)
        ValueError: 예측에 필요한 만큼 데이터가 충분하지 않은 경우
    """
    bundle: ModelBundle = load_model_bundle(ticker)

    feature_columns: list[str] = bundle.metadata["feature_columns"]
    lookback: int = bundle.metadata["lookback"]
    target_col_index: int = bundle.metadata["target_column_index"]
    n_features = len(feature_columns)

    raw_df = fetch_recent_data(ticker)
    features_df = build_features(raw_df)

    if len(features_df) < lookback:
        raise ValueError(
            f"예측에 필요한 최소 {lookback}일치 데이터가 부족합니다 (현재 {len(features_df)}일). "
            "휴장일이 많았거나 신규 상장 종목일 수 있습니다."
        )

    recent_window = features_df.tail(lookback)
    scaled_window = bundle.scaler.transform(recent_window[feature_columns])
    X = scaled_window.reshape(1, lookback, n_features)

    predicted_scaled = float(bundle.model.predict(X, verbose=0)[0][0])
    predicted_price = _inverse_transform_target(bundle.scaler, predicted_scaled, target_col_index, n_features)

    current_price = float(raw_df[TARGET_COLUMN].iloc[-1])
    current_date = str(raw_df.index[-1].date())

    change = predicted_price - current_price
    change_percent = (change / current_price) * 100 if current_price else 0.0

    return {
        "ticker": ticker,
        "current_price": round(current_price, 2),
        "current_date": current_date,
        "predicted_price": round(predicted_price, 2),
        "predicted_change": round(change, 2),
        "predicted_change_percent": round(change_percent, 2),
    }
