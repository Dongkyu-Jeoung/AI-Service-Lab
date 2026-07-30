# schemas/prediction.py
# ==========================================================
# 요청/응답 데이터 형식(Pydantic 모델). services/09-chatbot-ai 계열과 동일하게
# "요청 스키마가 첫 번째 방어선" 원칙을 따른다 - 잘못된 요청은 여기서 422로 걸러진다.
# ==========================================================

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    ticker: str = Field(..., description="예측할 종목 코드 (예: AAPL)")

    model_config = {"json_schema_extra": {"example": {"ticker": "AAPL"}}}


class PredictResponse(BaseModel):
    ticker: str
    current_price: float = Field(..., description="가장 최근 거래일 종가")
    current_date: str = Field(..., description="가장 최근 거래일 날짜 (YYYY-MM-DD)")
    predicted_price: float = Field(..., description="다음 거래일 예측 종가")
    predicted_change: float = Field(..., description="예상 변동 금액 (predicted - current)")
    predicted_change_percent: float = Field(..., description="예상 등락률 (%)")
    disclaimer: str = Field(
        default="이 예측은 교육 목적으로만 제공되며 투자 판단의 근거로 사용해서는 안 됩니다.",
        description="투자 목적이 아님을 알리는 고지 문구",
    )


class RecentDataPoint(BaseModel):
    date: str
    close: float
    ma5: float | None = None
    ma20: float | None = None
    ma60: float | None = None


class RecentDataResponse(BaseModel):
    ticker: str
    data: list[RecentDataPoint]


class ModelMetrics(BaseModel):
    MAE: float
    RMSE: float
    MAPE: float
    R2: float


class ModelInfoResponse(BaseModel):
    ticker: str
    lookback: int
    feature_count: int
    trained_at: str
    data_date_range: dict
    test_metrics: ModelMetrics
    train_rows: int
    val_rows: int
    test_rows: int
    epochs_ran: int


class AvailableTickersResponse(BaseModel):
    supported_tickers: list[str] = Field(..., description="이 서비스가 지원하는 전체 종목 목록")
    trained_tickers: list[str] = Field(..., description="현재 학습된 모델이 존재해 예측 가능한 종목 목록")


class HealthResponse(BaseModel):
    status: str
    trained_tickers: list[str]
