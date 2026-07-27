// components/RecommendationCard.jsx

export default function RecommendationCard({ movie, rank }) {
  return (
    <div className="recommendation-card">
      <div className="poster-placeholder">
        <span>{rank}</span>
      </div>
      <div className="recommendation-body">
        <p className="recommendation-title">
          {movie.title}
          {movie.release_year ? ` (${movie.release_year})` : ""}
        </p>
        <p className="recommendation-genres">{movie.genres?.join(", ")}</p>
        <p className="recommendation-reason">{movie.recommendation_reason}</p>

        <div className="recommendation-meta">
          <span>하이브리드 {Math.round(movie.hybrid_score * 100)}%</span>
          {movie.predicted_rating != null && <span>예측 평점 {movie.predicted_rating}</span>}
          <span>⭐ {movie.average_rating}</span>
          <span>평가 {movie.rating_count}건</span>
        </div>

        <div className="recommendation-scores">
          {movie.content_score != null && <span>콘텐츠 {movie.content_score}</span>}
          {movie.collaborative_score != null && <span>협업 필터링 {movie.collaborative_score}</span>}
          {movie.svd_score != null && <span>SVD {movie.svd_score}</span>}
          {movie.popularity_score != null && <span>인기도 {movie.popularity_score}</span>}
        </div>
      </div>
    </div>
  );
}
