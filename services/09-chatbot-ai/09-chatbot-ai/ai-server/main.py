# ==========================================================
# Chatbot AI - FastAPI
# OpenAI API 기반 세션형 대화 챗봇 서비스
#
# services/09-llm-1day/PART6_FastAPI_Chatbot.md, PART7_React_연결.md 의
# 라이브코딩 결과를 services/06-movie-recommendation-ai 와 동일한 구조로 서비스화한 것.
# ==========================================================

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from chat_service import (
    MODEL_NAME,
    ask_chatbot,
    client as openai_client,
    get_history,
    reset_conversation,
)


# ==========================================================
# 1. 상수
# ==========================================================

API_KEY_CONFIGURED = openai_client is not None


# ==========================================================
# 2. FastAPI 앱 생성 및 CORS 설정
# ==========================================================

app = FastAPI(
    title="Chatbot AI",
    description="OpenAI API 기반 세션형 대화 챗봇 서비스 (교육/포트폴리오 목적)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sanitize_validation_errors(errors):
    """Pydantic 오류의 ctx에 담긴 예외 객체(JSON으로 직렬화 불가능)를 문자열로 바꾼다."""
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
            {
                "error": "입력값을 확인해주세요.",
                "details": _sanitize_validation_errors(exc.errors()),
            }
        ),
    )


# ==========================================================
# 3. 요청 / 응답 스키마
# ==========================================================

class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="대화 세션을 구분하는 ID (프론트에서 발급)")
    message: str = Field(..., min_length=1, description="사용자 메시지")
    temperature: float = Field(
        0.7, ge=0.0, le=2.0, description="응답의 다양성 정도 (0=일관적, 2=창의적, PART3 참고)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {"session_id": "demo-001", "message": "LLM이 뭔지 한 문장으로 설명해줘.", "temperature": 0.7}
        }
    }


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatMessage(BaseModel):
    role: str
    content: str


# ==========================================================
# 4. Root / Health Check
# ==========================================================

@app.get("/")
def root():
    return {
        "service": "Chatbot AI",
        "status": "running",
        "model": MODEL_NAME,
        "api_key_configured": API_KEY_CONFIGURED,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_key_configured": API_KEY_CONFIGURED,
    }


# ==========================================================
# 5. 챗봇 API
# ==========================================================

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    if not API_KEY_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY가 설정되지 않았습니다. "
                "ai-server/.env 파일에 OPENAI_API_KEY를 추가한 뒤 서버를 다시 시작하세요."
            ),
        )

    try:
        reply, usage = ask_chatbot(payload.session_id, payload.message, payload.temperature)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:  # noqa: BLE001 - OpenAI API 오류를 그대로 노출하지 않고 감싼다.
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류가 발생했습니다: {error}")

    return ChatResponse(
        session_id=payload.session_id,
        reply=reply,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
    )


@app.post("/chat/reset")
def chat_reset(session_id: str = Query(..., description="초기화할 세션 ID")):
    reset_conversation(session_id)
    return {"session_id": session_id, "message": "대화 기록이 초기화되었습니다."}


@app.get("/chat/history")
def chat_history(session_id: str = Query(..., description="조회할 세션 ID")):
    history = get_history(session_id)
    visible_messages = [ChatMessage(role=m["role"], content=m["content"]) for m in history if m["role"] != "system"]
    return {"session_id": session_id, "messages": visible_messages}
