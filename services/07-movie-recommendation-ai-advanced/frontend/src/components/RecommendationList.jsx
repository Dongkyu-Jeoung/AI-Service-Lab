// components/RecommendationList.jsx
// 초기 안내 / Loading / 오류 / 추천 전략 설명 / 추천 결과 카드 목록

import LoadingState from "./LoadingState";
import ErrorState from "./ErrorState";
import RecommendationCard from "./RecommendationCard";

const STRATEGY_EXPLANATION = {
  "Low Activity": "이 사용자는 평점 이력이 적어 인기도와 콘텐츠(장르) 기반 추천 비중을 높여 대체 추천을 제공합니다.",
  "Medium Activity": "이 사용자는 평점 이력이 어느 정도 쌓여 콘텐츠 기반과 협업 필터링을 균형 있게 사용했습니다.",
  "High Activity": "이 사용자는 평점 이력이 충분하여 협업 필터링과 SVD(잠재 요인) 비중을 높여 추천했습니다.",
  "Power User": "이 사용자는 활동량이 매우 많아 협업 필터링과 SVD를 중심으로 정교한 개인화 추천을 제공했습니다.",
};

export default function RecommendationList({ recommendation, loading, error, onRetry }) {
  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }

  if (!recommendation) {
    return (
      <div className="result-panel state-empty">
        <p className="state-title">추천을 받을 사용자를 선택해 주세요</p>
        <p className="state-message">
          왼쪽 목록에서 사용자를 선택하면 취향 프로필과 개인화 추천 결과를 확인할 수 있습니다.
        </p>
      </div>
    );
  }

  const { user, recommendations } = recommendation;
  const explanation = STRATEGY_EXPLANATION[user.activity_level] ?? "";

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="result-panel state-empty">
        <p className="state-title">추천 결과가 없습니다</p>
        <p className="state-message">이 사용자에게 추천할 새로운 영화를 찾지 못했습니다.</p>
      </div>
    );
  }

  return (
    <div className="result-panel state-result">
      <div className="strategy-explanation">
        <span className="algorithm-badge">Hybrid Recommendation</span>
        <p>{explanation}</p>
      </div>

      <div className="recommendation-list">
        {recommendations.map((movie, index) => (
          <RecommendationCard key={movie.movie_id} movie={movie} rank={index + 1} />
        ))}
      </div>
    </div>
  );
}
