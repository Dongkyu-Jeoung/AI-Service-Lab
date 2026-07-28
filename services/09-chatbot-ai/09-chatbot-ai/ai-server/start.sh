#!/bin/bash

echo "Chatbot AI - 서버 시작 준비"

# main.py는 python-dotenv로 .env를 읽지만, 이 스크립트의 안내 메시지가
# 실제 설정 여부와 어긋나지 않도록 셸에서도 .env를 함께 읽어들인다.
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "======================================================"
    echo "[안내] OPENAI_API_KEY 환경변수가 설정되지 않았습니다."
    echo "  .env.example 을 복사해 .env 파일을 만들고, OPENAI_API_KEY를"
    echo "  채운 뒤 컨테이너를 다시 시작하세요."
    echo "  서버는 정상적으로 시작되지만, /chat 요청 시 503 오류를 반환합니다."
    echo "======================================================"
else
    echo "OPENAI_API_KEY를 확인했습니다."
fi

echo "FastAPI 서버를 시작합니다."

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000
