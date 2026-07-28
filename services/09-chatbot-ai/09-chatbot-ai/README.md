# Chatbot AI

OpenAI API를 기반으로, 세션 단위로 대화 맥락을 기억하는 AI 챗봇 서비스입니다.

> 이 서비스는 교육 및 포트폴리오 목적으로 제작되었으며, `services/09-llm-1day`(LLM 1Day 강의)의
> PART 6(FastAPI Chatbot), PART 7(React 연결) 라이브코딩 로직을
> `services/06-movie-recommendation-ai`와 동일한 구조로 서비스화한 것입니다.

---

## 1. 프로젝트 소개

사용자가 채팅창에 메시지를 입력하면 OpenAI GPT 모델이 답변하는 서비스입니다. 로그인 없이 브라우저
세션(`session_id`) 단위로 대화가 이어지며, "대화 초기화" 버튼으로 언제든 새 대화를 시작할 수
있습니다.

## 2. 주요 기능

- 세션 단위 대화 기억 (같은 세션 내에서는 이전 대화를 참고해서 답변)
- 대화 초기화 기능
- 대화 기록 조회 API (`/chat/history`)
- Token 사용량 표시 (질문/답변/합계, 최근 응답 기준)
- OpenAI API Key 미설정 시에도 서버는 정상 기동하고, `/chat` 요청에만 503으로 안내 (Fail-soft 설계)

## 3. 기술 스택

**Backend**: Python, FastAPI, Uvicorn, OpenAI Python SDK, python-dotenv, Pydantic
**Frontend**: React, Vite, JavaScript, Axios
**실행 환경**: Docker, Docker Compose

## 4. 폴더 구조

```text
services/09-chatbot-ai/
├── ai-server/
│   ├── chat_service.py       # 대화 기록 관리 + OpenAI API 호출
│   ├── main.py                # FastAPI 앱 (/chat, /chat/reset, /chat/history 등)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example           # 이 파일을 복사해 .env로 만들고 API Key 입력
│   └── start.sh
├── frontend/
│   ├── public/favicon.svg
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   └── ChatInput.jsx
│   │   ├── services/api.js
│   │   ├── App.jsx / App.css
│   │   ├── main.jsx / index.css
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 5. OpenAI API Key 준비

이 저장소에는 API Key가 포함되어 있지 않습니다. 아래 순서로 준비하세요.

```bash
cd services/09-chatbot-ai/ai-server
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY=sk-... 를 실제 발급받은 키로 채워 넣기
```

API Key 발급 방법 및 보안 주의사항은
[`services/09-llm-1day/PART5_OpenAI_API.md`](../09-llm-1day/PART5_OpenAI_API.md) 4.1절을
참고하세요. `.env` 파일은 Git에 절대 커밋되지 않도록 `.gitignore`에 등록되어 있습니다.

## 6. 로컬 실행

```bash
# Backend
cd services/09-chatbot-ai/ai-server
pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY 입력 후 저장
uvicorn main:app --reload

# Frontend
cd services/09-chatbot-ai/frontend
npm install
npm run dev
```

## 7. Docker 실행

```bash
cd services/09-chatbot-ai
docker compose up --build -d
docker compose ps
docker compose logs -f
docker compose down
```

`ai-server/.env`가 아직 없어도 `docker compose up` 자체는 정상적으로 동작합니다(`./ai-server:/app`
볼륨 마운트로 컨테이너가 호스트의 `ai-server` 폴더를 그대로 사용하므로, `.env`를 나중에
추가하고 `docker compose restart backend`만 해도 즉시 반영됩니다).

`ai-server/start.sh`가 컨테이너 시작 시 다음과 같이 동작합니다.

```text
OPENAI_API_KEY 있음   -> 정상 안내 후 FastAPI 실행
OPENAI_API_KEY 없음   -> 경고 메시지 출력, 그래도 서버는 실행 (단, /chat은 503 반환)
```

## 8. 접속 주소

| 서비스 | 주소 |
|---|---|
| Backend (FastAPI) | http://localhost:8000 |
| Swagger 문서 | http://localhost:8000/docs |
| Frontend (React/Vite) | http://localhost:5173 |

## 9. API 목록

| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 서비스 상태 (모델명, API Key 설정 여부) |
| GET | `/health` | Health Check |
| POST | `/chat` | 메시지 전송 (`{"session_id": "...", "message": "...", "temperature": 0.7}`) |
| POST | `/chat/reset?session_id=...` | 세션 대화 기록 초기화 |
| GET | `/chat/history?session_id=...` | 세션 대화 기록 조회 (system 메시지 제외) |

`POST /chat` 응답 예시:

```json
{
  "session_id": "demo-001",
  "reply": "LLM은 방대한 텍스트를 학습해 다음에 올 단어를 예측하며 문장을 생성하는 인공지능 모델입니다.",
  "prompt_tokens": 32,
  "completion_tokens": 28,
  "total_tokens": 60
}
```

`OPENAI_API_KEY`가 설정되지 않았으면 503, 요청 형식이 잘못되면 422, OpenAI API 호출 중 오류가
발생하면 500을 반환합니다.

## 10. 대화 기억 방식 (세션)

GPT 모델 자체는 요청마다 완전히 독립적으로 추론하며 아무것도 "기억"하지 않습니다. 이 서비스는
`session_id`별로 지금까지의 대화(`messages` 리스트)를 서버 메모리(`conversation_store`)에 저장해
두었다가, 매 요청마다 전체 대화를 다시 OpenAI API에 통째로 전달하는 방식으로 "기억하는 것처럼"
동작합니다. 원리는
[`services/09-llm-1day/PART6_FastAPI_Chatbot.md`](../09-llm-1day/PART6_FastAPI_Chatbot.md)
4.2절을 참고하세요.

대화가 너무 길어지는 것(Context Window 초과)을 막기 위해, `chat_service.py`의
`MAX_HISTORY_MESSAGES`(기본 20개)를 넘는 오래된 메시지는 자동으로 제거됩니다.

서버가 재시작되면 메모리에 저장된 모든 세션 기록이 사라집니다(교육/포트폴리오 목적의 단순화이며,
실무에서는 Redis/DB로 영속화합니다).

## 11. 문제 해결

| 증상 | 원인 / 해결 |
|---|---|
| `/chat`이 503을 반환 | `OPENAI_API_KEY`가 설정되지 않았습니다. `ai-server/.env`를 확인하고 서버를 재시작하세요. |
| `/chat`이 500을 반환 | OpenAI API Key가 유효하지 않거나, 네트워크/요금 한도 문제일 수 있습니다. 서버 로그를 확인하세요. |
| React에서 "서버에 연결할 수 없습니다" | FastAPI가 실행 중인지, Docker Compose라면 `backend` 컨테이너가 정상인지 확인하세요(`docker compose logs backend`). |
| `.env`를 만들었는데도 `api_key_configured`가 `false` | Docker Compose는 `./ai-server:/app` 볼륨 마운트로 `.env`를 즉시 반영하지만, 컨테이너를 재시작(`docker compose restart backend`)해야 `python-dotenv`가 다시 읽습니다. |
| 대화가 이어지지 않고 매번 처음 인사말만 나옴 | 브라우저 `sessionStorage`가 초기화된 것입니다(탭을 완전히 닫았다 열거나 시크릿 모드 재진입 시 발생). 서버 쪽 세션은 남아있을 수 있으니 `/chat/history?session_id=...`로 확인할 수 있습니다. |

## 12. Movie Recommendation AI(06)와 공통된 구조

- Backend/Frontend 분리, FastAPI + React(Vite) 구성
- CORS, 422 검증 오류 처리, Swagger 문서 자동 생성
- `start.sh`가 사전 조건(06은 모델 파일, 09는 API Key)을 확인하고 안내 메시지를 출력하는 방식
- 서버가 핵심 산출물(06은 추천 모델, 09는 API Key) 없이도 켜지고, 실제 기능 호출 시점에만 503으로
  방어적으로 안내하는 Fail-soft 설계
- React의 Loading/Error 상태 UI 패턴, `services/api.js` 하나로 API 호출을 집중시키는 구조

## 13. Movie Recommendation AI(06)와 달라진 부분

- 문제 유형: 추천(유사 아이템 랭킹) → 생성(대화형 텍스트 생성)
- 모델: 자체 학습한 유사도 행렬(`.pkl`) → OpenAI의 사전학습된 GPT 모델을 API로 호출
- 데이터 준비: MovieLens 100K 데이터셋 다운로드 → OpenAI API Key 발급
- 상태 관리: 학습된 모델 파일의 존재 여부 → 세션별 대화 기록(서버 메모리)
- 학습 스크립트: `train_model.py` 별도 실행 필요 → 별도 학습 없이 즉시 API 호출 가능(사전학습 완료된
  모델을 그대로 사용)

## 14. 관련 자료

- [`services/09-llm-1day/PART6_FastAPI_Chatbot.md`](../09-llm-1day/PART6_FastAPI_Chatbot.md) —
  이 서비스의 백엔드 로직(세션 관리, 대화 기억)의 원본 강의 자료
- [`services/09-llm-1day/PART7_React_연결.md`](../09-llm-1day/PART7_React_연결.md) — 이 서비스의
  프론트엔드 구조(ChatWindow, ChatInput, api.js)의 원본 강의 자료
