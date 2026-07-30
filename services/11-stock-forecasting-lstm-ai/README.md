# Stock Forecasting AI (LSTM)

> ⚠️ **교육용 프로젝트 안내**
>
> 이 프로젝트는 **"주가를 맞추는 AI"가 아닙니다.** LSTM을 이용한 시계열 예측을
> 처음부터 끝까지 직접 구현해보는 **교육용 실습 프로젝트**이며, 실제 투자 판단의
> 근거로 사용해서는 안 됩니다. 주가는 뉴스, 심리, 거시경제 등 모델이 알 수 없는
> 수많은 요인에 좌우되며, 여기서 학습하는 모델은 과거 가격 패턴만을 학습합니다.
> **실제 투자에 이 프로젝트의 예측 결과를 사용하지 마세요.**

Yahoo Finance 주가 데이터로 LSTM 모델을 학습하고, FastAPI + React로 서빙하는
End-to-End 실습 프로젝트입니다.

## 프로젝트 구조

```text
10-stock-forecasting-lstm-ai/
├── ai-model/          # 데이터 수집 → EDA → Feature Engineering → 학습 → 평가
│   ├── src/
│   └── artifacts/     # 학습 결과물 (model.keras, scaler.pkl, metadata.json, 리포트/그래프)
├── ai-server/          # FastAPI 예측 API (routers/services/schemas/core/utils)
├── frontend/           # React + TailwindCSS 대시보드
├── docs/               # 01~14 단계별 학습 문서
├── prompts/            # 이 프로젝트를 생성한 원본 프롬프트
├── docker-compose.yml
└── README.md
```

## 빠른 시작

### 1) 모델 학습 (필수 — 최소 1개 종목)

```bash
cd ai-model
pip install -r requirements.txt
cd src
python train.py --ticker AAPL
```

학습이 끝나면 `ai-model/artifacts/AAPL/`에 `model.keras`, `scaler.pkl`,
`metadata.json`, EDA 리포트, 평가 그래프가 생성됩니다.

### 2) 백엔드 실행

```bash
cd ai-server
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger 문서: http://localhost:8000/docs

### 3) 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

http://localhost:5173 접속

### 4) Docker로 한 번에 실행

```bash
# 1) 먼저 최소 한 종목은 로컬에서 학습되어 있어야 합니다
cd ai-model/src && python train.py --ticker AAPL && cd ../..

# 2) 컨테이너 실행
docker compose up --build
```

## 지원 종목

`AAPL`, `MSFT`, `TSLA`, `NVDA`, `GOOG` (`ai-model/src/config.py`의
`SUPPORTED_TICKERS`에서 변경/추가 가능)

## 스크린샷

`docs/screenshots/` 폴더에 실습 후 직접 캡처한 화면을 추가하세요.

## 학습 문서 (docs/)

| 문서 | 내용 |
|---|---|
| 01_Project_Overview.md | 프로젝트 개요, 교육 목적 안내 |
| 02_TimeSeries_Basics.md | 시계열 데이터 기초 |
| 03_EDA.md | 탐색적 데이터 분석 |
| 04_FeatureEngineering.md | 피처 엔지니어링, 스케일링, 시퀀스 생성 |
| 05_LSTM.md | LSTM 모델 구조 |
| 06_Model_Training.md | 모델 학습 |
| 07_Model_Evaluation.md | 평가지표, Baseline 비교 |
| 08_FastAPI.md | 백엔드 API 구조 |
| 09_React.md | 프론트엔드 구조 |
| 10_Docker.md | Docker 실행 방법 |
| 11_AWS_Deployment.md | 배포 참고 가이드 |
| 12_API_Document.md | API 명세 |
| 13_Project_Workflow.md | 전체 워크플로우 요약 |
| 14_Troubleshooting.md | 트러블슈팅 |

## 기술 스택

- **AI Model**: Python, TensorFlow/Keras, Pandas, NumPy, Scikit-Learn, Matplotlib, yfinance
- **Backend**: FastAPI
- **Frontend**: React, Vite, TailwindCSS, recharts
- **Infra**: Docker, Docker Compose

## 다시 한 번: 이 프로젝트의 목적

이 프로젝트의 목표는 **LSTM으로 시계열을 예측하는 전체 파이프라인을 학생이
가장 쉽게 이해하도록 돕는 것**입니다. 실제 주가 예측 성능(수익률)을 높이는 것이
목적이 아니며, 실전 투자에 사용하기에는 명백히 부족한 단순화된 모델입니다.
**교육 목적으로만 사용하세요.**
