# routers/predict.py
# ==========================================================
# 예측 + 최근 주가 차트 API. HTTP 계층 - 실제 로직은 services/*에 위임한다.
# ==========================================================

from fastapi import APIRouter, HTTPException

from schemas.prediction import PredictRequest, PredictResponse, RecentDataPoint, RecentDataResponse
from services.data_service import get_recent_chart_data
from services.prediction_service import predict_next_close

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    try:
        result = predict_next_close(payload.ticker.upper())
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:  # noqa: BLE001 - 외부 API/모델 추론 오류를 그대로 노출하지 않고 감싼다.
        raise HTTPException(status_code=500, detail=f"예측 중 오류가 발생했습니다: {error}")

    return PredictResponse(**result)


@router.get("/stock/{ticker}/history", response_model=RecentDataResponse)
def get_stock_history(ticker: str, days: int = 90):
    ticker = ticker.upper()
    try:
        points = get_recent_chart_data(ticker, display_days=days)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"데이터 조회 중 오류가 발생했습니다: {error}")

    return RecentDataResponse(ticker=ticker, data=[RecentDataPoint(**p) for p in points])
