# feature_engineering.py
# ---------------------------------------------------------------
# Movie Recommendation AI Advanced - 공용 데이터 로딩 / Feature Engineering 모듈
#
# Notebook(EDA/알고리즘 비교/평가)과 운영 코드(train_model.py, recommendation_service.py)가
# 완전히 동일한 로딩·정제·파생변수 로직을 사용해야 하므로, 데이터 처리와 관련된 함수를
# 이 모듈 하나에 모아두고 세 곳(Notebook, 학습, 서빙)에서 그대로 가져다 쓴다.
#
# Project06(심화)은 Project05(services/06-movie-recommendation-ai, "영화 한 편 선택 -> 유사
# 영화 추천")와 달리, 사용자별 평점 이력을 분석해 사용자 취향 프로필을 만들고, 이를 기반으로
# 개인화 추천(Content-Based / Item-CF / User-CF / SVD / Hybrid)을 제공한다.
# ---------------------------------------------------------------

import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------
# 1. 데이터 경로 / 원본 컬럼 상수
# ---------------------------------------------------------------

# data/ 폴더에서 이 순서로 MovieLens 100K 폴더를 탐색한다.
CANDIDATE_DATA_DIRS = ["ml-100k", "ML-100k", "movielens-100k"]

REQUIRED_FILES = ["u.data", "u.item", "u.user"]

GENRE_COLUMNS = [
    "unknown", "Action", "Adventure", "Animation", "Children's", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
]

ITEM_COLUMNS = ["movie_id", "title", "release_date", "video_release_date", "imdb_url"] + GENRE_COLUMNS
USER_COLUMNS = ["user_id", "age", "gender", "occupation", "zip_code"]
RATING_COLUMNS = ["user_id", "movie_id", "rating", "timestamp"]

RANDOM_STATE = 42

# 영화별 최소 평점 수 기준. EDA 결과(영화별 평점 개수 분포가 매우 긴 꼬리를 가지며, 중앙값 대비
# 하위 다수 영화는 평가가 거의 없다) 를 근거로 협업 필터링/유사도 계산에 포함할 "충분히 평가된
# 영화"의 기준을 정한다. 실제 값은 train_model.py 실행 시 rating_count 분포의 40번째 백분위수로
# 데이터 기반 결정하며, 아래 값은 최소 하한선(fallback)이다.
MIN_RATING_COUNT_FOR_MOVIE_CF = 5
MOVIE_CF_QUANTILE = 0.40

# 사용자별 최소 평점 수 기준. User-Based CF의 이웃(neighbor) 유사도 계산 대상 사용자를 정할 때
# 사용한다. 평점이 너무 적은 사용자는 유사도 자체의 신뢰도가 낮기 때문이다.
MIN_RATING_COUNT_FOR_USER_CF = 5

# 인기도(Bayesian Weighted Rating) 계산 시 사용하는 최소 투표 수 m은 train_model.py에서
# rating_count의 60번째 백분위수로 데이터 기반 결정한다.
POPULARITY_QUANTILE = 0.60

# 사용자 활동 수준 구간을 나누는 백분위수. 실제 분포를 보고 결정한 값이며,
# Research_Report.md 11.4절/EDA 노트북 14.2절에서 근거를 설명한다.
ACTIVITY_LEVEL_QUANTILES = [0.0, 0.50, 0.80, 0.95, 1.0]
ACTIVITY_LEVEL_LABELS = ["Low Activity", "Medium Activity", "High Activity", "Power User"]

# 영화 인기 수준 구간(4분위) 라벨.
POPULARITY_LEVEL_LABELS = ["Niche", "Moderate", "Popular", "Blockbuster"]

# 사용자 선호 장르 계산 시, 상위 몇 개 장르를 "대표 선호 장르"로 볼 것인가.
TOP_FAVORITE_GENRE_COUNT = 3
# 사용자 대표 고평점 영화 개수.
TOP_RATED_MOVIE_COUNT = 5
# "높게 평가했다"고 볼 최소 평점(그 이하는 선호 장르/대표 영화 계산에서 제외).
HIGH_RATING_THRESHOLD = 4

# SVD(Matrix Factorization) 잠재 요인 개수.
SVD_N_COMPONENTS = 20

DEFAULT_TOP_N = 10
TOP_N_MIN = 1
TOP_N_MAX = 30

# 하이브리드 추천에서 사용자 활동 수준별 알고리즘 가중치.
# content_score / collaborative_score / svd_score / popularity_score 를 조합한다.
#
# 초기값은 "활동량이 적을수록 인기도+콘텐츠, 많을수록 협업 필터링/SVD" 라는 직관으로 정했지만,
# Notebook 24장의 Leave-One-Out 평가에서 각 신호의 실제 기여도를 측정한 뒤 아래 값으로 조정했다.
# 특히 SVD가 단일 알고리즘 중 Hit Rate@10이 가장 높게 측정되어(0.0657) 모든 활동 구간에서 SVD 비중을
# 가장 크게 반영하고, User-Based CF는 이 데이터 규모에서 상대적으로 약해(Hit Rate@10 0.0053) collaborative
# 내부 비중과 활동 구간별 가중치를 함께 낮췄다. 근거와 실제 수치는 Research_Report.md 11.8절 참고.
HYBRID_WEIGHTS_BY_ACTIVITY = {
    "Low Activity": {"content": 0.25, "collaborative": 0.10, "svd": 0.35, "popularity": 0.30},
    "Medium Activity": {"content": 0.20, "collaborative": 0.15, "svd": 0.45, "popularity": 0.20},
    "High Activity": {"content": 0.10, "collaborative": 0.15, "svd": 0.60, "popularity": 0.15},
    "Power User": {"content": 0.10, "collaborative": 0.15, "svd": 0.65, "popularity": 0.10},
}
# collaborative_score 내부에서 Item-Based CF와 User-Based CF를 섞는 비율.
# Item-Based CF의 단독 Hit Rate@10(0.0170)이 User-Based CF(0.0053)보다 뚜렷이 높게 측정되어
# Item-Based CF의 비중을 더 크게 둔다.
ITEM_CF_WEIGHT_IN_COLLABORATIVE = 0.8
USER_CF_WEIGHT_IN_COLLABORATIVE = 0.2


# ---------------------------------------------------------------
# 2. 데이터 파일 탐색 / 로딩
# ---------------------------------------------------------------

def find_data_dir(base_dir: str = "data") -> Optional[Path]:
    """data/ 폴더 아래에서 MovieLens 100K 원본 파일이 있는 폴더를 찾는다.
    없으면 None을 반환한다 (자동 다운로드는 시도하지 않는다).
    """
    base = Path(base_dir)

    for candidate in CANDIDATE_DATA_DIRS:
        path = base / candidate
        if all((path / f).exists() for f in REQUIRED_FILES):
            return path

    # data/ 바로 아래에 압축을 풀어둔 경우도 지원한다.
    if all((base / f).exists() for f in REQUIRED_FILES):
        return base

    return None


def print_missing_data_guide(base_dir: str = "data") -> None:
    print("=" * 70)
    print("[오류] MovieLens 100K 데이터를 찾을 수 없습니다.")
    print("=" * 70)
    print("다음 파일이 필요합니다:", ", ".join(REQUIRED_FILES))
    print(f"다음 경로에 MovieLens 100K 압축을 해제한 뒤 다시 실행하세요.")
    print(f"  - {Path(base_dir) / 'ml-100k'} /u.data, u.item, u.user 등")
    print()
    print("자세한 안내는 data/README.md 를 참고하세요.")
    print("=" * 70)


def load_ratings(data_dir: Path) -> pd.DataFrame:
    ratings = pd.read_csv(
        data_dir / "u.data",
        sep="\t",
        names=RATING_COLUMNS,
        dtype={"user_id": "int32", "movie_id": "int32", "rating": "int8", "timestamp": "int64"},
        engine="python",
    )
    return ratings


def load_movies(data_dir: Path) -> pd.DataFrame:
    movies = pd.read_csv(
        data_dir / "u.item",
        sep="|",
        names=ITEM_COLUMNS,
        encoding="latin-1",
        engine="python",
    )
    # video_release_date는 MovieLens 100K 전체에서 항상 결측이라 제거한다.
    return movies.drop(columns=["video_release_date"])


def load_users(data_dir: Path) -> pd.DataFrame:
    users = pd.read_csv(
        data_dir / "u.user",
        sep="|",
        names=USER_COLUMNS,
        dtype={"user_id": "int32", "age": "int32"},
        engine="python",
    )
    return users


# ---------------------------------------------------------------
# 3. 데이터 정제
# ---------------------------------------------------------------

def clean_ratings(ratings: pd.DataFrame) -> pd.DataFrame:
    """중복 평가((user_id, movie_id) 쌍이 두 번 이상 등장)와 범위를 벗어난 평점을 제거한다."""
    before = len(ratings)
    ratings = ratings.drop_duplicates(subset=["user_id", "movie_id"], keep="last")
    ratings = ratings[(ratings["rating"] >= 1) & (ratings["rating"] <= 5)]
    after = len(ratings)
    if before != after:
        print(f"정리 과정에서 {before - after:,}건의 행을 제거했습니다 (중복 평가/범위 밖 평점).")
    return ratings.reset_index(drop=True)


# ---------------------------------------------------------------
# 4. 영화 제목 정리 (개봉연도 분리)
# ---------------------------------------------------------------

_YEAR_PATTERN = re.compile(r"\((\d{4})\)")


def split_title_and_year(raw_title: str) -> tuple:
    """"Toy Story (1995)" -> ("Toy Story", 1995)로 분리한다.

    연도 뒤에 "(V)" 같은 부가 표기가 더 붙는 영화도 있어, 문자열 마지막이 아니라
    "(YYYY)" 패턴이 마지막으로 등장하는 위치를 기준으로 자른다.
    "unknown"처럼 연도 표기가 아예 없는 경우 release_year는 None이 된다.
    """
    title = str(raw_title).strip()
    matches = list(_YEAR_PATTERN.finditer(title))
    if not matches:
        return title, None

    last_match = matches[-1]
    year = int(last_match.group(1))
    clean = title[: last_match.start()].strip()
    return clean, year


def bin_by_quantile(values: pd.Series, quantiles, labels) -> pd.Series:
    """실제 분포의 백분위수를 경계로 구간화한다 (임의 고정값 사용 금지)."""
    edges = values.quantile(quantiles).values
    edges = np.unique(edges)
    if len(edges) - 1 < len(labels):
        # 값의 종류가 너무 적어(동률이 많아) 구간이 충분히 안 나뉘는 극단적 경우를 대비한 안전장치.
        labels = labels[: max(len(edges) - 1, 1)]
    return pd.cut(values, bins=edges, labels=labels, include_lowest=True, duplicates="drop")


# ---------------------------------------------------------------
# 5. 영화 Feature Engineering
# ---------------------------------------------------------------

def compute_bayesian_weighted_rating(rating_count: pd.Series, rating_mean: pd.Series, quantile: float = POPULARITY_QUANTILE):
    """Bayesian Weighted Rating (IMDB 공식과 동일한 형태).

    weighted = (v / (v + m)) * R + (m / (v + m)) * C
      v: 해당 영화의 평점 수, R: 해당 영화의 평균 평점
      m: 최소 투표 수 기준(데이터의 rating_count 분포에서 quantile 백분위수로 결정)
      C: 전체 영화 평균 평점

    평점 수가 아주 적은 영화가 평균 평점만으로 최상위에 올라가는 문제를 완화한다.
    """
    m = float(rating_count.quantile(quantile))
    C = float(rating_mean[rating_count > 0].mean())
    v = rating_count.astype(float)
    weighted = (v / (v + m)) * rating_mean + (m / (v + m)) * C
    return weighted, m, C


def build_movie_features(movies: pd.DataFrame, ratings: pd.DataFrame) -> pd.DataFrame:
    """u.item + u.data를 합쳐 영화 Feature 테이블을 만든다 (movie_id 인덱스).

    포함 컬럼: title(원본), clean_title, release_year, search_title, genres(리스트),
    rating_count, rating_mean, rating_std, weighted_rating, popularity_level
    """
    movies = movies.copy()

    parsed = movies["title"].apply(split_title_and_year)
    movies["clean_title"] = [p[0] for p in parsed]
    movies["release_year"] = [p[1] for p in parsed]
    movies["search_title"] = movies["clean_title"].str.lower()

    genre_matrix = movies[GENRE_COLUMNS]
    movies["genres"] = genre_matrix.apply(
        lambda row: [genre for genre, flag in zip(GENRE_COLUMNS, row) if flag == 1], axis=1
    )

    rating_stats = ratings.groupby("movie_id")["rating"].agg(
        rating_count="count", rating_mean="mean", rating_std="std"
    )

    metadata = movies.set_index("movie_id").join(rating_stats, how="left")
    metadata["rating_count"] = metadata["rating_count"].fillna(0).astype(int)
    metadata["rating_mean"] = metadata["rating_mean"].fillna(0.0)
    # 평점이 1건 이하인 영화는 표준편차가 NaN이므로 0으로 채운다 ("호불호를 판단할 근거 없음").
    metadata["rating_std"] = metadata["rating_std"].fillna(0.0)

    weighted_rating, m, C = compute_bayesian_weighted_rating(metadata["rating_count"], metadata["rating_mean"])
    metadata["weighted_rating"] = weighted_rating

    metadata["popularity_level"] = bin_by_quantile(
        metadata["rating_count"], ACTIVITY_LEVEL_QUANTILES, POPULARITY_LEVEL_LABELS
    ).astype(str)

    columns = [
        "title", "clean_title", "release_year", "search_title", "genres",
        "rating_count", "rating_mean", "rating_std", "weighted_rating", "popularity_level",
    ]
    return metadata[columns], m, C


def build_genre_matrix(movies: pd.DataFrame) -> pd.DataFrame:
    """콘텐츠 기반 추천에 쓰이는 movie_id x genre 멀티-핫 행렬."""
    genre_matrix = movies.set_index("movie_id")[GENRE_COLUMNS].astype(float)
    return genre_matrix


# ---------------------------------------------------------------
# 6. 사용자-영화 평점 행렬 / 중심화
# ---------------------------------------------------------------

def build_user_item_matrix(ratings: pd.DataFrame) -> pd.DataFrame:
    """행=user_id, 열=movie_id, 값=rating 인 평점 행렬. 평가하지 않은 칸은 NaN이다.

    NaN을 바로 0으로 채우지 않는 이유: 0은 "1점보다 낮은 평점"으로 오인될 수 있어,
    사용자별 평균으로 중심화(centering)한 뒤에 남는 결측만 0으로 채운다.
    """
    return ratings.pivot_table(index="user_id", columns="movie_id", values="rating")


def mean_center_user_item_matrix(user_item_matrix: pd.DataFrame) -> tuple:
    """사용자마다 후한/짠 평점 성향이 다르므로, 사용자 평균을 빼서 중심화한다.
    평가하지 않은 칸은 0으로 채워 "차이 없음"으로 취급한다.

    Returns:
        (centered_matrix, user_mean_series)
    """
    user_mean = user_item_matrix.mean(axis=1)
    centered = user_item_matrix.sub(user_mean, axis=0)
    return centered.fillna(0.0), user_mean


# ---------------------------------------------------------------
# 7. 사용자 Feature Engineering (사용자 취향 프로필)
# ---------------------------------------------------------------

def build_user_features(
    ratings: pd.DataFrame,
    users: pd.DataFrame,
    movies: pd.DataFrame,
    genre_matrix: pd.DataFrame,
) -> pd.DataFrame:
    """사용자별 평점 이력을 요약해 취향 프로필 테이블을 만든다 (user_id 인덱스).

    포함 컬럼: age, gender, occupation, rating_count, rating_mean, rating_std,
    activity_level, favorite_genres(리스트), genre_preference_vector(19차원 numpy),
    preferred_release_year, preferred_release_decade, top_rated_movie_ids(리스트),
    first_rating_date, last_rating_date, active_days
    """
    rating_stats = ratings.groupby("user_id")["rating"].agg(
        rating_count="count", rating_mean="mean", rating_std="std"
    )
    rating_stats["rating_std"] = rating_stats["rating_std"].fillna(0.0)

    profile = users.set_index("user_id").join(rating_stats, how="left")
    profile["rating_count"] = profile["rating_count"].fillna(0).astype(int)
    profile["rating_mean"] = profile["rating_mean"].fillna(0.0)
    profile["rating_std"] = profile["rating_std"].fillna(0.0)

    profile["activity_level"] = bin_by_quantile(
        profile["rating_count"], ACTIVITY_LEVEL_QUANTILES, ACTIVITY_LEVEL_LABELS
    ).astype(str)

    # -------------------------------------------------------
    # 장르 선호 벡터: "본 횟수"가 아니라 "평점"을 반영한다.
    # 단순히 많이 본 장르가 아니라, 높게 평가한 장르일수록 가중치를 크게 준다.
    # (rating - 3)을 사용해 3점(중립)은 선호에 기여하지 않고, 4~5점은 양의 기여,
    # 1~2점은 음의 기여를 하도록 한다.
    # -------------------------------------------------------
    merged = ratings[["user_id", "movie_id", "rating"]].merge(
        genre_matrix, left_on="movie_id", right_index=True, how="left"
    )
    genre_only = merged[GENRE_COLUMNS].to_numpy()
    weight = (merged["rating"].to_numpy() - 3.0).reshape(-1, 1)
    weighted_genre = genre_only * weight

    weighted_sum = pd.DataFrame(weighted_genre, columns=GENRE_COLUMNS)
    weighted_sum["user_id"] = merged["user_id"].to_numpy()
    genre_pref_raw = weighted_sum.groupby("user_id")[GENRE_COLUMNS].sum()

    # 음수 선호(비선호)까지 유사도 계산에 그대로 활용할 수 있도록 0 미만 값은 0으로 잘라
    # "양의 선호 벡터"로 만든다 (코사인 유사도는 음수 성분이 섞이면 해석이 어려워짐).
    genre_pref_positive = genre_pref_raw.clip(lower=0.0)
    row_sum = genre_pref_positive.sum(axis=1)
    # 모든 장르 선호가 0인 사용자(평가가 전부 3점 이하)는 균등 분포로 대체한다.
    zero_rows = row_sum == 0
    genre_pref_normalized = genre_pref_positive.div(row_sum.replace(0, np.nan), axis=0)
    genre_pref_normalized.loc[zero_rows, :] = 1.0 / len(GENRE_COLUMNS)

    profile = profile.join(
        genre_pref_normalized.add_prefix("genre_pref_"), how="left"
    )
    genre_pref_cols = [f"genre_pref_{g}" for g in GENRE_COLUMNS]
    profile[genre_pref_cols] = profile[genre_pref_cols].fillna(1.0 / len(GENRE_COLUMNS))

    def top_genres(row):
        values = row[genre_pref_cols].to_numpy(dtype=float)
        order = np.argsort(values)[::-1][:TOP_FAVORITE_GENRE_COUNT]
        return [GENRE_COLUMNS[i] for i in order if values[i] > 0]

    profile["favorite_genres"] = profile.apply(top_genres, axis=1)

    # -------------------------------------------------------
    # 선호 개봉연도: 높게 평가한(HIGH_RATING_THRESHOLD 이상) 영화의 개봉연도 중앙값.
    # -------------------------------------------------------
    movie_year = movies.set_index("movie_id")["title"].apply(lambda t: split_title_and_year(t)[1])
    high_rated = ratings[ratings["rating"] >= HIGH_RATING_THRESHOLD].copy()
    high_rated["release_year"] = high_rated["movie_id"].map(movie_year)
    preferred_year = high_rated.dropna(subset=["release_year"]).groupby("user_id")["release_year"].median()
    profile = profile.join(preferred_year.rename("preferred_release_year"), how="left")
    profile["preferred_release_decade"] = (profile["preferred_release_year"] // 10 * 10)

    # -------------------------------------------------------
    # 대표 고평점 영화: 평점 내림차순 -> 동점이면 최근 평가 순.
    # -------------------------------------------------------
    high_rated_sorted = ratings.sort_values(["user_id", "rating", "timestamp"], ascending=[True, False, False])
    top_movies = (
        high_rated_sorted.groupby("user_id")["movie_id"]
        .apply(lambda s: list(s.head(TOP_RATED_MOVIE_COUNT)))
    )
    profile = profile.join(top_movies.rename("top_rated_movie_ids"), how="left")
    profile["top_rated_movie_ids"] = profile["top_rated_movie_ids"].apply(
        lambda v: v if isinstance(v, list) else []
    )

    # -------------------------------------------------------
    # 활동 기간: 데이터 내부의 timestamp 기준(절대적인 "현재 시점"을 사용하지 않는다).
    # -------------------------------------------------------
    ts_stats = ratings.groupby("user_id")["timestamp"].agg(first_ts="min", last_ts="max")
    profile = profile.join(ts_stats, how="left")
    profile["first_rating_date"] = pd.to_datetime(profile["first_ts"], unit="s", errors="coerce")
    profile["last_rating_date"] = pd.to_datetime(profile["last_ts"], unit="s", errors="coerce")
    profile["active_days"] = (profile["last_rating_date"] - profile["first_rating_date"]).dt.days.fillna(0).astype(int)
    profile = profile.drop(columns=["first_ts", "last_ts"])

    return profile


def get_genre_preference_vector(user_profile_row: pd.Series) -> np.ndarray:
    return np.array([user_profile_row[f"genre_pref_{g}"] for g in GENRE_COLUMNS], dtype=float)


# ---------------------------------------------------------------
# 8. Interaction Feature Engineering (유사도 행렬)
# ---------------------------------------------------------------

def determine_movie_cf_min_count(rating_count: pd.Series, quantile: float = MOVIE_CF_QUANTILE) -> int:
    value = int(rating_count.quantile(quantile))
    return max(value, MIN_RATING_COUNT_FOR_MOVIE_CF)


def build_item_similarity_matrix(centered_matrix: pd.DataFrame, eligible_movie_ids) -> pd.DataFrame:
    """평점 수가 충분한 영화만 대상으로 아이템 기반 협업 필터링 유사도 행렬을 계산한다.

    사용자 평균으로 중심화된 평점을 사용해, 사용자마다 다른 평점 성향의 영향을 줄인다.
    """
    columns = [c for c in centered_matrix.columns if c in set(eligible_movie_ids)]
    matrix = centered_matrix[columns]
    movie_vectors = matrix.T
    similarity = cosine_similarity(movie_vectors)
    return pd.DataFrame(similarity, index=movie_vectors.index, columns=movie_vectors.index)


def build_user_similarity_matrix(centered_matrix: pd.DataFrame, eligible_user_ids) -> pd.DataFrame:
    """평점 수가 충분한 사용자만 대상으로 사용자 기반 협업 필터링 유사도 행렬을 계산한다."""
    rows = [u for u in centered_matrix.index if u in set(eligible_user_ids)]
    matrix = centered_matrix.loc[rows]
    similarity = cosine_similarity(matrix)
    return pd.DataFrame(similarity, index=matrix.index, columns=matrix.index)


# ---------------------------------------------------------------
# 9. Matrix Factorization (SVD)
# ---------------------------------------------------------------

def fit_svd_model(centered_matrix: pd.DataFrame, user_mean: pd.Series, n_components: int = SVD_N_COMPONENTS):
    """TruncatedSVD로 사용자-영화 중심화 평점 행렬을 잠재 요인으로 분해하고,
    예측 평점 행렬(user x movie)을 재구성한다.

    Returns:
        dict(predicted_ratings: DataFrame, user_factors, item_factors,
             explained_variance_ratio, n_components)
    """
    from sklearn.decomposition import TruncatedSVD

    n_components = min(n_components, min(centered_matrix.shape) - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=RANDOM_STATE)
    user_factors = svd.fit_transform(centered_matrix.to_numpy())
    item_factors = svd.components_.T

    reconstructed_centered = user_factors @ svd.components_
    predicted = reconstructed_centered + user_mean.to_numpy().reshape(-1, 1)
    # 평점 척도(1~5) 밖으로 나간 예측값을 잘라준다.
    predicted = np.clip(predicted, 1.0, 5.0)

    predicted_df = pd.DataFrame(predicted, index=centered_matrix.index, columns=centered_matrix.columns)

    return {
        "predicted_ratings": predicted_df,
        "user_factors": pd.DataFrame(user_factors, index=centered_matrix.index),
        "item_factors": pd.DataFrame(item_factors, index=centered_matrix.columns),
        "explained_variance_ratio": float(svd.explained_variance_ratio_.sum()),
        "n_components": n_components,
    }


# ---------------------------------------------------------------
# 10. 점수 정규화 / 후보 필터링
# ---------------------------------------------------------------

def normalize_scores(scores: pd.Series) -> pd.Series:
    """0~1 Min-Max 정규화. NaN(신호 없음)은 그대로 NaN으로 유지한다.
    값이 모두 같으면(분산 0) 유효한 값들을 0.5로 채운다.
    """
    if scores.empty:
        return scores
    min_v, max_v = np.nanmin(scores), np.nanmax(scores)
    if not np.isfinite(min_v):
        return scores
    if max_v - min_v < 1e-9:
        return scores.where(scores.isna(), 0.5)
    return (scores - min_v) / (max_v - min_v)


def combine_weighted_scores(components: dict, weights: dict) -> pd.Series:
    """여러 추천 점수(Series, 인덱스=movie_id)를 가중합으로 결합한다.

    일부 후보에서 특정 알고리즘 점수가 NaN(신호 없음, 예: 협업 필터링 대상 밖의 영화)이면
    해당 후보에 한해 그 가중치를 제외하고 나머지 가중치의 비율로 재분배한다.
    (예: collaborative_score가 없는 영화는 content/svd/popularity 가중치만으로 정규화하여 계산)
    """
    df = pd.DataFrame(components)
    weight_series = pd.Series(weights).reindex(df.columns).fillna(0.0)

    weighted_sum = df.mul(weight_series, axis=1).sum(axis=1, skipna=True)
    valid_weight = df.notna().astype(float).mul(weight_series, axis=1).sum(axis=1)

    combined = weighted_sum / valid_weight.replace(0.0, np.nan)
    return combined


def get_unseen_movies(user_id: int, ratings: pd.DataFrame, all_movie_ids) -> np.ndarray:
    """사용자가 이미 평가한 영화를 제외한 후보 movie_id 배열을 반환한다."""
    seen = set(ratings.loc[ratings["user_id"] == user_id, "movie_id"])
    return np.array([m for m in all_movie_ids if m not in seen])
