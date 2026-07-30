# core/config.py
# ==========================================================
# 서버 전역 설정.
#
# ARTIFACTS_DIR: ai-model이 학습해서 저장한 model.keras/scaler.pkl/metadata.json이
# 있는 위치. 로컬 개발 환경(uvicorn을 ai-server 폴더에서 직접 실행)과 Docker
# 환경(docker-compose가 볼륨을 다른 경로에 마운트)에서 경로가 다르기 때문에,
# 환경 변수 ARTIFACTS_DIR로 오버라이드할 수 있게 만들었다.
# ==========================================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # ai-server/

# 로컬 실행 기본값: ai-server/ 기준 형제 폴더인 ai-model/artifacts
_default_artifacts_dir = (BASE_DIR.parent / "ai-model" / "artifacts").resolve()
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", str(_default_artifacts_dir)))

SUPPORTED_TICKERS = ["AAPL", "MSFT", "TSLA", "NVDA", "GOOG"]
DEFAULT_TICKER = "AAPL"

LOOKBACK = 60
TARGET_COLUMN = "Close"

# ai-model/src/config.py의 FEATURE_COLUMNS와 반드시 동일해야 한다.
# (Train/Serve Skew 방지 - docs/08_FastAPI.md 참고)
FEATURE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "MA5",
    "MA20",
    "MA60",
    "Daily_Return",
    "Price_Change",
    "Price_Range",
    "High_Low",
    "Open_Close",
    "Volume_Change",
    "Lag1",
    "Lag3",
    "Lag5",
    "Rolling_Mean_5",
    "Rolling_Std_5",
]

# 예측을 위해 최소 필요한 과거 데이터 일수 (LOOKBACK + Feature Engineering 워밍업 기간)
# MA60이 가장 긴 window이므로 60 + 60 = 120일 이상을 넉넉히 받아온다.
MIN_HISTORY_DAYS = "1y"

APP_TITLE = "Stock Forecasting AI"
APP_DESCRIPTION = (
    "LSTM 기반 주가 예측 교육용 서비스 API. "
    "※ 이 서비스는 투자 목적이 아닌 교육 목적으로 제작되었습니다."
)
APP_VERSION = "1.0.0"
