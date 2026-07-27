# Movie Recommendation AI Advanced

MovieLens 100K 데이터셋을 기반으로, 사용자의 평점 이력을 분석해 취향 프로필을 만들고 개인화된 영화를
추천하는 AI 서비스입니다.

> 이 서비스는 교육 및 포트폴리오 목적으로 제작되었으며, 실제 상용 스트리밍 서비스의 추천 품질을
> 대신하지 않습니다. 로그인은 실제 인증이 아니라 MovieLens 사용자를 선택하는 **교육용 데모 로그인**입니다.

---

## 1. 프로젝트 소개

사용자 목록에서 한 명을 선택하면(실제 회원가입/로그인이 아닌 데모 선택), 그 사용자의 평점 이력을 분석해
활동 수준·선호 장르 같은 취향 프로필을 보여주고, 하이브리드 알고리즘으로 계산한 개인화 추천 영화 목록과
추천 이유를 제공합니다. Project05(`services/06-movie-recommendation-ai`, "영화 한 편 선택 -> 유사 영화
추천")를 사용자 단위 개인화로 확장한 심화 프로젝트입니다.

## 2. 주요 기능

- 사용자 검색(ID/직업) 및 카드 선택형 데모 로그인 (숫자 직접 입력 없음)
- 사용자 대시보드: 평점 개수/평균/표준편차, 활동 수준, 선호 장르, 높게 평가한 영화, 평점 이력
- 하이브리드 개인화 추천(Content-Based + Item/User-CF + SVD + Popularity), 활동 수준별 가중치 자동 적용
- 추천 결과별 하이브리드 점수, 예측 평점, 세부 알고리즘 점수, 자연어 추천 이유
- 신규/저활동 사용자를 위한 인기 추천 대체 API(`GET /recommend/popular`)

## 3. 기술 스택

**Backend**: Python, FastAPI, Uvicorn, Pandas, NumPy, scikit-learn, SciPy, Joblib, Pydantic
**Frontend**: React, Vite, JavaScript, Axios
**실행 환경**: Docker, Docker Compose

## 4. 폴더 구조

```text
services/06-movie-recommendation-ai-advanced/
├── ai-server/
│   ├── data/
│   │   ├── README.md
│   │   └── ml-100k/                  # MovieLens 100K 원본
│   ├── notebooks/
│   │   └── project06_movie_recommendation_advanced.ipynb
│   ├── models/                       # 학습 산출물 (model_info.json, recommendation_config.json만 Git 포함)
│   ├── feature_engineering.py
│   ├── train_model.py
│   ├── recommendation_service.py
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   └── start.sh
├── frontend/
│   ├── public/favicon.svg
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── UserSearch.jsx / UserCard.jsx
│   │   │   ├── UserProfile.jsx / FavoriteGenres.jsx / RatingHistory.jsx
│   │   │   ├── RecommendationList.jsx / RecommendationCard.jsx
│   │   │   └── LoadingState.jsx / ErrorState.jsx
│   │   ├── services/api.js
│   │   ├── App.jsx / App.css
│   │   └── main.jsx / index.css
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── Research_Report.md
├── Instructor_Movie_Recommendation_Advanced_Guide.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 5. MovieLens 100K 데이터

이 저장소에는 교육용 데모를 별도 준비 없이 바로 실행할 수 있도록 `ai-server/data/ml-100k/` 원본 데이터가
포함되어 있습니다. 데이터가 없는 환경이라면 아래 방법으로 준비하세요.

```bash
cd services/06-movie-recommendation-ai-advanced/ai-server/data
curl -O https://files.grouplens.org/datasets/movielens/ml-100k.zip
unzip ml-100k.zip
```

저장 경로: `services/06-movie-recommendation-ai-advanced/ai-server/data/ml-100k/`. 자세한 내용은
[`ai-server/data/README.md`](./ai-server/data/README.md)를 참고하세요.

## 6. 로컬 실행

```bash
# Backend
cd services/06-movie-recommendation-ai-advanced/ai-server
pip install -r requirements.txt
python train_model.py        # data/ml-100k/ 에 데이터가 있을 때만
uvicorn main:app --reload

# Frontend
cd services/06-movie-recommendation-ai-advanced/frontend
npm install
npm run dev
```

## 7. Docker 실행

```bash
cd services/06-movie-recommendation-ai-advanced
docker compose up --build
# 백그라운드 실행
docker compose up --build -d
docker compose ps
docker compose logs -f
docker compose down
```

`ai-server/start.sh`가 컨테이너 시작 시 다음 순서로 동작합니다.

```text
모델 산출물 있음               -> 바로 FastAPI 실행
모델 없음 + 데이터 있음         -> train_model.py 실행 후 FastAPI 실행
모델 없음 + 데이터 없음         -> 안내 메시지 출력 후 서버 실행하지 않음(exit 1)
```

## 8. 접속 주소

| 서비스 | 주소 |
|---|---|
| Backend (FastAPI) | http://localhost:8001 |
| Swagger 문서 | http://localhost:8001/docs |
| Frontend (React/Vite) | http://localhost:5174 |

> 같은 저장소의 `06-movie-recommendation-ai`(Project05)와 동시에 실행할 수 있도록 호스트 포트를
> 8000/5173이 아닌 **8001/5174**로 배정했습니다(컨테이너 내부 포트는 동일하게 8000/5173을 사용합니다).

## 9. API 목록

| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 서비스 상태 |
| GET | `/health` | Health Check (모델 로딩 상태 포함) |
| GET | `/model-info` | 모델명/알고리즘/평점 통계/데이터 규모 |
| GET | `/users?search=&limit=&min_ratings=` | 사용자 목록/검색 |
| GET | `/users/{user_id}/profile` | 사용자 취향 프로필 |
| GET | `/users/{user_id}/ratings?limit=&sort=` | 사용자 평점 이력 |
| POST | `/recommend/user` | 개인화 추천 (`{"user_id": 1, "top_n": 10}`) |
| GET | `/recommend/popular?top_n=` | 인기 추천(Cold Start 대체) |
| GET | `/movies?search=&limit=` | 영화 검색 |

`POST /recommend/user` 응답 예시(실제 실행 결과):

```json
{
  "user": {
    "user_id": 1,
    "rating_count": 272,
    "activity_level": "High Activity",
    "favorite_genres": ["Drama", "Sci-Fi", "Comedy"]
  },
  "strategy": {
    "name": "hybrid",
    "weights": {"content": 0.1, "collaborative": 0.15, "svd": 0.6, "popularity": 0.15},
    "cold_start": false
  },
  "recommendations": [
    {
      "movie_id": 276,
      "title": "Leaving Las Vegas",
      "release_year": 1995,
      "genres": ["Drama", "Romance"],
      "hybrid_score": 0.8941,
      "predicted_rating": 4.61,
      "content_score": 0.7504,
      "collaborative_score": 0.8252,
      "svd_score": 1.0,
      "popularity_score": 0.635,
      "average_rating": 3.7,
      "rating_count": 298,
      "recommendation_reason": "잠재 요인 분석 결과, 아직 보지 않은 영화 중 예측 평점이 높습니다."
    }
  ]
}
```

존재하지 않는 `user_id`는 404, `top_n`이 1~30 범위를 벗어나면 422, 모델이 아직 준비되지 않았으면 503을
반환합니다.

## 10. 모델 학습 / 재생성

```bash
cd services/06-movie-recommendation-ai-advanced/ai-server
python train_model.py
```

산출물: `models/movie_features.pkl`, `genre_matrix.pkl`, `user_profiles.pkl`, `item_similarity.pkl`,
`user_similarity.pkl`, `svd_model.pkl`, `popularity_ranking.pkl`, `ratings.pkl`,
`recommendation_config.json`, `model_info.json`. `.pkl` 파일은 Git에서 제외되며, JSON 산출물만 Git에
포함됩니다.

## 11. 추천 알고리즘

Popularity / Content-Based / Item-Based CF / User-Based CF / SVD(Matrix Factorization) 5개를 구현하고
Leave-One-Out 방식으로 평가한 뒤, **활동 수준별로 가중치를 다르게 적용하는 Hybrid Recommendation**을
최종 전략으로 채택했습니다. 알고리즘별 원리, 실제 평가 지표(Precision/Recall/Hit Rate@10, Coverage),
가중치를 튜닝하게 된 과정은 [`Research_Report.md`](./Research_Report.md) 11.6~11.8절에 근거와 함께
정리되어 있습니다.

## 12. 데이터 파일 / 모델 파일 관리

- `ai-server/data/ml-100k/`: 교육용 데모 목적으로 이 저장소에 포함되어 있습니다(`.gitignore`는 일반
  정책상 제외하도록 되어 있으나 예외적으로 포함).
- `ai-server/models/*.pkl`: Git에서 제외합니다. `model_info.json`, `recommendation_config.json`은 용량이
  작고 통계/설정 정보만 담고 있어 Git에 유지합니다.
- 데이터를 다시 받았거나 모델을 재생성하고 싶다면 `start.sh`(Docker) 또는 `python train_model.py`(로컬)로
  언제든 재생성할 수 있습니다.

## 13. 문제 해결

| 증상 | 원인 / 해결 |
|---|---|
| 서버가 시작되지 않고 바로 종료됨 | 모델과 데이터가 모두 없는 상태입니다. `data/README.md`에 안내된 경로에 데이터를 추가하세요. |
| `POST /recommend/user`가 503을 반환 | 모델이 아직 준비되지 않았습니다. `python train_model.py`를 실행하거나 데이터 추가 후 컨테이너를 재시작하세요. |
| `POST /recommend/user`가 404를 반환 | 존재하지 않는 `user_id`입니다. `GET /users`로 유효한 ID를 확인하세요. |
| React에서 "서버에 연결할 수 없습니다" | FastAPI가 실행 중인지, Docker Compose라면 `backend` 컨테이너가 정상인지 확인하세요(`docker compose logs backend`). |
| 사용자 선택 화면이 전부 Power User로만 보임 | `GET /users`는 기본적으로 `user_id` 오름차순으로 반환합니다. 특정 정렬이 안 맞다면 `search`/`min_ratings` 파라미터를 조정하세요. |

## 14. 기존 프로젝트(Project04/05)와 공통된 구조

- Backend/Frontend 분리, FastAPI + React(Vite) 구성
- `start.sh`가 모델 존재 여부를 확인해 필요할 때만 학습 후 서버를 실행하는 방식
- `feature_engineering.py`를 Notebook·학습(`train_model.py`)·서빙(`recommendation_service.py`)이 공유하는 구조
- 데이터/모델 파일을 Git에서 기본적으로 제외하고 안내 메시지로 준비 방법을 알려주는 정책
- CORS, 404/422/503 오류 처리, Swagger 문서, React의 Loading/Error/초기 상태 UI 패턴

## 15. Project05에서 새로 추가된 기능

- 영화 1편 기준 유사도 추천 -> **사용자 평점 이력 기반 개인화 추천**
- 사용자 프로필 Feature Engineering(활동 수준, 장르 선호 벡터, 선호 개봉연도, 활동 기간)
- Item-Based CF 단일 알고리즘 -> **Popularity/Content/Item-CF/User-CF/SVD 5종 구현 및 정량 평가**
- 고정 가중치 -> **평가 결과를 근거로 튜닝한 활동 수준별 하이브리드 가중치**
- 영화 검색 UI -> **사용자 선택(카드) + 대시보드 + 개인화 추천 결과 UI**

## 16. AWS 관련 안내

이 프로젝트에는 AWS 배포 관련 문서·설정·명령어가 포함되어 있지 않습니다. Docker Compose 기반 로컬/서버
실행만 다룹니다.
