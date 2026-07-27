// components/UserProfile.jsx
// 선택된 사용자의 기본 정보 + 평점 통계 + 활동 기간

export default function UserProfile({ profile }) {
  return (
    <div className="user-profile">
      <div className="user-profile-header">
        <p className="selected-label">선택한 사용자</p>
        <p className="selected-title">User #{profile.user_id}</p>
        <p className="user-profile-basic">
          {profile.age}세 · {profile.gender === "M" ? "남성" : "여성"} · {profile.occupation}
        </p>
      </div>

      <div className="stat-grid">
        <div className="stat-box">
          <span className="stat-label">평점 개수</span>
          <span className="stat-value">{profile.rating_count}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">평균 평점</span>
          <span className="stat-value">⭐ {profile.rating_mean}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">평점 표준편차</span>
          <span className="stat-value">{profile.rating_std}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">활동 수준</span>
          <span className="stat-value">{profile.activity_level}</span>
        </div>
      </div>

      <p className="user-profile-activity">
        활동 기간: {profile.first_rating_date ?? "-"} ~ {profile.last_rating_date ?? "-"} (
        {profile.active_days}일)
        {profile.preferred_release_year && ` · 선호 개봉연도대: ${profile.preferred_release_year}년경`}
      </p>
    </div>
  );
}
