# services/model_loader.py
# ==========================================================
# ai-model이 저장한 아티팩트(model.keras, scaler.pkl, metadata.json)를
# 읽어와 메모리에 캐싱한다. 요청마다 디스크에서 모델을 다시 읽으면 느리므로,
# 한 번 로드한 모델은 프로세스가 살아있는 동안 재사용한다.
# ==========================================================

import json
import pickle
from functools import lru_cache
from pathlib import Path

from tensorflow import keras

from core.config import ARTIFACTS_DIR


class ModelBundle:
    """한 종목에 대한 model + scaler + metadata를 묶어서 다루는 컨테이너."""

    def __init__(self, ticker: str, model: keras.Model, scaler, metadata: dict):
        self.ticker = ticker
        self.model = model
        self.scaler = scaler
        self.metadata = metadata


def get_trained_tickers() -> list[str]:
    """artifacts/ 폴더를 스캔해서 실제로 학습이 완료된(model.keras가 존재하는) 종목 목록을 반환한다."""
    if not ARTIFACTS_DIR.exists():
        return []

    tickers = []
    for path in sorted(ARTIFACTS_DIR.iterdir()):
        if path.is_dir() and (path / "model.keras").exists():
            tickers.append(path.name)
    return tickers


def is_ticker_trained(ticker: str) -> bool:
    return (ARTIFACTS_DIR / ticker / "model.keras").exists()


@lru_cache(maxsize=8)
def load_model_bundle(ticker: str) -> ModelBundle:
    """모델/스케일러/메타데이터를 로드한다. 같은 ticker는 캐시되어 재사용된다.

    Raises:
        FileNotFoundError: 해당 ticker의 학습된 모델이 없는 경우
    """
    ticker_dir = ARTIFACTS_DIR / ticker

    model_path = ticker_dir / "model.keras"
    scaler_path = ticker_dir / "scaler.pkl"
    metadata_path = ticker_dir / "metadata.json"

    if not model_path.exists():
        raise FileNotFoundError(
            f"'{ticker}' 종목의 학습된 모델을 찾을 수 없습니다. "
            f"먼저 ai-model/src/train.py --ticker {ticker} 를 실행해 모델을 학습하세요."
        )

    model = keras.models.load_model(model_path)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    return ModelBundle(ticker=ticker, model=model, scaler=scaler, metadata=metadata)


def clear_cache() -> None:
    """테스트/재학습 후 캐시를 비우고 싶을 때 사용."""
    load_model_bundle.cache_clear()
