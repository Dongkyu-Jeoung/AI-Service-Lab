# config.py
# ==========================================================
# 프로젝트 전역 설정. 학생이 종목/기간/하이퍼파라미터를 바꾸고 싶으면
# 이 파일 하나만 수정하면 된다 - 다른 스크립트를 뒤질 필요가 없도록
# 모든 상수를 이 파일 하나에 모아둔다.
# ==========================================================

from pathlib import Path

# ----------------------------------------------------------
# 1. 경로
# ----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # ai-model/
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

DATA_DIR.mkdir(exist_ok=True)
ARTIFACTS_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------
# 2. 종목 (Yahoo Finance 티커)
# ----------------------------------------------------------
SUPPORTED_TICKERS = ["AAPL", "MSFT", "TSLA", "NVDA", "GOOG"]
DEFAULT_TICKER = "AAPL"

# ----------------------------------------------------------
# 3. 데이터 수집
# ----------------------------------------------------------
PERIOD = "5y"      # yfinance 다운로드 기간 (5년치 일봉)
INTERVAL = "1d"    # 일봉

# ----------------------------------------------------------
# 4. 시계열/모델 하이퍼파라미터
# ----------------------------------------------------------
LOOKBACK = 60          # 최근 N일을 보고 다음 하루를 예측
TARGET_COLUMN = "Close"

TRAIN_RATIO = 0.70     # 학습 70%
VAL_RATIO = 0.15       # 검증 15%
# 나머지 15%는 테스트

RANDOM_SEED = 42

# LSTM 구조
LSTM_UNITS_1 = 64
LSTM_UNITS_2 = 32
DROPOUT_RATE = 0.2
DENSE_UNITS = 16

# 학습
EPOCHS = 100            # EarlyStopping이 있으므로 넉넉하게 잡아도 된다
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EARLY_STOPPING_PATIENCE = 10

# ----------------------------------------------------------
# 5. Feature Engineering에서 사용할 컬럼 목록
# ----------------------------------------------------------
# 원본 OHLCV + 파생 피처를 합쳐 LSTM 입력으로 사용한다.
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
