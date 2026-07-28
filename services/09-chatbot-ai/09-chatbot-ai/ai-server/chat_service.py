# chat_service.py
# ==========================================================
# Chatbot AI - 대화 기록 관리 + OpenAI API 호출
#
# services/09-llm-1day/PART6_FastAPI_Chatbot.md 의 라이브코딩을 그대로 서비스화한 것.
#
#   - session_id 별로 대화 기록(messages)을 서버 메모리에 저장한다.
#   - 매 요청마다 "지금까지의 전체 대화"를 다시 OpenAI API에 전달해서,
#     모델이 이전 대화를 "기억하는 것처럼" 보이게 만든다.
#   - GPT 자체는 추론 중 학습하지 않는다(PART3 참고). 기억은 이 저장소가 만든다.
# ==========================================================

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# API Key가 없으면 클라이언트를 만들지 않는다.
# (main.py가 이 값을 보고 서버는 켜두되 /chat만 503으로 안내하도록 방어적으로 동작한다.)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = (
    "당신은 친절하고 간결하게 답하는 AI 어시스턴트입니다. "
    "모르는 내용은 모른다고 솔직하게 답하세요."
)

MAX_HISTORY_MESSAGES = 20  # system 제외, user/assistant 합산 (Context Window 관리용, PART3 참고)

# session_id -> messages 리스트 ([{role, content}, ...])
# 실무에서는 Redis/DB를 사용하지만, 이 프로젝트는 원리를 보여주는 것이 목적이라 메모리로 충분하다.
conversation_store: dict[str, list[dict]] = {}


def get_or_create_conversation(session_id: str) -> list[dict]:
    if session_id not in conversation_store:
        conversation_store[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return conversation_store[session_id]


def _trim_history(messages: list[dict]) -> None:
    """system 메시지를 제외한 대화가 너무 길어지면 오래된 것부터 제거한다."""
    system_messages = [m for m in messages if m["role"] == "system"]
    other_messages = [m for m in messages if m["role"] != "system"]

    if len(other_messages) > MAX_HISTORY_MESSAGES:
        other_messages = other_messages[-MAX_HISTORY_MESSAGES:]
        messages[:] = system_messages + other_messages


def ask_chatbot(session_id: str, user_message: str, temperature: float = 0.7):
    """사용자 메시지를 대화 기록에 추가하고, GPT 응답을 받아 다시 기록한다.

    Returns:
        (reply: str, usage: openai.types.CompletionUsage)
    Raises:
        RuntimeError: OPENAI_API_KEY가 설정되지 않은 경우
    """
    if client is None:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    messages = get_or_create_conversation(session_id)
    messages.append({"role": "user", "content": user_message})
    _trim_history(messages)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    return reply, response.usage


def reset_conversation(session_id: str) -> None:
    conversation_store.pop(session_id, None)


def get_history(session_id: str) -> list[dict]:
    return conversation_store.get(session_id, [])
