// components/RatingHistory.jsx
// 사용자가 높게 평가한 영화 목록 (최근/평점순 정렬은 API에서 처리)

export default function RatingHistory({ ratings }) {
  if (!ratings || ratings.length === 0) {
    return null;
  }

  return (
    <div className="rating-history">
      <p className="section-label">높게 평가한 영화</p>
      <ul className="rating-history-list">
        {ratings.map((item) => (
          <li key={item.movie_id} className="rating-history-item">
            <span className="rating-history-title">{item.title}</span>
            <span className="rating-history-score">⭐ {item.rating}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
