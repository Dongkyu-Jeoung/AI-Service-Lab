// components/UserSearch.jsx
// 사용자 검색 + 최소 평점 수 필터 + 사용자 카드 목록

import UserCard from "./UserCard";

const MIN_RATINGS_OPTIONS = [0, 20, 50, 100, 200];

export default function UserSearch({
  query,
  onQueryChange,
  minRatings,
  onMinRatingsChange,
  users,
  loading,
  onSelectUser,
}) {
  return (
    <div className="user-search">
      <div className="user-search-filters">
        <div className="field">
          <label htmlFor="user-query">사용자 검색 (ID 또는 직업)</label>
          <input
            id="user-query"
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="예: 1, student, engineer..."
            autoComplete="off"
          />
        </div>

        <div className="field">
          <label htmlFor="min-ratings">최소 평점 수</label>
          <select
            id="min-ratings"
            value={minRatings}
            onChange={(e) => onMinRatingsChange(Number(e.target.value))}
          >
            {MIN_RATINGS_OPTIONS.map((n) => (
              <option key={n} value={n}>
                {n === 0 ? "제한 없음" : `${n}건 이상`}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <p className="search-status">사용자를 불러오는 중...</p>}
      {!loading && users.length === 0 && <p className="search-status">조건에 맞는 사용자가 없습니다.</p>}

      <div className="user-card-grid">
        {!loading &&
          users.map((user) => <UserCard key={user.user_id} user={user} onSelect={onSelectUser} />)}
      </div>
    </div>
  );
}
