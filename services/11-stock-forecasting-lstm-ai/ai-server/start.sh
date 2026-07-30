#!/bin/bash

echo "Stock Forecasting AI - 서버 시작 준비"

if [ ! -d "${ARTIFACTS_DIR:-/app/ai-model-artifacts}" ] || [ -z "$(ls -A "${ARTIFACTS_DIR:-/app/ai-model-artifacts}" 2>/dev/null)" ]; then
    echo "======================================================"
    echo "[안내] 학습된 모델(artifacts)을 찾을 수 없습니다."
    echo "  먼저 ai-model/src/train.py --ticker AAPL 을 실행해 모델을 학습하세요."
    echo "  서버는 정상적으로 시작되지만, /predict 요청 시 404 오류를 반환합니다."
    echo "======================================================"
else
    echo "학습된 모델을 확인했습니다."
fi

echo "FastAPI 서버를 시작합니다."

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000
