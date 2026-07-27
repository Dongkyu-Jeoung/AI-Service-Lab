// components/FavoriteGenres.jsx
// 사용자 선호 장르 배지 목록

export default function FavoriteGenres({ genres }) {
  if (!genres || genres.length === 0) {
    return null;
  }

  return (
    <div className="favorite-genres">
      <p className="section-label">선호 장르</p>
      <div className="genre-badge-list">
        {genres.map((genre) => (
          <span key={genre} className="genre-badge">
            {genre}
          </span>
        ))}
      </div>
    </div>
  );
}
