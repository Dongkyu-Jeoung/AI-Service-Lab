import { useEffect, useState } from "react";
import "./App.css";

import Header from "./components/Header";
import UserSearch from "./components/UserSearch";
import UserProfile from "./components/UserProfile";
import FavoriteGenres from "./components/FavoriteGenres";
import RatingHistory from "./components/RatingHistory";
import RecommendationList from "./components/RecommendationList";
import {
  getModelInfo,
  getUserProfile,
  getUserRatings,
  recommendForUser,
  searchUsers,
} from "./services/api";

const SEARCH_DEBOUNCE_MS = 300;
const TOP_N_DEFAULT = 10;

function extractErrorMessage(error) {
  const response = error?.response;

  if (!response) {
    return "FastAPI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.";
  }
  if (response.status === 503) {
    return response.data?.detail ?? "추천 모델이 아직 준비되지 않았습니다.";
  }
  if (response.status === 404) {
    return response.data?.detail ?? "요청한 대상을 찾을 수 없습니다.";
  }
  if (response.status === 422) {
    const details = response.data?.details;
    if (Array.isArray(details) && details.length > 0) {
      return details.map((item) => item.msg).join("\n");
    }
    return response.data?.error ?? "입력값을 확인해주세요.";
  }
  return response.data?.detail ?? "알 수 없는 오류가 발생했습니다.";
}

export default function App() {
  const [modelInfo, setModelInfo] = useState(null);

  // 사용자 선택 화면 상태
  const [query, setQuery] = useState("");
  const [minRatings, setMinRatings] = useState(0);
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);

  // 선택된 사용자 / 대시보드 상태
  const [selectedUser, setSelectedUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [ratingHistory, setRatingHistory] = useState([]);
  const [topN, setTopN] = useState(TOP_N_DEFAULT);
  const [recommendation, setRecommendation] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getModelInfo()
      .then(setModelInfo)
      .catch(() => setModelInfo(null));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setUsersLoading(true);
      searchUsers({ search: query, minRatings, limit: 30 })
        .then(setUsers)
        .catch(() => setUsers([]))
        .finally(() => setUsersLoading(false));
    }, SEARCH_DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [query, minRatings]);

  async function loadDashboard(userId, requestedTopN) {
    setDashboardLoading(true);
    setError("");
    try {
      const [profileData, ratingsData, recommendationData] = await Promise.all([
        getUserProfile(userId),
        getUserRatings(userId, { limit: 8, sort: "rating" }),
        recommendForUser({ userId, topN: requestedTopN }),
      ]);
      setProfile(profileData);
      setRatingHistory(ratingsData);
      setRecommendation(recommendationData);
    } catch (err) {
      setError(extractErrorMessage(err));
      setRecommendation(null);
    } finally {
      setDashboardLoading(false);
    }
  }

  function handleSelectUser(user) {
    setSelectedUser(user);
    setProfile(null);
    setRatingHistory([]);
    setRecommendation(null);
    setTopN(TOP_N_DEFAULT);
    loadDashboard(user.user_id, TOP_N_DEFAULT);
  }

  function handleBackToSelection() {
    setSelectedUser(null);
    setProfile(null);
    setRatingHistory([]);
    setRecommendation(null);
    setError("");
  }

  function handleTopNChange(nextTopN) {
    setTopN(nextTopN);
    if (selectedUser) {
      loadDashboard(selectedUser.user_id, nextTopN);
    }
  }

  function handleRetry() {
    if (selectedUser) {
      loadDashboard(selectedUser.user_id, topN);
    }
  }

  return (
    <main className="page">
      <Header modelLoaded={modelInfo?.model_loaded !== false} />

      {!selectedUser && (
        <section className="panel selection-panel">
          <h2>사용자 선택</h2>
          <p className="panel-subtitle">
            MovieLens 사용자 중 한 명을 선택하면 평점 이력을 분석해 맞춤 추천을 보여드립니다.
            (실제 로그인이 아닌 교육용 데모 사용자 선택입니다.)
          </p>
          <UserSearch
            query={query}
            onQueryChange={setQuery}
            minRatings={minRatings}
            onMinRatingsChange={setMinRatings}
            users={users}
            loading={usersLoading}
            onSelectUser={handleSelectUser}
          />
        </section>
      )}

      {selectedUser && (
        <section className="dashboard">
          <div className="panel profile-panel">
            <div className="profile-panel-header">
              <h2>사용자 대시보드</h2>
              <button type="button" className="secondary-button" onClick={handleBackToSelection}>
                다른 사용자 선택
              </button>
            </div>

            {profile && (
              <>
                <UserProfile profile={profile} />
                <FavoriteGenres genres={profile.favorite_genres} />
                <RatingHistory ratings={ratingHistory} />
              </>
            )}
          </div>

          <div className="panel result-panel-wrapper">
            <div className="result-panel-header">
              <h2>개인화 추천 결과</h2>
              <div className="field top-n-field">
                <label htmlFor="top-n">추천 개수</label>
                <select
                  id="top-n"
                  value={topN}
                  onChange={(e) => handleTopNChange(Number(e.target.value))}
                  disabled={dashboardLoading}
                >
                  {[5, 10, 15, 20].map((n) => (
                    <option key={n} value={n}>
                      {n}개
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <RecommendationList
              recommendation={recommendation}
              loading={dashboardLoading}
              error={error}
              onRetry={handleRetry}
            />
          </div>
        </section>
      )}

      <footer className="page-footer">
        추천 결과는 MovieLens 100K 데이터 기반의 통계적 개인화 추천이며, 실제 취향과 다를 수 있습니다.
      </footer>
    </main>
  );
}
