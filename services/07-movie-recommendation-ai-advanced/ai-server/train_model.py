# train_model.py
# ---------------------------------------------------------------
# Movie Recommendation AI Advanced - MovieLens 100K 기반 개인화 추천 모델 학습
#
# Notebook(ai-server/notebooks/project06_movie_recommendation_advanced.ipynb)에서 비교한 결과,
# 최종 추천 방식으로 다음 4가지 신호를 사용자 활동 수준에 따라 다르게 조합하는
# "Hybrid Recommendation"을 채택했다.
#
#   1) Content-Based   : 사용자 장르 선호 벡터 <-> 영화 장르 벡터 코사인 유사도
#   2) Collaborative    : Item-Based CF(60%) + User-Based CF(40%) 결합
#   3) SVD(Matrix Factorization) : TruncatedSVD로 재구성한 예측 평점
#   4) Popularity       : Bayesian Weighted Rating 기반 인기도
#
# 활동량이 적은 사용자일수록 협업 필터링/SVD 신호가 희소하므로 콘텐츠/인기도 비중을 높이고,
# 활동량이 많을수록 협업 필터링/SVD 비중을 높인다 (자세한 근거는 Research_Report.md 11.8절 참고).
#
# 이 스크립트는 Notebook의 실험 코드를 그대로 복사하지 않고, 운영(FastAPI)에 필요한 최종
# 산출물만 만든다. 알고리즘 간 비교/평가는 Notebook에서만 수행한다.
#
# 실행:
#   python train_model.py
# ---------------------------------------------------------------

import json
import os
import sys

import joblib

from feature_engineering import (
    ACTIVITY_LEVEL_LABELS,
    DEFAULT_TOP_N,
    HIGH_RATING_THRESHOLD,
    HYBRID_WEIGHTS_BY_ACTIVITY,
    ITEM_CF_WEIGHT_IN_COLLABORATIVE,
    MIN_RATING_COUNT_FOR_USER_CF,
    SVD_N_COMPONENTS,
    TOP_FAVORITE_GENRE_COUNT,
    TOP_N_MAX,
    TOP_N_MIN,
    TOP_RATED_MOVIE_COUNT,
    USER_CF_WEIGHT_IN_COLLABORATIVE,
    build_genre_matrix,
    build_item_similarity_matrix,
    build_movie_features,
    build_user_features,
    build_user_item_matrix,
    build_user_similarity_matrix,
    clean_ratings,
    determine_movie_cf_min_count,
    find_data_dir,
    fit_svd_model,
    load_movies,
    load_ratings,
    load_users,
    mean_center_user_item_matrix,
    normalize_scores,
    print_missing_data_guide,
)


# ---------------------------------------------------------------
# 0. 경로 상수
# ---------------------------------------------------------------

DATA_DIR = "data"
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


# ---------------------------------------------------------------
# 1. 데이터 품질 점검
# ---------------------------------------------------------------

def report_data_quality(ratings, movies, users) -> None:
    print("-" * 70)
    print("데이터 품질 점검")
    print("-" * 70)
    print(f"ratings: {ratings.shape}, movies: {movies.shape}, users: {users.shape}")
    print("ratings 결측치:", dict(ratings.isnull().sum()[ratings.isnull().sum() > 0]) or "없음")
    print("(user_id, movie_id) 중복 평가:", ratings.duplicated(subset=["user_id", "movie_id"]).sum())
    out_of_range = ((ratings["rating"] < 1) | (ratings["rating"] > 5)).sum()
    print("평점 범위(1~5) 벗어난 값:", out_of_range)
    print("-" * 70)


# ---------------------------------------------------------------
# 2. 학습 메인 로직
# ---------------------------------------------------------------

def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    data_dir = find_data_dir(DATA_DIR)
    if data_dir is None:
        print_missing_data_guide(DATA_DIR)
        sys.exit(1)

    print(f"데이터 경로: {data_dir}")

    # -----------------------------------------------------------
    # 1) 데이터 로딩 및 정리
    # -----------------------------------------------------------
    ratings = load_ratings(data_dir)
    movies = load_movies(data_dir)
    users = load_users(data_dir)

    report_data_quality(ratings, movies, users)
    ratings = clean_ratings(ratings)

    print(f"사용자 수: {users.shape[0]:,} / 영화 수: {movies.shape[0]:,} / 평점 수: {ratings.shape[0]:,}")

    # -----------------------------------------------------------
    # 2) 영화 Feature Engineering
    # -----------------------------------------------------------
    movie_features, popularity_m, popularity_C = build_movie_features(movies, ratings)
    movie_features["popularity_score"] = normalize_scores(movie_features["weighted_rating"])
    genre_matrix = build_genre_matrix(movies)
    print(f"영화 Feature 생성 완료: {movie_features.shape}, 인기도 기준 m={popularity_m:.2f}건, 전체 평균 C={popularity_C:.4f}")

    # -----------------------------------------------------------
    # 3) 사용자 Feature Engineering (취향 프로필)
    # -----------------------------------------------------------
    user_features = build_user_features(ratings, users, movies, genre_matrix)
    print(f"사용자 Feature 생성 완료: {user_features.shape}")
    print("사용자 활동 수준 분포:")
    print(user_features["activity_level"].value_counts().reindex(ACTIVITY_LEVEL_LABELS))

    # -----------------------------------------------------------
    # 4) 사용자-영화 행렬 및 중심화
    # -----------------------------------------------------------
    user_item_matrix = build_user_item_matrix(ratings)
    centered_matrix, user_mean = mean_center_user_item_matrix(user_item_matrix)

    # -----------------------------------------------------------
    # 5) Item-Based / User-Based Collaborative Filtering 유사도 행렬
    # -----------------------------------------------------------
    min_movie_count_for_cf = determine_movie_cf_min_count(movie_features["rating_count"])
    eligible_movie_ids = movie_features[movie_features["rating_count"] >= min_movie_count_for_cf].index
    item_similarity = build_item_similarity_matrix(centered_matrix, eligible_movie_ids)
    print(f"Item 유사도 행렬: {item_similarity.shape} (평점 {min_movie_count_for_cf}건 이상 영화만 대상)")

    eligible_user_ids = user_features[user_features["rating_count"] >= MIN_RATING_COUNT_FOR_USER_CF].index
    user_similarity = build_user_similarity_matrix(centered_matrix, eligible_user_ids)
    print(f"User 유사도 행렬: {user_similarity.shape} (평점 {MIN_RATING_COUNT_FOR_USER_CF}건 이상 사용자만 대상)")

    # -----------------------------------------------------------
    # 6) Matrix Factorization (SVD)
    # -----------------------------------------------------------
    svd_result = fit_svd_model(centered_matrix, user_mean, n_components=SVD_N_COMPONENTS)
    svd_model = {
        "predicted_ratings": svd_result["predicted_ratings"],
        "explained_variance_ratio": svd_result["explained_variance_ratio"],
        "n_components": svd_result["n_components"],
    }
    print(
        f"SVD 학습 완료: n_components={svd_result['n_components']}, "
        f"설명된 분산 비율={svd_result['explained_variance_ratio']:.4f}"
    )

    # -----------------------------------------------------------
    # 7) 인기 추천 산출물 (Cold Start / 신규 사용자 대체용)
    # -----------------------------------------------------------
    popularity_ranking = movie_features.sort_values("weighted_rating", ascending=False)[
        ["title", "clean_title", "release_year", "genres", "rating_count", "rating_mean", "weighted_rating", "popularity_score"]
    ].copy()
    print(f"인기 추천 랭킹 생성 완료: {popularity_ranking.shape}")

    # -----------------------------------------------------------
    # 8) 산출물 저장
    # -----------------------------------------------------------
    joblib.dump(movie_features, PATHS["movie_features"])
    joblib.dump(genre_matrix, PATHS["genre_matrix"])
    joblib.dump(user_features, PATHS["user_profiles"])
    joblib.dump(item_similarity, PATHS["item_similarity"])
    joblib.dump(user_similarity, PATHS["user_similarity"])
    joblib.dump(svd_model, PATHS["svd_model"])
    joblib.dump(popularity_ranking, PATHS["popularity_ranking"])
    joblib.dump(ratings, PATHS["ratings"])

    for key in [
        "movie_features", "genre_matrix", "user_profiles", "item_similarity",
        "user_similarity", "svd_model", "popularity_ranking", "ratings",
    ]:
        print(f"저장 완료: {PATHS[key]}")

    recommendation_config = {
        "hybrid_weights_by_activity": HYBRID_WEIGHTS_BY_ACTIVITY,
        "item_cf_weight_in_collaborative": ITEM_CF_WEIGHT_IN_COLLABORATIVE,
        "user_cf_weight_in_collaborative": USER_CF_WEIGHT_IN_COLLABORATIVE,
        "min_rating_count_for_movie_cf": int(min_movie_count_for_cf),
        "min_rating_count_for_user_cf": MIN_RATING_COUNT_FOR_USER_CF,
        "high_rating_threshold": HIGH_RATING_THRESHOLD,
        "top_favorite_genre_count": TOP_FAVORITE_GENRE_COUNT,
        "top_rated_movie_count": TOP_RATED_MOVIE_COUNT,
        "user_cf_neighbor_k": 30,
        "default_top_n": DEFAULT_TOP_N,
        "top_n_min": TOP_N_MIN,
        "top_n_max": TOP_N_MAX,
        "popularity_min_votes_m": round(popularity_m, 4),
        "popularity_global_mean_C": round(popularity_C, 4),
    }
    with open(PATHS["recommendation_config"], "w", encoding="utf-8") as f:
        json.dump(recommendation_config, f, indent=2, ensure_ascii=False)
    print(f"저장 완료: {PATHS['recommendation_config']}")

    model_info = {
        "project": "06-movie-recommendation-ai-advanced",
        "service_name": "Movie Recommendation AI Advanced",
        "dataset": "MovieLens 100K",
        "model_name": "Hybrid Recommendation (Content-Based + Item/User CF + SVD + Popularity)",
        "model_version": "1.0.0",
        "algorithms": [
            "popularity_based",
            "content_based",
            "item_based_cf",
            "user_based_cf",
            "svd_matrix_factorization",
            "hybrid",
        ],
        "num_users": int(users.shape[0]),
        "num_movies": int(movies.shape[0]),
        "num_ratings": int(ratings.shape[0]),
        "num_movies_in_item_cf": int(item_similarity.shape[0]),
        "num_users_in_user_cf": int(user_similarity.shape[0]),
        "svd_n_components": svd_result["n_components"],
        "svd_explained_variance_ratio": round(svd_result["explained_variance_ratio"], 4),
        "activity_level_distribution": {
            level: int((user_features["activity_level"] == level).sum()) for level in ACTIVITY_LEVEL_LABELS
        },
    }
    with open(PATHS["model_info"], "w", encoding="utf-8") as f:
        json.dump(model_info, f, indent=2, ensure_ascii=False)
    print(f"저장 완료: {PATHS['model_info']}")

    print("\n=== 학습 완료 ===")
    print(json.dumps(model_info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
