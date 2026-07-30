# ==========================================================
# Stock Forecasting AI - FastAPI
#
# LSTM으로 학습한 모델(ai-model/이 생성)을 로드해서 다음 거래일 종가를
# 예측하는 API 서버. AI Service Blueprint의 기존 프로젝트들과 동일하게
# 계층을 분리한다 - routers(HTTP) / services(비즈니스 로직) / schemas(요청·응답
# 형식) / core(설정) / utils(공용 함수).
#
# ※ 이 서비스는 교육 목적으로 제작되었으며, 실제 투자 판단에 사용해서는
#   안 됩니다. docs/01_Project_Overview.md 참고.
# ==========================================================

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, ARTIFACTS_DIR
from routers.model import router as model_router
from routers.predict import router as predict_router
from services.model_loader import get_trained_tickers

app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sanitize_validation_errors(errors):
    sanitized = []
    for error in errors:
        error = dict(error)
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            error["ctx"] = {key: str(value) for key, value in ctx.items()}
        sanitized.append(error)
    return sanitized


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"error": "입력값을 확인해주세요.", "details": _sanitize_validation_errors(exc.errors())}
        ),
    )


@app.get("/", tags=["health"])
def root():
    return {
        "service": APP_TITLE,
        "status": "running",
        "trained_tickers": get_trained_tickers(),
        "disclaimer": "교육 목적 프로젝트이며 투자 판단에 사용해서는 안 됩니다.",
    }


@app.get("/health", tags=["health"])
def health():
    trained = get_trained_tickers()
    return {"status": "ok", "trained_tickers": trained}


app.include_router(predict_router)
app.include_router(model_router)

# 학습 시 생성된 평가 그래프(loss curve, prediction vs actual, residuals 등)를
# 화면에서 이미지로 바로 보여주기 위한 정적 파일 마운트.
# 예) http://localhost:8000/plots/AAPL/plots/loss_curve.png
if ARTIFACTS_DIR.exists():
    app.mount("/plots", StaticFiles(directory=str(ARTIFACTS_DIR)), name="plots")
