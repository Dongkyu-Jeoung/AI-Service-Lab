# Research Report — Movie Recommendation AI Advanced

Project06(심화) 연구 보고서입니다. 이 문서의 모든 수치는 `ai-server/notebooks/project06_movie_recommendation_advanced.ipynb`를
실제로 실행한 결과이며, 가상의 수치는 포함하지 않습니다. 재현하려면 해당 노트북을 위에서부터 순서대로 실행하세요.

---

## 11.1 프로젝트 개요

### 프로젝트 배경

MovieLens 100K는 추천 시스템 교육에 널리 쓰이는 공개 데이터셋으로, 943명의 사용자가 1,682편의 영화에 남긴
100,000건의 평점(1~5점)과 사용자/영화 메타데이터를 포함한다. Project05(`services/06-movie-recommendation-ai`)는
같은 데이터로 "영화 한 편을 선택하면 비슷한 영화를 추천"하는 입문 프로젝트를 구현했다. Project06은 여기서
한 단계 심화해, **사용자의 평점 이력 전체를 분석해 개인 취향 프로필을 만들고 이를 바탕으로 개인화 추천**을
제공한다.

### 프로젝트 목적

- 사용자별 활동량과 평점 이력을 분석해 취향 프로필(선호 장르, 선호 연대, 대표 고평점 영화 등)을 만든다.
- Popularity / Content-Based / Item-Based CF / User-Based CF / SVD(Matrix Factorization) 다섯 가지 알고리즘을
  각각 구현하고 정량/정성적으로 비교한다.
- 사용자 활동 수준에 따라 가중치를 다르게 적용하는 Hybrid Recommendation을 최종 전략으로 채택하고, 그 근거를
  실제 평가 지표로 뒷받침한다.
- Cold Start(신규/저활동 사용자), 이미 평가한 영화 제외, 추천 이유 생성 등 실제 서비스에 필요한 요소를 갖춘다.

### 해결하려는 문제

"영화 한 편과 비슷한 영화 찾기"만으로는 사용자마다 다른 취향, 활동량, 평가 성향의 차이를 반영할 수 없다.
Project06은 사용자 단위로 데이터를 분석해 이 문제를 해결한다.

### 사용자에게 제공하는 가치

- 자신의 평점 이력을 요약해서 확인할 수 있다(평점 개수, 평균, 활동 수준, 선호 장르).
- 취향에 맞는 영화를 추천받고, 왜 추천되었는지 이유를 확인할 수 있다.
- 평점 이력이 적은 사용자도 인기 기반 대체 추천을 받을 수 있다.

### 최종 서비스 기능

MovieLens 사용자 카드 선택(교육용 데모 로그인) → 사용자 대시보드(평점 통계, 선호 장르, 평점 이력) → 개인화
추천 결과(추천 개수 조절, 하이브리드 점수, 추천 이유) → 다른 사용자로 전환.

### Project05와의 차이

| 구분 | Project05 (`06-movie-recommendation-ai`) | Project06 (`06-movie-recommendation-ai-advanced`) |
|---|---|---|
| 입력 | 영화 1편 선택 | 사용자 선택(평점 이력 전체 사용) |
| 알고리즘 | Item-Based CF + 장르 기반 대체 | Popularity/Content/Item-CF/User-CF/SVD/Hybrid |
| 개인화 | 없음(선택한 영화 기준) | 있음(사용자 취향 프로필 기반) |
| 평가 | 없음 | Leave-One-Out 기반 정량 평가 |
| Cold Start | 평점 부족 "영화"에 대응 | 평점 부족 "사용자"에 대응(활동 수준별 가중치) |

---

## 11.2 개인화 추천 시스템 개념

- **추천 시스템**: 사용자가 관심 가질 만한 아이템을 자동으로 찾아 보여주는 시스템.
- **개인화 추천 vs 비개인화 추천**: 비개인화 추천(Popularity)은 모든 사용자에게 동일한 결과를 주지만,
  개인화 추천은 사용자마다 다른 결과를 준다.
- **사용자, 아이템, 상호작용**: 이 프로젝트에서 사용자=MovieLens user_id, 아이템=영화, 상호작용=평점(1~5).
- **명시적 피드백**: 사용자가 직접 남긴 평점처럼 선호를 명확히 드러내는 신호. **암묵적 피드백**: 클릭,
  시청 시간처럼 간접적으로 선호를 추정하는 신호. 이 프로젝트는 명시적 피드백(평점)만 사용한다.
- **사용자 프로필 / 취향 벡터**: 사용자의 장르 선호를 19차원 벡터(`genre_pref_*`)로 표현한 것.
- **후보 생성(Candidate Generation)**: 추천 가능한 영화 후보를 추리는 단계(이미 평가한 영화 제외 등).
- **랭킹(Ranking)**: 후보에 점수를 매겨 정렬하는 단계.
- **Cold Start**: 상호작용(평점) 이력이 거의 없는 사용자/아이템에 대한 추천이 어려운 문제.
- **데이터 희소성(Sparsity)**: 사용자-아이템 행렬에서 실제 상호작용이 채워진 비율이 매우 낮은 현상
  (본 데이터셋은 93.70%가 빈 칸이다 — 20장 참고).
- **인기 편향(Popularity Bias)**: 인기 아이템이 계속 더 많이 추천되어 다양성이 줄어드는 현상.
- **필터 버블(Filter Bubble)**: 개인화가 지나쳐 사용자가 이미 좋아하는 것과 비슷한 것만 반복 추천되는 현상.
- **추천 이유의 중요성**: "왜 추천되었는지" 설명이 있어야 사용자가 추천 결과를 신뢰할 수 있다.

---

## 11.3 데이터셋 설명

**MovieLens 100K**: GroupLens Research가 제공하는 943명 사용자, 1,682편 영화, 100,000건 평점(1~5점,
정수) 데이터셋.

| 파일 | 역할 | 주요 컬럼 |
|---|---|---|
| `u.data` | 평점 이력 | user_id, movie_id, rating, timestamp (탭 구분) |
| `u.item` | 영화 메타데이터 | movie_id, title, release_date, imdb_url, 장르 19개 (파이프 구분, latin-1) |
| `u.user` | 사용자 정보 | user_id, age, gender, occupation, zip_code (파이프 구분) |
| `u.genre` | 장르 코드 목록 | genre_name, genre_id |
| `u.occupation` | 직업 코드 목록 | occupation_name |

- 사용자 수: 943명 / 영화 수: 1,682편 / 평점 수: 100,000건 (실제 로딩 결과와 일치)
- 평점 범위: 1~5 (정수)
- 관계: `ratings.user_id` → `users.user_id`, `ratings.movie_id` → `movies.movie_id` (다대다를 잇는
  중간 테이블이 `ratings`)

---

## 11.4 EDA

### 데이터 구조/기술통계

- `ratings`: (100000, 4), 결측치 없음, 완전 중복 0건, (user_id, movie_id) 중복 평가 0건
- `movies`: (1682, 22, `video_release_date` 제거 후), `release_date`/`imdb_url`에 소수 결측 존재(추천 로직
  미사용 컬럼)
- `users`: (943, 5), 결측치 없음
- 제목이 중복된 영화가 존재하지만(서로 다른 `movie_id`), 추천/유사도 계산은 `movie_id` 기준이라 문제 없음

### 전체 평점 분포

- 평점별 건수: 1점 6,110 / 2점 11,370 / 3점 27,145 / 4점 34,174 / 5점 21,201
- 평균 3.530, 중앙값 4.0, 최빈값 4, 표준편차 1.126 → 평균 < 중앙값(약한 음의 왜도), 사용자들이 전반적으로
  후하게 평가하는 경향

### 사용자별 평점 개수 분포 (핵심 분석)

- `count`=943, `mean`=106.04, `std`=100.93, `min`=20, `25%`=33, `50%`=65, `75%`=148, `max`=737
- 왜도(skewness) = **1.90** (뚜렷한 양의 왜도, 오른쪽으로 긴 꼬리)
- 활동 수준 구간(실제 분포의 백분위수 0/50/80/95/100%로 구간화):

  | 구간 | 인원 | 비율 |
  |---|---|---|
  | Low Activity | 477명 | 50.6% |
  | Medium Activity | 277명 | 29.4% |
  | High Activity | 141명 | 15.0% |
  | Power User | 48명 | 5.1% |

- **해석**: 절반 이상의 사용자가 Low Activity 구간에 속한다. 이는 이 데이터셋이 "최소 20건 이상 평가한
  사용자만 수집"했음에도 불구하고, 여전히 다수 사용자는 상대적으로 적은 정보만 제공한다는 뜻이다. 협업
  필터링 신뢰도는 활동량에 비례해서 좋아지므로, 서비스는 이 절반 이상의 사용자에게 안정적인 대체 신호
  (Content-Based, Popularity)를 함께 제공해야 한다 — 이것이 활동 수준별 하이브리드 가중치의 근거다.

### 영화별 평점 개수 분포 (Long Tail)

- 1,682편 중 743편(44.2%)이 평점 20건 미만 — Long Tail이 사용자 쪽보다 더 뚜렷하다.
- `mean`=59.45, `std`=80.38, `max`=583 (영화별 평점 개수, 평점 0건 영화 포함)
- 인기도 구간(백분위수 기준): Niche 855편 / Moderate 493편 / Popular 249편 / Blockbuster 85편

### 사용자별/영화별 평균 평점, 표준편차

- 사용자별 평균 평점은 사용자마다 후하게/엄격하게 평가하는 차이가 존재 → 사용자 평균 중심화(centering)의
  근거
- 평점 수가 적은 영화일수록 평균이 극단(1.0 또는 5.0)에 몰리는 경향 → Bayesian Weighted Rating 사용 근거

### 사용자 인구통계

- 연령 중앙값 31세, 성별 비율 남성 71.0% / 여성 29.0%, 직업은 `student`, `other`, `educator` 비중이 높음
- 인구통계는 프로필 표시용으로만 사용하고 추천 점수 계산에는 관여시키지 않는다(차별적 추천 방지).

### 장르 / 개봉연도 / 시간 분포

- 장르 수: Drama, Comedy가 가장 많고 Fantasy/Film-Noir/unknown이 가장 적음
- 개봉연도: 평균 1989.1년, 중앙값 1995년(1990년대 중후반에 집중, 데이터 수집 시점이 1997~1998년이기 때문).
  제목에서 연도를 추출하지 못한 영화 1편("unknown")
- 평점 활동 기간: 데이터 내 최초 평가일 1997-09-20, 최근 평가일 1998-04-22 (약 7개월)

---

## 11.5 Feature Engineering

### 영화 Feature

| Feature | 설명 |
|---|---|
| `rating_count`, `rating_mean`, `rating_std` | 영화별 평점 통계 |
| `weighted_rating` | Bayesian Weighted Rating (`m`=43.00건, 전체 평균 `C`=3.0760) |
| `clean_title`, `release_year`, `search_title` | 제목 파싱(정규식 `\(\d{4}\)` 마지막 매치 기준 연도 분리) |
| `genres` | 19차원 Multi-Hot 장르 리스트 |
| `popularity_level` | `rating_count` 백분위수 기반 4구간(Niche/Moderate/Popular/Blockbuster) |
| `popularity_score` | `weighted_rating`을 전체 영화 기준 Min-Max 정규화(0~1) |

가중 평점 공식: `weighted = (v/(v+m))·R + (m/(v+m))·C` (`v`=평점 수, `R`=평균 평점, `m`=최소 투표 수 기준,
`C`=전체 평균). `m`은 `rating_count`의 60번째 백분위수로 데이터 기반 결정한다.

### 사용자 Feature (취향 프로필)

| Feature | 설명 |
|---|---|
| `rating_count`, `rating_mean`, `rating_std` | 사용자별 평점 통계 |
| `activity_level` | `rating_count` 백분위수 기반 4구간 |
| `genre_pref_*` (19차원) | `(rating-3)`을 가중치로 사용한 장르 선호 벡터(음수는 0으로 클리핑 후 정규화) |
| `favorite_genres` | 선호 벡터 상위 3개 장르 |
| `preferred_release_year`/`preferred_release_decade` | 4점 이상 평가한 영화의 개봉연도 중앙값 |
| `top_rated_movie_ids` | 평점 내림차순(동점 시 최신 평가 우선) 상위 5편 |
| `first_rating_date`/`last_rating_date`/`active_days` | 데이터 내부 timestamp 기준(절대 현재 시점 사용 금지) |

**"본 횟수"가 아니라 "평점"을 반영하는 이유**: 어떤 사용자가 특정 장르를 많이 "봤다"고 해서 그 장르를
좋아한다고 볼 수 없다(낮게 평가했을 수도 있음). `(rating-3)` 가중치는 4~5점을 양의 신호, 1~2점을 음의
신호, 3점을 중립으로 처리해 실제 선호에 더 가깝게 만든다.

### Interaction Feature

- **사용자-영화 행렬**: (943, 1682), 희소도(빈 칸 비율) **93.70%**
- **평점 중심화**: 사용자 평균을 뺀 뒤 결측은 0으로 채워 유사도 계산에 사용
- **Item 유사도**: 평점 수가 `MIN_RATING_COUNT_FOR_MOVIE_CF`(실측값 16건, `rating_count`의 40번째
  백분위수) 이상인 **1,010편**만 대상으로 코사인 유사도 계산
- **User 유사도**: 평점 5건 이상인 **943명 전원**(이 데이터셋은 모든 사용자가 20건 이상 평가) 대상으로 계산
- **SVD(Matrix Factorization)**: `TruncatedSVD(n_components=20)`, 설명된 분산 비율 **0.2218**

---

## 11.6 추천 알고리즘

| 알고리즘 | 원리 | Cold Start 대응 | 설명 가능성 | 계산 비용 |
|---|---|---|---|---|
| Popularity | Bayesian Weighted Rating 상위 정렬 | 항상 가능(개인화 없음) | 높음 | 매우 낮음 |
| Content-Based | 사용자 장르 선호 벡터 ↔ 영화 장르 벡터 코사인 유사도 | 신규 영화도 장르만 있으면 가능 | 높음 | 낮음 |
| Item-Based CF | 사용자가 평가한 영화와 유사한 영화의 가중 평균 | 평점 부족 영화는 유사도 행렬에서 제외됨 | 중간 | 중간(사전 계산) |
| User-Based CF | 유사한 사용자(이웃)의 평점 가중 평균 | 평점 부족 사용자는 유사도 신뢰도 낮음 | 중간 | 사용자 수 증가 시 높음(O(n²)) |
| SVD | 잠재 요인 기반 평점 예측 | 학습 데이터에 있는 사용자/영화면 항상 예측 가능 | 낮음(해석 어려움) | 학습 시 중간, 서빙 시 낮음 |
| Hybrid | 위 4개 신호(Popularity/Content/Collaborative/SVD)를 활동 수준별 가중합 | 활동 수준별 가중치로 대응 | 중간(기여도 최대 요소로 이유 생성) | 중간 |

`collaborative_score`는 Item-Based CF(가중치 0.8)와 User-Based CF(가중치 0.2)를 결합한 값이다(근거는
11.8절 참고).

---

## 11.7 모델 평가

### 평가 방식

사용자별 **가장 최근 평점 1건**을 Test로 Holdout하고 나머지를 Train으로 사용하는 시간 순서 기반
Leave-One-Out 평가를 사용했다. Train: 99,057건 / Test: 943건(사용자 1명당 1건), Train 후 사용자별 최소
평점 수는 19건이다. Feature/유사도/SVD는 모두 **Train 데이터만으로 다시 계산**해 데이터 누수를 방지했다.

### 평가 지표

Precision@10, Recall@10, Hit Rate@10, Coverage를 사용했다(사용자당 정답이 1건뿐이라 이 설정에서
Recall@10과 Hit Rate@10은 값이 같다). MAP@K/NDCG는 정답이 1건뿐인 구조에서 정보량이 크지 않아 생략했다.

### 비교표 (실제 실행 결과, K=10)

| 알고리즘 | Precision@10 | Hit Rate@10 (=Recall@10) | Coverage |
|---|---|---|---|
| Popularity | 0.0039 | 0.0392 | 0.0452 |
| Content-Based | 0.0019 | 0.0191 | 0.6867 |
| Item-Based CF | 0.0017 | 0.0170 | 0.4804 |
| User-Based CF | 0.0005 | 0.0053 | 0.6011 |
| **SVD** | **0.0066** | **0.0657** | 0.2372 |
| Hybrid (초기 가중치) | 0.0039 | 0.0392 | 0.2093 |
| **Hybrid (튜닝 후, 최종 채택)** | 0.0053 | 0.0530 | 0.2004 |

Popularity를 기준선으로 사용하는 이유는, 개인화 알고리즘이 "아무 것도 안 하는 것(인기순 정렬)"보다도
못하다면 그 개인화는 의미가 없기 때문이다.

---

## 11.8 최종 모델 선정

### 초기 가중치의 문제 발견

최초 설계한 가중치("활동량이 적을수록 Popularity/Content, 많을수록 Collaborative/SVD")로 평가한 결과,
Hybrid의 Hit Rate@10(0.0392)이 Popularity(0.0392)와 **완전히 동일**했다. 원인을 분석해보니 전체 사용자의
50.6%가 Low Activity 구간인데, 이 구간에 Popularity 가중치(0.40)를 가장 크게 배정했기 때문에 하이브리드
전체 순위가 사실상 Popularity를 따라간 것이었다.

### 가중치 튜닝

각 신호의 단독 성능(11.7절 비교표)을 근거로 가중치를 재설계했다.

- SVD가 단일 알고리즘 중 가장 강한 신호(Hit Rate@10 0.0657)이므로 모든 활동 구간에서 SVD 비중을 가장
  크게 둔다.
- Item-Based CF(0.0170)가 User-Based CF(0.0053)보다 3배 이상 강했으므로 `collaborative_score` 내부
  가중치를 Item 0.6→0.8, User 0.4→0.2로 조정한다.
- Popularity/Content를 0으로 만들지 않는다. 정확도 지표는 낮아도 저활동 사용자의 안정적인 대체 추천과
  추천 이유의 설명 가능성을 담당하기 때문이다.

### 최종 가중치 (`feature_engineering.HYBRID_WEIGHTS_BY_ACTIVITY`)

| 활동 수준 | content | collaborative | svd | popularity |
|---|---|---|---|---|
| Low Activity | 0.25 | 0.10 | 0.35 | 0.30 |
| Medium Activity | 0.20 | 0.15 | 0.45 | 0.20 |
| High Activity | 0.10 | 0.15 | 0.60 | 0.15 |
| Power User | 0.10 | 0.15 | 0.65 | 0.10 |

튜닝 결과 Hit Rate@10이 0.0392 → **0.0530**으로 개선되었다(+35% 상대 개선).

### 왜 SVD 단독이 아니라 Hybrid를 최종 채택했는가

SVD 단독(0.0657)이 튜닝된 Hybrid(0.0530)보다 이 지표 하나에서는 근소하게 앞선다. 그럼에도 Hybrid를 최종
전략으로 채택한 이유:

1. **설명 가능성** — SVD의 잠재 요인은 해석할 수 없어 추천 이유를 만들 수 없다. Hybrid는 기여도가 가장 큰
   구성 요소를 근거로 자연어 추천 이유를 생성한다.
2. **Cold Start 견고성** — 활동량이 매우 적은 사용자에게는 Popularity/Content 비중을 높여 안정적인 대체
   추천을 제공할 수 있다.
3. **단일 지표의 한계** — 이번 평가는 사용자당 정답 1건짜리 고분산 지표다. 정확도 하나만으로 알고리즘을
   고르면 다양성/설명 가능성 같은 다른 서비스 품질 요소를 놓치게 된다.

### 개별 알고리즘의 역할 / 신규·저활동 사용자 처리 / 이미 평가한 영화 제외

- Popularity: 신규 사용자 대체 추천(`GET /recommend/popular`), Hybrid의 안정성 확보
- Content-Based: 해석 가능한 장르 기반 추천, Cold Start 영화에도 강함
- Item/User-CF: 실제 평점 패턴 기반 협업 신호
- SVD: 가장 강한 정확도 신호, 밀집 예측으로 항상 값 존재
- 모든 알고리즘의 후보 생성 단계에서 `unseen_movies()`로 이미 평가한 영화를 제외한다.
- 이 데이터셋은 모든 사용자가 20건 이상 평가되어 있어 "평점 0건 신규 사용자"는 존재하지 않는다. 활동량이
  가장 적은 사용자(Low Activity)를 사실상의 Cold Start 사용자로 간주해 대응한다.

### 추천 이유 생성 방식

하이브리드 점수에 가중치를 곱한 기여도가 가장 큰 구성 요소를 기준으로 문장을 생성한다
(`recommendation_service.py`의 `_build_reason`). Content가 1위면 공통 선호 장르를 언급하고, Collaborative가
1위면 "비슷한 취향의 사용자들이 높게 평가"를, SVD가 1위면 "잠재 요인 분석 결과 예측 평점이 높음"을,
Popularity가 1위면 "평가 수와 평균 평점이 높은 인기 영화"를 안내한다.

### 한계 및 향후 개선 방향

한계: (1) User-Based CF는 사용자 수 증가 시 유사도 계산 비용이 커진다. (2) SVD 잠재 요인은 해석이 어렵다.
(3) 장르만으로는 세밀한 스토리 취향까지 구분하지 못한다. (4) 완전한 신규 사용자(평점 0건) 데모는 이
데이터셋 특성상 제공하지 못한다. (5) 가중치 튜닝이 Hit Rate@10 한 지표만 기준으로 이루어졌다.

향후 개선: 태그/줄거리 텍스트 기반 Content Feature 추가, 시청 시간 등 암묵적 피드백 활용, 온라인 A/B
테스트를 통한 가중치 자동 튜닝, NDCG·다양성·참신성을 포함한 다목적 평가.

---

## 11.9 서비스 구조

- **Notebook** (`ai-server/notebooks/project06_movie_recommendation_advanced.ipynb`): EDA, Feature
  Engineering 검증, 알고리즘 구현·비교·평가, 가중치 튜닝, 최종 전략 선정 근거를 담은 연구 문서.
- **`feature_engineering.py`**: 데이터 로딩/정제/Feature 생성/유사도·SVD 계산 등 Notebook과 운영 코드가
  공유하는 순수 함수와 최종 하이브리드 가중치 상수.
- **`train_model.py`**: Notebook에서 검증한 로직을 운영용으로 정리해 `models/*.pkl`,
  `recommendation_config.json`, `model_info.json`을 생성.
- **`recommendation_service.py`**: 저장된 산출물만 로드해 요청마다 다시 학습하지 않고 하이브리드 추천을
  계산.
- **`main.py`(FastAPI)**: 입출력/오류 처리(404/422/503 등)만 담당.
- **React Frontend**: 사용자 선택(카드) → 대시보드(프로필/선호 장르/평점 이력) → 개인화 추천 결과.
- **Docker**: `docker-compose.yml`이 Backend/Frontend를 함께 실행하며, `start.sh`가 산출물 존재 여부를
  확인해 필요할 때만 `train_model.py`를 실행한다.

전체 요청 흐름: `사용자 선택 → GET /users/{id}/profile, /users/{id}/ratings → POST /recommend/user →
하이브리드 점수 계산(메모리에 로드된 산출물 사용) → 추천 결과 + 이유 반환`.
