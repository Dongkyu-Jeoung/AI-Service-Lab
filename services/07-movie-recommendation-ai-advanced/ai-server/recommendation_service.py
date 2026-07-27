# recommendation_service.py
# ---------------------------------------------------------------
# Movie Recommendation AI Advanced - 추천 계산 로직
#
# train_model.py가 저장한 산출물(models/*.pkl, recommendation_config.json)만 로드하여
# 요청마다 다시 학습하지 않고 추천을 계산한다. FastAPI 라우터(main.py)는 이 모듈의 함수를
# 호출하고 입출력/오류 처리만 담당한다.
#
# 하이브리드 추천 조합:
#   hybrid_score = w1*content_score + w2*collaborative_score + w3*svd_score + w4*popularity_score
#   가중치(w1~w4)는 사용자 활동 수준(activity_level)별로 다르게 적용한다
#   (recommendation_config.json의 hybrid_weights_by_activity, 근거는 Research_Report.md 11.8절).
# ---------------------------------------------------------------

import json
import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from feature_engineering import (
    GENRE_COLUMNS,
    combine_weighted_scores,
    get_genre_preference_vector,
    normalize_scores,
)


MODEL_DIR = "models"
PATHS = {
    "movie_features": os.path.join(MODEL_DIR, "movie_features.pkl"),
    "genre_matrix": os.path.join(MODEL_DIR, "genre_matrix.pkl"),
    "user_profiles": os.path.join(MODEL_DIR, "user_profiles.pkl"),
    "item_similarity": os.path.join(MODEL_DIR, "item_similarity.pkl"),
    "user_similarity": os.path.join(MODEL_DIR, "user_similarity.pkl"),
    "svd_model": os.path.join(MODEL_DIR, "svd_model.pkl"),
    "popularity_ranking": os.path.join(MODEL_DIR, "popularity_ranking.pkl"),
    "ratings": os.path.join(MODEL_DIR, "ratings.pkl"),
    "recommendation_config": os.path.join(MODEL_DIR, "recommendation_config.json"),
    "model_info": os.path.join(MODEL_DIR, "model_info.json"),
}

REQUIRED_ARTIFACTS = [
    "movie_features", "genre_matrix", "user_profiles", "item_similarity",
    "user_similarity", "svd_model", "popularity_ranking", "ratings",
]


class RecommendationEngine:
    """저장된 모델 산출물을 한 번만 로드하고, 이후 요청은 메모리에서 바로 계산한다."""

    def __init__(self):
        self.loaded = False
        self.movie_features: Optional[pd.DataFrame] = None
        self.genre_matrix: Optional[pd.DataFrame] = None
        self.user_profiles: Optional[pd.DataFrame] = None
        self.item_similarity: Optional[pd.DataFrame] = None
        self.user_similarity: Optional[pd.DataFrame] = None
        self.svd_predicted_ratings: Optional[pd.DataFrame] = None
        self.popularity_ranking: Optional[pd.DataFrame] = None
        self.ratings: Optional[pd.DataFrame] = None
        self.user_rating_mean: Optional[pd.Series] = None
        self.config: dict = {}
        self.model_info: dict = {}
        self._load()

    def _load(self) -> None:
        missing = [PATHS[key] for key in REQUIRED_ARTIFACTS if not os.path.exists(PATHS[key])]
        if missing:
            print("[안내] 추천 모델 산출물이 없습니다:", ", ".join(missing))
            print("       data/ 폴더에 MovieLens 100K 데이터를 추가한 뒤 train_model.py를 실행하세요.")
            return

        try:
            self.movie_features = joblib.load(PATHS["movie_features"])
            self.genre_matrix = joblib.load(PATHS["genre_matrix"])
            self.user_profiles = joblib.load(PATHS["user_profiles"])
            self.item_similarity = joblib.load(PATHS["item_similarity"])
            self.user_similarity = joblib.load(PATHS["user_similarity"])
            svd_model = joblib.load(PATHS["svd_model"])
            self.svd_predicted_ratings = svd_model["predicted_ratings"]
            self.popularity_ranking = joblib.load(PATHS["popularity_ranking"])
            self.ratings = joblib.load(PATHS["ratings"])
            self.user_rating_mean = self.ratings.groupby("user_id")["rating"].mean()
        except Exception as error:  # noqa: BLE001 - 로딩 실패 시 서버가 죽지 않고 안내만 한다.
            print(f"[경고] 모델 산출물 로딩 중 오류가 발생했습니다: {error}")
            return

        if os.path.exists(PATHS["recommendation_config"]):
            with open(PATHS["recommendation_config"], "r", encoding="utf-8") as f:
                self.config = json.load(f)

        if os.path.exists(PATHS["model_info"]):
            with open(PATHS["model_info"], "r", encoding="utf-8") as f:
                self.model_info = json.load(f)

        self.loaded = True

    # -----------------------------------------------------------
    # 사용자 조회
    # -----------------------------------------------------------

    def user_exists(self, user_id: int) -> bool:
        return self.loaded and user_id in self.user_profiles.index

    def list_users(self, search: str = "", min_ratings: int = 0, limit: int = 50) -> list:
        df = self.user_profiles
        if search.strip():
            keyword = search.strip()
            if keyword.isdigit():
                df = df[df.index == int(keyword)]
            else:
                df = df[df["occupation"].str.contains(keyword, case=False, na=False)]
        if min_ratings > 0:
            df = df[df["rating_count"] >= min_ratings]

        # user_id 순으로 정렬해 활동 수준이 고르게 섞여서 보이도록 한다
        # (평점 개수 내림차순으로만 정렬하면 첫 화면이 Power User로만 채워진다).
        df = df.sort_index().head(limit)

        return [
            {
                "user_id": int(user_id),
                "age": int(row["age"]),
                "gender": row["gender"],
                "occupation": row["occupation"],
                "rating_count": int(row["rating_count"]),
                "rating_mean": round(float(row["rating_mean"]), 2),
                "activity_level": row["activity_level"],
                "favorite_genres": row["favorite_genres"],
            }
            for user_id, row in df.iterrows()
        ]

    def get_user_profile(self, user_id: int) -> dict:
        row = self.user_profiles.loc[user_id]
        top_movies = [self._serialize_movie_brief(m) for m in row["top_rated_movie_ids"]]

        return {
            "user_id": int(user_id),
            "age": int(row["age"]),
            "gender": row["gender"],
            "occupation": row["occupation"],
            "rating_count": int(row["rating_count"]),
            "rating_mean": round(float(row["rating_mean"]), 2),
            "rating_std": round(float(row["rating_std"]), 2),
            "activity_level": row["activity_level"],
            "favorite_genres": row["favorite_genres"],
            "top_rated_movies": top_movies,
            "preferred_release_year": None if pd.isna(row["preferred_release_year"]) else int(row["preferred_release_year"]),
            "first_rating_date": None if pd.isna(row["first_rating_date"]) else row["first_rating_date"].strftime("%Y-%m-%d"),
            "last_rating_date": None if pd.isna(row["last_rating_date"]) else row["last_rating_date"].strftime("%Y-%m-%d"),
            "active_days": int(row["active_days"]),
        }

    def get_user_ratings(self, user_id: int, limit: int = 20, sort: str = "recent") -> list:
        user_ratings = self.ratings[self.ratings["user_id"] == user_id].copy()
        if sort == "rating":
            user_ratings = user_ratings.sort_values(["rating", "timestamp"], ascending=[False, False])
        else:
            user_ratings = user_ratings.sort_values("timestamp", ascending=False)
        user_ratings = user_ratings.head(limit)

        results = []
        for _, r in user_ratings.iterrows():
            movie_row = self.movie_features.loc[r["movie_id"]]
            results.append(
                {
                    "movie_id": int(r["movie_id"]),
                    "title": movie_row["title"],
                    "genres": movie_row["genres"],
                    "rating": int(r["rating"]),
                    "rated_at": pd.to_datetime(r["timestamp"], unit="s").strftime("%Y-%m-%d"),
                }
            )
        return results

    def _serialize_movie_brief(self, movie_id: int) -> dict:
        row = self.movie_features.loc[movie_id]
        return {
            "movie_id": int(movie_id),
            "title": row["title"],
            "genres": row["genres"],
        }

    def serialize_movie(self, movie_id: int) -> dict:
        row = self.movie_features.loc[movie_id]
        return {
            "movie_id": int(movie_id),
            "title": row["title"],
            "clean_title": row["clean_title"],
            "release_year": None if pd.isna(row["release_year"]) else int(row["release_year"]),
            "genres": row["genres"],
            "average_rating": round(float(row["rating_mean"]), 2),
            "rating_count": int(row["rating_count"]),
        }

    # -----------------------------------------------------------
    # 영화 검색
    # -----------------------------------------------------------

    def list_movies(self, search: str = "", limit: int = 20) -> list:
        df = self.movie_features
        if search.strip():
            keyword = search.strip().lower()
            df = df[df["search_title"].str.contains(keyword, regex=False)]
            df = df.sort_values("rating_count", ascending=False)
        else:
            df = df.sort_values("popularity_score", ascending=False)
        df = df.head(limit)
        return [self.serialize_movie(movie_id) for movie_id in df.index]

    # -----------------------------------------------------------
    # 인기 추천 (신규/저활동 사용자 대체용)
    # -----------------------------------------------------------

    def recommend_popular(self, top_n: int = 10, exclude_movie_ids=None) -> list:
        df = self.popularity_ranking
        if exclude_movie_ids:
            df = df[~df.index.isin(exclude_movie_ids)]
        df = df.head(top_n)

        return [
            {
                "movie_id": int(movie_id),
                "title": row["title"],
                "clean_title": row["clean_title"],
                "release_year": None if pd.isna(row["release_year"]) else int(row["release_year"]),
                "genres": row["genres"],
                "weighted_rating": round(float(row["weighted_rating"]), 3),
                "average_rating": round(float(row["rating_mean"]), 2),
                "rating_count": int(row["rating_count"]),
                "recommendation_reason": "평가 수와 평균 평점이 모두 높은 인기 영화입니다.",
            }
            for movie_id, row in df.iterrows()
        ]

    # -----------------------------------------------------------
    # 개별 알고리즘 점수 계산 (후보 movie_id 배열 -> pd.Series)
    # -----------------------------------------------------------

    def _unseen_movies(self, user_id: int) -> np.ndarray:
        seen = set(self.ratings.loc[self.ratings["user_id"] == user_id, "movie_id"])
        return np.array([m for m in self.movie_features.index if m not in seen])

    def _content_scores(self, user_id: int, candidate_ids: np.ndarray) -> pd.Series:
        user_vector = get_genre_preference_vector(self.user_profiles.loc[user_id]).reshape(1, -1)
        candidate_genres = self.genre_matrix.loc[candidate_ids]
        scores = cosine_similarity(user_vector, candidate_genres)[0]
        return pd.Series(scores, index=candidate_ids)

    def _item_cf_scores(self, user_id: int, candidate_ids: np.ndarray) -> pd.Series:
        user_mean = float(self.user_rating_mean.get(user_id, 3.0))
        user_ratings = self.ratings.loc[self.ratings["user_id"] == user_id, ["movie_id", "rating"]].set_index("movie_id")["rating"]

        rated_in_sim = user_ratings.index.intersection(self.item_similarity.columns)
        cand_in_sim = pd.Index(candidate_ids).intersection(self.item_similarity.index)
        result = pd.Series(np.nan, index=candidate_ids)
        if len(rated_in_sim) == 0 or len(cand_in_sim) == 0:
            return result

        devs = (user_ratings.loc[rated_in_sim] - user_mean).to_numpy()
        sub = self.item_similarity.loc[cand_in_sim, rated_in_sim].to_numpy()
        numer = sub @ devs
        denom = np.abs(sub).sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            pred = user_mean + numer / denom
        pred = np.where(denom > 1e-9, pred, np.nan)
        pred = np.clip(pred, 1.0, 5.0)
        result.loc[cand_in_sim] = pred
        return result

    def _user_cf_scores(self, user_id: int, candidate_ids: np.ndarray, k: int = 30) -> pd.Series:
        result = pd.Series(np.nan, index=candidate_ids)
        if user_id not in self.user_similarity.index:
            return result

        sims = self.user_similarity.loc[user_id].drop(labels=[user_id], errors="ignore")
        sims = sims[sims > 0].sort_values(ascending=False).head(k)
        if sims.empty:
            return result

        neighbor_ratings = self.ratings[
            self.ratings["user_id"].isin(sims.index) & self.ratings["movie_id"].isin(candidate_ids)
        ]
        if neighbor_ratings.empty:
            return result

        pivot = neighbor_ratings.pivot_table(index="user_id", columns="movie_id", values="rating")
        neighbor_means = self.user_rating_mean.reindex(pivot.index)
        dev = pivot.sub(neighbor_means, axis=0)
        sims_aligned = sims.reindex(pivot.index)

        numer = dev.mul(sims_aligned, axis=0).sum(axis=0, skipna=True)
        mask = dev.notna()
        denom = mask.mul(sims_aligned.abs(), axis=0).sum(axis=0)

        user_mean = float(self.user_rating_mean.get(user_id, 3.0))
        with np.errstate(invalid="ignore", divide="ignore"):
            pred = user_mean + numer / denom.replace(0, np.nan)
        pred = pred.clip(1.0, 5.0)
        result.loc[pred.index] = pred.values
        return result

    def _svd_raw(self, user_id: int, candidate_ids: np.ndarray) -> pd.Series:
        if user_id not in self.svd_predicted_ratings.index:
            return pd.Series(np.nan, index=candidate_ids)
        cols = pd.Index(candidate_ids).intersection(self.svd_predicted_ratings.columns)
        row = self.svd_predicted_ratings.loc[user_id, cols]
        return row.reindex(candidate_ids)

    # -----------------------------------------------------------
    # 추천 이유 생성
    # -----------------------------------------------------------

    def _build_reason(self, weighted_contributions: dict, user_genres: list, movie_genres: list) -> str:
        common_genres = [g for g in movie_genres if g in set(user_genres)]
        if not weighted_contributions:
            top_component = "popularity"
        else:
            top_component = max(weighted_contributions, key=weighted_contributions.get)

        if top_component == "content":
            if common_genres:
                return f"사용자가 선호하는 {', '.join(common_genres)} 장르와 유사합니다."
            return "사용자의 장르 취향과 전반적으로 유사한 영화입니다."
        if top_component == "collaborative":
            if common_genres:
                return f"비슷한 취향의 사용자들이 높게 평가했고 선호 장르({', '.join(common_genres)})와도 잘 맞습니다."
            return "비슷한 취향의 사용자들이 높은 평점을 준 영화입니다."
        if top_component == "svd":
            return "잠재 요인 분석 결과, 아직 보지 않은 영화 중 예측 평점이 높습니다."
        return "평가 수와 평균 평점이 모두 높은 인기 영화입니다."

    # -----------------------------------------------------------
    # 하이브리드 개인화 추천
    # -----------------------------------------------------------

    def recommend_for_user(self, user_id: int, top_n: int = 10) -> dict:
        profile_row = self.user_profiles.loc[user_id]
        activity_level = profile_row["activity_level"]
        weights = self.config["hybrid_weights_by_activity"][activity_level]

        candidate_ids = self._unseen_movies(user_id)
        if len(candidate_ids) == 0:
            candidate_ids = self.movie_features.index.to_numpy()

        content = self._content_scores(user_id, candidate_ids)
        item_cf = self._item_cf_scores(user_id, candidate_ids)
        user_cf = self._user_cf_scores(user_id, candidate_ids)

        collaborative_raw = combine_weighted_scores(
            {"item": item_cf, "user": user_cf},
            {
                "item": self.config["item_cf_weight_in_collaborative"],
                "user": self.config["user_cf_weight_in_collaborative"],
            },
        )
        collaborative = normalize_scores(collaborative_raw)

        svd_raw = self._svd_raw(user_id, candidate_ids)
        svd_norm = normalize_scores(svd_raw)

        popularity = self.movie_features.loc[candidate_ids, "popularity_score"]
        popularity.index = candidate_ids

        components = {
            "content": content,
            "collaborative": collaborative,
            "svd": svd_norm,
            "popularity": popularity,
        }
        hybrid = combine_weighted_scores(components, weights)
        hybrid = hybrid.dropna().sort_values(ascending=False).head(top_n)

        user_genres = profile_row["favorite_genres"]
        recommendations = []
        for movie_id, hybrid_score in hybrid.items():
            movie_row = self.movie_features.loc[movie_id]
            row_scores = {name: series.get(movie_id, np.nan) for name, series in components.items()}
            contributions = {
                name: weights.get(name, 0.0) * val
                for name, val in row_scores.items()
                if not pd.isna(val)
            }
            reason = self._build_reason(contributions, user_genres, movie_row["genres"])
            predicted_rating = svd_raw.get(movie_id, np.nan)

            recommendations.append(
                {
                    "movie_id": int(movie_id),
                    "title": movie_row["clean_title"],
                    "release_year": None if pd.isna(movie_row["release_year"]) else int(movie_row["release_year"]),
                    "genres": movie_row["genres"],
                    "hybrid_score": round(float(hybrid_score), 4),
                    "predicted_rating": None if pd.isna(predicted_rating) else round(float(predicted_rating), 2),
                    "content_score": None if pd.isna(row_scores["content"]) else round(float(row_scores["content"]), 4),
                    "collaborative_score": None if pd.isna(row_scores["collaborative"]) else round(float(row_scores["collaborative"]), 4),
                    "svd_score": None if pd.isna(row_scores["svd"]) else round(float(row_scores["svd"]), 4),
                    "popularity_score": None if pd.isna(row_scores["popularity"]) else round(float(row_scores["popularity"]), 4),
                    "average_rating": round(float(movie_row["rating_mean"]), 2),
                    "rating_count": int(movie_row["rating_count"]),
                    "recommendation_reason": reason,
                }
            )

        return {
            "user": {
                "user_id": int(user_id),
                "rating_count": int(profile_row["rating_count"]),
                "activity_level": activity_level,
                "favorite_genres": user_genres,
            },
            "strategy": {
                "name": "hybrid",
                "weights": weights,
                "cold_start": activity_level == "Low Activity",
            },
            "recommendations": recommendations,
        }
