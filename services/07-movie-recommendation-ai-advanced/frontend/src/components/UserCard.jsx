// components/UserCard.jsx
// 사용자 선택 화면의 데모 사용자 카드 (user_id를 숫자로 직접 입력하지 않고 카드에서 선택)

const ACTIVITY_BADGE_CLASS = {
  "Low Activity": "activity-low",
  "Medium Activity": "activity-medium",
  "High Activity": "activity-high",
  "Power User": "activity-power",
};

export default function UserCard({ user, onSelect }) {
  return (
    <button type="button" className="user-card" onClick={() => onSelect(user)}>
      <div className="user-card-top">
        <span className="user-card-id">User #{user.user_id}</span>
        <span className={`activity-badge ${ACTIVITY_BADGE_CLASS[user.activity_level] ?? ""}`}>
          {user.activity_level}
        </span>
      </div>
      <p className="user-card-meta">
        {user.age}세 · {user.gender === "M" ? "남성" : "여성"} · {user.occupation}
      </p>
      <p className="user-card-stats">
        평점 {user.rating_count}건 · 평균 ⭐ {user.rating_mean}
      </p>
      {user.favorite_genres?.length > 0 && (
        <p className="user-card-genres">선호 장르: {user.favorite_genres.join(", ")}</p>
      )}
    </button>
  );
}
