// components/ErrorState.jsx

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="result-panel state-error">
      <p className="state-title">추천을 불러오지 못했습니다</p>
      <p className="state-message">{message}</p>
      {onRetry && (
        <button type="button" className="secondary-button" onClick={onRetry}>
          다시 시도
        </button>
      )}
    </div>
  );
}
