# routers/model.py
# ==========================================================
# 모델 정보 조회 API. 화면의 "모델 정보" 패널과 종목 선택 드롭다운이
# 이 API들을 사용한다.
# ==========================================================

from fastapi import APIRouter, HTTPException

from core.config import SUPPORTED_TICKERS
from schemas.prediction import AvailableTickersResponse, ModelInfoResponse
from services.model_loader import get_trained_tickers, load_model_bundle

router = APIRouter(tags=["model"])


@router.get("/tickers", response_model=AvailableTickersResponse)
def list_tickers():
    return AvailableTickersResponse(
        supported_tickers=SUPPORTED_TICKERS,
        trained_tickers=get_trained_tickers(),
    )


@router.get("/model/info/{ticker}", response_model=ModelInfoResponse)
def get_model_info(ticker: str):
    ticker = ticker.upper()
    try:
        bundle = load_model_bundle(ticker)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    meta = bundle.metadata
    return ModelInfoResponse(
        ticker=ticker,
        lookback=meta["lookback"],
        feature_count=len(meta["feature_columns"]),
        trained_at=meta["trained_at"],
        data_date_range=meta["data_date_range"],
        test_metrics=meta["test_metrics"],
        train_rows=meta["train_rows"],
        val_rows=meta["val_rows"],
        test_rows=meta["test_rows"],
        epochs_ran=meta["epochs_ran"],
    )
