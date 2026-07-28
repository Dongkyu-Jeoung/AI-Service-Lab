import { useEffect, useRef } from "react";

export default function ChatWindow({ messages, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="chat-window">
      {messages.map((msg, index) => (
        <div key={index} className={`chat-bubble ${msg.role}`}>
          <span className="chat-role">{msg.role === "user" ? "나" : "AI"}</span>
          <p>{msg.content}</p>
        </div>
      ))}

      {loading && (
        <div className="chat-bubble assistant loading">
          <span className="chat-role">AI</span>
          <p>답변을 작성 중입니다...</p>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
