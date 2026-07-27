# ==========================================================
# Movie Recommendation AI Advanced - FastAPI
# MovieLens 100K 기반 사용자 개인화 영화 추천 API
# ==========================================================

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from feature_engineering import DEFAULT_TOP_N, TOP_N_MAX, TOP_N_MIN
from recommendation_service import RecommendationEngine


# ==========================================================
# 1. FastAPI 앱 생성 및 CORS 설정
# ==========================================================

app = FastAPI(
    title="Movie Recommendation AI Advanced",
    description="MovieLens 100K 기반 사용자 개인화 영화 추천 서비스 (교육/포트폴리오 목적)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sanitize_validation_errors(errors):
    """Pydantic 오류의 ctx에 담긴 예외 객체(JSON으로 직렬화 불가능)를 문자열로 바꾼다."""
    sanitized = []
    for error in errors:
        error = dict(error)
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            error["ctx"] = {key: str(value) for key, value in ctx.items()}
        sanitized.append(error)
    return sanitized


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "error": "입력값을 확인해주세요.",
                "details": _sanitize_validation_errors(exc.errors()),
            }
        ),
    )


# ==========================================================
# 2. 추천 엔진 로딩
#    - 서버 시작 시 한 번만 모델 산출물을 로드한다. 요청마다 다시 읽지 않는다.
#    - 산출물이 없어도 서버 자체는 켜지도록 하고, 추천 관련 엔드포인트에서 503과 함께
#      안내 메시지를 반환한다. (start.sh가 컨테이너 진입 시 먼저 학습 여부를 판단하지만,
#      main.py도 방어적으로 동작한다.)
# ==========================================================

engine = RecommendationEngine()


def _ensure_loaded():
    if not engine.loaded:
        raise HTTPException(
            status_code=503,
            detail=(
                "추천 모델이 아직 준비되지 않았습니다. data/ 폴더에 MovieLens 100K 데이터를 추가한 뒤 "
                "train_model.py를 실행하거나 서버를 다시 시작하세요."
            ),
        )


def _ensure_user_exists(user_id: int):
    if not engine.user_exists(user_id):
        raise HTTPException(status_code=404, detail=f"user_id={user_id} 에 해당하는 사용자를 찾을 수 없습니다.")


# ==========================================================
# 3. 요청 스키마
# ==========================================================

class RecommendUserRequest(BaseModel):
    user_id: int = Field(..., description="추천을 받을 사용자 ID")
    top_n: int = Field(
        DEFAULT_TOP_N, ge=TOP_N_MIN, le=TOP_N_MAX, description=f"추천 개수 ({TOP_N_MIN}~{TOP_N_MAX})"
    )

    model_config = {"json_schema_extra": {"example": {"user_id": 1, "top_n": 10}}}


# ==========================================================
# 4. Root / Health Check
# ==========================================================

@app.get("/")
def root():
    return {
        "service": "Movie Recommendation AI Advanced",
        "dataset": "MovieLens 100K",
        "status": "running",
        "model_loaded": engine.loaded,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": engine.loaded,
        "num_users": int(engine.user_profiles.shape[0]) if engine.loaded else 0,
        "num_movies": int(engine.movie_features.shape[0]) if engine.loaded else 0,
        "num_movies_in_item_cf": int(engine.item_similarity.shape[0]) if engine.loaded else 0,
        "num_users_in_user_cf": int(engine.user_similarity.shape[0]) if engine.loaded else 0,
    }


@app.get("/model-info")
def model_info_endpoint():
    if not engine.model_info:
        return {
            "model_loaded": engine.loaded,
            "message": (
                "학습된 추천 모델 정보가 없습니다. data/ 폴더에 MovieLens 100K 데이터를 추가한 뒤 "
                "train_model.py를 실행하세요."
            ),
        }
    return {"model_loaded": engine.loaded, **engine.model_info}


# ==========================================================
# 5. 사용자 목록 / 프로필 / 평점 이력
# ==========================================================

@app.get("/users")
def list_users(
    search: str = Query("", description="사용자 ID(숫자) 또는 직업 검색어"),
    limit: int = Query(50, ge=1, le=200),
    min_ratings: int = Query(0, ge=0, description="최소 평점 개수 필터"),
):
    _ensure_loaded()
    return engine.list_users(search=search, min_ratings=min_ratings, limit=limit)


@app.get("/users/{user_id}/profile")
def get_user_profile(user_id: int):
    _ensure_loaded()
    _ensure_user_exists(user_id)
    return engine.get_user_profile(user_id)


@app.get("/users/{user_id}/ratings")
def get_user_ratings(
    user_id: int,
    limit: int = Query(20, ge=1, le=200),
    sort: str = Query("recent", pattern="^(recent|rating)$", description="recent 또는 rating"),
):
    _ensure_loaded()
    _ensure_user_exists(user_id)
    return engine.get_user_ratings(user_id, limit=limit, sort=sort)


# ==========================================================
# 6. 영화 검색
# ==========================================================

@app.get("/movies")
def list_movies(
    search: str = Query("", description="영화 제목 검색어 (부분 일치, 대소문자 무시)"),
    limit: int = Query(20, ge=1, le=200),
):
    _ensure_loaded()
    return engine.list_movies(search=search, limit=limit)


# ==========================================================
# 7. 추천 API
# ==========================================================

@app.post("/recommend/user")
def recommend_user(payload: RecommendUserRequest):
    _ensure_loaded()
    _ensure_user_exists(payload.user_id)

    result = engine.recommend_for_user(payload.user_id, top_n=payload.top_n)
    if not result["recommendations"]:
        raise HTTPException(status_code=404, detail="추천할 영화를 찾지 못했습니다.")
    return result


@app.get("/recommend/popular")
def recommend_popular(top_n: int = Query(DEFAULT_TOP_N, ge=TOP_N_MIN, le=TOP_N_MAX)):
    _ensure_loaded()
    recommendations = engine.recommend_popular(top_n=top_n)
    if not recommendations:
        raise HTTPException(status_code=404, detail="추천할 영화를 찾지 못했습니다.")
    return {
        "strategy": {"name": "popularity", "cold_start": True},
        "recommendations": recommendations,
    }
