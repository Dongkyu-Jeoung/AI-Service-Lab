import { useEffect, useState } from "react";
import "./App.css";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import { getServiceStatus, resetChat, sendMessage } from "./services/api";

const SESSION_STORAGE_KEY = "chatbot_ai_session_id";

function getOrCreateSessionId() {
  let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

function extractErrorMessage(error) {
  const response = error?.response;

  if (!response) {
    return "FastAPI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.";
  }

  if (response.status === 503) {
    return response.data?.detail ?? "챗봇이 아직 준비되지 않았습니다.";
  }

  if (response.status === 422) {
    const details = response.data?.details;
    if (Array.isArray(details) && details.length > 0) {
      return details.map((item) => item.msg).join("\n");
    }
    return response.data?.error ?? "입력값을 확인해주세요.";
  }

  return response.data?.detail ?? "알 수 없는 오류가 발생했습니다.";
}

export default function App() {
  const [sessionId] = useState(getOrCreateSessionId);
  const [status, setStatus] = useState(null);

  const [messages, setMessages] = useState([
    { role: "assistant", content: "안녕하세요! 무엇을 도와드릴까요?" },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUsage, setLastUsage] = useState(null);

  useEffect(() => {
    getServiceStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  async function handleSend(text) {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setError("");
    setLoading(true);

    try {
      const data = await sendMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      setLastUsage({
        prompt: data.prompt_tokens,
        completion: data.completion_tokens,
        total: data.total_tokens,
      });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    try {
      await resetChat(sessionId);
    } catch {
      // 세션이 이미 없는 경우 등은 무시하고 화면만 초기화한다.
    }
    setMessages([{ role: "assistant", content: "대화가 초기화되었습니다. 무엇을 도와드릴까요?" }]);
    setLastUsage(null);
    setError("");
  }

  return (
    <main className="page">
      <header className="page-header">
        <p className="badge">AI Service Blueprint</p>
        <h1>Chatbot AI</h1>
        <p className="subtitle">OpenAI API 기반 세션형 대화 챗봇입니다.</p>
        {status?.api_key_configured === false && (
          <p className="model-warning">
            아직 OPENAI_API_KEY가 설정되지 않았습니다. ai-server/.env 파일에 API Key를 추가한 뒤
            서버를 다시 시작하면 대화를 시작할 수 있습니다.
          </p>
        )}
      </header>

      <section className="panel chat-panel">
        <div className="chat-panel-header">
          <h2>대화</h2>
          <button className="secondary-button reset-button" onClick={handleReset}>
            대화 초기화
          </button>
        </div>

        <ChatWindow messages={messages} loading={loading} />

        {error && <p className="chat-error">{error}</p>}

        <ChatInput onSend={handleSend} disabled={loading} />

        {lastUsage && (
          <p className="token-usage">
            Token 사용량 (최근 응답) — 질문 {lastUsage.prompt} / 답변 {lastUsage.completion} / 합계{" "}
            {lastUsage.total}
          </p>
        )}
      </section>

      <footer className="page-footer">
        대화 내용은 서버 메모리에 세션 단위로만 저장되며, 서버가 재시작되면 초기화됩니다.
      </footer>
    </main>
  );
}
