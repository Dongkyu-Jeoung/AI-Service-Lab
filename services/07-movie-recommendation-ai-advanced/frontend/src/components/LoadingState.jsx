// components/LoadingState.jsx

export default function LoadingState({ message = "추천을 계산하고 있습니다..." }) {
  return (
    <div className="result-panel state-loading">
      <div className="spinner" />
      <p>{message}</p>
    </div>
  );
}
